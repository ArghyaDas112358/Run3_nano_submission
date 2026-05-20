# GlobalTag Mapping by Year and Type

GlobalTags specify the set of calibration constants, alignment parameters, and
detector conditions used during reconstruction and NanoAOD production. Using the
correct GlobalTag is critical for physics results.

## GlobalTag Table

### MC GlobalTags

| Year | Era | Config File | GlobalTag | CMSSW Generation |
|---|---|---|---|---|
| 2022 (pre-EE) | Run3_2024 | MC_preEE2022_NANO.py | `140X_mcRun3_2022_realistic_v12` | 130X |
| 2022EE (post-EE) | Run3_2024 | MC_postEE2022_NANO.py | `140X_mcRun3_2022_realistic_v12` | 130X |
| 2023 (pre-BPix) | Run3_2024 | MC_preBPix2023_NANO.py | `140X_mcRun3_2023_realistic_v9` | 130X |
| 2023BPix (post-BPix) | Run3_2024 | MC_postBPix2023_NANO.py | `140X_mcRun3_2023_realistic_v9` | 130X |
| 2024 (standard) | Run3_2024 | MC_2024_NANO.py | `140X_mcRun3_2024_realistic_v26` | 150X |
| 2024 (alternate) | Run3 | MC_2024.py | `140X_mcRun3_2024_realistic_v26` | 150X |
| 2024 (scouting) | Run3_2024 | MC_2024_Scouting.py | `auto:phase1_2024_realistic` | 150X |

### Data GlobalTags

| Year | Era | Config File | GlobalTag |
|---|---|---|---|
| 2022 | Run3_2024 | DATA_2022_NANO.py | `140X_dataRun3_v20` |
| 2022EE | Run3_2024 | DATA_2022_NANO.py | `140X_dataRun3_v20` |
| 2023 | Run3_2024 | DATA_2023_NANO.py | `140X_dataRun3_v20` |
| 2023BPix | Run3_2024 | DATA_2023_NANO.py | `140X_dataRun3_v20` |
| 2024 | Run3_2024 | DATA_2024_NANO.py | `140X_dataRun3_v20` |

## What GlobalTags Control

A GlobalTag aggregates hundreds of individual condition records from the CMS
Conditions Database (CondDB). The main categories are:

### Detector Alignment
- Tracker alignment (pixel + strip positions)
- Muon chamber alignment
- ECAL/HCAL geometry corrections

### Calibration Constants
- Jet energy corrections (JEC) -- L1, L2, L3, and residual corrections
- Jet energy resolution (JER) smearing factors
- b-tagging scale factors and working points
- Tau energy scale corrections
- ECAL intercalibration and laser corrections
- HCAL response corrections

### Beam and Luminosity
- Beamspot position and width
- Luminosity calibration constants
- Pileup reweighting profiles

### Trigger
- L1 trigger prescale columns
- HLT menu configuration references

### Simulation-Specific (MC only)
- Pileup scenario (number of interactions per bunch crossing)
- Detector response simulation parameters
- Material budget description

## GlobalTag Naming Convention

The tag format is `{CMSSW_version}X_{type}Run3_{version}`:

```
140X_mcRun3_2024_realistic_v26
 |     |       |        |     |
 |     |       |        |     +-- Version (v26 = 26th revision)
 |     |       |        +-------- Scenario (realistic simulation)
 |     |       +----------------- Year (2024 conditions)
 |     +------------------------- Type (mc = simulation, data = collision data)
 +------------------------------- CMSSW release series (140X = 14.0.X)
```

## Scouting-Specific GlobalTag Considerations

The scouting config uses `auto:phase1_2024_realistic` instead of an explicit
tag. This auto-tag resolves at runtime to the latest recommended GlobalTag for
2024 MC within the CMSSW release being used.

Key differences for scouting:
- **JEC payload**: Scouting reclustered jets use `AK4PFHLT` and `AK8PFHLT`
  correction payloads (HLT-level), not the standard offline `AK4PFchs` or
  `AK4PFPuppi` payloads.
- **Vertex conditions**: Scouting PV reconstruction uses track-based fitting
  from scouting tracks, so the vertex conditions must match the scouting
  track resolution model.
- **B-tagging conditions**: The UParT model files are loaded from the local
  filesystem (`RecoBTag/Combined/data/`) rather than from CondDB, so the
  GlobalTag does not control the tagger weights directly.

## How to Find and Update GlobalTags

### Finding the Current Recommended Tag

Check the CMS TWiki page for recommended GlobalTags:
```
https://twiki.cern.ch/twiki/bin/viewauth/CMS/PdmVRun3Analysis
```

Alternatively, query the conditions database:
```bash
conddb search --tag '*mcRun3_2024*'
```

### Checking What a GlobalTag Contains

```bash
conddb list <GlobalTag>
# Example:
conddb list 140X_mcRun3_2024_realistic_v26
```

### Using Auto-Tags

Auto-tags resolve to the latest recommended tag for a given scenario. Common
auto-tags used in this project:

| Auto-Tag | Resolves To | Use Case |
|---|---|---|
| `auto:phase1_2024_realistic` | Latest 2024 MC tag | Scouting MC config |
| `auto:run3_data` | Latest Run3 data tag | (Not currently used) |

The resolution happens at config-loading time based on the CMSSW release.
Auto-tags are convenient for development but explicit tags are preferred for
reproducible production.

## Matching GlobalTags to Input Samples

It is important that the NanoAOD production GlobalTag is compatible with the
conditions used to produce the input MiniAOD. The MiniAOD campaign tag
encodes the generation conditions:

| MiniAOD Campaign | Generation GlobalTag | NanoAOD GlobalTag |
|---|---|---|
| `Run3Summer22MiniAODv4 / 130X_mcRun3_2022_realistic_v5` | 130X series | `140X_mcRun3_2022_realistic_v12` |
| `Run3Summer22EEMiniAODv4 / 130X_mcRun3_2022_realistic_postEE_v6` | 130X series | `140X_mcRun3_2022_realistic_v12` |
| `Run3Summer23MiniAODv4 / 130X_mcRun3_2023_realistic_v14` | 130X series | `140X_mcRun3_2023_realistic_v9` |
| `Run3Summer23BPixMiniAODv4 / 130X_mcRun3_2023_realistic_postBPix_v2` | 130X series | `140X_mcRun3_2023_realistic_v9` |
| `RunIII2024Summer24MiniAODv6 / 150X_mcRun3_2024_realistic_v2` | 150X series | `140X_mcRun3_2024_realistic_v26` |

The NanoAOD GlobalTag (140X series) is typically more recent than the MiniAOD
generation tag (130X or 150X) because it includes updated calibrations and
corrections developed after the MiniAOD production.

## Lumi Masks (Data Quality JSONs)

For data processing, lumi masks complement GlobalTags by selecting only
certified good-quality luminosity sections:

| Year | Golden JSON File |
|---|---|
| 2022 / 2022EE | `Cert_Collisions2022_355100_362760_Golden.json` |
| 2023 / 2023BPix | `Cert_Collisions2023_366442_370790_Golden.json` |
| 2024 | `Cert_Collisions2024_378981_386951_Golden.json` |

These are applied via `config.Data.lumiMask` in the CRAB submission, not in
the CMSSW config itself.

## Related Files

- `/home/das214/HHtobbtautau/Run3_nano_submission/jsons/` -- Golden JSON lumi
  mask files.
- `/home/das214/HHtobbtautau/Run3_nano_submission/crabby.py` -- JSONS dictionary
  mapping years to lumi mask files.
