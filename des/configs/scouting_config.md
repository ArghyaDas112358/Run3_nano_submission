# MC_2024_Scouting.py -- Scouting Config Deep Dive

This document provides a complete walkthrough of the scouting NanoAOD
configuration, which produces NanoAOD output with reclustered jets and advanced
ML taggers from HLT scouting objects.

## Generation Command

The config was generated with `cmsDriver.py`:

```
cmsDriver.py --python_file MC_2024_Scouting.py \
  -s NANO:@GENFromMini+@ScoutFromMini \
  --process NANO -n 10 --nThreads 4 \
  --era Run3_2024 \
  --customise PhysicsTools/NanoAOD/custom_run3scouting_cff.addScoutingPFCandidate \
  --customise_commands 'process.NANOAODSIMoutput.outputCommands.append("keep edmTriggerResults_*_*_*")' \
  --no_exec --eventcontent NANOAODSIM --datatier NANOAODSIM --mc \
  --fileout file:MC_2024_Scouting.root \
  --conditions auto:phase1_2024_realistic \
  --filein <MiniAOD_input>
```

Key differences from standard `cmsDriver.py` invocations:
- The step is `NANO:@GENFromMini+@ScoutFromMini` instead of `NANO:@BTV`.
- The `--customise` flag adds `addScoutingPFCandidate` from the scouting module.
- Trigger results are explicitly kept in the output commands.

## Process Definition

```python
from Configuration.Eras.Era_Run3_2024_cff import Run3_2024
process = cms.Process('NANO', Run3_2024)
```

The `Run3_2024` era enables 2024-specific detector geometry, calibration, and
reconstruction behavior throughout the CMSSW framework.

## Module Loading

The config loads two NanoAOD-related modules instead of the single `nano_cff`
used by standard configs:

```python
process.load('PhysicsTools.NanoAOD.nanogen_cff')
process.load('PhysicsTools.NanoAOD.custom_run3scouting_cff')
```

- `nanogen_cff`: Provides generator-level NanoAOD tables (GenParticles,
  GenJets, LHE info, GenMET) from MiniAOD input.
- `custom_run3scouting_cff`: Provides the scouting NanoAOD sequence that
  converts packed HLT scouting objects into flat NanoAOD tables.

## Path and Schedule

```python
process.nanoAOD_step0 = cms.Path(process.nanogenSequence)
process.nanoAOD_step1 = cms.Path(process.scoutingNanoSequence)
process.endjob_step   = cms.EndPath(process.endOfProcess)
process.NANOAODSIMoutput_step = cms.EndPath(process.NANOAODSIMoutput)

process.schedule = cms.Schedule(
    process.nanoAOD_step0,
    process.nanoAOD_step1,
    process.endjob_step,
    process.NANOAODSIMoutput_step
)
```

The schedule runs two processing paths in order:
1. **step0 (nanogenSequence)**: Produces generator-level NanoAOD tables from
   MiniAOD packed gen particles. This provides truth information for MC.
2. **step1 (scoutingNanoSequence)**: Produces scouting-level NanoAOD tables
   from packed HLT scouting objects (jets, PF candidates, muons, vertices).

## Customization Chain

The customizations are applied in this order:

### 1. addScoutingPFCandidate

```python
from PhysicsTools.NanoAOD.custom_run3scouting_cff import addScoutingPFCandidate
process = addScoutingPFCandidate(process)
```

Adds scouting PF candidate flat tables to the NanoAOD output, giving access to
individual particle-level information from the HLT scouting stream.

### 2. customiseScoutingNano

```python
process = customiseScoutingNano(process)
```

Applies general scouting NanoAOD customizations: table definitions for scouting
jets, muons, electrons, photons, and MET.

### 3. customiseScoutingNanoFromMini

```python
process = customiseScoutingNanoFromMini(process)
```

Adapts the scouting sequence for MiniAOD input (as opposed to raw scouting
data). This is necessary because MC samples are produced as MiniAOD, not as
raw scouting format.

### 4. ScoutingTranslator addAll

```python
from PhysicsTools.ScoutingTranslator.ScoutingNanoCustomisation_cff import addAll
process = addAll(process)
```

This is the most significant customization. It adds the full ScoutingTranslator
pipeline:

- **Translation layer**: Converts HLT packed scouting objects (PF candidates,
  tracks, vertices) into reco-format intermediate objects.
- **AK4 jet reclustering**: Clusters `recoScoutingPFCandidate` into AK4 jets
  (R=0.4, pT > 20 GeV) with JEC (AK4PFHLT payload).
- **AK8 fat jet reclustering**: Clusters into AK8 jets (R=0.8, pT > 170 GeV)
  with JEC (AK8PFHLT payload).
- **Primary/secondary vertex reconstruction**: Builds PV from tracks with
  adaptive vertex fitter; finds displaced secondary vertices.
- **HLT ParticleNet tagger**: Runs on both AK4 (probtauhp, probtauhm, probb,
  probc, probuds, probg) and AK8 (probHtt, probHbb, probHcc, etc.) jets.
- **UParT AK4 tagger**: Runs the custom Unified Particle Transformer on
  reclustered AK4 jets, producing 8 discriminator scores: probb, probbb,
  problepb, probc, probuds, probg, probtaum, probtaup.

### 5. customizeNanoGENFromMini

```python
from PhysicsTools.NanoAOD.nanogen_cff import customizeNanoGENFromMini
process = customizeNanoGENFromMini(process)
```

Configures the generator-level NanoAOD tables to read from MiniAOD packed
collections rather than GEN-level collections.

## Tagger Integration Details

### UParT AK4 (Custom HH->bbtautau Model)

- **TagInfo producer**: `UnifiedParticleTransformerAK4TagInfoProducer`
  - `jet_radius = 0.4`, `min_candidate_pt = 0.1`, `max_jet_eta = 2.5`
  - Uses `scoutingVerticesPF` for vertex association
  - `fallback_puppi_weight = True` (no PUPPI available in scouting)
- **ONNX producer**: `UnifiedParticleTransformerAK4ONNXJetTagsScoutingProducer`
  - Model path: `RecoBTag/Combined/data/UParTAK4/Scouting_HHbbtautau/V00/modelfile/model.onnx`
  - Output scores: probb, probbb, problepb, probc, probuds, probg, probtaum, probtaup
- **NanoAOD branch prefix**: `ScoutingPFJetRecluster2_scoutUParT_prob*`
- **NanoAOD pT cut**: >= 15 GeV, |eta| <= 2.5

### HLT ParticleNet AK4

- **TagInfo producer**: `DeepBoostedJetTagInfoProducer`
  - `min_jet_pt = 5.0`, `max_jet_eta = 2.6`, `use_hlt_features = True`
- **ONNX producer**: `BoostedJetONNXJetTagsProducer`
- **Output scores**: probtauhp, probtauhm, probb, probc, probuds, probg
- **NanoAOD branch prefix**: `ScoutingPFJetRecluster2_hltPNet_prob*`

### HLT ParticleNet AK8

- **TagInfo producer**: `DeepBoostedJetTagInfoProducer` (AK8 variant)
  - `jet_radius = 0.8`, `min_jet_pt = 200.0`, `max_jet_eta = 2.5`
- **Output scores**: probHtt, probHtm, probHte, probHbb, probHcc, probHqq,
  probHgg, probQCD2hf, probQCD1hf, probQCD0hf

## Output Module Configuration

```python
process.NANOAODSIMoutput = cms.OutputModule("NanoAODOutputModule",
    compressionAlgorithm = cms.untracked.string('LZMA'),
    compressionLevel = cms.untracked.int32(9),
    dataset = cms.untracked.PSet(
        dataTier = cms.untracked.string('NANOAODSIM'),
        filterName = cms.untracked.string('')
    ),
    fileName = cms.untracked.string('file:MC_2024_Scouting.root'),
    outputCommands = process.NANOAODSIMEventContent.outputCommands
)
```

The output uses LZMA compression at level 9 (maximum) for optimal file size.
The `edmTriggerResults` are explicitly kept via:

```python
process.NANOAODSIMoutput.outputCommands.append("keep edmTriggerResults_*_*_*")
```

This preserves HLT trigger decision bits, which are essential for scouting
trigger studies and event selection.

## Key Parameters Summary

| Parameter | Value | Purpose |
|---|---|---|
| Era | `Run3_2024` | 2024 detector configuration |
| GlobalTag | `auto:phase1_2024_realistic` | Auto-resolved MC conditions |
| Threads | 4 | Parallel processing |
| Compression | LZMA level 9 | Maximum output compression |
| AK4 jet pT min | 20 GeV (clustering), 15 GeV (NanoAOD) | Jet selection |
| AK8 jet pT min | 170 GeV (clustering), 200 GeV (NanoAOD) | Fat jet selection |
| UParT model | Scouting_HHbbtautau/V00 | Custom b-tagging + tau model |

## CMSSW Requirements

This config requires CMSSW 16_0_1 or later with the following external packages:
- `PhysicsTools/ScoutingTranslator` -- Scouting object translation and jet
  reclustering (from ArghyaRanjanDas/ScoutingTranslator fork).
- Custom `RecoBTag` plugins -- Scouting-specific UParT ONNX producers (from
  Yao Yao's development area).
- Two ONNX model files under `RecoBTag/Combined/data/UParTAK4/`:
  - `Scouting/V00/modelfile/model.onnx` (standard)
  - `Scouting_HHbbtautau/V00/modelfile/model.onnx` (analysis-specific)

## Related Files

- `/home/das214/HHtobbtautau/Run3_nano_submission/configs/MC_2024_Scouting.py`
- `/home/das214/HHtobbtautau/Run3_nano_submission/configs/DATA_2024.py` (older
  scouting config variant using `Run3` era)
