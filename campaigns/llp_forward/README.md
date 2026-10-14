# `llp_forward` campaign

From the repository root, open this campaign in the toolbench dashboard:

```bash
toolbench dashboard campaigns/llp_forward/trials --port 0
```

The `--port 0` option automatically selects an available port and prints the dashboard URL in the terminal. Open that URL in your browser, select a run, then select a trial to inspect its grades. If toolbench is not installed, follow the [Quickstart](../../README.md#quickstart). Viewing the campaign does not require an agent login or HEPTAPOD.

The checkout includes the score records. To inspect transcripts and preserved files, download `hepbench-trials-llp_forward.tar.gz` from [Releases](https://github.com/tonymenzo/hepbench/releases) and extract it from the repository root, replacing the path with your downloaded file:

```bash
tar xzf /path/to/hepbench-trials-llp_forward.tar.gz -C campaigns/llp_forward
```

## Campaign

The tool ablation on the forward-LLP benchmark: `core_only` against `tools_defined` on the `bare` variant, four systems, five trials per cell, 40 trials. The `bare` variant ships one file, the output schema, and states everything the answer depends on in the user prompt, so the domain arm's advantage cannot come from scaffolding the arms share.

| Directory | Harness | Model | Core arm | Domain arm | Trials |
|---|---|---|---|---|---|
| `claude-code_opus4.8` | Claude Code 2.1.225 | `claude-opus-4-8` | `core_only` | `tools_defined` | 10 |
| `claude-code_sonnet5` | Claude Code 2.1.226 | `claude-sonnet-5` | `core_only` | `tools_defined_unprompted` | 10 |
| `codex_gpt5.5` | Codex 0.146.0 | `gpt-5.5` | `core_only` | `tools_defined` | 10 |
| `codex_gpt5.6` | Codex 0.146.0 | `gpt-5.6-sol` | `core_only` | `tools_defined` | 10 |

All runs: variant `bare`, seeds 1001 to 1005, subscription access, toolbench 0.7.0. The toolkit served to the domain arm is HEPTAPOD 3.0.0 through the `forward-llp-defined` loadout: the `llp` pipeline, `PythiaFromRunCard`, and the run-card guide. The benchmark as graded is [`benchmarks/llp_forward`](../../benchmarks/llp_forward) as committed: regrading every trial's preserved artifacts under it reproduces the recorded stage credits and scores, apart from the weightless `pythia_ran` report in three trials whose flux files are among the omitted intermediates.

The Codex domain arms carry the `tools_defined` system-prompt addendum stating that a toolkit is served and preferred; without it neither GPT model called a domain tool. The Claude Code systems adopted the toolkit unprompted and ran without it. The addendum is recorded in every trial record.

## Contents

| Path | What it is |
|---|---|
| `trials/<harness>_<model>/<run_id>/` | Per-run ledgers: `trials.jsonl`, `manifest.json`, and the summaries. Both arms are in the same run. |

The per-trial evidence (transcripts, preserved sandboxes, grades) is in the release asset `hepbench-trials-llp_forward.tar.gz`; extracted into this directory it completes each run for `toolbench dashboard`. Each trial's `prompts.json`, the system and user prompt as composed for that trial, was written into the asset after the campaign from the committed variant prompts and the loadout recorded in `trial.json`; toolbench 0.7.0 did not record it. Agent-written intermediates over 2 MiB are left out of the asset and listed, with hashes, in its `OMITTED.txt`; none is an input to any number in the paper.
