# CMSSW Integration and Build Process

## Overview

The Run3_nano_submission repository builds a CMSSW_16_0_1 working area
that combines stock CMSSW packages from CVMFS, custom external packages
cloned from GitHub, and scouting-specific C++ plugins and ML model files
from collaborator development areas. This document describes the complete
build process, package layout, and how configurations reference the
assembled code.

---

## Build Process: setup.sh

The `setup.sh` script creates the CMSSW environment and links the
repository's customizations into the CMSSW Python path.

### Step-by-Step Breakdown

```bash
# Step 1: Set CMSSW version
CMSSW_VER=CMSSW_16_0_1

# Step 2: Initialize CMS software environment from CVMFS
source /cvmfs/cms.cern.ch/cmsset_default.sh

# Step 3: Check if already installed (idempotent)
if ! [ -f "$this_dir/cmssw/$CMSSW_VER/.installed" ]; then

    # Step 4: Create CMSSW project area
    mkdir -p "$this_dir/cmssw"
    cd "$this_dir/cmssw"
    scramv1 project CMSSW $CMSSW_VER
    #   Creates: cmssw/CMSSW_16_0_1/
    #            cmssw/CMSSW_16_0_1/src/
    #            cmssw/CMSSW_16_0_1/lib/
    #            cmssw/CMSSW_16_0_1/bin/
    #            (and other standard CMSSW directories)

    cd $CMSSW_VER/src
    eval `scramv1 runtime -sh`
    #   Sets up PATH, LD_LIBRARY_PATH, CMSSW_BASE, etc.

    # Step 5: Create symlink for custom Python code
    mkdir -p DAZSLE/DAZSLE
    ln -s "$this_dir/customizations" DAZSLE/DAZSLE/python
    #   Result: cmssw/CMSSW_16_0_1/src/DAZSLE/DAZSLE/python
    #           -> /path/to/Run3_nano_submission/customizations/
    #
    #   This makes 'from DAZSLE.DAZSLE.customize import ...'
    #   importable within CMSSW Python configs.

    # Step 6: Build (base only, no external packages yet)
    scram b -j8
    cmsenv

    # Step 7: Mark as installed
    touch "$this_dir/cmssw/$CMSSW_VER/.installed"

else
    # Already installed: just set up environment
    cd "$this_dir/cmssw/$CMSSW_VER/"
    cmsenv
fi
```

### Post-setup.sh: External Package Installation

After `setup.sh` completes, the user must manually install the external
scouting packages. This two-phase approach keeps `setup.sh` lightweight
and allows the external packages to be updated independently.

```bash
cd cmssw/CMSSW_16_0_1/src

# 1. Clone ScoutingTranslator
git clone https://github.com/ArghyaRanjanDas/ScoutingTranslator \
    PhysicsTools/ScoutingTranslator

# 2. Copy custom RecoBTag C++ plugins
cp -r /depot/cms/private/users/yao317/Analysis/HHtoBBTautau/cmssw/tmp/\
CMSSW_16_0_1/src/RecoBTag/ONNXRuntime RecoBTag/
cp -r /depot/cms/private/users/yao317/Analysis/HHtoBBTautau/cmssw/tmp/\
CMSSW_16_0_1/src/RecoBTag/FeatureTools RecoBTag/

# 3. Copy ONNX model files
mkdir -p RecoBTag/Combined/data/UParTAK4/Scouting_HHbbtautau/V00/modelfile
mkdir -p RecoBTag/Combined/data/UParTAK4/Scouting/V00/modelfile
cp /depot/cms/private/users/yao317/.../Scouting_HHbbtautau/V00/modelfile/\
model.onnx RecoBTag/Combined/data/UParTAK4/Scouting_HHbbtautau/V00/modelfile/
cp /depot/cms/private/users/yao317/.../Scouting/V00/modelfile/\
model.onnx RecoBTag/Combined/data/UParTAK4/Scouting/V00/modelfile/

# 4. Build everything (compiles C++ plugins, registers Python modules)
scram b -j8
```

---

## External CMSSW Packages

### 1. PhysicsTools/ScoutingTranslator

**Source:** `https://github.com/ArghyaRanjanDas/ScoutingTranslator`
**Installed to:** `cmssw/CMSSW_16_0_1/src/PhysicsTools/ScoutingTranslator/`

```
PhysicsTools/ScoutingTranslator/
  python/
    Run3ScoutingTranslation_cff.py        HLT->reco translation modules
    Run3ScoutingPFJet_cff.py              Direct scouting PF jets
    Run3ScoutingPFJetRecluster_cff.py     AK4 reclustering + UParT/PNet
    Run3ScoutingFatPFJetRecluster_cff.py  AK8 reclustering + HLT PNet
    Run3ScoutingSecondaryVertex_cff.py    PV/SV reconstruction
    OnlineBeamSpot_cff.py                 Online beam spot
    ScoutingNanoCustomisation_cff.py      NanoAOD table definitions + addAll()
    common_cff.py                         Shared variable definitions
  plugins/
    Run3ScoutingParticle2RecoPFCandidateProducer.cc
    Run3ScoutingParticleMatchTrackIndexProducer.cc
    Run3ScoutingLostTrackProducer.cc
    Run3ScoutingElectron2PatElectronProducer.cc
    SimpleTranslationProducer.cc
  src/
    TranslationToRecoFormat.cc            createRecoPFCandidate(), createRecoTrack()
    TranslationToPatFormat.cc             PAT conversion helpers
    Run3ScoutingUtils.cc                  hasTrack() utility
  interface/
    TranslationToRecoFormat.h
    TranslationToPatFormat.h
    Run3ScoutingUtils.h
  BuildFile.xml                           SCRAM build dependencies
```

This package provides the complete scouting reconstruction chain:
translation from HLT packed formats, jet reclustering, ML tagger
integration, vertex reconstruction, and NanoAOD table customization.

### 2. RecoBTag/ONNXRuntime (Custom Scouting Version)

**Source:** Yao Yao's depot at Purdue:
`/depot/cms/private/users/yao317/Analysis/HHtoBBTautau/cmssw/tmp/CMSSW_16_0_1/src/RecoBTag/ONNXRuntime`
**Installed to:** `cmssw/CMSSW_16_0_1/src/RecoBTag/ONNXRuntime/`

Contains the scouting-specific ONNX inference producer:

```
RecoBTag/ONNXRuntime/
  plugins/
    UnifiedParticleTransformerAK4ONNXJetTagsScoutingProducer.cc
  interface/
    tensor_fillers.h
    tensor_configs.h
  python/
    pfUnifiedParticleTransformerAK4_cff.py
  BuildFile.xml
```

This package **overrides** the stock CMSSW RecoBTag/ONNXRuntime. The
scouting-specific producer has 6 input tensors (vs. 8 in stock) because
lost tracks are not available in scouting data. It uses fixed tensor
shapes and single-jet-per-call inference.

### 3. RecoBTag/FeatureTools (Custom Scouting Version)

**Source:** Same Yao Yao depot as ONNXRuntime.
**Installed to:** `cmssw/CMSSW_16_0_1/src/RecoBTag/FeatureTools/`

Contains the scouting-specific feature extraction producer:

```
RecoBTag/FeatureTools/
  plugins/
    UnifiedParticleTransformerAK4TagInfoScoutingProducer.cc
  interface/
    ChargedCandidateConverter.h
    NeutralCandidateConverter.h
    SecondaryVertexConverter.h
  python/
    pfUnifiedParticleTransformerAK4TagInfos_cfi.py
  BuildFile.xml
```

Extracts 6 tensor groups per jet:
- Charged PF candidates: [26 x 20] features + [26 x 4] pairwise
- Neutral PF candidates: [25 x 10] features + [25 x 4] pairwise
- Secondary vertices: [5 x 15] features + [5 x 4] pairwise

### 4. RecoBTag/Combined (Model Data Only)

**Source:** ONNX model files from Yao Yao's depot.
**Installed to:** `cmssw/CMSSW_16_0_1/src/RecoBTag/Combined/data/`

```
RecoBTag/Combined/data/UParTAK4/
  Scouting_HHbbtautau/V00/modelfile/
    model.onnx                  3.8 MB, custom HH->bbtautau model
  Scouting/V00/modelfile/
    model.onnx                  3.7 MB, general-purpose scouting model
```

The HLT ParticleNet models are provided by stock CMSSW:

```
RecoBTag/Combined/data/HLT/
  ParticleNetAK4/V01/
    particle-net.onnx           HLT PNet AK4 model
    preprocess.json             Feature preprocessing config
```

### 5. DAZSLE/DAZSLE (Symlink to Repository Customizations)

**Source:** Symlink to `Run3_nano_submission/customizations/`
**Installed to:** `cmssw/CMSSW_16_0_1/src/DAZSLE/DAZSLE/python/`

```
DAZSLE/DAZSLE/python/  ->  Run3_nano_submission/customizations/
  customize.py              Analysis-specific NanoAOD customizations:
                              - customizeTaus(): extra tau variables
                              - customizeBoostedTaus(): boosted tau cuts
                              - customizePV(): extended vertex info
                              - addIPCovToLeptons(): IP covariance matrix
                              - addTrackVarsToTimeLifeInfo()
  __init__.py               (if present, makes it a Python package)
```

---

## Relationship Between Repository and CMSSW Working Area

### Directory Layout

```
Run3_nano_submission/                  <-- This repository (git tracked)
  setup.sh                             Build script
  configs/                             cmsRun configuration files
    MC_2024_Scouting.py                Scouting MC config
    MC_2024_NANO.py                    Standard MC config
    DATA_2024_NANO.py                  Standard Data config
    ...
  customizations/                      Analysis-specific Python code
    customize.py
  datasets/                            JSON dataset catalogs
  crabby.py                            CRAB submission script
  des/                                 Design documentation

  cmssw/                               <-- CMSSW working area (NOT git tracked)
    CMSSW_16_0_1/
      src/
        PhysicsTools/
          ScoutingTranslator/          (cloned from GitHub)
          NanoAOD/                     (stock, from CVMFS)
          PatAlgos/                    (stock, from CVMFS)
        RecoBTag/
          ONNXRuntime/                 (custom scouting, from depot)
          FeatureTools/                (custom scouting, from depot)
          Combined/                    (model data, from depot + stock)
        DAZSLE/DAZSLE/python/          (symlink to customizations/)
      lib/                             Compiled shared libraries
      bin/                             Compiled executables
      .installed                       Installation marker file
```

### Key Design Decisions

**Why symlink customizations instead of copying?**
The symlink (`DAZSLE/DAZSLE/python -> customizations/`) means edits to
`customizations/customize.py` in the git-tracked repository are
immediately visible to CMSSW without rebuilding. This supports rapid
iteration on NanoAOD variable definitions.

**Why is cmssw/ not git-tracked?**
The CMSSW working area contains large compiled binaries, stock CMSSW
symlinks, and site-specific paths. It is built locally from the
instructions in `setup.sh` and the README.

**Why are RecoBTag packages copied from a depot instead of cloned?**
The scouting-specific C++ producers are under active development and not
yet in a public repository. They are maintained in Yao Yao's development
area at Purdue (`/depot/cms/`). Once stabilized, they may be contributed
upstream to CMSSW or hosted on GitHub.

---

## Git Branch Strategy

### Repository Branches

The primary development branch for scouting work is:

```
NanoAODv15_151_Scouting_PAF
```

This branch name encodes:
- **NanoAODv15** -- Target NanoAOD schema version (v15)
- **151** -- CMSSW generation family (15X -> CMSSW_16_0_1 uses 150X global tags)
- **Scouting** -- Scouting-specific features enabled
- **PAF** -- Purdue Analysis Facility deployment target

The `main` branch contains the stable standard (non-scouting) NanoAOD
production configuration.

### ScoutingTranslator Branch

The ScoutingTranslator package is cloned from the default branch of:

```
https://github.com/ArghyaRanjanDas/ScoutingTranslator
```

This is a personal fork maintained by the repository author, containing
scouting-specific customizations not yet merged into any central CMS
repository.

### Recent Commit History Context

Recent commits on the scouting branch reflect the integration work:
- `fae94ce` -- JSON updated with data and MC dataset paths
- `253fd3a` -- Adding latest dataset updates
- `82bd322` -- Updating config files
- `8a33085` -- Fixing trigger branches in scouting sample
- `88a0816` -- Working test config for scouting

---

## How Configs Reference External Producers

### Python Import Chain

The scouting config `MC_2024_Scouting.py` loads external code through
CMSSW's Python module system:

```python
# 1. Load base scouting sequences (from stock CMSSW on CVMFS)
process.load('PhysicsTools.NanoAOD.custom_run3scouting_cff')

# 2. Import stock scouting customization functions
from PhysicsTools.NanoAOD.custom_run3scouting_cff import (
    addScoutingPFCandidate,
    customiseScoutingNano,
    customiseScoutingNanoFromMini
)

# 3. Apply stock customizations
process = addScoutingPFCandidate(process)
process = customiseScoutingNano(process)
process = customiseScoutingNanoFromMini(process)

# 4. Import ScoutingTranslator (from cloned GitHub repo)
from PhysicsTools.ScoutingTranslator.ScoutingNanoCustomisation_cff import addAll

# 5. Apply full scouting reconstruction pipeline
process = addAll(process)
#   addAll() internally loads:
#     - Run3ScoutingTranslation_cff (translation producers)
#     - Run3ScoutingSecondaryVertex_cff (vertex producers)
#     - Run3ScoutingPFJetRecluster_cff (AK4 + taggers)
#     - Run3ScoutingFatPFJetRecluster_cff (AK8 + taggers)
#     - OnlineBeamSpot_cff
#     - NanoAOD table producers
#   Each of these loads C++ plugins registered via BuildFile.xml

# 6. Import generator-level customization (stock CMSSW)
from PhysicsTools.NanoAOD.nanogen_cff import customizeNanoGENFromMini
process = customizeNanoGENFromMini(process)
```

### C++ Plugin Registration

When `scram b` compiles the working area, it:

1. Reads `BuildFile.xml` in each package to determine dependencies
2. Compiles C++ sources into shared libraries in `lib/`
3. Registers EDM plugin factories so that Python `cms.EDProducer('Name')`
   can find the compiled C++ code at runtime

For example, when the Python config references:

```python
UnifiedParticleTransformerAK4ONNXJetTagsScoutingProducer
```

CMSSW looks up this class name in the plugin registry, finds it was
compiled from `RecoBTag/ONNXRuntime/plugins/`, and loads the shared
library.

### ONNX Model File Resolution

Model paths in Python configs use `cms.FileInPath()`, which resolves
relative paths against the CMSSW search path:

```python
model_path = cms.FileInPath(
    'RecoBTag/Combined/data/UParTAK4/Scouting_HHbbtautau/V00/modelfile/model.onnx'
)
```

CMSSW searches for this file in order:
1. `$CMSSW_BASE/src/RecoBTag/Combined/data/...` (local working area)
2. `$CMSSW_RELEASE_BASE/src/RecoBTag/Combined/data/...` (stock release)

Since we copy the model files to the local `src/` directory, they are
found in step 1, overriding any stock models.

---

## Build Linking: How Everything Connects

### Compilation Order

SCRAM (CMSSW build system) automatically resolves dependencies:

```
1. Stock CMSSW libraries (from CVMFS, precompiled)
      |
      v
2. RecoBTag/FeatureTools  (depends on: DataFormats, FWCore, stock RecoBTag)
      |
      v
3. RecoBTag/ONNXRuntime   (depends on: FeatureTools, PhysicsTools/ONNXRuntime)
      |
      v
4. PhysicsTools/ScoutingTranslator  (depends on: RecoBTag, DataFormats,
      |                               PatAlgos, RecoJets, stock NanoAOD)
      v
5. DAZSLE/DAZSLE          (Python-only, no compilation needed)
```

### Runtime Module Resolution

At `cmsRun` execution time:

```
cmsRun configs/MC_2024_Scouting.py
  |
  +--> Python: process.load('PhysicsTools.NanoAOD.custom_run3scouting_cff')
  |      Resolves to: $CMSSW_RELEASE_BASE/python/PhysicsTools/NanoAOD/
  |
  +--> Python: from PhysicsTools.ScoutingTranslator.ScoutingNanoCustomisation_cff ...
  |      Resolves to: $CMSSW_BASE/src/PhysicsTools/ScoutingTranslator/python/
  |      (local working area overrides stock)
  |
  +--> C++: EDProducer plugins loaded from $CMSSW_BASE/lib/
  |      (compiled from RecoBTag/ONNXRuntime/plugins/, etc.)
  |
  +--> Data: cms.FileInPath('RecoBTag/Combined/data/...')
         Resolves to: $CMSSW_BASE/src/RecoBTag/Combined/data/
         (local model files)
```

---

## Environment Setup for Different Workflows

### Local Testing

```bash
cd Run3_nano_submission
./setup.sh                          # First time: builds CMSSW area
                                    # Subsequent: just sets environment
cmsRun configs/MC_2024_Scouting.py  # Run locally on a test file
```

### CRAB Grid Submission

The CRAB submission requires a specific environment setup order because
`crab-setup.sh` can conflict with other tools:

```bash
cd cmssw/CMSSW_16_0_1/src
source /cvmfs/cms.cern.ch/cmsset_default.sh
cmsenv
source /cvmfs/cms.cern.ch/common/crab-setup.sh
cd /path/to/Run3_nano_submission

# Submit scouting MC jobs
python3 crabby.py --year 2024 --dataset HHbbtt --scouting --make --submit
```

CRAB packages the entire CMSSW working area (including custom packages,
model files, and compiled libraries) into a sandbox that gets shipped to
grid worker nodes.

### DAS Client (Dataset Discovery)

```bash
pip3 install dbs3-client
# IMPORTANT: DAS client does not work after sourcing crab-setup.sh
```

---

## Platform and Version Requirements

| Component | Version | Notes |
|-----------|---------|-------|
| CMSSW | 16_0_1 | Required for Run3_2024 era support |
| Architecture | el8_amd64_gcc13 | Enterprise Linux 8, GCC 13 |
| OS | el8 or el9 | Only tested on these platforms |
| CVMFS | Required | For stock CMSSW and crab-setup |
| Python | 3.x | Included with CMSSW |
| ONNX Runtime | From CMSSW | PhysicsTools/ONNXRuntime |
| Global Tag (MC) | auto:phase1_2024_realistic | Detector conditions |
| Global Tag (Data) | auto:run3_data_prompt | Data conditions |

### Known Compatibility Notes

- CMSSW_16_0_1 upgraded from CMSSW_15_0_13 to support NanoAODv15 and
  the Run3_2024 era
- The el8_amd64_gcc13 scram architecture requires Enterprise Linux 8+
- Model ONNX files are architecture-independent (portable)
- The RecoBTag scouting plugins are not yet in stock CMSSW and must be
  copied manually from the collaborator depot
