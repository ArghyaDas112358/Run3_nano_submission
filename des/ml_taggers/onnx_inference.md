# ONNX Runtime: Model Loading, Batching, and Feature Tensors

## Overview

The ML jet taggers in the scouting NanoAOD pipeline use ONNX (Open Neural Network
Exchange) as the inference format. ONNX models are loaded and executed through the
CMS-integrated ONNXRuntime library, which wraps the Microsoft ONNX Runtime C++ API.
This document covers the inference pipeline from model loading through output
production.

## ONNXRuntime Integration in CMSSW

CMSSW provides a generic ONNX inference interface through the `PhysicsTools/ONNXRuntime`
package. The key class is `ONNXRuntime`, which handles:

- Loading an ONNX model file into memory
- Allocating inference sessions with configurable threading
- Running forward passes with arbitrary input/output tensor configurations
- Thread-safe execution via CMSSW's stream-based concurrency model

Two CMSSW producer patterns use this interface in the scouting pipeline:

1. **BoostedJetONNXJetTagsProducer** -- Used by HLT ParticleNet (AK4 and AK8).
   Takes `DeepBoostedJetTagInfo` objects, applies preprocessing from a JSON file,
   and runs inference. Supports both preprocessed and raw feature inputs.

2. **UnifiedParticleTransformerAK4ONNXJetTagsScoutingProducer** -- Custom producer
   for scouting UParT. Takes `UnifiedParticleTransformerAK4TagInfo` objects and
   runs inference directly without JSON-based preprocessing (normalization is
   handled in the feature extraction stage).

## Model Loading and Caching

### GlobalCache Pattern

The scouting UParT producer uses the CMSSW `edm::GlobalCache` pattern to load the
ONNX model exactly once per job:

```cpp
class UnifiedParticleTransformerAK4ONNXJetTagsScoutingProducer
    : public edm::stream::EDProducer<edm::GlobalCache<ONNXRuntime>>
```

The lifecycle is:

```
Job Start
  |-- initializeGlobalCache()
  |     |-- Read model.onnx from FileInPath
  |     |-- Create ONNXRuntime session
  |     |-- Return shared pointer (accessible to all streams)
  |
  |-- Event Processing (parallel streams)
  |     |-- Stream 0: produce() --> globalCache()->run(...)
  |     |-- Stream 1: produce() --> globalCache()->run(...)
  |     |-- Stream 2: produce() --> globalCache()->run(...)
  |     |-- ...
  |
Job End
  |-- globalEndJob()
  |     |-- ONNXRuntime destructor releases memory
```

This ensures the ~3.8 MB ONNX model is loaded into memory only once, regardless of
the number of processing threads. The `globalCache()` method provides thread-safe
read-only access to the model.

### Model Path Resolution

The model path is specified as a `cms.FileInPath`, which resolves through the CMSSW
data search path:

```python
model_path = cms.FileInPath(
    'RecoBTag/Combined/data/UParTAK4/Scouting_HHbbtautau/V00/modelfile/model.onnx'
)
```

At runtime, CMSSW searches for this path in:
1. The local `src/` directory (for development builds)
2. `$CMSSW_DATA_PATH` (for centrally deployed data)
3. The release area (CVMFS for grid jobs)

For the scouting-specific models, the files must be present in the user's local
`src/RecoBTag/Combined/data/` directory since they are not part of the official
CMSSW release.

## Feature Extraction Pipeline

The inference pipeline follows a two-stage design:

### Stage 1: TagInfo Production

Producer: `UnifiedParticleTransformerAK4TagInfoScoutingProducer`

Input collections:
- `recoScoutingPFJetRecluster` -- Reclustered AK4 jets
- `recoScoutingPFCandidate` -- Translated PF candidates
- `scoutingVerticesPF` -- Reconstructed primary vertices
- `scoutingDeepInclusiveMergedVerticesPF` -- Secondary vertices

For each jet, the producer:
1. Identifies charged and neutral constituents within the jet cone
2. Builds track-level features (impact parameters, SIP, jet distance) for charged candidates
3. Computes relative kinematics (ptrel, deltaR, drminsv) for all candidates
4. Extracts secondary vertex properties (displacement, mass, track count)
5. Sorts charged candidates by SIP2d significance (descending)
6. Sorts neutral candidates by pT (descending)
7. Sorts SVs by dxy significance (descending)
8. Pads/truncates to fixed sizes (26 charged, 25 neutral, 5 SV)
9. Stores the result as a `UnifiedParticleTransformerAK4TagInfo` object

### Stage 2: ONNX Inference

Producer: `UnifiedParticleTransformerAK4ONNXJetTagsScoutingProducer`

Takes the TagInfo objects and converts them to flat float arrays for ONNX input.

## The 6 Input Tensor Groups and Their Shapes

Each tensor uses the layout `[batch, N_objects, N_features]`:

| Tensor | Input Name | Shape | Content |
|--------|-----------|-------|---------|
| 1 | `input_1` | (1, 26, 20) | Charged PF candidate features |
| 2 | `input_2` | (1, 25, 10) | Neutral PF candidate features |
| 3 | `input_3` | (1, 5, 15) | Secondary vertex features |
| 4 | `input_4` | (1, 26, 4) | Charged PF 4-vectors (px, py, pz, e) |
| 5 | `input_5` | (1, 25, 4) | Neutral PF 4-vectors (px, py, pz, e) |
| 6 | `input_6` | (1, 5, 4) | SV 4-vectors (px, py, pz, e) |

The output tensor is:

| Output | Name | Shape | Content |
|--------|------|-------|---------|
| 1 | `ID_pred` | (1, 8) | Flavor probabilities |

Total input floats per jet: 26x20 + 25x10 + 5x15 + 26x4 + 25x4 + 5x4 = 520 + 250 + 75 + 104 + 100 + 20 = **1069 floats**.

## Batch Processing

### Current Implementation: Per-Jet Inference

The scouting producer runs one ONNX inference call per jet within each event:

```
For each event:
    Get TagInfo collection (all jets in event)
    For each jet with is_filled = true:
        1. Read feature sizes (n_cpf, n_npf, n_sv)
        2. Build input shapes: {1, 26, 20}, {1, 25, 10}, ...
        3. Populate 6 float arrays from TagInfo features
        4. Call globalCache()->run(input_names, data, shapes, output_names, batch=1)
        5. Read 8 output probabilities
        6. Store in JetTag collections
```

This means an event with 50 jets triggers 50 separate ONNX inference calls.

### Why Not True Batching?

True batching (processing all jets in a single inference call) would require:
- All jets padded to the same constituent counts
- A single batch dimension covering all jets

The current per-jet approach was chosen because:
1. Jet constituent counts vary significantly (some jets have 5 charged candidates,
   others have 26), making uniform padding wasteful.
2. The scouting context prioritizes simplicity and correctness over throughput.
3. Each inference call processes a small tensor (~1069 floats), so overhead is modest.

### Fixed vs Dynamic Axes

The scouting producer uses `use_dynamic_axes_ = false`, meaning tensor shapes are
fixed at the maximum constituent counts (26, 25, 5). This avoids the overhead of
ONNX dynamic axis resolution at the cost of always padding to maximum size.

## Memory Management

### Input Data Allocation

Input float arrays are allocated per jet and reused across jets within an event:

```cpp
std::vector<std::vector<float>> data_;  // 6 vectors, one per input tensor
```

Before each jet, the arrays are resized and zero-filled. The zero-fill serves as
implicit padding for jets with fewer constituents than the maximum.

### Output Data

The output is a `std::vector<float>` of size 8, returned by reference from the
ONNX runtime. For jets where `is_filled = false` (e.g., no primary vertex available),
the output scores are set to -1 at the NanoAOD table level.

## Scouting-Specific Optimizations

Several design choices reflect the constraints of scouting data:

1. **No lost tracks**: The standard UParT uses 8 input tensors (adding lost track
   features and 4-vectors). Scouting skips these entirely, reducing inputs from 8 to 6.

2. **PUPPI weight fallback**: Scouting PF candidates lack PUPPI weights. The feature
   extractor uses a fallback value of 1.0 for all candidates.

3. **Vertex association fallback**: Without a proper vertex association ValueMap, the
   producer uses the closest-dz primary vertex for each candidate.

4. **Neutral feature placeholder**: The `hadFrac` feature (hadronic energy fraction)
   is unavailable in scouting. It is replaced with a constant value of 1.0. The model
   was trained with this substitution, so it is intentional.

5. **Minimum pT thresholds**: The feature extractor has `min_jet_pt = 0` (no cut),
   but NanoAOD applies a selection of pT >= 15 GeV and |eta| <= 2.5 at the table level.

## HLT ParticleNet ONNX Inference

The HLT ParticleNet taggers (AK4 and AK8) use a different inference path through
`BoostedJetONNXJetTagsProducer`. Key differences from the UParT producer:

- **Preprocessing JSON**: ParticleNet reads feature normalization parameters from a
  JSON file (`preprocess.json`) at runtime, applying per-feature centering and scaling
  before inference.

- **DeepBoostedJetTagInfo**: Uses a different TagInfo format with a single flattened
  feature vector per jet (not split by constituent type).

- **HLT features**: The `use_hlt_features = True` flag activates a reduced feature
  set matching what the HLT computes during data-taking.

## Performance Considerations

- **Model load time**: The 3.8 MB ONNX file loads in under 1 second. This happens once
  per job, so it is negligible for typical production runs processing thousands of events.

- **Per-jet inference time**: Each ONNX call processes ~4 KB of input data through a
  ~3.8 MB model. Typical inference time is on the order of 1 ms per jet.

- **Memory footprint**: The model resides in memory for the lifetime of the job. With
  multi-threaded processing, the shared `GlobalCache` avoids duplicating the model.

- **Debug output**: The current implementation contains debug `std::cout` statements
  (prefixed with "YY:") that should be removed for production to avoid excessive logging.
