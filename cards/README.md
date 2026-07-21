# Site cards

Per-site overrides for `crabby.py`.  Pass with `--card cards/<site>.yaml`.

```bash
python3 crabby.py --year 2024 --dataset HHbbtt --scouting \
                  --card cards/cern.yaml --make --submit --test True
```

## How card overrides work

`crabby.py` builds a defaults dict from `--year` / `--dataset` / `--user`
/ `--campaign` / `$STORAGE_SITE`, then merges the YAML card on top via
shallow `dict-union` (defaults `|` card).  Any key the card sets wins.

The full schema crabby expects (every key is optional in a card):

| Key | Default | When to override |
|---|---|---|
| `name` | `<dlabel>_<year>_<dataset>` | Almost never |
| `crab_template` | `template_crab.py` | Custom CRAB skeleton |
| `workArea` | `crab/<TAG>/<dlabel>_<year>_<dataset>` | Custom output dir |
| `storageSite` | `$STORAGE_SITE` or `T2_US_Purdue` | **Yes — per site** |
| `outLFNDirBase` | `/store/user/<user>/production/Scouting/<TAG>/<dlabel>_<year>` | **Yes — per site, if your T2 uses a non-standard LFN base** |
| `voGroup` | `null` | Set to a VO group (e.g. `dazsle`) if your role demands it |
| `publication` | `True` (overridden to `False` by `--test True`) | Rarely |
| `config` | `configs/<CONFIGS[dlabel][year]>` | Custom cmsRun pset |
| `tag_extension` | `DAZSLE_PFNano` | Output-dataset tag suffix |
| `tag_mod` | `null` | In-place tag rename (mutually exclusive with `tag_extension`) |
| `data` | derived from `--dataset in DATASETS` | Don't override |
| `lumiMask` | `jsons/<JSONS[year]>` for data, `null` for MC | Custom Golden JSON |
| `datasets` | dict from `MC_<year>.json[--dataset]` | Don't override — crabby iterates this dict's values |

**Critical:** do NOT set `datasets:` in a card.  `crabby.py:319`
expects it to be a `dict` (from `MC_<year>.json`) and iterates
`.items()`; a YAML list / multiline-string overrides will break.

## Placeholder substitution

The cards committed here use literal placeholders like `<your-CERN-user>`.
You can either:

1. Edit the card in place with your username (do **not** commit).
2. Wrap the invocation in a shell snippet that templates the card.
3. Pass `--user "$CERN_USER"` and rely on `outLFNDirBase` derivation
   from the default — only override `storageSite` in the card.

The third option is cleanest for collaborators and is what these cards
ship with.
