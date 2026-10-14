[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0) [![Python](https://img.shields.io/badge/Python-3.12%20|%203.13-blue.svg)](https://www.python.org/downloads/) [![Runs on](https://img.shields.io/badge/Runs%20on-toolbench-orange.svg)](https://github.com/tonymenzo/toolbench)

# **HEPBench**

**HEPBench** is a collection of **high-energy physics benchmarks for LLM agents**.

Benchmarks run through [toolbench](https://github.com/tonymenzo/toolbench), which launches agents, grades their outputs, and provides a dashboard for inspecting results. Domain tools come from [HEPTAPOD](https://github.com/tonymenzo/heptapod), served over the [Model Context Protocol (MCP)](https://modelcontextprotocol.io) by [toolbase](https://github.com/alexr314/toolbase).

- [Run a benchmark](#run-a-benchmark) to evaluate an agent on an included task.
- [Inspect the campaigns](#inspect-the-campaigns) to browse the recorded runs, grades, and trial evidence.

## Quickstart

You'll need **Python 3.12 or 3.13**. Clone the repository and install HEPBench with its runner and grading dependencies:

```bash
git clone https://github.com/tonymenzo/hepbench.git
cd hepbench
python -m pip install .
```

Run the commands below from this directory.

## Run a benchmark

For the example below, install Claude Code and log in before running it. The Claude Code and Codex harnesses use the agent's subscription access, so they do not require a separate API key.

Run three trials of the scalar-decay task with a live dashboard:

```bash
toolbench run --benchmark benchmarks/symbolic/decay_S_to_SS \
    --harnesses claude-code/default --model claude-haiku-4-5 \
    --variants unguided --loadouts core_only --n 3 --max-cost-usd 5 \
    --dashboard --dashboard-port 0
```

The `core_only` loadout uses the agent's built-in tools. The dashboard selects an available port and prints its URL in the terminal. Open that URL in your browser to follow the trials. The dashboard stops when the run ends; results are saved under `runs/<run_id>/`.

To inspect the latest run afterward, launch the dashboard again:

```bash
toolbench dashboard --port 0
```

The `--port 0` option automatically selects an available port and prints the dashboard URL in the terminal. Open that URL in your browser. Pass `runs/<run_id>` to open a specific run, or `runs` to browse all local runs. The run directory contains `trials.jsonl` with one graded record per trial, `manifest.json` with the resolved configuration, `summary.txt` with aggregate scores, and `trials/` with the trial evidence.

### Choose a task and configuration

Available benchmarks cover symbolic decay widths and cross sections, and forward long-lived-particle searches. See the [benchmark catalog](benchmarks/README.md) for task paths and links to their prompts, tool requirements, deliverables, and grading.

The main run options are:

| Flag | Purpose | Example or default |
|---|---|---|
| `--benchmark` | Task directory containing `benchmark.yaml` (required) | `benchmarks/symbolic/decay_S_to_SS` |
| `--harnesses` | Agent runtime and configuration | `claude-code/default` or `codex/default` |
| `--model` | Model used by the runtime | `claude-haiku-4-5` |
| `--variants` | Prompt and initial files | `unguided` for symbolic tasks; `bare` for the LLP campaign |
| `--loadouts` | Tools available to the agent | `core_only` or a benchmark's `tools_*` loadout |
| `--n` | Trials per configuration | Default: `3` |
| `--parallel` | Maximum number of trials running concurrently across the run | Default: `1`; use `3` to run up to three at once |
| `--max-cost-usd` | Run budget cap (required) | `5` |
| `--dashboard` | Serve a live dashboard and print its URL; stops when the run ends | Include to enable |
| `--dashboard-port` | Port for the live dashboard | Use `0` to select an available port |
| `--campaign` | Group new runs under `runs/campaigns/<name>/` | `symbolic-comparison` |

`--n` sets trials per configuration; `--parallel` limits concurrent trials. In-flight trials may finish after the budget cap is reached. See `toolbench run --help` for all options.

Comma-separated values compare configurations. After [configuring HEPTAPOD](#configure-domain-tools), this example runs six trials across two loadouts, up to three at once:

```bash
toolbench run --benchmark benchmarks/symbolic/decay_S_to_SS \
    --harnesses claude-code/default --model claude-haiku-4-5 \
    --variants unguided --loadouts core_only,tools_eda --n 3 --parallel 3 \
    --max-cost-usd 10 --dashboard --dashboard-port 0
```

## Inspect the campaigns

The [`campaigns/`](campaigns/README.md) directory contains the trial runs from the two campaigns described in [HEPTABench](https://arxiv.org/abs/2610.18454). You can inspect these records without running new trials.

| Campaign | Comparison | Trials |
|---|---|:---:|
| [`llp_forward`](campaigns/llp_forward/README.md) | Built-in tools and HEPTAPOD on four agent systems, five trials per configuration | 40 |
| [`symbolic`](campaigns/symbolic/README.md) | Built-in tools and HEPTAPOD on Claude Haiku 4.5, with a GPT-5.5 baseline, ten trials per task and configuration | 280 |

Open either campaign on its own:

```bash
toolbench dashboard campaigns/symbolic/trials --port 0
```

or:

```bash
toolbench dashboard campaigns/llp_forward/trials --port 0
```

Open the URL printed in the terminal, select a run, then a trial in its matrix to inspect the recorded result and per-stage grades. Each command selects an available port automatically. Use `toolbench dashboard campaigns --port 0` to browse both campaigns together. Stop a dashboard with `Ctrl+C` in the terminal when finished.

### Add transcripts and artifacts

The full trial evidence is distributed separately as `hepbench-trials-<campaign>.tar.gz` assets on the [Releases page](https://github.com/tonymenzo/hepbench/releases). Download the archive for the campaign you want to inspect, then extract it into that campaign's directory. Replace the example path with your downloaded file:

```bash
tar xzf /path/to/hepbench-trials-symbolic.tar.gz -C campaigns/symbolic
toolbench dashboard campaigns/symbolic/trials --port 0
```

For the forward-LLP campaign:

```bash
tar xzf /path/to/hepbench-trials-llp_forward.tar.gz -C campaigns/llp_forward
toolbench dashboard campaigns/llp_forward/trials --port 0
```

## Configure domain tools

The `tools_*` loadouts use **HEPTAPOD 3.0.0**. Download `heptapod-3.0.0.tar.gz` from the [HEPTAPOD releases](https://github.com/tonymenzo/heptapod/releases), then install and select it:

```bash
tb install "/path/to/heptapod-3.0.0.tar.gz"
tb use heptapod@3.0.0
```

The benchmark loadouts select the tools automatically using the definitions in [`.toolbase/loadouts/`](.toolbase/loadouts/).

| Benchmark loadout | Tools | Configuration required |
|---|---|---|
| `symbolic`: `tools_eda` | `ComputeDecayRate`, `ComputeCrossSection` | WolframScript and FeynCalc |
| `llp_forward`: `tools_defined` | The `llp` bundle and `PythiaFromRunCard` | No additional paths |
| `llp_forward`: `tools_derived` | The above plus the `eda` bundle | WolframScript and FeynCalc |

For symbolic calculations, install FeynCalc and set the path to your WolframScript executable:

```bash
tb config set heptapod wolframscript_path /path/to/wolframscript
```

For `llp_forward` with `core_only`, Pythia must be available in the agent's own environment. The supplied [Conda environment](environment.yml) includes the runner and the Pythia version used by the reference:

```bash
conda env create -f environment.yml
conda activate hepbench
```

Run the benchmark from that environment. A forward-LLP trial can take ~tens of minutes.

## Citation

If you use HEPBench in your research, please cite:

- **HEPTABench:** [https://arxiv.org/abs/2610.18454](https://arxiv.org/abs/2610.18454).
- For the domain tools, also cite **HEPTAPOD:** [https://arxiv.org/abs/2512.15867](https://arxiv.org/abs/2512.15867), [https://arxiv.org/abs/2603.26990](https://arxiv.org/abs/2603.26990).

BibTeX entries are available in [CITATION.bib](CITATION.bib).

## License

HEPBench is licensed under [GPL-3.0](LICENSE.txt).

## Contact

**Maintainer:** Tony Menzo — [menzo.ynot@gmail.com](mailto:menzo.ynot@gmail.com).

**Issues and support:** [https://github.com/tonymenzo/hepbench/issues](https://github.com/tonymenzo/hepbench/issues).
