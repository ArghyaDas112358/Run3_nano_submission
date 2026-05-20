# Jet Branches: AK4 and AK8 Reclustered Jets with Tagger Scores

This document details all jet-related branches in the scouting NanoAOD output,
covering three jet collections and their associated ML tagger scores.

---

## 1. ScoutingPFJetRecluster2 (Reclustered AK4 Jets)

**Source:** `patScoutingPFJetRecluster`
**Algorithm:** Anti-kT R=0.4, reclustered from translated scouting PF candidates
**Clustering pT threshold:** 20 GeV
**JEC payload:** AK4PFHLT (L1FastJet, L2Relative, L3Absolute, L2L3Residual)

### 1.1 Kinematic Variables

These come from `P4Vars` (standard CMS 4-momentum variables):

| Branch | Type | Description |
|--------|------|-------------|
| `ScoutingPFJetRecluster2_pt` | float | Transverse momentum (GeV), JEC-corrected |
| `ScoutingPFJetRecluster2_eta` | float | Pseudorapidity |
| `ScoutingPFJetRecluster2_phi` | float | Azimuthal angle |
| `ScoutingPFJetRecluster2_mass` | float | Invariant mass (GeV), JEC-corrected |

### 1.2 Jet Composition and Structure

Defined in `common_cff.py` as `PFJetVariables`:

| Branch | Type | Description |
|--------|------|-------------|
| `ScoutingPFJetRecluster2_area` | float | Jet catchment area (for JECs) |
| `ScoutingPFJetRecluster2_chHEF` | float | Charged hadron energy fraction |
| `ScoutingPFJetRecluster2_neHEF` | float | Neutral hadron energy fraction |
| `ScoutingPFJetRecluster2_chEmEF` | float | Charged electromagnetic energy fraction |
| `ScoutingPFJetRecluster2_neEmEF` | float | Neutral electromagnetic energy fraction |
| `ScoutingPFJetRecluster2_hfHEF` | float | HF hadronic energy fraction |
| `ScoutingPFJetRecluster2_hfEmEF` | float | HF electromagnetic energy fraction |
| `ScoutingPFJetRecluster2_muEF` | float | Muon energy fraction |
| `ScoutingPFJetRecluster2_chHadMultiplicity` | int16 | Number of charged hadrons |
| `ScoutingPFJetRecluster2_neHadMultiplicity` | int | Number of neutral hadrons |
| `ScoutingPFJetRecluster2_hfHadMultiplicity` | int | Number of HF hadrons |
| `ScoutingPFJetRecluster2_hfEMMultiplicity` | int | Number of HF EM particles |
| `ScoutingPFJetRecluster2_muMultiplicity` | int | Number of muons |
| `ScoutingPFJetRecluster2_elMultiplicity` | int | Number of electrons |
| `ScoutingPFJetRecluster2_phMultiplicity` | int | Number of photons |
| `ScoutingPFJetRecluster2_nConstituents` | int | Total number of PF constituents |

### 1.3 JEC and Charge

| Branch | Type | Description |
|--------|------|-------------|
| `ScoutingPFJetRecluster2_rawFactor` | float | `1 - jecFactor('Uncorrected')`: multiply corrected pT by (1 - rawFactor) to get raw pT |
| `ScoutingPFJetRecluster2_charge` | float | Jet charge from `jetCharge()` |

### 1.4 UParT AK4 Tagger Scores (Custom HH->bbtautau Model)

**Model:** `RecoBTag/Combined/data/UParTAK4/Scouting_HHbbtautau/V00/modelfile/model.onnx`
**Selection:** Applied only when pT >= 15 GeV AND |eta| <= 2.5; set to -1 otherwise
**Prefix:** `scoutUParT_`

| Branch | Type | Description |
|--------|------|-------------|
| `ScoutingPFJetRecluster2_scoutUParT_probb` | float | b quark probability |
| `ScoutingPFJetRecluster2_scoutUParT_probbb` | float | bb (double-b) probability |
| `ScoutingPFJetRecluster2_scoutUParT_problepb` | float | Leptonic b (b->lepton) probability |
| `ScoutingPFJetRecluster2_scoutUParT_probc` | float | c quark probability |
| `ScoutingPFJetRecluster2_scoutUParT_probuds` | float | Light quark (u/d/s) probability |
| `ScoutingPFJetRecluster2_scoutUParT_probg` | float | Gluon probability |
| `ScoutingPFJetRecluster2_scoutUParT_probtaum` | float | Tau minus probability |
| `ScoutingPFJetRecluster2_scoutUParT_probtaup` | float | Tau plus probability |

The 8 output scores are the key discriminants for HH->bbtautau analysis.
Values of -1 indicate the jet is outside the tagger acceptance. Valid scores
range from 0.0 to 1.0. The sum of all 8 probabilities equals approximately 1.0
for jets within acceptance.

### 1.5 HLT ParticleNet AK4 Scores

**Model:** `RecoBTag/Combined/data/HLT/ParticleNetAK4/V01/particle-net.onnx`
**Selection:** Applied only when pT >= 5 GeV AND |eta| <= 2.6; set to -1 otherwise
**Prefix:** `hltPNet_`

| Branch | Type | Description |
|--------|------|-------------|
| `ScoutingPFJetRecluster2_hltPNet_probtauhp` | float | Tau high-purity score |
| `ScoutingPFJetRecluster2_hltPNet_probtauhm` | float | Tau high-multiplicity score |
| `ScoutingPFJetRecluster2_hltPNet_probb` | float | b quark score |
| `ScoutingPFJetRecluster2_hltPNet_probc` | float | c quark score |
| `ScoutingPFJetRecluster2_hltPNet_probuds` | float | Light quark (u/d/s) score |
| `ScoutingPFJetRecluster2_hltPNet_probg` | float | Gluon score |

The HLT ParticleNet provides 6 outputs. Its pT threshold (5 GeV) is lower
than UParT (15 GeV), and its eta range (2.6) is slightly wider than UParT (2.5).

### 1.6 MC-Only Branches (Extension Table)

Present only in NANOAODSIM (MC). Cloned from `jetMCTable`:

| Branch | Type | Description |
|--------|------|-------------|
| `ScoutingPFJetRecluster2_genJetIdx` | int16 | Index into `GenJet` collection (-1 if unmatched, requires genJet pT > 10 GeV) |
| `ScoutingPFJetRecluster2_hadronFlavour` | int | Hadron-based jet flavor (5=b, 4=c, 0=light) |
| `ScoutingPFJetRecluster2_partonFlavour` | int | Parton-based jet flavor |

---

## 2. ScoutingFatPFJetRecluster2 (Reclustered AK8 Fat Jets)

**Source:** `patScoutingFatPFJetRecluster`
**Algorithm:** Anti-kT R=0.8, reclustered from translated scouting PF candidates
**Clustering pT threshold:** 170 GeV
**JEC payload:** AK8PFHLT

### 2.1 Kinematic Variables

Same `P4Vars` as AK4 jets:

| Branch | Type | Description |
|--------|------|-------------|
| `ScoutingFatPFJetRecluster2_pt` | float | Transverse momentum (GeV), JEC-corrected |
| `ScoutingFatPFJetRecluster2_eta` | float | Pseudorapidity |
| `ScoutingFatPFJetRecluster2_phi` | float | Azimuthal angle |
| `ScoutingFatPFJetRecluster2_mass` | float | Invariant mass (GeV), JEC-corrected |

### 2.2 Jet Composition and Structure

Same `PFJetVariables` set as AK4. All branches listed in Section 1.2 are
present with the `ScoutingFatPFJetRecluster2_` prefix.

### 2.3 JEC and Charge

| Branch | Type | Description |
|--------|------|-------------|
| `ScoutingFatPFJetRecluster2_rawFactor` | float | JEC raw factor |
| `ScoutingFatPFJetRecluster2_charge` | float | Jet charge |

### 2.4 HLT ParticleNet AK8 Scores

**Model:** HLT ParticleNet AK8 (from CMSSW `RecoBTag/Combined/data/`)
**Selection:** Applied only when pT >= 200 GeV AND |eta| <= 2.5; set to -1 otherwise
**Prefix:** `hltPNetAK8_`

| Branch | Type | Description |
|--------|------|-------------|
| `ScoutingFatPFJetRecluster2_hltPNetAK8_probHtt` | float | H->tau_h tau_h score |
| `ScoutingFatPFJetRecluster2_hltPNetAK8_probHtm` | float | H->tau_h mu score |
| `ScoutingFatPFJetRecluster2_hltPNetAK8_probHte` | float | H->tau_h e score |
| `ScoutingFatPFJetRecluster2_hltPNetAK8_probHbb` | float | H->bb score |
| `ScoutingFatPFJetRecluster2_hltPNetAK8_probHcc` | float | H->cc score |
| `ScoutingFatPFJetRecluster2_hltPNetAK8_probHqq` | float | H->qq score |
| `ScoutingFatPFJetRecluster2_hltPNetAK8_probHgg` | float | H->gg score |
| `ScoutingFatPFJetRecluster2_hltPNetAK8_probQCD2hf` | float | QCD 2 heavy flavors score |
| `ScoutingFatPFJetRecluster2_hltPNetAK8_probQCD1hf` | float | QCD 1 heavy flavor score |
| `ScoutingFatPFJetRecluster2_hltPNetAK8_probQCD0hf` | float | QCD 0 heavy flavors score |

The AK8 tagger provides Higgs decay hypothesis scores (Hbb, Hcc, Hqq, Hgg,
and three Htau modes) plus QCD background scores binned by heavy-flavor content.

### 2.5 MC-Only Branches

Cloned from `fatJetMCTable`:

| Branch | Type | Description |
|--------|------|-------------|
| `ScoutingFatPFJetRecluster2_genJetAK8Idx` | int16 | Index into `GenJetAK8` collection |
| `ScoutingFatPFJetRecluster2_hadronFlavour` | int | Hadron-based flavor |
| `ScoutingFatPFJetRecluster2_partonFlavour` | int | Parton-based flavor |

---

## 3. ScoutingPFJet2 (Direct Scouting Jets)

**Source:** `patScoutingPFJet`
**Description:** AK4 jets directly converted from HLT scouting packed jets
(no reclustering). JEC applied with AK4PFHLT payload.

### 3.1 Branches

Same `PFJetVariables` and `P4Vars` as reclustered jets:

| Branch | Type | Description |
|--------|------|-------------|
| `ScoutingPFJet2_pt` | float | pT (JEC-corrected) |
| `ScoutingPFJet2_eta` | float | Pseudorapidity |
| `ScoutingPFJet2_phi` | float | Azimuthal angle |
| `ScoutingPFJet2_mass` | float | Mass (JEC-corrected) |
| `ScoutingPFJet2_area` | float | Jet area |
| `ScoutingPFJet2_rawFactor` | float | JEC raw factor |
| (+ all `PFJetVariables`) | | Energy fractions, multiplicities |

No tagger scores are attached to this collection. MC extension provides
`genJetIdx` only.

---

## 4. Tagger Selection Logic

All tagger scores use a conditional expression in the NanoAOD table definition.
Jets outside the acceptance window receive a sentinel value of -1:

```python
# UParT example:
scoutUParT_probb = Var(
    "?(pt>=15)&&(abs(eta)<=2.5)"
    "?bDiscriminator('scoutingPFJetRecluster...AK4Tags:probb')"
    ":-1",
    float, precision=10
)
```

When analyzing, filter jets with score > 0 (or >= 0) to select only jets where
the tagger was actually evaluated.

---

## 5. Summary of Tagger Coverage

| Tagger | Collection | pT Cut | |eta| Cut | N Outputs | Key Outputs |
|--------|-----------|--------|----------|-----------|-------------|
| UParT AK4 (HHbbtautau) | ScoutingPFJetRecluster2 | >= 15 GeV | <= 2.5 | 8 | probb, probbb, probtaum, probtaup |
| HLT PNet AK4 | ScoutingPFJetRecluster2 | >= 5 GeV | <= 2.6 | 6 | probb, probc, probtauhp, probtauhm |
| HLT PNet AK8 | ScoutingFatPFJetRecluster2 | >= 200 GeV | <= 2.5 | 10 | probHbb, probHtt, probQCD* |
