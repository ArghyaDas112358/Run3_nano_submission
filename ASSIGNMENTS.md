# CHS campaign submission assignments — NanoAODv17ScoutingCHS24

Claim a group: put your name + CERN username in the row, push (or message
Arghya). One `crabby.py` invocation per group — full commands in
[`RUNBOOK_CHS.md`](RUNBOOK_CHS.md).

Statuses: `open` → `claimed` → `testing` (1-unit self-test) → `submitted` →
`done` (all tasks finished + published). Note any wall-clock/INVALID wrinkles
in the Notes column.

**Stage-out site is per-submitter, not per-campaign.** Use a site where YOUR
grid identity has `/store/user` write access and set it in `.env`
(`STORAGE_SITE`) — see the DATA section for the live example. Files landing on
different T2s is expected and fine; discovery goes through DBS `phys03`, not
through a shared directory.

| group (`--dataset` key) | stems | ~scale | owner (CERN user) | status | notes |
|---|---:|---|---|---|---|
| `DYJetsNLO` | 5 | 3.4k jobs | Arghya (arghyara) | **done** | 57.6M evts published; 2,985 files / 557 GB on Purdue EOS; 40to100 EOS-only (INVALID parent); 1 wall-clock job → recovery task |
| `HHbbtt` (signal, full coupling scan) | 14 | small (each stem ~10⁶ evts, ~66% eff) | Arghya (arghyara) | **done** | full round 2026-07-22 + 2 recovery tasks 2026-07-24. `crab status` sweep 2026-08-09: **all 14 stem-tasks 100% finished AND 100% published** (recoveries plugged the 3 failed jobs: kl-1p00 ×2 exit-8028, c2-0p35 ×1 exit-50664). 14 `HHBBTT_CHSUParT` datasets in DAS phys03; 10 coupling points |
| `TT` | 3 | large (TTto4Q biggest) | Irene (CERN user TBD) | **claimed** | 1-unit self-test **already green 3/3** (2026-07-25, submitted by arghyara) → skip RUNBOOK §3, go straight to §4. Clear the test workArea first: `rm -rf crab/NanoAODv17ScoutingCHS24/mcscouting_2024_TT` |
| `WJetsLO` | 9 | large (1.83 B evts) | Arghya (arghyara) | **submitted** | **the analysis background** (W→lnu 4 + Wto2Q HT 5). Full round 2026-08-05, tasks `260805_2046`–`260805_2049`. Sweep 2026-08-09: **6/9 done + 100% published** (HT-100to400/800to1500/1500to2500/2500, WtoLNu-3J/4J — the `FileBased` override on 4J worked, 2723/2723); HT-400to800 running (51%), WtoLNu-2J running (81%); WtoLNu-1J 423/424 with 1 exit-8022 job resubmitted 2026-08-09. Auto-resubmit watchdog (2 h cycle, 3-resub cap) running on Purdue AF (Arghya) until all green |
| `QCD-4Jets_HT` | 11 | **largest group** | Arghya (arghyara) | **testing** | 1-unit self-test submitted 2026-08-09, **11/11 delivered**; acceptance readback (RUNBOOK §3 criteria 2-3) pending. Pre-screened all blocks via DAS: max block-lumis 45,857 (HT-70to100) — safely under the 100k SUBMITREFUSED limit, no `FileBased` override needed. Low-HT bins huge + low eff; full submission may still be split 40-400 / 400+ between two people |
| `Diboson` | 5 | small | — | open | no self-test yet |
| `ZJetsLO` | 5 | 0.80 B evts | — | **deferred** | Zto2Q — not used as a background per the seniors' decision; self-test green 5/5 (2026-07-25), submit only if that changes |

### Self-test round of 2026-07-25

TT / WJetsLO / ZJetsLO were self-tested campaign-wide by arghyara with
`--test True` (`totalUnits = 1`). Those task dirs live under the ordinary
`mcscouting_2024_<GROUP>/` work areas, **not** under `testround_*`, so they
look like full submissions in `ls` — they are not. The tell is
`totalUnits = 1` in the task's `crab.log`, and a single few-MB file on EOS.
Delete the work area before the full submit, as RUNBOOK §4 says.

## DATA — Run2024 HLTSCOUT (`--dataset ScoutingHLT`, card `cards/chs_data.yml`)

One row per era. `--dataset ScoutingHLT` submits ALL eras — if you take a
single era, run `--make` alone and `crab submit` only your era's config
(RUNBOOK §4b). File counts from DAS 2026-07-21.

**Coordinate before claiming**: one era, one submitter. Say which era you are
taking in the channel before you submit.

| era | files | owner (CERN user) | stage-out | status | notes |
|---|---:|---|---|---|---|
| Run2024C | 21,692 | — | — | open | old campaign processed this era on the v16 recipe |
| Run2024D | 21,624 | Marc Huwiler (mhuwiler) | **T2_US_UCSD** | **submitted** | full era submitted 2026-08-05, task `260805_181416:mhuwiler_crab_ScoutingPFRun3_Run2024D-v1_HLTSCOUT` |
| Run2024E | 31,335 | — | — | open | |
| Run2024F | 70,447 | — | — | open | biggest single era |
| Run2024G | 95,424 | — | — | open | consider two submitters / split by run range |
| Run2024H | 13,795 | — | — | open | |
| Run2024I | 28,250 | — | — | open | |

Eras A/B (commissioning) + J (1 file) are deliberately excluded — the Golden
JSON mask removes them anyway.

### Why Run2024D stages out to UCSD

Marc has no `/store/user` write permission at T2_US_Purdue, so the data round
goes to UCSD (`/ceph/cms/store/user/mhuwiler/...`). That is the preferred
outcome anyway — the data is the bulk of the campaign and this keeps it off
the Purdue T2 quota. A Purdue write-permission request for external submitters
is still worth making (Stefan is aware of the campaign), but it is **not** a
blocker for this round.

### Run2024D test-file validation (2026-08-05)

One test file was checked before the full submission and passed on every axis
that has bitten this campaign before:

- **schema**: `ScoutingPFJetReclusterCHS` + the 6-class `scoutUParT`
  (`probb/c/g/uds/taup/taum`, no `problepb`) — matches `SCOUTING_JET_ERA=chs`
- **baked preselection ran**: `min(nJets) = 3`, and the smallest per-event
  `max(BvsAll)` is `0.6500` — exactly the cut boundary
- **tagger guard behaves as in MC**: 2.38% of jets carry the −1 sentinel, and
  guard ⟺ (pT ≤ 15 or |η| ≥ 2.5) for 99.996% of jets; denominator −6, BvsAll
  = 1/6 on guarded jets
- **golden**: run 380534, LS 535, inside the certified range `[1, 746]`
- the analysis define chain runs on it end to end (101 columns)

Reference: 18,846 events, 105,543,255 bytes, one lumisection.

**Not in this round:** `DYJetsLO` (GT mismatch: Winter24/133X parents vs the
150X pset — deliberately excluded), everything else in `datasets/MC_2024.json`
(SingleTop / single-H / HH4b / QCD_PT / EWKV — add only on group request).

## Campaign size

MC: ~46 stems ≈ 26 TB (675 GB of it produced so far — DY + signal).

DATA: measured, not guessed — the Run2024D test file is **100.7 MB per
lumisection** after the baked preselection. Against the golden JSON that is
**≈ 2.2 TB for Run2024D** (23,209 golden LS) and **≈ 28 TB for all of 2024**
(287,603 golden LS). Per-LS yield scales with instantaneous lumi, so treat
these as ±50%, and note this sits below the ~60 TB working figure used in the
2026-08-05 discussion — worth re-checking once Run2024D completes and a real
era total is on disk.
