# `campaigns/` — the records behind the paper

From the repository root, open all included campaigns in the toolbench dashboard:

```bash
toolbench dashboard campaigns --port 0
```

The `--port 0` option automatically selects an available port and prints the dashboard URL in the terminal. Open that URL in your browser, select a run, then select a trial to inspect its grades. If toolbench is not installed, follow the [Quickstart](../README.md#quickstart). Viewing the campaigns does not require an agent login or HEPTAPOD.

## Included campaigns

Each campaign directory holds the ledger of every run: the resolved configuration, one graded row per trial, and the summaries. The numbers in the paper come from these records, and the benchmarks they ran are the ones in [`benchmarks/`](../benchmarks/) as committed. The per-trial evidence, transcripts, preserved artifacts, and grades, is attached to each [release](https://github.com/tonymenzo/hepbench/releases) as `hepbench-trials-<campaign>.tar.gz`.

| Directory | Campaign | Trials |
|---|---|---|
| [`llp_forward/`](llp_forward/) | `bare × core_only` against `bare × tools_defined`, four systems | 40 |
| [`symbolic/`](symbolic/) | `unguided × core_only` against `unguided × tools_eda` on Haiku 4.5, with a GPT-5.5 core baseline | 280 |

## Add transcripts and artifacts

The checkout includes the score records. Download the release asset for a campaign to add its transcripts and preserved trial files. From the repository root, extract the archive into the campaign directory, replacing the path with your downloaded file:

```bash
tar xzf /path/to/hepbench-trials-symbolic.tar.gz -C campaigns/symbolic
toolbench dashboard campaigns/symbolic/trials --port 0
```

For forward-LLP extraction instructions, see the [`llp_forward` campaign README](llp_forward/README.md). Each campaign README gives its dashboard command and describes the recorded evidence. The [symbolic regrading notes](symbolic/README.md#regrading) explain why its trial grades differ from the saved summaries.
