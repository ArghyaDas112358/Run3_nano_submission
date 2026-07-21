# Run3 Scouting NanoAOD Submission Harness

[![Codestyle](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

CMS scouting NanoAOD production for HH→bbττ. Submits CRAB jobs that read MiniAOD (or `ScoutingPFRun3` ScoutNano) and write reclustered scouting AK4/AK8 jets with UParT + HLT ParticleNet tagger scores.

- **Upstream:** [`github.com/ArghyaRanjanDas/Run3_nano_submission`](https://github.com/ArghyaRanjanDas/Run3_nano_submission)
- **Active campaign:** branch `NanoAODv17_CHS` → campaign `NanoAODv17ScoutingCHS24` (CHS jets + 6-class scouting UParT + baked HHbbtt preselection). **Submitters: start at [`RUNBOOK_CHS.md`](RUNBOOK_CHS.md)**; claim your group in [`ASSIGNMENTS.md`](ASSIGNMENTS.md). Legacy v15 site branches remain as history.
- **Per-user config:** `.env` (gitignored); template in `.env.example`
- **Full workflow:** see [`CLAUDE.md`](CLAUDE.md) — first-time setup, every-session shell, `crabby.py` reference, monitoring, and safety rules

## Quick start

```bash
git clone https://github.com/ArghyaRanjanDas/Run3_nano_submission
cd Run3_nano_submission
git checkout NanoAODv17_CHS                    # the active CHS campaign branch

cp .env.example .env                            # then edit PURDUE_USER / CERN_USER / FNAL_USER / CMSSW_AREA / STORAGE_SITE
./setup.sh                                      # one-time CMSSW build (~10–20 min)

# Every-session setup (see CLAUDE.md "Every-session setup" for the full recipe)
set -a; source .env; set +a
cd "${CMSSW_AREA}/src"
source /cvmfs/cms.cern.ch/cmsset_default.sh
cmsenv
source /cvmfs/cms.cern.ch/common/crab-setup.sh
cd -
voms-proxy-init --voms cms --valid 168:00       # ~7-day grid proxy

# Smoke test (one-shot --test True is safe — does not publish)
python3 crabby.py --year 2024 --dataset HHbbtt --scouting --make --submit --test True
```

For real production submissions use the **two-phase `--make` → inspect → `--submit`** workflow described in [`CLAUDE.md`](CLAUDE.md). The full flag reference, monitoring recipes, and safety rules live there.

## Tests

```bash
pytest tests/
```

No CMSSW required — `tests/conftest.py` stubs `CRABAPI`. 1.6k LOC pytest suite covering `crabby.py`, `crab_status.py`, dataset catalogs, and the CRAB template.

## Documentation

- [`CLAUDE.md`](CLAUDE.md) — operator workflow, every-session shell, safety rules
- [`des/`](des/) — design docs: architecture, data flow, tagger map, CMSSW integration, dataset catalogs, CRAB workflow, NanoAOD output schema
- [`.env.example`](.env.example) — variables every user must set

## Access

Closed for now (CMS-internal). Reach out via the upstream repo for access requests.
