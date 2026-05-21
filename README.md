# Run3 Scouting NanoAOD Submission Harness

[![Codestyle](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

CMS scouting NanoAOD production for HH→bbττ. Submits CRAB jobs that read MiniAOD (or `ScoutingPFRun3` ScoutNano) and write reclustered scouting AK4/AK8 jets with UParT + HLT ParticleNet tagger scores.

- **Upstream:** [`github.com/ArghyaRanjanDas/Run3_nano_submission`](https://github.com/ArghyaRanjanDas/Run3_nano_submission)
- **Site branches:** `NanoAODv15_151_Scouting_PAF` (Purdue AF), `NanoAODv15_151_Scouting_FNAL`, `NanoAODv15_151_Scouting`
- **Per-user config:** `.env` (gitignored); template in `.env.example`
- **Full workflow:** see [`CLAUDE.md`](CLAUDE.md) — first-time setup, every-session shell, `crabby.py` reference, monitoring, and safety rules

## Quick start

```bash
git clone https://github.com/ArghyaRanjanDas/Run3_nano_submission
cd Run3_nano_submission
git checkout NanoAODv15_151_Scouting_PAF       # or _FNAL / _Scouting

cp .env.example .env                            # then edit PURDUE_USER / CERN_USER / FNAL_USER / CMSSW_AREA / STORAGE_SITE
./setup.sh                                      # one-time CMSSW build (~10–20 min)

set -a; source .env; set +a
voms-proxy-init --voms cms --valid 168:00       # ~7-day grid proxy

python3 crabby.py --year 2024 --dataset HHbbtt --scouting --make --submit --test True
```

The two-phase `--make` / `--submit` pattern and the full flag reference live in [`CLAUDE.md`](CLAUDE.md).

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
