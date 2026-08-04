"""The pset guard must catch a missing CMSSW_AREA BEFORE CRAB does.

Field failure (lxplus, 2026-08-04): with CMSSW_AREA unset, expandvars kept the
literal ``${CMSSW_AREA}/...``, --make succeeded, and the user got CRAB's opaque
ConfigurationException at submit. These pin the loud replacement.
"""
import os
import pytest

import crabby


CARD_PATH = "${CMSSW_AREA}/src/ScoutingNanoProduction/scoutingnano_data_hhbbtt.py"


def test_unset_var_fails_loudly_with_recipe(monkeypatch):
    monkeypatch.delenv("CMSSW_AREA", raising=False)
    with pytest.raises(SystemExit) as e:
        crabby.resolve_pset(CARD_PATH)
    msg = str(e.value)
    assert "CMSSW_AREA is not set" in msg
    assert "source .env" in msg          # the fix is IN the error


def test_set_but_unbuilt_area_names_setup(monkeypatch, tmp_path):
    monkeypatch.setenv("CMSSW_AREA", str(tmp_path))
    with pytest.raises(SystemExit) as e:
        crabby.resolve_pset(CARD_PATH)
    assert "setup.sh" in str(e.value)


def test_valid_area_passes_through(monkeypatch, tmp_path):
    pset = tmp_path / "src" / "ScoutingNanoProduction" / "scoutingnano_data_hhbbtt.py"
    pset.parent.mkdir(parents=True)
    pset.write_text("# pset")
    monkeypatch.setenv("CMSSW_AREA", str(tmp_path))
    assert crabby.resolve_pset(CARD_PATH) == str(pset)
