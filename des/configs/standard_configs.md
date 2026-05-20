# Standard MC and Data Configs

This document covers the non-scouting configuration files used for standard
NanoAOD production from MiniAOD input across all Run 3 years.

## Common Architecture

All standard configs (MC and Data) share the same generation approach using
`cmsDriver.py` with the `NANO:@BTV` step, which enables NanoAODv15 production
with BTV (b-tag and vertexing) customizations.

### Generation Command Pattern

```
cmsDriver.py <config_name> \
  --fileout file:<output>.root \
  --conditions <GlobalTag> \
  --filein <MiniAOD_file> \
  --customise DAZSLE/DAZSLE/customize.customize \
  --step NANO:@BTV --scenario pp \
  --customise_commands "process.add_(cms.Service('InitRootHandlers',EnableIMT=cms.untracked.bool(False)));process.MessageLogger.cerr.FwkReport.reportEvery=1000" \
  --no_exec -n 10 --nThreads 4 \
  --era Run3_2024 \
  --eventcontent <NANOAODSIM|NANOAOD> \
  --datatier <NANOAODSIM|NANOAOD> \
  <--mc|--data>
```

### Customization Chain (Standard Configs)

All standard configs apply three customizations in order:

1. **DAZSLE.DAZSLE.customize.customize** -- Analysis-specific customizations
   from the customize.py module (tau variables, boosted tau cuts, PV extensions,
   lepton lifetime info, IP covariance). See `des/configs/customizations.md`.

2. **PhysicsTools.NanoAOD.nano_cff.nanoAOD_customizeCommon** -- Standard CMS
   NanoAOD common customizations (trigger objects, MET filters, etc.).

3. **PhysicsTools.NanoAOD.custom_btv_cff.BTVCustomNanoAOD** -- BTV group
   customization that adds extended b-tagging discriminators, jet flavor
   information, and track-level variables to the NanoAOD output.

### NanoAOD Sequence

| Data Type | Main Sequence | Module Loaded |
|---|---|---|
| MC | `process.nanoSequenceMC` | `PhysicsTools.NanoAOD.nano_cff` |
| Data | `process.nanoSequence` | `PhysicsTools.NanoAOD.nano_cff` |

The MC sequence includes generator-level tables (GenParticles, GenJets, LHE
weights) while the data sequence omits them. Both include the full set of
reconstructed object tables (jets, taus, electrons, muons, photons, MET).

## Standard Jet Tagging

Through the `@BTV` step and `BTVCustomNanoAOD` customization, standard configs
include the following jet taggers:

- **DeepJet** (DeepFlavour) -- Standard b-tagging and c-tagging discriminators.
- **ParticleNet** -- Advanced GNN-based tagger for b/c/light jet
  discrimination and jet mass regression.
- **RobustParTAK4** -- Robust Particle Transformer for AK4 jets.
- **UParT** -- Unified Particle Transformer (standard offline version, not the
  scouting-specific variant).

These taggers operate on standard PAT jets reconstructed from MiniAOD, unlike
the scouting config which recluters jets from scouting PF candidates.

## MC Configs by Year

### MC_preEE2022_NANO.py (2022 pre-EE)

- **Era**: `Run3_2024`
- **GlobalTag**: `140X_mcRun3_2022_realistic_v12`
- **Input sample era**: `Run3Summer22MiniAODv4` / `130X_mcRun3_2022_realistic_v5`
- **Used for**: MC datasets in `MC_2022.json`

### MC_postEE2022_NANO.py (2022 post-EE)

- **Era**: `Run3_2024`
- **GlobalTag**: `140X_mcRun3_2022_realistic_v12`
- **Input sample era**: `Run3Summer22EEMiniAODv4` / `130X_mcRun3_2022_realistic_postEE_v6`
- **Used for**: MC datasets in `MC_2022EE.json`
- **Note**: Same GlobalTag as pre-EE, but input samples have different
  conditions reflecting the post-ECAL endcap (EE) recovery period.

### MC_preBPix2023_NANO.py (2023 pre-BPix)

- **Era**: `Run3_2024`
- **GlobalTag**: `140X_mcRun3_2023_realistic_v9`
- **Input sample era**: `Run3Summer23MiniAODv4` / `130X_mcRun3_2023_realistic_v14`
- **Used for**: MC datasets in `MC_2023.json`

### MC_postBPix2023_NANO.py (2023 post-BPix)

- **Era**: `Run3_2024`
- **GlobalTag**: `140X_mcRun3_2023_realistic_v9`
- **Input sample era**: `Run3Summer23BPixMiniAODv4` / `130X_mcRun3_2023_realistic_postBPix_v2`
- **Used for**: MC datasets in `MC_2023BPix.json`
- **Note**: Same GlobalTag as pre-BPix; input samples have different conditions
  reflecting the period after BPix (barrel pixel) issue in 2023.

### MC_2024_NANO.py (2024 standard)

- **Era**: `Run3_2024`
- **GlobalTag**: `140X_mcRun3_2024_realistic_v26`
- **Input sample era**: `RunIII2024Summer24MiniAODv6` / `150X_mcRun3_2024_realistic_v2`
- **Used for**: MC datasets in `MC_2024.json` (standard processing)
- **Note**: Uses the most recent GlobalTag for 2024 conditions.

### MC_2024.py (2024 alternate)

- **Era**: `Run3` (generic, not year-specific)
- **GlobalTag**: `140X_mcRun3_2024_realistic_v26`
- **Note**: An older variant using the generic `Run3` era instead of
  `Run3_2024`. Not used in the current `crabby.py` mapping.

## Data Configs by Year

### DATA_2022_NANO.py (2022 / 2022EE)

- **Era**: `Run3_2024`
- **GlobalTag**: `140X_dataRun3_v20`
- **Reprocessing tag**: `22Sep2023`
- **Used for**: Both `DATA_2022.json` and `DATA_2022EE.json`

### DATA_2023_NANO.py (2023 / 2023BPix)

- **Era**: `Run3_2024`
- **GlobalTag**: `140X_dataRun3_v20`
- **Reprocessing tag**: `22Sep2023` (with version variants)
- **Used for**: Both `DATA_2023.json` and `DATA_2023BPix.json`

### DATA_2024_NANO.py (2024)

- **Era**: `Run3_2024`
- **GlobalTag**: `140X_dataRun3_v20`
- **Reprocessing tags**: `2024CDEReprocessing` (Runs C-E), `PromptReco` (Runs F-J)
- **Used for**: `DATA_2024.json`

## Key Differences: MC vs Data Configs

| Aspect | MC | Data |
|---|---|---|
| `--mc` / `--data` flag | `--mc` | `--data` |
| Output module name | `NANOAODSIMoutput` | `NANOAODoutput` |
| Data tier | `NANOAODSIM` | `NANOAOD` |
| Event content | `NANOAODSIMEventContent` | `NANOAODEventContent` |
| Mixing module | Loaded (mixNoPU) | Not loaded |
| NanoAOD sequence | `nanoSequenceMC` | `nanoSequence` |
| Lumi mask (in CRAB) | None | Year-specific golden JSON |
| CRAB splitting | `Automatic` | `LumiBased` (50 lumis/job) |

## Key Differences: Standard vs Scouting

| Aspect | Standard | Scouting |
|---|---|---|
| NanoAOD step | `NANO:@BTV` | `NANO:@GENFromMini+@ScoutFromMini` |
| Jet source | PAT jets from MiniAOD | Reclustered from scouting PF candidates |
| Taggers | DeepJet, ParticleNet, RobustParT, offline UParT | HLT ParticleNet, scouting UParT |
| PV source | Offline PV from MiniAOD | Reconstructed from scouting tracks |
| Customizations | DAZSLE + BTV | Scouting + ScoutingTranslator |
| CMSSW requirement | Standard NanoAODv15 | CMSSW 16_0_1 + external packages |

## Related Files

- `/home/das214/HHtobbtautau/Run3_nano_submission/configs/MC_2024_NANO.py`
- `/home/das214/HHtobbtautau/Run3_nano_submission/configs/DATA_2024_NANO.py`
- `/home/das214/HHtobbtautau/Run3_nano_submission/configs/MC_preEE2022_NANO.py`
- `/home/das214/HHtobbtautau/Run3_nano_submission/configs/MC_postEE2022_NANO.py`
- `/home/das214/HHtobbtautau/Run3_nano_submission/configs/MC_preBPix2023_NANO.py`
- `/home/das214/HHtobbtautau/Run3_nano_submission/configs/MC_postBPix2023_NANO.py`
- `/home/das214/HHtobbtautau/Run3_nano_submission/configs/DATA_2022_NANO.py`
- `/home/das214/HHtobbtautau/Run3_nano_submission/configs/DATA_2023_NANO.py`
