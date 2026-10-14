# `symbolic` campaign

From the repository root, open this campaign in the toolbench dashboard:

```bash
toolbench dashboard campaigns/symbolic/trials --port 0
```

The `--port 0` option automatically selects an available port and prints the dashboard URL in the terminal. Open that URL in your browser, select a run, then select a trial to inspect its grades. If toolbench is not installed, follow the [Quickstart](../../README.md#quickstart). Viewing the campaign does not require an agent login or HEPTAPOD.

The checkout includes the score records. To inspect transcripts and preserved files, download `hepbench-trials-symbolic.tar.gz` from [Releases](https://github.com/tonymenzo/hepbench/releases) and extract it from the repository root, replacing the path with your downloaded file:

```bash
tar xzf /path/to/hepbench-trials-symbolic.tar.gz -C campaigns/symbolic
```

The trial records contain the current grades; saved summaries predate a regrade. See [Regrading](#regrading) below.

## Campaign

This campaign compares built-in tools with HEPTAPOD on the symbolic benchmark family: three configurations, ten trials per task and configuration, and 280 trials in total. Comparisons use the eight two-body tasks supported by the `eda` toolset.

| Directory | Harness | Model | Loadout | Tasks | Trials |
|---|---|---|---|---|---|
| `claude-code_haiku4.5` | Claude Code 2.1.286 | `claude-haiku-4-5-20251001` | `core_only` | 10 | 100 |
| `claude-code_haiku4.5` | Claude Code 2.1.287 | `claude-haiku-4-5-20251001` | `tools_eda` | 8 | 80 |
| `codex_gpt5.5` | Codex 0.152.1 | `gpt-5.5`, medium effort | `core_only` | 10 | 100 |

All runs use the `unguided` variant, seeds 1001 to 1010, and subscription access. A trial passes only if it passes every stage. The domain-tool configuration uses HEPTAPOD 3.0.0 through the `symbolic-eda` loadout, which serves `ComputeDecayRate` and `ComputeCrossSection`. The MCP preflight confirms that two tools are served for every run.

## Task coverage

The three configurations share eight tasks. The derivative couplings in `decay_S_to_SpV` and `decay_V_to_SS` are not supported by the `eda` generator, so these tasks are excluded from the domain-tool configuration. Both configurations using built-in tools include these two additional tasks. Their records are retained, but comparisons are restricted to the eight shared tasks.

## Contents

| Path | What it is |
|---|---|
| `trials/<harness>_<model>/<run_id>/` | Per-run ledgers: one run per task and loadout; `trials.jsonl`, `manifest.json`, `plan.json`, `status.json`, and the summaries. |

The benchmark as graded is [`benchmarks/symbolic`](../../benchmarks/symbolic) as committed, including the ground truth.

The per-trial evidence (transcripts, artifacts, grades) is in the release asset `hepbench-trials-symbolic.tar.gz`; extracted into this directory it completes each run for `toolbench dashboard`.

## Regrading

The original grader rejected `Conjugate(...)` in submitted formulas, causing numerically equivalent answers to fail. The correction in `benchmarks/symbolic/_shared/checks.py` maps both spellings to `sympy.conjugate`, and all configurations were regraded with this correction. **`trials.jsonl` is authoritative.** The `summary.json` and `summary.txt` files predate the regrade and still carry the earlier numbers.

The Haiku arms ran at adjacent benchmark states that differ only in the `tools_eda` loadout's system-prompt addendum, so the core prompt is byte-identical across the three cells.
