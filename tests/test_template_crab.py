"""Adversarial tests for the template_crab.py <-> crabby.py:make() coupling.

These tests treat the placeholder substitution as a contract:
  template_crab.py declares slots like ``_requestName_``;
  crabby.py:make() builds a ``card_info`` dict that fills those slots via
  ``str.replace()``.  Any drift between the two surfaces silently produces
  broken CRAB configs (literal ``_token_`` strings end up in the submitted
  file) so we test the agreement explicitly.

The sibling agent owns ``tests/conftest.py`` which is expected to install a
mock for the ``CRABAPI`` module before any test imports crabby.  These tests
also install a defensive fallback mock at module-import time so the file is
not coupled to test-collection order.
"""

from __future__ import annotations

import ast
import os
import re
import sys
import types
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Repo paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = REPO_ROOT / "template_crab.py"
CRABBY_PATH = REPO_ROOT / "crabby.py"

# Ensure the repo root is importable so ``import crabby`` works.
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# ---------------------------------------------------------------------------
# Defensive CRABAPI mock.  The sibling agent's conftest.py is expected to
# install this; we install a no-op fallback so the file can also be loaded
# in isolation (e.g. during local debugging).  ``setdefault``-style guards
# guarantee we do not clobber a richer fixture put there by conftest.
# ---------------------------------------------------------------------------
if "CRABAPI" not in sys.modules:
    crabapi_pkg = types.ModuleType("CRABAPI")
    raw_cmd_mod = types.ModuleType("CRABAPI.RawCommand")
    raw_cmd_mod.crabCommand = lambda *a, **kw: None  # noqa: E731
    crabapi_pkg.RawCommand = raw_cmd_mod
    sys.modules["CRABAPI"] = crabapi_pkg
    sys.modules["CRABAPI.RawCommand"] = raw_cmd_mod


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
# Tokens that match ``_[A-Za-z]+_`` in the template but are NOT placeholders
# substituted by crabby.py:make().  ``_ALLOW_`` is a substring of the JDL
# expression ``+CMS_ALLOW_OVERFLOW=False`` and intentionally never replaced.
KNOWN_NON_PLACEHOLDER_TOKENS = {"_ALLOW_"}

# Realistic dummy values for every placeholder we expect make() to fill.
# Values are picked so the rendered file is valid Python (strings stay
# inside their quotes; ``_publication_`` is a Python literal because
# crabby.py replaces it verbatim, not as a quoted string -- see test_4).
DUMMY_CARD_INFO_STR = {
    "_requestName_": "dummy_request_name",
    "_workArea_": "crab/TAG/dummy_workarea",
    "_psetName_": "configs/MC_2024_Scouting.py",
    "_inputDataset_": "/DummyDataset/Run3-MiniAOD/MINIAODSIM",
    "_outputDatasetTag_": "Run3_Tag_DAZSLE_PFNano",
    "_outLFNDirBase_": "/store/user/dummy/production/",
    "_splitting_": "Automatic",
    "_publication_": "True",  # literal Python token, NOT a quoted string
    "_storageSite_": "T2_US_Purdue",
}


def _read_template() -> str:
    return TEMPLATE_PATH.read_text()


def _read_crabby_source() -> str:
    return CRABBY_PATH.read_text()


def _collect_template_tokens() -> set[str]:
    """Every ``_[A-Za-z]+_`` substring in template_crab.py.

    Note: this regex is *greedy* and intentionally matches ``_ALLOW_`` inside
    ``+CMS_ALLOW_OVERFLOW=False``.  Such substring matches are filtered out
    via KNOWN_NON_PLACEHOLDER_TOKENS in the agreement test below; any *new*
    accidental match would surface as a test failure and force a conscious
    decision to either rename the literal or extend the allow-list.
    """
    return set(re.findall(r"_[A-Za-z]+_", _read_template()))


def _collect_card_info_keys() -> set[str]:
    """Extract the literal string keys assigned into ``card_info`` inside
    crabby.py:make().  Uses the AST so it is robust to whitespace/comments
    and to extra dict mutations after the initial literal."""
    tree = ast.parse(_read_crabby_source())
    make_fn = next(
        (n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "make"),
        None,
    )
    assert make_fn is not None, "crabby.py is missing a top-level ``make`` function"

    keys: set[str] = set()
    for node in ast.walk(make_fn):
        # Initial literal:  card_info = {...}
        if (
            isinstance(node, ast.Assign)
            and any(
                isinstance(t, ast.Name) and t.id == "card_info" for t in node.targets
            )
            and isinstance(node.value, ast.Dict)
        ):
            for k in node.value.keys:
                if isinstance(k, ast.Constant) and isinstance(k.value, str):
                    keys.add(k.value)
        # Subsequent subscript assignments:  card_info["_publication_"] = ...
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Subscript)
            and isinstance(node.targets[0].value, ast.Name)
            and node.targets[0].value.id == "card_info"
        ):
            slice_node = node.targets[0].slice
            if isinstance(slice_node, ast.Constant) and isinstance(slice_node.value, str):
                keys.add(slice_node.value)
    return keys


# ---------------------------------------------------------------------------
# 1) Placeholder roundtrip
# ---------------------------------------------------------------------------
def test_template_tokens_match_card_info_keys():
    """Every placeholder in template_crab.py must be filled by crabby.make().

    Surfaces three failure modes loudly:
      * tokens in the template that make() does not fill   (left as literals)
      * keys in make() that the template does not consume  (silently dropped)
      * any *new* unintended ``_FOO_`` substring in the template
    """
    template_tokens = _collect_template_tokens()
    card_info_keys = _collect_card_info_keys()

    # Drop documented known-substring matches (e.g. ``_ALLOW_``).
    real_template_tokens = template_tokens - KNOWN_NON_PLACEHOLDER_TOKENS

    missing_in_card_info = real_template_tokens - card_info_keys
    missing_in_template = card_info_keys - template_tokens

    msg_parts = []
    if missing_in_card_info:
        msg_parts.append(
            "Template tokens with NO corresponding key in crabby.make().card_info "
            f"(these will be left as literals in the submitted CRAB config): "
            f"{sorted(missing_in_card_info)}"
        )
    if missing_in_template:
        msg_parts.append(
            "card_info keys that are NOT present in template_crab.py "
            f"(these are silently dropped during make()): {sorted(missing_in_template)}"
        )

    assert not msg_parts, "\n".join(msg_parts)


def test_known_non_placeholder_tokens_still_present():
    """Sanity: if ``_ALLOW_`` ever disappears from the template, drop it
    from the allow-list.  Catches stale documentation."""
    template_tokens = _collect_template_tokens()
    stale = KNOWN_NON_PLACEHOLDER_TOKENS - template_tokens
    assert not stale, (
        f"KNOWN_NON_PLACEHOLDER_TOKENS contains tokens no longer in the template: "
        f"{sorted(stale)}.  Remove them from the allow-list."
    )


# ---------------------------------------------------------------------------
# 2) Rendered file is valid Python
# ---------------------------------------------------------------------------
def _render_template(card_info: dict[str, str], verbatim_lines: list[str] | None = None) -> str:
    """Reproduce the substitution loop from crabby.make() in isolation."""
    rendered = _read_template()
    for line in verbatim_lines or []:
        rendered += "\n" + line
    rendered += "\n"
    for key, value in card_info.items():
        rendered = rendered.replace(key, value)
    return rendered


def test_rendered_template_compiles_as_python():
    rendered = _render_template(DUMMY_CARD_INFO_STR)
    try:
        compile(rendered, "submit_dummy.py", "exec")
    except SyntaxError as exc:
        pytest.fail(
            f"Rendered CRAB config is not valid Python: {exc}\n"
            f"--- rendered ---\n{rendered}\n----------------"
        )


def test_no_unsubstituted_original_placeholders_remain():
    """After a complete substitution none of the *original* template
    placeholders may remain.  This is narrower than ``no _X_ leftover``
    because realistic substituted values themselves can legitimately
    contain ``_X_`` substrings (e.g. ``T2_US_Purdue``, ``Run3_Tag_..``)
    which the naive grep would flag."""
    original_tokens = _collect_template_tokens() - KNOWN_NON_PLACEHOLDER_TOKENS
    rendered = _render_template(DUMMY_CARD_INFO_STR)
    still_present = {tok for tok in original_tokens if tok in rendered}
    assert not still_present, (
        f"Original placeholders still present after make(): {sorted(still_present)}"
    )


# ---------------------------------------------------------------------------
# 3) Verbatim line append behaviour
# ---------------------------------------------------------------------------
def test_test_mode_appends_total_units_once():
    """``--test True`` must append exactly one ``config.Data.totalUnits = 1``
    line on its own line."""
    verbatim = ["config.Data.totalUnits = 1"]
    rendered = _render_template(DUMMY_CARD_INFO_STR, verbatim_lines=verbatim)

    # Exactly one occurrence (no accidental duplication, no inline merge).
    count = rendered.count("config.Data.totalUnits = 1")
    assert count == 1, (
        f"Expected exactly one ``config.Data.totalUnits = 1`` line, got {count}."
    )

    # Must be on its own line, not concatenated to another statement.
    own_line_matches = [
        line
        for line in rendered.splitlines()
        if line.strip() == "config.Data.totalUnits = 1"
    ]
    assert len(own_line_matches) == 1, (
        "``config.Data.totalUnits = 1`` is present but not on its own line:\n"
        + rendered
    )


def test_data_mode_appends_units_and_runtime_lines():
    """For ``card['data']=True`` make() appends two extra lines."""
    verbatim = [
        "config.Data.unitsPerJob = 50",
        "config.JobType.maxJobRuntimeMin = 2750",
    ]
    rendered = _render_template(DUMMY_CARD_INFO_STR, verbatim_lines=verbatim)

    own_lines = {line.strip() for line in rendered.splitlines()}
    assert "config.Data.unitsPerJob = 50" in own_lines
    assert "config.JobType.maxJobRuntimeMin = 2750" in own_lines


# ---------------------------------------------------------------------------
# 4) _publication_ replacement semantics
# ---------------------------------------------------------------------------
def test_publication_renders_as_bare_bool_literal():
    """template_crab.py line 22 now reads:

        config.Data.publication = _publication_   # no surrounding quotes

    so crabby.make() substitutes the raw token ``False`` / ``True`` and
    the rendered line is a bare Python bool literal.  This is what CRAB's
    Python config DSL expects -- quoting the placeholder used to silently
    break ``--test True`` (non-empty strings are truthy, so CRAB
    published anyway).
    """
    card_info = dict(DUMMY_CARD_INFO_STR)
    card_info["_publication_"] = "False"
    rendered = _render_template(card_info)
    assert "config.Data.publication = False" in rendered, (
        "Expected ``config.Data.publication = False`` (bare bool literal).\n"
        f"Rendered line: "
        f"{[ln for ln in rendered.splitlines() if 'publication' in ln]}"
    )
    assert 'config.Data.publication = "False"' not in rendered


def test_crabby_make_passes_string_False_under_test_flag():
    """Spot-check the *source* of crabby.py to confirm that --test True
    actually sets ``card_info['_publication_'] = 'False'`` (string token).
    This pins down the contract the previous test relies on."""
    src = _read_crabby_source()
    assert 'card_info["_publication_"] = "False"' in src, (
        "crabby.py:make() no longer sets ``card_info['_publication_'] = 'False'`` "
        "under --test.  The publication test contract is broken."
    )


# ---------------------------------------------------------------------------
# 5) Integration smoke: call crabby.make() end-to-end and inspect the output
# ---------------------------------------------------------------------------
def _build_card(workarea: Path, *, data: bool) -> dict:
    return {
        "name": "dummy",
        "crab_template": str(TEMPLATE_PATH),
        "workArea": str(workarea),
        "storageSite": "T2_US_Purdue",
        "outLFNDirBase": "/store/user/dummy/x",
        "voGroup": None,
        "publication": True,
        "config": "configs/MC_2024_Scouting.py",
        "tag_extension": "DAZSLE_PFNano",
        "tag_mod": None,
        "data": data,
        "lumiMask": None,
    }


def test_crabby_make_test_mode_writes_valid_python(tmp_path):
    """End-to-end: --test=True must produce a syntactically valid Python
    file with the totalUnits line appended exactly once and no original
    placeholders left behind."""
    import crabby

    workarea = tmp_path / "wa"
    workarea.mkdir()
    card = _build_card(workarea, data=False)
    base_template = TEMPLATE_PATH.read_text()

    datasets = ["/DummyDS/Run3-MiniAOD/MINIAODSIM"]
    crabby.make(card, datasets, base_template, test=True)

    out = workarea / "submit_DummyDS_Run3-MiniAOD_MINIAODSIM.py"
    assert out.exists(), f"crabby.make did not write {out}"
    rendered = out.read_text()

    # totalUnits must be the test-mode line, exactly once, on its own line.
    assert rendered.count("config.Data.totalUnits = 1") == 1
    assert any(
        line.strip() == "config.Data.totalUnits = 1"
        for line in rendered.splitlines()
    )
    # Original placeholders all replaced (substring matches in real values
    # like ``T2_US_Purdue`` are allowed).
    original = _collect_template_tokens() - KNOWN_NON_PLACEHOLDER_TOKENS
    still_present = {tok for tok in original if tok in rendered}
    assert not still_present, f"Unsubstituted placeholders: {sorted(still_present)}"
    # Must be valid Python.
    compile(rendered, str(out), "exec")


def test_crabby_make_data_mode_appends_runtime_lines(tmp_path):
    """End-to-end: card['data']=True appends both unitsPerJob and the
    maxJobRuntimeMin lines."""
    import crabby

    workarea = tmp_path / "wa_data"
    workarea.mkdir()
    card = _build_card(workarea, data=True)
    base_template = TEMPLATE_PATH.read_text()

    datasets = ["/DummyData/Run3-Prompt/MINIAOD"]
    crabby.make(card, datasets, base_template, test=False)

    out = workarea / "submit_DummyData_Run3-Prompt_MINIAOD.py"
    assert out.exists()
    rendered = out.read_text()

    own_lines = {line.strip() for line in rendered.splitlines()}
    assert "config.Data.unitsPerJob = 50" in own_lines
    assert "config.JobType.maxJobRuntimeMin = 2750" in own_lines
    # Rendered file must still be valid Python.
    compile(rendered, str(out), "exec")
