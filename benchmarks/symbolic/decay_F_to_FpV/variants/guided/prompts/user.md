Compute the exact tree-level partial decay widths of a heavy Dirac fermion $\Psi$ with mass $m_F$ into a lighter Dirac fermion $\psi$ (mass $m_f$) plus a massive neutral vector $V$ (mass $m_V$), for two interaction structures. All couplings are real. Average over the initial spin and sum over the vector's three polarizations. Work in natural units; report widths in GeV.

**Part (a) — pure vector coupling.** The interaction is
$$\mathcal{L}_a = g\, \bar{\psi}\gamma^\mu \Psi\, V_\mu + \mathrm{h.c.}$$
Compute $\Gamma(\Psi \to \psi\,V)$ for $g = 0.74$, $m_F = 900\ \mathrm{GeV}$, $m_f = 180\ \mathrm{GeV}$, $m_V = 240\ \mathrm{GeV}$.

**Part (b) — chiral coupling.** The interaction is
$$\mathcal{L}_b = \bar{\psi}\gamma^\mu\left(g_L P_L + g_R P_R\right)\Psi\, V_\mu + \mathrm{h.c.},\qquad P_{L,R}=(1\mp\gamma_5)/2 .$$
Compute $\Gamma(\Psi \to \psi\,V)$ for $g_L = 0.58$, $g_R = 0.29$, $m_F = 900\ \mathrm{GeV}$, $m_f = 180\ \mathrm{GeV}$, $m_V = 240\ \mathrm{GeV}$.

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

The `*_width_gev` fields are the numeric partial widths in GeV at the parameter values above. The `*_width_formula` fields are the closed-form widths as single-line Python/SymPy strings using `**`, explicit `*`, `sqrt` and `pi` only. Use exactly these symbol names:

- part (a): `g`, `mF`, `mf`, `mV`
- part (b): `gL`, `gR`, `mF`, `mf`, `mV`

Give exact tree-level results including the full massive-vector polarization structure, not order-of-magnitude estimates.
