"""
# tests/test_symbolic_checks.py is a part of HEPBench.
# Copyright (C) 2026 HEPBench authors (see AUTHORS for details).
# HEPBench is licensed under the GNU GPL v3 or later, see LICENSE for details.
"""
"""
Unit tests for benchmarks/symbolic/_shared/checks.py, exercised through
toolbench's own dispatch (`run_check` + `load_benchmark_checks`) so the
registration contract is covered too.
"""

import json
from pathlib import Path

import pytest
from toolbench.core.checks import load_benchmark_checks, run_check

SHARED = (Path(__file__).resolve().parents[1]
          / "benchmarks" / "symbolic" / "_shared" / "checks.py")
REGISTRY = load_benchmark_checks(SHARED)


@pytest.fixture()
def bench(tmp_path):
    """A throwaway benchmark dir (ground truth) + sandbox pair."""
    bench_dir = tmp_path / "bench"
    (bench_dir / "ground_truth").mkdir(parents=True)
    sandbox = tmp_path / "sandbox"
    (sandbox / "results").mkdir(parents=True)

    truth = {
        "width_gev": 12.5,
        "width_formula": "y**2 * mS * (1 - 4*mf**2/mS**2)**(3/2) / (8*pi)",
    }
    (bench_dir / "ground_truth" / "truth.json").write_text(json.dumps(truth))

    def write_answer(obj):
        (sandbox / "results" / "answer.json").write_text(json.dumps(obj))

    def check(name, params):
        merged = {"file": "results/answer.json",
                  "reference": "ground_truth/truth.json", **params}
        return run_check(name, sandbox, merged,
                         benchmark_dir=bench_dir, registry=REGISTRY)

    return write_answer, check


SYMS = {"y": [0.1, 2.0], "mS": [500.0, 3000.0], "mf": [1.0, 200.0]}


def test_value_rel_tol(bench):
    write, check = bench
    write({"width_gev": 12.6})
    ok, msg = check("answer_value", {"field": "width_gev", "rel_tol": 0.05})
    assert ok, msg
    ok, _ = check("answer_value", {"field": "width_gev", "rel_tol": 0.001})
    assert not ok


def test_value_log10_tol(bench):
    write, check = bench
    write({"width_gev": 30.0})  # x2.4 off: fails 10%, passes order-of-mag
    ok, _ = check("answer_value", {"field": "width_gev", "rel_tol": 0.10})
    assert not ok
    ok, msg = check("answer_value", {"field": "width_gev", "log10_tol": 0.5})
    assert ok, msg


def test_value_missing_and_malformed(bench):
    write, check = bench
    ok, msg = check("answer_value", {"field": "width_gev"})
    assert not ok and "missing file" in msg
    write({"other": 1.0})
    ok, msg = check("answer_value", {"field": "width_gev"})
    assert not ok and "missing" in msg
    write({"width_gev": "twelve"})
    ok, msg = check("answer_value", {"field": "width_gev"})
    assert not ok and "not numeric" in msg


def test_formula_equivalent_form_passes(bench):
    write, check = bench
    # Algebraically equivalent rearrangement (sqrt instead of **(3/2)).
    write({"width_formula":
           "(y^2 * mS / (8*pi)) * sqrt(1 - 4*mf^2/mS^2)**3"})
    ok, msg = check("answer_formula",
                    {"field": "width_formula", "symbols": SYMS})
    assert ok, msg


def test_formula_wrong_factor_fails(bench):
    write, check = bench
    write({"width_formula":
           "y**2 * mS * (1 - 4*mf**2/mS**2)**(3/2) / (16*pi)"})
    ok, _ = check("answer_formula",
                  {"field": "formula", "symbols": SYMS,
                   "ref_field": "width_formula"})
    assert not ok  # missing field
    write({"width_formula":
           "y**2 * mS * (1 - 4*mf**2/mS**2)**(3/2) / (16*pi)"})
    ok, msg = check("answer_formula",
                    {"field": "width_formula", "symbols": SYMS})
    assert not ok and "disagrees" in msg


def test_formula_wrong_power_fails(bench):
    write, check = bench
    write({"width_formula":
           "y**2 * mS * (1 - 4*mf**2/mS**2)**(1/2) / (8*pi)"})
    ok, _ = check("answer_formula",
                  {"field": "width_formula", "symbols": SYMS})
    assert not ok


def test_formula_unknown_symbol_rejected(bench):
    write, check = bench
    write({"width_formula": "g**2 * mS / (8*pi)"})
    ok, msg = check("answer_formula",
                    {"field": "width_formula", "symbols": SYMS})
    assert not ok and "unknown symbols" in msg


def test_formula_injection_rejected(bench):
    write, check = bench
    for evil in ("__import__('os').system('true')",
                 "y.__class__",
                 "open('/etc/passwd')"):
        write({"width_formula": evil})
        ok, _ = check("answer_formula",
                      {"field": "width_formula", "symbols": SYMS})
        assert not ok


def test_formula_constraints(bench):
    write, check = bench
    write({"width_formula":
           "y**2 * mS * (1 - 4*mf**2/mS**2)**(3/2) / (8*pi)"})
    syms = {"y": [0.1, 2.0], "mS": [100.0, 3000.0], "mf": [1.0, 200.0]}
    ok, msg = check("answer_formula",
                    {"field": "width_formula", "symbols": syms,
                     "constraints": ["mS - 2*mf"]})
    assert ok, msg


def test_consistency(bench):
    write, check = bench
    write({"br_a": 0.6, "br_b": 0.3, "br_c": 0.1, "name": "x"})
    ok, msg = check("answer_consistency",
                    {"expr": "br_a + br_b + br_c", "equals": 1.0})
    assert ok, msg
    write({"br_a": 0.6, "br_b": 0.3, "br_c": 0.3})
    ok, _ = check("answer_consistency",
                  {"expr": "br_a + br_b + br_c", "equals": 1.0})
    assert not ok


def test_roles_exported():
    import importlib.util
    spec = importlib.util.spec_from_file_location("symbolic_checks", SHARED)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert set(mod.ROLES) == set(mod.CHECKS)
    assert all(v in ("presence", "correctness") for v in mod.ROLES.values())


# ---------------------------------------------------------------------------
# `fixed:` — symbols the TASK pins to a constant.
#
# A part that specialises a mass to zero (a massless daughter) declares only
# the symbols it varies, and `_parse_formula` admits nothing else. Without
# `fixed`, the two correct ways of answering would grade differently:
#
#   declare "mass": 0        -> tool returns the specialised form  -> passes
#   keep it symbolic, values -> tool returns the GENERAL form      -> rejected
#                               {..., "mS": 0}                        unparsed
#
# Both are right and both give the exact number, and the tools arm naturally
# returns the general form, so the asymmetry would bias a tools-vs-core
# comparison on every massless-daughter part (decay_V_to_SVp/b,
# decay_S_to_SpV/b, decay_V_to_SS/b).
#
# `fixed` makes the rubric STATE the specialisation instead of implying it by
# omission: the symbol is admissible in either formula and substituted before
# sampling, so the general answer is evaluated at the point the task actually
# asks about.
# ---------------------------------------------------------------------------

GEN_SYMS = {"y": [0.1, 2.0], "mS": [500.0, 3000.0]}


@pytest.fixture()
def massless_bench(tmp_path):
    """Ground truth SPECIALISED to mf = 0, as a massless-daughter part is."""
    bench_dir = tmp_path / "bench"
    (bench_dir / "ground_truth").mkdir(parents=True)
    sandbox = tmp_path / "sandbox"
    (sandbox / "results").mkdir(parents=True)
    truth = {"width_formula": "y**2 * mS / (8*pi)"}     # the mf -> 0 limit
    (bench_dir / "ground_truth" / "truth.json").write_text(json.dumps(truth))

    def write_answer(obj):
        (sandbox / "results" / "answer.json").write_text(json.dumps(obj))

    def check(name, params):
        merged = {"file": "results/answer.json",
                  "reference": "ground_truth/truth.json", **params}
        return run_check(name, sandbox, merged,
                         benchmark_dir=bench_dir, registry=REGISTRY)
    return write_answer, check


GENERAL = "y**2 * mS * (1 - 4*mf**2/mS**2)**(3/2) / (8*pi)"


def test_general_formula_is_rejected_without_fixed(massless_bench):
    """The current behaviour, pinned so the change is visible: an undeclared
    symbol makes the answer unparseable, not merely wrong."""
    write, check = massless_bench
    write({"width_formula": GENERAL})
    ok, msg = check("answer_formula",
                    {"field": "width_formula", "symbols": GEN_SYMS})
    assert not ok


def test_general_formula_passes_when_the_task_pins_the_symbol(massless_bench):
    """THE FIX. mf is fixed at 0 by the task, so the general form is evaluated
    there and agrees with the specialised ground truth."""
    write, check = massless_bench
    write({"width_formula": GENERAL})
    ok, msg = check("answer_formula",
                    {"field": "width_formula", "symbols": GEN_SYMS,
                     "fixed": {"mf": 0.0}})
    assert ok, msg


def test_the_specialised_formula_still_passes_with_fixed(massless_bench):
    """Both styles must grade the same. This is the whole point."""
    write, check = massless_bench
    write({"width_formula": "y**2 * mS / (8*pi)"})
    ok, msg = check("answer_formula",
                    {"field": "width_formula", "symbols": GEN_SYMS,
                     "fixed": {"mf": 0.0}})
    assert ok, msg


def test_fixed_does_not_excuse_a_wrong_formula(massless_bench):
    """Pinning a symbol must not weaken the test on the sampled ones."""
    write, check = massless_bench
    write({"width_formula": "y**2 * mS * (1 - 4*mf**2/mS**2)**(3/2) / (16*pi)"})
    ok, msg = check("answer_formula",
                    {"field": "width_formula", "symbols": GEN_SYMS,
                     "fixed": {"mf": 0.0}})
    assert not ok and "disagrees" in msg


def test_fixed_catches_a_formula_wrong_at_the_pinned_value(massless_bench):
    """Wrong in the mf dependence such that it misses at mf = 0."""
    write, check = massless_bench
    write({"width_formula": "y**2 * mS * (1 + mf/mS) / (8*pi) + mf"})
    ok, msg = check("answer_formula",
                    {"field": "width_formula", "symbols": GEN_SYMS,
                     "fixed": {"mf": 1.0}})
    assert not ok


def test_absent_fixed_is_unchanged(bench):
    """Every existing stage passes no `fixed`; behaviour must be identical."""
    write, check = bench
    write({"width_formula": "y**2 * mS * (1 - 4*mf**2/mS**2)**(3/2) / (8*pi)"})
    ok, msg = check("answer_formula",
                    {"field": "width_formula", "symbols": SYMS})
    assert ok, msg


def test_an_undeclared_symbol_is_named_in_the_message(massless_bench):
    """The rejection names the symbol that was not declared and says that
    `fixed` is how a task pins one, instead of reading like a syntax error."""
    write, check = massless_bench
    write({"width_formula": GENERAL})
    ok, msg = check("answer_formula",
                    {"field": "width_formula", "symbols": GEN_SYMS})
    assert not ok
    assert "mf" in msg, msg
    assert "fixed" in msg.lower(), msg


def test_fixed_may_pin_several_symbols(massless_bench):
    write, check = massless_bench
    write({"width_formula":
           "y**2 * mS * (1 - 4*mf**2/mS**2)**(3/2) / (8*pi) + 0*mX"})
    ok, msg = check("answer_formula",
                    {"field": "width_formula", "symbols": GEN_SYMS,
                     "fixed": {"mf": 0.0, "mX": 0.0}})
    assert ok, msg


# ---------------------------------------------------------------------------
# `conjugate` belongs in the formula alphabet.
#
# The eda tools emit it: unless `assume_real_couplings` is set, `width_formula`
# comes back as `g*sqrt(...)*(...)*Conjugate(g)/(16*pi*mS**3)` -- that is
# |g|^2, which for the real couplings these tasks specify is exactly g^2. An
# agent that copies the tool's own output into answer.json was then marked
# wrong on the alphabet: 15 trials across five tasks in the 2026-10 campaigns,
# seven of them on decay_F_to_FpV alone, every one numerically identical to the
# ground truth.
#
# This is the same correction `Rational(3,2)` already got, for the same reason
# recorded in _FUNCS: widening what counts as a well-formed answer, not what
# the grader can execute. `conjugate` is a pure sympy callable, and because
# `_parse_formula` builds its symbols `positive=True`, conjugate(g) collapses
# to g at every sample point.
# ---------------------------------------------------------------------------

CONJ_SYMS = {"g": [0.1, 2.0], "mS": [500.0, 3000.0], "mf": [1.0, 200.0]}


def test_conjugate_is_accepted_in_a_formula(bench):
    write, check = bench
    write({"width_formula":
           "y**2 * mS * (1 - 4*mf**2/mS**2)**(3/2) / (8*pi)"})
    ok, msg = check("answer_formula",
                    {"field": "width_formula", "symbols": SYMS})
    assert ok, msg          # control: the plain form still passes
    # The tool's own spelling of the same thing.
    write({"width_formula":
           "y*conjugate(y) * mS * (1 - 4*mf**2/mS**2)**(3/2) / (8*pi)"})
    ok, msg = check("answer_formula",
                    {"field": "width_formula", "symbols": SYMS})
    assert ok, msg


def test_the_mathematica_capitalisation_is_accepted(bench):
    """The tools emit `Conjugate(`, capitalised, as Mathematica spells it."""
    write, check = bench
    write({"width_formula":
           "y*Conjugate(y) * mS * (1 - 4*mf**2/mS**2)**(3/2) / (8*pi)"})
    ok, msg = check("answer_formula",
                    {"field": "width_formula", "symbols": SYMS})
    assert ok, msg


def test_conjugate_of_a_wrong_expression_still_fails(bench):
    """Widening the alphabet must not widen what counts as correct."""
    write, check = bench
    write({"width_formula":
           "y*Conjugate(y) * mS * (1 - 4*mf**2/mS**2)**(3/2) / (16*pi)"})
    ok, msg = check("answer_formula",
                    {"field": "width_formula", "symbols": SYMS})
    assert not ok and "disagrees" in msg


def test_conjugate_is_not_treated_as_an_undeclared_symbol(bench):
    """The old failure mode: it was reported as `unknown symbols
    ['Conjugate']`, which reads as the answer naming something it should not
    rather than as a function the grader had never been taught."""
    write, check = bench
    write({"width_formula":
           "y*Conjugate(y) * mS * (1 - 4*mf**2/mS**2)**(3/2) / (8*pi)"})
    ok, msg = check("answer_formula",
                    {"field": "width_formula", "symbols": SYMS})
    assert "Conjugate" not in msg or ok, msg
