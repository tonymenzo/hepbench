"""
# benchmarks/symbolic/_shared/checks.py is a part of HEPBench.
# Copyright (C) 2026 HEPBench authors (see AUTHORS for details).
# HEPBench is licensed under the GNU GPL v3 or later, see LICENSE for details.
"""
"""
Custom checks for the `symbolic` benchmark family.

Every symbolic benchmark asks the agent to write a flat JSON answer file
(`results/answer.json`) holding numeric values (widths in GeV, cross
sections in pb, lifetimes in s, ...) and closed-form formula strings.
Three checks grade it:

  answer_value        scalar vs the ground-truth value; `rel_tol` mode
                      (|pred - truth| <= rel_tol * |truth|) or `log10_tol`
                      mode (|log10(pred/truth)| <= log10_tol, the
                      order-of-magnitude rung an NDA estimate can pass).

  answer_formula      formula string vs the ground-truth formula, graded
                      by NUMERIC SAMPLING: both are sympy-parsed against a
                      declared symbol alphabet and evaluated at fixed
                      pseudo-random points of the declared domain; they
                      must agree to `rel_tol` everywhere. No symbolic
                      equivalence engine, so any algebraically equivalent
                      arrangement passes and a wrong factor cannot.

  answer_consistency  an expression over the answer's own numeric fields
                      (e.g. "br_a + br_b + br_c", "tau_s * width_gev")
                      compared against a constant — internal-consistency
                      stages for composite tasks.

Ground truth lives in the benchmark's `ground_truth/truth.json` (the
`reference:` param; toolbench resolves relative paths against the
benchmark dir). It is generated and *verified* by the benchmark's
`ground_truth/derivation.py` — see that file for conventions and
literature citations.

Formula strings are parsed defensively: a character allowlist plus a
token allowlist (declared symbols, a few functions, pi) is enforced
before sympy ever sees the string, so an answer file cannot smuggle
code into the grader.
"""

import json
import random
import re
from pathlib import Path

import sympy
from sympy.parsing.sympy_parser import parse_expr

# Allowed callables/constants inside formula answers. Kept deliberately
# small: every ground-truth formula in this family is built from
# rational operations, sqrt and powers; pi is the only constant.
_FUNCS = {
    "sqrt": sympy.sqrt,
    "exp": sympy.exp,
    "log": sympy.log,
    "ln": sympy.log,
    "Abs": sympy.Abs,
    "abs": sympy.Abs,
    "atan": sympy.atan,
    "asin": sympy.asin,
    "acos": sympy.acos,
    # Exact rational exponents. The tasks ask for a "sympy-parseable"
    # formula, and `(...)**Rational(3,2)` is the idiomatic sympy way to
    # write a 3/2 power -- a real gpt-oss-120b trial wrote exactly that
    # for the beta^3 width and was rejected on the alphabet despite
    # being algebraically identical to the ground truth. These are pure
    # numeric constructors: they widen what counts as a well-formed
    # answer, not what the grader can execute.
    "Rational": sympy.Rational,
    "Integer": sympy.Integer,
    "Float": sympy.Float,
    # The eda tools emit this: without `assume_real_couplings` the returned
    # `width_formula` carries `Conjugate(g)`, i.e. |g|^2, which for the real
    # couplings these tasks specify is g^2. An agent copying the tool's own
    # output was marked wrong on the alphabet -- 15 trials over five tasks in
    # the 2026-10 campaigns, each numerically identical to the ground truth.
    # Both spellings: sympy writes `conjugate`, the tools emit Mathematica's
    # `Conjugate`. Because `_parse_formula` builds symbols `positive=True`,
    # conjugate(g) collapses to g at every sample point, so this widens what
    # counts as well-formed without widening what counts as correct.
    "conjugate": sympy.conjugate,
    "Conjugate": sympy.conjugate,
}
_CONSTS = {"pi": sympy.pi, "Pi": sympy.pi}

_CHARSET = re.compile(r"^[A-Za-z0-9_+\-*/^(). ,\s]*$")
_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
# Scientific-notation literals (1e-3, 2.5E+07) would otherwise leave a
# stray "e"/"E" token behind for the name scan.
_SCINOT = re.compile(r"\d+\.?\d*[eE][+-]?\d+")

# Fixed seed: grading must be reproducible run-to-run and regrade-safe.
_SAMPLE_SEED = 20260611


def _load_json(sandbox: Path, rel: str):
    p = Path(sandbox) / rel
    if not p.is_file():
        return None, f"missing file: {rel}"
    try:
        obj = json.loads(p.read_text())
    except Exception as e:
        return None, f"unparseable JSON in {rel}: {e}"
    if not isinstance(obj, dict):
        return None, f"{rel} must hold a JSON object"
    return obj, None


def _get_field(obj: dict, dotted: str):
    cur = obj
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None, f"field {dotted!r} missing"
        cur = cur[part]
    return cur, None


def _as_float(val, label: str):
    try:
        x = float(val)
    except (TypeError, ValueError):
        return None, f"{label} is not numeric: {val!r}"
    if not (x == x and abs(x) != float("inf")):  # NaN / inf guard
        return None, f"{label} is not finite: {val!r}"
    return x, None



def _free_symbol_names(text) -> set:
    """Best-effort set of identifier-like tokens in a formula string.

    Only used to make a rejection message name the undeclared symbols, so a
    loose match is fine: anything that is a known function or constant is
    dropped, and being wrong here costs a slightly noisier message, never a
    grade.
    """
    if not isinstance(text, str):
        return set()
    # Same scan `_parse_formula` uses: strip scientific-notation literals
    # first so 1e-3 does not leave a stray "e" token behind.
    stripped = _SCINOT.sub("", text)
    toks = set(_NAME.findall(stripped))
    return toks - set(_FUNCS) - set(_CONSTS)


def _parse_formula(text, symbol_names):
    """Parse an untrusted formula string into a sympy expression.

    Defense layers (in order): type/length, character allowlist, token
    allowlist against the declared symbol alphabet, then parse with a
    closed local dict. Returns (expr, error_message)."""
    if not isinstance(text, str):
        return None, "formula must be a string"
    if not text.strip():
        return None, "formula is empty"
    if len(text) > 4000:
        return None, "formula longer than 4000 characters"
    if not _CHARSET.match(text):
        return None, "formula contains disallowed characters"
    names = set(_NAME.findall(_SCINOT.sub("0", text)))
    allowed = set(symbol_names) | set(_FUNCS) | set(_CONSTS)
    unknown = names - allowed
    if unknown:
        return None, (f"unknown symbols {sorted(unknown)}; "
                      f"allowed symbols: {sorted(symbol_names)}")
    local = dict(_FUNCS)
    local.update(_CONSTS)
    local.update({n: sympy.Symbol(n, positive=True) for n in symbol_names})
    try:
        expr = parse_expr(text.replace("^", "**"), local_dict=local,
                          evaluate=True)
    except Exception as e:
        return None, f"formula failed to parse: {e}"
    return expr, None


def _sample_points(symbols: dict, constraints, n_points: int):
    """Deterministic sample of the declared domain.

    `symbols` maps name -> [lo, hi]; `constraints` is a list of formula
    strings (same alphabet) that must evaluate > 0 at a valid point."""
    names = sorted(symbols)
    cexprs = []
    for c in constraints or []:
        expr, err = _parse_formula(c, names)
        if err:
            raise ValueError(f"bad constraint {c!r}: {err}")
        cexprs.append(sympy.lambdify(names, expr, modules="math"))
    rng = random.Random(_SAMPLE_SEED)
    points, attempts = [], 0
    while len(points) < n_points and attempts < 200 * n_points:
        attempts += 1
        pt = {n: rng.uniform(*map(float, symbols[n])) for n in names}
        try:
            if all(c(**pt) > 0 for c in cexprs):
                points.append(pt)
        except Exception:
            continue
    if len(points) < n_points:
        raise ValueError("could not sample enough points satisfying the "
                         "domain constraints; widen the declared ranges")
    return names, points


def check_answer_value(sandbox: Path, params: dict):
    """Compare a numeric answer field against the ground-truth value.

    params: file, field, reference, ref_field (default: field), and one
    of rel_tol (relative error) / log10_tol (order-of-magnitude)."""
    obj, err = _load_json(sandbox, params.get("file", "results/answer.json"))
    if err:
        return False, err
    field = params["field"]
    raw, err = _get_field(obj, field)
    if err:
        return False, err
    pred, err = _as_float(raw, f"answer field {field!r}")
    if err:
        return False, err

    ref_path = Path(params["reference"])
    if not ref_path.is_file():
        return False, f"ground-truth file not found: {ref_path}"
    truth_obj = json.loads(ref_path.read_text())
    truth_raw, err = _get_field(truth_obj, params.get("ref_field", field))
    if err:
        return False, f"ground truth: {err}"
    truth, err = _as_float(truth_raw, "ground-truth value")
    if err:
        return False, err

    log10_tol = params.get("log10_tol")
    if log10_tol is not None:
        if pred <= 0 or truth <= 0:
            return False, (f"{field}: log10 comparison needs positive "
                           f"values; got {pred:.6g} vs {truth:.6g}")
        import math
        dev = abs(math.log10(pred / truth))
        ok = dev <= float(log10_tol)
        return ok, (f"{field}: got {pred:.6g}, expected {truth:.6g}; "
                    f"|log10 ratio| = {dev:.3f} (tol {float(log10_tol)})")

    rel_tol = float(params.get("rel_tol", 0.10))
    denom = abs(truth) if truth != 0 else 1.0
    rel = abs(pred - truth) / denom
    ok = rel <= rel_tol
    return ok, (f"{field}: got {pred:.6g}, expected {truth:.6g}; "
                f"rel err = {rel:.3g} (tol {rel_tol})")


def check_answer_formula(sandbox: Path, params: dict):
    """Grade a closed-form formula answer by numeric sampling.

    params: file, field, reference, ref_field (default: field),
    symbols ({name: [lo, hi]}), constraints (optional list of ">0"
    expressions), n_points (default 8), rel_tol (default 1e-6)."""
    obj, err = _load_json(sandbox, params.get("file", "results/answer.json"))
    if err:
        return False, err
    field = params["field"]
    text, err = _get_field(obj, field)
    if err:
        return False, err

    symbols = params.get("symbols") or {}
    if not symbols:
        return False, "rubric error: answer_formula needs a `symbols` map"
    names = sorted(symbols)

    # `fixed` declares symbols the TASK pins to a constant -- a massless
    # daughter's mass, say. They are ADMISSIBLE in either formula and
    # substituted before sampling, so an answer written in the general form
    # is evaluated at the point the task actually asks about instead of being
    # rejected for mentioning a symbol the specialised ground truth dropped.
    #
    # Without this, a part that fixes a mass to zero graded two correct
    # answers differently: declare `"mass": 0` and the tool returns the
    # specialised form (passes), keep the mass symbolic and pass 0 in `values`
    # and it returns the general form (rejected unparsed). It also biased one
    # arm -- a tools arm naturally returns the general form.
    fixed = params.get("fixed") or {}
    try:
        # `positive=True` to match how `_parse_formula` builds its symbols --
        # Symbol("mf") and Symbol("mf", positive=True) are different objects
        # and a substitution keyed on the wrong one silently does nothing,
        # leaving the expression unevaluatable.
        subs = {sympy.Symbol(k, positive=True): float(v)
                for k, v in fixed.items()}
    except (TypeError, ValueError):
        return False, ("rubric error: `fixed` must map symbol names to "
                       f"numbers, got {fixed!r}")
    admissible = sorted(set(names) | set(fixed))

    pred_expr, err = _parse_formula(text, admissible)
    if err:
        # Name the undeclared symbols. A bare parse failure here reads like a
        # syntax error in the answer, when the usual cause is a correct
        # formula mentioning a symbol the rubric did not declare.
        extra = sorted(_free_symbol_names(text) - set(admissible))
        if extra:
            return False, (
                f"{field}: {err}; symbol(s) {', '.join(extra)} are not "
                f"declared for this stage (declared: "
                f"{', '.join(admissible)}). If the task fixes them to a "
                f"constant, declare that with `fixed`.")
        return False, f"{field}: {err}"

    ref_path = Path(params["reference"])
    truth_obj = json.loads(ref_path.read_text())
    truth_text, err = _get_field(truth_obj, params.get("ref_field", field))
    if err:
        return False, f"ground truth: {err}"
    truth_expr, err = _parse_formula(truth_text, admissible)
    if err:
        return False, f"ground-truth formula: {err}"

    if subs:
        pred_expr = pred_expr.subs(subs)
        truth_expr = truth_expr.subs(subs)

    try:
        names, points = _sample_points(symbols, params.get("constraints"),
                                       int(params.get("n_points", 8)))
    except ValueError as e:
        return False, f"rubric error: {e}"

    f_pred = sympy.lambdify(names, pred_expr, modules="math")
    f_truth = sympy.lambdify(names, truth_expr, modules="math")
    rel_tol = float(params.get("rel_tol", 1e-6))
    worst = 0.0
    for pt in points:
        try:
            a = float(f_pred(**pt))
        except Exception as e:
            return False, f"{field}: formula failed to evaluate at {pt}: {e}"
        try:
            b = float(f_truth(**pt))
        except Exception as e:
            # A rubric bug (domain straying outside the ground-truth
            # formula's support, e.g. a missing threshold `constraints:`
            # entry), not an answer bug -- surface it as such rather than
            # crashing the judge mid-run.
            return False, (f"rubric error: ground-truth formula for {field} "
                           f"is undefined at sampled point {pt}: {e}; "
                           f"tighten the declared domain or add a constraint")
        denom = max(abs(b), 1e-300)
        rel = abs(a - b) / denom
        worst = max(worst, rel)
        if rel > rel_tol:
            return False, (f"{field}: disagrees with ground truth at "
                           f"{ {k: round(v, 3) for k, v in pt.items()} }: "
                           f"got {a:.6g}, expected {b:.6g} "
                           f"(rel err {rel:.3g}, tol {rel_tol})")
    return True, (f"{field}: matches ground truth at {len(points)} sample "
                  f"points (max rel err {worst:.3g}, tol {rel_tol})")


def check_answer_consistency(sandbox: Path, params: dict):
    """Evaluate an expression over the answer's own numeric fields.

    params: file, expr (over top-level numeric answer fields), equals,
    rel_tol (default 0.01)."""
    obj, err = _load_json(sandbox, params.get("file", "results/answer.json"))
    if err:
        return False, err
    fields = {k: float(v) for k, v in obj.items()
              if isinstance(v, (int, float)) and not isinstance(v, bool)}
    expr_text = params["expr"]
    expr, err = _parse_formula(expr_text, sorted(fields))
    if err:
        return False, f"consistency expr: {err}"
    try:
        val = float(sympy.lambdify(sorted(fields), expr,
                                   modules="math")(**fields))
    except Exception as e:
        return False, f"consistency expr failed to evaluate: {e}"
    target = float(params["equals"])
    rel_tol = float(params.get("rel_tol", 0.01))
    denom = abs(target) if target != 0 else 1.0
    rel = abs(val - target) / denom
    ok = rel <= rel_tol
    return ok, (f"{expr_text} = {val:.6g}, expected {target:.6g}; "
                f"rel err = {rel:.3g} (tol {rel_tol})")


CHECKS = {
    "answer_value": check_answer_value,
    "answer_formula": check_answer_formula,
    "answer_consistency": check_answer_consistency,
}

# All three decide correctness; the presence rung of each rubric uses the
# built-in (presence-role) `json_with_keys` check instead.
ROLES = {
    "answer_value": "correctness",
    "answer_formula": "correctness",
    "answer_consistency": "correctness",
}
