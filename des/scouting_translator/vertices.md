# Primary and Secondary Vertex Reconstruction

## Overview

Vertex reconstruction (`Run3ScoutingSecondaryVertex_cff.py`) builds primary vertices
(PV) from scouting tracks and secondary vertices (SV) using the Inclusive Vertex
Finder (IVF). These vertices are essential for:

- **Primary vertices:** jet-track association, pileup suppression, impact parameter
  computation, PFCandidate vertex sorting
- **Secondary vertices:** b-tagging inputs (both HLT ParticleNet and UParT taggers
  consume SV collections), displaced vertex identification for heavy flavor decays

The vertex reconstruction chain feeds directly into the jet tagging pipeline. Both
the `DeepBoostedJetTagInfoProducer` (HLT PNet) and
`UnifiedParticleTransformerAK4TagInfoProducer` (UParT) require primary and secondary
vertex collections as inputs.

## Primary Vertex Reconstruction

Primary vertices are reconstructed in a three-step chain: fitting, quality selection,
and fake rejection.

### Step 1: Vertex Fitting

**Producer:** `PrimaryVertexProducer`
**Module label:** `scoutingVerticesPF`

```python
scoutingVerticesPF = cms.EDProducer("PrimaryVertexProducer",
    TrackLabel = cms.InputTag("recoScoutingPFCandidate:track"),
    beamSpotLabel = cms.InputTag("onlineBeamSpot"),
    vertexCollections = cms.VPSet(
        cms.PSet(
            label = cms.string(""),
            algorithm = cms.string("AdaptiveVertexFitter"),
            chi2cutoff = cms.double(3.0),
            useBeamConstraint = cms.bool(False),
            minNdof = cms.double(0.0),
            maxDistanceToBeam = cms.double(1.0),
        ),
        cms.PSet(
            label = cms.string("WithBS"),
            algorithm = cms.string("AdaptiveVertexFitter"),
            chi2cutoff = cms.double(3.0),
            useBeamConstraint = cms.bool(True),
            minNdof = cms.double(0.0),
            maxDistanceToBeam = cms.double(1.0),
        ),
    ),
    TkFilterParameters = cms.PSet(
        minSiliconLayersWithHits = cms.int32(5),
        minPixelLayersWithHits = cms.int32(2),
        minPt = cms.double(0.0),
        maxEta = cms.double(100.0),
        maxNormalizedChi2 = cms.double(20.0),
        maxD0Significance = cms.double(999.0),
        trackQuality = cms.string("any"),
        algorithm = cms.string("filter"),
    ),
    TkClusParameters = cms.PSet(
        algorithm = cms.string("DA_vect"),
        TkDAClusParameters = cms.PSet(
            zmerge = cms.double(0.01),
            Tstop = cms.double(0.5),
            d0CutOff = cms.double(999.0),
            dzCutOff = cms.double(4.0),
            vertexSize = cms.double(0.15),
            coolingFactor = cms.double(0.6),
            Tpurge = cms.double(2.0),
            Tmin = cms.double(2.4),
            uniquetrkweight = cms.double(0.9),
        ),
    ),
)
```

**Input tracks:** `recoScoutingPFCandidate:track` -- these are the reco::Track objects
produced by the translation layer from matched scouting tracks (not the direct
scouting track conversion, but tracks built from PF-particle-matched scouting tracks
with full quality information).

**Track filtering parameters:**

| Parameter | Value | Purpose |
|---|---|---|
| `minSiliconLayersWithHits` | 5 | Minimum silicon tracker layers (pixel + strip) |
| `minPixelLayersWithHits` | 2 | Minimum pixel layers |
| `minPt` | 0.0 GeV | No pT cut (accept all tracks) |
| `maxEta` | 100.0 | No eta cut (accept all tracks) |
| `maxNormalizedChi2` | 20.0 | Maximum track fit chi2/ndof |
| `maxD0Significance` | 999.0 | Effectively no impact parameter cut |
| `trackQuality` | "any" | Accept tracks of any quality level |

**Clustering algorithm:** Deterministic Annealing vectorized (`DA_vect`). This
algorithm clusters tracks in z based on their longitudinal position, using an
annealing schedule to progressively resolve vertex candidates:

- `dzCutOff = 4.0` cm -- maximum z separation to consider tracks for the same vertex
- `vertexSize = 0.15` cm -- scale parameter for vertex resolution
- `coolingFactor = 0.6` -- temperature reduction per annealing step
- `zmerge = 0.01` cm -- merge vertices closer than this distance

**Vertex fitting:** `AdaptiveVertexFitter` iteratively assigns track weights
(0 to 1) based on compatibility with the vertex, with `chi2cutoff = 3.0` determining
the chi2 threshold for downweighting outlier tracks.

Two vertex collections are produced: one without beam constraint (default) and one
with beam constraint (`"WithBS"`).

**Output:** `reco::VertexCollection` -- fitted primary vertices.

### Step 2: Quality Selection

**Producer:** `PrimaryVertexObjectFilter`
**Module label:** `scoutingVerticesPFSelector`

```python
scoutingVerticesPFSelector = cms.EDFilter("PrimaryVertexObjectFilter",
    src = cms.InputTag("scoutingVerticesPF"),
    filter = cms.bool(False),
    filterParams = cms.PSet(
        maxRho = cms.double(2.0),
        maxZ = cms.double(24.0),
        minNdof = cms.double(4.0),
    ),
)
```

| Quality Cut | Value | Purpose |
|---|---|---|
| `minNdof` | 4.0 | Reject poorly constrained vertices |
| `maxRho` | 2.0 cm | Reject vertices far from beam axis (transverse) |
| `maxZ` | 24.0 cm | Reject vertices far from IP (longitudinal) |

The `filter = False` setting means this module does not veto events; it only
selects vertices into a filtered collection.

**Output:** Filtered `reco::VertexCollection`.

### Step 3: Fake Vertex Rejection

**Producer:** `VertexSelector`
**Module label:** `scoutingVerticesPFFilter`

```python
scoutingVerticesPFFilter = cms.EDFilter("VertexSelector",
    src = cms.InputTag("scoutingVerticesPFSelector"),
    cut = cms.string("!isFake"),
    filter = cms.bool(True),
)
```

Removes fake vertices (where `isFake()` returns true). The `filter = True` flag
means that if no valid vertex survives, the event would be rejected from the path.
In practice, this runs inside a `cms.Task` where the filter behavior may not apply
as a path-level veto.

**Output:** `scoutingVerticesPFFilter` -- final primary vertex collection used by
jet reclustering and tagging producers.

## Secondary Vertex Reconstruction

Secondary vertices are reconstructed using the Inclusive Vertex Finder (IVF) chain,
which identifies displaced vertices from track pairs consistent with heavy flavor
hadron decays (B and D mesons, baryons).

### Step 1: Inclusive Vertex Finding

**Producer:** `inclusiveCandidateVertexFinder` (cloned)
**Module label:** `scoutingDeepInclusiveVertexFinderPF`

```python
scoutingDeepInclusiveVertexFinderPF = inclusiveCandidateVertexFinder.clone(
    beamSpot = cms.InputTag("onlineBeamSpot"),
    primaryVertices = cms.InputTag("scoutingVerticesPFFilter"),
    tracks = cms.InputTag("recoScoutingPFCandidate"),
    minHits = cms.uint32(8),
)
```

The IVF algorithm:

1. Forms all pairs of tracks from the PF candidate collection
2. Fits each pair to a common vertex using the `AdaptiveVertexFitter`
3. Retains vertex seeds that pass a flight distance significance cut
4. Iteratively adds compatible tracks to grow vertex candidates
5. Filters vertices by track multiplicity and quality

**Key parameter:** `minHits = 8` -- this is the HLT default (offline reconstruction
uses `minHits = 0`). The higher threshold ensures track quality in the reduced-
precision scouting environment but may reduce SV finding efficiency for tracks
with fewer hits.

**Input tracks:** `recoScoutingPFCandidate` -- the PF candidate collection (the IVF
uses the tracks embedded in/associated with the PF candidates).

**Output:** Raw inclusive vertex candidates.

### Step 2: First Vertex Merging

**Producer:** `candidateVertexMerger` (cloned)
**Module label:** `scoutingDeepInclusiveSecondaryVerticesPF`

```python
scoutingDeepInclusiveSecondaryVerticesPF = candidateVertexMerger.clone(
    secondaryVertices = cms.InputTag("scoutingDeepInclusiveVertexFinderPF"),
)
```

Merges nearby vertex candidates that likely originate from the same decay chain.
Uses the default merging parameters (shared track fraction and distance thresholds).

**Output:** Merged secondary vertex candidates.

### Step 3: Track-Vertex Arbitration

**Producer:** `candidateVertexArbitrator` (cloned)
**Module label:** `scoutingDeepTrackVertexArbitratorPF`

```python
scoutingDeepTrackVertexArbitratorPF = candidateVertexArbitrator.clone(
    beamSpot = cms.InputTag("onlineBeamSpot"),
    primaryVertices = cms.InputTag("scoutingVerticesPFFilter"),
    tracks = cms.InputTag("recoScoutingPFCandidate"),
    secondaryVertices = cms.InputTag("scoutingDeepInclusiveSecondaryVerticesPF"),
)
```

When a track is compatible with multiple secondary vertices, the arbitrator assigns
it to the best-fit vertex based on chi2 compatibility and vertex fit quality. This
step resolves ambiguities from overlapping decay chains (e.g., a B meson decaying
to a D meson, producing two displaced vertices that share tracks).

**Output:** Arbitrated secondary vertex collection with unique track assignments.

### Step 4: Final Vertex Merging

**Producer:** `candidateVertexMerger` (cloned)
**Module label:** `scoutingDeepInclusiveMergedVerticesPF`

```python
scoutingDeepInclusiveMergedVerticesPF = candidateVertexMerger.clone(
    secondaryVertices = cms.InputTag("scoutingDeepTrackVertexArbitratorPF"),
    maxFraction = cms.double(0.2),
    minSignificance = cms.double(10.0),
)
```

| Parameter | Value | Purpose |
|---|---|---|
| `maxFraction` | 0.2 | Merge vertices sharing > 80% of their tracks |
| `minSignificance` | 10.0 | Minimum flight distance significance to keep a vertex |

The `minSignificance = 10.0` cut ensures only vertices with strong displacement
evidence survive. This is a tight requirement: the flight distance from the PV
must exceed 10 times its uncertainty.

**Output:** `scoutingDeepInclusiveMergedVerticesPF` -- the final secondary vertex
collection consumed by both HLT ParticleNet and UParT TagInfo producers.

## How Vertices Feed into B-Tagging

### Primary Vertices in TagInfo Production

Both TagInfo producers use primary vertices for:

- **Impact parameter computation:** Track d0, dz, and their significances are computed
  relative to the primary vertex
- **Vertex association:** The `PFCandidatePrimaryVertexSorter` assigns jet constituents
  to primary vertices; this mapping (via the `"original"` ValueMap) is consumed by
  the `DeepBoostedJetTagInfoProducer`
- **Charged hadron subtraction:** Tracks from pileup vertices can be identified and
  downweighted (though PUPPI is not used in scouting)

The UParT TagInfo producer uses `scoutingVerticesPF` (unfiltered) as its primary
vertex input, while the HLT PNet TagInfo uses `scoutingVerticesPFFilter` (filtered).

### Secondary Vertices in TagInfo Production

Both taggers consume `scoutingDeepInclusiveMergedVerticesPF` and extract per-SV
features including:

- SV 4-momentum (pt, eta, phi, mass from daughter tracks)
- SV position (x, y, z) relative to the primary vertex
- Flight distance and flight distance significance (2D and 3D)
- SV chi2/ndof (vertex fit quality)
- Number of daughter tracks
- Energy ratio (SV energy / jet energy)

The UParT model accepts up to 5 secondary vertices per jet, each encoded as a
15-feature vector plus 4 pairwise features.

## Track-Vertex Association

The connection between tracks and vertices flows through several paths:

```
recoScoutingPFCandidate:track
    |
    +--> PrimaryVertexProducer (scoutingVerticesPF)
    |       Track -> PV clustering via DA_vect
    |
    +--> inclusiveCandidateVertexFinder (scoutingDeepInclusiveVertexFinderPF)
    |       Track pairs -> SV seeds -> grown vertices
    |
    +--> PFCandidatePrimaryVertexSorter
            PF candidates sorted by PV association
            Used by TagInfo producers to compute jet-level vertex features
```

## NanoAOD Output Tables

### Primary Vertex Table (`ScoutingPV`)

```python
process.scoutingPrimaryVertexPFTable = simpleVertexFlatTableProducer.clone(
    src = cms.InputTag("scoutingVerticesPF"),
    name = cms.string("ScoutingPV"),
    variables = cms.PSet(
        x    = Var("position().x()", float, precision=10),
        y    = Var("position().y()", float, precision=10),
        z    = Var("position().z()", float, precision=16),
        ndof = Var("ndof()", float, precision=8),
        chi2 = Var("normalizedChi2()", float, precision=8),
        isFake = Var("isFake()", bool),
    ),
)
```

### Secondary Vertex Table (`ScoutingSV`)

```python
process.scoutingSecondaryVertexTable = simpleSecondaryVertexFlatTableProducer.clone(
    src = cms.InputTag("scoutingDeepInclusiveMergedVerticesPF"),
    name = cms.string("ScoutingSV"),
    variables = cms.PSet(
        P4Vars,                                              # pt, eta, phi, mass
        x       = Var("position().x()", float, precision=10),
        y       = Var("position().y()", float, precision=10),
        z       = Var("position().z()", float, precision=14),
        ndof    = Var("vertexNdof()", float, precision=8),
        chi2    = Var("vertexNormalizedChi2()", float, precision=8),
        ntracks = Var("numberOfDaughters()", "uint8"),
    ),
)
```

## Task Definitions

```python
# ESProducer for TransientTracks (required by vertex fitters)
scoutingTransientTrackBuilderTask = cms.Task(TransientTrackBuilderESProducer)

# Primary vertex chain
scoutingPrimaryVertexPFTask = cms.Task(
    scoutingVerticesPF,           # Fitting
    scoutingVerticesPFSelector,   # Quality selection
    scoutingVerticesPFFilter,     # Fake rejection
)

# Secondary vertex chain
scoutingSecondaryVertexTask = cms.Task(
    scoutingDeepInclusiveVertexFinderPF,         # IVF
    scoutingDeepInclusiveSecondaryVerticesPF,     # First merge
    scoutingDeepTrackVertexArbitratorPF,          # Track arbitration
    scoutingDeepInclusiveMergedVerticesPF,        # Final merge
)
```

All three tasks are registered into `scoutingNanoTaskCommon` by either
`addScoutingSecondaryVertex()` or `addAll()` in `ScoutingNanoCustomisation_cff.py`.

## Scouting-Specific Considerations

1. **Track quality in scouting:** Scouting tracks have approximate hit patterns
   reconstructed from limited information (pixel/strip hit counts, lost inner hits).
   The `PrimaryVertexProducer` track filter accepts `trackQuality = "any"` to avoid
   rejecting tracks with imprecise quality assignments.

2. **No timing information:** `useTiming = False` throughout because scouting data
   does not include track timing measurements from the MTD.

3. **HLT vs offline minHits:** The IVF uses `minHits = 8` (HLT default) rather than
   the offline default of 0. This trades SV reconstruction efficiency for purity in
   the scouting context.

4. **Beam spot source:** All vertex producers use `onlineBeamSpot` (extracted from
   online conditions) rather than the offline beam spot.
