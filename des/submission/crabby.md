# crabby.py -- CRAB Job Configuration and Submission

`crabby.py` is the primary entry point for generating and submitting CRAB jobs.
It reads dataset catalogs from JSON files, maps each dataset to the correct CMSSW
configuration, fills the CRAB template with per-dataset values, and optionally
submits jobs to the grid.

**Source file:** `crabby.py` (repository root)

## Command-Line Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--year` | Yes | -- | Data-taking era: `2022`, `2022EE`, `2023`, `2023BPix`, `2024` |
| `--dataset` | Yes | -- | Dataset group name (e.g., `HHbbtt`, `TT`, `JetMET`) |
| `--scouting` | No | `False` | Use scouting NanoAOD configuration instead of standard |
| `--make` | No | `False` | Generate per-dataset CRAB config files |
| `--submit` | No | `False` | Submit previously generated CRAB configs |
| `--status` | No | `False` | Query CRAB status and collect output DAS names |
| `--test` | No | `False` | Test mode: process 1 unit only, disable publication |
| `--card` | No | `None` | Path to a YAML card that overrides default parameters |
| `--user` | No | `$USER` | Username for storage path (auto-detected from `$USER`, splitting on `-`) |
| `--campain` | No | `NanoAODv15Scouting24` | Production campaign string used in TAG and output paths |

Both `--make` and `--submit` can be passed together in a single invocation.
When `--submit` is used without `--make`, the script expects that config files
already exist in the work area from a prior `--make` run.

## How It Reads Dataset JSON Files

The script determines which JSON file to read based on `--year` and whether the
dataset name matches a known data stream:

```python
DATASETS = ["JetMET", "EGamma", "Muon", "MuonEG", "BTagMu", "Tau"]
```

If `--dataset` matches one of these names, `crabby.py` loads from
`datasets/DATA_{year}.json`. Otherwise, it loads from `datasets/MC_{year}.json`.

Each JSON file is structured as:

```json
{
    "HHbbtt": {
        "GluGluHHto2B2Tau_...": "/GluGluHHto2B2Tau_.../MINIAODSIM",
        "VBFHHto2B2Tau_...": "/VBFHHto2B2Tau_.../MINIAODSIM"
    },
    "TT": { ... }
}
```

The script indexes by the `--dataset` argument to retrieve the dictionary of
subsample names to DAS dataset paths. Only entries with string length > 10
and not starting with `#` are processed (commented-out entries are skipped):

```python
datasets = [value for key, value in card["datasets"].items()
            if len(value) > 10 and not value.startswith("#")]
```

## Dataset-to-Config Mapping

The central mapping from dataset type and year to CMSSW config file is defined
in the `CONFIGS` dictionary:

```python
CONFIGS = {
    "data": {
        "2022": "DATA_2022_NANO.py",
        "2022EE": "DATA_2022_NANO.py",
        "2023": "DATA_2023_NANO.py",
        "2023BPix": "DATA_2023_NANO.py",
        "2024": "DATA_2024_NANO.py",
    },
    "mc": {
        "2022": "MC_preEE2022_NANO.py",
        "2022EE": "MC_postEE2022_NANO.py",
        "2023": "MC_preBPix2023_NANO.py",
        "2023BPix": "MC_postBPix2023_NANO.py",
        "2024": "MC_2024_NANO.py",
    },
    "mcscouting": {
        "2022": "MC_preEE2022_NANO.py",
        "2022EE": "MC_postEE2022_NANO.py",
        "2023": "MC_preBPix2023_NANO.py",
        "2023BPix": "MC_postBPix2023_NANO.py",
        "2024": "MC_2024_Scouting.py",
    },
}
```

The label is chosen as follows:

- `"data"` -- dataset name is in the `DATASETS` list and `--scouting` is not set.
- `"datascouting"` -- dataset name is in `DATASETS` and `--scouting` is set.
  (Note: there is no `"datascouting"` key in `CONFIGS`, so this currently only
  works for MC scouting.)
- `"mc"` -- dataset name is not in `DATASETS` and `--scouting` is not set.
- `"mcscouting"` -- dataset name is not in `DATASETS` and `--scouting` is set.

The selected config file path is prefixed with `configs/`, for example
`configs/MC_2024_Scouting.py`.

For data, a luminosity mask JSON is also applied from the `JSONS` dictionary,
selecting the appropriate Golden JSON for the year.

## TAG Versioning and Naming

The TAG string serves as the production campaign identifier and appears in both
the output directory path and the CRAB work area. It defaults to `"25v2"` but is
overridden by the `--campain` argument (default: `NanoAODv15Scouting24`):

```python
TAG = "25v2"
# overridden at parse time:
if args.campain != "":
    TAG = args.campain
```

The output dataset tag (`_outputDatasetTag_`) is derived from the third field
of the DAS dataset path (the processing string). Two modification modes exist:

- **tag_mod** (default: `None`) -- Replaces `MiniAOD[v][N]` in the processing
  string with the specified value, or appends it if the tag does not start with `RunII`.
- **tag_extension** (default: `"DAZSLE_PFNano"`) -- Appends `_DAZSLE_PFNano` to
  the existing processing string.

Exactly one of `tag_mod` or `tag_extension` must be non-`None`; specifying both
causes the script to exit.

## Output Directory Structure

CRAB output is organized under the user's storage area on the Tier-2 site:

```
/store/user/<username>/production/Scouting/<campaign>/<dlabel>_<year>/
```

For example, with default settings and user `das214`:

```
/store/user/das214/production/Scouting/NanoAODv15Scouting24/mcscouting_2024/
```

The local CRAB work area is:

```
crab/<TAG>/<dlabel>_<year>_<dataset>/
    submit_<dataset_name>.py        # generated CRAB config per subsample
    crab_<request_name>/            # CRAB project directory (after submission)
```

## Request Name Truncation

CRAB imposes a maximum length on request names. If the dataset name (with slashes
replaced by underscores) exceeds 95 characters, it is truncated to 90 characters
and an 8-character deterministic random suffix is appended. The random seed is
derived from a SHA-512 hash of the dataset name, ensuring the same dataset always
produces the same suffix.

## Batch Submission

The `submit_wrapper` function submits each dataset in a separate `multiprocessing.Process`.
This isolates each CRAB submission so that a failure on one dataset does not block
others. Each process calls `crabCommand("submit", config=config)` from the CRAB API.

For data jobs, additional parameters are injected:

- `config.Data.unitsPerJob = 50` (50 lumisections per job)
- `config.JobType.maxJobRuntimeMin = 2750` (~46 hours maximum runtime)
- Luminosity mask from the Golden JSON for the appropriate year

## Example Commands

```bash
# Test submission of scouting HHbbtt for 2024
python3 crabby.py --year 2024 --dataset HHbbtt --scouting --make --submit --test True

# Full production of scouting TT background
python3 crabby.py --year 2024 --dataset TT --scouting --make --submit

# Standard (non-scouting) data submission for JetMET 2024
python3 crabby.py --year 2024 --dataset JetMET --make --submit

# Generate configs only, using a custom campaign tag
python3 crabby.py --year 2024 --dataset DYJetsNLO --scouting --campain ScoutingV2_test --make

# Check status and collect output DAS names
python3 crabby.py --year 2024 --dataset HHbbtt --scouting --status

# Use a YAML card for custom parameters
python3 crabby.py --year 2024 --dataset HHbbtt --card cards/custom.yaml --make --submit
```

## YAML Card Override

When `--card` is provided, the YAML file is loaded and its `campaign:` key
(if present) is merged on top of the default parameter dictionary using Python
dict union (`defaults | input_card`). This allows overriding any parameter:
`storageSite`, `publication`, `outLFNDirBase`, `tag_mod`, `tag_extension`, etc.
