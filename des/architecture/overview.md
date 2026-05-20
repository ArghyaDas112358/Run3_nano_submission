# System Architecture Overview

## Pipeline Summary

The Run3_nano_submission repository produces NanoAOD files for the
HH->bb(tau)(tau) analysis at CMS. It supports three processing modes:
standard MC, standard Data, and Scouting. The scouting pathway is the most
complex, adding HLT object translation, jet reclustering, and advanced ML
jet taggers (UParT, GloParT/HLT ParticleNet) on top of the base NanoAOD
production.

### End-to-End Pipeline (Scouting Mode)

```
 +---------------------+
 |  MiniAOD / RAW      |    Input datasets (RunIII2024Summer24MiniAODv6 or
 |  (from CMS Grid)    |    ScoutingPFRun3 NanoAOD)
 +----------+----------+
            |
            v
 +---------------------+     PhysicsTools/NanoAOD/custom_run3scouting_cff
 | Standard Scouting   |     - Base scouting PF candidates, muons,
 | NanoAOD sequences   |       electrons, photons, MET tables
 +----------+----------+     - addScoutingPFCandidate()
            |                - customiseScoutingNano()
            v
 +---------------------+     PhysicsTools/ScoutingTranslator
 | ScoutingTranslator  |     - HLT packed formats -> reco::PFCandidate,
 | (HLT -> Reco)       |       reco::Track, reco::Vertex, pat::Muon
 +----------+----------+     - 11 ValueMaps for track parameters
            |
            v
 +---------------------+     PhysicsTools/ScoutingTranslator
 | Vertex Production   |     - PrimaryVertexProducer (DA_vect clustering)
 | (PV + SV + V0)      |     - Inclusive SV finder, merger, arbitrator
 +----------+----------+     - K0s / Lambda reconstruction
            |
     +------+------+
     |             |
     v             v
 +--------+   +--------+
 | AK4    |   | AK8    |    Jet reclustering from scouting PF candidates
 | R=0.4  |   | R=0.8  |    AK4: pT_min = 20 GeV
 | Reclus |   | Reclus |    AK8: pT_min = 170 GeV
 +---+----+   +---+----+
     |             |
     v             v
 +--------+   +--------+
 | JEC    |   | JEC    |    Jet Energy Corrections (AK4PFHLT / AK8PFHLT)
 | L1+L2  |   | L1+L2  |    L1FastJet + L2Relative + L3Absolute
 | +L3+Res|   | +L3+Res|    + L2L3Residual
 +---+----+   +---+----+
     |             |
     v             v
 +--------+   +--------+
 | ML     |   | ML     |    AK4: HLT ParticleNet (6 scores)
 | Tagging|   | Tagging|         + UParT custom (8 scores)
 | AK4    |   | AK8    |    AK8: HLT ParticleNet AK8 (10 scores)
 +---+----+   +---+----+
     |             |
     +------+------+
            |
            v
 +---------------------+
 | PAT Jet Producer    |     Combines JEC, discriminators, MC matching
 | (pat::Jet)          |     into unified PAT objects
 +----------+----------+
            |
            v
 +---------------------+
 | NanoAOD Tables      |     simplePATJetFlatTableProducer
 | (ROOT TTree)        |     ScoutingPFJetRecluster2, ScoutingFatPFJetRecluster2
 +----------+----------+     ScoutingPV, ScoutingSV, ScoutingKshort, ...
            |
            v
 +---------------------+
 | NANOAODSIM Output   |     LZMA-compressed ROOT file
 | (.root file)        |     ~100 flat tables of physics objects
 +---------------------+
```

### Generator-Level NanoAOD (MC Only)

In parallel with the scouting sequence, MC processing also runs
`nanogenSequence` to produce generator-level truth tables (GenPart,
GenJet, GenVisTau, etc.) via `PhysicsTools/NanoAOD/nanogen_cff`.

---

## Major CMSSW Packages

The system depends on six primary CMSSW package families:

### 1. PhysicsTools/ScoutingTranslator

**Source:** Cloned from `ArghyaRanjanDas/ScoutingTranslator` on GitHub.

Converts HLT-level scouting objects into standard reco/PAT formats and
orchestrates the full scouting reconstruction chain:

- `Run3ScoutingTranslation_cff.py` -- HLT packed -> reco conversion
- `Run3ScoutingPFJetRecluster_cff.py` -- AK4 reclustering + tagging
- `Run3ScoutingFatPFJetRecluster_cff.py` -- AK8 reclustering + tagging
- `Run3ScoutingSecondaryVertex_cff.py` -- PV/SV production
- `ScoutingNanoCustomisation_cff.py` -- NanoAOD table definitions
- C++ plugins for particle/track/vertex format translation

### 2. RecoBTag/ONNXRuntime

**Source:** Custom scouting-specific C++ plugins from Yao Yao's depot.

Contains the ONNX inference producer
`UnifiedParticleTransformerAK4ONNXJetTagsScoutingProducer` that runs the
UParT neural network model. Key differences from stock CMSSW:

- 6 input tensors instead of 8 (lost tracks disabled for scouting)
- Custom scouting-optimized batch processing
- GlobalCache model loading for thread safety

### 3. RecoBTag/FeatureTools

**Source:** Custom scouting-specific C++ plugins from Yao Yao's depot.

Feature extraction producer
`UnifiedParticleTransformerAK4TagInfoScoutingProducer` that converts raw
jet constituents into the fixed-size feature tensors required by the UParT
model (charged PF: 26x20, neutral PF: 25x10, SV: 5x15, plus pairwise
4-vectors).

### 4. RecoBTag/Combined

**Source:** Model data files copied from Yao Yao's depot.

Stores the ONNX model files:

- `data/UParTAK4/Scouting_HHbbtautau/V00/modelfile/model.onnx` (3.8 MB)
  -- Custom HH->bb(tau)(tau) model with tau discrimination
- `data/UParTAK4/Scouting/V00/modelfile/model.onnx` (3.7 MB)
  -- General-purpose scouting model (fallback)
- `data/HLT/ParticleNetAK4/V01/particle-net.onnx`
  -- HLT ParticleNet AK4 model (from stock CMSSW)

### 5. PhysicsTools/NanoAOD

**Source:** Stock CMSSW (from CVMFS).

Provides the base NanoAOD framework:

- `custom_run3scouting_cff.py` -- Base scouting NanoAOD customizations
  (`addScoutingPFCandidate`, `customiseScoutingNano`,
  `customiseScoutingNanoFromMini`)
- `nanogen_cff.py` -- Generator-level truth tables for MC
- `NanoAODOutputModule` -- Output file writing

### 6. PhysicsTools/PatAlgos

**Source:** Stock CMSSW (from CVMFS).

PAT (Physics Analysis Toolkit) infrastructure:

- `_patJets` base producer cloned for scouting jets
- `patJetCorrFactors` for jet energy corrections
- `patJetCharge`, `patJetFlavourAssociation` for jet properties
- `associatePatAlgosToolsTask` for task scheduling

---

## Three Processing Modes

### Standard MC (configs like MC_2024_NANO.py)

Standard NanoAOD production from MiniAOD. Uses stock CMSSW sequences for
offline-reconstructed jets, leptons, MET, etc. No scouting translation or
reclustering. Jet taggers use the standard offline UParT/ParticleNet with
full tracking and PUPPI weights.

**Input:** MiniAOD from grid production
**CMSSW step:** `-s NANO`
**Key sequences:** `nanoSequenceMC`

### Standard Data (configs like DATA_2024_NANO.py)

Same as standard MC but without generator-level truth, with different
global tags, and with data-specific JEC residuals applied.

**Input:** MiniAOD from prompt/reprocessed reconstruction
**CMSSW step:** `-s NANO`
**Key sequences:** `nanoSequence`

### Scouting (configs/MC_2024_Scouting.py)

The specialized mode documented in depth in this repository. Processes
HLT scouting objects that are embedded in MiniAOD (for MC) or arrive as
ScoutingPF NanoAOD (for data). Requires all custom packages listed above.

**Input:** MiniAOD with embedded scouting collections (MC) or
ScoutingPFRun3 data
**CMSSW step:** `-s NANO:@GENFromMini+@ScoutFromMini`
**Key sequences:** `nanogenSequence` + `scoutingNanoSequence`
**Customization chain:**
1. `addScoutingPFCandidate(process)` -- base scouting PF candidates
2. `customiseScoutingNano(process)` -- standard scouting tables
3. `customiseScoutingNanoFromMini(process)` -- MiniAOD-specific adjustments
4. `addAll(process)` -- ScoutingTranslator full pipeline (translation,
   reclustering, ML tagging, vertex finding, NanoAOD tables)
5. `customizeNanoGENFromMini(process)` -- generator truth from MiniAOD

---

## Role of This Repository vs. External CMSSW Code

### This Repository (Run3_nano_submission)

- **Configuration management:** All cmsRun config files for MC, Data, and
  Scouting processing modes
- **Dataset catalogs:** JSON files defining MC samples, Data runs, and
  Scouting datasets across 2022-2024
- **CRAB submission:** `crabby.py` script for grid job submission with
  dataset selection, year filtering, and scouting flag support
- **Customizations:** Analysis-specific NanoAOD variable additions
  (`customizations/customize.py`) for taus, boosted taus, primary vertices,
  lepton lifetime info, and IP covariance
- **Build orchestration:** `setup.sh` creates the CMSSW working area and
  links customizations
- **Documentation:** Architecture docs, NanoAOD output descriptions

### External CMSSW Code (cloned into cmssw/ working area)

- **PhysicsTools/ScoutingTranslator** -- Full scouting reconstruction chain
  (Python configs + C++ plugins) maintained in a separate GitHub repository
- **RecoBTag/{ONNXRuntime,FeatureTools}** -- Custom scouting UParT C++
  producers maintained in Yao Yao's development area at Purdue
- **RecoBTag/Combined/data/** -- ONNX model weights trained specifically
  for scouting HH->bb(tau)(tau)
- **Stock CMSSW packages** (from CVMFS via `scramv1 project`) -- Base
  NanoAOD framework, PAT algorithms, jet clustering, JEC infrastructure

### Separation of Concerns

```
Run3_nano_submission/           External CMSSW (cmssw/CMSSW_16_0_1/src/)
-------------------------       ------------------------------------------
configs/*.py                    PhysicsTools/ScoutingTranslator/
  (what to run)                   (how to translate + recluster)

customizations/customize.py     RecoBTag/ONNXRuntime/
  (analysis-specific vars)        (how to run ML inference)

datasets/*.json                 RecoBTag/FeatureTools/
  (which samples)                 (how to extract NN features)

crabby.py                       RecoBTag/Combined/data/
  (where to submit)               (trained model weights)

setup.sh                        Stock CMSSW on CVMFS
  (build orchestration)           (base framework)
```

The repository is designed so that the physics configuration lives here
while the heavy CMSSW C++/Python code is maintained externally and cloned
at build time. This allows the configuration repository to remain
lightweight while the complex producer code evolves independently.

---

## Key Technical Parameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| CMSSW version | 16_0_1 | el8_amd64_gcc13 architecture |
| Era | Run3_2024 | Defines detector conditions |
| Global tag (MC) | auto:phase1_2024_realistic | MC conditions |
| NanoAOD version | v15 | Compatible with NanoAODv15 schema |
| Threads | 4 | Default multi-threaded processing |
| Compression | LZMA level 9 | Maximum compression for output |
| Output tier | NANOAODSIM | Standard CMS data tier |
