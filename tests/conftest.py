"""
Shared pytest fixtures.

`crabby.py` does `from CRABAPI.RawCommand import crabCommand` at module top.
That import requires a CMSSW environment (with crab-setup.sh sourced) which is
not present in a vanilla CI / dev shell. We stub it out *before* anyone imports
`crabby` so the module can load.

We also stub `http.client.HTTPException` users? -> no, that's stdlib, fine.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest


# --- Stub CRABAPI before any test imports crabby ------------------------------
# Must happen at conftest import time, which is before test collection imports.
if "CRABAPI" not in sys.modules:
    crabapi_stub = MagicMock()
    crabapi_stub.RawCommand = MagicMock()
    crabapi_stub.RawCommand.crabCommand = MagicMock()
    sys.modules["CRABAPI"] = crabapi_stub
    sys.modules["CRABAPI.RawCommand"] = crabapi_stub.RawCommand


# --- Make the repo root importable -------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """Absolute path to the harness root (the dir containing crabby.py)."""
    return REPO_ROOT


@pytest.fixture(scope="session")
def datasets_dir(repo_root: Path) -> Path:
    return repo_root / "datasets"


@pytest.fixture(scope="session")
def template_crab_text(repo_root: Path) -> str:
    return (repo_root / "template_crab.py").read_text()
