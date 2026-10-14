**Task:** Estimate the projected signal yield $N_{\rm sig}^{(i)}(m_\phi,g)$ over the $(m_\phi,g)$ plane for a real scalar $\phi$ coupled only to muons, in the forward-detector setup defined below. Treat the dimuon and diphoton searches separately, with $i\in\{\mu\mu,\gamma\gamma\}$. Use these yields to determine the projected exclusion region for each search, defined by $N_{\rm sig}^{(i)}(m_\phi,g)\geq3$ with zero background. The model is

$$
\mathcal{L} \supset -\frac{1}{2}m_\phi^2\phi^2-g\phi\bar{\mu}\mu.
$$

Compute the yields from your own simulation. Do not look them up.

**Decay widths:** The tree-level dimuon width is open for $m_\phi>2m_\mu$:

$$
\Gamma(\phi\to\mu^+\mu^-)
=\frac{g^2m_\phi}{8\pi}
\left(1-\frac{4m_\mu^2}{m_\phi^2}\right)^{3/2}.
$$

The one-loop diphoton width from the muon triangle is the only visible channel below the dimuon threshold:

$$
\Gamma(\phi\to\gamma\gamma)
=\frac{\alpha^2g^2m_\phi^3}{256\pi^3m_\mu^2}
\left|A_{1/2}\right|^2,
\qquad
A_{1/2}=\frac{2[\tau+(\tau-1)f]}{\tau^2},
\qquad
\tau=\frac{m_\phi^2}{4m_\mu^2},
\qquad
f=\arcsin^2\!\sqrt{\tau}\quad\text{for }\tau\leq1.
$$

The total width, visible branching fractions, and proper lifetime are

$$
\Gamma_{\rm tot}=\Gamma(\phi\to\mu^+\mu^-)+\Gamma(\phi\to\gamma\gamma),
\qquad
{\rm BR}_i=\frac{\Gamma_i}{\Gamma_{\rm tot}},
\qquad
c\tau=\frac{\hbar c}{\Gamma_{\rm tot}},
$$

with $\hbar c=1.973269804\times10^{-16}~\mathrm{GeV\,m}$. All widths scale as $g^2$, so the lifetime at any coupling follows from its value at $g=1$, $c\tau(g)=c\tau(1)/g^2$.

**Production:** The scalar is radiated from final-state muons in forward hadron decays, through two topologies,

$$
P\to\mu\nu\phi \quad\text{(pseudoscalar parents)},
\qquad
V\to\mu^+\mu^-\phi \quad\text{(vector parents)}.
$$

Which hadrons contribute, and at what rate, is part of the calculation.

**Beam and flux normalization:** $pp$ collisions at $\sqrt{s}=13.6$ TeV. Generate the forward parent flux with Pythia 8, Monash tune, including soft-QCD light-hadron production and charmonium, and harvest the parent hadrons at production rather than letting the generator decay them. Keep parents within $\theta<0.05$ rad of the beam axis. Take the inelastic cross section to be $\sigma_{\rm inel}=80.0$ mb and weight each harvested parent per inelastic collision. The total number of primary interactions is $N_{\rm int}=2.7\times10^{18}$.

**Apparatus:** All distances are measured from the interaction point along the beam axis, and everything is on-axis.

- Parents fly and decay in the open region $0<z<50$ m. Shielding begins at $z=50$ m and absorbs all Standard-Model particles, so a $\phi$ counts only if its parent decayed at $z<50$ m. The $\phi$ itself passes through the shielding freely.
- Decay volume (fiducial): a cylinder spanning $112<z<163$ m of radius $0.92$ m. The $\phi$ must decay inside it.
- Detector: a plane at $z=165$ m of radius $0.92$ m. The decay products must reach it.

**Searches:** For the dimuon search, $\phi\to\mu^+\mu^-$, both muons must reach the detector plane within its radius. For the diphoton search, $\phi\to\gamma\gamma$, both photons must reach it. Treat the decay products as travelling in straight lines from the decay point: no magnetic field, no material, and no scattering. Detection is purely geometric, with no efficiency, resolution, or background.

**Evaluate at** the mass grid [GeV]

$$
0.06,\ 0.12,\ 0.18,\ 0.205,\ 0.23,\ 0.28,\ 0.34,\ 0.42,\ 0.70,\ 1.20,\ 1.90,\ 2.30,
$$

and report the following probe values:

| field | evaluated at | quantity |
|---|---|---|
| `width_probe_gev` | $m_\phi=0.30$, $g=4.2\times10^{-4}$ | $\Gamma(\phi\to\mu^+\mu^-)$ [GeV] |
| `width_gg_probe_gev` | $m_\phi=0.12$, $g=1.0\times10^{-3}$ | $\Gamma(\phi\to\gamma\gamma)$ [GeV] |
| `ctau_probe_m[0]` | $m_\phi=0.30$, $g=3.7\times10^{-6}$ | $c\tau$ [m], from the total width |
| `ctau_probe_m[1]` | $m_\phi=0.30$, $g=1.11\times10^{-5}$ | $c\tau$ [m], from the total width |

**Deliverables:**

- In `results/answer.json`, following `results/answer_schema.json`, report the dimuon-width formula and the probe values above.
- Write the yield scan to `results/scan.csv` as a flat table with columns `search, m_phi, g, nsig` and one row for each sampled coupling.
- Render the projected exclusion region to `results/reach.pdf` with $m_\phi$ on the horizontal axis and $g$ on the vertical axis. For each search channel, shade the region where $N_{\rm sig}^{(i)}\geq3$.
- Provide `report.tex` summarizing the analysis and conclusions.
