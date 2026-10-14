# `publication/` — figures and tables

The scripts that build the paper's figures and tables from the two campaign records, and their outputs.

```bash
python campaigns/publication/make_figures.py
python campaigns/publication/make_tables.py
```

Run from the repository root with matplotlib, numpy, and scipy available. Nothing is rerun or regraded. `data.json` records the input hashes, software versions, per-cell scores and pass counts, observable summaries, and the symbolic check counts behind every figure and table.

| Output | Figure |
|---|---|
| `llp_bare_allsystems` | reach by system: scores, and mean against sample standard deviation |
| `llp_bare_yields_vs_truth` | per-system peak-yield ratios to the reference |
| `llp_bare_contour_vs_truth` | per-system sensitivity boundaries against the reference |
| `llp_bare_threshold_sensitivity` | pass rate against the reach threshold |
| `llp_bare_code_capture` | agent-authored code volume by arm |
| `llp_reference_sensitivity` | the reference sensitivity regions |
| `symbolic_overview` | Haiku trial reach per task, both arms |
| `symbolic_passk` | per-task pass@k and pass^k |
| `symbolic_errors` | recorded numerical and formula discrepancies |
| `llp-tables.tex` | the LLP tables, from `table-template.tex` |

Conventions: curves are separated by search channel, observable summaries are conditional on a positive submitted peak or both contour crossings, and missing trials remain in every campaign-level score.
