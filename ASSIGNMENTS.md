# CHS campaign submission assignments — NanoAODv17ScoutingCHS24

Claim a group: put your name + CERN username in the row, push (or message
Arghya). One `crabby.py` invocation per group — full commands in
[`RUNBOOK_CHS.md`](RUNBOOK_CHS.md).

Statuses: `open` → `claimed` → `testing` (1-unit self-test) → `submitted` →
`done` (all tasks finished + published). Note any wall-clock/INVALID wrinkles
in the Notes column.

| group (`--dataset` key) | stems | ~scale | owner (CERN user) | status | notes |
|---|---:|---|---|---|---|
| `DYJetsNLO` | 5 | 3.4k jobs | Arghya (arghyara) | **done** | 57.6M evts published; 40to100 EOS-only (INVALID parent); 1 wall-clock job → recovery task |
| `HHbbtt` (signal, full coupling scan) | 14 | small (each stem ~10⁶ evts, ~66% eff) | Arghya (arghyara) | **submitted** | full round 2026-07-22 (test 98/98 green, eff 52-74% per point) |
| `TT` | 3 | large (TTto4Q biggest) | — | open | |
| `QCD-4Jets_HT` | 11 | **largest group** | — | open | low-HT bins huge + low eff; consider splitting 40-400 / 400+ between two people |
| `WJetsLO` | 9 | large (1.88 B evts) | — | open | **the analysis background** (W→lnu 4 + Wto2Q HT 5). Split out of VJetsLO 2026-07-25 |
| `ZJetsLO` | 5 | 0.80 B evts | — | **deferred** | Zto2Q — not used as a background per the seniors' decision; test-round-validated, submit only if that changes |
| `Diboson` | 5 | small | — | open | |

## DATA — Run2024 HLTSCOUT (`--dataset ScoutingHLT`, card `cards/chs_data.yml`)

One row per era. `--dataset ScoutingHLT` submits ALL eras — if you take a
single era, run `--make` alone and `crab submit` only your era's config
(RUNBOOK §4b). File counts from DAS 2026-07-21.

| era | files | owner (CERN user) | status | notes |
|---|---:|---|---|---|
| Run2024C | 21,692 | — | open | old campaign processed this era on the v16 recipe |
| Run2024D | 21,624 | — | open | |
| Run2024E | 31,335 | — | open | |
| Run2024F | 70,447 | — | open | biggest single era |
| Run2024G | 95,424 | — | open | consider two submitters / split by run range |
| Run2024H | 13,795 | — | open | |
| Run2024I | 28,250 | — | open | |

Eras A/B (commissioning) + J (1 file) are deliberately excluded — the Golden
JSON mask removes them anyway.

**Not in this round:** `DYJetsLO` (GT mismatch: Winter24/133X parents vs the
150X pset — deliberately excluded), everything else in `datasets/MC_2024.json`
(SingleTop / single-H / HH4b / QCD_PT / EWKV — add only on group request).

Campaign totals when complete: ~46 MC stems ≈26 TB + Run2024 data ≈10 TB
(at 10 fb⁻¹) → ≈36 TB on EOS — within the approved budget.
