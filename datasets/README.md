# Datasets

Sample catalogs for CRAB submission.  These JSONs (one per year, plus
`Scouting_DATA.json`) are read by `crabby.py` as `--dataset` lookup
tables.  See the top-level [`CLAUDE.md`](../CLAUDE.md) for the
operator workflow.

## Files

| File | Purpose |
|---|---|
| `MC_<year>.json` | MC dataset catalog (5 years: 2022, 2022EE, 2023, 2023BPix, 2024) |
| `DATA_<year>.json` | Data catalog per year (JetMET / Muon / EGamma / MuonEG / BTagMu / Tau / ParkingVBF / ParkingSingleMuon) |
| `Scouting_DATA.json` | Scouting NANOAOD data (Run2024C-J) |
| `get_mc.py` | DAS-querying script that regenerates `MC_<year>.json` |
| `get_datasets.py` | DAS-querying script that regenerates `DATA_<year>.json` |
| `utils.py` | Helpers shared by the two scripts |
| `old_backup/` | Archived earlier versions — do not regenerate over |

## Setup

`get_mc.py` and `get_datasets.py` depend on `dbs3-client` (CMS DBS REST
client).  Install it once:

```bash
pip3 install --user dbs3-client
```

**Important environment gotcha:** `dbs3-client` is broken by
`source /cvmfs/cms.cern.ch/common/crab-setup.sh`.  Always regenerate
JSON catalogs **before** sourcing `crab-setup.sh`, or do it in a
separate shell where you only sourced `cmsenv`.

Both scripts must be run from this `datasets/` directory (the relative
import of `utils.py` fails otherwise).

## Regenerating the catalogs

### Data

```bash
cd datasets
python3 get_datasets.py --years 2024 --datasets JetMET Muon
```

| Flag | Meaning |
|---|---|
| `--years` | One or more from `2022 2022EE 2023 2023BPix 2024` (default: all years) |
| `--datasets` | One or more category keys from `DATASETS` in `get_datasets.py` (default: all) |

Output is written to `DATA_<year>.json` (whole-file overwrite — there
is no `--append` mode on the data script).

### MC

```bash
cd datasets
python3 get_mc.py --years 2024 --samples VJetsLO Diboson --append --overwrite-samples
```

| Flag | Meaning |
|---|---|
| `--years` | One or more from `2022 2022EE 2023 2023BPix 2024` (default: all) |
| `--samples` | One or more category keys from `SAMPLES` in `get_mc.py` (default: all) |
| `--append` / `--no-append` | Merge into existing `MC_<year>.json` instead of overwriting. **Default: `--append`** |
| `--overwrite-samples` / `--no-overwrite-samples` | When `--append` is on, allow overwriting the queried sample groups in place. **Default: `--no-overwrite-samples`** (skips existing groups with a warning) |
| `--save` / `--no-save` | Whether to write the JSON at all. **Default: `--save`** (use `--no-save` for dry-run inspection) |
| `--tsg` / `--no-tsg` | Include datasets whose `prep_id` starts with `TSG`. **Default: `--no-tsg`** |

The safest pattern when adding new samples is **append + overwrite the
specific groups you're touching**:

```bash
python3 get_mc.py --years 2024 --samples VJetsLO --append --overwrite-samples
```

This re-queries DAS for `VJetsLO` only, leaves every other top-level
key in `MC_2024.json` untouched, and reports any naming-convention
mismatches.

## Adding new datasets

### Data

1. Add the new stream name + DAS selector list to `DATASETS` in
   `get_datasets.py`.
2. Run `python3 get_datasets.py --years <year> --datasets <name>`.
3. Diff `DATA_<year>.json` to verify expected datasets appear and none
   disappeared accidentally.
4. Add the new stream name to `crabby.py`'s `DATASETS` list so it is
   submittable as data (not silently treated as MC).
5. Open a PR.

### MC

1. Decide the sample's category (`HH4b`, `Diboson`, `VJetsLO`, …) or
   create a new one in `SAMPLES` in `get_mc.py`.
2. Add a `Sample(selector, expected_datasets, strict=…)` entry.  Use
   the broadest correct DAS-glob selector — note that 2024 production
   inserts a `_Bin-` infix before HT/PT/PTQQ/PTG bin tags
   (e.g. `Wto2Q-3Jets_Bin-HT-200to400` in 2024 vs
   `Wto2Q-3Jets_HT-200to400` in 2022/2023), so `Wto2Q-3Jets*HT*` matches
   both naming forms while `Wto2Q-3Jets_HT*` silently misses every 2024
   dataset.
3. Run `python3 get_mc.py --years <year> --samples <category> --append --overwrite-samples`.
4. Diff `MC_<year>.json`.
5. Open a PR.
