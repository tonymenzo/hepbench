# `symbolic` campaign

The core-to-tools delta on the symbolic family: three cells of ten trials per task over the eight two-body tasks the `eda` toolset supports.

| Cell | Harness | Model | Loadout | Tasks | Trials |
|---|---|---|---|---|---|
| `core_haiku` | Claude Code 2.1.286 | `claude-haiku-4-5-20251001` | `core_only` | 10 | 100 |
| `tools_haiku` | Claude Code 2.1.287 | `claude-haiku-4-5-20251001` | `tools_eda` | 8 | 80 |
| `core_gpt55` | Codex 0.152.1 | `gpt-5.5`, medium effort | `core_only` | 10 | 100 |

All cells: variant `unguided`, seeds 1001 to 1010, pass criterion all stages, subscription access. The toolkit served to the domain arm is HEPTAPOD 3.0.0 through the `symbolic-eda` loadout, exactly `ComputeDecayRate` and `ComputeCrossSection`; the MCP preflight reports two tools served for every run.

## Which tasks

The three cells share eight tasks. `decay_S_to_SpV` and `decay_V_to_SS` have derivative couplings the `eda` generator does not support, so the domain arm cannot run them; the two core cells ran them anyway, and their runs are included, but every comparison restricts to the eight shared tasks.

## Contents

| Path | What it is |
|---|---|
| `dataset/ground_truth/` | `truth.json` per task, as graded. |
| `trials/<cell>/<run>/` | Per-run ledgers: `trials.jsonl`, `manifest.json`, `plan.json`, `status.json`, and the summaries. |

The per-trial evidence (transcripts, artifacts, grades) is in the release asset `hepbench-trials-symbolic.tar.gz`; extracted into this directory it completes each run for `toolbench dashboard`.

## Regrading

The original grader rejected `Conjugate(...)` in a submitted formula, failing answers that were numerically identical to the ground truth. The fix in `benchmarks/symbolic/_shared/checks.py` maps both spellings onto `sympy.conjugate`, and every cell was regraded with it. **`trials.jsonl` is authoritative.** The `summary.json` and `summary.txt` files predate the regrade and still carry the earlier numbers.

The Haiku arms ran at adjacent benchmark states that differ only in the `tools_eda` loadout's system-prompt addendum, so the core prompt is byte-identical across the three cells.
