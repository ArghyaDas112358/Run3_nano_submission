"""
Invariants over `datasets/{MC,DATA,Scouting_DATA}_*.json`.

These tests don't import crabby's runtime behaviour; they just lock down the
shape of the JSON catalogs that `crabby.py` blindly trusts. A regression in
catalog shape (e.g. someone wraps a DAS path in extra slashes, drops a
required category, or commits a malformed JSON) would slip past code review
because crabby fails *late*, deep inside CRAB submission.
"""

from __future__ import annotations

import importlib
import json
import re
from pathlib import Path

import pytest


# Reuse the stub set up in conftest.py.
crabby = importlib.import_module("crabby")


# ---- Discovery ---------------------------------------------------------------
def _all_catalog_files(datasets_dir: Path) -> list[Path]:
    """All JSON catalogs that crabby actually reads."""
    out: list[Path] = []
    for pat in ("MC_*.json", "DATA_*.json", "Scouting_DATA*.json"):
        out.extend(sorted(datasets_dir.glob(pat)))
    # Skip the "additions" file -- it's an out-of-band patch, not the main catalog.
    return [p for p in out if "additions" not in p.name]


def pytest_generate_tests(metafunc):
    # Parametrize anything that takes `catalog_path`.
    if "catalog_path" in metafunc.fixturenames:
        datasets_dir = Path(__file__).resolve().parent.parent / "datasets"
        paths = _all_catalog_files(datasets_dir)
        metafunc.parametrize(
            "catalog_path", paths, ids=[p.name for p in paths]
        )


# ---- DAS path regex ----------------------------------------------------------
# Three slash-separated fields after the leading slash, none empty, no extra
# slashes. e.g. /Foo/Bar/MINIAODSIM, /JetMET0/Run2024C-..-v1/NANOAOD.
DAS_PATH_RE = re.compile(r"^/[^/]+/[^/]+/[^/]+$")


def _iter_leaf_values(obj):
    """Yield every leaf string in a nested dict (depth 1 or 2)."""
    if isinstance(obj, dict):
        for v in obj.values():
            yield from _iter_leaf_values(v)
    elif isinstance(obj, str):
        yield obj
    # silently ignore lists/other -- catalogs aren't supposed to have them


def _shape(catalog_path: Path) -> str:
    """Catalog files come in two shapes:
       - 'flat': {category: {sample_name: das_path}}   <-- MC_*, DATA_*
       - 'by_year': {year: {run_name: das_path}}       <-- Scouting_DATA.json
    Both have leaf-level DAS paths, so most tests don't care, but a few do.
    """
    if catalog_path.name.startswith("Scouting_DATA"):
        return "by_year"
    return "flat"


# =============================================================================
# 1. Parses as JSON
# =============================================================================
class TestParses:
    def test_json_loads(self, catalog_path: Path) -> None:
        with catalog_path.open() as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                pytest.fail(f"{catalog_path.name} is not valid JSON: {e}")
        assert isinstance(data, dict), f"{catalog_path.name} top-level must be a dict"


# =============================================================================
# 2. Top-level keys non-empty, values are dicts
# =============================================================================
class TestTopLevelShape:
    def test_top_level_nonempty(self, catalog_path: Path) -> None:
        data = json.loads(catalog_path.read_text())
        assert len(data) > 0, f"{catalog_path.name} has no top-level entries"

    def test_values_are_dicts(self, catalog_path: Path) -> None:
        data = json.loads(catalog_path.read_text())
        non_dict = {k: type(v).__name__ for k, v in data.items() if not isinstance(v, dict)}
        assert not non_dict, (
            f"{catalog_path.name}: top-level values must all be dicts, got {non_dict}"
        )


# =============================================================================
# 3. DAS path shape
# =============================================================================
class TestDasPathShape:
    def test_all_leaf_values_well_formed(self, catalog_path: Path) -> None:
        data = json.loads(catalog_path.read_text())
        bad: list[tuple[str, str]] = []
        for v in _iter_leaf_values(data):
            if v.startswith("#"):
                continue  # commented out, ignored by crabby
            if len(v) < 10:
                continue  # sentinel for "disabled", crabby filter drops these
            if not DAS_PATH_RE.match(v):
                bad.append((catalog_path.name, v))
        assert not bad, (
            f"Malformed DAS paths in {catalog_path.name}:\n"
            + "\n".join(f"  {v}" for _, v in bad)
        )


# =============================================================================
# 4. 2024 MC must contain the categories crabby/CLAUDE.md call out
# =============================================================================
REQUIRED_2024_MC_KEYS = ("HHbbtt", "HH4b", "TT", "DYJetsNLO")


def test_mc_2024_has_required_categories(datasets_dir: Path) -> None:
    p = datasets_dir / "MC_2024.json"
    if not p.exists():
        pytest.skip("MC_2024.json not present")
    data = json.loads(p.read_text())
    missing = [k for k in REQUIRED_2024_MC_KEYS if k not in data]
    assert not missing, f"MC_2024.json missing required keys: {missing}"


# =============================================================================
# 5. MC catalogs must not have category names that collide with the data DATASETS list
# =============================================================================
def test_mc_catalogs_do_not_collide_with_data_keys(datasets_dir: Path) -> None:
    """
    In crabby.main(), `isData = args.dataset in DATASETS` decides which JSON
    file to read. If an MC JSON had e.g. a "JetMET" key, calling
    `--dataset JetMET` from the MC side would silently route to DATA -- a
    confusing footgun. Lock that down here.
    """
    data_keys = set(crabby.DATASETS)
    offenders: list[str] = []
    for mc_path in sorted(datasets_dir.glob("MC_*.json")):
        if "additions" in mc_path.name:
            continue
        mc = json.loads(mc_path.read_text())
        clash = data_keys & set(mc.keys())
        if clash:
            offenders.append(f"{mc_path.name}: {sorted(clash)}")
    assert not offenders, (
        "MC catalogs share category names with crabby.DATASETS (would mis-route "
        "from data to MC or vice versa):\n  " + "\n  ".join(offenders)
    )


# =============================================================================
# 6. The crabby filter (`len(v) > 10 and not v.startswith('#')`) leaves at
#    least one usable sample per file
# =============================================================================
class TestCrabbyFilterIsNonEmpty:
    def test_at_least_one_category_has_usable_samples(self, catalog_path: Path) -> None:
        """The exact filter from crabby.py line 319."""
        data = json.loads(catalog_path.read_text())
        shape = _shape(catalog_path)

        # In both flat and by_year shapes, the second-level dict has values
        # that are DAS paths. Apply crabby's filter to each second-level dict
        # and verify at least one second-level group has at least one item left.
        any_nonempty = False
        empty_groups: list[str] = []
        for cat, samples in data.items():
            if not isinstance(samples, dict):
                continue
            usable = [
                v
                for v in samples.values()
                if isinstance(v, str) and len(v) > 10 and not v.startswith("#")
            ]
            if usable:
                any_nonempty = True
            else:
                empty_groups.append(cat)

        assert any_nonempty, (
            f"{catalog_path.name}: every top-level group is empty after the "
            f"crabby filter. Empty groups: {empty_groups}"
        )


# =============================================================================
# 7. DATA catalogs use crabby.DATASETS keys (sanity / detection of typos)
# =============================================================================
def test_data_catalogs_keys_subset_of_DATASETS(datasets_dir: Path) -> None:
    """
    Every top-level key in DATA_*.json (except Scouting_DATA, which is
    year-keyed) should be one of crabby.DATASETS, otherwise no `--dataset`
    invocation can reach it. Flag any rogue keys.
    """
    allowed = set(crabby.DATASETS)
    offenders: list[str] = []
    for data_path in sorted(datasets_dir.glob("DATA_*.json")):
        d = json.loads(data_path.read_text())
        rogue = set(d.keys()) - allowed
        if rogue:
            offenders.append(f"{data_path.name}: unreachable keys {sorted(rogue)}")
    # If this test fails, either crabby.DATASETS is stale or the JSON has a typo.
    assert not offenders, "\n".join(offenders)


# =============================================================================
# 8. Scouting_DATA.json sanity: outer keys are year strings crabby supports
# =============================================================================
def test_scouting_data_outer_keys_are_year_like(datasets_dir: Path) -> None:
    p = datasets_dir / "Scouting_DATA.json"
    if not p.exists():
        pytest.skip("Scouting_DATA.json not present")
    data = json.loads(p.read_text())
    # Year strings: 4 digits, optionally followed by "EE" or "BPix"
    for k in data.keys():
        assert re.fullmatch(r"20\d{2}(EE|BPix)?", k), (
            f"Scouting_DATA.json outer key {k!r} doesn't look like a year"
        )
