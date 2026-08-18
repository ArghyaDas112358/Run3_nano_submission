# CHS campaign runbook — NanoAODv17ScoutingCHS24

Submitting scouting-NanoAOD production for HH→bbττ on the new CHS recipe
(CMSSW_16_1_0_pre4 + `JanFSchulte:derivedScouting` + the HHbbtt preselection
psets). This page is everything a submitter needs — target time to first
submission: **~30 min, most of it the CMSSW build**.

The DY bins are already produced and published (57.6M events, campaign
validated end-to-end). You are submitting more groups of the same campaign.

## 0. What you need

- A CMS grid certificate in `~/.globus` (usercert.pem + userkey.pem) and VO CMS
  membership. Any CMS site works — **you do NOT need a Purdue account**.
- An lxplus-like el8/el9 machine with cvmfs (lxplus itself is fine).
- Your CERN username registered in [`ASSIGNMENTS.md`](ASSIGNMENTS.md) next to
  the group(s) you're taking.

## 1. One-time setup (~25 min)

```bash
git clone -b NanoAODv17_CHS https://github.com/ArghyaRanjanDas/Run3_nano_submission
cd Run3_nano_submission

./setup.sh                                # builds CMSSW_16_1_0_pre4 + recipe + psets
                                          # el8 AND el9 hosts, no container, no GitHub fork touched

cp .env.example .env                      # then edit:
#   CERN_USER      = your CERN/grid username
#   CMSSW_AREA     = printed by setup.sh at the end
#   STORAGE_SITE   = a site where YOUR identity has /store/user
#                    (your institute T2/T3; Purdue mapping for externals is
#                     being requested — until then use your own site)

crab createmyproxy --days 30              # one-time per month, asks your grid-cert passphrase
```

## 2. Every session

```bash
cd Run3_nano_submission
set -a; source .env; set +a
source /cvmfs/cms.cern.ch/cmsset_default.sh
cd cmssw/$CMSSW_VERSION/src && cmsenv && cd ../../..
source /cvmfs/cms.cern.ch/common/crab-setup.sh
voms-proxy-init --voms cms --valid 168:00
```

## 3. Claim a group, run the self-test (1-unit)

Pick an unclaimed group in [`ASSIGNMENTS.md`](ASSIGNMENTS.md), put your name in,
push (or tell Arghya). Then:

```bash
python3 crabby.py --year 2024 --dataset <GROUP> --scouting --make --submit \
    --test True --card cards/chs_mc.yml \
    --campaign NanoAODv17ScoutingCHS24 --user $CERN_USER
```

`<GROUP>` is the ASSIGNMENTS.md key, e.g. `TT`, `QCD-4Jets_HT`, `HHbbtt`,
`VJetsLO`, `Diboson`.

**Self-test pass criteria** (~1–2 h after submission):
1. every task printed `Success: Your task has been delivered…`;
2. `crab status` reaches `SUBMITTED` / jobs running for **every** task;
3. one output file lands under your
   `/store/user/$CERN_USER/production/Scouting/NanoAODv17ScoutingCHS24/…`
   **for every stem** — count the stems, not the tasks.

> **"Delivered" is not "accepted".** The CRAB server can print
> `Success: Your task has been delivered` and then have the TaskWorker
> **refuse** the task. `crab.log` stays clean; the only symptom is a stem that
> never produces a file. This is why criteria 2 and 3 exist — a self-test you
> submit but never read back is not a test. `WtoLNu-4Jets_Bin-4J` sat refused
> for eleven days exactly this way (2026-07-25 → 2026-08-05).
>
> The usual cause is `SUBMITREFUSED` with *"Block … contains more than 100000
> lumis"*. Fix it with a `splitting_overrides` entry in your card
> (`FileBased`, `unitsPerJob: 1`) — see `cards/chs_mc.yml` for the live
> example — then resubmit that stem.

Read every task back in one command:

```bash
for d in crab/NanoAODv17ScoutingCHS24/mcscouting_2024_<GROUP>/crab_*/; do
  printf '%-52s ' "$(basename "$d" | cut -c6-57)"
  crab status -d "$d" 2>/dev/null | grep -m1 -E 'Status on the CRAB server' || echo '<no status>'
done
```

The physics content is already validated campaign-wide — your self-test only
proves *your* proxy/stageout works, and that CRAB accepted every stem.

## 4. Full submission

```bash
rm -rf crab/NanoAODv17ScoutingCHS24/mcscouting_2024_<GROUP>   # clear the test workArea
python3 crabby.py --year 2024 --dataset <GROUP> --scouting --make --submit \
    --card cards/chs_mc.yml --campaign NanoAODv17ScoutingCHS24 --user $CERN_USER
```

Then mark the group `submitted` in ASSIGNMENTS.md. Publication is automatic
(phys03). Check progress any time with `crab status -d <workdir>`.

## 4b. DATA submissions (Run2024 HLTSCOUT)

Same machinery, three differences — a different card, per-era claims, and
scale. The DATA pset (`scoutingnano_data_hhbbtt.py`) has no gen block, keeps
the FED-based L1 unpacking, and applies the same baked preselection (measured
data efficiency ~11%). crabby automatically switches to **LumiBased splitting
+ the 2024 Golden JSON lumi mask** for data.

```bash
# self-test (one unit):
python3 crabby.py --year 2024 --dataset ScoutingHLT --scouting --make --submit \
    --test True --card cards/chs_data.yml \
    --campaign NanoAODv17ScoutingCHS24 --user $CERN_USER

# full era set (all 7 eras C-I in one go — check ASSIGNMENTS.md first!):
rm -rf crab/NanoAODv17ScoutingCHS24/datascouting_2024_ScoutingHLT
python3 crabby.py --year 2024 --dataset ScoutingHLT --scouting --make --submit \
    --card cards/chs_data.yml --campaign NanoAODv17ScoutingCHS24 --user $CERN_USER
```

**Single-era claims (the normal case):** each era has its own dataset key —
`--dataset ScoutingHLT_Run2024D` submits era D alone. `--dataset ScoutingHLT`
submits **all seven eras at once** (C–I, ~280k files — era G alone is 95k),
so only use it if you claimed the whole data leg. Eras A/B/J are excluded
(commissioning / 1 file; the Golden mask removes them anyway).

⚠ The `--card cards/chs_data.yml` flag is REQUIRED for data — there is no
in-repo fallback config; without the card crabby stops with a clear error.

## 5. Known gotchas (read once — they will save you a resubmission)

| symptom | cause / fix |
|---|---|
| `workArea already exists (y/n)` prompt | old test dirs — delete them first (step 4); never run crabby in a non-interactive shell with a leftover workArea |
| task stuck NEW → `SUBMITFAILED`, >100k lumis | Automatic-splitting refusal — edit the generated `submit_*.py`: `splitting="FileBased"`, `unitsPerJob=1`, `crab submit` it directly |
| a job fails with exit **50664** and "Not retrying (wall clock)" | `crab resubmit` will NOT work for these — flag it in ASSIGNMENTS.md; the fix is a lumi-masked recovery task (`crab report` → `notFinishedLumis.json`; ops/submit_ptll200_recovery1.py is a worked example) |
| `crab getlog` fails with a lowercased path | client bug — fetch logs directly from your site's EOS: `<task webdir>/…/log/cmsRun_*.log.tar.gz` |
| input dataset warned `INVALID` at submit | CRAB runs on the valid files but **auto-disables publication** for that task — note it in ASSIGNMENTS.md (the DY 40to100 bin hit this) |
| parent MiniAOD not hosted anywhere near your site | fine — jobs read via AAA (xrootd); nothing to do |

Grab one job log per task **early** (`crab getlog` or webdir) — the schedd
purges task info after ~40 days.

## 6. Where outputs end up + aggregation

Each submitter's outputs stage to **their own** `/store/user/<user>/production/
Scouting/NanoAODv17ScoutingCHS24/` at their `STORAGE_SITE`, and publish to
phys03 as `/<primary>/<user>-…HHBBTT_CHSUParT…/USER`.

Discovery across all submitters (this is why the tag matters):

```
dataset=/*/*HHBBTT_CHSUParT*/USER instance=prod/phys03
```

Aggregation to Purdue (for the analysis cache) is handled centrally by Arghya
via the published file lists — you don't need to move anything.

## 7. Reference

- Production pset: `ScoutingNanoProduction/scoutingnano_mc_hhbbtt.py`
  (fork `ArghyaRanjanDas/ScoutingNanoProduction`, branch `hhbbtt-chs-integration`).
  Baked preselection: 5-DST trigger OR + loosev2 kinematics (3 jets
  20/20/10 GeV, |η|<2.5, 4th-object OR) + max-BvsAll > 0.65 on the 6-class
  CHS scoutUParT scores. `genEventSumw` counts ALL events (filter-safe norm).
- Branch whitelist + rationale: `scouting_HHbbtautau/output/crab_branch_whitelist_v3.md`
- DY campaign record (worked example incl. recovery): ops/ dir in the
  campaign workArea + `scouting_HHbbtautau/output/dy_launch_comms.md`
