# AK4 Jet Reclustering Pipeline

## Overview

The AK4 reclustering pipeline (`Run3ScoutingPFJetRecluster_cff.py`) takes translated
scouting PF candidates and builds physics-analysis-ready AK4 jets with two independent
ML taggers attached. This is the primary jet collection for the HH->bb(tau)(tau)
analysis, providing both HLT ParticleNet (6 outputs) and custom UParT (8 outputs)
flavor discrimination scores.

The pipeline proceeds through 9 stages, from raw PF candidate input to final
PAT jet output with all discriminators attached.

## Input

- **PF Candidates:** `recoScoutingPFCandidate` (from translation layer)
- **Tracks:** `recoScoutingTrack` (from translation layer)
- **Primary Vertices:** `scoutingVerticesPF` / `scoutingVerticesPFFilter` (from vertex reconstruction)
- **Secondary Vertices:** `scoutingDeepInclusiveMergedVerticesPF` (from vertex reconstruction)

## Stage 1: Anti-kT R=0.4 Jet Clustering

**Producer:** `ak4PFJets` (cloned)
**Module label:** `recoScoutingPFJetRecluster`

```python
recoScoutingPFJetRecluster = ak4PFJets.clone(
    src = "recoScoutingPFCandidate",
    jetPtMin = 20,
)
```

| Parameter | Value | Note |
|---|---|---|
| Algorithm | Anti-kT | Standard CMS jet algorithm |
| Radius (R) | 0.4 | AK4 jets |
| `jetPtMin` | 20 GeV | Minimum seed pT for clustering |
| Input | `recoScoutingPFCandidate` | Translated PF candidates |

**Output:** `reco::PFJetCollection` -- reclustered jets from scouting PF candidates.

## Stage 2: Jet Energy Corrections (JEC)

**Producer:** `patJetCorrFactors` (cloned)
**Module label:** `scoutingPFJetReclusterCorrFactors`

```python
scoutingPFJetReclusterCorrFactors = patJetCorrFactors.clone(
    src = "recoScoutingPFJetRecluster",
    levels = cms.vstring("L1FastJet", "L2Relative", "L3Absolute", "L2L3Residual"),
    payload = cms.string("AK4PFHLT"),
    primaryVertices = cms.InputTag("recoScoutingPrimaryVertex"),
)
```

| JEC Level | Purpose |
|---|---|
| L1FastJet | Pileup subtraction (uses PV for rho estimation) |
| L2Relative | Eta-dependent relative correction |
| L3Absolute | Absolute pT scale correction |
| L2L3Residual | Data/MC residual correction (data only) |

The payload `AK4PFHLT` uses HLT-calibrated jet energy corrections, not offline JEC.
This is important: scouting jets were formed from HLT-level reconstruction, so HLT
JEC constants are the appropriate calibration.

**Output:** Correction factors that are later consumed by the PAT jet producer.

## Stage 3: Jet-Track Association

**Producer:** `ak4JetTracksAssociatorAtVertex`
**Module label:** `scoutingPFJetReclusterTracksAssociatorAtVertex`

```python
scoutingPFJetReclusterTracksAssociatorAtVertex = ak4JetTracksAssociatorAtVertex.clone(
    jets = cms.InputTag("recoScoutingPFJetRecluster"),
    coneSize = cms.double(0.4),
    tracks = cms.InputTag("recoScoutingTrack"),
    pvSrc = cms.InputTag("scoutingVerticesPF"),
)
```

Associates scouting tracks to jets within a cone of delta-R < 0.4. This association
is used for computing jet charge and provides track-level inputs for the
b-tagging chain.

**Output:** `reco::JetTracksAssociation` mapping tracks to jets.

## Stage 4: Primary Vertex Association

**Producer:** `PFCandidatePrimaryVertexSorter`
**Module label:** `scoutingPFJetReclusterPrimaryVertexAssociation`

```python
scoutingPFJetReclusterPrimaryVertexAssociation = cms.EDProducer(
    "PFCandidatePrimaryVertexSorter",
    jets = cms.InputTag("recoScoutingPFJetRecluster"),
    particles = cms.InputTag("recoScoutingPFCandidate"),
    vertices = cms.InputTag("scoutingVerticesPFFilter"),
    assignment = cms.PSet(
        minJetPt = cms.double(5.0),           # lowered from 25.0 for scouting
        maxJetDeltaR = cms.double(0.5),
        maxDistanceToJetAxis = cms.double(0.07),
        maxDzForPrimaryAssignment = cms.double(0.1),
        maxDxySigForNotReconstructedPrimary = cms.double(2.0),
        useVertexFit = cms.bool(True),
        useTiming = cms.bool(False),
    ),
)
```

This producer sorts PF candidates by their primary vertex association. Key scouting
adaptations include:

- **`minJetPt = 5.0`** (standard offline: 25.0) -- lowered to retain soft jets from scouting
- **`useTiming = False`** -- timing information is not available in scouting
- **`useVertexFit = True`** -- uses vertex fit for assignment

**Output:** `ValueMap` with the label `"original"` providing the association of jet
constituents to primary vertices. This is consumed by the TagInfo producers.

## Stage 5: HLT ParticleNet TagInfo Production

**Producer:** `DeepBoostedJetTagInfoProducer`
**Module label:** `scoutingPFJetReclusterHLTParticleNetJetTagInfos`

```python
scoutingPFJetReclusterHLTParticleNetJetTagInfos = cms.EDProducer(
    "DeepBoostedJetTagInfoProducer",
    jets = cms.InputTag("recoScoutingPFJetRecluster"),
    pf_candidates = cms.InputTag("recoScoutingPFCandidate"),
    secondary_vertices = cms.InputTag("scoutingDeepInclusiveMergedVerticesPF"),
    vertices = cms.InputTag("scoutingVerticesPFFilter"),
    vertex_associator = cms.InputTag(
        "scoutingPFJetReclusterPrimaryVertexAssociation", "original"),
    jet_radius = cms.double(0.4),
    min_jet_pt = cms.double(5.0),
    max_jet_eta = cms.double(2.6),
    use_hlt_features = cms.bool(True),
    use_scouting_features = cms.bool(False),
)
```

Collects PF candidate four-vectors, track impact parameters, and secondary vertex
information per jet into the `DeepBoostedJetTagInfo` structure. The
`use_hlt_features = True` flag activates HLT-specific feature computation paths.

**Output:** `reco::DeepBoostedJetTagInfoCollection`

## Stage 6: HLT ParticleNet ONNX Inference

**Producer:** `BoostedJetONNXJetTagsProducer`
**Module label:** `scoutingPFJetReclusterHLTParticleNetONNXJetTags`

```python
scoutingPFJetReclusterHLTParticleNetONNXJetTags = cms.EDProducer(
    "BoostedJetONNXJetTagsProducer",
    src = cms.InputTag("scoutingPFJetReclusterHLTParticleNetJetTagInfos"),
    model_path = cms.FileInPath(
        "RecoBTag/Combined/data/HLT/ParticleNetAK4/V01/particle-net.onnx"),
    preprocess_json = cms.string(
        "RecoBTag/Combined/data/HLT/ParticleNetAK4/V01/preprocess.json"),
    flav_names = cms.vstring(
        "probtauhp", "probtauhm", "probb", "probc", "probuds", "probg", "ptcorr"),
)
```

| Output Score | Particle Hypothesis |
|---|---|
| `probtauhp` | Hadronic tau (positive helicity) |
| `probtauhm` | Hadronic tau (negative helicity / muonic) |
| `probb` | b quark |
| `probc` | c quark |
| `probuds` | Light quarks (u, d, s) |
| `probg` | Gluon |
| `ptcorr` | pT correction factor |

**Output:** `reco::JetTagCollection` (one per flavor name).

## Stage 7: UParT TagInfo Production

**Producer:** `UnifiedParticleTransformerAK4TagInfoProducer`
**Module label:** `scoutingPFJetReclusterPFUnifiedParticleTransformerAK4TagInfos`

```python
scoutingPFJetReclusterPFUnifiedParticleTransformerAK4TagInfos = cms.EDProducer(
    "UnifiedParticleTransformerAK4TagInfoProducer",
    jets = cms.InputTag("recoScoutingPFJetRecluster"),
    candidates = cms.InputTag("recoScoutingPFCandidate"),
    vertices = cms.InputTag("scoutingVerticesPF"),
    secondary_vertices = cms.InputTag("scoutingDeepInclusiveMergedVerticesPF"),
    jet_radius = cms.double(0.4),
    min_candidate_pt = cms.double(0.1),
    min_jet_pt = cms.double(0),
    max_jet_eta = cms.double(2.5),
    losttracks = cms.InputTag(""),             # Disabled for scouting
    puppi_value_map = cms.InputTag(""),        # No PUPPI in scouting
    fallback_puppi_weight = cms.bool(True),    # Use default weight = 1.0
    fallback_vertex_association = cms.bool(True),
    vertex_associator = cms.InputTag(""),      # Auto-associate
)
```

The UParT TagInfo producer extracts per-jet feature tensors organized into groups:

| Input Tensor | Content | Max Entries | Features |
|---|---|---|---|
| `input_1` | Charged PF candidates | 26 | 20 features (track kinematics, IP, quality, 4-vector) |
| `input_2` | Neutral PF candidates | 25 | 10 features (kinematics, drminsv) |
| `input_3` | Secondary vertices | 5 | 15 features (vertex kinematics, decay length, mass) |
| `input_4` | Charged pairwise | 26 | 4 features (delta-eta, delta-phi, delta-R, pT ratio) |
| `input_5` | Neutral pairwise | 25 | 4 features |
| `input_6` | SV pairwise | 5 | 4 features |

Key scouting adaptations:
- **No lost tracks** (`losttracks = ""`): scouting lost tracks are not fed to UParT
- **No PUPPI** (`puppi_value_map = ""`): PUPPI weights unavailable; uses fallback weight of 1.0
- **Fallback vertex association**: if explicit PV association fails, uses nearest vertex
- **`min_jet_pt = 0`**: no pT cut at the TagInfo stage (cut applied later in NanoAOD)

**Output:** `UnifiedParticleTransformerAK4TagInfo` collection.

## Stage 8: UParT ONNX Inference (Custom HH->bb(tau)(tau) Model)

**Producer:** `UnifiedParticleTransformerAK4ONNXJetTagsScoutingProducer`
**Module label:** `scoutingPFJetReclusterPFUnifiedParticleTransformerAK4Tags`

```python
scoutingPFJetReclusterPFUnifiedParticleTransformerAK4Tags = cms.EDProducer(
    "UnifiedParticleTransformerAK4ONNXJetTagsScoutingProducer",
    src = cms.InputTag(
        "scoutingPFJetReclusterPFUnifiedParticleTransformerAK4TagInfos"),
    model_path = cms.FileInPath(
        "RecoBTag/Combined/data/UParTAK4/Scouting_HHbbtautau/V00/modelfile/model.onnx"),
    input_names = cms.vstring(
        "input_1", "input_2", "input_3", "input_4", "input_5", "input_6"),
    output_names = cms.vstring("ID_pred"),
    flav_names = cms.vstring(
        "probb", "probbb", "problepb", "probc",
        "probuds", "probg", "probtaum", "probtaup"),
)
```

| Output Score | Particle Hypothesis | Physics Role |
|---|---|---|
| `probb` | Single b quark | b-jet identification |
| `probbb` | Double b (merged bb) | H->bb tagging |
| `problepb` | Leptonic b decay (b->l+X) | Semi-leptonic b-jet |
| `probc` | c quark | Charm-jet identification |
| `probuds` | Light quarks (u, d, s) | Light-jet background |
| `probg` | Gluon | Gluon-jet background |
| `probtaum` | Tau -> muon decay | Leptonic tau identification |
| `probtaup` | Tau -> pion decay | Hadronic tau identification |

This is a **custom ONNX model** trained specifically for the HH->bb(tau)(tau) signal,
with dedicated tau decay mode outputs (`probtaum`, `probtaup`) that are critical for
tau jet identification in the scouting data stream. The model file is 3.7 MB.

A general-purpose scouting UParT model also exists at
`RecoBTag/Combined/data/UParTAK4/Scouting/V00/modelfile/model.onnx` (3.6 MB)
but is not used in the current configuration.

**Output:** 8 `reco::JetTagCollection` objects (one per flavor name).

## Stage 9: PAT Jet Assembly

**Producer:** `_patJets` (cloned)
**Module label:** `patScoutingPFJetRecluster`

The final stage combines everything into `pat::Jet` objects:

```python
patScoutingPFJetRecluster = _patJets.clone(
    jetSource = "recoScoutingPFJetRecluster",
    addJetCorrFactors = True,
    jetCorrFactorsSource = ["scoutingPFJetReclusterCorrFactors"],
    addBTagInfo = True,
    addDiscriminators = True,
    discriminatorSources = [
        # HLT ParticleNet (6 active scores)
        "scoutingPFJetReclusterHLTParticleNetONNXJetTags:probtauhp",
        "scoutingPFJetReclusterHLTParticleNetONNXJetTags:probtauhm",
        "scoutingPFJetReclusterHLTParticleNetONNXJetTags:probb",
        "scoutingPFJetReclusterHLTParticleNetONNXJetTags:probc",
        "scoutingPFJetReclusterHLTParticleNetONNXJetTags:probuds",
        "scoutingPFJetReclusterHLTParticleNetONNXJetTags:probg",
        # UParT custom (8 active scores)
        "scoutingPFJetReclusterPFUnifiedParticleTransformerAK4Tags:probb",
        "scoutingPFJetReclusterPFUnifiedParticleTransformerAK4Tags:probbb",
        "scoutingPFJetReclusterPFUnifiedParticleTransformerAK4Tags:problepb",
        "scoutingPFJetReclusterPFUnifiedParticleTransformerAK4Tags:probc",
        "scoutingPFJetReclusterPFUnifiedParticleTransformerAK4Tags:probuds",
        "scoutingPFJetReclusterPFUnifiedParticleTransformerAK4Tags:probg",
        "scoutingPFJetReclusterPFUnifiedParticleTransformerAK4Tags:probtaum",
        "scoutingPFJetReclusterPFUnifiedParticleTransformerAK4Tags:probtaup",
    ],
    addJetCharge = True,
    jetChargeSource = "scoutingPFJetReclusterCharge",
    getJetMCFlavour = True,
    addJetFlavourInfo = True,
    JetFlavourInfoSource = cms.InputTag("scoutingPFJetReclusterFlavourAssociation"),
)
```

For MC, additional gen-level matching is included:
- **Gen jet matching:** `slimmedGenJets` matched by delta-R quality
- **Gen parton matching:** `prunedGenParticles`
- **Jet flavor association:** b/c hadron-based ghost clustering via `patJetPartonsNano`

**Output:** `pat::JetCollection` ready for NanoAOD table production.

## NanoAOD Output

The PAT jets are flattened to NanoAOD with pT- and eta-gated discriminators:

| Branch Prefix | Tagger | pT Gate | eta Gate |
|---|---|---|---|
| `hltPNet_*` | HLT ParticleNet | >= 5 GeV | abs(eta) <= 2.6 |
| `scoutUParT_*` | Custom UParT | >= 15 GeV | abs(eta) <= 2.5 |

Jets outside the gate return -1 for the corresponding discriminator value.

## Complete AK4 Task

```python
scoutingPFJetRecluster2Task = cms.Task(
    recoScoutingPFJetRecluster,                        # [1] Jet clustering
    scoutingPFJetReclusterCorrFactors,                 # [2] JEC
    scoutingPFJetReclusterTracksAssociatorAtVertex,    # [3] Track assoc
    scoutingPFJetReclusterCharge,                      #     Jet charge
    scoutingPFJetReclusterPrimaryVertexAssociation,    # [4] PV assoc
    scoutingPFJetReclusterHLTParticleNetJetTagInfos,   # [5] HLT PNet TagInfo
    scoutingPFJetReclusterHLTParticleNetONNXJetTags,   # [6] HLT PNet inference
    scoutingPFJetReclusterPFUnifiedParticleTransformerAK4TagInfos,  # [7] UParT TagInfo
    scoutingPFJetReclusterPFUnifiedParticleTransformerAK4Tags,      # [8] UParT inference
    scoutingPFJetReclusterGenJetMatch,                 #     MC gen-jet match
    patJetPartonsNano,                                 #     MC parton selection
    scoutingPFJetReclusterFlavourAssociation,          #     MC flavor assoc
    scoutingPFJetReclusterGenPartonMatch,              #     MC parton match
    patScoutingPFJetRecluster,                         # [9] PAT assembly
)
```

## Key Parameter Summary

| Parameter | Value | Context |
|---|---|---|
| Jet radius | 0.4 | Anti-kT clustering |
| Jet pT minimum (clustering) | 20 GeV | FastJet seed threshold |
| JEC payload | `AK4PFHLT` | HLT-calibrated corrections |
| HLT PNet min pT | 5 GeV | TagInfo producer threshold |
| HLT PNet max eta | 2.6 | Pseudorapidity coverage |
| UParT min pT (TagInfo) | 0 GeV | No cut at feature extraction |
| UParT max eta | 2.5 | Narrower than HLT PNet |
| UParT min pT (NanoAOD) | 15 GeV | Output gate for score validity |
| PV assoc minJetPt | 5 GeV | Lowered from 25 GeV for scouting |
| PUPPI weights | Disabled | Not available in scouting |
