# `soln/` — the `llp_forward` ground truth

The answer key, the derivation behind it, and what rebuilds it. Deny-read for graded agents.

## The graded contract

| File | What it is |
|---|---|
| `truth.json` | The 48 declared `(search, m_phi, g)` points the rubric grades against, the width and lifetime probes, and the per-mass reach bands. |
| `fine_reach_contour.json` | A fine mass scan of the reach contour, for plotting. Not a replicate of `truth.json` at the graded masses. |
| `input.json` | The model card the reference was built from. |
| `reference/manifest.json` | Provenance, and the measured noise floors the rubric uses: 0.00188 dex on yields and 0.00200 on each contour edge, from two independent same-size builds. |
| `reference/out/truth_a.json`, `truth_b.json` | The two 2M-event builds. |

## The solution, written down

- `leptonic_ground_truth.tex`: the derivation, with its figures in `figs/`.
- `notes/`: the accuracy metric, the detector model and every approximation in it, and the strata-convergence study.
- `verify_tools_reproduce_truth.py`: checks that the served toolkit reproduces `truth.json`.

## Rebuilding it

`code/` holds the generators, `reference/build_reference.py` and `build_fine_contour.py` the reference itself, and `reference/compare_truth.py` and `check_strata_convergence.py` the checks. The 329 MB parent-flux samples are not tracked; `manifest.json` records their generator, seeds, and hashes.

## One trap

Do not measure the noise floor against `fine_reach_contour.json`. It samples different masses from the graded points, and the reach edge moves steeply with mass, so the comparison returns a floor roughly eighteen times too large. The floor comes from `reference/manifest.json`.
