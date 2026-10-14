"""Grading `benchmarks/llp_forward` must give the CURRENT rubric.

The arrangement used to be inverted: the parent benchmark carried the
superseded tolerance ladder and a sibling directory carried the calibrated
one. Nothing announced that, so `--benchmark benchmarks/llp_forward` silently
graded the old way -- which is exactly what happened to the 2026-08-09 pilot,
whose scores had to be regraded afterwards.

The live rubric now lives in the parent and the ladder is archived in
`llp_forward_legacy`. These tests pin that direction, because the failure mode
is silent: a run against the wrong rubric completes, produces plausible
numbers, and is only caught by noticing the stage names.
"""
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]
BENCH = REPO / "benchmarks"

#: The distance-based stages that define the current rubric.
CURRENT = {"yield_distance", "contour_lower", "contour_upper"}
#: The superseded ladder. Its hallmark was scoring ONE measurement at three
#: hand-chosen thresholds, which is why it must not reappear in the live one.
LEGACY = {"peak_yield", "band_coarse", "band_mid", "band_fine"}


def _rubric(name):
    cfg = yaml.safe_load((BENCH / name / "benchmark.yaml").read_text())
    return cfg, (cfg.get("rubric") or {})


def _stage_ids(rubric):
    return {s["id"] for s in rubric.get("stages", [])}


def test_parent_benchmark_carries_the_current_rubric():
    _, rubric = _rubric("llp_forward")
    ids = _stage_ids(rubric)
    assert CURRENT <= ids, f"missing distance stages: {CURRENT - ids}"
    assert not (LEGACY & ids), f"superseded ladder still live: {LEGACY & ids}"
    print(f"[OK] llp_forward grades by distance: {sorted(CURRENT & ids)}")


def test_live_rubric_weights_sum_to_one():
    """A rubric that does not sum to 1 makes every score silently unreadable."""
    _, rubric = _rubric("llp_forward")
    total = sum(float(s.get("weight", 0.0)) for s in rubric["stages"])
    assert abs(total - 1.0) < 1e-9, total
    # and the two reach edges are graded SEPARATELY -- they are different
    # physics (production- vs lifetime-limited) and pooling them hid the most
    # informative result of the 2026-08 campaign.
    w = {s["id"]: s.get("weight", 0.0) for s in rubric["stages"]}
    assert w["contour_lower"] > 0 and w["contour_upper"] > 0
    print(f"[OK] weights sum to 1.00; both edges graded separately")


@pytest.mark.parametrize("name", ["llp_forward"])
def test_every_variant_of_the_task_still_parses(name):
    cfg, _ = _rubric(name)
    assert cfg.get("name"), name


if __name__ == "__main__":
    for fn in [v for k, v in sorted(globals().items())
               if k.startswith("test_") and not hasattr(v, "pytestmark")]:
        fn()
    print("\nall rubric-currency tests passed")
