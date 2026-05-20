# Scouting Object Collections: PF Candidates, Leptons, Photons, MET

This document describes the non-jet scouting collections in the NanoAOD output.
These originate from the standard CMS scouting NanoAOD customization
(`custom_run3scouting_cff`) and from the ScoutingTranslator package.

---

## 1. ScoutingParticle (Raw Scouting PF Particles)

The `ScoutingParticle` collection stores the raw HLT-level PF particles from
`hltScoutingPFPacker`, before any translation to reco format. This is the
most basic particle-level information available in scouting.

Typical branches include:

| Branch | Type | Description |
|--------|------|-------------|
| `ScoutingParticle_pt` | float | Transverse momentum (GeV) |
| `ScoutingParticle_eta` | float | Pseudorapidity |
| `ScoutingParticle_phi` | float | Azimuthal angle |
| `ScoutingParticle_pdgId` | int | PDG particle ID |
| `ScoutingParticle_vertex` | int | Vertex index |
| `ScoutingParticle_normchi2` | float | Track normalized chi-squared |
| `ScoutingParticle_dz` | float | Longitudinal impact parameter |
| `ScoutingParticle_dxy` | float | Transverse impact parameter |
| `ScoutingParticle_dzsig` | float | dz significance |
| `ScoutingParticle_dxysig` | float | dxy significance |
| `ScoutingParticle_lostInnerHits` | int | Number of lost inner tracker hits |
| `ScoutingParticle_quality` | int | Track quality flag |
| `ScoutingParticle_trk_pt` | float | Track pT (may be relative-encoded) |
| `ScoutingParticle_trk_eta` | float | Track eta |
| `ScoutingParticle_trk_phi` | float | Track phi |

### Track Variable Encoding

Track variables may be stored in relative form depending on the HLT packer
version. The ScoutingTranslator handles this decoding automatically.

Not all scouting particles have tracks. The `hasTrack()` utility returns
`false` for photons (22), K0-long (130), HF particles (1, 2), invalid (0),
and particles with normchi2 >= 999.

---

## 2. ScoutingPFCandidate (Translated PF Candidates)

The `ScoutingPFCandidate` collection is the reco-format translation of
scouting particles, produced by `addScoutingPFCandidate()`. This is used
as input for jet reclustering and provides analysis-ready PF candidate
information.

The translation is performed by
`Run3ScoutingParticle2RecoPFCandidateProducer`, which converts HLT
`Run3ScoutingParticle` objects into `reco::PFCandidate` objects and attaches
11 ValueMaps for track-level information.

---

## 3. ScoutingMuon

HLT scouting muons, stored from two sources: `hltScoutingMuonPackerNoVtx`
(muons without vertex constraint) and `hltScoutingMuonPackerVtx` (muons with
vertex constraint). These are translated to `pat::Muon` format by
`SimpleRun3ScoutingMuon2PatMuonProducer`.

Typical branches:

| Branch | Type | Description |
|--------|------|-------------|
| `ScoutingMuon_pt` | float | Transverse momentum (GeV) |
| `ScoutingMuon_eta` | float | Pseudorapidity |
| `ScoutingMuon_phi` | float | Azimuthal angle |
| `ScoutingMuon_mass` | float | Mass (GeV) |
| `ScoutingMuon_charge` | int | Electric charge (+1/-1) |
| `ScoutingMuon_pdgId` | int | PDG ID (+/-13) |
| `ScoutingMuon_trk_pt` | float | Track transverse momentum |
| `ScoutingMuon_trk_eta` | float | Track pseudorapidity |
| `ScoutingMuon_trk_phi` | float | Track azimuthal angle |
| `ScoutingMuon_dxy` | float | Transverse impact parameter (cm) |
| `ScoutingMuon_dz` | float | Longitudinal impact parameter (cm) |
| `ScoutingMuon_nValidPixelHits` | int | Number of valid pixel hits |
| `ScoutingMuon_nValidStripHits` | int | Number of valid strip hits |
| `ScoutingMuon_nTrackerLayersWithMeasurement` | int | Tracker layers with hits |
| `ScoutingMuon_chi2` | float | Track chi-squared |
| `ScoutingMuon_ndof` | float | Track degrees of freedom |
| `ScoutingMuon_type` | int | Muon type bitmask |
| `ScoutingMuon_ecalIso` | float | ECAL isolation |
| `ScoutingMuon_hcalIso` | float | HCAL isolation |
| `ScoutingMuon_trackIso` | float | Tracker isolation |
| `ScoutingMuon_nMatchedStations` | int | Number of matched muon stations |
| `ScoutingMuon_vtxIdx` | int | Vertex index for this muon |

Scouting muons have reduced ID information compared to offline PAT muons.
There is no full muon ID (tight/medium/loose) or PF-based isolation. The
isolation variables are calorimeter-based (ecalIso, hcalIso) and tracker-based.

---

## 4. ScoutingElectron

HLT scouting electrons, translated by
`Run3ScoutingElectron2PatElectronProducer`.

Typical branches:

| Branch | Type | Description |
|--------|------|-------------|
| `ScoutingElectron_pt` | float | Transverse momentum (GeV) |
| `ScoutingElectron_eta` | float | Pseudorapidity |
| `ScoutingElectron_phi` | float | Azimuthal angle |
| `ScoutingElectron_mass` | float | Mass (GeV) |
| `ScoutingElectron_charge` | int | Electric charge |
| `ScoutingElectron_dEtaIn` | float | Delta-eta at inner layer |
| `ScoutingElectron_dPhiIn` | float | Delta-phi at inner layer |
| `ScoutingElectron_sigmaIetaIeta` | float | Shower shape (sigma ieta-ieta) |
| `ScoutingElectron_hOverE` | float | H/E ratio |
| `ScoutingElectron_ooEMOop` | float | |1/E - 1/p| |
| `ScoutingElectron_missingHits` | int | Missing inner tracker hits |
| `ScoutingElectron_ecalIso` | float | ECAL isolation |
| `ScoutingElectron_hcalIso` | float | HCAL isolation |
| `ScoutingElectron_trackIso` | float | Tracker isolation |
| `ScoutingElectron_r9` | float | R9 shower shape variable |
| `ScoutingElectron_sMin` | float | Minimum cluster spread |
| `ScoutingElectron_sMaj` | float | Maximum cluster spread |
| `ScoutingElectron_seedId` | int | Seed crystal ID |

No full electron MVA ID is available at scouting level. Cut-based ID must
be applied in analysis using the available shower shape and isolation variables.

---

## 5. ScoutingPhoton

HLT scouting photons with calorimeter-level information. Branches follow
the same pattern as ScoutingElectron: pt, eta, phi, mass, sigmaIetaIeta,
hOverE, ecalIso, hcalIso, r9, sMin, sMaj, seedId.

---

## 6. ScoutingMET

Scouting-level missing transverse energy from the HLT scouting MET producer.

| Branch | Type | Description |
|--------|------|-------------|
| `ScoutingMET_pt` | float | MET magnitude (GeV) |
| `ScoutingMET_phi` | float | MET azimuthal direction |
| `ScoutingMET_sumEt` | float | Scalar sum of transverse energy (GeV) |

This is a singleton collection (one value per event). Unlike offline PuppiMET
or PFMET, scouting MET does not include Type-I JEC corrections or dedicated
MET filters. The covariance matrix elements (covXX, covXY, covYY) that are
available in standard NanoAOD PuppiMET are not present here.

---

## 7. ScoutingRho

Scouting energy density.

| Branch | Type | Description |
|--------|------|-------------|
| `ScoutingRho_rho` | float | Median energy density per unit area |

Singleton collection. Used for pileup corrections in scouting context.

---

## 8. Primary Vertex Collections

### 8.1 ScoutingPrimaryVertex (HLT-level)

Direct translation of HLT scouting vertices from `hltScoutingPrimaryVertexPacker`.
Produced by `SimpleRun3ScoutingVertex2RecoVertexProducer`.

### 8.2 ScoutingPV (Refitted from Scouting Tracks)

Produced by the ScoutingTranslator vertex reconstruction chain. Uses
`PrimaryVertexProducer` with adaptive vertex fitter on translated scouting
tracks, followed by quality filtering (minNdof >= 4, maxRho < 2 cm,
maxZ < 24 cm, !isFake).

| Branch | Type | Description |
|--------|------|-------------|
| `ScoutingPV_x` | float | x position (cm), precision 10 |
| `ScoutingPV_y` | float | y position (cm), precision 10 |
| `ScoutingPV_z` | float | z position (cm), precision 16 |
| `ScoutingPV_ndof` | float | Number of degrees of freedom |
| `ScoutingPV_chi2` | float | Normalized chi-squared (chi2/ndof) |
| `ScoutingPV_isFake` | bool | Whether the vertex is fake |

The first vertex in the collection (`ScoutingPV[0]`) is the best primary
vertex, used as reference for impact parameter calculations.

---

## 9. Secondary Vertex Collection (ScoutingSV)

Produced by deep inclusive vertex finding on scouting tracks, with merging
and arbitration. Source: `scoutingDeepInclusiveMergedVerticesPF`.

| Branch | Type | Description |
|--------|------|-------------|
| `ScoutingSV_pt` | float | SV transverse momentum (GeV) |
| `ScoutingSV_eta` | float | SV pseudorapidity |
| `ScoutingSV_phi` | float | SV azimuthal angle |
| `ScoutingSV_mass` | float | SV invariant mass (GeV) |
| `ScoutingSV_x` | float | x position (cm) |
| `ScoutingSV_y` | float | y position (cm) |
| `ScoutingSV_z` | float | z position (cm) |
| `ScoutingSV_ndof` | float | Number of degrees of freedom |
| `ScoutingSV_chi2` | float | Normalized chi-squared |
| `ScoutingSV_ntracks` | uint8 | Number of tracks in vertex |

---

## 10. V0 Candidates

### ScoutingKshort

| Branch | Type | Description |
|--------|------|-------------|
| `ScoutingKshort_pt` | float | pT (GeV) |
| `ScoutingKshort_eta` | float | Pseudorapidity |
| `ScoutingKshort_phi` | float | Azimuthal angle |
| `ScoutingKshort_mass` | float | Invariant mass (GeV) |
| `ScoutingKshort_charge` | int | Charge (0 for neutral) |
| `ScoutingKshort_pdgId` | int | PDG ID (310) |

### ScoutingLambda

Same structure as ScoutingKshort, with `ScoutingLambda_` prefix and
pdgId = 3122.

---

## 11. OnlineBeamSpot

| Branch | Type | Description |
|--------|------|-------------|
| `OnlineBeamSpot_x0` | float | x position of beam spot |
| `OnlineBeamSpot_y0` | float | y position of beam spot |
| `OnlineBeamSpot_z0` | float | z position of beam spot |
| `OnlineBeamSpot_sigmaZ` | float | Beam spot sigma in z |
| `OnlineBeamSpot_type` | int | Beam spot type |

Singleton collection. Used by SV reconstruction and B-tagging feature
extraction as the reference position for impact parameter calculations.
