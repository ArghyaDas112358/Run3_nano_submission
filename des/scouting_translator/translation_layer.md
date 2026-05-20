# Translation Layer: HLT Packed Scouting to Reco Format

## Overview

The translation layer (`Run3ScoutingTranslation_cff.py`) converts HLT-level scouting
objects stored in MiniAOD into standard CMSSW reco and PAT formats. This is the
foundational step: every downstream operation (jet clustering, vertex finding,
b-tagging) depends on these translated objects.

The HLT scouting system stores objects in compact `Run3Scouting*` data formats with
reduced precision and stripped associations. The translation layer reconstructs
full `reco::PFCandidate`, `reco::Track`, `reco::Vertex`, and `pat::Muon` objects,
recovering track-particle associations and propagating track quality information
through ValueMaps.

## HLT Input Collections

| HLT Producer Label | Data Format | Content |
|---|---|---|
| `hltScoutingPFPacker` | `Run3ScoutingParticleCollection` | PF candidates with embedded track params |
| `hltScoutingTrackPacker` | `Run3ScoutingTrackCollection` | Full tracking info (5D covariance, hit pattern) |
| `hltScoutingPrimaryVertexPacker:primaryVtx` | `Run3ScoutingVertexCollection` | HLT primary vertices |
| `hltScoutingMuonPackerNoVtx` | `Run3ScoutingMuonCollection` | Muons without vertex constraint |
| `hltScoutingMuonPackerVtx` | `Run3ScoutingMuonCollection` | Muons with vertex constraint |

## Translation Producer Chain

The translation runs as a single `cms.Task` with 10 ordered producers:

### Step 1: PF-to-Track Index Matching

**Producer:** `Run3ScoutingParticleMatchTrackIndexProducer`
**Module label:** `scoutingParticleMatchTrackIndex`

```python
scoutingParticleMatchTrackIndex = cms.EDProducer(
    "Run3ScoutingParticleMatchTrackIndexProducer",
    particle = cms.InputTag("hltScoutingPFPacker"),
    track = cms.InputTag("hltScoutingTrackPacker"),
    useIP = cms.bool(False),
    sortBeforeMatch = cms.bool(True),
    uniqueMatch = cms.bool(True),
)
```

**Output:** `ValueMap<int>` mapping each PF particle to its closest scouting track
index by delta-R matching. The `uniqueMatch` flag ensures each track is matched to
at most one particle. This index is consumed by the PFCandidate producer for building
full track objects.

### Step 2: PF Candidate Translation (Core Producer)

**Producer:** `Run3ScoutingParticle2RecoPFCandidateProducer`
**Module label:** `recoScoutingPFCandidate`

```python
recoScoutingPFCandidate = cms.EDProducer(
    "Run3ScoutingParticle2RecoPFCandidateProducer",
    particle = cms.InputTag("hltScoutingPFPacker"),
    track = cms.InputTag("hltScoutingTrackPacker"),
    matchTrackIndex = cms.InputTag("scoutingParticleMatchTrackIndex"),
    primaryVertex = cms.InputTag(""),
)
```

This is the most complex producer in the package. It outputs:

**Collections:**
- `recoScoutingPFCandidate` -- `reco::PFCandidateCollection`
- `recoScoutingPFCandidate:track` -- `reco::TrackCollection` (matched scouting tracks converted to reco format)

**ValueMaps (11 total, keyed on the PFCandidate collection):**

| ValueMap Name | Type | Content |
|---|---|---|
| `vertexIndex` | `int` | Index of the associated primary vertex |
| `normchi2` | `float` | Normalized chi-squared of the track fit |
| `dz` | `float` | Longitudinal impact parameter |
| `dxy` | `float` | Transverse impact parameter |
| `dzsig` | `float` | dz significance (dz / sigma_dz) |
| `dxysig` | `float` | dxy significance (dxy / sigma_dxy) |
| `lostInnerHits` | `int` | Number of missing inner tracker hits |
| `quality` | `int` | Track quality bitmask |
| `trkPt` | `float` | Track transverse momentum |
| `trkEta` | `float` | Track pseudorapidity |
| `trkPhi` | `float` | Track azimuthal angle |

#### PDG ID to PFCandidate ParticleType Mapping

The C++ function `createRecoPFCandidate()` in `TranslationToRecoFormat.cc` maps
scouting PDG IDs to `reco::PFCandidate::ParticleType` and assigns particle masses:

| abs(pdgId) | Particle | ParticleType | Mass (GeV) | Charged |
|---|---|---|---|---|
| 211 | Charged pion | `h` (charged hadron) | 0.13957 | Yes |
| 11 | Electron | `e` | 0.00051 | Yes |
| 13 | Muon | `mu` | 0.10566 | Yes |
| 22 | Photon | `gamma` | 0 | No |
| 130 | K0_L | `h0` (neutral hadron) | 0.49767 | No |
| 1 | HF hadron | `h_HF` | 0 | No |
| 2 | HF EM | `egamma_HF` | 0 | No |
| 0 | Invalid | `X` | 0 | No |

Mass values are read from `HepPDT::ParticleDataTable` when available, falling back
to hardcoded defaults.

#### Track Presence Filter: `hasTrack()`

Not all PF candidates have associated tracks. The utility function
`hltScoutingRun3::hasTrack()` in `Run3ScoutingUtils.cc` returns `false` for:

- Neutral particles: `pdgId` in {22, 130, 1, 2, 0}
- Particles with no valid fit: `normchi2 >= 999` (sentinel value)

Only particles passing this check get track objects built and attached.

#### Relative Track Variable Decoding

Scouting stores track kinematics in either absolute or relative-to-particle form.
When `relative_trk_vars()` is `true`, the producer recovers absolute values:

```cpp
trkPt  = part.trk_pt()  + part.pt()    // relative pT -> absolute pT
trkEta = part.trk_eta() + part.eta()   // relative eta -> absolute eta
trkPhi = part.trk_phi() + part.phi()   // relative phi -> absolute phi
```

### Step 3: Direct PF Jet Translation

**Producer:** `SimpleRun3ScoutingPFJet2RecoPFJetProducer`
**Module label:** `recoScoutingPFJet`

Converts HLT-packed jets directly to `reco::PFJet`, preserving energy fractions,
multiplicities, and jet area. No reclustering is performed; these are the original
HLT jet definitions.

### Step 4: Scouting Track Translation

**Producer:** `SimpleRun3ScoutingTrack2RecoTrackProducer`
**Module label:** `recoScoutingTrack`

Converts `Run3ScoutingTrack` objects to `reco::Track` with full 5D curvilinear
covariance matrices. The `createRecoTrack(const Run3ScoutingTrack&)` function
reconstructs:

- Reference point (vx, vy, vz) from the scouting track vertex
- 3D momentum from (pT, eta, phi)
- Full 15-element covariance matrix: q/p, lambda, phi, dxy, dsz and all cross-terms
- Hit pattern from pixel + strip hit counts (approximate layer assignment)
- Track quality set to `confirmed`

### Step 5-6: Lost Track Recovery

**Producer (Step 5):** `Run3ScoutingLostTrackProducer` -> `scoutingLostTrack`
**Producer (Step 6):** `SimpleRun3ScoutingTrack2RecoTrackProducer` -> `recoScoutingLostTrack`

Identifies scouting tracks that were NOT matched to any PF candidate (via the
match index ValueMap), then converts them to `reco::Track`. These "lost tracks"
provide additional tracking information for vertex reconstruction.

### Step 7: Track Merging

**Producer:** `CandMerger` -> `recoScoutingTrackMerged`

Merges the PF-associated tracks (`recoScoutingPFCandidate:track`) with the lost
tracks (`recoScoutingLostTrack`) into a single combined collection for downstream
vertex fitting.

### Step 8: Primary Vertex Translation

**Producer:** `SimpleRun3ScoutingVertex2RecoVertexProducer` -> `recoScoutingPrimaryVertex`

Converts HLT-packed vertices to `reco::Vertex`, including:
- Position (x, y, z) with full error matrix (diagonal + off-diagonal covariances)
- Chi-squared, ndof, tracks size
- Validity flag (fake vertices are flagged)

The off-diagonal covariance terms (xy, xz, yz) were added to the scouting format
in early 2024.

### Step 9: Muon Translation

**Producer:** `SimpleRun3ScoutingMuon2PatMuonProducer`
**Module labels:** `patScoutingMuonNoVtx`, `patScoutingMuonVtx`

Two instances run in parallel for muons reconstructed with and without vertex
constraints. Each converts `Run3ScoutingMuon` to `pat::Muon` using
`createPatMuon()`, which fills the four-momentum, charge, vertex position, and
muon type flags.

## Complete Translation Task

```python
scoutingTranslationTask = cms.Task(
    patScoutingMuonNoVtx,              # Muons (no vertex)
    patScoutingMuonVtx,                # Muons (with vertex)
    scoutingParticleMatchTrackIndex,   # PF-Track matching
    recoScoutingPFCandidate,           # PF candidates + tracks + ValueMaps
    recoScoutingPFJet,                 # Direct HLT jets
    recoScoutingTrack,                 # Full scouting tracks
    scoutingLostTrack,                 # Unmatched tracks (scouting format)
    recoScoutingLostTrack,             # Unmatched tracks (reco format)
    recoScoutingTrackMerged,           # All tracks combined
    recoScoutingPrimaryVertex,         # HLT vertices -> reco vertices
)
```

## ValueMap Mechanism

ValueMaps are CMSSW's mechanism for associating extra per-object variables to an
existing collection without modifying the collection's data format. The 11 ValueMaps
produced by the PFCandidate producer are keyed on the `recoScoutingPFCandidate`
collection handle. Downstream consumers (TagInfo producers, NanoAOD tables) retrieve
track-level information from these maps using:

```cpp
edm::ValueMap<float> dxy_map = iEvent.get(dxy_token_);
float dxy = dxy_map[pfCandRef];
```

This design keeps the `reco::PFCandidate` objects compatible with standard CMSSW
algorithms while carrying scouting-specific metadata through the event.

## HLT-Level Variable Preservation

Several HLT-computed quantities are preserved through the translation:

- **B-tag scores:** Not directly translated here; they are recomputed from reclustered
  jets via the HLT ParticleNet and UParT tagger chains.
- **Jet energy fractions:** Preserved in the direct jet translation (Step 3) via
  `reco::PFJet::Specific` fields (charged/neutral hadron, EM, HF, muon energies).
- **Track quality flags:** Stored as ValueMap `quality` and also set on the
  `reco::Track` quality mask.
- **Vertex association index:** Stored as ValueMap `vertexIndex`, indicating which
  HLT primary vertex each particle was assigned to.
