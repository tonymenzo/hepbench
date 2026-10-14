Estimate the projected signal yield $N_{\rm sig}^{(i)}(m_\phi,g)$ over the $(m_\phi,g)$ plane for a real scalar $\phi$ coupled only to muons in the supplied forward-detector configuration. Treat the dimuon and diphoton searches separately, with $i\in\{\mu\mu,\gamma\gamma\}$. The model is defined by

$$
\mathcal{L} \supset -\frac{1}{2}m_\phi^2\phi^2-g\phi\bar{\mu}\mu.
$$

Use these yields to determine the projected exclusion region for each search, defined by $N_{\rm sig}^{(i)}(m_\phi,g)\geq3$.

The complete experimental setup is defined jointly by this prompt, `reference.tex`, and `geometry/geometry.yaml`. Read both files before beginning and use their definitions exactly. The Pythia cards in `pythia_cards/`, the production factors in `production/kappa.csv`, and the rest-frame energy spectra in `spectra/` provide the remaining inputs.

Compute the yields from your own simulation. Do not look them up.

Produce the following outputs:

- In `results/answer.json`, following `results/answer_schema.json`, report the dimuon-width formula and the requested width and lifetime probe values.
- Write the yield scan to `results/scan.csv` as a flat table with columns `search, m_phi, g, nsig` and one row for each sampled coupling.
- Render the projected exclusion region to `results/reach.pdf` with $m_\phi$ on the horizontal axis and $g$ on the vertical axis. For each search channel, shade the region where $N_{\rm sig}^{(i)}\geq3$.
- Provide `report.tex` summarizing the analysis and conclusions.
