Compute the exact tree-level partial decay widths of a heavy Dirac fermion $\Psi$ with mass $m_F$ into a lighter Dirac fermion $\psi$ (mass $m_f$) plus a real scalar $\phi$ (mass $m_S$), for two independent interaction structures. All couplings are real. Average over the initial spin. Work in natural units; report widths in GeV.

**Part (a) — scalar Yukawa coupling.** The interaction is
$$\mathcal{L}_a = -\, y\, \phi\, \bar{\psi}\Psi + \mathrm{h.c.}$$
Compute $\Gamma(\Psi \to \psi\,\phi)$ for $y = 0.66$, $m_F = 880\ \mathrm{GeV}$, $m_f = 130\ \mathrm{GeV}$, $m_S = 340\ \mathrm{GeV}$.

**Part (b) — chiral coupling.** The interaction is
$$\mathcal{L}_b = -\, \phi\, \bar{\psi} \left( y_L P_L + y_R P_R \right) \Psi + \mathrm{h.c.},$$
where $P_{L,R} = (1 \mp \gamma_5)/2$. Compute $\Gamma(\Psi \to \psi\,\phi)$ for $y_L = 0.45$, $y_R = 0.18$, $m_F = 880\ \mathrm{GeV}$, $m_f = 130\ \mathrm{GeV}$, $m_S = 340\ \mathrm{GeV}$.

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

- part (a): `y`, `mF`, `mf`, `mS`
- part (b): `yL`, `yR`, `mF`, `mf`, `mS`

Give exact tree-level results including all mass and threshold dependence (pay attention to the sign of any mass interference term), not order-of-magnitude estimates.
