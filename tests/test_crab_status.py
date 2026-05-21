"""Tests for the CRAB status parsing logic.

NOTE ON FILE NAMING:
    The behaviours described in the task brief -- ``os.popen("crab status ...")``,
    extracting the ``CRAB project directory:`` / ``Jobs status:`` /
    ``Output dataset:`` lines, writing ``outputs_<card>.txt`` -- live in
    ``crabby.py:status()``, NOT in the top-level ``crab_status.py`` (which
    is a separate aggregate-monitor script using ``subprocess.run`` and a
    very different parsing routine).  These tests exercise the function the
    brief is actually describing.  The placement under
    ``tests/test_crab_status.py`` matches the requested file path.
"""

from __future__ import annotations

import os
import sys
import types
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Path / mock setup (mirrors test_template_crab.py)
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

if "CRABAPI" not in sys.modules:
    crabapi_pkg = types.ModuleType("CRABAPI")
    raw_cmd_mod = types.ModuleType("CRABAPI.RawCommand")
    raw_cmd_mod.crabCommand = lambda *a, **kw: None  # noqa: E731
    crabapi_pkg.RawCommand = raw_cmd_mod
    sys.modules["CRABAPI"] = crabapi_pkg
    sys.modules["CRABAPI.RawCommand"] = raw_cmd_mod

import crabby  # noqa: E402  (must come after CRABAPI mock)


# ---------------------------------------------------------------------------
# A realistic-looking ``crab status`` output, taken from the CRAB docs format.
# ---------------------------------------------------------------------------
SAMPLE_CRAB_OUTPUT = """\
CRAB project directory: crab/TAG/mc_2024_HHbbtt/crab_GluGluHHto2B2Tau_kl-1
Task name:              250101_120000:user_crab_GluGluHHto2B2Tau_kl-1
Status on the CRAB server: SUBMITTED
Task status:            COMPLETED

Jobs status:    unsubmitted             0.0% (   0/100)
                idle                    2.0% (   2/100)
                running                10.0% (  10/100)
                transferring            3.0% (   3/100)
                transferred             5.0% (   5/100)
                finished               75.0% (  75/100)
                failed                  5.0% (   5/100)

Output dataset:                /GluGluHHto2B2Tau_kl-1/user-DAZSLE_PFNano-abcd1234/USER
Output dataset DBS:            phys03
"""


# ---------------------------------------------------------------------------
# Fake popen plumbing: replaces ``os.popen`` so we can feed canned output
# into crabby.status() without actually running ``crab``.
# ---------------------------------------------------------------------------
class _FakePopen:
    def __init__(self, text: str):
        self._text = text

    def read(self) -> str:
        return self._text


def _patch_popen(monkeypatch, responses):
    """``responses`` is either a single string (used for every call) or a
    list of strings consumed in order.  Captures the commands invoked."""
    calls: list[str] = []

    if isinstance(responses, str):
        def fake(cmd):
            calls.append(cmd)
            return _FakePopen(responses)
    else:
        it = iter(responses)

        def fake(cmd):
            calls.append(cmd)
            try:
                return _FakePopen(next(it))
            except StopIteration:
                return _FakePopen("")

    monkeypatch.setattr(crabby.os, "popen", fake)
    return calls


def _make_card(workarea: Path) -> dict:
    return {"workArea": str(workarea)}


def _set_args(monkeypatch, card_path: str = "cards/dummy.yaml"):
    """crabby.status() reads ``args.card`` from a module-level global -- a
    real coupling smell that this test deliberately exercises."""
    fake_args = types.SimpleNamespace(card=card_path)
    monkeypatch.setattr(crabby, "args", fake_args, raising=False)


# ---------------------------------------------------------------------------
# 1) Status block extraction
# ---------------------------------------------------------------------------
def test_status_extracts_project_dir_and_dataset(monkeypatch, tmp_path, capsys):
    """status() must surface the CRAB project directory line and the
    output dataset DAS name even on a *generously realistic* CRAB stdout."""
    _patch_popen(monkeypatch, SAMPLE_CRAB_OUTPUT)
    _set_args(monkeypatch)
    monkeypatch.chdir(tmp_path)

    card = _make_card(tmp_path / "wa")
    datasets = ["/GluGluHHto2B2Tau_kl-1/Run3-MiniAOD/MINIAODSIM"]

    crabby.status(card, datasets)
    out = capsys.readouterr().out

    # CRAB project directory line propagates verbatim.
    assert "CRAB project directory: crab/TAG/mc_2024_HHbbtt/crab_GluGluHHto2B2Tau_kl-1" in out

    # The first three keywords (which fall inside the parser's hardcoded
    # 5-line lookahead window after ``Jobs status:``) MUST appear.
    for keyword in ("unsubmitted", "idle", "running"):
        assert keyword in out, f"job-status keyword {keyword!r} missing from status() output"

    # outputs_<card>.txt must contain exactly the DAS name extracted from
    # the "Output dataset:" line (not the "Output dataset DBS:" line).
    expected = "/GluGluHHto2B2Tau_kl-1/user-DAZSLE_PFNano-abcd1234/USER"
    out_file = tmp_path / "outputs_dummy.txt"
    assert out_file.exists(), "status() did not write outputs_<card>.txt"
    assert out_file.read_text().strip() == expected


@pytest.mark.xfail(
    strict=True,
    reason=(
        "REAL BUG: crabby.status() looks ahead only ``range(5)`` lines after "
        "``Jobs status:``, but real CRAB output has 7 status lines "
        "(unsubmitted/idle/running/transferring/transferred/finished/failed). "
        "The last two (``finished``, ``failed``) are silently dropped from "
        "the printed status.  Fix: widen the lookahead to range(7) or scan "
        "until the next blank line."
    ),
)
def test_status_prints_all_seven_job_status_keywords(monkeypatch, tmp_path, capsys):
    _patch_popen(monkeypatch, SAMPLE_CRAB_OUTPUT)
    _set_args(monkeypatch)
    monkeypatch.chdir(tmp_path)

    crabby.status(
        _make_card(tmp_path / "wa"),
        ["/GluGluHHto2B2Tau_kl-1/Run3-MiniAOD/MINIAODSIM"],
    )
    out = capsys.readouterr().out

    for keyword in (
        "unsubmitted",
        "idle",
        "running",
        "transferring",
        "transferred",
        "finished",
        "failed",
    ):
        assert keyword in out, f"job-status keyword {keyword!r} missing from status() output"


# ---------------------------------------------------------------------------
# 2) Empty / single / multi dataset iteration
# ---------------------------------------------------------------------------
def test_status_empty_dataset_list(monkeypatch, tmp_path):
    """An empty dataset list must still produce ``outputs_<card>.txt`` (empty)
    and must not crash or invoke ``crab status`` at all."""
    calls = _patch_popen(monkeypatch, SAMPLE_CRAB_OUTPUT)
    _set_args(monkeypatch)
    monkeypatch.chdir(tmp_path)

    crabby.status(_make_card(tmp_path / "wa"), [])

    assert calls == [], "status() should not call ``crab status`` for an empty list"
    out_file = tmp_path / "outputs_dummy.txt"
    assert out_file.exists()
    assert out_file.read_text() == ""


def test_status_multiple_datasets_emit_one_das_per_line(monkeypatch, tmp_path):
    """For N datasets we get N popen calls and N lines in outputs_<card>.txt."""
    outputs = []
    for i in range(3):
        outputs.append(
            SAMPLE_CRAB_OUTPUT.replace(
                "GluGluHHto2B2Tau_kl-1/user-DAZSLE_PFNano-abcd1234",
                f"DummyDS_{i}/user-DAZSLE_PFNano-abcd123{i}",
            )
        )
    calls = _patch_popen(monkeypatch, outputs)
    _set_args(monkeypatch)
    monkeypatch.chdir(tmp_path)

    datasets = [f"/DummyDS_{i}/Run3-MiniAOD/MINIAODSIM" for i in range(3)]
    crabby.status(_make_card(tmp_path / "wa"), datasets)

    assert len(calls) == 3, f"Expected 3 popen calls, got {len(calls)}"

    lines = (tmp_path / "outputs_dummy.txt").read_text().splitlines()
    # One DAS line per dataset.
    assert len(lines) == 3
    for i, line in enumerate(lines):
        assert f"DummyDS_{i}" in line


# ---------------------------------------------------------------------------
# 3) Truncated-request-name coupling between make() and status()
# ---------------------------------------------------------------------------
def _request_name_via_make_logic(dataset: str) -> str:
    """Re-derive the request name using the *exact* expression in make()."""
    dataset_name = dataset.lstrip("/").replace("/", "_")
    if len(dataset_name) < 95:
        return dataset_name
    return dataset_name[:90] + crabby.rnd_str(8, dataset_name)


def test_truncated_request_name_matches_between_make_and_status(monkeypatch, tmp_path):
    """A dataset whose flattened name is >= 95 chars should produce the
    same truncated request name in both make() and status().  Anything
    else means status() looks for a directory make() never created."""
    # Build a dataset string whose flattened form is well past 95 chars.
    long_blob = "X" * 120
    dataset = f"/Long_{long_blob}/Run3-MiniAOD/MINIAODSIM"

    expected = _request_name_via_make_logic(dataset)
    assert len(dataset.lstrip("/").replace("/", "_")) >= 95, "fixture should exceed cutoff"
    assert len(expected) == 98, f"truncated name should be 90+8 chars, got {len(expected)}"

    # Capture what status() actually constructs as its cfg_dir.
    calls = _patch_popen(monkeypatch, SAMPLE_CRAB_OUTPUT)
    _set_args(monkeypatch)
    monkeypatch.chdir(tmp_path)

    workarea = tmp_path / "wa"
    crabby.status({"workArea": str(workarea)}, [dataset])

    assert len(calls) == 1
    cmd = calls[0]
    # The command must include the *truncated* request name.
    expected_dir = os.path.join(str(workarea), "crab_" + expected)
    assert expected_dir in cmd, (
        f"status() invoked: {cmd!r}\n"
        f"  expected directory fragment: {expected_dir!r}\n"
        f"  (truncated request name from make()-style logic: {expected!r})"
    )


def test_short_dataset_name_is_not_truncated(monkeypatch, tmp_path):
    """Names < 95 chars must round-trip unchanged."""
    dataset = "/Short/Run3-MiniAOD/MINIAODSIM"
    calls = _patch_popen(monkeypatch, SAMPLE_CRAB_OUTPUT)
    _set_args(monkeypatch)
    monkeypatch.chdir(tmp_path)

    workarea = tmp_path / "wa"
    crabby.status({"workArea": str(workarea)}, [dataset])

    expected_dir = os.path.join(str(workarea), "crab_Short_Run3-MiniAOD_MINIAODSIM")
    assert expected_dir in calls[0]


# ---------------------------------------------------------------------------
# 4) DAS-names file: path derivation from ``args.card``
# ---------------------------------------------------------------------------
def test_outputs_filename_derived_from_args_card(monkeypatch, tmp_path):
    """The output file name is ``outputs_<basename-without-ext>.txt`` where
    the basename comes from the *global* ``args.card``.  Exercise the
    sketchy global coupling here so regressions are obvious."""
    _patch_popen(monkeypatch, SAMPLE_CRAB_OUTPUT)
    _set_args(monkeypatch, card_path="cards/fnal_2024.yaml")
    monkeypatch.chdir(tmp_path)

    crabby.status(_make_card(tmp_path / "wa"), ["/A/B/C"])

    assert (tmp_path / "outputs_fnal_2024.txt").exists()
    assert not (tmp_path / "outputs_dummy.txt").exists()


def test_outputs_filename_handles_card_without_directory(monkeypatch, tmp_path):
    """``args.card == "plain.yaml"`` (no directory prefix) must still work."""
    _patch_popen(monkeypatch, SAMPLE_CRAB_OUTPUT)
    _set_args(monkeypatch, card_path="plain.yaml")
    monkeypatch.chdir(tmp_path)

    crabby.status(_make_card(tmp_path / "wa"), ["/A/B/C"])
    assert (tmp_path / "outputs_plain.txt").exists()


def test_outputs_file_one_das_per_line(monkeypatch, tmp_path):
    """The file must be ``\\n``-joined, never comma-joined or single-line."""
    outputs = [
        SAMPLE_CRAB_OUTPUT.replace("abcd1234", f"abcd000{i}")
        for i in range(4)
    ]
    _patch_popen(monkeypatch, outputs)
    _set_args(monkeypatch)
    monkeypatch.chdir(tmp_path)

    crabby.status(
        _make_card(tmp_path / "wa"),
        [f"/DS_{i}/Run3-MiniAOD/MINIAODSIM" for i in range(4)],
    )

    text = (tmp_path / "outputs_dummy.txt").read_text()
    lines = text.split("\n")
    assert len(lines) == 4
    for line in lines:
        # Each line is a DAS-format dataset path
        assert line.startswith("/") and line.count("/") >= 3, f"malformed DAS line: {line!r}"


# ---------------------------------------------------------------------------
# 5) Robustness: empty / broken popen output
# ---------------------------------------------------------------------------
def test_status_handles_empty_popen_output(monkeypatch, tmp_path):
    """If ``crab status`` returns nothing (missing project dir, no proxy,
    crab client error etc.) the parser must not crash; it just writes an
    empty outputs_<card>.txt."""
    _patch_popen(monkeypatch, "")
    _set_args(monkeypatch)
    monkeypatch.chdir(tmp_path)

    # Must not raise.
    crabby.status(_make_card(tmp_path / "wa"), ["/Foo/Bar/Baz"])

    out_file = tmp_path / "outputs_dummy.txt"
    assert out_file.exists()
    assert out_file.read_text() == ""


def test_status_handles_garbled_output_with_trailing_jobs_status(monkeypatch, tmp_path):
    """A well-formed garbled stdout (no trailing ``Jobs status:`` line)
    must not crash the parser."""
    garbled = (
        "Error: project directory not found\n"
        "Some other line\n"
        "(no real content)\n"
    )
    _patch_popen(monkeypatch, garbled)
    _set_args(monkeypatch)
    monkeypatch.chdir(tmp_path)

    crabby.status(_make_card(tmp_path / "wa"), ["/Foo/Bar/Baz"])
    out_file = tmp_path / "outputs_dummy.txt"
    assert out_file.exists()
    assert out_file.read_text() == ""


@pytest.mark.xfail(
    strict=True,
    reason=(
        "REAL BUG: crabby.status() blindly indexes ``o[i+j]`` for j in "
        "range(5) after finding the ``Jobs status:`` line, without "
        "checking that the slice is in-bounds.  When the popen buffer "
        "ends within 5 lines of the ``Jobs status:`` header (truncated "
        "CRAB output, network error, broken pipe, ...) the call raises "
        "IndexError instead of degrading gracefully.  Fix: check "
        "``i + j < len(o)`` inside the inner loop, or use slicing."
    ),
)
def test_status_does_not_crash_on_truncated_jobs_status_block(monkeypatch, tmp_path):
    short = "Jobs status:\nfinished 100.0% (10/10)\n"
    _patch_popen(monkeypatch, short)
    _set_args(monkeypatch)
    monkeypatch.chdir(tmp_path)
    # IndexError here means status() walks past end-of-list.
    crabby.status(_make_card(tmp_path / "wa"), ["/Foo/Bar/Baz"])


@pytest.mark.xfail(
    strict=True,
    reason=(
        "REAL BUG (same root cause as above): a stdout that ends with "
        "``Jobs status:\\n`` (header only, no body) triggers IndexError "
        "in the ``o[i+j]`` lookahead."
    ),
)
def test_status_does_not_crash_on_header_only_jobs_status(monkeypatch, tmp_path):
    garbled = (
        "Error: project directory not found\n"
        "Some other line\n"
        "Jobs status:\n"
    )
    _patch_popen(monkeypatch, garbled)
    _set_args(monkeypatch)
    monkeypatch.chdir(tmp_path)
    crabby.status(_make_card(tmp_path / "wa"), ["/Foo/Bar/Baz"])
