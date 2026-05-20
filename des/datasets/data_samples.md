# Data Streams and Samples

This document describes the collision data streams used in the HH->bbtautau
analysis, covering standard physics streams and parking datasets across
Run 3 years.

## Data Stream Overview

CMS collision data is split into streams based on the HLT trigger paths that
fired for each event. The analysis uses multiple streams to cover different
final-state topologies.

### Primary Physics Streams

| Stream | Physics Content | Split Streams | Data Tier |
|---|---|---|---|
| JetMET | Jet and MET triggers | JetMET0, JetMET1 | NANOAOD |
| Muon | Single/double muon triggers | Muon0, Muon1 | MINIAOD |
| EGamma | Electron/photon triggers | EGamma0, EGamma1 | MINIAOD |
| Tau | Tau triggers | Tau (single) | MINIAOD |
| BTagMu | B-tagging with muon trigger | BTagMu (single) | MINIAOD |
| MuonEG | Muon+electron cross-triggers | MuonEG (single) | MINIAOD |

The JetMET stream is already available as centrally produced NANOAOD, while
other streams require MINIAOD -> NANOAOD conversion using the project configs.

### Parking Datasets

| Stream | Physics Content | Split Streams |
|---|---|---|
| ParkingVBF | VBF-topology triggers (parked) | ParkingVBF0 through ParkingVBF7 |
| ParkingSingleMuon | Low-pT single muon (parked) | ParkingSingleMuon0 through ParkingSingleMuon11 |

Parking datasets collect events that pass softer trigger thresholds and are
reconstructed later ("parked") during inter-fill periods. They provide access
to lower-pT phase space but require additional processing time.

## 2024 Data (Primary for Analysis)

### Run Periods and Reconstruction

| Runs | Reconstruction Tag | Notes |
|---|---|---|
| Run2024C, D, E | `2024CDEReprocessing-v1` | Reprocessed with improved calibrations |
| Run2024F, G, H | `PromptReco-v1` | Prompt reconstruction |
| Run2024I | `PromptReco-v1` and `PromptReco-v2` | Multiple versions for some streams |
| Run2024J | `PromptReco-v1` | Latest available run |

### JetMET (2024)

16 entries: 2 split streams (JetMET0, JetMET1) across 8 run periods (C-J).

Example DAS paths:
```
/JetMET0/Run2024C-2024CDEReprocessing-v1/NANOAOD
/JetMET1/Run2024F-PromptReco-v1/NANOAOD
```

JetMET is the only stream already in NANOAOD format. It is the primary stream
for jet-based analyses and contains events firing jet and MET triggers.

### Muon (2024)

16 entries with version splits for Run2024I:
```
/Muon0/Run2024C-2024CDEReprocessing-v1/MINIAOD
/Muon0/Run2024I-PromptReco-v1/MINIAOD
/Muon0/Run2024I-PromptReco-v2/MINIAOD
```

The v1/v2 split for Run2024I means both versions should be processed (they may
cover different luminosity sections or have different calibrations).

### EGamma (2024)

Same structure as Muon with 16 entries and Run2024I version splits.

### Tau (2024)

8 entries (single stream, no 0/1 split):
```
/Tau/Run2024C-2024CDEReprocessing-v1/MINIAOD
/Tau/Run2024I-PromptReco-v1/MINIAOD
/Tau/Run2024I-PromptReco-v2/MINIAOD
```

Critical for the tautau leg of the HH->bbtautau signal.

### BTagMu (2024)

8 entries (single stream):
```
/BTagMu/Run2024C-2024CDEReprocessing-v1/MINIAOD
/BTagMu/Run2024I-PromptReco-v1/MINIAOD
/BTagMu/Run2024I-PromptReco-v2/MINIAOD
```

Used for b-tagging efficiency measurements and scale factor derivation.

### MuonEG (2024)

8 entries (single stream). Used for mutau and etau cross-trigger studies.

### ParkingVBF (2024)

48+ entries across 8 parallel streams (ParkingVBF0 through ParkingVBF7),
multiple run periods, and version variants for Run2024I.

### ParkingSingleMuon (2024)

60+ entries across 8-12 parallel streams with extensive version splits.

## Earlier Years

### 2022 (DATA_2022.json) and 2022EE (DATA_2022EE.json)

- Reconstruction tag: `22Sep2023`
- Run ranges: 2022C-G (split at EE boundary)
- Same stream structure as 2024 but different runs

### 2023 (DATA_2023.json) and 2023BPix (DATA_2023BPix.json)

- Reconstruction tag: `22Sep2023` variants
- Run ranges: 2023C-D (split at BPix issue boundary)

## Data Quality and JSON Files

Good-quality luminosity sections are certified by the CMS data quality
monitoring group and published as "Golden JSON" files.

| Year | Golden JSON | Run Range |
|---|---|---|
| 2022 / 2022EE | `Cert_Collisions2022_355100_362760_Golden.json` | 355100-362760 |
| 2023 / 2023BPix | `Cert_Collisions2023_366442_370790_Golden.json` | 366442-370790 |
| 2024 | `Cert_Collisions2024_378981_386951_Golden.json` | 378981-386951 |

These files are stored in the `jsons/` directory and applied during CRAB
submission via `config.Data.lumiMask`. They filter out luminosity sections
affected by:
- Detector subsystem issues (tracker, calorimeters, muon system)
- Beam conditions problems
- DAQ and trigger malfunctions
- Unusual noise or backgrounds

Data configs do not hard-code the lumi mask; instead, `crabby.py` applies it
dynamically based on the year:
```python
"lumiMask": f"jsons/{JSONS[args.year]}" if isData else None
```

## Processing Considerations

### CRAB Submission for Data

Data jobs use `LumiBased` splitting with 50 lumis per job and a maximum runtime
of 2750 minutes:
```python
config.Data.splitting = 'LumiBased'
config.Data.unitsPerJob = 50
config.JobType.maxJobRuntimeMin = 2750
```

### Data Tier Implications

- **NANOAOD** (JetMET): No further processing needed for standard analysis;
  can be used directly.
- **MINIAOD** (all others): Requires NanoAOD production using the project
  configs before analysis.

### Multi-Version Datasets

For Run2024I, several streams have both v1 and v2 processing versions. Both
should be submitted to ensure complete luminosity coverage. The golden JSON
lumi mask handles any overlap by selecting only certified good luminosity
sections.

## Related Files

- `/home/das214/HHtobbtautau/Run3_nano_submission/datasets/DATA_2024.json`
- `/home/das214/HHtobbtautau/Run3_nano_submission/datasets/DATA_2023.json`
- `/home/das214/HHtobbtautau/Run3_nano_submission/datasets/DATA_2022.json`
- `/home/das214/HHtobbtautau/Run3_nano_submission/datasets/DATA_2022EE.json`
- `/home/das214/HHtobbtautau/Run3_nano_submission/datasets/DATA_2023BPix.json`
- `/home/das214/HHtobbtautau/Run3_nano_submission/jsons/` -- Golden JSON files.
