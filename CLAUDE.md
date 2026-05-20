# Run3 Scouting NanoAOD submission harness

CMS scouting NanoAOD production for HH→bbττ. Submits CRAB jobs that read MiniAOD (or `ScoutingPFRun3` ScoutNano) and write reclustered scouting AK4/AK8 jets with UParT + HLT ParticleNet tagger scores.

- **Upstream remote:** `github.com/ArghyaRanjanDas/Run3_nano_submission`
- **Site branches:** `NanoAODv15_151_Scouting_PAF`, `NanoAODv15_151_Scouting_FNAL`, `NanoAODv15_151_Scouting`
- **Design docs:** `des/` — architecture, data flow, tagger map, dataset catalog, CRAB workflow

> **Never hardcode usernames or absolute home paths in any file in this repo.** Per-user values live in `.env` (gitignored). The committed template is `.env.example`.

---

## First-time setup (new collaborator)

1. **Clone and check out your site's branch:**
   ```bash
   git clone https://github.com/ArghyaRanjanDas/Run3_nano_submission
   cd Run3_nano_submission
   git checkout NanoAODv15_151_Scouting_PAF   # or _FNAL, or _Scouting
   ```

2. **Build CMSSW** (one-time, ~10–20 min):
   ```bash
   ./setup.sh
   ```
   Then install the scouting-specific externals — see `des/architecture/cmssw_integration.md`. Outline:
   ```bash
   cd cmssw/$CMSSW_VERSION/src
   git clone https://github.com/ArghyaRanjanDas/ScoutingTranslator PhysicsTools/ScoutingTranslator
   # Copy RecoBTag/{ONNXRuntime,FeatureTools} and UParT ONNX models per des/ doc
   scram b -j8
   cd -
   ```

3. **Configure your environment:**
   ```bash
   cp .env.example .env
   # edit .env: PURDUE_USER / FNAL_USER / CERN_USER / CMSSW_AREA / STORAGE_SITE
   ```

4. **Grid proxy** (~7 days, refresh as needed):
   ```bash
   voms-proxy-init --voms cms --valid 168:00
   ```

---

## Every-session setup

Run once per fresh shell before any `crabby.py` call:

```bash
set -a; source .env; set +a              # load PURDUE_USER, CMSSW_AREA, CAMPAIGN, ...
cd "${CMSSW_AREA}/src"
source /cvmfs/cms.cern.ch/cmsset_default.sh
cmsenv
source /cvmfs/cms.cern.ch/common/crab-setup.sh
cd -                                      # back to harness root
voms-proxy-info --timeleft                # must be > 0
```

**Gotcha:** `dbs3-client` (DAS queries via `datasets/get_*.py`) breaks AFTER `crab-setup.sh` is sourced. If you need to regenerate JSON catalogs, do it in a separate shell BEFORE setting up CRAB.

---

## `crabby.py` reference

```bash
python3 crabby.py --year <YEAR> --dataset <CATEGORY> \
                  [--scouting] [--make] [--submit] [--status] [--test True] \
                  [--user "$PURDUE_USER"] [--card cards/X.yaml] [--campain "$CAMPAIGN"]
```

| Flag | Meaning |
|---|---|
| `--year` | `2022`, `2022EE`, `2023`, `2023BPix`, `2024` (required) |
| `--dataset` | Category key from `datasets/<MC\|DATA>_<year>.json` (required) |
| `--scouting` | Use the scouting cmsRun config (`configs/MC_2024_Scouting.py` for 2024) |
| `--make` | Generate per-sample CRAB configs in `crab/<TAG>/<dlabel>_<year>_<dataset>/` |
| `--submit` | Submit configs created by `--make`. **Irreversible** — publishes to DBS `phys03`. |
| `--status` | Query CRAB status; writes `outputs_<card>.txt` |
| `--test True` | Dry run: 1 unit, publication off |
| `--user` | Grid username (default `$USER`; pass `"$PURDUE_USER"` for portability) |
| `--card` | YAML override (e.g. site-specific `storageSite`) |
| `--campain` | TAG used in `workArea` + LFN path |

### 2024 MC categories (`datasets/MC_2024.json`)
`HHbbtt`, `HH4b`, `HH2b2tau`, `TT`, `SingleTop`, `Hbb`, `Hcc`, `Htautau`, `DYJetsLO`, `DYJetsNLO`, `VJetsLO`, `VJetsNLO`, `Diboson`, `EWKV`, `VGamma`, `QCD-4Jets_HT`, `QCD_PT`.

### Data streams (`datasets/DATA_2024.json`)
`JetMET`, `EGamma`, `Muon`, `MuonEG`, `BTagMu`, `Tau`.

### Scouting data (`datasets/Scouting_DATA.json`)
`/ScoutingPFRun3/Run2024{C..J}-ScoutNano-v1/NANOAOD` for 2024.

### Canonical commands

```bash
# Dry-run a single subsample (one unit, no publication)
python3 crabby.py --year 2024 --dataset HHbbtt --scouting --make --submit --test True

# Full scouting MC production
python3 crabby.py --year 2024 --dataset HHbbtt --scouting --make --submit --user "$PURDUE_USER"
python3 crabby.py --year 2024 --dataset TT --scouting --make --submit --user "$PURDUE_USER"
python3 crabby.py --year 2024 --dataset DYJetsNLO --scouting --make --submit --user "$PURDUE_USER"

# Inspect configs before submitting (two-phase)
python3 crabby.py --year 2024 --dataset HHbbtt --scouting --make
ls crab/"$CAMPAIGN"/mcscouting_2024_HHbbtt/

# Non-Purdue users: override storageSite via --card
python3 crabby.py --year 2024 --dataset HHbbtt --scouting --card cards/fnal.yaml --make --submit
```

---

## Monitoring & resubmission

```bash
# Aggregate status → CrabStatus.csv
python3 crab_status.py --years 2024 --samples HHbbtt TT DYJetsNLO

# Or via crabby
python3 crabby.py --year 2024 --dataset HHbbtt --scouting --status

# Per-task CRAB commands
crab status   -d crab/<TAG>/<dlabel>_<year>_<dataset>/crab_<request>/
crab resubmit -d crab/.../crab_.../
crab resubmit -d ... --jobids 1,5,12
crab resubmit -d ... --maxmemory 8000          # memory-killed jobs
crab resubmit -d ... --maxjobruntime 3500      # timeouts
crab getlog   -d ... --jobids 1
```

Common failure modes: high-jet-mult memory blow-up, UParT inference timeouts, T2_US_Purdue stageout retries, invalid input datasets. See `des/submission/monitoring.md`.

---

## Output locations

EOS LFN: `/store/user/$PURDUE_USER/production/Scouting/$CAMPAIGN/<dlabel>_<year>/`
xrootd at Purdue: `root://eos.cms.rcac.purdue.edu/store/user/$PURDUE_USER/...`
Published datasets land in DBS `phys03` with tag `<original_tag>_DAZSLE_PFNano`.

---

## Key files

| File | Purpose |
|---|---|
| `crabby.py` | Submission entry point |
| `crab_status.py` | Multi-task monitor → `CrabStatus.csv` |
| `template_crab.py` | CRAB job template (5 GB / 4 cores / `phys03`) |
| `configs/MC_2024_Scouting.py` | Main cmsRun config (scouting MC) |
| `configs/{MC,DATA}_*.py` | Other year/stream configs |
| `customizations/customize.py` | Analysis-specific NanoAOD variables |
| `datasets/*.json` | Sample catalogs |
| `des/` | Full design documentation |
| `.env` | Personal config (gitignored) |
| `.env.example` | Template — copy to `.env` |
| `.claude/settings.json` | Shared Claude Code permission allowlist |

---

## Safety rules for Claude (the AI assistant)

When working in this repo via Claude Code:

- Run `--test True` first when in doubt about a new submission
- Always check `voms-proxy-info --timeleft > 0` before submission
- Two-phase submit: do `--make` alone first, inspect `crab/<TAG>/.../submit_*.py`, THEN `--submit`
- **Never run `python3 crabby.py ... --submit` without an explicit "yes, submit" from the user** — CRAB submission publishes to DBS `phys03` and cannot be unwound
- Never run `crab resubmit` / `crab kill` without explicit user confirmation
- Never re-run `setup.sh` unless the user explicitly asks (CMSSW rebuilds are expensive)
- Never modify `template_crab.py` placeholders (`_requestName_` etc.) — they're filled by `crabby.py`
- Never hardcode anyone's username or absolute home path in committed files — use `$PURDUE_USER` / `$CMSSW_AREA` from `.env`
- Never commit `.env` (already gitignored)

---

## See also

- `des/architecture/{overview,data_flow,cmssw_integration}.md`
- `des/submission/{overview,crabby,crab_template,monitoring}.md`
- `des/datasets/{overview,mc_samples,data_samples,scouting_data}.md`
- `des/nanoaod_output/{overview,jet_branches,scouting_collections,triggers,gen_collections}.md`
- `des/ml_taggers/{overview,upart_ak4,hlt_particlenet,glopart_ak8,onnx_inference}.md`
- `des/scouting_translator/{overview,translation_layer,ak4_reclustering,ak8_reclustering,vertices}.md`
- `des/configs/{overview,scouting_config,standard_configs,global_tags,customizations}.md`
