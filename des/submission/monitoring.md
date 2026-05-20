# crab_status.py -- Job Monitoring and Resubmission

`crab_status.py` provides centralized monitoring of CRAB job progress across
multiple years and samples. It queries `crab status` for each submitted task,
aggregates completion percentages into a CSV file, and can generate color-coded
progress plots.

**Source file:** `crab_status.py` (repository root)

## Command-Line Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--years` | No | All years (`2022`, `2022EE`, `2023`, `2023BPix`, `2024`) | Which data-taking eras to check |
| `--samples` | Yes | -- | One or more sample names to monitor |

The `--samples` argument accepts any name from the `SAMPLES` dictionary in
`datasets/get_mc.py` (MC samples like `HHbbtt`, `TT`, `DYJetsNLO`, etc.)
or from the `DATASETS` dictionary in `datasets/get_datasets.py` (data streams
like `JetMET`, `Muon`, `EGamma`, `Tau`, `BTagMu`, `MuonEG`).

## Usage

```bash
# Check all years for HHbbtt and TT
python3 crab_status.py --samples HHbbtt TT

# Check only 2024 for specific samples
python3 crab_status.py --years 2024 --samples HHbbtt DYJetsNLO TT DYJetsLO

# Check data status
python3 crab_status.py --years 2024 --samples JetMET Muon EGamma
```

## How It Works

### Directory Discovery

The script constructs directory paths from the year and sample name:

```
crab/<datamc_label>_<year>_<sample>/
```

where `datamc_label` is `"data"` if the sample is a known data stream, or
`"mc"` otherwise. Within each directory, it finds all subdirectories whose
names contain `"crab"` -- these are the CRAB project directories created
during submission.

**Note:** The current implementation looks for directories under `crab/` without
the TAG prefix. If you submitted with a campaign tag (e.g., `crab/NanoAODv15Scouting24/...`),
you may need to adjust the directory path or create a symlink.

### Status Extraction

For each CRAB project directory, the script runs:

```bash
crab status -d <directory>
```

via `subprocess.run()` with `capture_output=True`. It parses the stdout
to extract:

- **Job completion percentage**: Extracted via regex from lines matching
  `finished X.X%`. The last match is used (CRAB output may contain
  multiple progress lines).
- **Output dataset**: The DAS path of the published output, extracted from
  lines containing `"Output dataset:"`.

### CSV Output

All results are written to `CrabStatus.csv` with columns:

```
Dataset, Subsample, Jobs Status, Output Dataset
```

The CSV is overwritten on each run (not appended). This file provides a
machine-readable summary suitable for downstream scripts or spreadsheet
analysis.

### Inline Status via crabby.py

`crabby.py` also has a built-in `--status` mode that provides similar
functionality but operates within the `crabby.py` framework. It iterates
over the datasets in the selected JSON catalog, constructs the CRAB project
directory paths, runs `crab status` via `os.popen()`, and filters the output
for key status lines (unsubmitted, idle, running, transferring, transferred,
finished, failed). It also writes output DAS names to a file named
`outputs_<card_name>.txt`.

## Progress Visualization

The `plotter()` function generates horizontal bar charts showing completion
percentage for each subsample. Bars are color-coded by completion range:

| Range | Color |
|-------|-------|
| 0-25% | Red |
| 25-50% | Orange |
| 50-75% | Yellow |
| 75-90% | Light green |
| 90-98% | Medium sea green |
| >98% | Dark green |

A vertical red line marks the 100% threshold. Plots are saved to
`ProgressPlots/<dir_name>.pdf` when a filename is provided. The plotter
uses matplotlib and numpy.

**Note:** The plotter call is currently commented out in `main()` (line 88).
To enable it, uncomment the line and ensure `ProgressPlots/` directory exists.

## Failed Job Handling and Resubmission

`crab_status.py` itself does not perform automatic resubmission. Failed jobs
must be resubmitted manually using the CRAB command-line tools:

```bash
# Check which jobs failed
crab status -d crab/<workarea>/crab_<request_name>/

# Resubmit failed jobs
crab resubmit -d crab/<workarea>/crab_<request_name>/

# Resubmit specific job IDs
crab resubmit -d crab/<workarea>/crab_<request_name>/ --jobids 1,5,12

# Force resubmission with more memory (if jobs failed due to memory)
crab resubmit -d crab/<workarea>/crab_<request_name>/ --maxmemory 8000

# Force resubmission with longer runtime
crab resubmit -d crab/<workarea>/crab_<request_name>/ --maxjobruntime 3500
```

## Output Collection and Validation

After all jobs complete, output NanoAOD files are stored on the configured
Tier-2 site (default: `T2_US_Purdue`) under the LFN base path. Published
datasets appear in the `phys03` DBS instance.

To verify output completeness:

1. Check the CSV file for any samples below 100%.
2. Use the output dataset DAS names to query file counts:
   ```bash
   dasgoclient --query="file dataset=<output_dataset>"
   ```
3. Compare event counts between input MINIAOD and output NanoAOD:
   ```bash
   dasgoclient --query="summary dataset=<input_dataset>" | python3 -m json.tool
   dasgoclient --query="summary dataset=<output_dataset>" | python3 -m json.tool
   ```

## Common Failure Modes

### Memory Exhaustion

Jobs processing events with very high jet multiplicity may exceed the 5 GB
memory limit. Symptoms: job status shows `MemoryError` or killed by condor.
Fix: resubmit with `--maxmemory 8000`.

### Timeout

Scouting NanoAOD production with UParT inference is computationally expensive.
Data jobs have a 2750-minute limit; MC uses the CRAB default. If jobs time out,
resubmit with `--maxjobruntime 3500`.

### Stageout Failures

If `T2_US_Purdue` storage is temporarily unavailable, stageout fails but the
job computation is complete. CRAB automatically retries stageout. If persistent,
check the site status on the CMS Site Status Board.

### Input File Access

If an input MINIAOD file has been deleted or the dataset is marked invalid in DBS,
jobs will fail at the input-reading stage. The `allowNonValidInputDataset = True`
setting in the template helps with datasets still in production state, but
cannot help with genuinely missing files.

### CMSSW Configuration Errors

If the CMSSW config has a Python syntax error or a missing module, all jobs for
that dataset will fail immediately. Always test locally with `cmsRun` before
submitting:

```bash
cmsRun configs/MC_2024_Scouting.py
```

## Integration with CMS Monitoring

### CRAB Dashboard

The CRAB web interface provides real-time monitoring:

- **Task Monitoring**: https://monit-grafana.cern.ch/d/�cmsTMGrafana/ (CMS Task Monitoring)
- **Task Worker**: https://cmsweb.cern.ch/crabserver/ui/task/ (per-task details)

Use `crab status --json` to get machine-readable status output for integration
with custom monitoring scripts.

### Grafana

CMS provides Grafana dashboards for site-level and task-level monitoring. Search
for your username in the CMS monitoring Grafana instance to see job efficiency,
wallclock usage, and failure breakdown by exit code.

### Transfer Logs

Since `transferLogs = True` is set in the template, job logs are available via:

```bash
crab getlog -d crab/<workarea>/crab_<request_name>/ --jobids 1
```

These logs contain the full `cmsRun` stdout and stderr, which are essential for
diagnosing CMSSW-level failures.
