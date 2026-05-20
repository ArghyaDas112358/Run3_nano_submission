# template_crab.py -- CRAB Configuration Template

`template_crab.py` defines the CRAB job configuration skeleton. It contains
placeholder tokens (e.g., `_requestName_`, `_inputDataset_`) that `crabby.py`
fills with per-dataset values at generation time. This file is read as raw text
and processed by string replacement rather than imported as a Python module.

**Source file:** `template_crab.py` (repository root)

## Template Structure

The template instantiates a `CRABClient.UserUtilities.config` object and sets
four configuration sections: `General`, `JobType`, `Data`, `Debug`, and `Site`.

```python
from CRABClient.UserUtilities import config

config = config()

config.General.requestName = "_requestName_"
config.General.workArea = "_workArea_"
config.General.transferLogs = True

config.JobType.pluginName = "Analysis"
config.JobType.psetName = "_psetName_"
config.JobType.maxMemoryMB = 5000
config.JobType.numCores = 4
config.JobType.allowUndistributedCMSSW = True

config.Debug.extraJDL = ["+CMS_ALLOW_OVERFLOW=False"]

config.Data.inputDataset = "_inputDataset_"
config.Data.outputDatasetTag = "_outputDatasetTag_"
config.Data.outLFNDirBase = "_outLFNDirBase_"
config.Data.splitting = "_splitting_"
config.Data.ignoreLocality = False
config.Data.publication = "_publication_"
config.Data.allowNonValidInputDataset = True
config.Data.publishDBS = "phys03"

config.Site.storageSite = "_storageSite_"
```

## Placeholder Tokens

Each `_token_` in the template is replaced by `crabby.py` via `str.replace()`.
The following table lists all tokens and their source:

| Token | Filled From | Example Value |
|-------|------------|---------------|
| `_requestName_` | Sanitized dataset name (slashes to underscores, truncated to 95 chars) | `GluGluHHto2B2Tau_Par-c2-...MINIAODSIM` |
| `_workArea_` | `crab/<TAG>/<dlabel>_<year>_<dataset>` | `crab/NanoAODv15Scouting24/mcscouting_2024_HHbbtt` |
| `_psetName_` | `configs/<config_file>` from `CONFIGS` dict | `configs/MC_2024_Scouting.py` |
| `_inputDataset_` | Full DAS path from dataset JSON | `/GluGluHHto2B2Tau_.../MINIAODSIM` |
| `_outLFNDirBase_` | `/store/user/<user>/production/Scouting/<campaign>/<dlabel>_<year>` | `/store/user/das214/production/Scouting/NanoAODv15Scouting24/mcscouting_2024` |
| `_storageSite_` | Default or card override | `T2_US_Purdue` |
| `_publication_` | `True` or `False` (string) | `True` |
| `_splitting_` | `LumiBased` for data, `Automatic` for MC | `Automatic` |
| `_outputDatasetTag_` | Processing string from DAS path, with `tag_extension` appended | `PowhegBugFix_150X_..._DAZSLE_PFNano` |

## Key Resource Parameters

### Memory: 5000 MB

```python
config.JobType.maxMemoryMB = 5000
```

Each CRAB job requests 5 GB of RAM. This is required because the scouting NanoAOD
workflow runs multiple ML inference engines simultaneously:

- **UParT AK4 tagger** -- ONNX model inference for 8 flavor classification scores
  on reclustered AK4 jets.
- **HLT ParticleNet** -- ONNX inference for AK4 and AK8 jet tagging.
- **GloParT** -- AK8 fat jet classification.

The ONNX runtime and the jet reclustering chain (primary vertex reconstruction,
secondary vertex finding, track association, JEC application) contribute
significantly to peak memory usage. 5 GB provides adequate headroom for events
with high jet multiplicity.

### Cores: 4

```python
config.JobType.numCores = 4
```

Four cores are allocated per job, matching the `numberOfThreads = 4` setting
in the CMSSW config files (e.g., `MC_2024_Scouting.py` line 106). This enables
CMSSW framework multithreading across the processing modules.

### Splitting Strategy

The splitting strategy depends on whether the input is data or MC:

- **MC:** `Automatic` -- CRAB determines the optimal number of files per job
  based on available resources and dataset size.
- **Data:** `LumiBased` -- Jobs are split by luminosity sections, with
  `unitsPerJob = 50` (50 lumi sections per job). Data jobs also receive a
  longer maximum runtime of 2750 minutes (~46 hours) via
  `config.JobType.maxJobRuntimeMin = 2750`.

### Overflow Control

```python
config.Debug.extraJDL = ["+CMS_ALLOW_OVERFLOW=False"]
```

Overflow to other CMS sites is disabled. Jobs run only at the site where the
input dataset is located. This avoids the WAN data transfer overhead that would
be incurred when processing the full MINIAOD input.

## Input Dataset and DBS Configuration

```python
config.Data.inputDataset = "_inputDataset_"
config.Data.allowNonValidInputDataset = True
config.Data.publishDBS = "phys03"
```

- **inputDataset**: The full DAS path to the MINIAOD(SIM) dataset, injected
  per-subsample from the JSON catalog.
- **allowNonValidInputDataset**: Set to `True` to permit processing datasets
  that are in `PRODUCTION` or `VALID` state in DBS. This is important for
  newly produced MC samples that may not yet be fully validated.
- **publishDBS**: Output NanoAOD files are published to the `phys03` DBS
  instance, making them discoverable via DAS for downstream analysis.
- **ignoreLocality**: Set to `False`, meaning CRAB respects data locality
  and schedules jobs at the site hosting the input files.

## Output Storage

```python
config.Data.outLFNDirBase = "_outLFNDirBase_"
config.Site.storageSite = "_storageSite_"
```

The default storage site is **T2_US_Purdue**. Output files are written to the
user's storage area under the LFN base:

```
/store/user/<user>/production/Scouting/<campaign>/<dlabel>_<year>/
```

Published output datasets appear in DBS `phys03` with the tag constructed
from the original processing string plus the `tag_extension` suffix.

## How Template Variables Get Filled

The filling process in `crabby.py` works as follows:

1. The template file is read as a raw string: `base_crab_config = open("template_crab.py").read()`.
2. A deep copy is made for each dataset.
3. A dictionary `card_info` maps each placeholder token to its replacement value.
4. Additional verbatim lines are appended for data-specific settings (lumi mask,
   units per job, max runtime) and test-mode overrides.
5. All placeholders are replaced via `crab_config.replace(key, card_info[key])`.
6. The resulting string is written to `crab/<workArea>/submit_<dataset_name>.py`.

The generated file is a valid Python module that can be imported by the CRAB client
or inspected manually.

## Job Sandbox and Runtime Environment

CRAB packages the CMSSW area into a sandbox that is transferred to the worker node.
The key components included are:

- The CMSSW configuration file (e.g., `configs/MC_2024_Scouting.py`)
- All compiled CMSSW code from `cmssw/CMSSW_16_0_1/`
- ScoutingTranslator plugins and Python configs
- RecoBTag ONNX runtime plugins and UParT model files
- Custom `DAZSLE/DAZSLE/python/` customization modules

The `allowUndistributedCMSSW = True` setting permits use of locally built CMSSW
areas that are not part of the official CMSSW distribution. This is necessary
because the scouting workflow includes custom C++ plugins (scouting-specific
UParT producer, feature extraction tools) that are not in the central CMSSW release.

Log transfer is enabled (`transferLogs = True`) so that job stdout/stderr are
available for debugging failed jobs.
