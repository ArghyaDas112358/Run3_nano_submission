# MC Samples: HH Signals and Backgrounds

This document catalogs all Monte Carlo simulation samples used in the
HH->bbtautau analysis, organized by physics process category.

## HH Signal Samples

### HH -> bbtautau (Target Channel)

The primary signal for this analysis. Samples are produced with varying BSM
coupling parameters to enable EFT (Effective Field Theory) interpretations.

#### Gluon-Gluon Fusion (ggF)

Generator: Powheg + Pythia8 (NLO QCD, TuneCP5, 13.6 TeV)

| Sample | c2 | kl | kt | ext1 Available |
|---|---|---|---|---|
| `GluGluHHto2B2Tau_Par-c2-0p00-kl-0p00-kt-1p00` | 0.00 | 0.00 | 1.00 | Yes |
| `GluGluHHto2B2Tau_Par-c2-0p00-kl-1p00-kt-1p00` | 0.00 | 1.00 | 1.00 | Yes |
| `GluGluHHto2B2Tau_Par-c2-0p00-kl-2p45-kt-1p00` | 0.00 | 2.45 | 1.00 | Yes |
| `GluGluHHto2B2Tau_Par-c2-0p00-kl-5p00-kt-1p00` | 0.00 | 5.00 | 1.00 | Yes |
| `GluGluHHto2B2Tau_Par-c2-0p10-kl-1p00-kt-1p00` | 0.10 | 1.00 | 1.00 | No |
| `GluGluHHto2B2Tau_Par-c2-0p35-kl-1p00-kt-1p00` | 0.35 | 1.00 | 1.00 | No |
| `GluGluHHto2B2Tau_Par-c2-1p00-kl-0p00-kt-1p00` | 1.00 | 0.00 | 1.00 | No |
| `GluGluHHto2B2Tau_Par-c2-2p24-kl-m20p00-kt-1p00` | 2.24 | -20.00 | 1.00 | No |
| `GluGluHHto2B2Tau_Par-c2-3p00-kl-1p00-kt-1p00` | 3.00 | 1.00 | 1.00 | No |
| `GluGluHHto2B2Tau_Par-c2-m2p00-kl-1p00-kt-1p00` | -2.00 | 1.00 | 1.00 | No |

The `_ext1` suffix denotes extended statistics samples with the same physics
but additional generated events, produced with a different random seed.

The 2024 campaign tag is `RunIII2024Summer24MiniAODv6-PowhegBugFix_150X_mcRun3_2024_realistic_v2`.
All ggF samples include the PowhegBugFix tag.

### HH -> 4b (Cross-Check Channel)

Generator: Powheg + Pythia8 (ggF), MadGraph + Pythia8 (VBF)

#### ggF HH -> 4b (10 samples)

Same coupling parameter grid as bbtautau, but with 4 b-quark final state.
Used for cross-checks and combined HH searches.

#### VBF HH -> 4b (10 samples)

| Sample | CV | C2V | C3 |
|---|---|---|---|
| `VBFHHto4B_Par-CV-1-C2V-0-C3-1` | 1.00 | 0.00 | 1.00 |
| `VBFHHto4B_Par-CV-1-C2V-1-C3-1` | 1.00 | 1.00 | 1.00 |
| `VBFHHto4B_Par-CV-1p74-C2V-1p37-C3-14p4` | 1.74 | 1.37 | 14.40 |
| `VBFHHto4B_Par-CV-2p12-C2V-3p87-C3-m5p96` | 2.12 | 3.87 | -5.96 |
| ... and 6 more VBF benchmark points | | | |

VBF samples use MadGraph (LO) with CV, C2V, C3 coupling variations.

## Background Samples

### QCD Multijet

The dominant instrumental background, produced in two complementary binning
schemes.

#### QCD-4Jets (HT-binned, 11 samples)

Generator: MadGraph MLM + Pythia8

| HT Bin (GeV) | Sample Name |
|---|---|
| 40-70 | `QCD-4Jets_Bin-HT-40to70` |
| 70-100 | `QCD-4Jets_Bin-HT-70to100` |
| 100-200 | `QCD-4Jets_Bin-HT-100to200` |
| 200-400 | `QCD-4Jets_Bin-HT-200to400` |
| 400-600 | `QCD-4Jets_Bin-HT-400to600` |
| 600-800 | `QCD-4Jets_Bin-HT-600to800` |
| 800-1000 | `QCD-4Jets_Bin-HT-800to1000` |
| 1000-1200 | `QCD-4Jets_Bin-HT-1000to1200` |
| 1200-1500 | `QCD-4Jets_Bin-HT-1200to1500` |
| 1500-2000 | `QCD-4Jets_Bin-HT-1500to2000` |
| > 2000 | `QCD-4Jets_Bin-HT-2000` |

Note: 2024 naming uses `Bin-HT-` prefix (vs `HT-` in 2022-2023).

#### QCD (pT-binned, 16 samples)

Generator: Pythia8 (parton shower only)

pT bins from 15 GeV to > 3000 GeV, plus a flat pT spectrum sample
(`QCD_Bin-PT-15to7000_Par-PT-flat2022`).

### Top Quark Production

#### Top Pair (TTbar, 3 samples)

Generator: Powheg + Pythia8

| Decay Mode | Sample |
|---|---|
| Dileptonic | `TTto2L2Nu` |
| All-hadronic | `TTto4Q` |
| Semi-leptonic | `TTtoLNu2Q` |

TTbar is the single largest physics background in the bbtautau final state.

#### Single Top (6 samples)

Includes t-channel and tW-channel production:
- `TbarWplus_4Q`, `TbarWplus_LNu`
- `TWminus_4Q`, `TWminus_LNu`
- `TbarBQ_4FS` (t-channel, 4-flavor scheme)
- `TBbarQ_4FS`

### Higgs Single Production

#### H -> bb (Hbb, ~10 samples)

Production modes: ggH, VBF, TTH, WH, ZH, with pT-binned variants for
high-pT (> 200 GeV) studies.

#### H -> cc (Hcc, ~10 samples)

Same production modes as Hbb. Used for charm background studies.

#### H -> tautau (Htautau, ~4 samples)

A mixture of uncorrelated decay samples and filtered variants. Naming
conventions vary (`Hto2Tau` vs `HTo2Tau`).

### Drell-Yan (DY) Lepton Production

#### DYJetsLO (Leading Order, ~5 samples for 2024)

Generator: MadGraph MLM. In 2024, binned by jet multiplicity (1J-4J plus
inclusive). In 2022-2023, additionally binned in HT.

#### DYJetsNLO (NLO, ~7 samples for 2024)

Generator: MC@NLO FXFx. Binned by jet multiplicity with pT(ll) sub-bins
in earlier years.

### Vector Boson + Jets (V+jets)

#### VJetsLO (Leading Order, ~7 samples)

W->2Q (hadronic), W->LNu (leptonic), Z->2Q, binned in HT or jet multiplicity.

#### VJetsNLO (NLO, ~12 samples)

W and Z with jet multiplicity and pT binning using MC@NLO FXFx matching.

### Diboson (8 samples)

Inclusive WW, WZ, ZZ (Pythia8) plus exclusive channels (WZ->3LNu, ZZ->4L, etc.)
using MC@NLO FXFx.

### Electroweak VBF Production (5 samples)

VBFZto2Q, VBFWto2Q, VBFto2L, VBFto2Nu, VBFtoLNu. Generator: MadGraph.

### V+gamma (12 samples)

WG and ZG with photon pT binning (10-100, 100-200, 200-400, 400-600, 600+ GeV).
Generator: MC@NLO FXFx.

## Year-to-Year Differences

| Aspect | 2022 | 2023 | 2024 |
|---|---|---|---|
| CMSSW gen version | 130X | 130X | 150X |
| MiniAOD version | v4 | v4 | v6 |
| Process naming | `GluGlutoHHto` | `GluGlutoHHto` | `GluGluHHto_Par-` |
| Extended samples | Many `_ext1`, `_ext2` | Moderate | Select `_ext1` |
| DY binning | HT + jet multiplicity | HT + jet multiplicity | Jet multiplicity only |

## Physics Summary

| Category | Role in Analysis | Dominant Generator | Key Feature |
|---|---|---|---|
| HH -> bbtautau | Primary signal | Powheg | Coupling morphing |
| HH -> 4b | Cross-check signal | Powheg / MadGraph | Same couplings |
| TTbar | Main background | Powheg | b-jets + leptons |
| QCD | Instrumental background | MadGraph / Pythia8 | High statistics needed |
| Single H | Peaking background | Various | Same final state objects |
| DY / V+jets | Minor background | MadGraph / MC@NLO | Leptonic decays |
| Diboson / VBF-EWK | Rare backgrounds | Pythia8 / MC@NLO | Small contributions |

## Related Files

- `/home/das214/HHtobbtautau/Run3_nano_submission/datasets/MC_2024.json`
- `/home/das214/HHtobbtautau/Run3_nano_submission/datasets/MC_2023.json`
- `/home/das214/HHtobbtautau/Run3_nano_submission/datasets/MC_2022.json`
- `/home/das214/HHtobbtautau/Run3_nano_submission/datasets/MC_2022EE.json`
- `/home/das214/HHtobbtautau/Run3_nano_submission/datasets/MC_2023BPix.json`
