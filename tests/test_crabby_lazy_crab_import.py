"""`--make` must work without a CRAB environment.

The docs prescribe a two-phase `--make` -> inspect -> `--submit` workflow, but a
module-scope `from CRABAPI.RawCommand import crabCommand` made the whole tool
unimportable without crab-setup.sh, greeting a new collaborator with a bare
ModuleNotFoundError. Our shells always had CRAB sourced, so it was invisible
from the inside (cold-start rehearsal, 2026-08-04).
"""
import pathlib
import re

SRC = (pathlib.Path(__file__).resolve().parent.parent / "crabby.py").read_text()


def test_no_module_scope_crab_import():
    """A top-level CRABAPI import breaks --make for everyone without CRAB."""
    for line in SRC.splitlines():
        if line.startswith(("import ", "from ")) and "CRABAPI" in line:
            raise AssertionError(
                f"module-scope CRAB import reintroduced: {line!r} — this makes "
                f"--make impossible without crab-setup.sh"
            )


def test_crab_import_is_inside_a_function():
    """It must be lazy, i.e. indented inside the accessor."""
    m = re.search(r"^(\s+)from CRABAPI\.RawCommand import crabCommand", SRC, re.M)
    assert m and m.group(1), "the CRABAPI import is not indented inside a function"


def test_missing_crab_explains_how_to_get_it():
    """The failure must carry the recipe, not a raw ImportError."""
    fn = SRC[SRC.index("def _crab_command"):]
    fn = fn[: fn.index("\ndef ", 1)] if "\ndef " in fn[1:] else fn
    assert "crab-setup.sh" in fn, "the error does not name crab-setup.sh"
    assert "--make works without" in fn, "the error does not say --make needs no CRAB"
    assert "SystemExit" in fn, "raises a raw exception instead of exiting cleanly"


def test_submit_still_goes_through_the_accessor():
    assert "_crab_command()(\"submit\"" in SRC, "submit no longer uses the lazy accessor"
