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

The decay widths are supplied below.

**Supplied decay widths**

- The tree-level dimuon width is open for $m_\phi>2m_\mu$:
  $$
  \Gamma(\phi\to\mu^+\mu^-)
  =\frac{g^2m_\phi}{8\pi}
  \left(1-\frac{4m_\mu^2}{m_\phi^2}\right)^{3/2}.
  $$
- The one-loop diphoton width from the muon triangle is the only visible channel below the dimuon threshold:
  $$
  \Gamma(\phi\to\gamma\gamma)
  =\frac{\alpha^2g^2m_\phi^3}{256\pi^3m_\mu^2}
  \left|A_{1/2}\right|^2,
  $$
  with
  $$
  A_{1/2}=\frac{2[\tau+(\tau-1)f]}{\tau^2},
  \qquad
  \tau=\frac{m_\phi^2}{4m_\mu^2},
  \qquad
  f=\arcsin^2\!\sqrt{\tau}\quad\text{for }\tau\leq1.
  $$
- The total width, visible branching fractions, and proper lifetime are
  $$
  \Gamma_{\rm tot}=\Gamma(\phi\to\mu^+\mu^-)+\Gamma(\phi\to\gamma\gamma),
  \qquad
  {\rm BR}_i=\frac{\Gamma_i}{\Gamma_{\rm tot}},
  \qquad
  c\tau=\frac{\hbar c}{\Gamma_{\rm tot}},
  $$
  with $\hbar c=1.973269804\times10^{-16}~\mathrm{GeV\,m}$. All widths scale as $g^2$, so the lifetime at any coupling follows from its value at $g=1$, $c\tau(g)=c\tau(1)/g^2$.
