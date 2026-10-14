# `campaigns/` — the records behind the paper

Each campaign directory holds the ledger of every cell, the configuration as run, the collected results, and the per-run graded ledgers. The per-trial evidence, transcripts, preserved artifacts, and grades, is attached to each [release](https://github.com/tonymenzo/hepbench/releases) as `hepbench-trials-<campaign>.tar.gz`.

| Directory | Campaign | Trials |
|---|---|---|
| [`llp_forward/`](llp_forward/) | `bare × core_only` against `bare × tools_defined`, four systems | 40 |
| [`symbolic/`](symbolic/) | `unguided × core_only` against `unguided × tools_eda` on Haiku 4.5, with a GPT-5.5 core baseline | 280 |
| [`publication/`](publication/) | the scripts that build the paper's figures and tables from the two records above | |

## Viewing the trials

Download the asset for a campaign, extract it into the campaign directory, and open it with the toolbench dashboard:

```bash
tar xzf hepbench-trials-symbolic.tar.gz -C campaigns/symbolic
toolbench dashboard campaigns/symbolic/trials
```

The dashboard lists every run in the campaign, with each run's trial matrix, per-stage grades, and transcripts.

## Rebuilding the figures and tables

```bash
python campaigns/publication/make_figures.py
python campaigns/publication/make_tables.py
```

Both read the committed records only; nothing is rerun or regraded. The symbolic figures read the per-run `trials.jsonl` ledgers, which are committed; the LLP figures read `llp_forward/graded_record.tar.gz`.
