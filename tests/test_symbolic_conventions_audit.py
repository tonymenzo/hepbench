"""
# tests/test_symbolic_conventions_audit.py is a part of HEPBench.
# Copyright (C) 2026 HEPBench authors (see AUTHORS for details).
# HEPBench is licensed under the GNU GPL v3 or later, see LICENSE for details.
"""
"""
Conventions audit: re-run every benchmarks/symbolic/*/ground_truth/
derivation.py and confirm it still succeeds. Each derivation asserts
internally that its committed analytic formulas reproduce an independent
numeric computation from _shared/dirac_numeric.py (the executable
encoding of CONVENTIONS.md), so a green run here is a proof that the
whole family is mutually consistent with the documented conventions.
Auto-discovers new archetypes.
"""

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SYMBOLIC = ROOT / "benchmarks" / "symbolic"
DERIVATIONS = sorted(SYMBOLIC.glob("*/ground_truth/derivation.py"))


def test_conventions_doc_exists():
    assert (SYMBOLIC / "CONVENTIONS.md").is_file()


@pytest.mark.parametrize("script", DERIVATIONS,
                         ids=lambda p: p.parent.parent.name)
def test_derivation_reproduces_numeric(script):
    """Each derivation re-derives ground truth and asserts analytic ==
    numeric to its stated tolerance; a nonzero exit means a convention
    drift between the analytic formula and dirac_numeric.py.

    Run in place: the derivation depends on `_shared/dirac_numeric.py` via
    a relative path and writes a deterministic `truth.json` next to
    itself, so re-running regenerates identical bytes (no repo mutation)."""
    res = subprocess.run([sys.executable, str(script)],
                         capture_output=True, text=True, timeout=300)
    assert res.returncode == 0, (
        f"{script.parent.parent.name} derivation failed "
        f"(convention drift?):\n{res.stdout}\n{res.stderr}")
    assert "wrote" in res.stdout.lower()
