[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0) [![Python](https://img.shields.io/badge/Python-3.12%20|%203.13-blue.svg)](https://www.python.org/downloads/) [![Runs on](https://img.shields.io/badge/Runs%20on-toolbench-orange.svg)](https://github.com/tonymenzo/toolbench)

# **HEPBench**

**HEPBench** is a collection of **high-energy physics benchmarks for LLM agents**: tasks, scientific inputs, grading rubrics, and the campaign records behind the accompanying paper. Each benchmark is a self-contained directory that fixes the physics objective, the required output artifacts, a rerunnable ground truth, and a rubric that grades the submitted artifacts stage by stage.

Benchmarks run through [toolbench](https://github.com/tonymenzo/toolbench), which drives the agent harness, grades the results, and records every trial. Domain tools come from [HEPTAPOD](https://github.com/tonymenzo/heptapod), served at a pinned version by [toolbase](https://github.com/alexr314/toolbase). HEPBench contains no runner or metrics code of its own.

## Quickstart

You'll need **Python 3.12 or 3.13** and a logged-in coding agent, such as Claude Code or Codex. No API key is used.

Install toolbench and clone the benchmarks:

```bash
pip install "toolbench[toolbase]"
git clone https://github.com/tonymenzo/hepbench.git && cd hepbench
```

Check the wiring without spending tokens. The `stub` model writes no answer, so every score is zero:

```bash
toolbench run --benchmark benchmarks/symbolic/decay_S_to_SS \
    --model stub --loadouts core_only --n 1 --max-cost-usd 0 --dry-run
```

Run one task under Claude Code with the harness's own tools:

```bash
toolbench run --benchmark benchmarks/symbolic/decay_S_to_SS \
    --harnesses claude-code/default --model claude-opus-4-8 \
    --loadouts core_only --n 3 --max-cost-usd 5
```

Results land in `runs/<run_id>/`. Start with `summary.txt`; `trials.jsonl` holds one graded row per trial, `manifest.json` the resolved configuration, and `trials/` the transcripts and preserved artifacts. To watch a run, or browse a finished one:

```bash
toolbench dashboard
```

Comma-separate any axis to sweep it, for example `--loadouts core_only,tools_eda` for a tools ablation or `--harnesses claude-code/default,codex/default` for a cross-system comparison.

## Benchmarks

| Benchmark | Tasks | What the agent does |
|-----------|:---:|---|
| [`llp_forward`](benchmarks/llp_forward/) | 1 | Forward long-lived-particle reach for a muon-philic scalar: generate the forward meson flux with Pythia, decay it to the scalar across every open channel, propagate through a decay volume, and report signal yields and the sensitivity boundary. |
| [`symbolic`](benchmarks/symbolic/) | 14 | Tree-level decay widths and cross sections on generic toy field theories, returned as numerical values and closed forms. Ten two-body decays cover every renormalizable three-point vertex among scalars, fermions, and massive vectors. |

Every benchmark carries harness definitions for Claude Code, Codex, and the in-process [orchestral](https://github.com/orchestralAI/orchestral-core) harness, prompt variants along the scaffolding axis, and loadouts along the tools axis. Each benchmark's README gives its physics, deliverable, variants, and loadouts.

## Domain tools

The `tools_*` loadouts serve HEPTAPOD over MCP. Download `heptapod-3.0.0.tar.gz` from the [HEPTAPOD releases](https://github.com/tonymenzo/heptapod/releases) and install it:

```bash
tb install "/path/to/heptapod-3.0.0.tar.gz"
tb use heptapod@3.0.0
```

The loadouts under [`.toolbase/loadouts/`](.toolbase/loadouts/) apply automatically from the repository root:

| Loadout | Serves | Used by |
|---|---|---|
| `symbolic-eda` | `ComputeDecayRate`, `ComputeCrossSection` | `symbolic` `tools_eda` arm |
| `forward-llp-defined` | the `llp` bundle and `PythiaFromRunCard` | `llp_forward` `tools_defined` arm |
| `forward-llp-derived` | the above plus the `eda` bundle | `llp_forward` `tools_derived` arm |

The symbolic tools need `wolframscript` with FeynCalc; set it with `tb config set heptapod wolframscript_path /path/to/wolframscript`. The `llp` tools are pure Python. No loadout serves literature, particle-data, or web tools, since the tasks are graded against a committed reference.

## Campaign records

[`campaigns/`](campaigns/) holds the data behind the paper: the ledger of every cell, the as-run configuration, the collected results, and the scripts that build the figures and tables.

| Directory | Contents |
|---|---|
| `campaigns/llp_forward/` | four systems, two loadouts, five trials each |
| `campaigns/symbolic/` | eight tasks, ten trials per task and configuration |
| `campaigns/publication/` | `make_figures.py`, `make_tables.py`, and their outputs |

The per-trial transcripts and artifacts are attached to each [release](https://github.com/tonymenzo/hepbench/releases) as `hepbench-trials-<campaign>.tar.gz`. Extract one into its campaign directory and open it in the dashboard:

```bash
tar xzf hepbench-trials-symbolic.tar.gz -C campaigns/symbolic
toolbench dashboard campaigns/symbolic/trials
```

The dashboard shows each run's trial matrix, per-stage grades, and transcripts.

## Layout

```
benchmarks/<name>/
├── benchmark.yaml        task, rubric, artifact policy, defaults
├── harnesses/            claude-code, codex, orchestral
├── loadouts/             tool surfaces served per arm
├── variants/             prompt and scaffolding variants
└── soln/ | ground_truth/ committed, rerunnable reference
.toolbase/loadouts/       served-toolkit loadouts
campaigns/                campaign records and publication scripts
scripts/                  oracle-access audit, tool-use and code-volume analysis
tests/                    rubric self-grading, convention audits, check functions
```

Ground truth lives outside the agent's sandbox, the harness denies reading it, and a transcript auditor scans finished runs for answer-key access:

```bash
python scripts/audit_oracle_access.py runs/<run_id> --zero
```

## Citation

If you use HEPBench in your research, please cite the accompanying paper (arXiv number to follow). BibTeX is in [CITATION.bib](CITATION.bib).

## License

HEPBench is licensed under [GPL-3.0](LICENSE.txt).

## Contact

**Maintainer:** Tony Menzo — [menzo.ynot@gmail.com](mailto:menzo.ynot@gmail.com).

**Issues and support:** [https://github.com/tonymenzo/hepbench/issues](https://github.com/tonymenzo/hepbench/issues).
