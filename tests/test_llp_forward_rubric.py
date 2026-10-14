"""
# tests/test_llp_forward_rubric.py is a part of HEPBench.
# Copyright (C) 2026 HEPBench authors (see AUTHORS for details).
# HEPBench is licensed under the GNU GPL v3 or later, see LICENSE for details.
"""
"""Structural invariants of the `benchmarks/llp_forward` rubric.

The rubric grades by calibrated distance: a yield stage and one stage per
reach-contour edge. A run against a rubric missing one of them completes and
produces plausible numbers, so the stage set, the weights and the parse of
the task are pinned here.
"""
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]
BENCH = REPO / "benchmarks"

#: The distance-based stages that define the rubric.
DISTANCE = {"yield_distance", "contour_lower", "contour_upper"}


def _rubric(name):
    cfg = yaml.safe_load((BENCH / name / "benchmark.yaml").read_text())
    return cfg, (cfg.get("rubric") or {})


def _stage_ids(rubric):
    return {s["id"] for s in rubric.get("stages", [])}


def test_benchmark_carries_the_distance_stages():
    _, rubric = _rubric("llp_forward")
    ids = _stage_ids(rubric)
    assert DISTANCE <= ids, f"missing distance stages: {DISTANCE - ids}"


def test_rubric_weights_sum_to_one():
    """A rubric that does not sum to 1 makes every score silently unreadable."""
    _, rubric = _rubric("llp_forward")
    total = sum(float(s.get("weight", 0.0)) for s in rubric["stages"])
    assert abs(total - 1.0) < 1e-9, total
    # The two reach edges are graded separately: they are different physics
    # (production- vs lifetime-limited) and pooling them hides the difference.
    w = {s["id"]: s.get("weight", 0.0) for s in rubric["stages"]}
    assert w["contour_lower"] > 0 and w["contour_upper"] > 0


@pytest.mark.parametrize("name", ["llp_forward"])
def test_benchmark_parses(name):
    cfg, _ = _rubric(name)
    assert cfg.get("name"), name
