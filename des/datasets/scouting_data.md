# Scouting-Specific Datasets

This document covers the CMS scouting datasets used in the HH->bbtautau
analysis, including available years, trigger evolution, and processing
considerations unique to the scouting data stream.

## What is Scouting Data?

CMS scouting (also called "data scouting" or "trigger-level analysis") collects
reduced-format physics objects directly from the HLT (High-Level Trigger)
system, bypassing the standard offline reconstruction chain. This enables:

- **Lower trigger thresholds**: Events that fail standard triggers can still be
  recorded as scouting data, providing access to lower-pT phase space.
- **Higher event rates**: Reduced event size allows recording more events per
  second.
- **Faster availability**: No need for offline reconstruction before analysis.

The trade-off is reduced information quality compared to fully reconstructed
data: scouting objects have lower resolution, no offline calibrations, and
limited tracking information.

## Scouting Datasets in This Analysis

All scouting data is stored in `Scouting_DATA.json`, organized by year.

### 2022 Scouting (5 runs)

| Run | DAS Path |
|---|---|
| Run2022C | `/ScoutingPFRun3/Run2022C-ScoutNano-v1/NANOAOD` |
| Run2022D | `/ScoutingPFRun3/Run2022D-ScoutNano-v1/NANOAOD` |
| Run2022E | `/ScoutingPFRun3/Run2022E-ScoutNano-v1/NANOAOD` |
| Run2022F | `/ScoutingPFRun3/Run2022F-ScoutNano-v1/NANOAOD` |
| Run2022G | `/ScoutingPFRun3/Run2022G-ScoutNano-v1/NANOAOD` |

### 2023 Scouting (2 runs)

| Run | DAS Path |
|---|---|
| Run2023C | `/ScoutingPFRun3/Run2023C-ScoutNano-v1/NANOAOD` |
| Run2023D | `/ScoutingPFRun3/Run2023D-ScoutNano-v1/NANOAOD` |

The 2023 scouting dataset has limited run coverage compared to other years.

### 2024 Scouting (8 runs)

| Run | DAS Path |
|---|---|
| Run2024C | `/ScoutingPFRun3/Run2024C-ScoutNano-v1/NANOAOD` |
| Run2024D | `/ScoutingPFRun3/Run2024D-ScoutNano-v1/NANOAOD` |
| Run2024E | `/ScoutingPFRun3/Run2024E-ScoutNano-v1/NANOAOD` |
| Run2024F | `/ScoutingPFRun3/Run2024F-ScoutNano-v1/NANOAOD` |
| Run2024G | `/ScoutingPFRun3/Run2024G-ScoutNano-v1/NANOAOD` |
| Run2024H | `/ScoutingPFRun3/Run2024H-ScoutNano-v1/NANOAOD` |
| Run2024I | `/ScoutingPFRun3/Run2024I-ScoutNano-v1/NANOAOD` |
| Run2024J | `/ScoutingPFRun3/Run2024J-ScoutNano-v1/NANOAOD` |

2024 provides the most complete scouting dataset with the widest run coverage.
This is the primary year for the scouting analysis pathway.

## Dataset Format: ScoutNano

Scouting data is already provided in NANOAOD format by the central CMS
scouting group under the `ScoutNano` processing tag. The primary dataset
name is always `ScoutingPFRun3`.

### Content of ScoutNano Files

ScoutNano files contain flat tables produced from HLT scouting objects:

| Collection | Content |
|---|---|
| ScoutingPFJet | HLT PF jets (directly from scouting packer) |
| ScoutingMuon | HLT muons (with and without vertex) |
| ScoutingElectron | HLT electrons |
| ScoutingPhoton | HLT photons |
| ScoutingPFCandidate | HLT PF candidates |
| ScoutingTrack | HLT tracks |
| ScoutingPrimaryVertex | HLT primary vertices |
| TriggerResults | HLT trigger decision bits |

These collections use HLT-level reconstruction, which differs from offline
reconstruction in resolution and calibration.

## Scouting Trigger Menu Evolution

The Run 3 scouting trigger menu has evolved across years, with implications
for the available phase space and event rates.

### 2022 Scouting Triggers

- Initial Run 3 scouting menu
- PF jet scouting with basic thresholds
- Limited HT and dijet triggers

### 2023 Scouting Triggers

- Expanded trigger menu
- Lower jet pT thresholds enabled
- Improved scouting muon triggers

### 2024 Scouting Triggers

- Most mature Run 3 scouting menu
- Lowest jet thresholds, enabling HH->bbtautau with softer jets
- Additional topology-based triggers (e.g., multi-jet, b-jet triggers)
- Scouting track triggers with improved resolution

The 2024 menu is the primary target for HH->bbtautau because it provides the
lowest effective thresholds for b-jets and tau-jets.

## Processing Pipeline for Scouting

Unlike standard data (which goes through offline reconstruction), scouting data
requires a specialized processing pipeline:

```
ScoutNano (HLT objects)
    |
    v
ScoutingTranslator (translation layer)
    |  - Converts packed scouting objects to reco format
    |  - Produces recoScoutingPFCandidate, recoScoutingTrack, etc.
    |
    v
Jet Reclustering
    |  - AK4 jets from recoScoutingPFCandidate (R=0.4, pT>20 GeV)
    |  - AK8 fat jets (R=0.8, pT>170 GeV)
    |  - JEC with AK4PFHLT / AK8PFHLT payloads
    |
    v
Vertex Reconstruction
    |  - Primary vertices from scouting tracks
    |  - Secondary vertices via inclusive vertex finder
    |
    v
ML Tagger Inference
    |  - HLT ParticleNet (AK4 and AK8)
    |  - UParT AK4 (custom HH->bbtautau model)
    |  - ONNX runtime inference
    |
    v
NanoAOD Output
    - ScoutingPFJetRecluster2 table with tagger scores
    - ScoutingFatPFJetRecluster2 table
    - SV, V0, beamspot tables
```

This pipeline is implemented in `MC_2024_Scouting.py` and the
ScoutingTranslator package. For MC samples, the config uses
`@GENFromMini+@ScoutFromMini` to process MiniAOD as if it were scouting data,
enabling truth-level studies on MC.

## Data Volume and Processing Considerations

### File Sizes

Scouting datasets are significantly larger in event count than standard streams
because of the lower trigger thresholds. However, each event is smaller due to
the reduced object information.

### Download Strategy

The project provides `download_scouting_data.py` with multi-threaded downloading
(12 threads by default) to handle the large scouting datasets:

```bash
python download_scouting_data.py --year 2024 --threads 12 --user das214
```

Files are downloaded to:
```
root://eos.cms.rcac.purdue.edu/store/user/{user}/production/Scouting/{campaign}/data_{year}/
```

### Processing Time

Scouting NanoAOD production with the ScoutingTranslator and UParT tagger is
computationally intensive due to:
- ONNX model inference for UParT on every jet
- Jet reclustering from individual PF candidates
- Secondary vertex finding from scouting tracks
- Multi-threaded processing helps (configs use 4 threads)

### Memory Requirements

The ONNX models are loaded into memory at job startup. The
`Scouting_HHbbtautau/V00/model.onnx` and `Scouting/V00/model.onnx` files are
loaded by the ONNX runtime. The `customiseEarlyDelete` function in the config
helps manage peak memory by removing intermediate data products.

## Scouting vs Standard Data Comparison

| Aspect | Scouting Data | Standard Data |
|---|---|---|
| Input format | ScoutNano (NANOAOD) | MINIAOD / NANOAOD |
| Jet source | Reclustered from HLT PF candidates | PAT jets from offline reco |
| Vertex source | Reconstructed from HLT tracks | Offline PV |
| B-tagging | UParT (scouting model) + HLT PNet | DeepJet, ParticleNet, offline UParT |
| Jet energy corrections | AK4PFHLT payload | AK4PFchs / AK4PFPuppi |
| Trigger thresholds | Lower (scouting menu) | Higher (standard menu) |
| Event rate | Higher | Lower |
| Resolution | HLT-level | Offline-level |
| CMSSW requirements | 16_0_1 + external packages | Standard NanoAODv15 |

## Related Files

- `/home/das214/HHtobbtautau/Run3_nano_submission/datasets/Scouting_DATA.json`
- `/home/das214/HHtobbtautau/Run3_nano_submission/configs/MC_2024_Scouting.py`
- `/home/das214/HHtobbtautau/Run3_nano_submission/configs/DATA_2024.py` (older
  scouting config variant)
