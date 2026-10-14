Compute the tree-level three-body partial decay widths of a heavy Dirac fermion $\Psi$ with mass $m_F$ into three distinct massless Dirac fermions $\psi_a$, $\psi_b$, $\bar{\psi}_c$, mediated by a heavy boson of mass $M \gg m_F$. Work at LEADING order in $m_F / M$ (contact limit). Average over the initial spin. All couplings are real. Work in natural units; report widths in GeV.

**Part (a) — heavy vector mediator with left-handed couplings.** The interactions are
$$\mathcal{L}_a = g\, V_\mu\, \bar{\psi}_a \gamma^\mu P_L \Psi \;+\; g\, V_\mu\, \bar{\psi}_b \gamma^\mu P_L \psi_c \;+\; \mathrm{h.c.},$$
where $P_L = (1 - \gamma_5)/2$ and the vector $V$ has mass $M_V$. Compute $\Gamma(\Psi \to \psi_a \psi_b \bar{\psi}_c)$ at leading order in $m_F/M_V$ for $g = 0.62$, $m_F = 17.3\ \mathrm{GeV}$, $M_V = 1450\ \mathrm{GeV}$.

**Part (b) — heavy scalar mediator with Yukawa couplings.** The interactions are
$$\mathcal{L}_b = -\, y_1\, \phi\, \bar{\psi}_a \Psi \;-\; y_2\, \phi\, \bar{\psi}_b \psi_c \;+\; \mathrm{h.c.},$$
where the scalar $\phi$ has mass $M_S$. Compute $\Gamma(\Psi \to \psi_a \psi_b \bar{\psi}_c)$ at leading order in $m_F/M_S$ for $y_1 = 0.71$, $y_2 = 0.58$, $m_F = 17.3\ \mathrm{GeV}$, $M_S = 1450\ \mathrm{GeV}$.

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

The `*_width_formula` fields are the closed-form symbolic widths (leading order in $m_F/M$) as single-line strings parseable by Python/SymPy, using `**` for powers, explicit `*` for products, and only the function `sqrt` and the constant `pi`. Use exactly these symbol names:

- part (a): `g`, `mF`, `MV`
- part (b): `y1`, `y2`, `mF`, `MS`

Be careful to match the coupling normalization exactly as written in the Lagrangians above; do not assume a Fermi-theory normalization.
