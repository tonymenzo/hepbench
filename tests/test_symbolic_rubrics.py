"""
# tests/test_symbolic_rubrics.py is a part of HEPBench.
# Copyright (C) 2026 HEPBench authors (see AUTHORS for details).
# HEPBench is licensed under the GNU GPL v3 or later, see LICENSE for details.
"""
"""
Self-grading tests for every benchmark under benchmarks/symbolic/: a
synthetic sandbox holding the ground truth's own values and formulas
must score 1.0 through the real toolbench judge, and an everything-
doubled sandbox must clear only the order-of-magnitude rungs. Picks up
new symbolic benchmarks automatically.
"""

import json
import re
from pathlib import Path

import pytest
from toolbench.core.benchmark import YamlBenchmark
from toolbench.core.checks import load_benchmark_checks, merged_registry
from toolbench.core.judge import RuleJudge
from toolbench.core.trajectory import Trajectory

ROOT = Path(__file__).resolve().parents[1]
SYMBOLIC = ROOT / "benchmarks" / "symbolic"
BENCH_DIRS = sorted(p.parent for p in SYMBOLIC.glob("*/benchmark.yaml"))

# Fields graded only on the log10 rung in some families may not exist;
# everything is driven off truth.json so this stays generic.


def _grade(bench_dir: Path, sandbox: Path):
    bench = YamlBenchmark(bench_dir)
    registry = merged_registry(load_benchmark_checks(bench.checks_module_path()))
    judge = RuleJudge(registry=registry, benchmark_dir=str(bench.BENCHMARK_DIR))
    return judge.grade(Trajectory(), bench.rubric, str(sandbox))


def _truth_fields(bench_dir: Path) -> dict:
    truth = json.loads((bench_dir / "ground_truth" / "truth.json").read_text())
    return {k: v for k, v in truth.items() if not k.startswith("_")}


@pytest.mark.parametrize("bench_dir", BENCH_DIRS, ids=lambda p: p.name)
def test_perfect_answer_scores_one(bench_dir, tmp_path):
    sandbox = tmp_path / "sandbox"
    (sandbox / "results").mkdir(parents=True)
    (sandbox / "results" / "answer.json").write_text(
        json.dumps(_truth_fields(bench_dir)))
    grade = _grade(bench_dir, sandbox)
    failed = [s.id + ": " + s.evidence
              for s in grade.stage_grades if not s.passed]
    assert grade.score == pytest.approx(1.0), failed


@pytest.mark.parametrize("bench_dir", BENCH_DIRS, ids=lambda p: p.name)
def test_doubled_values_clear_only_coarse_rungs(bench_dir, tmp_path):
    fields = _truth_fields(bench_dir)
    doubled = {k: (2 * v if isinstance(v, (int, float)) else v)
               for k, v in fields.items()}
    sandbox = tmp_path / "sandbox"
    (sandbox / "results").mkdir(parents=True)
    (sandbox / "results" / "answer.json").write_text(json.dumps(doubled))
    grade = _grade(bench_dir, sandbox)
    for s in grade.stage_grades:
        if "within" in s.id:
            assert not s.passed, f"{s.id} passed with doubled values"
        if "order_of_magnitude" in s.id:
            assert s.passed, f"{s.id} failed: {s.evidence}"


@pytest.mark.parametrize("bench_dir", BENCH_DIRS, ids=lambda p: p.name)
def test_empty_sandbox_scores_zero(bench_dir, tmp_path):
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    grade = _grade(bench_dir, sandbox)
    assert grade.score == 0.0


@pytest.mark.parametrize("bench_dir", BENCH_DIRS, ids=lambda p: p.name)
def test_only_answer_present_gates(bench_dir):
    """`answer_present` is the sole prerequisite; the rest are independent.

    Absorption models "stage N presupposes stage N-1", which is true of a
    pipeline benchmark but false here: parts (a)/(b)/(c) are separate
    calculations. Leaving them gating silently zeroes correct work — a
    real gpt-oss-120b trial with all three values exact and two formulas
    rejected on a technicality scored 0.22 instead of 1.00.
    """
    stages = YamlBenchmark(bench_dir).rubric.stages
    gating = [s["id"] for s in stages if s.get("gating", True)]
    assert gating == ["answer_present"], (
        f"expected answer_present to be the only gating stage, got {gating}")


@pytest.mark.parametrize("bench_dir", BENCH_DIRS, ids=lambda p: p.name)
def test_one_bad_field_costs_only_its_own_stages(bench_dir, tmp_path):
    """Corrupting one answer field must not zero the others.

    The property the previous tests could not see: `perfect` has no
    failure to absorb, and `doubled` inspects per-stage flags rather than
    the score. This one pins the score itself.
    """
    fields = _truth_fields(bench_dir)
    target = next((k for k in fields if isinstance(fields[k], str)), None)
    if target is None:                       # values-only benchmark
        target = next(iter(fields))
    broken = dict(fields)
    broken[target] = ("mS + 1" if isinstance(fields[target], str)
                      else float(fields[target]) * 1e6)

    sandbox = tmp_path / "sandbox"
    (sandbox / "results").mkdir(parents=True)
    (sandbox / "results" / "answer.json").write_text(json.dumps(broken))
    grade = _grade(bench_dir, sandbox)

    lost = sum(s.weight for s in grade.stage_grades if not s.passed)
    assert grade.score == pytest.approx(1.0 - lost, abs=1e-6), (
        f"corrupting {target!r} cost {1.0 - grade.score:.3f} of reach but only "
        f"{lost:.3f} of stage weight failed — an independent stage was absorbed"
    )
    assert grade.score > 0.0


@pytest.mark.parametrize("bench_dir", BENCH_DIRS, ids=lambda p: p.name)
def test_rubric_weights_sum_to_one(bench_dir):
    bench = YamlBenchmark(bench_dir)
    total = sum(float(s.get("weight", 0.0)) for s in bench.rubric.stages)
    assert total == pytest.approx(1.0, abs=1e-9)


# --------------------------------------------------------------------
# Leakage guard.
#
# A prompt may state the task's INPUTS (Lagrangians, couplings, masses)
# but must never state a graded ANSWER. The test is tolerance-based
# rather than textual: a prompt leaks if some numeric literal in it
# would clear the tightest rel_tol rung the rubric grades that answer
# field on -- i.e. if copying a number out of the prompt scores points.
#
# This exists because the shared system.md once carried a worked JSON
# example whose value (23.46) was decay_S_to_FFbar's real part-(a)
# width to 2e-4, handing over 0.18 of reach on that benchmark.
# --------------------------------------------------------------------

# Sci-notation first so "1.2e-3" is not read as "1.2" then "3".
_NUMBER = re.compile(r"\d+\.?\d*[eE][+-]?\d+|\d+\.\d+|\d+")
# rel_tol floor used for fields the rubric only grades on a log10 rung.
_DEFAULT_TOL = 0.01
# Stating an answer means stating it to answer-like precision. Bare
# 1-2 digit literals are exponents, part labels and LaTeX subscripts;
# scanning them produces coincidences (decay_S_to_SS's true width is
# 1.98, so the "2" in every "^2" would trip a naive scan) rather than
# leaks. Three significant digits is the floor for "this is a value".
_MIN_SIG_DIGITS = 3


def _sig_digits(literal: str) -> int:
    mantissa = re.split(r"[eE]", literal)[0].replace(".", "").lstrip("0")
    return len(mantissa)


def _prompt_files(bench_dir: Path):
    for variant in sorted((bench_dir / "variants").iterdir()):
        for name in ("user.md", "system.md"):
            path = variant / "prompts" / name
            if path.is_file():
                yield f"{variant.name}/{name}", path.read_text()


def _tightest_rel_tols(bench_dir: Path) -> dict:
    """field -> tightest rel_tol the rubric grades that field on."""
    tols = {}
    for stage in YamlBenchmark(bench_dir).rubric.stages:
        for check in stage.get("checks", []):
            params = check.get("answer_value")
            if not params:
                continue
            field = params.get("ref_field", params["field"])
            tol = float(params.get("rel_tol", _DEFAULT_TOL))
            tols[field] = min(tols.get(field, tol), tol)
    return tols


@pytest.mark.parametrize("bench_dir", BENCH_DIRS, ids=lambda p: p.name)
def test_prompts_never_state_a_graded_answer(bench_dir):
    truth = _truth_fields(bench_dir)
    tols = _tightest_rel_tols(bench_dir)
    numeric = {k: float(v) for k, v in truth.items()
               if isinstance(v, (int, float)) and not isinstance(v, bool)
               and float(v) != 0.0}
    formulas = {k: re.sub(r"\s+", "", v) for k, v in truth.items()
                if isinstance(v, str) and v.strip()}

    leaks = []
    for where, text in _prompt_files(bench_dir):
        squashed = re.sub(r"\s+", "", text)
        for field, expr in formulas.items():
            if expr in squashed:
                leaks.append(f"{where}: ground-truth formula {field!r} "
                             f"appears verbatim")
        literals = [float(m) for m in _NUMBER.findall(text)
                    if _sig_digits(m) >= _MIN_SIG_DIGITS]
        for field, value in numeric.items():
            tol = tols.get(field, _DEFAULT_TOL)
            hits = [x for x in literals
                    if abs(x - value) <= tol * abs(value)]
            if hits:
                leaks.append(
                    f"{where}: literal {hits[0]:.6g} is within the graded "
                    f"rel_tol {tol} of {field}={value:.6g}")
    assert not leaks, "prompt states a graded answer:\n  " + "\n  ".join(leaks)
