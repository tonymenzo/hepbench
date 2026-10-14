"""
# benchmarks/llp_forward/checks/checks.py is a part of HEPBench.
# Copyright (C) 2026 HEPBench authors (see AUTHORS for details).
# HEPBench is licensed under the GNU GPL v3 or later, see LICENSE for details.
"""
"""
Custom checks for the `llp_forward` benchmark (v1, full spectrum).

The deliverable is `results/answer.json` (schema shipped in the sandbox
at results/answer_schema.json): the derived phi decay width fields and
the expected signal yield N_sig at every DECLARED (search, m_phi, g)
evaluation point. Ground truth lives in the benchmark's
`ground_truth/truth.json` (the `reference:` param), generated and
self-gated by `ground_truth/derivation.py`.

The contour (g_low/g_high) is intentionally NOT a graded field: the
grader reduces the yield cells to the exclusion band itself, so the
graded quantity is the well-conditioned yield, not the agent's
root-find. Every correctness check reads answer.json; the only
disk-touching check is a loose Pythia-output glob.

Checks:

  glob_present     presence: >= min_matches of `patterns` match a file
                   (loadout-robust: loose, name-based Pythia-output gate).
  llp_value        scalar answer field vs truth, rel_tol or log10_tol
                   (adapted from the symbolic family's answer_value).
  llp_formula      formula string graded by NUMERIC SAMPLING against the
                   truth formula over a declared symbol domain (the
                   symbolic family's answer_formula: charset + token
                   allowlist, sympy parse, fixed pseudo-random points).
  llp_ctau_pair    both ctau probes within rel_tol AND their ratio
                   consistent with the total-width ctau ~ g^-2 scaling.
  llp_nsig_filled  presence: a numeric N_sig for every declared truth
                   (search, m_phi, g) point (matched by search + m + g).
  llp_nsig_close   correctness: the agent N_sig within `factor` in
                   LOG space of truth at >= `min_fraction` of the
                   declared points (a coarse->fine tolerance ladder).

The answer-structure gate uses toolbench's built-in `json_with_keys`
and the optional plot uses `plot_nonempty` — not redefined here.
"""

import fnmatch
import json
import math
import statistics
import random
import re
from pathlib import Path

import sympy
from sympy.parsing.sympy_parser import parse_expr

# --------------------------------------------------------------------------
# formula parsing / sampling — adapted from benchmarks/symbolic/_shared/
# checks.py (charset, token allowlist, closed local dict, fixed seed).
# --------------------------------------------------------------------------
_FUNCS = {
    "sqrt": sympy.sqrt, "exp": sympy.exp, "log": sympy.log,
    "ln": sympy.log, "Abs": sympy.Abs, "abs": sympy.Abs,
    "atan": sympy.atan, "asin": sympy.asin, "acos": sympy.acos,
}
_CONSTS = {"pi": sympy.pi, "Pi": sympy.pi}
_CHARSET = re.compile(r"^[A-Za-z0-9_+\-*/^(). ,\s]*$")
_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_SCINOT = re.compile(r"\d+\.?\d*[eE][+-]?\d+")
_SAMPLE_SEED = 20260715


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


def _load_truth(params: dict):
    ref_path = Path(params["reference"])
    if not ref_path.is_file():
        return None, f"ground-truth file not found: {ref_path}"
    return json.loads(ref_path.read_text()), None


def _as_float(val, label: str):
    try:
        x = float(val)
    except (TypeError, ValueError):
        return None, f"{label} is not numeric: {val!r}"
    if not (x == x and abs(x) != float("inf")):
        return None, f"{label} is not finite: {val!r}"
    return x, None


# A piecewise qualifier appended to an otherwise-valid expression, e.g.
#   "g**2*m_phi/(8*pi)*(1 - 4*m_mu**2/m_phi**2)**(3/2) for m_phi > 2*m_mu, else 0"
#   "g**2*... if m_phi > 2*m_mu else 0"
# The dimuon width IS piecewise -- it vanishes below 2*m_mu, where the
# phase-space factor turns imaginary -- so an agent that states the condition is
# being MORE precise than `soln/truth.json`, which stores the bare expression and
# gets away with it only because `constraints` samples strictly above threshold.
# The character whitelist below rejects the letters in such a qualifier before
# anything is parsed, so the graded formula was failing for being too correct.
# Strip the qualifier and grade the expression it qualifies.
_PIECEWISE = re.compile(r"\s+(?:for|if|when|where|valid|only)\s", re.I)
_ELSE = re.compile(r"\s+else\s+", re.I)


def _strip_lhs(text: str):
    """Drop a leading `NAME(...) =` label, returning just the expression.

    Asked to "report the dimuon-width formula", agents reasonably write the
    whole equation rather than a bare right-hand side:

        Gamma(phi->mu+mu-) = g**2 * m_phi / (8*pi) * (1 - 4*m_mu**2/m_phi**2)**(3/2)

    The label carries `->`, which `_CHARSET` rejects, so the formula was
    failed for its punctuation while the expression itself was exactly right.
    That cost a 2026-08-10 Sonnet trial its entire score: `width_correct`
    absorbs, so a label rejected on characters zeroed a yield scan that had
    scored 0.977. The rubric asks for a formula, not for a particular way of
    presenting one.

    Only a SINGLE leading `=` is stripped, and only when a right-hand side
    remains -- an expression containing a comparison or an assignment chain is
    still rejected rather than silently truncated.
    """
    if text.count("=") != 1:
        return text
    lhs, _, rhs = text.partition("=")
    if rhs.strip() and lhs.strip():
        return rhs.strip()
    return text


def _strip_piecewise(text: str):
    """Return (expression, dropped_qualifier_or_None).

    Handles the two orderings seen in practice: `EXPR for COND, else 0` /
    `EXPR if COND else 0` (take the head), and the inverted Python ternary
    `0 if COND else EXPR` (the head is a bare constant, so take the tail).
    A formula for a width must depend on its symbols, so a symbol-free head is
    the reliable signal that the real expression is in the else-branch.
    """
    m = _PIECEWISE.search(text)
    if not m:
        return text, None
    head = text[:m.start()].strip().rstrip(",;:")
    qualifier = text[m.start():].strip()
    if head and not _NAME.findall(_SCINOT.sub("0", head)):
        tail = _ELSE.split(text, 1)
        if len(tail) == 2 and _NAME.findall(_SCINOT.sub("0", tail[1])):
            return tail[1].strip().rstrip(",;:"), qualifier
    return head, qualifier


def _parse_formula(text, symbol_names):
    if not isinstance(text, str):
        return None, "formula must be a string"
    if not text.strip():
        return None, "formula is empty"
    if len(text) > 4000:
        return None, "formula longer than 4000 characters"
    if not _CHARSET.match(text):
        # An `LHS =` label is presentation, not content; try it before prose.
        relabelled = _strip_lhs(text)
        if relabelled is not text and _CHARSET.match(relabelled):
            text = relabelled
    if not _CHARSET.match(text):
        stripped, qualifier = _strip_piecewise(text)
        if qualifier and stripped and _CHARSET.match(stripped):
            text = stripped          # graded on the expression, not the prose
        else:
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
                         "domain constraints")
    return names, points


# --------------------------------------------------------------------------
# presence: loose Pythia-output glob (loadout-robust)
# --------------------------------------------------------------------------
def check_glob_present(sandbox: Path, params: dict):
    """At least `min_matches` (default 1) of `patterns` match a file.
    Patterns are sandbox-relative globs; any match counts. Used as the
    loose 'a forward flux was generated' presence gate (never reads the
    oracle, robust across loadouts)."""
    patterns = params.get("patterns") or []
    if not patterns:
        return False, "glob_present: `patterns` must be non-empty"
    min_matches = int(params.get("min_matches", 1))
    rel = [str(p.relative_to(sandbox))
           for p in Path(sandbox).rglob("*") if p.is_file()]
    hits = sorted({f for f in rel
                   if any(fnmatch.fnmatch(f, pat) for pat in patterns)})
    if len(hits) >= min_matches:
        shown = ", ".join(hits[:3]) + ("…" if len(hits) > 3 else "")
        return True, f"{len(hits)} match(es): {shown}"
    return False, f"no file matches {patterns} (need >={min_matches})"


# --------------------------------------------------------------------------
# scalar / formula checks
# --------------------------------------------------------------------------
def check_llp_value(sandbox: Path, params: dict):
    """Numeric answer field vs truth. params: file, field, index (optional),
    reference, ref_field, rel_tol XOR log10_tol."""
    obj, err = _load_json(sandbox, params.get("file", "results/answer.json"))
    if err:
        return False, err
    field = params["field"]
    raw = obj.get(field)
    if raw is None:
        return False, f"field {field!r} missing or null"
    truth, err = _load_truth(params)
    if err:
        return False, err
    truth_raw = truth.get(params.get("ref_field", field))
    idx = params.get("index")
    label = field
    if idx is not None:
        label = f"{field}[{idx}]"
        if not isinstance(raw, list) or len(raw) <= int(idx):
            return False, f"{field} is not a list with index {idx}"
        raw = raw[int(idx)]
        truth_raw = truth_raw[int(idx)]
    pred, err = _as_float(raw, label)
    if err:
        return False, err
    tval, err = _as_float(truth_raw, f"truth {label}")
    if err:
        return False, err
    log10_tol = params.get("log10_tol")
    if log10_tol is not None:
        if pred <= 0 or tval <= 0:
            return False, f"{label}: log10 mode needs positive values"
        dev = abs(math.log10(pred / tval))
        return dev <= float(log10_tol), (
            f"{label}: got {pred:.6g}, expected {tval:.6g}; "
            f"|log10 ratio| = {dev:.3f} (tol {float(log10_tol)})")
    rel_tol = float(params.get("rel_tol", 0.10))
    rel = abs(pred - tval) / max(abs(tval), 1e-300)
    return rel <= rel_tol, (
        f"{label}: got {pred:.6g}, expected {tval:.6g}; "
        f"rel err = {rel:.3g} (tol {rel_tol})")


def check_llp_formula(sandbox: Path, params: dict):
    """Closed-form formula string vs truth by numeric sampling.
    params: file, field, reference, ref_field, symbols {name:[lo,hi]},
    constraints (">0" expressions), n_points, rel_tol."""
    obj, err = _load_json(sandbox, params.get("file", "results/answer.json"))
    if err:
        return False, err
    field = params["field"]
    text = obj.get(field)
    symbols = params.get("symbols") or {}
    if not symbols:
        return False, "rubric error: llp_formula needs a `symbols` map"
    names = sorted(symbols)
    pred_expr, err = _parse_formula(text, names)
    if err:
        return False, f"{field}: {err}"
    truth, err = _load_truth(params)
    if err:
        return False, err
    truth_expr, err = _parse_formula(
        truth.get(params.get("ref_field", field)), names)
    if err:
        return False, f"ground-truth formula: {err}"
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
            return False, f"{field}: failed to evaluate at {pt}: {e}"
        b = float(f_truth(**pt))
        rel = abs(a - b) / max(abs(b), 1e-300)
        worst = max(worst, rel)
        if rel > rel_tol:
            return False, (
                f"{field}: disagrees with ground truth at "
                f"{ {k: round(v, 4) for k, v in pt.items()} }: got {a:.6g}, "
                f"expected {b:.6g} (rel err {rel:.3g}, tol {rel_tol})")
    return True, (f"{field}: matches ground truth at {len(points)} points "
                  f"(max rel err {worst:.3g}, tol {rel_tol})")


def check_llp_ctau_pair(sandbox: Path, params: dict):
    """Both ctau probes within rel_tol of truth AND the pair ratio
    consistent with the TOTAL-width ctau ~ g^-2 scaling (probe g values
    come from truth.ctau_probe.g)."""
    obj, err = _load_json(sandbox, params.get("file", "results/answer.json"))
    if err:
        return False, err
    truth, err = _load_truth(params)
    if err:
        return False, err
    field = params.get("field", "ctau_probe_m")
    pred = obj.get(field)
    tval = truth[field]
    if not isinstance(pred, list) or len(pred) != len(tval):
        return False, f"{field} must be a list of {len(tval)} values"
    rel_tol = float(params.get("rel_tol", 0.05))
    vals = []
    for i, (a_raw, b) in enumerate(zip(pred, tval)):
        a, err = _as_float(a_raw, f"{field}[{i}]")
        if err:
            return False, err
        rel = abs(a - b) / abs(b)
        if rel > rel_tol:
            return False, (f"{field}[{i}]: got {a:.6g}, expected {b:.6g}; "
                           f"rel err = {rel:.3g} (tol {rel_tol})")
        vals.append(a)
    g1, g2 = truth["ctau_probe"]["g"]
    ratio_tol = float(params.get("ratio_tol", 0.01))
    expected = (g2 / g1) ** 2
    got = vals[0] / vals[1]
    dev = abs(got / expected - 1.0)
    if dev > ratio_tol:
        return False, (f"{field} ratio ctau(g1)/ctau(g2) = {got:.6g} vs "
                       f"(g2/g1)^2 = {expected:.6g}: g^-2 scaling violated "
                       f"(dev {dev:.3g}, tol {ratio_tol})")
    return True, (f"{field}: both probes within {rel_tol} and g^-2 "
                  f"scaling within {ratio_tol}")


# --------------------------------------------------------------------------
# yield-table checks (declared (search, m_phi, g) points)
# --------------------------------------------------------------------------
_SEARCH_KEYS = {"search", "channel", "mode"}
_MASS_KEYS = {"m", "m_phi", "mass", "m_gev", "m_phi_gev", "mphi"}
_G_KEYS = {"g", "coupling", "g_phi", "gphi"}
_N_KEYS = {"nsig", "n_sig", "n", "n_signal", "yield", "nsignal"}


def _pick(d, keys):
    for k in d:
        if isinstance(k, str) and k.strip().lower() in keys:
            return d[k]
    return None


def _truth_points(truth):
    """[(search, m_phi, g, nsig)] from truth['points']."""
    out = []
    for p in truth.get("points", []):
        out.append((str(p["search"]), float(p["m_phi"]), float(p["g"]),
                    float(p["nsig"])))
    return out


def _agent_points(obj):
    """[(search, m_phi, g, nsig_or_None)] from answer.json. Accepts a
    'points' list of {search,m_phi,g,nsig} (aliases allowed) or a nested
    'nsig' dict {search:{m:{g:val}}}."""
    pts = obj.get("points")
    out = []
    if isinstance(pts, list):
        for p in pts:
            if not isinstance(p, dict):
                continue
            s = _pick(p, _SEARCH_KEYS)
            m = _pick(p, _MASS_KEYS)
            g = _pick(p, _G_KEYS)
            n = _pick(p, _N_KEYS)
            try:
                out.append((str(s), float(m), float(g),
                            None if n is None else float(n)))
            except (TypeError, ValueError):
                continue
        return out
    nested = obj.get("nsig")
    if isinstance(nested, dict):
        for s, md in nested.items():
            if not isinstance(md, dict):
                continue
            for m, gd in md.items():
                if not isinstance(gd, dict):
                    continue
                for g, v in gd.items():
                    try:
                        out.append((str(s), float(m), float(g),
                                    None if v is None else float(v)))
                    except (TypeError, ValueError):
                        continue
    return out


def _match(agent_pts, search, m, g, m_tol=1e-4, g_ltol=math.log(1.02)):
    """Nearest agent point with the same search, m within m_tol and g within
    a small log tolerance. Returns its nsig (may be None) or 'missing'."""
    best, best_d = None, None
    for (s, ma, ga, na) in agent_pts:
        if s != search or abs(ma - m) > m_tol or ga <= 0.0:
            continue
        d = abs(math.log(ga / g))
        if d <= g_ltol and (best_d is None or d < best_d):
            best, best_d = na, d
    return best if best is not None or best_d is not None else "missing"


def check_llp_nsig_filled(sandbox: Path, params: dict):
    """Every declared truth point has a matching, finite, non-negative
    N_sig in answer.json."""
    obj, err = _load_json(sandbox, params.get("file", "results/answer.json"))
    if err:
        return False, err
    truth, err = _load_truth(params)
    if err:
        return False, err
    tpts = _truth_points(truth)
    apts = _agent_points(obj)
    if not tpts:
        return False, "reference has no declared points"
    missing, bad = 0, 0
    for (s, m, g, _n) in tpts:
        got = _match(apts, s, m, g)
        if got == "missing" or got is None:
            missing += 1
        elif not (isinstance(got, float) and got == got and got >= 0.0):
            bad += 1
    if missing or bad:
        det = []
        if missing:
            det.append(f"{missing}/{len(tpts)} points missing")
        if bad:
            det.append(f"{bad} non-numeric/negative")
        return False, "; ".join(det)
    return True, f"all {len(tpts)} N_sig points present"


def check_llp_nsig_close(sandbox: Path, params: dict):
    """Agent N_sig within `factor` in log space of truth at >=
    `min_fraction` of declared points. Cells with truth N_sig <= `floor`
    or m_phi > `max_mass` are skipped (the high-mass vector frontier is
    physically negligible and MC-noise-dominated, so it is reported by the
    agent but not tightly graded). params: file, reference, factor,
    min_fraction, floor, max_mass."""
    obj, err = _load_json(sandbox, params.get("file", "results/answer.json"))
    if err:
        return False, err
    truth, err = _load_truth(params)
    if err:
        return False, err
    tpts = _truth_points(truth)
    apts = _agent_points(obj)
    factor = float(params.get("factor", 2.0))
    min_fraction = float(params.get("min_fraction", 1.0))
    floor = float(params.get("floor", 0.0))
    max_mass = float(params.get("max_mass", float("inf")))
    ltol = math.log(factor)
    graded, npass, worst, worst_cell = 0, 0, 0.0, None
    for (s, m, g, nt) in tpts:
        if nt <= floor or m > max_mass:
            continue
        graded += 1
        got = _match(apts, s, m, g)
        if got == "missing" or got is None:
            dev = float("inf")
        else:
            dev = abs(math.log(max(got, nt * 1e-12) / nt))
        if dev <= ltol:
            npass += 1
        if dev > worst:
            worst, worst_cell = dev, (s, m, g)
    if graded == 0:
        return False, "no gradeable points"
    frac = npass / graded
    ok = frac >= min_fraction
    wc = ""
    if worst_cell:
        s, m, g = worst_cell
        wf = math.exp(worst) if worst != float("inf") else float("inf")
        wc = f", worst {s} m={m:g} g={g:.2e} off x{wf:.2f}"
    return ok, (f"{npass}/{graded} within x{factor:g} "
                f"(need {min_fraction*100:.0f}%){wc}")


# ---------------------------------------------------------------------------
# GRID-INDEPENDENT reach grading. The agent reports a g-scan per (search,
# m_phi) -- `reach: [{search, m_phi, scan:[{g, nsig}]}]` -- NOT yields at a
# pinned g-grid. The grader root-finds the N_sig = target band from that scan
# and grades the DERIVED REACH by log-g distance (band_close), plus grid-free
# peak-yield agreement that catches dropped channels even at null-for-reach
# masses (peak_close), plus a structural g^4 / below-threshold-gg gate
# (scaling). This tests the physics, not the ability to hit a declared grid.
# ---------------------------------------------------------------------------
def _agent_reach(obj):
    """{(search, round(m,4)): [(g, nsig), ...] sorted by g} from the answer's
    `reach` list. Falls back to the legacy flat `points` list (grouped by
    search+m) so old answers still grade."""
    out = {}
    reach = obj.get("reach")
    if isinstance(reach, list):
        for e in reach:
            if not isinstance(e, dict):
                continue
            s = _pick(e, _SEARCH_KEYS)
            m = _pick(e, _MASS_KEYS)
            scan = e.get("scan") or e.get("points") or e.get("yields")
            if s is None or m is None or not isinstance(scan, list):
                continue
            pts = []
            for q in scan:
                if not isinstance(q, dict):
                    continue
                g = _pick(q, _G_KEYS)
                n = _pick(q, _N_KEYS)
                try:
                    g = float(g)
                    n = float(n)
                except (TypeError, ValueError):
                    continue
                if g > 0.0 and n == n and n >= 0.0:
                    pts.append((g, n))
            if pts:
                out[(str(s), round(float(m), 4))] = sorted(pts)
        if out:
            return out
    for (s, m, g, n) in _agent_points(obj):        # legacy fallback
        if n is None or g <= 0.0:
            continue
        out.setdefault((str(s), round(m, 4)), []).append((g, float(n)))
    for k in out:
        out[k] = sorted(out[k])
    return out


def _crossings(scan, target):
    """(g_lo, g_hi) where the g-scan crosses `target`, by linear interp in
    (log10 g, nsig): g_lo = first up-crossing, g_hi = last down-crossing.
    (None, None) if the peak never reaches target; g_hi=None if the curve
    never falls back below target within the scanned range."""
    if len(scan) < 2 or max(n for _g, n in scan) < target:
        return (None, None)
    xs = [math.log10(g) for g, _n in scan]
    ys = [n for _g, n in scan]
    g_lo = g_hi = None
    for i in range(len(scan) - 1):
        y0, y1 = ys[i], ys[i + 1]
        if g_lo is None and y0 < target <= y1 and y1 != y0:
            t = (target - y0) / (y1 - y0)
            g_lo = 10.0 ** (xs[i] + t * (xs[i + 1] - xs[i]))
        if g_lo is not None and y0 >= target > y1 and y1 != y0:
            t = (target - y0) / (y1 - y0)
            g_hi = 10.0 ** (xs[i] + t * (xs[i + 1] - xs[i]))
    if g_lo is None:
        return (None, None)
    return (g_lo, g_hi)


def _truth_bands(truth):
    """{(search, round(m,4)): [g_lo, g_hi] or None} from truth `_per_mass`."""
    return {(str(r["search"]), round(float(r["m"]), 4)): r.get("band")
            for r in truth.get("_per_mass", [])}


def _truth_peaks(truth):
    """{(search, round(m,4)): peak_nsig} from truth `_per_mass`."""
    return {(str(r["search"]), round(float(r["m"]), 4)): float(r["peak"])
            for r in truth.get("_per_mass", []) if r.get("peak") is not None}


# Characteristic scale (in dex, i.e. log10 g) for turning a distance-to-
# reference into a continuous [0,1] closeness. Overridable per check via the
# `dex_scale` rubric param.
#
# 3.0, not 1.0: with scale 1 the credit exp(-dist) is numerically dead beyond
# ~3 dex, so every trial whose yields are off by more than a factor of 1000
# scores the same zero no matter how much better one of them is. Weak models
# live in exactly that 1-15 dex range, which made the stage blind where it was
# most needed. At 3.0 a 1-dex miss reads 0.72, 3 dex 0.37, 10 dex 0.04.
_DEX_SCALE = 3.0


# Credit awarded to a distance sitting exactly ON a stage's tolerance. The
# tolerance is "acceptable", not "perfect", so this is high but < 1: it leaves
# headroom above, which is what keeps the top of the scale from saturating.
_CREDIT_AT_TOL = 0.8


def _closeness(dex: float, tol: float = 0.0, scale: float = None) -> float:
    """Map a non-negative log10 distance to [0,1] (1 = exact, 0 = far).

    The stage's OWN tolerance sets the decay scale: credit = exp(-dex/(K*tol))
    with K chosen so that dex == tol scores _CREDIT_AT_TOL. A tighter stage
    therefore decays faster, which is what makes the coarse/mid/fine ladder
    three genuinely different measurements.

    Previously the credit used a single global scale and ignored `tol`
    entirely, so coarse/mid/fine returned the identical number on every trial
    and 60% of the rubric weight was one measurement counted three times.

    Note the tolerance is a scale, not a free zone: giving full credit
    everywhere inside it saturates the top of the range and makes a
    near-perfect trial indistinguishable from a perfect one.
    """
    if tol and tol > 0.0:
        k = -1.0 / math.log(_CREDIT_AT_TOL)
        return math.exp(-max(0.0, dex) / (k * tol))
    scale = _DEX_SCALE if scale is None else scale
    return math.exp(-max(0.0, dex) / scale)


_SEARCH_ALIASES = {
    # dimuon / two-track search -> canonical "mumu"
    "mumu": "mumu", "mu_mu": "mumu", "dimuon": "mumu", "di_muon": "mumu",
    "two_track": "mumu", "twotrack": "mumu", "mm": "mumu", "muon": "mumu",
    # diphoton / photon search -> canonical "gg"
    "gg": "gg", "gamma_gamma": "gg", "gammagamma": "gg", "diphoton": "gg",
    "di_photon": "gg", "photon": "gg", "yy": "gg", "aa": "gg",
    "two_photons": "gg", "two_photon": "gg", "twophotons": "gg",
    "two_gamma": "gg", "2gamma": "gg", "2photon": "gg",
}


def _normalize_search(raw) -> str:
    """Map an agent's search label to the canonical 'mumu'/'gg' the reference
    uses, tolerating synonyms (dimuon/two_track, diphoton/photon, ...). An
    unrecognized label passes through unchanged, so a wrong search assignment
    still fails to match the reference key (the assignment is still graded)."""
    key = str(raw).strip().lower().replace("-", "_").replace(" ", "_")
    return _SEARCH_ALIASES.get(key, str(raw).strip())


def _load_scan(sandbox: Path, params: dict):
    """Read the agent's yield scans from a flat CSV (default results/scan.csv,
    columns search, m_phi, g, nsig; header names matched leniently) into
    {(search, round(m,4)): [(g, nsig), ...] sorted by g}. This is the bulk
    deliverable; the scalar probes live in results/answer.json. Returns
    (dict, None) on success or (None, error)."""
    import csv
    rel = params.get("scan_file", "results/scan.csv")
    p = Path(sandbox) / rel
    if not p.is_file():
        return None, f"missing scan file: {rel}"
    try:
        with p.open(newline="") as fh:
            rows = list(csv.reader(fh))
    except Exception as e:
        return None, f"unreadable scan CSV {rel}: {e}"
    if len(rows) < 2:
        return None, f"{rel} has a header but no data rows"
    header = [h.strip().lower() for h in rows[0]]

    def _col(names):
        for i, h in enumerate(header):
            if h in names:
                return i
        return None

    i_s, i_m, i_g, i_n = (_col(_SEARCH_KEYS), _col(_MASS_KEYS),
                          _col(_G_KEYS), _col(_N_KEYS))
    if None in (i_s, i_m, i_g, i_n):
        return None, (f"{rel} needs columns search, m_phi, g, nsig; "
                      f"got header {header}")
    out = {}
    for r in rows[1:]:
        if len(r) <= max(i_s, i_m, i_g, i_n):
            continue
        try:
            s = _normalize_search(r[i_s])
            m, g, n = float(r[i_m]), float(r[i_g]), float(r[i_n])
        except (TypeError, ValueError):
            continue
        if g > 0.0 and n == n and n >= 0.0:
            out.setdefault((s, round(m, 4)), []).append((g, n))
    for k in out:
        out[k] = sorted(out[k])
    if not out:
        return None, f"{rel} has no usable (search, m_phi, g, nsig) rows"
    return out, None


def check_llp_scan_present(sandbox: Path, params: dict):
    """results/scan.csv exists, parses, and carries usable
    (search, m_phi, g, nsig) rows -- the bulk yield deliverable."""
    scan, err = _load_scan(sandbox, params)
    if err:
        return False, err
    n = sum(len(v) for v in scan.values())
    return True, f"scan present: {n} rows across {len(scan)} (search, m) groups"


def check_llp_band_close(sandbox: Path, params: dict):
    """The reach band derived from the agent's g-scan agrees with the
    reference band in log-g. For each (search, m) whose reference band is a
    finite [g_lo, g_hi], the grader root-finds the agent's N_sig = target
    crossings and requires the mean |Delta log10 g| over the available branch
    endpoints to be <= `dex_tol`; passes if >= `min_fraction` do."""
    truth, err = _load_truth(params)
    if err:
        return False, err
    reach, err = _load_scan(sandbox, params)
    if err:
        return False, err
    target = float(params.get("target", truth.get("n_target", 3.0)))
    dex_tol = float(params.get("dex_tol", 0.30))
    min_fraction = float(params.get("min_fraction", 1.0))
    dex_scale = float(params.get("dex_scale", _DEX_SCALE))
    bands = _truth_bands(truth)
    reach_masses = [(k, b) for k, b in bands.items()
                    if isinstance(b, (list, tuple)) and b and b[0]]
    if not reach_masses:
        return False, "reference has no finite reach band"
    graded = npass = 0
    worst = None
    per_band, dists, closeness_vals, n_unclosed = {}, [], [], []
    for (key, b) in reach_masses:
        graded += 1
        klabel = f"{key[0]}@{key[1]}"
        scan = reach.get(key)
        dist = None
        unclosed = False
        if scan:
            g_lo_a, g_hi_a = _crossings(scan, target)
            if g_lo_a is not None:
                g_lo_t = float(b[0])
                g_hi_t = float(b[1]) if len(b) > 1 and b[1] else None
                ds = [abs(math.log10(g_lo_a / g_lo_t))]
                if g_hi_t:
                    if g_hi_a:
                        ds.append(abs(math.log10(g_hi_a / g_hi_t)))
                    else:
                        # The scan never fell back through the target, so the
                        # agent's band does not close: its actual claim is
                        # "excluded from g_lo up to at least the top of my
                        # grid". Score that claim against the reference
                        # ceiling instead of dropping the endpoint.
                        #
                        # Dropping it (the previous behaviour) graded the trial
                        # on the lower edge alone -- the easier one, since the
                        # weak-coupling rise is steep and well localized. That
                        # EXCUSED the exact failure the task warns about
                        # (a g-grid too narrow to bracket the band) and
                        # systematically flattered whichever arm truncated more.
                        unclosed = True
                        g_top = max(g for g, _n in scan)
                        ds.append(abs(math.log10(g_top / g_hi_t)))
                dist = sum(ds) / len(ds)
        if dist is None:
            # Agent produced no reach band here: infinite distance -> closeness 0.
            per_band[klabel] = None
            closeness_vals.append(0.0)
            continue
        per_band[klabel] = round(dist, 3)
        dists.append(dist)
        if unclosed:
            n_unclosed.append(klabel)
        closeness_vals.append(_closeness(dist, tol=dex_tol, scale=dex_scale))
        if worst is None or dist > worst[0]:
            worst = (dist, key)
        # An unclosed band never counts as a pass however close its edges land:
        # the reference band is bounded and the agent has not shown a ceiling.
        if dist <= dex_tol and not unclosed:
            npass += 1
    frac = npass / graded if graded else 0.0
    closeness = sum(closeness_vals) / len(closeness_vals) if closeness_vals else 0.0
    mean_dex = (sum(dists) / len(dists)) if dists else None
    metrics = {
        "closeness": round(closeness, 4),        # [0,1]; no-contour bands = 0
        "mean_dex": (round(mean_dex, 4) if mean_dex is not None else None),
        # Canonical distance surfaced generically by the harness alongside the
        # continuous credit (see StageGrade.metrics convention): the raw
        # distance-to-reference and its human label/unit.
        "distance": (round(mean_dex, 4) if mean_dex is not None else None),
        "distance_label": "dex (log10 g)",
        "n_bands": graded,
        "n_no_contour": graded - len(dists),
        "n_unclosed": len(n_unclosed),           # band never fell back below target
        "unclosed": sorted(n_unclosed),
        "per_band_dex": per_band,                # null = no agent reach band
        "dex_scale": dex_scale,
        "dex_tol": dex_tol,                      # credit is free inside this
    }
    utxt = f"; {len(n_unclosed)} unclosed" if n_unclosed else ""
    wtxt = f"; worst {worst[1]} {worst[0]:.2f} dex{utxt}" if worst else utxt
    return frac >= min_fraction, (
        f"{npass}/{graded} reach bands within {dex_tol} dex "
        f"(need >={min_fraction:.0%}); closeness {closeness:.2f}{wtxt}"), metrics


def check_llp_peak_close(sandbox: Path, params: dict):
    """Grid-free channel-completeness check: the agent's PEAK N_sig over its
    g-scan (max over g) agrees with the reference peak within `factor` in log
    space for >= `min_fraction` of (search, m) with reference m <= `max_mass`
    and peak > `floor`. Catches a dropped production channel even at masses
    that are null-for-reach, where the band check is blind."""
    truth, err = _load_truth(params)
    if err:
        return False, err
    reach, err = _load_scan(sandbox, params)
    if err:
        return False, err
    factor = float(params.get("factor", 2.0))
    min_fraction = float(params.get("min_fraction", 1.0))
    floor = float(params.get("floor", 0.0))
    max_mass = float(params.get("max_mass", float("inf")))
    dex_scale = float(params.get("dex_scale", _DEX_SCALE))
    ltol = math.log(factor)
    dex_tol = ltol / math.log(10.0)   # the same tolerance, expressed in dex
    peaks_t = _truth_peaks(truth)
    graded = npass = 0
    worst = None
    per_peak, dexes, closeness_vals = {}, [], []
    for key, pk_t in peaks_t.items():
        _s, m = key
        if pk_t <= floor or m > max_mass:
            continue
        graded += 1
        klabel = f"{key[0]}@{key[1]}"
        scan = reach.get(key)
        pk_a = max((n for _g, n in scan), default=0.0) if scan else 0.0
        if pk_a <= 0.0:
            per_peak[klabel] = None            # no agent yield here
            closeness_vals.append(0.0)
            continue
        d = abs(math.log(pk_a / pk_t))         # natural log
        d_dex = d / math.log(10.0)             # report in dex for consistency
        per_peak[klabel] = round(d_dex, 3)
        dexes.append(d_dex)
        closeness_vals.append(_closeness(d_dex, tol=dex_tol, scale=dex_scale))
        if worst is None or d > worst[0]:
            worst = (d, key)
        if d <= ltol:
            npass += 1
    frac = npass / graded if graded else 0.0
    closeness = sum(closeness_vals) / len(closeness_vals) if closeness_vals else 0.0
    mean_dex = (sum(dexes) / len(dexes)) if dexes else None
    metrics = {
        "closeness": round(closeness, 4),
        "mean_dex": (round(mean_dex, 4) if mean_dex is not None else None),
        "distance": (round(mean_dex, 4) if mean_dex is not None else None),
        "distance_label": "dex (log10 N_sig)",
        "n_peaks": graded,
        "n_no_yield": graded - len(dexes),
        "per_peak_dex": per_peak,
        "dex_scale": dex_scale,
        "dex_tol": round(dex_tol, 4),            # credit is free inside this
    }
    wtxt = f"; worst {worst[1]} x{math.exp(worst[0]):.2f}" if worst else ""
    return frac >= min_fraction, (
        f"{npass}/{graded} peak yields within x{factor} "
        f"(need >={min_fraction:.0%}); closeness {closeness:.2f}{wtxt}"), metrics


def check_llp_no_spurious_reach(sandbox: Path, params: dict):
    """The mirror of band_close: at every (search, m) where the reference has
    NO reach band, the agent must not claim one.

    band_close only iterates over reference masses that HAVE a finite band, so
    a trial that invents an exclusion where the reference sees none was never
    graded at all -- and claiming sensitivity you do not have is the most
    consequential error a reach study can make. Credit is the fraction of
    null-band points left correctly empty, attenuated by how much spurious
    coupling range was claimed (a sliver over threshold is not the same
    mistake as a decade of invented exclusion).
    """
    truth, err = _load_truth(params)
    if err:
        return False, err
    reach, err = _load_scan(sandbox, params)
    if err:
        return False, err
    target = float(params.get("target", truth.get("n_target", 3.0)))
    dex_scale = float(params.get("dex_scale", _DEX_SCALE))
    min_fraction = float(params.get("min_fraction", 1.0))
    bands = _truth_bands(truth)
    null_masses = [k for k, b in bands.items()
                   if not (isinstance(b, (list, tuple)) and b and b[0])]
    if not null_masses:
        return True, "reference has no null-band points to check", {
            "closeness": 1.0, "n_null": 0, "n_spurious": 0, "spurious": {}}
    graded = len(null_masses)
    spurious, creds = {}, []
    for key in null_masses:
        klabel = f"{key[0]}@{key[1]}"
        scan = reach.get(key)
        g_lo_a, g_hi_a = _crossings(scan, target) if scan else (None, None)
        if g_lo_a is None:
            creds.append(1.0)                    # correctly claims nothing
            continue
        # Width of the invented band, in dex; an unclosed one runs to the grid top.
        g_hi = g_hi_a or max(g for g, _n in scan)
        width = abs(math.log10(g_hi / g_lo_a)) if g_hi > g_lo_a else 0.0
        spurious[klabel] = round(width, 3)
        creds.append(_closeness(width, scale=dex_scale))
    n_bad = len(spurious)
    closeness = sum(creds) / len(creds) if creds else 1.0
    frac = (graded - n_bad) / graded if graded else 1.0
    metrics = {
        "closeness": round(closeness, 4),
        "distance": (round(sum(spurious.values()) / n_bad, 4) if n_bad else 0.0),
        "distance_label": "dex (log10 g) of invented band",
        "n_null": graded,
        "n_spurious": n_bad,
        "spurious": dict(sorted(spurious.items())),
    }
    stxt = f"; invented {', '.join(sorted(spurious))}" if spurious else ""
    return frac >= min_fraction, (
        f"{graded - n_bad}/{graded} null-reach points left empty "
        f"(need >={min_fraction:.0%}){stxt}"), metrics


def check_llp_channel_coverage(sandbox: Path, params: dict):
    """Did the pipeline produce ANY yield for every (search, m) the reference
    reaches? A dropped production channel (vector, charm) or a whole search
    silently missing from the scan is a physics failure independent of how
    accurate the surviving numbers are -- `peak_close` folds it into a
    magnitude comparison, and `band_close` is blind to it wherever the
    reference band is null. This isolates it: credit IS the covered fraction.
    """
    truth, err = _load_truth(params)
    if err:
        return False, err
    reach, err = _load_scan(sandbox, params)
    if err:
        return False, err
    floor = float(params.get("floor", 0.0))
    max_mass = float(params.get("max_mass", float("inf")))
    min_fraction = float(params.get("min_fraction", 1.0))
    peaks_t = _truth_peaks(truth)
    graded = 0
    covered, missing = [], []
    for key, pk_t in peaks_t.items():
        _s, m = key
        if pk_t <= floor or m > max_mass:
            continue
        graded += 1
        scan = reach.get(key)
        has = bool(scan) and any(n > 0.0 for _g, n in scan)
        (covered if has else missing).append(f"{key[0]}@{key[1]}")
    frac = len(covered) / graded if graded else 0.0
    metrics = {
        "closeness": round(frac, 4),          # continuous credit = coverage
        "n_channels": graded,
        "n_covered": len(covered),
        "missing": sorted(missing),
    }
    mtxt = f"; missing {', '.join(sorted(missing))}" if missing else ""
    return frac >= min_fraction, (
        f"{len(covered)}/{graded} (search, m) points carry a yield "
        f"(need >={min_fraction:.0%}){mtxt}"), metrics


def check_llp_reach_plot(sandbox: Path, params: dict):
    """The requested sensitivity figure exists and actually contains a plot.

    The task asks for a shaded exclusion region in the (g, m_phi) plane, and it
    is the only artifact a human can audit at a glance -- but agents produce it
    inconsistently, and a blank or axes-only figure is indistinguishable from a
    good one by file presence alone. This grades the figure MECHANICALLY, never
    aesthetically: it is a real PDF, it carries drawing content, it carries text
    (axis labels / ticks), and it contains filled regions -- the shading the
    task explicitly asks for, which a line-only or empty plot lacks.

    Thresholds sit ~8x below the minimum observed across 35 real agent plots, so
    they fail a broken figure without false-failing a plain one. Credit is the
    fraction of criteria met, so a thin-but-real plot scores partially rather
    than being judged on style.
    """
    import re
    import zlib

    rel = params.get("file", "results/reach.pdf")
    path = Path(sandbox) / rel
    crit = {"exists": False, "is_pdf": False, "has_drawing": False,
            "has_text": False, "has_shading": False}
    if not path.is_file():
        return False, f"no figure at {rel}", {
            "closeness": 0.0, "criteria": crit,
            "distance_label": "fraction of plot criteria met"}
    raw = path.read_bytes()
    crit["exists"] = True
    crit["is_pdf"] = raw[:5] == b"%PDF-" and len(raw) >= int(params.get("min_bytes", 2048))

    ops = fills = 0
    n_text = 0
    for st in re.findall(rb"stream\r?\n(.*?)endstream", raw, re.S):
        try:
            d = zlib.decompress(st)
        except Exception:
            d = st
        ops += len(re.findall(rb"(?m)\b[ml]\b", d))
        fills += len(re.findall(rb"(?m)\b(?:f|f\*|B|B\*)\b", d))
        n_text += len(re.findall(rb"\((?:[^()\\]|\\.)*\)\s*Tj", d))
    # Calibrated against 35 real agent plots (draw >= 386, fills >= 52,
    # text >= 35) versus deliberately degenerate figures rendered with the same
    # backend: bare log-log axes score (94, 28, 12) and a single plotted line
    # (111, 31, 15). Matplotlib's own axes frame and background patch already
    # produce draw ops, fills and tick text, so a floor near zero passes an
    # empty figure -- these thresholds sit between the degenerate cases and the
    # real ones. They are backend-sensitive by nature; all three are params, so
    # a benchmark whose agents plot differently can retune without code change.
    crit["has_drawing"] = ops >= int(params.get("min_draw_ops", 150))
    crit["has_text"] = n_text >= int(params.get("min_text", 20))
    crit["has_shading"] = fills >= int(params.get("min_fills", 40))

    frac = sum(1 for v in crit.values() if v) / len(crit)
    missing = [k for k, v in crit.items() if not v]
    metrics = {"closeness": round(frac, 4), "criteria": crit,
               "draw_ops": ops, "fills": fills, "text_fragments": n_text,
               "bytes": len(raw),
               "distance_label": "fraction of plot criteria met"}
    return (not missing), (
        f"{len(crit) - len(missing)}/{len(crit)} plot criteria met"
        + (f"; missing {', '.join(missing)}" if missing else "")), metrics


def check_llp_scaling(sandbox: Path, params: dict):
    """Structural gate (grid-free): (1) at least one gg-search scan carries a
    positive yield (the below-threshold diphoton channel is present), and
    (2) where a low-g tail exists, the weak-coupling rise is N_sig ~ g^4 --
    the log-log slope of the two lowest-g positive points lies in [lo, hi] --
    for >= `min_fraction` of scans."""
    reach, err = _load_scan(sandbox, params)
    if err:
        return False, err
    lo = float(params.get("slope_lo", 3.0))
    hi = float(params.get("slope_hi", 5.0))
    min_fraction = float(params.get("min_fraction", 0.5))
    if not reach:
        return False, "no scan rows"
    has_gg = any(s == "gg" and any(n > 0.0 for _g, n in scan)
                 for (s, _m), scan in reach.items())
    if not has_gg:
        return False, "no positive below-threshold gg yield"
    checked = good = 0
    for scan in reach.values():
        pos = [(g, n) for g, n in scan if n > 0.0]
        if len(pos) < 2 or pos[1][0] <= pos[0][0]:
            continue
        (g0, n0), (g1, n1) = pos[0], pos[1]
        slope = (math.log(n1) - math.log(n0)) / (math.log(g1) - math.log(g0))
        checked += 1
        if lo <= slope <= hi:
            good += 1
    if checked == 0:
        return True, "gg present; no low-g tail available to test g^4 slope"
    frac = good / checked
    return frac >= min_fraction, (
        f"gg present; g^4 slope in [{lo},{hi}] for {good}/{checked} scans "
        f"(need >={min_fraction:.0%})")



# --------------------------------------------------------------------------
# calibrated-distance checks (see benchmarks/llp_forward/soln/notes/accuracy_metric.tex)
#
# These score ACCURACY as a distance standardised by the reference's own
# Monte-Carlo precision, instead of against a hand-chosen tolerance. sigma is
# measured by comparing two independent MC estimates of the same physics
# (truth.json, 2e6-event flux vs fine_reach_contour.json, 3.9e5) and
# deconvolving the sample-size ratio; it is NOT a free parameter.
#
# Reported metrics: `distance` (median |dex|), `z` (= distance / sigma),
# `coverage` (fraction of graded points answered) and `closeness`
# (= exp(-z^2/2), the likelihood under "the agent did the same calculation and
# differs only by MC noise"). The rubric consumes `closeness`; a reader should
# quote `distance` and `z`.
# --------------------------------------------------------------------------
def _standardise(dists, sigma, z_crit, n_graded, n_cov, signed=None):
    """Turn per-point residuals into a score, a test, and a diagnosis.

    `dists` are |log10(agent/reference)| in decades; `signed` are the same
    residuals WITH their sign, when the caller can supply them.

    THE SCORE is 10^-D with D the median |dex|, which is exactly the
    reciprocal of the median factor the agent is off by: exact -> 1.000,
    factor 2 -> 0.500, factor 10 -> 0.100. It has no free parameter -- the only
    choice is the base, and that is already the unit D is quoted in. And since
    x -> 10^-x is strictly monotone, quantiles commute with it, so scoring per
    point then aggregating equals aggregating then scoring; the reported D and
    the reported score cannot disagree.

    This replaces exp(-z^2/2). Once the reference was rebuilt to
    sigma ~ 0.002 dex, that mapping returned exactly 0.000 for every arm of the
    2026-08 campaign -- correctly, since the agents' errors are SYSTEMATIC and
    properly computed error bars make a systematic look MORE significant, not
    less. A score has to degrade gracefully; a test statistic must not.

    z IS STILL COMPUTED, as a test rather than a score: "is this discrepancy
    real, or could it be sampling noise?" It earns its place -- on the
    contour's weak-coupling edge the best tooled cells sit at z ~ 1, i.e.
    consistent with having done the same calculation, while everything else is
    z >> 1 and therefore systematically displaced.

    BIAS AND SCATTER decompose D when signed residuals are available:

        d_i = bias + r_i,   bias = median(d_i),   scatter = median|d_i - bias|

    D alone cannot tell "uniformly off by a clean factor" from "randomly wrong
    by the same amount", and those are different results: the first is a
    normalisation or convention slip, the second is a failure to reproduce the
    functional form. On the 2026-08 campaign the core arms sat at
    |bias|/D ~ 1.00 with scatter 0.015-0.057 dex -- the whole error was one
    constant factor, with the shape right to a few percent.
    """
    if not dists:
        return False, "no graded point produced a usable value", {
            "closeness": 0.0, "distance": None, "z": None, "coverage": 0.0}
    d = statistics.median(dists)
    z = d / float(sigma)
    cov = n_cov / n_graded if n_graded else 0.0
    metrics = {
        "closeness": 10.0 ** (-d),
        "closeness_label": "10^-D = 1 / (median factor off)",
        "distance": round(d, 5),
        "distance_label": "median |dex| vs reference",
        "z": round(z, 3),
        "z_label": "D / sigma -- consistency TEST, not the score",
        "coverage": round(cov, 4),
        "n_covered": n_cov,
        "n_graded": n_graded,
    }
    evidence = (f"median |dex| = {d:.4f} -> score {10.0 ** (-d):.3f} "
                f"(off by x{10.0 ** d:.2f}); z = {z:.2f} "
                f"(sigma = {sigma}); coverage {n_cov}/{n_graded}")
    if signed:
        b = statistics.median(signed)
        sc = statistics.median([abs(x - b) for x in signed])
        metrics["bias"] = round(b, 5)
        metrics["bias_factor"] = round(10.0 ** b, 5)
        metrics["scatter"] = round(sc, 5)
        metrics["bias_label"] = ("median SIGNED dex: a uniform offset, i.e. a "
                                 "normalisation/convention error")
        metrics["scatter_label"] = ("median |dex - bias|: the shape error, "
                                    "what is left after the offset")
        evidence += (f"; bias {b:+.4f} dex (x{10.0 ** b:.3f}), "
                     f"scatter {sc:.4f} dex")
    return (z <= float(z_crit) and cov >= 1.0), evidence, metrics


def check_llp_yield_distance(sandbox: Path, params: dict):
    """Yield accuracy as a calibrated distance, evaluated AT THE REFERENCE'S OWN
    DECLARED (search, m_phi, g) POINTS.

    Deliberately NOT against `_per_mass.peak`. That field is the maximum of the
    reference's internal 400-point scan over g in [1e-9, 1], taken at a coupling
    the declared point set never samples; comparing it to the maximum of an
    agent's own grid compares two different quantities on two different grids.
    On the 2026-08 campaign it reported ~0.48 dex for cells whose band edges
    agree with the reference to 0.005-0.03 dex -- i.e. it was measuring the
    mismatch, not the physics.

    Here the agent's scan is interpolated in log-log onto the reference's own
    couplings, so both sides are evaluated at the same (search, m_phi, g). 48
    graded points instead of 12, and no grid dependence.
    """
    truth, err = _load_truth(params)
    if err:
        return False, err
    reach, err = _load_scan(sandbox, params)
    if err:
        return False, err
    sigma = params.get("sigma", 0.09)
    z_crit = params.get("z_crit", 3.0)

    declared = {}
    for pt in truth.get("points", []):
        key = (str(pt["search"]), round(float(pt["m_phi"]), 4))
        declared.setdefault(key, []).append((float(pt["g"]), float(pt["nsig"])))
    n_graded = sum(len(v) for v in declared.values())

    dists, signed, ncov = [], [], 0
    for key, pts in declared.items():
        scan = reach.get(key)
        if not scan:
            continue
        usable = [(g, n) for g, n in scan if g > 0 and n > 0]
        if len(usable) < 2:
            continue
        usable.sort()
        lg = [math.log10(g) for g, _ in usable]
        ln = [math.log10(n) for _, n in usable]
        for g, n in pts:
            if n <= 0:
                continue
            x = math.log10(g)
            if x < lg[0] or x > lg[-1]:      # outside the agent's scan range
                continue
            # linear interpolation in log-log
            i = max(1, min(len(lg) - 1, next(j for j in range(1, len(lg)) if lg[j] >= x)))
            f = (x - lg[i - 1]) / (lg[i] - lg[i - 1]) if lg[i] != lg[i - 1] else 0.0
            resid = ln[i - 1] + f * (ln[i] - ln[i - 1]) - math.log10(n)
            dists.append(abs(resid))
            signed.append(resid)
            ncov += 1
    return _standardise(dists, sigma, z_crit, n_graded, ncov, signed=signed)


def check_llp_contour_distance(sandbox: Path, params: dict):
    """Reach-contour accuracy as a calibrated distance, replacing the
    coarse/mid/fine ladder. Those three stages scored ONE measurement at three
    hand-chosen thresholds for 0.40 of the rubric weight.

    `edge` selects which boundary is graded: 'lower', 'upper', or 'both'.
    THE TWO EDGES SHOULD BE GRADED SEPARATELY. They are different physics --
    the lower edge is production-limited, the upper is lifetime-limited -- and
    they respond differently to method. On the 2026-08 campaign a single trial
    sat at 0.0028 dex on the lower edge and 0.066 on the upper, a factor 19,
    so pooling them turned a bimodal distribution into a misleading unimodal
    one and hid the campaign's most informative result. 'both' is kept only for
    continuity with the earlier rubric."""
    truth, err = _load_truth(params)
    if err:
        return False, err
    reach, err = _load_scan(sandbox, params)
    if err:
        return False, err
    bands = _truth_bands(truth)
    target = float(params.get("target", truth.get("n_target", 3.0)))
    sigma = params.get("sigma", 0.0224)
    z_crit = params.get("z_crit", 3.0)
    edge = str(params.get("edge", "both")).lower()
    if edge not in ("lower", "upper", "both"):
        return False, f"unknown edge {edge!r} (lower|upper|both)"
    graded = [k for k, b in bands.items() if b and b[0]]
    dists, signed, ncov = [], [], 0
    for k in graded:
        scan = reach.get(k)
        if not scan:
            continue
        lo, hi = _crossings(scan, target)
        if not (lo and hi):
            continue
        ncov += 1
        r_lo = math.log10(lo / bands[k][0])
        r_hi = math.log10(hi / bands[k][1])
        take = {"lower": [r_lo], "upper": [r_hi], "both": [r_lo, r_hi]}[edge]
        dists += [abs(r) for r in take]
        signed += take
    return _standardise(dists, sigma, z_crit, len(graded), ncov, signed=signed)

CHECKS = {
    "glob_present": check_glob_present,
    "llp_value": check_llp_value,
    "llp_formula": check_llp_formula,
    "llp_ctau_pair": check_llp_ctau_pair,
    "llp_scan_present": check_llp_scan_present,
    "llp_band_close": check_llp_band_close,
    "llp_peak_close": check_llp_peak_close,
    "llp_channel_coverage": check_llp_channel_coverage,
    "llp_no_spurious_reach": check_llp_no_spurious_reach,
    "llp_yield_distance": check_llp_yield_distance,
    "llp_contour_distance": check_llp_contour_distance,
    "llp_reach_plot": check_llp_reach_plot,
    "llp_scaling": check_llp_scaling,
    # legacy pinned-grid checks (kept for backward compatibility)
    "llp_nsig_filled": check_llp_nsig_filled,
    "llp_nsig_close": check_llp_nsig_close,
}

# presence gates the continue-nudge and never reads the oracle;
# correctness consults truth.json.
ROLES = {
    "glob_present": "presence",
    "llp_value": "correctness",
    "llp_formula": "correctness",
    "llp_ctau_pair": "correctness",
    "llp_scan_present": "presence",
    "llp_band_close": "correctness",
    "llp_peak_close": "correctness",
    "llp_channel_coverage": "correctness",
    "llp_no_spurious_reach": "correctness",
    "llp_yield_distance": "correctness",
    "llp_contour_distance": "correctness",
    "llp_reach_plot": "presence",
    "llp_scaling": "correctness",
    "llp_nsig_filled": "presence",
    "llp_nsig_close": "correctness",
}
