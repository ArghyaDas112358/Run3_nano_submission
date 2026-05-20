# Data Flow: HLT Scouting to NanoAOD

## Overview

This document traces the complete data flow from HLT scouting packed
formats through translation, reclustering, ML tagging, and NanoAOD table
production. Each stage lists the CMSSW producer module, its input
collections, and its output collections.

---

## Stage 1: HLT Packed Scouting Objects (Input)

HLT scouting data arrives in compact, reduced-precision formats designed
for high-rate trigger output. These are stored as Run3Scouting* data
products in MiniAOD.

```
Input Collections from HLT:
  hltScoutingPFPacker             -> Run3ScoutingParticleCollection
  hltScoutingTrackPacker          -> Run3ScoutingTrackCollection
  hltScoutingPrimaryVertexPacker  -> Run3ScoutingVertexCollection
  hltScoutingMuonPackerNoVtx      -> Run3ScoutingMuonCollection
  hltScoutingMuonPackerVtx        -> Run3ScoutingMuonCollection
```

These packed objects have limited precision (e.g., relative track
encoding, reduced vertex info) and cannot be used directly by standard
reconstruction algorithms. The ScoutingTranslator converts them to
standard reco formats.

---

## Stage 2: ScoutingTranslator Unpacking

**Config:** `PhysicsTools/ScoutingTranslator/python/Run3ScoutingTranslation_cff.py`

### 2a. Track-Particle Matching

```
Producer: Run3ScoutingParticleMatchTrackIndexProducer
Input:    hltScoutingPFPacker, hltScoutingTrackPacker
Output:   scoutingParticleMatchTrackIndex  (ValueMap<int>)

Purpose:  Match each PF particle to its closest scouting track by
          delta-R, enforce uniqueness, produce index mapping.
```

### 2b. PF Candidate Conversion

```
Producer: Run3ScoutingParticle2RecoPFCandidateProducer
Input:    hltScoutingPFPacker
          hltScoutingTrackPacker
          scoutingParticleMatchTrackIndex
          hltScoutingPrimaryVertexPacker:primaryVtx (optional)
Output:   recoScoutingPFCandidate            (reco::PFCandidateCollection)
          recoScoutingPFCandidate:pftrack     (reco::TrackCollection)
          recoScoutingPFCandidate:track       (reco::TrackCollection)
          + 11 ValueMaps keyed on recoScoutingPFCandidate:
            vertexIndex, normchi2, dz, dxy, dzsig, dxysig,
            lostInnerHits, quality, trkPt, trkEta, trkPhi

Logic:    - Converts PF particles to reco::PFCandidate objects
          - Creates reco::Track for each charged particle
          - Handles relative track encoding:
              if relative_trk_vars: trkPt = trk_pt + particle_pt
          - Filters trackless particles (photons pdgId=22,
            K0L pdgId=130, HF hadrons pdgId=1/2, normchi2>=999)
```

### 2c. Direct PF Jet Conversion

```
Producer: SimpleRun3ScoutingPFJet2RecoPFJetProducer
Input:    hltScoutingPFPacker
Output:   recoScoutingPFJet  (reco::PFJetCollection)
```

### 2d. Track Conversion

```
Producer: SimpleRun3ScoutingTrack2RecoTrackProducer
Input:    hltScoutingTrackPacker
Output:   recoScoutingTrack  (reco::TrackCollection)
```

### 2e. Lost Track Recovery

```
Producer: Run3ScoutingLostTrackProducer
Input:    hltScoutingPFPacker, hltScoutingTrackPacker,
          scoutingParticleMatchTrackIndex
Output:   scoutingLostTrack  (Run3ScoutingTrackCollection)

Producer: SimpleRun3ScoutingTrack2RecoTrackProducer  (second instance)
Input:    scoutingLostTrack
Output:   recoScoutingLostTrack  (reco::TrackCollection)
```

### 2f. Track Merging

```
Producer: CandMerger
Input:    recoScoutingPFCandidate:track, recoScoutingLostTrack
Output:   recoScoutingTrackMerged  (reco::CandidateCollection)
```

### 2g. Primary Vertex Conversion

```
Producer: SimpleRun3ScoutingVertex2RecoVertexProducer
Input:    hltScoutingPrimaryVertexPacker:primaryVtx
Output:   recoScoutingPrimaryVertex  (reco::VertexCollection)
```

### 2h. Muon Conversion

```
Producer: SimpleRun3ScoutingMuon2PatMuonProducer  (x2 instances)
Input:    hltScoutingMuonPackerNoVtx / hltScoutingMuonPackerVtx
Output:   patScoutingMuonNoVtx / patScoutingMuonVtx  (pat::MuonCollection)
```

### Translation Summary

```
HLT Packed                   Reco Format
-----------                  -----------
hltScoutingPFPacker     -->  recoScoutingPFCandidate  (+ ValueMaps)
hltScoutingTrackPacker  -->  recoScoutingTrack
                             recoScoutingLostTrack
                             recoScoutingTrackMerged
hltScoutingPrimaryVtx   -->  recoScoutingPrimaryVertex
hltScoutingMuonPacker*  -->  patScoutingMuon{NoVtx,Vtx}
```

---

## Stage 3: Vertex Reconstruction

**Config:** `PhysicsTools/ScoutingTranslator/python/Run3ScoutingSecondaryVertex_cff.py`

### 3a. Primary Vertex Production (from tracks)

```
Step 1 - Vertex Fitting:
  Producer: PrimaryVertexProducer
  Input:    recoScoutingPFCandidate:track, onlineBeamSpot
  Output:   scoutingVerticesPF  (reco::VertexCollection)
  Params:   DA_vect adaptive clustering, minSiliconHits=5,
            minPixelHits=2, minPt=0

Step 2 - Quality Filtering:
  Producer: PrimaryVertexObjectFilter
  Input:    scoutingVerticesPF
  Output:   scoutingVerticesPFSelector
  Params:   minNdof=4.0, maxRho=2.0, maxZ=24.0

Step 3 - Fake Removal:
  Producer: VertexSelector
  Input:    scoutingVerticesPFSelector
  Output:   scoutingVerticesPFFilter
  Cut:      !isFake
```

### 3b. Secondary Vertex Production

```
Step 1 - SV Finding:
  Producer: inclusiveCandidateVertexFinder
  Input:    recoScoutingPFCandidate, scoutingVerticesPFFilter,
            onlineBeamSpot
  Output:   scoutingDeepInclusiveVertexFinderPF
  Params:   minHits=8 (HLT default)

Step 2 - SV Merging:
  Producer: candidateVertexMerger
  Input:    scoutingDeepInclusiveVertexFinderPF
  Output:   scoutingDeepInclusiveSecondaryVerticesPF

Step 3 - Track Arbitration:
  Producer: candidateVertexArbitrator
  Input:    scoutingDeepInclusiveSecondaryVerticesPF,
            scoutingVerticesPFFilter
  Output:   scoutingDeepTrackVertexArbitratorPF

Step 4 - Final Merge:
  Producer: candidateVertexMerger
  Input:    scoutingDeepTrackVertexArbitratorPF
  Output:   scoutingDeepInclusiveMergedVerticesPF
  Params:   maxFraction=0.2, minSignificance=10.0
```

---

## Stage 4: AK4 Jet Reclustering (9-Step Pipeline)

**Config:** `PhysicsTools/ScoutingTranslator/python/Run3ScoutingPFJetRecluster_cff.py`

### Step 1: Jet Clustering

```
Producer: ak4PFJets (cloned)
Input:    recoScoutingPFCandidate
Output:   recoScoutingPFJetRecluster  (reco::PFJetCollection)
Params:   R=0.4, jetPtMin=20 GeV, src=recoScoutingPFCandidate
```

### Step 2: Jet Energy Corrections

```
Producer: patJetCorrFactors (cloned)
Input:    recoScoutingPFJetRecluster, recoScoutingPrimaryVertex
Output:   scoutingPFJetReclusterCorrFactors
Params:   payload=AK4PFHLT
          levels=[L1FastJet, L2Relative, L3Absolute, L2L3Residual]
```

### Step 3: Track Association

```
Producer: ak4JetTracksAssociatorAtVertex (cloned)
Input:    recoScoutingPFJetRecluster, recoScoutingTrack,
          scoutingVerticesPF
Output:   scoutingPFJetReclusterTracksAssociatorAtVertex
Params:   coneSize=0.4
```

### Step 4: Jet Charge

```
Producer: patJetCharge (cloned)
Input:    scoutingPFJetReclusterTracksAssociatorAtVertex
Output:   scoutingPFJetReclusterCharge
```

### Step 5: PV Association

```
Producer: PFCandidatePrimaryVertexSorter
Input:    recoScoutingPFJetRecluster, recoScoutingPFCandidate,
          scoutingVerticesPFFilter
Output:   scoutingPFJetReclusterPrimaryVertexAssociation  (ValueMap)
Params:   minJetPt=5.0 (lowered from 25.0 for scouting),
          maxJetDeltaR=0.5, maxDzForPrimaryAssignment=0.1,
          useVertexFit=True, fallback=True
```

### Step 6: HLT ParticleNet Feature Extraction

```
Producer: DeepBoostedJetTagInfoProducer
Input:    recoScoutingPFJetRecluster, recoScoutingPFCandidate,
          scoutingDeepInclusiveMergedVerticesPF,
          scoutingVerticesPFFilter,
          scoutingPFJetReclusterPrimaryVertexAssociation
Output:   scoutingPFJetReclusterHLTParticleNetJetTagInfos
Params:   jet_radius=0.4, min_jet_pt=5.0, max_jet_eta=2.6,
          use_hlt_features=True, use_scouting_features=False
```

### Step 7: HLT ParticleNet ONNX Inference

```
Producer: BoostedJetONNXJetTagsProducer
Input:    scoutingPFJetReclusterHLTParticleNetJetTagInfos
Output:   scoutingPFJetReclusterHLTParticleNetONNXJetTags
          (6 JetTag sub-collections: probtauhp, probtauhm,
           probb, probc, probuds, probg)
Model:    RecoBTag/Combined/data/HLT/ParticleNetAK4/V01/particle-net.onnx
```

### Step 8: UParT Feature Extraction + ONNX Inference

```
Feature Extraction:
  Producer: UnifiedParticleTransformerAK4TagInfoProducer
  Input:    recoScoutingPFJetRecluster, recoScoutingPFCandidate,
            scoutingVerticesPF, scoutingDeepInclusiveMergedVerticesPF
  Output:   scoutingPFJetReclusterPFUnifiedParticleTransformerAK4TagInfos
  Params:   jet_radius=0.4, min_candidate_pt=0.1, max_jet_eta=2.5,
            losttracks="" (disabled), puppi_value_map="" (fallback=1.0),
            fallback_vertex_association=True
  Tensors:  Charged PF [26 x 20], Neutral PF [25 x 10], SV [5 x 15],
            + pairwise 4-vectors [26x4, 25x4, 5x4]

ONNX Inference:
  Producer: UnifiedParticleTransformerAK4ONNXJetTagsScoutingProducer
  Input:    scoutingPFJetReclusterPFUnifiedParticleTransformerAK4TagInfos
  Output:   scoutingPFJetReclusterPFUnifiedParticleTransformerAK4Tags
            (8 JetTag sub-collections: probb, probbb, problepb,
             probc, probuds, probg, probtaum, probtaup)
  Model:    RecoBTag/Combined/data/UParTAK4/Scouting_HHbbtautau/V00/
            modelfile/model.onnx
  Inputs:   6 tensors (input_1 through input_6)
  Output:   ID_pred -> 8 flavor probabilities
```

### Step 9: PAT Jet Assembly

```
Producer: _patJets (cloned as patScoutingPFJetRecluster)
Input:    recoScoutingPFJetRecluster,
          scoutingPFJetReclusterCorrFactors,
          scoutingPFJetReclusterCharge,
          14 discriminator sources (6 HLT PNet + 8 UParT)
Output:   patScoutingPFJetRecluster  (pat::JetCollection)

MC-only additions:
  - scoutingPFJetReclusterGenJetMatch (gen-jet matching to slimmedGenJets)
  - scoutingPFJetReclusterFlavourAssociation (b/c/light hadron flavors)
```

---

## Stage 5: AK8 Fat Jet Reclustering

**Config:** `PhysicsTools/ScoutingTranslator/python/Run3ScoutingFatPFJetRecluster_cff.py`

Similar structure to AK4 but with larger cone size and different taggers:

```
Jet Clustering:    R=0.8, pT_min=170 GeV
JEC:               AK8PFHLT payload
HLT PNet AK8:     10 outputs (probHtt, probHtm, probHte, probHbb,
                   probHcc, probHqq, probHgg, probQCD2hf,
                   probQCD1hf, probQCD0hf)
UParT:             NOT applied to AK8 jets in current configuration
PAT output:        patScoutingFatPFJetRecluster
```

---

## Stage 6: NanoAOD Flat Table Production

**Config:** `PhysicsTools/ScoutingTranslator/python/ScoutingNanoCustomisation_cff.py`

### AK4 Reclustered Jet Table

```
Producer:  simplePATJetFlatTableProducer (cloned)
Input:     patScoutingPFJetRecluster
Table:     ScoutingPFJetRecluster2
Cut:       pt > 20 GeV

Variables:
  Kinematics:    pt, eta, phi, mass, area
  Composition:   chHEF, neHEF, chEmEF, neEmEF, muEF,
                 chHadMult, neHadMult, phoMult, eleMult, muMult, nConst
  JEC:           rawFactor = 1 - jecFactor('Uncorrected')
  Charge:        jetCharge

  HLT PNet (6):   Applied when pT>=5 and |eta|<=2.6, else -1
    hltPNet_probtauhp, hltPNet_probtauhm, hltPNet_probb,
    hltPNet_probc, hltPNet_probuds, hltPNet_probg

  UParT (8):       Applied when pT>=15 and |eta|<=2.5, else -1
    scoutUParT_probb, scoutUParT_probbb, scoutUParT_problepb,
    scoutUParT_probc, scoutUParT_probuds, scoutUParT_probg,
    scoutUParT_probtaum, scoutUParT_probtaup

MC-only Table:   ScoutingPFJetRecluster2MC
  genJetIdx (index into GenJet table)
  partonFlavour, hadronFlavour
```

### AK8 Fat Jet Table

```
Producer:  simplePATJetFlatTableProducer (cloned)
Input:     patScoutingFatPFJetRecluster
Table:     ScoutingFatPFJetRecluster2
Cut:       pt > 200 GeV

Variables:
  Kinematics + Composition (same structure as AK4)
  HLT PNet AK8 (10): probHtt, probHtm, probHte, probHbb, probHcc,
                      probHqq, probHgg, probQCD2hf, probQCD1hf, probQCD0hf
```

### Other Scouting Tables

```
ScoutingPV       -- Primary vertices (x, y, z, ndof, chi2)
ScoutingSV       -- Secondary vertices (pt, eta, phi, mass, dxy, dxysig,
                    d3d, d3dsig, ntracks)
ScoutingKshort   -- K0s candidates (V0 reconstruction)
ScoutingLambda   -- Lambda candidates (V0 reconstruction)
OnlineBeamSpot   -- Online beam spot position
ScoutingPFJet2   -- Direct (non-reclustered) scouting jets (basic kinematics only)
```

---

## The ValueMap Mechanism

CMSSW uses ValueMaps to associate derived quantities with collections
without modifying the original objects. This pattern is critical in the
scouting pipeline.

### How ValueMaps Work

A ValueMap<T> is a map from an edm::Ref (reference to an object in a
collection) to a value of type T. Producers create ValueMaps and store
them in the event; downstream consumers retrieve them by label.

### ValueMaps in the Scouting Pipeline

**Track parameter ValueMaps** (produced by
`Run3ScoutingParticle2RecoPFCandidateProducer`):

```
Collection: recoScoutingPFCandidate
ValueMaps (keyed on PFCandidate refs):
  recoScoutingPFCandidate:vertexIndex     -> int   (PV association)
  recoScoutingPFCandidate:normchi2        -> float (track chi2/ndof)
  recoScoutingPFCandidate:dz              -> float (longitudinal impact)
  recoScoutingPFCandidate:dxy             -> float (transverse impact)
  recoScoutingPFCandidate:dzsig           -> float (dz significance)
  recoScoutingPFCandidate:dxysig          -> float (dxy significance)
  recoScoutingPFCandidate:lostInnerHits   -> int   (missing pixel hits)
  recoScoutingPFCandidate:quality         -> int   (track quality flag)
  recoScoutingPFCandidate:trkPt           -> float (track pT)
  recoScoutingPFCandidate:trkEta          -> float (track eta)
  recoScoutingPFCandidate:trkPhi          -> float (track phi)
```

These ValueMaps are consumed by:
- The PV association producer (uses vertexIndex, dz)
- The UParT feature extractor (uses track impact parameters)
- The SV finder (uses track quality and kinematics)

**PV association ValueMap** (produced by
`PFCandidatePrimaryVertexSorter`):

```
Collection: scoutingPFJetReclusterPrimaryVertexAssociation
Key:        "original"
Maps:       PFCandidate -> best primary vertex assignment

Consumed by:
  - DeepBoostedJetTagInfoProducer (HLT PNet features)
  - UParT TagInfo producer (vertex association flag in features)
```

**Jet discriminator pattern** (alternative to ValueMap):

Jet taggers produce `reco::JetTagCollection` objects, which are
effectively a map from jet references to float scores. The PAT jet
producer reads these via `discriminatorSources` and attaches them as
`bDiscriminator("label:sublabel")` on the pat::Jet. The NanoAOD table
producer then accesses them:

```python
# In ScoutingNanoCustomisation_cff.py:
scoutUParT_probb = Var(
    "?(pt>=15)&&(abs(eta)<=2.5)?"
    "bDiscriminator('scoutingPFJetRecluster"
    "PFUnifiedParticleTransformerAK4Tags:probb'):-1",
    float, doc="scouting uParT b score", precision=10
)
```

---

## How Scouting Differs from Standard Reconstruction

### Input Data Quality

| Aspect | Standard (MiniAOD) | Scouting |
|--------|-------------------|----------|
| Track precision | Full offline | Reduced HLT |
| Track encoding | Absolute | Relative (trk_pt + particle_pt) |
| PF candidates | PUPPI-weighted | No PUPPI (weight=1.0 fallback) |
| Lost tracks | Available | Not available |
| Vertex info | Full refit | HLT primary vertex only |
| Trigger objects | All trigger paths | Scouting trigger only |

### Reconstruction Differences

| Step | Standard | Scouting |
|------|----------|----------|
| Jet clustering | From miniAOD PF | From translated scouting PF |
| JEC payload | AK4PFPuppi / AK4PFchs | AK4PFHLT |
| PV production | Offline-quality PV | Re-fit from scouting tracks |
| SV finding | Full tracking input | Scouting tracks (minHits=8) |
| b-tagging model | Standard UParT (8 inputs) | Scouting UParT (6 inputs) |
| Lost tracks | Input to tagger | Disabled (no scouting lost tracks) |
| PUPPI weights | From ValueMap | Fallback = 1.0 |
| Vertex association | From ValueMap | Fallback closest-dz method |

### ML Tagger Differences

| Feature | Standard UParT | Scouting UParT |
|---------|---------------|----------------|
| Input tensors | 8 (cpf, npf, sv, lt + 4-vectors) | 6 (cpf, npf, sv + 4-vectors) |
| Max charged PF | 26 | 26 |
| Max neutral PF | 25 | 25 |
| Max lost tracks | 5 | 0 (disabled) |
| Max SV | 5 | 5 |
| Model | Standard PUPPI V00/V01 | Scouting_HHbbtautau V00 |
| Output classes | 30+ | 8 (with tau discrimination) |
| Dynamic axes | True (V01) | False (fixed shapes) |
| PUPPI weight | Required | Fallback = 1.0 |
| Neutral feature #4 | hadFrac | Constant 1.0 (scouting compat) |

### Key Physics Implication

Scouting data enables access to events at lower pT thresholds than
standard triggers. For HH->bb(tau)(tau), this means sensitivity to
softer Higgs decay products. The trade-off is reduced reconstruction
precision, which the custom UParT model is trained to handle by learning
scouting-specific feature distributions.

---

## Complete Data Flow Diagram

```
hltScoutingPFPacker ----+
hltScoutingTrackPacker -+---> ScoutingTranslator
hltScoutingPVPacker ----+     |
                              v
                    recoScoutingPFCandidate (+ 11 ValueMaps)
                    recoScoutingTrack
                    recoScoutingPrimaryVertex
                              |
              +---------------+---------------+
              |               |               |
              v               v               v
         PV Producer     SV Pipeline     AK4 Clustering
              |               |               |
              v               v               v
     scoutingVerticesPF  scoutingDeep    recoScoutingPF
     (-> Filter)         InclusiveMerged JetRecluster
              |          VerticesPF           |
              +-------+--+---+               |
                      |      |               |
                      v      v               v
              HLT PNet     UParT        JEC (AK4PFHLT)
              TagInfo      TagInfo           |
                 |            |              v
                 v            v         Track Assoc
              PNet ONNX   UParT ONNX   PV Assoc
              (6 scores)  (8 scores)   Jet Charge
                 |            |              |
                 +-----+------+--------------+
                       |
                       v
                patScoutingPFJetRecluster  (pat::Jet)
                       |
                       v
              ScoutingPFJetRecluster2Table  (NanoAOD)
                       |
                       v
                  NANOAODSIM .root file
```
