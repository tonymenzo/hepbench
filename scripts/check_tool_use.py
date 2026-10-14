"""
# scripts/check_tool_use.py is a part of HEPBench.
# Copyright (C) 2026 HEPBench authors (see AUTHORS for details).
# HEPBench is licensed under the GNU GPL v3 or later, see LICENSE for details.

Preflight for a tools arm: fail when any trial of a `tools_*` loadout in a run
made no call to the served domain toolkit (a tool name containing the prefix,
default "heptapod"). A tools arm that silently never saw its tools -- codex-cli
defers MCP tools behind tool_search, and a smoke trial then solved the task by
hand -- would otherwise be reported as a tools result.

    python scripts/check_tool_use.py runs/campaigns/<campaign>/<run>  [--prefix heptapod]

Exit status 0 when every tools-arm trial called the toolkit at least once.

Calls are also split into model writing (WriteToyModel, WriteFeynArtsModel,
FeynRulesToUFO, WriteMartinModel) and calculation (everything else). A trial
that only wrote a model did the physics by hand; in round 3 that was most
of the martin arm on loop_S_to_gamgam. Those trials are flagged
"MODEL ONLY", and `--require-calculation` makes them fail too.
"""

import argparse
import json
import sys
from pathlib import Path


def served(run: Path, prefix: str) -> set:
    """The toolkit's tool names the run served, with and without the prefix
    (claude-code records `OneLoopAmplitude`, the manifest `heptapod__OneLoopAmplitude`)."""
    import re
    text = (run / "manifest.json").read_text()
    names = set(re.findall(rf"{prefix}__(\w+)", text))
    return names | {f"{prefix}__{n}" for n in names}


#: Toolkit calls that only write or translate a model.
MODEL_TOOLS = {"WriteToyModel", "WriteFeynArtsModel", "FeynRulesToUFO", "WriteMartinModel"}


def tool_calls(trial: dict, names: set, prefix: str) -> tuple:
    """(model-writing calls, calculation calls) to the toolkit."""
    model = calc = 0
    for name, n in (trial.get("tool_calls_by_name") or {}).items():
        if not (name in names or name.split(".")[-1] in names or f"{prefix}__" in name):
            continue
        if name.split(".")[-1].split("__")[-1] in MODEL_TOOLS:
            model += n
        else:
            calc += n
    return model, calc


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[1])
    ap.add_argument("run_dirs", nargs="+", type=Path)
    ap.add_argument("--prefix", default="heptapod")
    ap.add_argument("--require-calculation", action="store_true",
                    help="also fail tools-arm trials whose only toolkit calls wrote a model")
    args = ap.parse_args()
    bad = 0
    for run in args.run_dirs:
        rows = [json.loads(line) for line in (run / "trials.jsonl").read_text().splitlines() if line.strip()]
        names = served(run, args.prefix)
        for t in rows:
            if not str(t.get("loadout", "")).startswith("tools_"):
                continue
            model, calc = tool_calls(t, names, args.prefix)
            status = "ok" if calc else "MODEL ONLY" if model else "NO TOOL CALLS"
            bad += (model + calc == 0) or (args.require_calculation and calc == 0)
            print(f"{status:14s} {run.name} {t['trial_id']}: {model} model + {calc} calculation "
                  f"{args.prefix} call(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
