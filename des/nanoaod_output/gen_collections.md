# Generator-Level Collections (MC Only)

This document describes the generator-level collections present in the scouting
NanoAOD output when processing MC samples. These collections come from the
`nanogenSequence` (nanoAOD_step0), configured via `customizeNanoGENFromMini()`.

Generator-level collections are **absent in data** (both standard data and
scouting data). They are only present when the config is run with the `--mc`
flag, producing NANOAODSIM output.

---

## 1. GenPart (Generator-Level Particles)

The `GenPart` collection stores the generator-level particle content of each
event. The particle selection is configured in `customizeNanoGENFromMini()`
and further refined by `update_gen_particles()` in `addVars.py`.

### Branches

| Branch | Type | Description |
|--------|------|-------------|
| `GenPart_pt` | float | Transverse momentum (GeV) |
| `GenPart_eta` | float | Pseudorapidity |
| `GenPart_phi` | float | Azimuthal angle |
| `GenPart_mass` | float | Mass (GeV) |
| `GenPart_pdgId` | int | PDG particle ID code |
| `GenPart_status` | int | Pythia status code |
| `GenPart_statusFlags` | int | Generator status flags bitmask |
| `GenPart_genPartIdxMother` | int | Index of mother particle in GenPart (-1 if none) |

### Production Vertex Coordinates

When the `update_gen_particles()` customization from `addVars.py` is applied,
three additional branches are added:

| Branch | Type | Description |
|--------|------|-------------|
| `GenPart_vx` | float | x coordinate of production vertex (cm), precision 10 |
| `GenPart_vy` | float | y coordinate of production vertex (cm), precision 10 |
| `GenPart_vz` | float | z coordinate of production vertex (cm), precision 10 |

These vertex coordinates are essential for tau lifetime studies and displaced
vertex analyses.

### Particle Selection

The `addVars.py` customization expands the default gen particle selection
to keep full decay chains of important particles. The selection uses
`finalGenParticles.select`:

```python
# Important particles (full parent+daughter chain):
# pdgId: 6 (top), 21 (gluon), 22 (photon), 23 (Z), 24 (W), 25 (h),
#         35 (H), 36 (A), 37 (H+), 39 (graviton),
#         9990012, 9900012 (heavy neutral leptons), 1000015 (stau)

# Leptons (full decay chain):
# pdgId: 11 (e), 12 (nu_e), 13 (mu), 14 (nu_mu), 15 (tau), 16 (nu_tau)
```

The `keep++` directive retains full parent and daughter chains for leptons
with `isLastCopy()` status, while `keep+` retains parent chains for important
particles.

### statusFlags Bitmask

The `statusFlags` field encodes generator-level status information as a bitmask:

| Bit | Flag | Description |
|-----|------|-------------|
| 0 | isPrompt | Not from hadron, tau, or muon decay |
| 1 | isDecayedLeptonHadron | From a hadron or tau decay |
| 4 | isDirectHadronDecayProduct | Directly from hadron decay |
| 5 | isHardProcess | Part of the hard process |
| 6 | fromHardProcess | Has an ancestor from hard process |
| 7 | isHardProcessTauDecayProduct | From tau in hard process |
| 8 | isDirectHardProcessTauDecayProduct | Direct tau decay in hard process |
| 12 | isFirstCopy | First copy of the particle |
| 13 | isLastCopy | Last copy (before decay) |
| 14 | isLastCopyBeforeFSR | Last copy before final-state radiation |

---

## 2. GenJet (Generator-Level AK4 Jets)

Generator-level jets clustered with anti-kT R=0.4 from stable generator
particles (excluding neutrinos). Used for MC truth matching of reconstructed
scouting jets.

| Branch | Type | Description |
|--------|------|-------------|
| `GenJet_pt` | float | Transverse momentum (GeV) |
| `GenJet_eta` | float | Pseudorapidity |
| `GenJet_phi` | float | Azimuthal angle |
| `GenJet_mass` | float | Mass (GeV) |
| `GenJet_hadronFlavour` | int | Hadron-based flavor (5=b, 4=c, 0=light) |
| `GenJet_partonFlavour` | int | Parton-based flavor |

The `GenJet` table is added to the MC task by `addAll()` in
`ScoutingNanoCustomisation_cff.py`, along with the flavor association
(`genJetFlavourTable`).

Matching from reconstructed to gen jets is done via the `genJetIdx` branch
in the jet MC extension tables (e.g., `ScoutingPFJetRecluster2_genJetIdx`),
which requires the gen jet to have pT > 10 GeV.

---

## 3. GenJetAK8 (Generator-Level AK8 Jets)

Generator-level jets clustered with anti-kT R=0.8. Used for truth matching
of reconstructed AK8 fat jets.

| Branch | Type | Description |
|--------|------|-------------|
| `GenJetAK8_pt` | float | Transverse momentum (GeV) |
| `GenJetAK8_eta` | float | Pseudorapidity |
| `GenJetAK8_phi` | float | Azimuthal angle |
| `GenJetAK8_mass` | float | Mass (GeV) |
| `GenJetAK8_hadronFlavour` | int | Hadron-based flavor |
| `GenJetAK8_partonFlavour` | int | Parton-based flavor |

The `GenJetAK8` table and its flavor association are added by `addAll()`:

```python
process.scoutingNanoTaskMC.add(
    process.genJetAK8Table,
    process.genJetAK8FlavourAssociation,
    process.genJetAK8FlavourTable,
)
```

---

## 4. GenVtx (Generator Vertex)

The primary generator-level interaction vertex.

| Branch | Type | Description |
|--------|------|-------------|
| `GenVtx_x` | float | x position (cm) |
| `GenVtx_y` | float | y position (cm) |
| `GenVtx_z` | float | z position (cm) |
| `GenVtx_t0` | float | Time of vertex (ns) |

Singleton collection. Provides the true interaction point for comparison
with reconstructed vertices.

---

## 5. Pileup Information

| Branch | Type | Description |
|--------|------|-------------|
| `Pileup_nTrueInt` | float | True number of pileup interactions (Poisson mean) |
| `Pileup_nPU` | int | Number of simulated pileup interactions |
| `Pileup_sumEOOT` | int | Early out-of-time pileup |
| `Pileup_sumLOOT` | int | Late out-of-time pileup |
| `Pileup_pudensity` | float | Pileup density (interactions per crossing) |
| `Pileup_gpudensity` | float | Gaussian pileup density |

`Pileup_nTrueInt` is the primary variable used for pileup reweighting in
analysis. Note that scouting data operates at full L1 rate, so pileup
profiles may differ from standard triggered data.

---

## 6. Generator Weights

### GenWeight

| Branch | Type | Description |
|--------|------|-------------|
| `genWeight` | float | Generator-level event weight |

Singleton (single value per event). Used in all MC event weighting.

### LHE Weights

When available from the generator, LHE-level weight variations are stored:

| Branch | Type | Description |
|--------|------|-------------|
| `LHEWeight_originalXWGTUP` | float | Original LHE weight |
| `LHEScaleWeight` | float[] | Scale variation weights (muR, muF) |
| `LHEPdfWeight` | float[] | PDF variation weights |

These are used for systematic uncertainty estimation (scale and PDF variations).

### LHE Particle Information

| Branch | Type | Description |
|--------|------|-------------|
| `LHEPart_pt` | float | LHE particle pT |
| `LHEPart_eta` | float | LHE particle eta |
| `LHEPart_phi` | float | LHE particle phi |
| `LHEPart_mass` | float | LHE particle mass |
| `LHEPart_pdgId` | int | LHE particle PDG ID |
| `LHEPart_status` | int | LHE particle status |
| `nLHEPart` | int | Number of LHE particles |

---

## 7. Tau Lifetime Reweighting Variables

The `customize.py` file adds extended tau and lepton lifetime variables
for MC samples, which are important for tau lifetime studies in
HH->bbtautau:

### Tau Table Extensions

| Branch | Description |
|--------|-------------|
| `Tau_dxyErr` | dxy error |
| `Tau_ip3d` | 3D impact parameter |
| `Tau_ip3dErr` | 3D impact parameter error |
| `Tau_hasSV` | Has secondary vertex (bool) |
| `Tau_flightLengthX/Y/Z` | Flight length components (cm) |
| `Tau_flightLengthSig` | Flight length significance |
| `Tau_dzErr` | dz error from leading charged hadron track |
| `Tau_leadTkNormChi2` | Normalized chi2 of leading track |
| `Tau_leadChCandEtaAtEcalEntrance` | Leading charged candidate eta at ECAL entrance |

These branches are present only in standard NanoAOD configurations (non-scouting)
where full offline tau reconstruction is available. In scouting NanoAOD, tau
discrimination is handled entirely through UParT jet-level scores.

### Lepton IP Covariance

The `addIPCovToLeptons()` function adds IP covariance matrix elements for
electrons, muons, and taus. These 6 elements (cov_xx, cov_xy, cov_xz,
cov_yy, cov_yz, cov_zz) are stored as `IP_covJI` branches in the
corresponding `*TimeLifeInfoTable` extension tables.

---

## 8. Collections Absent in Data/Scouting-Only Mode

When processing real collision data (no `--mc` flag), the following
collections are entirely absent from the output:

- `GenPart` -- no generator particles
- `GenJet` / `GenJetAK8` -- no generator jets
- `GenVtx` -- no generator vertex
- `Pileup` -- no true pileup information
- `genWeight` -- no generator weight (event weight = 1)
- `LHEWeight` / `LHEScaleWeight` / `LHEPdfWeight` -- no LHE weights
- `LHEPart` -- no LHE particles
- All `*_genJetIdx` branches in jet MC extension tables
- All `*_hadronFlavour` and `*_partonFlavour` branches

The MC-specific tasks (`scoutingNanoTaskMC`, `scoutingPFJetRecluster2MCTask`,
etc.) are not scheduled when processing data, so these branches do not appear
in the output file at all.

---

## 9. Generator-Level Summary for HH->bbtautau Signal

For the primary signal sample (`GluGluHHto2B2Tau`), the GenPart collection
contains 2 Higgs bosons (pdgId 25), 2 b quarks (pdgId +/-5) from H->bb,
2 tau leptons (pdgId +/-15) from H->tautau, and their full decay chains.
The `genJetIdx` matching in `ScoutingPFJetRecluster2` enables efficiency
and fake rate measurements for the UParT tagger.
