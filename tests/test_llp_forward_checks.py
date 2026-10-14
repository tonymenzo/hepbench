"""
# tests/test_llp_forward_checks.py is a part of HEPBench.
# Copyright (C) 2026 HEPBench authors (see AUTHORS for details).
# HEPBench is licensed under the GNU GPL v3 or later, see LICENSE for details.
"""
"""
Self-grading tests for the llp_forward rubric.

A synthetic sandbox assembled from the ground truth's own values must score ~1.0
through the real toolbench judge; degraded variants of it must lose credit at the
specific stage responsible; and an empty sandbox must score 0. This is the
offline validation that has to hold before a campaign spends tokens, and it is
what catches a rubric whose stages do not measure what they claim.

The graded deliverable is `results/answer.json` (width formula and probe scalars)
plus `results/scan.csv`, a flat table of N_sig over the coupling per
(search, m_phi), plus the requested `results/reach.pdf`. The grader reduces the
scan to a band itself, so a perfect submission is one whose N_sig(g) crosses the
sensitivity threshold exactly at the reference band edges.

An earlier version of this module globbed `llp_forward/*/benchmark.yaml`, a
nested layout this flat family does not use. It matched nothing, collected zero
cases, and passed green while testing nothing at all.
"""

import json
import math
from pathlib import Path

import pytest
import yaml

from toolbench.core.benchmark import YamlBenchmark
from toolbench.core.checks import load_benchmark_checks, merged_registry
from toolbench.core.judge import RuleJudge
from toolbench.core.trajectory import Trajectory

ROOT = Path(__file__).resolve().parents[1]
FAMILY = ROOT / "benchmarks" / "llp_forward"

ANSWER_KEYS = ["width_formula_mumu", "width_probe_gev",
               "width_gg_probe_gev", "ctau_probe_m"]


def _truth_path(bench_dir: Path) -> Path:
    cfg = yaml.safe_load((bench_dir / "benchmark.yaml").read_text())
    rel = ((cfg.get("ground_truth") or {}).get("dir") or "ground_truth")
    return bench_dir / rel.lstrip("./") / "truth.json"


# Accept both the nested layout (one directory per benchmark) and the flat one
# this family uses, locating the truth wherever benchmark.yaml declares it.
BENCH_DIRS = sorted(
    {p.parent for p in list(FAMILY.glob("*/benchmark.yaml"))
     + list(FAMILY.glob("benchmark.yaml"))
     if _truth_path(p.parent).is_file()})


def _truth(bench_dir: Path) -> dict:
    return json.loads(_truth_path(bench_dir).read_text())


def _grade(bench_dir: Path, sandbox: Path):
    bench = YamlBenchmark(bench_dir)
    registry = merged_registry(load_benchmark_checks(bench.checks_module_path()))
    judge = RuleJudge(registry=registry, benchmark_dir=bench.search_dirs)
    return judge.grade(Trajectory(), bench.rubric, str(sandbox))


def _curve(band, peak, target, n=81):
    """A N_sig(g) curve crossing `target` exactly at the reference band edges.

    Log-parabolic in (log g, log N): pinned to `target` at both edges and to
    `peak` at their geometric mean. That is the shape a real scan has -- a
    steep rise, a maximum, then the decay-length collapse -- and it is what the
    grader's linear interpolation in (log g, N_sig) has to resolve.
    """
    lo, hi = float(band[0]), float(band[1])
    x0, x1 = math.log10(lo), math.log10(hi)
    xm = 0.5 * (x0 + x1)
    A = (math.log10(target) - math.log10(peak)) / (x0 - xm) ** 2
    span = x1 - x0
    pts = []
    for i in range(n):
        x = (x0 - 0.35 * span) + (1.7 * span) * i / (n - 1)
        pts.append((10 ** x, 10 ** (A * (x - xm) ** 2 + math.log10(peak))))
    return pts


def _null_curve(peak, n=41):
    """A curve for a mass the reference does not reach: peaks below threshold."""
    pts = []
    for i in range(n):
        x = -9.0 + 6.0 * i / (n - 1)
        pts.append((10 ** x, peak * math.exp(-((x + 6.0) ** 2) / 2.0)))
    return pts


def _write_sandbox(tmp_path: Path, truth: dict, *, answer=None,
                   drop_search=None, spurious=False, scan=True) -> Path:
    sandbox = tmp_path / "sandbox"
    (sandbox / "results").mkdir(parents=True)
    (sandbox / "flux").mkdir(parents=True, exist_ok=True)
    (sandbox / "flux" / "events.cmnd").write_text("! pythia flux artifact\n")

    if answer is None:
        answer = {k: truth[k] for k in ANSWER_KEYS}
    (sandbox / "results" / "answer.json").write_text(json.dumps(answer))
    if not scan:
        return sandbox

    target = float(truth.get("n_target", 3.0))

    # The rubric grades TWO different things off this one file: the reach
    # CONTOUR (needs a dense curve either side of the crossings) and the point
    # YIELDS at the reference's own declared (search, m, g) points. A curve
    # pinned only to the band edges satisfies the first and misses the second
    # by ~0.6 dex, so "perfect" has to mean both: the parabola supplies the
    # density, and truth's declared points are overlaid at their exact
    # couplings. They describe the same curve, so overlaying is consistent --
    # the declared points sit in the interior, away from the crossings the
    # contour check resolves.
    declared = {}
    for p in truth.get("points", []):
        key = (str(p["search"]), round(float(p["m_phi"]), 6))
        declared.setdefault(key, {})[float(p["g"])] = float(p["nsig"])

    rows = ["search,m_phi,g,nsig"]
    for r in truth["_per_mass"]:
        search, m = str(r["search"]), float(r["m"])
        if drop_search and search == drop_search:
            continue
        band, peak = r.get("band"), r.get("peak")
        if band and band[0]:
            pts = _curve(band, peak, target)
        elif peak:
            # A mass the reference does not reach. `spurious` invents a band
            # here, which only the no-spurious-reach mirror can see.
            pts = (_curve([1e-6, 1e-3], 50 * target, target) if spurious
                   else _null_curve(min(float(peak), target * 0.5)))
        else:
            continue
        exact = declared.get((search, round(m, 6)), {})
        merged = {float(g): float(n) for g, n in pts}
        merged.update(exact)                     # reference values win
        for g in sorted(merged):
            rows.append(f"{search},{m},{g:.9g},{merged[g]:.9g}")
    (sandbox / "results" / "scan.csv").write_text("\n".join(rows) + "\n")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots()
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.fill_between([0.06, 0.3], [1e-6, 1e-6], [1e-3, 1e-3], alpha=0.5)
    ax.plot([0.06, 0.3], [1e-6, 1e-3])
    ax.set_xlabel("m_phi [GeV]")
    ax.set_ylabel("g")
    fig.savefig(sandbox / "results" / "reach.pdf")
    plt.close(fig)
    return sandbox


@pytest.mark.parametrize("bench_dir", BENCH_DIRS, ids=lambda p: p.name)
def test_perfect_answer_scores_one(bench_dir, tmp_path):
    """Truth's own values, submitted as a deliverable, must earn full credit."""
    truth = _truth(bench_dir)
    grade = _grade(bench_dir, _write_sandbox(tmp_path, truth))
    failed = [f"{s.id}: {s.evidence}" for s in grade.stage_grades if not s.passed]
    assert grade.score > 0.95, (round(grade.score, 4), failed)


@pytest.mark.parametrize("bench_dir", BENCH_DIRS, ids=lambda p: p.name)
def test_empty_sandbox_scores_zero(bench_dir, tmp_path):
    """No deliverable: the structural gate absorbs and nothing is earned."""
    sandbox = tmp_path / "sandbox"
    (sandbox / "results").mkdir(parents=True)
    grade = _grade(bench_dir, sandbox)
    assert grade.score == pytest.approx(0.0), grade.score


@pytest.mark.parametrize("bench_dir", BENCH_DIRS, ids=lambda p: p.name)
def test_dropped_channel_loses_completeness(bench_dir, tmp_path):
    """A whole search silently missing must be caught by channel completeness.

    This is precisely the failure the band ladder is blind to: it iterates over
    reference bands, so a channel absent from the submission is never visited.
    """
    truth = _truth(bench_dir)
    grade = _grade(bench_dir, _write_sandbox(tmp_path, truth, drop_search="gg"))
    assert not grade.stages["channels_present"], \
        "a dropped search passed channel completeness"
    # The distance stages must FAIL on coverage too, not just report a good
    # median over the half that was submitted.
    for stage in ("yield_distance", "contour_lower", "contour_upper"):
        assert not grade.stages[stage], \
            f"{stage} passed despite a whole search channel being absent"

    # HOW MUCH it costs is deliberately asserted loosely, because the answer
    # is uncomfortable: ~0.955. `_standardise` prices coverage in its
    # pass/fail boolean but computes 10^-D over the points that WERE covered,
    # so an agent that submits only one of two searches keeps almost all of
    # its continuous credit and loses mainly `channels_present` (weight 0.10).
    # Dropping half the task for ~4.5% is arguably too cheap; changing it means
    # reweighting every score in the campaign, so it is recorded here rather
    # than quietly altered. Tighten this bound if that decision is taken.
    assert grade.score < 0.97, grade.score


@pytest.mark.parametrize("bench_dir", BENCH_DIRS, ids=lambda p: p.name)
def test_spurious_band_is_penalised(bench_dir, tmp_path):
    """Claiming reach where the reference has none must cost credit."""
    truth = _truth(bench_dir)
    grade = _grade(bench_dir, _write_sandbox(tmp_path, truth, spurious=True))
    assert not grade.stages["no_spurious_reach"], \
        "an invented exclusion band passed the spurious-reach mirror"


@pytest.mark.parametrize("bench_dir", BENCH_DIRS, ids=lambda p: p.name)
def test_hidden_probes_never_in_task_materials(bench_dir, tmp_path):
    """No graded reference value may be readable from prompts or the sandbox."""
    truth = _truth(bench_dir)
    needles = [f"{truth['width_probe_gev']:.6e}"[:8],
               f"{truth['width_gg_probe_gev']:.6e}"[:8]]
    corpus = []
    for pat in ("variants/*/prompts/*.md", "variants/*/sandbox/template/**/*"):
        for f in bench_dir.glob(pat):
            if f.is_file() and f.suffix in (".md", ".yaml", ".json", ".csv",
                                            ".txt", ".cmnd", ".tex"):
                corpus.append(f.read_text(errors="replace"))
    blob = "\n".join(corpus)
    for needle in needles:
        assert needle not in blob, \
            f"graded probe value {needle} leaked into the task materials"
