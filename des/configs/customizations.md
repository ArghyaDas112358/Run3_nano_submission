# Customization Modules: customize.py and addVars.py

The `customizations/` directory contains two Python modules that add
analysis-specific variables and modifications to the standard NanoAOD output.
These modules target the HH->bbtautau analysis needs, providing extended tau
variables, lepton lifetime information, PF candidate indexing, and vertex
refinements.

## customize.py

**Path**: `/home/das214/HHtobbtautau/Run3_nano_submission/customizations/customize.py`

**Based on**: CMS Tau POG NanoProd (`cms-tau-pog/NanoProd`), with no selection
cuts applied (all objects are kept).

### Top-Level Entry Point: customize()

```python
def customize(process):
    addMonitoring(process)
    process = customizeTaus(process)
    process = customizeBoostedTaus(process)
    process = addTrackVarsToTimeLifeInfo(process)
    process = addIPCovToLeptons(process)
    process = customizePV(process)
    return process
```

This is the function imported by all standard MC and Data configs via:
```python
from DAZSLE.DAZSLE.customize import customize
process = customize(process)
```

### Function Breakdown

#### customizeGenParticles(process)

**Status**: Currently commented out in `customize()` (conflicts with BTV
variables).

Extends the gen particle selection to keep full decay chains of important
particles and leptons. Adds production vertex coordinates (vx, vy, vz) to the
gen particle table.

Particles kept:
- Leptons: e, nu_e, mu, nu_mu, tau, nu_tau (pdgId 11-16)
- Important: top (6), Z (23), W (24), H (25), H' (35), graviton (39),
  heavy neutral lepton variants (9990012, 9900012), stau (1000015)

#### customizeTaus(process)

Adds the following variables to `process.tauTable.variables`:

| Variable | Expression | Description |
|---|---|---|
| `dxyErr` | `dxy_error` | Transverse IP error |
| `ip3d` | `ip3d` | 3D impact parameter |
| `ip3dErr` | `ip3d_error` | 3D IP error |
| `hasSV` | `hasSecondaryVertex` | Whether tau has an SV |
| `flightLengthX/Y/Z` | `flightLength().x/y/z()` | SV flight length components |
| `flightLengthSig` | `flightLengthSig()` | Flight length significance |
| `dzErr` | `leadChargedHadrCand.dzError()` | Leading track dz error (lazy eval) |
| `leadTkNormChi2` | `leadingTrackNormChi2()` | Leading track normalized chi2 |
| `leadChCandEtaAtEcalEntrance` | `etaAtEcalEntranceLeadChargedCand` | Leading charged candidate eta at ECAL |

These variables are critical for tau identification and lifetime-based
discrimination in the HH->bbtautau analysis.

#### customizeBoostedTaus(process)

Sets a minimal selection cut for boosted taus:
```python
process.finalBoostedTaus.cut = "pt > 18 && tauID('decayModeFindingNewDMs')"
```

The commented-out code shows that DeepTau score cuts were previously considered
but removed to keep all boosted tau candidates.

#### customizePV(process)

Calls `addExtendVertexInfo(process)` from the NanoAOD lepton time-life info
module, then adds:

| Variable | Expression | Description |
|---|---|---|
| `ndof` | `ndof()` | Vertex degrees of freedom |
| `valid` | `isValid()` | Whether the PV fit converged |

#### addSpinnerWeights(process)

**Status**: Currently commented out (leads to errors).

Would add TauSpinner reweighting tables for spin correlation studies. Produces
weights for different CP mixing angles (theta = 0, 0.25, 0.5, -0.25, 0.375).

#### addIPCovToLeptons(process)

Adds the full 3x3 IP covariance matrix to electron, muon, and tau time-life
info tables. The six independent elements are stored as:

```
IP_cov00, IP_cov10, IP_cov11, IP_cov20, IP_cov21, IP_cov22
```

These correspond to the (x,x), (y,x), (y,y), (z,x), (z,y), (z,z) covariance
elements of the impact parameter measurement.

### Era-Dependent Settings

```python
era_dependent_settings = cms.PSet(cmsE=cms.double(13600.0))
(~run3_common).toModify(era_dependent_settings, cmsE=13000.0)
```

The center-of-mass energy defaults to 13.6 TeV for Run 3 and falls back to
13 TeV for Run 2 eras.

## addVars.py

**Path**: `/home/das214/HHtobbtautau/Run3_nano_submission/customizations/addVars.py`

**Based on**: UHH NanoGen customizations (`uhh-cms/nanogen`).

### Architecture

This module defines a set of modular customization functions that can be
composed together. It provides both high-level convenience functions and
low-level building blocks.

### High-Level Functions

```python
def customize_run3_v14(process, **kwargs):
    return _customize(process, Run.III, NanoVersion.V14, **kwargs)
```

The `_customize()` function applies all customizations in order:

1. `update_gen_particles()` (MC only)
2. `add_pv_variables()`
3. `add_tau_variables()`
4. `add_met_variables()`
5. `add_pf_candidates()` (if `pf_candidates=True`)
6. `add_l1t_objects()` (if `l1t_objects=True`)

### PF Candidate Indexing

The most complex addition is the PF candidate system, which provides
particle-level information linked to reconstructed objects.

#### pfCandidateIndexer

An EDProducer that takes packed PF candidates and builds index maps to jets,
fat jets, taus, and boosted taus:

| Parameter | Default Source | Description |
|---|---|---|
| `candidateCollection` | `packedPFCandidates` | Input PF candidates |
| `jetCollection` | `linkedObjects:jets` | AK4 jets |
| `fatJetCollection` | `finalJetsAK8` | AK8 fat jets |
| `tauCollection` | `linkedObjects:taus` | Reconstructed taus |
| `boostedTauCollection` | `linkedObjects:boostedTaus` | Boosted taus |

Outputs:
- `containedPFCandidates` -- Filtered PF candidates contained in at least one
  reconstructed object.
- Index ValueMaps: `jet`, `fatjet`, `tau`, `boostedtau` -- Maps from candidate
  to the index of the containing object.

#### pfCandidateIndicesTable

Produces a NanoAOD flat table (`PFCandidateIndices`) with the index information,
enabling downstream analysis to associate individual PF candidates with their
parent jets/taus.

#### pfCandidateTable

Produces a flat table (`PFCandidate`) with kinematic variables for each
contained PF candidate:

| Variable | Type | Description |
|---|---|---|
| `pt` | float (8-bit) | Transverse momentum |
| `eta` | float (8-bit) | Pseudorapidity |
| `phi` | float (8-bit) | Azimuthal angle |
| `mass` | float (8-bit) | Candidate mass |
| `pdgId` | int32 | Particle type identifier |
| `charge` | int32 | Electric charge |
| `dxy` | float (8-bit) | Transverse impact parameter |
| `dz` | float (8-bit) | Longitudinal impact parameter |

### Additional Tau Variables

The `add_tau_variables()` function adds the same set of variables as
`customize.py`'s `customizeTaus()`, plus lifetime-related track variables
via `addTrackVarsToTimeLifeInfo()` (CMSSW >= 14.0.0).

### MET Covariance Variables

Adds PuppiMET significance matrix elements to `puppiMetTable`:
- `covXX`, `covXY`, `covYY` -- The 2x2 MET covariance matrix.

### L1 Trigger Objects

Lowers selection thresholds on L1 trigger objects for broader acceptance:

| L1 Object | Cut |
|---|---|
| EG (e/gamma) | pT >= 10 GeV |
| Tau | pT >= 20 GeV |
| Jet | pT >= 20 GeV |
| Muon | pT >= 0 GeV |
| EtSum | Types 1, 2, 3, 8, 21 (MET, HT, etc.) |

### Gen Particle Extensions

The `update_gen_particles()` function extends the default NanoAOD gen particle
selection with:
- Full parent/daughter chains for VIP particles: top, gluon, photon, Z, W, H,
  H', A, H+/-, graviton, heavy neutral leptons, stau.
- Full decay history for all leptons.
- Production vertex coordinates (vx, vy, vz) with 10-digit precision.

## How Customizations Are Applied

### Standard Config Flow

```
cmsDriver.py generates config
    |
    v
process = cms.Process('NANO', Run3_2024)
    |
    v
process.load('PhysicsTools.NanoAOD.nano_cff')       <-- Base NanoAOD modules
    |
    v
process = customize(process)                          <-- customize.py (Tau POG)
    |
    v
process = nanoAOD_customizeCommon(process)            <-- CMS common
    |
    v
process = BTVCustomNanoAOD(process)                   <-- BTV customizations
    |
    v
process = customiseEarlyDelete(process)               <-- Memory optimization
```

### Scouting Config Flow

```
process = cms.Process('NANO', Run3_2024)
    |
    v
process.load('PhysicsTools.NanoAOD.nanogen_cff')     <-- Gen-level modules
process.load('...custom_run3scouting_cff')            <-- Scouting modules
    |
    v
process = addScoutingPFCandidate(process)             <-- Scouting PF tables
process = customiseScoutingNano(process)              <-- Scouting NanoAOD
process = customiseScoutingNanoFromMini(process)      <-- MiniAOD adaptation
    |
    v
process = addAll(process)                             <-- ScoutingTranslator
    |                                                     (reclustering + taggers)
    v
process = customizeNanoGENFromMini(process)           <-- Gen from MiniAOD
```

Note that the scouting config does **not** use `customize.py` or `addVars.py`
because the scouting objects have a fundamentally different structure (no PAT
taus, no standard jets).

## Related Files

- `/home/das214/HHtobbtautau/Run3_nano_submission/customizations/customize.py`
- `/home/das214/HHtobbtautau/Run3_nano_submission/customizations/addVars.py`
- `/home/das214/HHtobbtautau/Run3_nano_submission/configs/MC_2024_NANO.py` --
  Example standard config that applies these customizations.
