# AK8 Fat Jet Reclustering Pipeline

## Overview

The AK8 fat jet reclustering pipeline (`Run3ScoutingFatPFJetRecluster_cff.py`)
reconstructs wide-cone jets from translated scouting PF candidates and attaches
HLT ParticleNet AK8 tagger scores for boosted object identification. AK8 jets
capture the decay products of heavy boosted particles (H, top, W, Z) within a
single fat jet, which is essential for identifying boosted H->bb and H->tau(tau)
signatures in the HH->bb(tau)(tau) analysis.

The AK8 pipeline currently uses only the HLT ParticleNet AK8 tagger. No custom
UParT model is integrated for AK8 jets at this time.

## Input

- **PF Candidates:** `scoutingPFCandidate` (from translation layer)
- **Tracks:** `recoScoutingTrack` (from translation layer)
- **Primary Vertices:** `scoutingVerticesPF` / `scoutingVerticesPFFilter` (from vertex reconstruction)
- **Secondary Vertices:** `scoutingDeepInclusiveMergedVerticesPF` (from vertex reconstruction)

**Known issue:** The config file references `scoutingPFCandidate` as the jet
clustering input, which should be `recoScoutingPFCandidate` for consistency with
the AK4 pipeline. This may need correction.

## Stage 1: Anti-kT R=0.8 Jet Clustering

**Producer:** `ak4PFJets` (cloned with R=0.8)
**Module label:** `recoScoutingFatPFJetRecluster`

```python
recoScoutingFatPFJetRecluster = ak4PFJets.clone(
    src = "scoutingPFCandidate",
    rParam = 0.8,
    jetPtMin = 170.0,
)
```

| Parameter | Value | AK4 Comparison |
|---|---|---|
| Algorithm | Anti-kT | Same |
| Radius (R) | 0.8 | 0.4 |
| `jetPtMin` | 170 GeV | 20 GeV |

The much higher pT threshold (170 GeV vs 20 GeV) reflects the boosted regime:
particles from heavy resonance decays are collimated into a single fat jet only
at high transverse momentum.

**Output:** `reco::PFJetCollection` -- reclustered AK8 fat jets.

## Stage 2: Jet Energy Corrections

**Producer:** `patJetCorrFactors` (cloned)
**Module label:** `scoutingFatPFJetReclusterCorrFactors`

```python
scoutingFatPFJetReclusterCorrFactors = patJetCorrFactors.clone(
    src = "recoScoutingFatPFJetRecluster",
    levels = cms.vstring("L1FastJet", "L2Relative", "L3Absolute", "L2L3Residual"),
    payload = cms.string("AK8PFHLT"),
    primaryVertices = cms.InputTag("recoScoutingPrimaryVertex"),
)
```

Uses the `AK8PFHLT` payload (HLT-calibrated for R=0.8 jets), distinct from the
`AK4PFHLT` used for narrow jets. The same four-level correction chain is applied.

**Output:** JEC correction factors for AK8 jets.

## Stage 3: Track Association and Jet Charge

**Producers:**
- `ak4JetTracksAssociatorAtVertex` -> `scoutingFatPFJetReclusterTracksAssociatorAtVertex`
- `patJetCharge` -> `scoutingFatPFJetReclusterCharge`

```python
scoutingFatPFJetReclusterTracksAssociatorAtVertex = ak4JetTracksAssociatorAtVertex.clone(
    jets = cms.InputTag("recoScoutingFatPFJetRecluster"),
    coneSize = cms.double(0.4),     # Note: cone size is 0.4, not 0.8
    tracks = cms.InputTag("recoScoutingTrack"),
    pvSrc = cms.InputTag("scoutingVerticesPF"),
)
```

The track association uses a cone size of 0.4 (not 0.8), which associates only
the core tracks near the jet axis. This is a deliberate choice inherited from the
standard CMSSW AK8 workflow, where track association is used for jet charge
computation and does not need to cover the full fat jet area.

## Stage 4: Primary Vertex Association

**Producer:** `PFCandidatePrimaryVertexSorter`
**Module label:** `scoutingFatPFJetReclusterPrimaryVertexAssociation`

The configuration mirrors the AK4 PV association with the same scouting-adapted
parameters:

```python
scoutingFatPFJetReclusterPrimaryVertexAssociation = cms.EDProducer(
    "PFCandidatePrimaryVertexSorter",
    jets = cms.InputTag("recoScoutingFatPFJetRecluster"),
    particles = cms.InputTag("recoScoutingPFCandidate"),
    vertices = cms.InputTag("scoutingVerticesPFFilter"),
    assignment = cms.PSet(
        minJetPt = cms.double(5.0),
        maxJetDeltaR = cms.double(0.5),
        maxDistanceToJetAxis = cms.double(0.07),
        maxDzForPrimaryAssignment = cms.double(0.1),
        useVertexFit = cms.bool(True),
        useTiming = cms.bool(False),
    ),
)
```

**Output:** PV association ValueMap with `"original"` label.

## Stage 5: HLT ParticleNet AK8 TagInfo Production

**Producer:** `DeepBoostedJetTagInfoProducer`
**Module label:** `scoutingFatPFJetReclusterHLTParticleNetJetTagsInfosAK8`

```python
scoutingFatPFJetReclusterHLTParticleNetJetTagsInfosAK8 = cms.EDProducer(
    "DeepBoostedJetTagInfoProducer",
    jets = cms.InputTag("recoScoutingFatPFJetRecluster"),
    pf_candidates = cms.InputTag("recoScoutingPFCandidate"),
    secondary_vertices = cms.InputTag("scoutingDeepInclusiveMergedVerticesPF"),
    vertices = cms.InputTag("scoutingVerticesPFFilter"),
    vertex_associator = cms.InputTag(
        "scoutingFatPFJetReclusterPrimaryVertexAssociation", "original"),
    jet_radius = cms.double(0.8),
    min_jet_pt = cms.double(200.0),
    max_jet_eta = cms.double(2.5),
    use_hlt_features = cms.bool(True),
    use_scouting_features = cms.bool(False),
)
```

| Parameter | AK8 Value | AK4 Comparison |
|---|---|---|
| `jet_radius` | 0.8 | 0.4 |
| `min_jet_pt` | 200 GeV | 5 GeV |
| `max_jet_eta` | 2.5 | 2.6 |
| `use_hlt_features` | True | True |

The higher pT threshold (200 GeV) ensures the tagger is only evaluated on jets in
the boosted regime where the model was trained.

**Output:** `reco::DeepBoostedJetTagInfoCollection`

## Stage 6: HLT ParticleNet AK8 ONNX Inference

**Producer:** `BoostedJetONNXJetTagsProducer`
**Module label:** `scoutingFatPFJetReclusterHLTParticleNetONNXJetTagsAK8`

```python
scoutingFatPFJetReclusterHLTParticleNetONNXJetTagsAK8 = cms.EDProducer(
    "BoostedJetONNXJetTagsProducer",
    src = cms.InputTag("scoutingFatPFJetReclusterHLTParticleNetJetTagsInfosAK8"),
    model_path = cms.FileInPath(
        "RecoBTag/Combined/data/HLT/ParticleNetAK8/V01/particle-net.onnx"),
    preprocess_json = cms.string(
        "RecoBTag/Combined/data/HLT/ParticleNetAK8/V01/preprocess.json"),
    flav_names = cms.vstring(
        "probHtt", "probHtm", "probHte", "probHbb", "probHcc",
        "probHqq", "probHgg", "probQCD2hf", "probQCD1hf", "probQCD0hf"),
)
```

### AK8 Tagger Output Scores

| Output Score | Physics Hypothesis | Description |
|---|---|---|
| `probHtt` | H -> tau_h tau_h | Fully hadronic di-tau Higgs |
| `probHtm` | H -> tau_h mu | Hadronic-muonic di-tau Higgs |
| `probHte` | H -> tau_h e | Hadronic-electronic di-tau Higgs |
| `probHbb` | H -> bb | Di-b Higgs |
| `probHcc` | H -> cc | Di-charm Higgs |
| `probHqq` | H -> qq (light) | Light-quark Higgs |
| `probHgg` | H -> gg | Gluon-gluon Higgs |
| `probQCD2hf` | QCD 2 heavy flavor | QCD with 2 b/c quarks |
| `probQCD1hf` | QCD 1 heavy flavor | QCD with 1 b/c quark |
| `probQCD0hf` | QCD 0 heavy flavor | Light QCD background |

For the HH->bb(tau)(tau) analysis, the most relevant scores are `probHbb` (for
identifying the boosted H->bb jet) and `probHtt`/`probHtm`/`probHte` (for the
H->tau(tau) jet in different tau decay channels).

**Output:** 10 `reco::JetTagCollection` objects.

## Stage 7: PAT Jet Assembly

**Producer:** `_patJets` (cloned)
**Module label:** `patScoutingFatPFJetRecluster`

```python
patScoutingFatPFJetRecluster = _patJets.clone(
    jetSource = "recoScoutingFatPFJetRecluster",
    addJetCorrFactors = True,
    jetCorrFactorsSource = ["scoutingFatPFJetReclusterCorrFactors"],
    addBTagInfo = True,
    addDiscriminators = True,
    discriminatorSources = [
        "scoutingFatPFJetReclusterHLTParticleNetONNXJetTagsAK8:probHtt",
        # ... all 10 scores ...
        "scoutingFatPFJetReclusterHLTParticleNetONNXJetTagsAK8:probQCD0hf",
    ],
    addJetCharge = True,
    addGenPartonMatch = False,
    addGenJetMatch = True,
    genJetMatch = cms.InputTag("scoutingFatPFJetReclusterGenJetMatch"),
    getJetMCFlavour = True,
)
```

For MC, gen-jet matching uses `slimmedGenJetsAK8` (AK8 gen jets) and flavor
association uses `rParam = 0.8` for the ghost clustering cone.

Note: `addGenPartonMatch = False` for AK8 jets, unlike AK4 which has it enabled.

**Output:** `pat::JetCollection` for NanoAOD table production.

## Differences from the AK4 Pipeline

| Feature | AK4 | AK8 |
|---|---|---|
| Jet radius | 0.4 | 0.8 |
| pT minimum (clustering) | 20 GeV | 170 GeV |
| JEC payload | `AK4PFHLT` | `AK8PFHLT` |
| HLT PNet model | `ParticleNetAK4/V01` | `ParticleNetAK8/V01` |
| HLT PNet output count | 7 (6 flavor + ptcorr) | 10 (Higgs + QCD) |
| HLT PNet min pT (TagInfo) | 5 GeV | 200 GeV |
| UParT tagger | Yes (custom HHbbtautau) | No |
| NanoAOD pT gate | 5 GeV (PNet), 15 GeV (UParT) | 200 GeV |
| Gen-jet matching source | `slimmedGenJets` | `slimmedGenJetsAK8` |
| Gen parton matching | Yes | No |
| Track assoc cone size | 0.4 | 0.4 (core only) |
| Flavor assoc rParam | 0.4 (default) | 0.8 |

## Substructure Variables

The current AK8 configuration does **not** compute:
- Soft-drop mass (groomed jet mass)
- N-subjettiness (tau_1, tau_2, tau_3 ratios)
- Subjet collections

These observables would require additional producers (`SoftDropJetProducer`,
`NjettinessProducer`) that are not yet integrated into the scouting pipeline.
The HLT ParticleNet AK8 tagger internally learns substructure features from
the PF candidate inputs, so explicit substructure variables are not required
for the tagger itself but would be useful for complementary analyses.

## NanoAOD Output

The AK8 jets are flattened to the `ScoutingFatPFJetRecluster2` NanoAOD table:

```
ScoutingFatPFJetRecluster2_pt
ScoutingFatPFJetRecluster2_eta
ScoutingFatPFJetRecluster2_phi
ScoutingFatPFJetRecluster2_mass
ScoutingFatPFJetRecluster2_hltPNetAK8_probHbb
ScoutingFatPFJetRecluster2_hltPNetAK8_probHtt
ScoutingFatPFJetRecluster2_hltPNetAK8_probHtm
...
ScoutingFatPFJetRecluster2_hltPNetAK8_probQCD0hf
```

All HLT PNet AK8 scores are gated at pT >= 200 GeV and abs(eta) <= 2.5, returning
-1 outside this kinematic range.

## Complete AK8 Task

```python
scoutingFatPFJetRecluster2Task = cms.Task(
    recoScoutingFatPFJetRecluster,                           # Jet clustering
    scoutingFatPFJetReclusterCorrFactors,                    # JEC
    scoutingFatPFJetReclusterTracksAssociatorAtVertex,       # Track assoc
    scoutingFatPFJetReclusterCharge,                         # Jet charge
    scoutingFatPFJetReclusterPrimaryVertexAssociation,       # PV assoc
    scoutingFatPFJetReclusterHLTParticleNetJetTagsInfosAK8,  # HLT PNet TagInfo
    scoutingFatPFJetReclusterHLTParticleNetONNXJetTagsAK8,   # HLT PNet inference
    scoutingFatPFJetReclusterGenJetMatch,                    # MC gen-jet match
    patJetPartonsNano,                                       # MC parton selection
    scoutingFatPFJetReclusterFlavourAssociation,             # MC flavor assoc
    patScoutingFatPFJetRecluster,                            # PAT assembly
)
```

## Known Issues

1. **Input source mismatch:** `Run3ScoutingFatPFJetRecluster_cff.py` line 5 uses
   `src = "scoutingPFCandidate"` instead of `src = "recoScoutingPFCandidate"`.
2. **`addScoutingFatPFJetRecluster2()` bugs in `ScoutingNanoCustomisation_cff.py`:**
   - Line 255: `prcoess.scoutingFatPFJetRecluster2MCTable` has a typo (`prcoess`
     instead of `process`).
   - Line 265: `scoutingFatPFJetRecluster2TableTask` is missing the `process.`
     prefix.
   These bugs cause `AttributeError` at runtime. The `addAll()` function duplicates
   this code with the bugs corrected.
