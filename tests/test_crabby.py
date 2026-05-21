"""
Adversarial tests for crabby.py.

Mocking note
------------
`crabby.py` does `from CRABAPI.RawCommand import crabCommand` at module top
level. That import requires a CMSSW environment with crab-setup.sh sourced --
which is not available outside the lxplus / Purdue CMS shell.

We work around this by stubbing `sys.modules['CRABAPI']` *before* importing
crabby. The stub lives in `conftest.py` so it is applied at test-collection
time, before any `import crabby` statement runs.
"""

from __future__ import annotations

import argparse
import importlib
import json
import re
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest


# Import crabby exactly once. conftest.py has already stubbed CRABAPI.
crabby = importlib.import_module("crabby")


# =============================================================================
# str2bool
# =============================================================================
class TestStr2Bool:
    @pytest.mark.parametrize("v", ["yes", "true", "1", "t", "y", "YES", "True", "T", "Y"])
    def test_truthy_strings(self, v: str) -> None:
        assert crabby.str2bool(v) is True

    @pytest.mark.parametrize("v", ["no", "false", "0", "f", "n", "NO", "False", "F", "N"])
    def test_falsy_strings(self, v: str) -> None:
        assert crabby.str2bool(v) is False

    def test_bool_passthrough_true(self) -> None:
        assert crabby.str2bool(True) is True

    def test_bool_passthrough_false(self) -> None:
        assert crabby.str2bool(False) is False

    @pytest.mark.parametrize("v", ["maybe", "tru", "", "2", "yess", "FALSEY"])
    def test_invalid_raises(self, v: str) -> None:
        with pytest.raises(argparse.ArgumentTypeError):
            crabby.str2bool(v)

    def test_non_string_non_bool_explodes(self) -> None:
        # `None` is not a bool and has no .lower() -> AttributeError. This is a
        # latent fragility in crabby.str2bool: it does isinstance(v, bool) but
        # then assumes .lower() works on anything else. Document the behaviour.
        with pytest.raises((AttributeError, argparse.ArgumentTypeError)):
            crabby.str2bool(None)


# =============================================================================
# rnd_str
# =============================================================================
class TestRndStr:
    def test_deterministic_same_seed(self) -> None:
        assert crabby.rnd_str(8, "seed_a") == crabby.rnd_str(8, "seed_a")

    def test_correct_length(self) -> None:
        for n in (1, 4, 8, 16, 64):
            assert len(crabby.rnd_str(n, "any_seed")) == n

    def test_only_ascii_letters(self) -> None:
        import string

        out = crabby.rnd_str(200, "alphabet_check")
        assert set(out) <= set(string.ascii_letters)

    def test_different_seeds_differ(self) -> None:
        a = crabby.rnd_str(8, "seed_a")
        b = crabby.rnd_str(8, "seed_b")
        assert a != b

    def test_collision_resistance_on_real_das_names(self, datasets_dir: Path) -> None:
        """
        Apply the actual crabby truncation logic to ~50 real DAS paths from
        MC_2024.json and verify no two produce the same 8-char suffix. This
        directly probes the request-name-collision risk that motivates the
        rnd_str hash in the first place.
        """
        with (datasets_dir / "MC_2024.json").open() as f:
            j = json.load(f)

        long_dataset_names = []
        for cat, samples in j.items():
            if not isinstance(samples, dict):
                continue
            for path in samples.values():
                if not isinstance(path, str):
                    continue
                if path.startswith("#") or len(path) < 10:
                    continue
                name = path.lstrip("/").replace("/", "_")
                if len(name) >= 95:
                    long_dataset_names.append(name)

        # We only need >= 2 to even test collisions. We expect tens.
        assert len(long_dataset_names) >= 2, "MC_2024.json has no long names to test against"

        suffixes = [crabby.rnd_str(8, n) for n in long_dataset_names]
        # No collisions among distinct names
        seen: dict[str, str] = {}
        for name, suf in zip(long_dataset_names, suffixes):
            if suf in seen and seen[suf] != name:
                pytest.fail(
                    f"Suffix collision: {name!r} and {seen[suf]!r} both produced {suf!r}"
                )
            seen[suf] = name


# =============================================================================
# Request-name truncation (the inline logic in make() and status())
# =============================================================================
def _truncate(dataset_path: str) -> str:
    """Replicate the (dataset_name, request_name) logic from crabby.make()."""
    dataset_name = dataset_path.lstrip("/").replace("/", "_")
    if len(dataset_name) < 95:
        return dataset_name
    return dataset_name[:90] + crabby.rnd_str(8, dataset_name)


class TestRequestNameTruncation:
    def test_short_name_unchanged(self) -> None:
        short = "/A/B/MINIAODSIM"
        assert _truncate(short) == "A_B_MINIAODSIM"
        assert len(_truncate(short)) < 95

    def test_long_name_truncated_to_98(self) -> None:
        long_path = (
            "/GluGluHHto2B2Tau_Par-c2-0p00-kl-0p00-kt-1p00_TuneCP5_13p6TeV_powheg-pythia8"
            "/RunIII2024Summer24MiniAODv6-PowhegBugFix_150X_mcRun3_2024_realistic_v2-v2"
            "/MINIAODSIM"
        )
        r = _truncate(long_path)
        assert len(r) == 98, f"Expected 98, got {len(r)}"

    def test_truncation_deterministic(self) -> None:
        long_path = (
            "/GluGluHHto2B2Tau_Par-c2-0p00-kl-0p00-kt-1p00_TuneCP5_13p6TeV_powheg-pythia8"
            "/RunIII2024Summer24MiniAODv6-PowhegBugFix_150X_mcRun3_2024_realistic_v2-v2"
            "/MINIAODSIM"
        )
        assert _truncate(long_path) == _truncate(long_path)

    def test_two_long_names_get_different_suffixes(self) -> None:
        a = (
            "/GluGluHHto2B2Tau_Par-c2-0p00-kl-0p00-kt-1p00_TuneCP5_13p6TeV_powheg-pythia8"
            "/RunIII2024Summer24MiniAODv6-PowhegBugFix_150X_mcRun3_2024_realistic_v2-v1"
            "/MINIAODSIM"
        )
        b = (
            "/GluGluHHto2B2Tau_Par-c2-0p00-kl-0p00-kt-1p00_TuneCP5_13p6TeV_powheg-pythia8"
            "/RunIII2024Summer24MiniAODv6-PowhegBugFix_150X_mcRun3_2024_realistic_v2-v2"
            "/MINIAODSIM"
        )
        # Names differ only in the very last suffix (v1 vs v2), which is in the
        # part beyond char 90 -> collision risk if the rnd_str seed weren't the
        # full dataset_name.
        assert _truncate(a) != _truncate(b)

    def test_real_das_paths_yield_unique_request_names(self, datasets_dir: Path) -> None:
        """
        Run the truncation over the *distinct* DAS paths in a real catalog and
        assert uniqueness of the resulting request names. We dedupe inputs
        first because MC_2024.json deliberately re-uses some paths across
        categories (e.g. HHbbtt vs HHbbtt_old) -- that's a catalog choice, not
        a crabby bug. The truncation function itself must still be injective
        on distinct inputs.
        """
        with (datasets_dir / "MC_2024.json").open() as f:
            j = json.load(f)

        paths: set[str] = set()
        for cat, samples in j.items():
            if not isinstance(samples, dict):
                continue
            for v in samples.values():
                if isinstance(v, str) and not v.startswith("#") and len(v) > 10:
                    paths.add(v)

        assert len(paths) > 50, f"only {len(paths)} distinct paths; too few to be meaningful"

        names = [_truncate(p) for p in paths]
        dups = {n for n in names if names.count(n) > 1}
        assert not dups, f"Duplicate request_names from distinct DAS paths: {dups}"


# =============================================================================
# Template substitution invariants (the heart of make())
# =============================================================================
@pytest.fixture
def base_card(tmp_path: Path) -> dict[str, Any]:
    """A minimal, valid card dict that make() will accept."""
    work_area = tmp_path / "crab_test_workarea"
    work_area.mkdir()
    return {
        "workArea": str(work_area),
        "config": "configs/MC_2024_NANO.py",
        "outLFNDirBase": "/store/user/testuser/whatever/mc_2024",
        "storageSite": "T2_US_Purdue",
        "publication": True,
        "tag_extension": "DAZSLE_PFNano",
        "tag_mod": None,
        "data": False,
        "lumiMask": None,
        "voGroup": None,
    }


@pytest.fixture
def base_card_data(base_card: dict[str, Any]) -> dict[str, Any]:
    base_card["data"] = True
    base_card["lumiMask"] = "jsons/Cert_Collisions2024_378981_386951_Golden.json"
    return base_card


PLACEHOLDER_RE = re.compile(r"_[A-Za-z]+_")
# Keys we know template_crab.py uses; everything else matching the regex is a leak.
KNOWN_PLACEHOLDERS = {
    "_requestName_",
    "_workArea_",
    "_psetName_",
    "_inputDataset_",
    "_outLFNDirBase_",
    "_storageSite_",
    "_publication_",
    "_splitting_",
    "_outputDatasetTag_",
}


def _read_generated(card: dict[str, Any], dataset: str) -> str:
    name = dataset.lstrip("/").replace("/", "_")
    out_path = Path(card["workArea"]) / f"submit_{name}.py"
    return out_path.read_text()


class TestMakeSubstitution:
    def test_mc_no_test_leaves_no_placeholders(
        self, base_card: dict[str, Any], template_crab_text: str
    ) -> None:
        ds = "/GluGluHHto2B2Tau_Foo/RunIII2024-v2/MINIAODSIM"
        crabby.make(base_card, [ds], template_crab_text, test=False)
        content = _read_generated(base_card, ds)

        # No leftover _<TOKEN>_ from the template's known set
        for ph in KNOWN_PLACEHOLDERS:
            assert ph not in content, f"Placeholder {ph!r} not substituted"
        # Defensive: no leftovers matching the regex *and* in the known set.
        # We deliberately don't fail on every `_word_` because LFN paths can
        # contain underscores-with-letters between them.
        leftover_known = [ph for ph in KNOWN_PLACEHOLDERS if ph in content]
        assert leftover_known == []

    def test_mc_output_compiles_as_python(
        self, base_card: dict[str, Any], template_crab_text: str
    ) -> None:
        ds = "/SomeDataset_Foo/SomeCampaign-v1/MINIAODSIM"
        crabby.make(base_card, [ds], template_crab_text, test=False)
        content = _read_generated(base_card, ds)
        # The generated submit_*.py is supposed to be a runnable Python config
        # (CRAB loads it via imp.load_source). It must at minimum compile.
        compile(content, "submit_generated.py", "exec")

    def test_mc_output_contains_dataset_verbatim(
        self, base_card: dict[str, Any], template_crab_text: str
    ) -> None:
        ds = "/GluGluFoo_Bar/RunIII2024Summer24MiniAODv6-Tag-v3/MINIAODSIM"
        crabby.make(base_card, [ds], template_crab_text, test=False)
        content = _read_generated(base_card, ds)
        assert ds in content

    @pytest.mark.xfail(
        reason=(
            "real bug: template_crab.py wraps _publication_ in quotes "
            "(`config.Data.publication = \"_publication_\"`) so after substitution "
            "the value is the STRING 'False', not the literal False. In Python any "
            "non-empty string is truthy -> CRAB would still publish in --test True "
            "mode. Either the template should drop the quotes around _publication_, "
            "or crabby should emit unquoted booleans. See template_crab.py L22."
        ),
        strict=True,
    )
    def test_test_mode_sets_total_units_and_publication_false(
        self, base_card: dict[str, Any], template_crab_text: str
    ) -> None:
        ds = "/A/B-v1/MINIAODSIM"
        crabby.make(base_card, [ds], template_crab_text, test=True)
        content = _read_generated(base_card, ds)

        assert "config.Data.totalUnits = 1" in content, (
            "test=True must inject totalUnits = 1"
        )
        # We *want* this to be the Python literal False, but it's currently the
        # string "False" -- see xfail reason.
        assert "config.Data.publication = False" in content
        assert "config.Data.publication = True" not in content

    def test_test_mode_injects_total_units_documented_behaviour(
        self, base_card: dict[str, Any], template_crab_text: str
    ) -> None:
        """Companion to the xfail above: lock down the part that DOES work."""
        ds = "/A/B-v1/MINIAODSIM"
        crabby.make(base_card, [ds], template_crab_text, test=True)
        content = _read_generated(base_card, ds)
        assert "config.Data.totalUnits = 1" in content
        # Document the current (buggy) string-quoted behaviour so any change is loud:
        assert 'config.Data.publication = "False"' in content

    def test_data_mode_sets_units_per_job_and_runtime(
        self, base_card_data: dict[str, Any], template_crab_text: str
    ) -> None:
        ds = "/JetMET0/Run2024C-2024CDEReprocessing-v1/NANOAOD"
        crabby.make(base_card_data, [ds], template_crab_text, test=False)
        content = _read_generated(base_card_data, ds)

        assert "config.Data.unitsPerJob = 50" in content
        assert "config.JobType.maxJobRuntimeMin = 2750" in content
        assert "config.Data.splitting = \"LumiBased\"" in content
        assert "config.Data.lumiMask" in content
        assert base_card_data["lumiMask"] in content

    def test_mc_mode_does_not_inject_data_only_lines(
        self, base_card: dict[str, Any], template_crab_text: str
    ) -> None:
        ds = "/A/B-v1/MINIAODSIM"
        crabby.make(base_card, [ds], template_crab_text, test=False)
        content = _read_generated(base_card, ds)
        # MC -> Automatic splitting, no unitsPerJob hint, no lumiMask
        assert "config.Data.splitting = \"Automatic\"" in content
        assert "unitsPerJob" not in content
        assert "lumiMask" not in content
        assert "maxJobRuntimeMin" not in content

    @pytest.mark.xfail(
        reason=(
            "real bug: see test_test_mode_sets_total_units_and_publication_false. "
            "_publication_ is quoted in template_crab.py, so test mode injects "
            "the string 'False' instead of the literal False -- CRAB sees a "
            "truthy string and publishes anyway."
        ),
        strict=True,
    )
    def test_test_mode_overrides_publication_even_if_card_says_true(
        self, base_card: dict[str, Any], template_crab_text: str
    ) -> None:
        assert base_card["publication"] is True
        ds = "/A/B-v1/MINIAODSIM"
        crabby.make(base_card, [ds], template_crab_text, test=True)
        content = _read_generated(base_card, ds)
        assert "config.Data.publication = False" in content
        assert "config.Data.publication = True" not in content


# =============================================================================
# Tag handling in make()
# =============================================================================
class TestTagHandling:
    @pytest.fixture
    def card_runII_tag_mod(self, base_card: dict[str, Any]) -> dict[str, Any]:
        c = dict(base_card)
        c["tag_mod"] = "MyMod"
        c["tag_extension"] = None
        return c

    def test_runII_with_tag_mod_substitutes_miniaod_regex(
        self, card_runII_tag_mod: dict[str, Any], template_crab_text: str
    ) -> None:
        ds = "/Foo/RunIISummer20UL18MiniAODv2-tag-v1/MINIAODSIM"
        crabby.make(card_runII_tag_mod, [ds], template_crab_text, test=False)
        content = _read_generated(card_runII_tag_mod, ds)
        # Original "MiniAODv2" is substituted by "MyMod" within the campaign
        # token (which becomes the outputDatasetTag value)
        m = re.search(r"outputDatasetTag\s*=\s*\"([^\"]+)\"", content)
        assert m is not None
        tag = m.group(1)
        assert "MiniAOD" not in tag, f"MiniAODv? not substituted: {tag}"
        assert "MyMod" in tag, f"tag_mod not present in: {tag}"

    def test_non_runII_with_tag_mod_appends(
        self, card_runII_tag_mod: dict[str, Any], template_crab_text: str
    ) -> None:
        ds = "/Foo/SomeRandomCampaign-v1/MINIAODSIM"
        crabby.make(card_runII_tag_mod, [ds], template_crab_text, test=False)
        content = _read_generated(card_runII_tag_mod, ds)
        m = re.search(r"outputDatasetTag\s*=\s*\"([^\"]+)\"", content)
        assert m is not None
        tag = m.group(1)
        assert tag.endswith("_MyMod"), f"tag_mod should be appended: {tag}"

    def test_tag_extension_appended_when_no_tag_mod(
        self, base_card: dict[str, Any], template_crab_text: str
    ) -> None:
        ds = "/Foo/RunIII2024Bar-v2/MINIAODSIM"
        crabby.make(base_card, [ds], template_crab_text, test=False)
        content = _read_generated(base_card, ds)
        m = re.search(r"outputDatasetTag\s*=\s*\"([^\"]+)\"", content)
        assert m is not None
        tag = m.group(1)
        assert tag.endswith("_DAZSLE_PFNano"), f"tag_extension not appended: {tag}"

    def test_no_tag_mod_and_no_tag_extension_raises(
        self, base_card: dict[str, Any], template_crab_text: str
    ) -> None:
        card = dict(base_card)
        card["tag_mod"] = None
        card["tag_extension"] = None
        with pytest.raises(ValueError, match="tag_mod.*tag_extension"):
            crabby.make(card, ["/A/B-v1/MINIAODSIM"], template_crab_text, test=False)


# =============================================================================
# parse_args
# =============================================================================
class TestParseArgs:
    def test_year_outside_choices_errors(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(sys, "argv", ["crabby.py", "--year", "1999", "--dataset", "HHbbtt"])
        with pytest.raises(SystemExit):
            crabby.parse_args()

    def test_year_required(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(sys, "argv", ["crabby.py", "--dataset", "HHbbtt"])
        with pytest.raises(SystemExit):
            crabby.parse_args()

    def test_dataset_required(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(sys, "argv", ["crabby.py", "--year", "2024"])
        with pytest.raises(SystemExit):
            crabby.parse_args()

    def test_minimal_valid_call(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            sys, "argv", ["crabby.py", "--year", "2024", "--dataset", "HHbbtt"]
        )
        monkeypatch.setenv("USER", "alice-foo")
        args = crabby.parse_args()
        assert args.year == "2024"
        assert args.dataset == "HHbbtt"
        # USER munging strips the "-foo"
        assert args.user == "alice"

    @pytest.mark.parametrize("year", ["2022", "2022EE", "2023", "2023BPix", "2024"])
    def test_all_valid_years(self, year: str, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(sys, "argv", ["crabby.py", "--year", year, "--dataset", "X"])
        monkeypatch.setenv("USER", "u")
        args = crabby.parse_args()
        assert args.year == year

    def test_test_flag_str2bool(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            sys,
            "argv",
            ["crabby.py", "--year", "2024", "--dataset", "HHbbtt", "--test", "True"],
        )
        monkeypatch.setenv("USER", "u")
        args = crabby.parse_args()
        assert args.test is True

    def test_test_flag_invalid_string_errors(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            sys,
            "argv",
            ["crabby.py", "--year", "2024", "--dataset", "HHbbtt", "--test", "maybe"],
        )
        monkeypatch.setenv("USER", "u")
        with pytest.raises(SystemExit):
            crabby.parse_args()


# =============================================================================
# Bonus: cross-cutting invariants on a real card from real JSON
# =============================================================================
class TestRealCatalogIntegration:
    """
    Spin up a synthetic card whose `datasets` come straight out of MC_2024.json
    HHbbtt category, run make() on the first three, and assert every generated
    file compiles and contains its dataset.
    """

    def test_make_over_real_HHbbtt_subset(
        self,
        base_card: dict[str, Any],
        template_crab_text: str,
        datasets_dir: Path,
    ) -> None:
        with (datasets_dir / "MC_2024.json").open() as f:
            j = json.load(f)
        if "HHbbtt" not in j:
            pytest.skip("MC_2024.json missing HHbbtt category")
        paths = [
            v
            for v in j["HHbbtt"].values()
            if isinstance(v, str) and not v.startswith("#") and len(v) > 10
        ]
        assert paths, "no usable HHbbtt paths in real catalog"
        subset = paths[:3]
        crabby.make(base_card, subset, template_crab_text, test=False)
        for ds in subset:
            content = _read_generated(base_card, ds)
            compile(content, "submit.py", "exec")
            assert ds in content
            for ph in KNOWN_PLACEHOLDERS:
                assert ph not in content, f"Placeholder {ph} survived for {ds}"
