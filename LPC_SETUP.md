# Submitting from cmslpc — quickstart (for external submitters)

Written 2026-08-17 for external submitters (e.g. while a Purdue account/mapping is
pending); applies to anyone submitting this campaign from LPC. Distilled from the Purdue production experience
(three campaigns); ask the campaign maintainer for details.

## One-time setup (~25 min, mostly compilation)

```bash
ssh <you>@cmslpc-el9.fnal.gov
cd ~/nobackup      # NOT your home dir - home has a 3 GB quota
git clone -b NanoAODv17_CHS https://github.com/ArghyaRanjanDas/Run3_nano_submission
cd Run3_nano_submission
./lpc_bootstrap.sh    # handles the el8 container, CMSSW build, and your .env
crab createmyproxy --days 30
```

Notes:
- The bootstrap enters the el8 container itself. If you ever need it manually, the
  stock `cmssw-el8` wrapper does NOT mount `/uscms_data` — use:
  `apptainer -s exec -B /cvmfs -B /uscms_data /cvmfs/unpacked.cern.ch/registry.hub.docker.com/cmssw/el8:x86_64 bash`
- `.env`: your own `CERN_USER`/`FNAL_USER`; `STORAGE_SITE=T3_US_FNALLPC` until your
  Purdue `/store/user` mapping exists (outputs get replicated to Purdue later —
  the analysis only needs a path, not a site).
- Everything the pset needs (custom NanoAOD cffs, PatFromScouting, the ONNX taggers,
  HHbbttPreselFilter) is assembled by `setup.sh` from public frozen branches — do not
  use JanFSchulte:derivedScouting directly, it has diverged.

## Every session

```bash
apptainer -s exec -B /cvmfs -B /uscms_data /cvmfs/unpacked.cern.ch/registry.hub.docker.com/cmssw/el8:x86_64 bash
cd ~/nobackup/Run3_nano_submission
set -a; source .env; set +a
source /cvmfs/cms.cern.ch/cmsset_default.sh
cd cmssw/$CMSSW_VERSION/src && cmsenv && cd ../../..
source /cvmfs/cms.cern.ch/common/crab-setup.sh    # AFTER cmsenv - order matters
voms-proxy-init --voms cms --valid 168:00
```

## Submitting (TT example)

```bash
# ALWAYS self-test first (1 unit per dataset):
python3 crabby.py --year 2024 --dataset TT --scouting --make --submit --test \
    --card cards/chs_mc.yml --campaign NanoAODv17ScoutingCHS24 --user <your-fnal-user>
# self-test passes only if: crab status reaches SUBMITTED *and* one file lands per stem.
# "task delivered" alone means nothing (see gotchas).

# before the full round: archive the test workArea:
mv crab/NanoAODv17ScoutingCHS24/mcscouting_2024_TT testround_TT_$(date +%Y%m%d)
# then the same command without --test
```

## Gotchas that have each cost real days

1. **"Delivered" ≠ accepted.** A task can be silently `SUBMITREFUSED` server-side with
   a clean crab.log. Watch `crab status` + files landing. (WtoLNu-4J sat dead 11 days.)
2. **Screen input blocks before a full round**: any block with >100k lumis gets refused.
   `dasgoclient -query "block dataset=..."` then the DBS `filesummaries` endpoint per
   block; anything over 100,000 lumis needs a `splitting_overrides` entry
   (FileBased, unitsPerJob: 1) in `cards/chs_mc.yml` (live example: WtoLNu-4J).
   TT has NOT been screened yet.
3. **`ModuleNotFoundError: 'past'`** = a conda/pixi python is shadowing cmsenv. Fresh
   shell, follow the session order above.
4. **Automatic-splitting pathologies**: jobs frozen as `rescheduled`, or probe jobs
   that stall forever → `crab kill` + resubmit that dataset FileBased/unitsPerJob=1.
   Plain `stageout` failures → just `crab resubmit`.
5. **Recovery of partially-failed tasks**: `crab report` → `notFinishedLumis.json` →
   new task with that lumiMask + FileBased + the SAME outputDatasetTag (worked
   precedents in `crab/NanoAODv17ScoutingCHS24/ops/submit_*_recovery*.py`).
6. **Exit 8022 from every replica** = corrupt source file; no retry helps.
7. Publication goes to phys03 under YOUR DBS name with your pset-hash — expected;
   the analysis maintainers repoint `samples.yaml` at your dataset names when they land.
8. Put your name on the dataset row in `ASSIGNMENTS.md` (or tell the campaign maintainer).
