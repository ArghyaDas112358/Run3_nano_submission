# Trigger Result Branches

This document describes how trigger information is stored in the scouting
NanoAOD output, the differences between scouting and standard trigger
configurations, and how to access trigger decisions in analysis.

---

## 1. How Trigger Results Are Stored in NanoAOD

CMS NanoAOD stores HLT trigger decisions as individual boolean branches in the
`Events` tree. Each branch name follows the convention `HLT_<path name>`, where
the value is `true` if the trigger path fired and `false` otherwise.

In the scouting configuration, trigger results are explicitly preserved via:

```python
process.NANOAODSIMoutput.outputCommands.append("keep edmTriggerResults_*_*_*")
```

This retains the full `edmTriggerResults` product, which the NanoAOD framework
unpacks into individual `HLT_*` branches. Without this line, scouting trigger
results would be dropped from the output because scouting uses a non-standard
HLT menu.

---

## 2. Scouting Trigger Paths

Scouting data is collected at the full L1 trigger rate (approximately 100 kHz)
using reduced-content HLT paths. The scouting trigger paths do not perform
full offline-quality reconstruction but instead save compact HLT-level objects.

### Scouting HLT Paths

The scouting HLT menu includes paths in the `DST_*` and `HLT_*Scouting*`
families. Typical scouting paths relevant for HH->bbtautau include:

**Jet triggers:**

| Path Pattern | Description |
|-------------|-------------|
| `DST_PFScouting_JetHT_v*` | Scouting jet+HT trigger |
| `DST_PFScouting_AXOLoose_v*` | Anomaly detection (AXO) loose |
| `DST_PFScouting_AXONominal_v*` | Anomaly detection nominal |
| `DST_PFScouting_AXOTight_v*` | Anomaly detection tight |
| `DST_PFScouting_AXOVTight_v*` | Anomaly detection very tight |
| `DST_PFScouting_SingleMuon_v*` | Single muon scouting |
| `DST_PFScouting_DoubleMuon_v*` | Double muon scouting |
| `DST_PFScouting_SingleElectron_v*` | Single electron scouting |
| `DST_PFScouting_DoubleEG_v*` | Double electron/photon scouting |
| `DST_PFScouting_ZeroBias_v*` | Zero bias scouting (unbiased) |

**Muon triggers:**

| Path Pattern | Description |
|-------------|-------------|
| `DST_PFScouting_SingleMuon_v*` | Single muon with scouting PF |
| `DST_PFScouting_DoubleMuon_v*` | Dimuon with scouting PF |

**Electron/photon triggers:**

| Path Pattern | Description |
|-------------|-------------|
| `DST_PFScouting_SingleElectron_v*` | Single electron scouting |
| `DST_PFScouting_DoubleEG_v*` | Double EG scouting |

The exact paths available depend on the HLT menu version and data-taking era.
Scouting trigger paths are versioned (e.g., `_v7`, `_v8`) and the version
number increments with menu updates during a run period.

---

## 3. Standard Trigger Paths (Non-Scouting Configs)

For comparison, the standard NanoAOD configurations (`MC_2024_NANO.py`,
`DATA_2024_NANO.py`) use the `NANO:@BTV` step which processes events that
passed the standard CMS HLT menu. These include:

**Jet triggers (standard):**

| Path Pattern | Description |
|-------------|-------------|
| `HLT_PFJet*` | Single PF jet (various pT thresholds) |
| `HLT_PFHT*` | PF HT triggers |
| `HLT_AK8PFJet*` | AK8 fat jet triggers |
| `HLT_DiPFJetAve*` | Dijet average pT triggers |

**Lepton triggers (standard):**

| Path Pattern | Description |
|-------------|-------------|
| `HLT_Mu*` | Single/double muon triggers |
| `HLT_Ele*` | Single/double electron triggers |
| `HLT_IsoMu*` | Isolated muon triggers |

**B-tag triggers (standard BTV):**

| Path Pattern | Description |
|-------------|-------------|
| `HLT_BTagMu_*` | B-tag with muon triggers |
| `HLT_Mu*_PFJet*_DeepCSV*` | Muon + jet with b-tag |

**MET triggers (standard):**

| Path Pattern | Description |
|-------------|-------------|
| `HLT_PFMET*` | PF MET triggers |
| `HLT_PFMETNoMu*` | MET without muon contribution |

---

## 4. Differences Between Scouting and Standard Trigger Branches

| Aspect | Scouting Config | Standard Config |
|--------|----------------|-----------------|
| Trigger menu | Scouting-specific (`DST_PFScouting_*`) | Full CMS HLT menu |
| Rate | ~100 kHz (L1 rate) | ~2 kHz (HLT rate) |
| Event content | Reduced (HLT-level objects) | Full (offline-quality reconstruction) |
| Branch prefix | `HLT_` (same convention) | `HLT_` (same convention) |
| Available paths | Scouting + some standard | All standard HLT paths |
| Prescales | Not stored in NanoAOD flat branches | Not stored in NanoAOD flat branches |
| Output command | Explicit `keep edmTriggerResults_*_*_*` required | Automatic via nano_cff |

In the scouting configuration, the `edmTriggerResults` product is kept
explicitly because the standard NanoAOD trigger table producer may not
recognize scouting-specific trigger paths by default.

---

## 5. TrigObj Collection

The `TrigObj` collection stores HLT trigger objects -- the physics objects
(jets, leptons, photons, MET) that were reconstructed at HLT level and caused
specific trigger paths to fire.

### Standard NanoAOD TrigObj Branches

| Branch | Type | Description |
|--------|------|-------------|
| `TrigObj_pt` | float | Trigger object pT (GeV) |
| `TrigObj_eta` | float | Pseudorapidity |
| `TrigObj_phi` | float | Azimuthal angle |
| `TrigObj_l1pt` | float | Associated L1 object pT |
| `TrigObj_l1iso` | int | L1 isolation flag |
| `TrigObj_l1charge` | int | L1 charge |
| `TrigObj_id` | int | Trigger object type (11=e, 13=mu, 15=tau, 22=photon, etc.) |
| `TrigObj_filterBits` | int | Bitmask of passed trigger filters |

In scouting NanoAOD, the `TrigObj` collection may be limited or absent,
depending on whether the standard NanoAOD trigger object producer is included
in the scouting sequence. The scouting-specific trigger objects are already
captured in the scouting object collections themselves (ScoutingMuon,
ScoutingElectron, etc.).

---

## 6. L1 Trigger Information

### L1 Trigger Bits

L1 trigger decisions are stored as boolean branches with the prefix `L1_`:

| Branch Pattern | Description |
|---------------|-------------|
| `L1_SingleMu*` | Single muon L1 seeds |
| `L1_DoubleMu*` | Double muon L1 seeds |
| `L1_SingleEG*` | Single electron/photon L1 seeds |
| `L1_DoubleEG*` | Double electron/photon L1 seeds |
| `L1_SingleJet*` | Single jet L1 seeds |
| `L1_HTT*` | HT L1 seeds |
| `L1_ETM*` | MET L1 seeds |

### L1 Trigger Objects

When the `add_l1t_objects()` customization from `addVars.py` is applied
(standard non-scouting configs), dedicated L1 trigger object tables are added:

| Collection | pT Cut | Description |
|-----------|--------|-------------|
| `L1EG` | >= 10 GeV | L1 electron/photon objects |
| `L1Tau` | >= 20 GeV | L1 tau objects |
| `L1Jet` | >= 20 GeV | L1 jet objects |
| `L1Mu` | >= 0 GeV | L1 muon objects |
| `L1EtSum` | Types 1,2,3,8,21 | L1 energy sums (MET, HT, etc.) |

Each L1 object table contains kinematic variables (pt, eta, phi) and quality
flags.

In scouting NanoAOD, L1 trigger objects may not be separately stored since
scouting operates at L1 rate and the L1 decisions are implicitly encoded in
the scouting trigger path decisions.

---

## 7. Accessing Trigger Information in Analysis

### Reading Trigger Decisions

In ROOT/Python analysis code:

```python
# Check if scouting jet trigger fired
events = uproot.open("file.root")["Events"]
jet_trigger = events["HLT_DST_PFScouting_JetHT_v7"].array()

# Select events passing at least one scouting trigger
mask = jet_trigger | events["HLT_DST_PFScouting_AXONominal_v5"].array()
```

### Trigger Version Handling

Trigger path versions change across run periods. In analysis, use version-
agnostic matching:

```python
# Find all scouting jet triggers regardless of version
import re
trigger_branches = [b for b in tree.keys() if re.match(r"HLT_DST_PFScouting_JetHT_v\d+", b)]
```

### Trigger Efficiency Studies

Since scouting data is collected at L1 rate with no HLT-level pT or topology
cuts on the saved objects (only the scouting path must fire), trigger
efficiencies for scouting paths are typically high. The limiting factor is
the L1 seed threshold, not the HLT reconstruction.

For standard trigger comparisons, the scouting NanoAOD can be cross-checked
against standard trigger-based NanoAOD using overlapping run/lumi/event numbers.

---

## 8. Scouting-Specific Trigger Considerations

### Event Selection Strategy

For HH->bbtautau analysis using scouting data, the recommended approach is:

1. Require at least one scouting trigger path to fire (e.g., `DST_PFScouting_JetHT`)
2. Apply offline-level cuts on scouting jet pT and tagger scores
3. No standard HLT trigger requirement (scouting bypasses normal HLT)

### Trigger Object Matching

In scouting NanoAOD, there is no need for explicit trigger-object matching
(as done in standard analyses with `TrigObj` delta-R matching) because the
scouting objects ARE the trigger-level objects. The entire event content is
at HLT precision.

### Prescale Information

Trigger prescale values are not directly stored in NanoAOD branches. For
scouting paths, prescales are typically 1 (unprescaled) since scouting
operates at L1 rate. Prescale information, if needed, must be obtained from
the CMS conditions database (brilcalc or OMS).
