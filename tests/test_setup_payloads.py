"""setup.sh must install every payload the fork README left to humans.

Both bugs below were REMOTE-ONLY: the local CMSSW area looked healthy, the
harness's own pytest suite was green, and the failure only appeared once a CRAB
worker unpacked the sandbox. They were found by a collaborator, not by us
(2026-08-04) — these tests exist so a third one cannot hide the same way.

  * ONNX taggers -> RecoBTag/CombinedScouting/data/   (exit 7002 FileInPathError)
  * HHbbttPreselFilter.cc -> PhysicsTools/PatFromScouting/plugins/
    (the psets do cms.EDFilter("HHbbttPreselFilter"); the frozen topic does NOT
    ship it, despite the fork README claiming otherwise)
"""
import pathlib
import re

import pytest

SETUP = pathlib.Path(__file__).resolve().parent.parent / "setup.sh"
TEXT = SETUP.read_text()


def _fresh_install_block() -> str:
    """The branch that runs on a first-time build (before `else`)."""
    return TEXT.split("\nelse\n")[0]


def _heal_block() -> str:
    """The branch that runs when the area already exists."""
    return TEXT.split("\nelse\n")[1]


@pytest.mark.parametrize("dest", [
    "RecoBTag/CombinedScouting/data",                 # ONNX taggers
    "PhysicsTools/PatFromScouting/plugins",           # the presel filter
])
def test_fresh_build_installs_payload(dest):
    assert dest in _fresh_install_block(), (
        f"setup.sh no longer installs into {dest} on a fresh build — a new "
        f"collaborator's CRAB sandbox will be missing it and every remote job "
        f"will fail while the local area looks fine."
    )


@pytest.mark.parametrize("payload", ["model*.onnx", "HHbbttPreselFilter.cc"])
def test_fresh_build_copies_payload(payload):
    assert payload in _fresh_install_block(), f"{payload} is not copied on a fresh build"


@pytest.mark.parametrize("payload", ["model_v3.onnx", "HHbbttPreselFilter.cc"])
def test_existing_area_is_healed(payload):
    """Areas built before these steps existed must self-repair on re-run."""
    assert payload in _heal_block(), (
        f"re-running setup.sh no longer heals a missing {payload}; users who "
        f"built earlier stay broken with no signal"
    )


def test_payloads_are_installed_before_the_build():
    """scram b must come after the copies, or the filter is never compiled."""
    block = _fresh_install_block()
    assert block.index("HHbbttPreselFilter.cc") < block.index("scram b"), (
        "the filter is copied AFTER scram b — it will not be compiled"
    )


def test_buildfile_dependencies_are_asserted_not_assumed():
    """The filter needs edm::View deps; setup.sh must verify, not hope."""
    block = _fresh_install_block()
    for dep in ("DataFormats/PatCandidates", "DataFormats/Common", "DataFormats/Scouting"):
        assert dep in block, f"setup.sh does not check BuildFile.xml for {dep}"
    assert "exit 1" in block, "the BuildFile check does not fail the build"


def test_heal_rebuilds_after_adding_the_filter():
    """A copied .cc is inert until scram b runs again."""
    heal = _heal_block()
    assert re.search(r"healed_needs_build=1", heal), "heal path never flags a rebuild"
    assert re.search(r"scram b", heal), "heal path never rebuilds"
