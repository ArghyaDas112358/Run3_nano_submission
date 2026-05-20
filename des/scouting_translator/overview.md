# ScoutingTranslator Package: Overview

## Purpose

The `PhysicsTools/ScoutingTranslator` package converts HLT-level Run3 Scouting data
formats into standard CMS reconstruction (reco) and physics analysis toolkit (PAT)
objects. This translation is necessary because the CMS Scouting system stores
trigger-level objects in a compact, reduced-precision format that is incompatible
with standard offline reconstruction algorithms, jet clustering, b-tagging, and
NanoAOD table production.

For the HH->bb(tau)(tau) analysis, ScoutingTranslator enables the full chain from
packed HLT scouting objects through reclustered AK4/AK8 jets to advanced ML-based
flavor taggers (HLT ParticleNet and custom UParT), producing NanoAOD output with
8 flavor-discrimination scores per jet.

## Package Directory Structure

```
PhysicsTools/ScoutingTranslator/
|
+-- interface/
|   +-- TranslationToRecoFormat.h      # Headers for createRecoPFCandidate(), createRecoTrack(), etc.
|   +-- TranslationToPatFormat.h       # Headers for PAT conversion (createPatMuon, createPatJet, etc.)
|   +-- Run3ScoutingUtils.h            # Utility: hasTrack() for track presence checks
|
+-- src/
|   +-- TranslationToRecoFormat.cc     # Core conversion: PFCandidate, Track, Jet, Vertex, Electron, Photon
|   +-- TranslationToPatFormat.cc      # PAT-level conversion helpers
|   +-- Run3ScoutingUtils.cc           # hasTrack() implementation (PDG ID + normchi2 filtering)
|
+-- plugins/
|   +-- Run3ScoutingParticle2RecoPFCandidateProducer.cc   # PF candidate + 11 ValueMaps + track collections
|   +-- Run3ScoutingParticleMatchTrackIndexProducer.cc    # Delta-R matching of PF particles to scouting tracks
|   +-- Run3ScoutingLostTrackProducer.cc                  # Finds scouting tracks not matched to PF particles
|   +-- Run3ScoutingElectron2PatElectronProducer.cc       # Electron translation (GSF track + supercluster)
|   +-- SimpleTranslationProducer.cc                      # Generic template for simple 1-to-1 translations
|   +-- SimpleFlatTableProducerExtraPlugins.cc            # NanoAOD table helper plugins
|   +-- BuildFile.xml
|
+-- python/
|   +-- Run3ScoutingTranslation_cff.py           # HLT -> reco object translation chain
|   +-- Run3ScoutingPFJet_cff.py                 # Direct scouting PF jets (no reclustering)
|   +-- Run3ScoutingPFJetRecluster_cff.py        # AK4 reclustering + HLT PNet + UParT tagging
|   +-- Run3ScoutingFatPFJetRecluster_cff.py     # AK8 fat jet reclustering + HLT PNet AK8
|   +-- Run3ScoutingSecondaryVertex_cff.py       # Primary + secondary vertex reconstruction
|   +-- Run3ScoutingV0_cff.py                    # K0short and Lambda0 reconstruction
|   +-- OnlineBeamSpot_cff.py                    # Online beam spot extraction
|   +-- ScoutingNanoCustomisation_cff.py         # High-level NanoAOD customization API
|   +-- common_cff.py                            # Shared PFJet variable definitions
|
+-- BuildFile.xml
```

## C++ EDProducer Inventory

The package provides six primary producer types, plus a generic template producer
that handles simple one-to-one translations.

### Dedicated Producers

| Producer Class | Plugin Name | Input Type | Output Type |
|---|---|---|---|
| `Run3ScoutingParticle2RecoPFCandidateProducer` | (same) | `Run3ScoutingParticleCollection` | `reco::PFCandidateCollection` + 2 TrackCollections + 11 ValueMaps |
| `Run3ScoutingParticleMatchTrackIndexProducer` | (same) | PF + Track collections | `ValueMap<int>` (track index per PF particle) |
| `Run3ScoutingLostTrackProducer` | (same) | PF + Track + MatchIndex | `Run3ScoutingTrackCollection` (unmatched tracks) |
| `Run3ScoutingElectron2PatElectronProducer` | (same) | `Run3ScoutingElectronCollection` | `pat::ElectronCollection` |

### Template-Based Simple Producers (SimpleTranslationProducer)

| Type Alias | Input | Output |
|---|---|---|
| `SimpleRun3ScoutingMuon2PatMuonProducer` | `Run3ScoutingMuon` | `pat::Muon` |
| `SimpleRun3ScoutingPFJet2RecoPFJetProducer` | `Run3ScoutingPFJet` | `reco::PFJet` |
| `SimpleRun3ScoutingPFJet2PatJetProducer` | `Run3ScoutingPFJet` | `pat::Jet` |
| `SimpleRun3ScoutingElectron2PatElectronProducer` | `Run3ScoutingElectron` | `pat::Electron` |
| `SimpleRun3ScoutingPhoton2PatPhotonProducer` | `Run3ScoutingPhoton` | `pat::Photon` |
| `SimpleRun3ScoutingTrack2RecoTrackProducer` | `Run3ScoutingTrack` | `reco::Track` |
| `SimpleRun3ScoutingVertex2RecoVertexProducer` | `Run3ScoutingVertex` | `reco::Vertex` |

The `SimpleTranslationProducer<TIn, TOut>` template loops over input objects and
calls a type-specialized `create()` function for each. The actual conversion logic
lives in `TranslationToRecoFormat.cc` and `TranslationToPatFormat.cc`.

## Position in the Overall Pipeline

```
MiniAODv6 Input (contains embedded HLT scouting collections)
    |
    v
[1] ScoutingTranslator: Translation Layer
    |   HLT packed scouting -> reco::PFCandidate, reco::Track, reco::Vertex, pat::Muon
    |
    v
[2] ScoutingTranslator: Vertex Reconstruction
    |   PrimaryVertexProducer -> Inclusive Vertex Finder -> Merged SVs
    |
    v
[3] ScoutingTranslator: Jet Reclustering
    |   AK4 (R=0.4, pT>20 GeV) + AK8 (R=0.8, pT>170 GeV)
    |   from translated PF candidates using FastJet
    |
    v
[4] ScoutingTranslator: ML Tagger Inference
    |   HLT ParticleNet (6 outputs) + custom UParT (8 outputs) via ONNX Runtime
    |
    v
[5] ScoutingTranslator: PAT Jet Production
    |   JEC, jet charge, discriminator attachment, MC flavor matching
    |
    v
[6] ScoutingTranslator: NanoAOD Tables
    |   FlatTable producers -> ScoutingPFJetRecluster2, ScoutingFatPFJetRecluster2,
    |   ScoutingPV, ScoutingSV, ScoutingKshort, ScoutingLambda, OnlineBeamSpot
    |
    v
NANOAODSIM Output (.root)
```

## Entry Point: `addAll(process)`

The primary entry point for the full scouting NanoAOD pipeline is the `addAll()`
function in `ScoutingNanoCustomisation_cff.py`. Calling `process = addAll(process)`
from the top-level config (`MC_2024_Scouting.py`) loads all config fragments, creates
all producer tasks, builds NanoAOD flat tables, and registers everything into the
CMSSW process schedule via two task groups:

- **`scoutingNanoTaskCommon`** -- runs for all events (data and MC)
- **`scoutingNanoTaskMC`** -- runs only for MC (gen-jet matching, flavor association, gen tables)

## Key Dependencies

- **CMSSW 16_0_1** (`el8_amd64_gcc13` architecture)
- **RecoBTag/ONNXRuntime** -- ONNX inference producers for ParticleNet and UParT
- **RecoBTag/Combined** -- Model weights and preprocessing JSON files
- **RecoJets/JetProducers** -- `ak4PFJets` for jet clustering
- **RecoVertex/AdaptiveVertexFinder** -- Inclusive vertex finder for secondary vertices
- **PhysicsTools/PatAlgos** -- PAT jet, muon, electron producers
- **PhysicsTools/NanoAOD** -- NanoAOD flat table infrastructure

## CMSSW Location

The working copy of ScoutingTranslator used in this project resides at:
```
/depot/cms/private/users/yao317/Analysis/HHtoBBTautau/cmssw/tmp/CMSSW_16_0_1/src/PhysicsTools/ScoutingTranslator/
```
Forked from `ArghyaRanjanDas/ScoutingTranslator` on GitHub.
