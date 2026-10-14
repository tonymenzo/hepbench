#!/usr/bin/env python
"""
# scripts/token_io_analysis.py is a part of HEPBench.
# Copyright (C) 2026 HEPBench authors (see AUTHORS for details).
# HEPBench is licensed under the GNU GPL v3 or later, see LICENSE for details.
"""
"""
Token-I/O analysis across loadout arms (toolkits).

Aggregates per-trial token accounting from one or more run directories,
grouped by (model, loadout arm), and surfaces how the toolkit changes
input/output token cost. The motivating question: equipping the agent
with a domain toolkit (tools_nda, tools_eda, ...) injects tool schemas
into every turn and lengthens tool-call loops, so the INPUT-token cost
scales with toolkit size — often more than the toolkit saves in
reasoning. This makes that trade visible.

Per arm it reports, over its trials:
  in/out/cache   mean input, output, cache-read tokens
  n_tools        domain tools the arm resolved (from the run manifest),
                 i.e. the schema surface added on top of the harness core
  base_in        input tokens of the leanest trial (~ one-turn context:
                 system+user+schemas), an estimate of the fixed schema tax
  in_per_call    mean input tokens / tool call (context re-billing rate)
  reach          mean rubric score
  in_per_win     mean input tokens spent per fully-correct trial
                 (reach==1.0); inf if the arm never scored 1.0

Caveats it prints when relevant: prompt caching disabled (cache_read==0
inflates input on multi-turn loops), and small n.

Usage:
    python scripts/token_io_analysis.py runs/<run_id> [runs/<run_id> ...]
    python scripts/token_io_analysis.py --glob 'runs/*decay_S_to_FFbar*'
    python scripts/token_io_analysis.py --latest-of symbolic-decay_S_to_FFbar
    python scripts/token_io_analysis.py runs/<run_id> --csv out.csv
"""

import argparse
import csv as csvmod
import glob as globmod
import json
import statistics as stats
from collections import defaultdict
from pathlib import Path


def _load_manifest_tools(run_dir: Path) -> dict:
    """Map loadout name -> number of domain (non-core) tools resolved."""
    mf = run_dir / "manifest.json"
    out = {}
    if not mf.is_file():
        return out
    try:
        m = json.loads(mf.read_text())
    except json.JSONDecodeError:
        return out
    for cell in m.get("resolution", []):
        loadout = cell.get("loadout")
        n = sum(len(s.get("tools", [])) for s in cell.get("sources", []))
        if loadout is not None:
            out[loadout] = n
    return out


def _trials(run_dir: Path):
    tj = run_dir / "trials.jsonl"
    if not tj.is_file():
        return
    for line in tj.read_text().splitlines():
        line = line.strip()
        if line:
            yield json.loads(line)


def collect(run_dirs):
    """Return rows keyed by (model, arm) with accumulated trial dicts."""
    groups = defaultdict(list)
    tools_by_arm = {}
    for rd in run_dirs:
        rd = Path(rd)
        tmap = _load_manifest_tools(rd)
        tools_by_arm.update(tmap)
        for t in _trials(rd):
            model = t.get("model", "?")
            arm = t.get("condition", t.get("loadout", "?"))
            # The closed-book arm reuses condition "core_only" but a
            # different harness; key on harness too so it doesn't merge
            # into the open core_only arm.
            harness = t.get("harness", "?")
            closed = harness.endswith("_closed")
            arm_key = f"{arm} (closed)" if closed else arm
            groups[(model, arm_key)].append(t)
    return groups, tools_by_arm


def _mean(xs):
    xs = [x for x in xs if x is not None]
    return stats.mean(xs) if xs else 0.0


def summarize(groups, tools_by_arm):
    rows = []
    for (model, arm), trials in sorted(groups.items()):
        ins = [t.get("input_tokens", 0) for t in trials]
        outs = [t.get("output_tokens", 0) for t in trials]
        cache = [t.get("cache_read_tokens", 0) for t in trials]
        calls = [t.get("tool_calls", 0) for t in trials]
        scores = [t.get("score", 0.0) for t in trials]
        wins = [t for t in trials if t.get("score", 0.0) >= 0.999]
        in_per_win = (_mean([t.get("input_tokens", 0) for t in wins])
                      if wins else float("inf"))
        total_calls = sum(calls) or 1
        rows.append({
            "model": model, "arm": arm, "n": len(trials),
            "n_tools": tools_by_arm.get(arm, 0),
            "in_mean": _mean(ins), "out_mean": _mean(outs),
            "cache_mean": _mean(cache),
            "base_in": min(ins) if ins else 0,
            "in_per_call": sum(ins) / total_calls,
            "calls_mean": _mean(calls),
            "reach": _mean(scores),
            "wins": len(wins),
            "in_per_win": in_per_win,
        })
    return rows


def print_table(rows):
    hdr = (f"{'model':16} {'arm':12} {'n':>2} {'tools':>5} {'in_mean':>9} "
           f"{'out_mean':>8} {'base_in':>8} {'in/call':>8} {'calls':>5} "
           f"{'reach':>5} {'in/win':>9}")
    print(hdr)
    print("-" * len(hdr))
    for r in rows:
        ipw = "inf" if r["in_per_win"] == float("inf") else f"{r['in_per_win']:.0f}"
        print(f"{r['model']:16} {r['arm']:12} {r['n']:>2} {r['n_tools']:>5} "
              f"{r['in_mean']:>9.0f} {r['out_mean']:>8.0f} {r['base_in']:>8.0f} "
              f"{r['in_per_call']:>8.0f} {r['calls_mean']:>5.1f} "
              f"{r['reach']:>5.2f} {ipw:>9}")


def print_notes(groups, rows):
    any_cache = any(t.get("cache_read_tokens", 0)
                    for trials in groups.values() for t in trials)
    print()
    if not any_cache:
        print("NOTE: prompt caching is OFF in this data (cache_read==0). "
              "Input tokens are re-billed in full every turn, so in_mean "
              "scales with context size x tool-call loops; the toolkit's "
              "schema tax (base_in) is paid on every turn.")
    small = [r for r in rows if r["n"] < 3]
    if small:
        print(f"NOTE: {len(small)} arm(s) have n<3 trials — treat per-arm "
              "means as indicative, not significant.")


def main(argv=None):
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dirs", nargs="*", help="runs/<run_id> directories")
    ap.add_argument("--glob", help="glob over run dirs, e.g. 'runs/*foo*'")
    ap.add_argument("--latest-of",
                    help="benchmark name substring; use newest matching run")
    ap.add_argument("--runs-root", default="runs")
    ap.add_argument("--csv", help="also write the per-arm table to this CSV")
    args = ap.parse_args(argv)

    run_dirs = list(args.run_dirs)
    if args.glob:
        run_dirs += sorted(globmod.glob(args.glob))
    if args.latest_of:
        cands = sorted(p for p in Path(args.runs_root).glob("*")
                       if args.latest_of in p.name and (p / "trials.jsonl").is_file())
        if cands:
            run_dirs.append(str(cands[-1]))
    run_dirs = [d for d in dict.fromkeys(run_dirs)
                if (Path(d) / "trials.jsonl").is_file()]
    if not run_dirs:
        ap.error("no run dirs with trials.jsonl found")

    print("runs analyzed:")
    for d in run_dirs:
        print(f"  {d}")
    print()
    groups, tools_by_arm = collect(run_dirs)
    rows = summarize(groups, tools_by_arm)
    print_table(rows)
    print_notes(groups, rows)

    if args.csv:
        with open(args.csv, "w", newline="") as fh:
            w = csvmod.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        print(f"\nwrote {args.csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
