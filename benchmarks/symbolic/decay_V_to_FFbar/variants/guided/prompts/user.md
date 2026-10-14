Compute the exact tree-level partial decay widths of a generic massive neutral vector boson $V^\mu$ with mass $m_V$ into a Dirac fermion pair $\psi\bar{\psi}$ (fermion mass $m_f$), for two independent interaction structures. All couplings are real. Average over the three initial polarizations. Work in natural units; report widths in GeV.

**Part (a) — pure vector coupling.** The interaction is
$$\mathcal{L}_a = g\, V_\mu\, \bar{\psi}\gamma^\mu\psi .$$
Compute $\Gamma(V \to \psi\bar{\psi})$ for $g = 0.47$, $m_V = 2150\ \mathrm{GeV}$, $m_f = 640\ \mathrm{GeV}$.

**Part (b) — general vector/axial coupling.** The interaction is
$$\mathcal{L}_b = V_\mu\, \bar{\psi}\gamma^\mu \left( g_V - g_A \gamma_5 \right) \psi .$$
Compute $\Gamma(V \to \psi\bar{\psi})$ for $g_V = 0.52$, $g_A = 0.36$, $m_V = 2150\ \mathrm{GeV}$, $m_f = 640\ \mathrm{GeV}$.

## Required output

Write a single file `results/answer.json` containing exactly:

```json
{
  "part_a_width_gev": <number>,
  "part_a_width_formula": "<string>",
  "part_b_width_gev": <number>,
  "part_b_width_formula": "<string>"
}
```

The `*_width_gev` fields are the numeric partial widths in GeV at the parameter values above.

The `*_width_formula` fields are the closed-form symbolic widths as single-line strings parseable by Python/SymPy, using `**` for powers, explicit `*` for products, and only the function `sqrt` and the constant `pi`. Use exactly these symbol names:

- part (a): `g`, `mV`, `mf`
- part (b): `gV`, `gA`, `mV`, `mf`

Give exact tree-level results including the full fermion-mass dependence, not order-of-magnitude estimates or massless-limit formulas.
