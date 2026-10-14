# `llp_forward` campaign

The single-axis tool ablation on the forward-LLP benchmark: `bare × core_only` against `bare × tools_defined` for four systems, five trials each, 40 trials. The out-of-the-box variant ships one file, the output contract, and states everything the answer depends on in the user prompt, so the domain arm's advantage cannot come from scaffolding the arms share.

| System | Harness | Core arm | Domain arm |
|---|---|---|---|
| Opus 4.8 | Claude Code | `core_only` | `tools_defined` |
| Sonnet 5 | Claude Code | `core_only` | `tools_defined_unprompted` |
| GPT-5.5 | Codex | `core_only` | `tools_defined` |
| GPT-5.6 | Codex | `core_only` | `tools_defined` |

The Codex domain arms carry the system-prompt addendum stating that a toolkit is served and preferred; without it neither GPT model called a domain tool. The Claude Code systems adopted the toolkit unprompted and ran without it. The addendum is recorded in every trial record.

## Contents

| Path | What it is |
|---|---|
| `campaign.yaml` | The ledger: every cell, its seeds, its validity, and the reason for each exclusion. |
| `config/` | The graded contract as run: `benchmark.yaml`, `checks.py`, the four harnesses, the loadouts, the variant, and the run-card guide served to the domain arm. |
| `dataset/` | The collected cells (`cells/*.json`), `index.json`, the verified Monte Carlo sample sizes, and the score table. |
| `graded_record.tar.gz` | The graded evidence of all 40 trials: answer files, yield scans, reach plots, per-trial grades, and audit logs. 3 MB. |
| `OMITTED.txt` | The ten agent-written flux intermediates over 2 MiB left out of the archive, with hashes. None is an input to any number in the paper. |

Transcripts and the full preserved sandboxes are in the release asset `hepbench-trials-llp_forward.tar.gz`.

## Reading the numbers

Every cell records the rubric fingerprint `6555a8797b4c` (sha256 of `benchmark.yaml` and `checks.py`), and every run was regraded under it and came back bit-identical. The noise floor comes from `benchmarks/llp_forward/soln/reference/manifest.json`, two independent same-size reference builds, which is the same source the rubric uses.

The graded distance statistic takes each trial's median |dex| and then the median across trials. The distance of a median curve drawn across trials is smaller, since it cancels their scatter, and is not the graded quantity.

One trial was rerun: GPT-5.6 seed 1001 originally scored zero by overwriting the supplied output schema and validating against its own. The replacement came from `toolbench resume` into the same run directory under the same seed, and the ledger records it.

An excluded Haiku 4.5 cell is recorded in `dataset/README.md`. One of its trials reached the ground truth through the git object store, which the deny-list did not then cover; toolbench now denies `.git` of every repository containing a benchmark.
