#!/usr/bin/env python
"""
# scripts/audit_oracle_access.py is a part of HEPBench.
# Copyright (C) 2026 HEPBench authors (see AUTHORS for details).
# HEPBench is licensed under the GNU GPL v3 or later, see LICENSE for details.
"""
"""
Post-hoc oracle-access auditor for benchmark runs.

The benchmarks/symbolic family grades against a `ground_truth/truth.json`
committed in the repo. The agent's filesystem tools are jailed to its
sandbox, but RunPythonTool can `open()` an arbitrary path, so the answer
key is reachable in principle. This auditor closes the loop: it scans
every trial's recorded tool calls (transcript.jsonl.gz, which stores
full argument payloads) for any reference to oracle material — the
ground-truth files, the derivation scripts, the check sources, or
filesystem traversal/search that climbs out of the sandbox toward
`benchmarks/`.

Verdict per trial: CLEAN or FLAGGED (with the offending calls). With
`--zero`, flagged trials are rewritten to score 0.0 in a copy of
trials.jsonl (the original is preserved as trials.jsonl.orig), so the
headline metric cannot reward a trial that peeked.

This is a detection net, not a sandbox: it makes a successful cheat
visible and non-scoring rather than impossible. Run it after every
real (non-stub) symbolic run.

Usage:
    python scripts/audit_oracle_access.py runs/<run_id>
    python scripts/audit_oracle_access.py runs/<run_id> --zero
    python scripts/audit_oracle_access.py --latest
"""

import argparse
import gzip
import json
import re
import sys
from pathlib import Path

# Substrings that should never appear in a legitimate tool-call payload.
# Matched case-insensitively against the JSON-serialized args of each
# call. `results/` (the deliverable dir) and the prompt's own symbol
# names are intentionally NOT here.
ORACLE_TOKENS = [
    "truth.json",
    "ground_truth",
    "derivation.py",
    "_shared/checks.py",
    "dirac_numeric",
    "benchmarks/symbolic",   # absolute/relative path into the family
]

# Heuristic patterns for "reaching outside the sandbox" even without a
# literal oracle name — parent traversal combined with a read, or a
# filesystem-wide search. Tuned to flag, not to be bulletproof.
ORACLE_PATTERNS = [
    re.compile(r"\.\./\.\./\.\."),                 # climbing several levels
    re.compile(r"\bos\.walk\b"),
    re.compile(r"\b(glob|rglob)\b"),
    re.compile(r"\bsubprocess\b"),                 # shelling out from python
    re.compile(r"\bos\.system\b"),
    re.compile(r"\bfind\s+/"),                     # find / ...
    re.compile(r"/home/[^\"'\s]*/benchmarks"),     # absolute repo path
]


def _iter_calls(transcript: Path):
    with gzip.open(transcript, "rt") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("type") == "tool_call" or "name" in rec:
                yield rec


def _scan_args(args) -> list:
    """Return the list of reasons this call looks like oracle access."""
    blob = json.dumps(args, default=str).lower()
    reasons = []
    for tok in ORACLE_TOKENS:
        if tok.lower() in blob:
            reasons.append(f"token:{tok}")
    for pat in ORACLE_PATTERNS:
        if pat.search(blob):
            reasons.append(f"pattern:{pat.pattern}")
    return reasons


def audit_trial(trial_dir: Path) -> dict:
    transcript = trial_dir / "transcript.jsonl.gz"
    hits = []
    n_calls = 0
    if transcript.is_file():
        for rec in _iter_calls(transcript):
            n_calls += 1
            reasons = _scan_args(rec.get("args", {}))
            if reasons:
                hits.append({"name": rec.get("name"),
                             "t": rec.get("t"),
                             "reasons": sorted(set(reasons))})
    return {"trial": trial_dir.name, "n_calls": n_calls,
            "flagged": bool(hits), "hits": hits}


def audit_run(run_dir: Path) -> list:
    trials_dir = run_dir / "trials"
    if not trials_dir.is_dir():
        raise SystemExit(f"no trials/ under {run_dir}")
    return [audit_trial(d) for d in sorted(trials_dir.iterdir())
            if d.is_dir()]


def zero_flagged(run_dir: Path, results: list) -> int:
    """Rewrite trials.jsonl so flagged trials score 0.0 (and ok=False)."""
    flagged = {r["trial"] for r in results if r["flagged"]}
    if not flagged:
        return 0
    tj = run_dir / "trials.jsonl"
    if not tj.is_file():
        print(f"  (no trials.jsonl to rewrite under {run_dir})")
        return 0
    orig = run_dir / "trials.jsonl.orig"
    if not orig.exists():
        orig.write_text(tj.read_text())
    out, n = [], 0
    for line in tj.read_text().splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        if rec.get("trial_id") in flagged:
            rec["score"] = 0.0
            rec["ok"] = False
            rec["oracle_flagged"] = True
            n += 1
        out.append(json.dumps(rec))
    tj.write_text("\n".join(out) + "\n")
    return n


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir", nargs="?", help="runs/<run_id> directory")
    ap.add_argument("--latest", action="store_true",
                    help="audit the most recent run under runs/")
    ap.add_argument("--zero", action="store_true",
                    help="rewrite trials.jsonl to score flagged trials 0.0")
    ap.add_argument("--runs-root", default="runs")
    args = ap.parse_args(argv)

    if args.latest:
        roots = sorted(Path(args.runs_root).glob("*/"),
                       key=lambda p: p.name)
        roots = [p for p in roots if (p / "trials").is_dir()]
        if not roots:
            raise SystemExit("no runs found")
        run_dir = roots[-1]
    elif args.run_dir:
        run_dir = Path(args.run_dir)
    else:
        ap.error("give a run_dir or --latest")

    results = audit_run(run_dir)
    flagged = [r for r in results if r["flagged"]]
    print(f"run: {run_dir}")
    print(f"trials audited: {len(results)}   flagged: {len(flagged)}")
    for r in results:
        status = "FLAGGED" if r["flagged"] else "clean"
        print(f"  [{status}] {r['trial']}  ({r['n_calls']} calls)")
        for h in r["hits"]:
            print(f"      - {h['name']} @t={h['t']}: {', '.join(h['reasons'])}")

    if args.zero:
        n = zero_flagged(run_dir, results)
        print(f"zeroed {n} flagged trial(s) in trials.jsonl "
              f"(original -> trials.jsonl.orig)")

    # Exit non-zero if anything was flagged, so CI / scripts can gate.
    return 1 if flagged else 0


if __name__ == "__main__":
    sys.exit(main())
