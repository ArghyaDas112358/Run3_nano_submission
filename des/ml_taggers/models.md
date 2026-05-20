# Model Files: Scouting vs Scouting_HHbbtautau

## Directory Structure

All UParT AK4 model files for scouting reside under the RecoBTag data area within the
CMSSW working directory:

```
CMSSW_16_0_1/src/RecoBTag/Combined/data/UParTAK4/
|-- Scouting/
|   |-- V00/
|       |-- modelfile/
|           |-- model.onnx                (3,770,396 bytes / ~3.6 MB)
|
|-- Scouting_HHbbtautau/
    |-- V00/
        |-- modelfile/
            |-- model.onnx                (3,803,162 bytes / ~3.6 MB)
```

The full absolute path to the model directory on the Purdue depot is:
```
/depot/cms/private/users/yao317/Analysis/HHtoBBTautau/cmssw/tmp/
    CMSSW_16_0_1/src/RecoBTag/Combined/data/UParTAK4/
```

## Model File Contents

### Current State

Each model variant currently contains a single file:

| Model Variant | File | Size | Last Modified |
|--------------|------|------|---------------|
| Scouting/V00 | `modelfile/model.onnx` | 3,770,396 bytes | 2026-03-05 |
| Scouting_HHbbtautau/V00 | `modelfile/model.onnx` | 3,803,162 bytes | 2026-03-06 |

The ONNX files contain the complete neural network: architecture definition,
trained weights, input/output tensor specifications, and operator graph.

### What Is Not Present

Unlike some other CMSSW taggers (e.g., HLT ParticleNet, GloParT AK8), the scouting
UParT model directories do **not** currently contain:

- **`preprocess.json`**: Feature normalization parameters. For the HLT ParticleNet
  models, a `preprocess.json` file specifies per-feature mean and standard deviation
  values for input normalization. The scouting UParT handles normalization differently:
  feature preprocessing is embedded within the ONNX model itself or applied at the
  C++ feature extraction stage.

- **`config.pbtxt`**: Triton inference server configuration. Present for models that
  support Triton-based inference (e.g., the standard UParT V01 Sonic variant). Not
  needed for the direct ONNX inference used in the scouting pipeline.

- **Training metadata**: No training configuration, hyperparameters, or validation
  performance metrics are stored alongside the model files.

### Contrast with HLT ParticleNet Model Files

For comparison, the HLT ParticleNet model directories contain both model and
preprocessing files:

```
RecoBTag/Combined/data/HLT/ParticleNetAK4/V01/
|-- particle-net.onnx
|-- preprocess.json

RecoBTag/Combined/data/HLT/ParticleNetAK8/V01/
|-- particle-net.onnx
|-- preprocess.json
```

And the standard GloParT AK8 directory:

```
RecoBTag/Combined/data/GlobalParticleTransformerAK8/PUPPI/V03/
|-- model.onnx
|-- preprocess.json
```

## Scouting/V00 vs Scouting_HHbbtautau/V00

### Scouting/V00: General-Purpose Model

- **Training data**: General QCD and signal samples in scouting format
- **Training objective**: Broad flavor discrimination without signal-specific optimization
- **Output classes**: 8 (probb, probbb, problepb, probc, probuds, probg, probtaum, probtaup)
- **Model size**: 3.6 MB (slightly smaller than HHbbtautau variant)
- **Use case**: Baseline model for general scouting analyses, comparison/cross-check
  reference for the HH-specific model

### Scouting_HHbbtautau/V00: Signal-Optimized Model

- **Training data**: Enriched with HH->bb(tautau) signal samples alongside QCD backgrounds,
  using scouting-format reduced-precision data
- **Training objective**: Optimized for simultaneous b-jet and tau-jet discrimination,
  specifically targeting the bb+tautau final state
- **Output classes**: 8 (same structure as Scouting/V00)
- **Model size**: 3.6 MB
- **Use case**: Default model for the HH->bb(tautau) analysis; provides enhanced
  tau discrimination in the low-to-moderate pT regime

The 33 KB size difference between the two models reflects minor differences in trained
weight values (the architecture is identical).

### Both models share:

- Same 6-input tensor structure (no lost tracks)
- Same maximum constituent counts (26 charged, 25 neutral, 5 SV)
- Same output tensor structure (8 flavor probabilities via `ID_pred`)
- Same C++ inference producer (`UnifiedParticleTransformerAK4ONNXJetTagsScoutingProducer`)
- Same feature extraction producer (`UnifiedParticleTransformerAK4TagInfoScoutingProducer`)

## Model Path Configuration in Python

The active model is specified in `Run3ScoutingPFJetRecluster_cff.py`:

```python
scoutingPFJetReclusterPFUnifiedParticleTransformerAK4Tags = cms.EDProducer(
    'UnifiedParticleTransformerAK4ONNXJetTagsScoutingProducer',
    src = cms.InputTag('scoutingPFJetReclusterPFUnifiedParticleTransformerAK4TagInfos'),
    input_names = cms.vstring('input_1', 'input_2', 'input_3',
                              'input_4', 'input_5', 'input_6'),
    model_path = cms.FileInPath(
        'RecoBTag/Combined/data/UParTAK4/Scouting_HHbbtautau/V00/modelfile/model.onnx'
    ),
    output_names = cms.vstring('ID_pred'),
    flav_names = cms.vstring('probb', 'probbb', 'problepb', 'probc',
                             'probuds', 'probg', 'probtaum', 'probtaup'),
)
```

To switch to the general-purpose model, change the `model_path` line to:
```python
    model_path = cms.FileInPath(
        'RecoBTag/Combined/data/UParTAK4/Scouting/V00/modelfile/model.onnx'
    ),
```

No other configuration changes are needed because both models share the same
input/output interface.

## Version Management

### Current Versioning

The directory hierarchy uses a version tag (`V00`) to track model iterations:

```
UParTAK4/<ModelVariant>/<Version>/modelfile/model.onnx
```

`V00` indicates the initial version. When a new model is trained (e.g., with
additional training data, improved hyperparameters, or corrected features), it
should be placed in a `V01` directory alongside the existing `V00`.

### How to Update Models

To deploy a new model version:

1. **Create the version directory**:
   ```
   mkdir -p RecoBTag/Combined/data/UParTAK4/Scouting_HHbbtautau/V01/modelfile/
   ```

2. **Copy the new ONNX model**:
   ```
   cp /path/to/new/model.onnx \
       RecoBTag/Combined/data/UParTAK4/Scouting_HHbbtautau/V01/modelfile/model.onnx
   ```

3. **Update the Python configuration** in `Run3ScoutingPFJetRecluster_cff.py`:
   ```python
   model_path = cms.FileInPath(
       'RecoBTag/Combined/data/UParTAK4/Scouting_HHbbtautau/V01/modelfile/model.onnx'
   )
   ```

4. **Verify input/output compatibility**: If the new model changes the number of
   input tensors, feature counts, or output classes, the C++ producer and the
   NanoAOD table definition must be updated accordingly.

5. **Rebuild CMSSW** if C++ changes were required: `scram b -j 8`

### Compatibility Constraints

When updating models, the following must remain consistent between the ONNX model
and the C++ producer:

| Property | Configured In | Must Match |
|----------|--------------|------------|
| Number of input tensors | `input_names` in Python config | ONNX model input count |
| Input tensor names | `input_names` in Python config | ONNX model input node names |
| Feature dimensions per tensor | Hardcoded in C++ producer | ONNX model input shapes |
| Output tensor name | `output_names` in Python config | ONNX model output node name |
| Number of flavor classes | `flav_names` in Python config | ONNX model output shape[1] |

If any of these change between model versions, both the Python configuration and
potentially the C++ producer code must be updated.

## Deployment for Grid Jobs

For CRAB/condor job submission, model files must be accessible from the worker nodes.
Two deployment strategies exist:

1. **Local checkout**: Include the model files in the CMSSW `src/` directory that
   gets packaged with the job. This is the current approach and works reliably but
   increases the tarball size by ~7.4 MB (both models).

2. **CVMFS deployment**: For officially supported models, files can be deployed to
   CVMFS under the CMSSW data area. The scouting-specific models are not yet
   officially deployed to CVMFS, so local checkout is required.

The `cms.FileInPath` mechanism transparently handles both cases: it searches the
local `src/` directory first, then falls back to CVMFS-deployed data.
