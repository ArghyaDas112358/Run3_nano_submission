# UParT AK4: Unified Particle Transformer for Scouting Jets

## Architecture Overview

The Unified Particle Transformer (UParT) is a transformer-based neural network designed
for jet flavor classification at CMS. It processes variable-length sets of jet
constituents (charged PF candidates, neutral PF candidates, and secondary vertices)
through attention-based layers that learn correlations between particles within a jet.

The key architectural features of UParT include:

- **Multi-head self-attention** across particle constituents within each category.
- **Cross-attention** between different constituent types (charged, neutral, SV).
- **Pairwise interaction features** using 4-momentum vectors for geometric relationships.
- **Permutation-invariant** design: the network is agnostic to the ordering of
  input particles, learning to weight important constituents via attention.

The scouting variant uses 6 input tensor groups (compared to 8 in the standard RECO
version) because lost tracks are unavailable in scouting data.

## Input Features: 6 Tensor Groups

The UParT model consumes 6 input tensors per jet. Each tensor has shape
`[1, N_max, N_features]` where `N_max` is the maximum number of objects and
`N_features` is the feature count per object.

### Tensor 1: Charged PF Candidate Features

Shape: `(1, 26, 20)` -- up to 26 charged candidates, 20 features each.

Candidates are sorted by signed impact parameter significance (SIP2d, descending).

| Index | Feature | Description |
|-------|---------|-------------|
| 0 | `btagPf_trackEtaRel` | Track pseudo-rapidity relative to jet axis |
| 1 | `btagPf_trackPtRel` | Track pT relative to jet axis |
| 2 | `btagPf_trackPPar` | Track momentum parallel to jet axis |
| 3 | `btagPf_trackDeltaR` | Delta-R between track and jet axis |
| 4 | `btagPf_trackPParRatio` | Parallel momentum fraction |
| 5 | `btagPf_trackSip2dVal` | 2D signed impact parameter value |
| 6 | `btagPf_trackSip2dSig` | 2D signed impact parameter significance |
| 7 | `btagPf_trackSip3dVal` | 3D signed impact parameter value |
| 8 | `btagPf_trackSip3dSig` | 3D signed impact parameter significance |
| 9 | `btagPf_trackJetDistVal` | Track-jet distance |
| 10 | `ptrel` | pT relative to jet |
| 11 | `drminsv` | Minimum delta-R to any secondary vertex |
| 12 | `vtx_ass` | Vertex association flag (0 or 1) |
| 13 | `puppiw` | PUPPI weight (fallback = 1.0 for scouting) |
| 14 | `chi2` | Track fit chi-squared |
| 15 | `quality` | Track reconstruction quality flag |
| 16 | `pt` | Candidate pT |
| 17 | `eta` | Candidate eta |
| 18 | `phi` | Candidate phi |
| 19 | `e` | Candidate energy |

### Tensor 2: Neutral PF Candidate Features

Shape: `(1, 25, 10)` -- up to 25 neutral candidates, 10 features each.

Candidates are sorted by pT (descending).

| Index | Feature | Description |
|-------|---------|-------------|
| 0 | `ptrel` | pT relative to jet |
| 1 | `deltaR` | Delta-R to jet axis |
| 2 | `isGamma` | Photon identification flag |
| 3 | (placeholder) | Fixed at 1.0 (replaces unavailable `hadFrac`) |
| 4 | `drminsv` | Minimum delta-R to any secondary vertex |
| 5 | `puppiw` | PUPPI weight (fallback = 1.0) |
| 6 | `pt` | Candidate pT |
| 7 | `eta` | Candidate eta |
| 8 | `phi` | Candidate phi |
| 9 | `e` | Candidate energy |

Note: `etarel` and `phirel` features present in the standard version are commented out
for scouting because scouting-level objects lack the necessary precision.

### Tensor 3: Secondary Vertex Features

Shape: `(1, 5, 15)` -- up to 5 secondary vertices, 15 features each.

Vertices are sorted by 2D displacement significance (descending), selected within
delta-R < 0.4 of the jet axis.

| Index | Feature | Description |
|-------|---------|-------------|
| 0 | `deltaR` | Delta-R to jet axis |
| 1 | `mass` | Vertex invariant mass |
| 2 | `chi2` | Vertex fit chi-squared |
| 3 | `normchi2` | Normalized chi-squared |
| 4 | `pt` | Vertex pT |
| 5 | `eta` | Vertex eta |
| 6 | `phi` | Vertex phi |
| 7 | `e` | Vertex energy |
| 8 | `dxy` | 2D displacement from primary vertex |
| 9 | `dxysig` | 2D displacement significance |
| 10 | `d3d` | 3D displacement from primary vertex |
| 11 | `d3dsig` | 3D displacement significance |
| 12 | `ntracks` | Number of tracks in vertex |
| 13 | `costhetasvpv` | Cosine of angle between SV-PV direction and SV momentum |
| 14 | `enratio` | Energy ratio (SV energy / jet energy) |

### Tensors 4, 5, 6: Pairwise 4-Momentum Features

These three tensors store the raw 4-momentum (px, py, pz, e) for each constituent,
enabling the transformer to compute pairwise geometric features:

- **Tensor 4**: Charged PF 4-vectors, shape `(1, 26, 4)`
- **Tensor 5**: Neutral PF 4-vectors, shape `(1, 25, 4)`
- **Tensor 6**: SV 4-vectors, shape `(1, 5, 4)`

## 8 Output Discriminants

The model output tensor has shape `(1, 8)`, representing flavor probabilities that
sum to approximately 1.0 for each jet:

| Index | Name | Physics Interpretation |
|-------|------|----------------------|
| 0 | `probb` | b quark jet |
| 1 | `probbb` | Merged bb system (e.g., gluon splitting to bb) |
| 2 | `problepb` | b quark with leptonic W decay |
| 3 | `probc` | c quark jet |
| 4 | `probuds` | Light quark jet (u, d, s) |
| 5 | `probg` | Gluon jet |
| 6 | `probtaum` | Tau-minus hadronic jet |
| 7 | `probtaup` | Tau-plus hadronic jet |

The inclusion of `probtaum` and `probtaup` as separate outputs is a distinguishing
feature of the HH->bb(tautau)-optimized model. Standard UParT models either lack tau
outputs entirely or combine them differently. The charge-split tau categories enable
studies of charge-dependent modeling biases.

## Model Variants: Scouting_HHbbtautau vs Scouting

Two model variants exist under `RecoBTag/Combined/data/UParTAK4/`:

### Scouting_HHbbtautau/V00 (Default)

- **File size**: 3.8 MB
- **Training signal**: HH->bb(tautau) with hadronic tau jets
- **Training background**: QCD multijet with misidentified taus
- **8 outputs**: probb, probbb, problepb, probc, probuds, probg, probtaum, probtaup
- **Optimization target**: Simultaneous b-jet and tau-jet discrimination in the
  low-to-moderate pT regime characteristic of scouting data
- **Tau charge splitting**: Separate tau-minus and tau-plus classes to capture
  potential charge-dependent asymmetries

### Scouting/V00 (General Purpose)

- **File size**: 3.7 MB
- **Training**: General-purpose scouting model without HH-specific signal enrichment
- **Outputs**: Same 8-class structure
- **Use case**: Baseline comparison and analyses not focused on HH->bb(tautau)

The active model is selected in the Python configuration at:
`Run3ScoutingPFJetRecluster_cff.py`, line 149:
```python
model_path = cms.FileInPath('RecoBTag/Combined/data/UParTAK4/Scouting_HHbbtautau/V00/modelfile/model.onnx')
```

## Scouting-Specific Adaptations

The scouting UParT differs from the standard RECO UParT in several ways:

| Aspect | Scouting UParT | Standard UParT |
|--------|---------------|----------------|
| Input tensors | 6 (no lost tracks) | 8 (includes lost tracks) |
| PUPPI weights | Fallback = 1.0 | Required from ValueMap |
| Vertex association | Fallback (closest dz) | Required from ValueMap |
| Feature producer | `UnifiedParticleTransformerAK4TagInfoScoutingProducer` | `UnifiedParticleTransformerAK4TagInfoProducer` |
| ONNX producer | `UnifiedParticleTransformerAK4ONNXJetTagsScoutingProducer` | `UnifiedParticleTransformerAK4ONNXJetTagsProducer` |
| Lost track tensor | Absent | Present (max 5, 18 features each) |
| Dynamic axes | Disabled (fixed shapes) | Configurable |
| Model directory | `Scouting_HHbbtautau/V00` or `Scouting/V00` | `PUPPI/V00` or `PUPPI/V01` |

The lost tracks tensor (present in standard UParT) would contribute an additional
5 candidates x 18 features = 90 input values per jet. Since scouting data does not
include track reconstruction beyond the HLT, these features are unavailable, and the
model was retrained to operate without them.

## Feature Extraction Configuration

Key parameters from `Run3ScoutingPFJetRecluster_cff.py`:

```
jet_radius          = 0.4
min_candidate_pt    = 0.1 GeV
min_jet_pt          = 0 GeV (applied at NanoAOD as 15 GeV)
max_jet_eta         = 2.5
fallback_puppi_weight         = True (use 1.0)
fallback_vertex_association   = True (use closest dz PV)
sort_cand_by_pt     = False (sort by SIP2d significance instead)
losttracks          = '' (disabled)
```

Unfilled constituent slots are zero-padded. For example, if a jet contains only
18 charged candidates, the last 8 slots in the 26-candidate tensor are filled
with zeros across all 20 feature dimensions.
