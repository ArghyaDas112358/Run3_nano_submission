# GloParT AK8: Global Particle Transformer for Fat Jets

## Status in the Scouting Pipeline

The Global Particle Transformer for AK8 jets (GloParT AK8) is **available in standard
CMSSW** but is **not currently integrated** into the scouting NanoAOD production
pipeline. The scouting AK8 fat jets use only the HLT ParticleNet AK8 tagger
(see `hlt_particlenet.md`).

This document describes the GloParT AK8 architecture and outputs for reference, as it
is a candidate for future integration and is used in standard CMS analyses on
RECO/MiniAOD data.

## Architecture: Global Particle Transformer

GloParT extends the Particle Transformer architecture with global attention mechanisms
for fat jet classification. The key differences from the AK4 UParT include:

- **Larger input space**: AK8 jets contain significantly more constituents than AK4
  jets due to the larger cone size (R=0.8 vs R=0.4).

- **Global context**: The "Global" variant incorporates event-level or jet-level
  context features that modulate the attention mechanism, enabling the network to
  adapt its classification strategy based on jet kinematics.

- **Broader classification targets**: Trained to discriminate among many more final
  states, including various Higgs, top, W, and Z boson decay modes.

The network processes PF candidates and secondary vertices through multi-head
self-attention layers, producing a jet-level embedding that feeds into classification
and regression heads.

## CMSSW Configuration

The standard CMSSW configuration for GloParT AK8 is defined in
`RecoBTag/ONNXRuntime/python/pfGlobalParticleTransformerAK8_cff.py`:

```python
pfGlobalParticleTransformerAK8TagInfos = _pfGlobalParticleTransformerAK8TagInfos.clone(
    use_puppiP4 = False
)

pfGlobalParticleTransformerAK8JetTags = boostedJetONNXJetTagsProducer.clone(
    src = 'pfGlobalParticleTransformerAK8TagInfos',
    preprocess_json = 'RecoBTag/Combined/data/GlobalParticleTransformerAK8/PUPPI/V03/preprocess.json',
    model_path = 'RecoBTag/Combined/data/GlobalParticleTransformerAK8/PUPPI/V03/model.onnx',
    flav_names = [...],  # 22 named outputs + 256 hidden neurons
    debugMode = False,
)
```

The model uses `BoostedJetONNXJetTagsProducer` (the same producer type as HLT
ParticleNet) with JSON-based feature preprocessing.

## Output Classes

### Flavor Classification (17 probabilities)

GloParT AK8 V03 produces 17 flavor classification outputs:

| Output | Description | Physics Channel |
|--------|-------------|----------------|
| `probXbb` | X -> bb | di-b resonance |
| `probXcc` | X -> cc | di-charm resonance |
| `probXcs` | X -> cs | charm-strange resonance |
| `probXqq` | X -> qq (light) | di-light-quark resonance |
| `probXtauhtaue` | X -> tau_h tau_e | leptonic-hadronic tau pair |
| `probXtauhtaum` | X -> tau_h tau_mu | muonic-hadronic tau pair |
| `probXtauhtauh` | X -> tau_h tau_h | fully hadronic tau pair |
| `probXWW4q` | X -> WW -> 4q | fully hadronic WW |
| `probXWW3q` | X -> WW -> 3q + lepton | semi-leptonic WW (3 quarks visible) |
| `probXWWqqev` | X -> WW -> qq + e nu | WW with electron |
| `probXWWqqmv` | X -> WW -> qq + mu nu | WW with muon |
| `probTopbWqq` | top -> bWqq | fully hadronic top |
| `probTopbWq` | top -> bWq | partial top (merged W) |
| `probTopbWev` | top -> bW(e nu) | leptonic top with electron |
| `probTopbWmv` | top -> bW(mu nu) | leptonic top with muon |
| `probTopbWtauhv` | top -> bW(tau_h nu) | leptonic top with hadronic tau |
| `probQCD` | QCD multijet background | generic QCD |

### Regression Outputs (2 values)

| Output | Description |
|--------|-------------|
| `massCorrX2p` | Mass correction factor for X -> 2-prong |
| `massCorrGeneric` | Generic mass correction factor |

### Derived Discriminators (3 values)

| Output | Description |
|--------|-------------|
| `probWithMassTopvsQCD` | Mass-decorrelated top vs QCD |
| `probWithMassWvsQCD` | Mass-decorrelated W vs QCD |
| `probWithMassZvsQCD` | Mass-decorrelated Z vs QCD |

### Hidden Neuron Outputs (256 values)

The model also exposes 256 hidden neuron activations (`hidNeuron000` through
`hidNeuron255`) from the penultimate layer. These can be used for:
- Transfer learning
- Anomaly detection
- Custom discriminant construction via retraining the classification head

## Comparison with HLT ParticleNet AK8

| Aspect | GloParT AK8 (V03) | HLT ParticleNet AK8 (V01) |
|--------|-------------------|--------------------------|
| Architecture | Global Particle Transformer | Dynamic Graph CNN |
| Total outputs | 22 + 256 hidden | 10 |
| Tau channels | 3 (tauhtaue, tauhtaum, tauhtauh) | 3 (Htt, Htm, Hte) |
| b channels | Xbb | Hbb |
| Top channels | 5 (various decay modes) | None |
| W/Z channels | 3 (mass-decorrelated) | None |
| QCD granularity | 1 (generic) | 3 (0hf, 1hf, 2hf) |
| Mass regression | Yes (2 corrections) | No |
| Hidden neurons | 256 exposed | None |
| Model size | Larger (~V03) | Smaller (HLT-optimized) |
| Preprocessing | JSON-based | JSON-based |

## Relevance to HH->bb(tautau)

GloParT AK8 would complement the existing HLT ParticleNet AK8 in several ways:

- **Finer tau discrimination**: Three separate tau pair categories
  (`Xtauhtauh`, `Xtauhtaum`, `Xtauhtaue`) directly map to the HH->bb(tautau)
  signal topology where the Higgs decays to different tau final states.

- **Mass regression**: The mass correction outputs enable improved resonance mass
  reconstruction for boosted Higgs candidates.

- **Top veto**: Five top quark decay categories allow precise rejection of
  tt-bar backgrounds, which are a major background for HH->bb(tautau).

- **QCD discrimination**: While HLT PNet provides 3 QCD categories (by heavy-flavor
  count), GloParT provides a single aggregated QCD score that can simplify
  analysis working point definitions.

## Why GloParT Is Not Yet Integrated

The current scouting pipeline omits GloParT AK8 because:

1. **Scouting-specific model**: No scouting-trained GloParT model exists yet. The
   standard `PUPPI/V03` model expects PUPPI-weighted inputs and full RECO-level
   features that may not be available from scouting data.

2. **Feature compatibility**: The `pfGlobalParticleTransformerAK8TagInfos` producer
   may require input collections (e.g., PUPPI weights, full track info) that the
   scouting translation does not provide.

3. **Priority**: The HLT ParticleNet AK8 already provides the primary Higgs and
   QCD discrimination needed for the analysis, and adding GloParT would increase
   processing time without immediate benefit until a scouting-compatible model is
   trained.

## Potential Integration Path

To integrate GloParT AK8 into the scouting pipeline:

1. Train a scouting-compatible GloParT model using scouting-format features (no PUPPI,
   reduced track precision, fallback vertex association).
2. Create a scouting-specific TagInfo producer (similar to the UParT scouting approach).
3. Add the ONNX model to `RecoBTag/Combined/data/GlobalParticleTransformerAK8/Scouting/`.
4. Configure the producer in `Run3ScoutingFatPFJetRecluster_cff.py`.
5. Add discriminator sources to the PAT fat jet and NanoAOD table definitions.

This would follow the same pattern used for integrating UParT AK4 into the scouting
pipeline, which required custom C++ producers and a dedicated model training.
