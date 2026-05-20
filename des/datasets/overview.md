# Dataset Catalog Summary and Statistics

This document provides an overview of all datasets managed by the
HH->bbtautau Run3_nano_submission repository, including total counts,
organizational structure, naming conventions, and management tools.

## Total Dataset Counts

| Category | Count | JSON Files |
|---|---|---|
| MC 2024 samples | ~139 | `MC_2024.json` |
| MC 2023 samples | varies | `MC_2023.json`, `MC_2023BPix.json` |
| MC 2022 samples | varies | `MC_2022.json`, `MC_2022EE.json` |
| Data 2024 entries | 180+ | `DATA_2024.json` |
| Data 2023 entries | varies | `DATA_2023.json`, `DATA_2023BPix.json` |
| Data 2022 entries | varies | `DATA_2022.json`, `DATA_2022EE.json` |
| Scouting data entries | 15 | `Scouting_DATA.json` |

## JSON File Inventory

The `datasets/` directory contains 11 JSON files:

### MC Dataset Files
| File | Year | Campaign Tag |
|---|---|---|
| `MC_2022.json` | 2022 (pre-EE) | `Run3Summer22MiniAODv4` |
| `MC_2022EE.json` | 2022 (post-EE) | `Run3Summer22EEMiniAODv4` |
| `MC_2023.json` | 2023 (pre-BPix) | `Run3Summer23MiniAODv4` |
| `MC_2023BPix.json` | 2023 (post-BPix) | `Run3Summer23BPixMiniAODv4` |
| `MC_2024.json` | 2024 | `RunIII2024Summer24MiniAODv6` |

### Data Dataset Files
| File | Year | Reconstruction Tags |
|---|---|---|
| `DATA_2022.json` | 2022 | `22Sep2023` |
| `DATA_2022EE.json` | 2022EE | `22Sep2023` |
| `DATA_2023.json` | 2023 | `22Sep2023` variants |
| `DATA_2023BPix.json` | 2023BPix | `22Sep2023` variants |
| `DATA_2024.json` | 2024 | `2024CDEReprocessing`, `PromptReco` |

### Scouting Dataset File
| File | Years | Format |
|---|---|---|
| `Scouting_DATA.json` | 2022, 2023, 2024 | `ScoutNano` NANOAOD |

## Organization by Physics Process

MC datasets are grouped into top-level keys in the JSON files. For 2024, these
categories are:

| JSON Key | Physics Process | Approx. Samples |
|---|---|---|
| `HH4b` | HH -> 4b (ggF + VBF) | 20 |
| `HHbbtt` | HH -> bbtautau (ggF) | 14 |
| `HHbbtt_old` | HH -> bbtautau (single sample) | 1 |
| `QCD-4Jets_HT` | QCD multijet (HT-binned) | 11 |
| `QCD_PT` | QCD (pT-binned) | 16 |
| `TT` | Top pair production | 3 |
| `SingleTop` | Single top (t/tW channels) | 6 |
| `Hbb` | H -> bb (all production modes) | ~10 |
| `Hcc` | H -> cc (all production modes) | ~10 |
| `Htautau` | H -> tautau | ~4 |
| `DYJetsLO` | Drell-Yan (leading order) | ~5 |
| `DYJetsNLO` | Drell-Yan (NLO) | ~7 |
| `VJetsLO` | V+jets (leading order) | ~7 |
| `VJetsNLO` | V+jets (NLO) | ~12 |
| `Diboson` | WW, WZ, ZZ | ~8 |
| `EWK` | EW vector boson (VBF) | ~5 |
| `VGamma` | V+gamma | ~12 |

Data datasets are grouped by physics stream (JetMET, Muon, EGamma, Tau, BTagMu,
MuonEG, ParkingVBF, ParkingSingleMuon).

## Dataset Naming Conventions

### DAS Path Format

All datasets follow the standard CMS DAS (Data Aggregation System) path format:

```
/<PrimaryDataset>/<Campaign>-<ProcessingTag>/<DataTier>
```

### MC Example

```
/GluGluHHto2B2Tau_Par-c2-0p00-kl-1p00-kt-1p00_TuneCP5_13p6TeV_powheg-pythia8/
RunIII2024Summer24MiniAODv6-PowhegBugFix_150X_mcRun3_2024_realistic_v2-v2/
MINIAODSIM
```

Breakdown:
- **Primary dataset**: Physics process, coupling parameters, tune, energy,
  generator chain.
- **Campaign**: Production campaign (`RunIII2024Summer24MiniAODv6`).
- **Processing tag**: Conditions tag + version (`PowhegBugFix_150X_...-v2`).
- **Data tier**: `MINIAODSIM` (MC simulation MiniAOD).

### Data Example

```
/JetMET0/Run2024C-2024CDEReprocessing-v1/NANOAOD
```

### Scouting Example

```
/ScoutingPFRun3/Run2024C-ScoutNano-v1/NANOAOD
```

### Coupling Parameter Encoding

HH signal samples encode BSM coupling parameters in their names:
- `Par-c2-0p00-kl-1p00-kt-1p00` means c2=0.00, kl=1.00, kt=1.00
- `Par-CV-1p74-C2V-1p37-C3-14p4` means CV=1.74, C2V=1.37, C3=14.4
- Negative values: `m` prefix, e.g., `kl-m20p00` means kl=-20.00

## How Datasets Are Managed

### Discovery: get_mc.py and get_datasets.py

MC datasets are discovered using the DAS API via `get_mc.py`, which queries
patterns like `/GluGlu*HHto4B*/RunIII2024Summer24MiniAODv6*/MINIAODSIM` and
validates the result count against expectations.

Data datasets are discovered via `get_datasets.py`, which queries run-specific
patterns and handles multi-stream datasets (e.g., JetMET0, JetMET1).

### Storage: JSON Files

Results are stored as nested JSON dictionaries:
```json
{
    "CategoryKey": {
        "ShortName": "/full/DAS/path"
    }
}
```

### Consumption: crabby.py

The CRAB submission script reads JSON files based on the `--year` and
`--dataset` arguments:
```python
jsonFile = f"datasets/MC_{args.year}.json"  # or DATA_
datasets = json.load(f)[args.dataset]
```

It iterates over all DAS paths in the selected category, generating one CRAB
submission config per dataset.

### Filtering

The `crabby.py` script filters out commented entries and short strings:
```python
datasets = [value for key, value in card["datasets"].items()
            if len(value) > 10 and not value.startswith("#")]
```

This allows temporarily disabling datasets by commenting them out in the JSON.

## Related Files

- `/home/das214/HHtobbtautau/Run3_nano_submission/datasets/` -- All JSON files.
- `/home/das214/HHtobbtautau/Run3_nano_submission/crabby.py` -- CRAB submission
  logic that reads dataset JSONs.
- `/home/das214/HHtobbtautau/Run3_nano_submission/datasets/get_mc.py` -- MC
  dataset discovery tool (DAS queries).
- `/home/das214/HHtobbtautau/Run3_nano_submission/datasets/get_datasets.py` --
  Data dataset discovery tool.
