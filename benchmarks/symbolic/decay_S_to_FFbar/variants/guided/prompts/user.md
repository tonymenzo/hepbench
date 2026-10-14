Compute the exact tree-level partial decay widths of a generic real scalar $\phi$ with mass $m_S$ into fermion pairs, for three independent interaction structures. All couplings are real. Work in natural units ($\hbar = c = 1$); report widths in GeV.

**Part (a) — scalar Yukawa coupling.** The interaction is
$$\mathcal{L}_a = -\, y\, \phi\, \bar{\psi}\psi ,$$
where $\psi$ is a Dirac fermion of mass $m_f$. Compute $\Gamma(\phi \to \psi\bar{\psi})$ for $y = 0.87$, $m_S = 1240\ \mathrm{GeV}$, $m_f = 320\ \mathrm{GeV}$.

**Part (b) — pseudoscalar coupling.** The interaction is
$$\mathcal{L}_b = -\, i\, y\, \phi\, \bar{\psi}\gamma_5\psi ,$$
with the same field content. Compute $\Gamma(\phi \to \psi\bar{\psi})$ for $y = 0.54$, $m_S = 1240\ \mathrm{GeV}$, $m_f = 320\ \mathrm{GeV}$.

**Part (c) — chiral coupling to two distinct fermions.** The interaction is
$$\mathcal{L}_c = -\, \phi\, \bar{\psi}_1 \left( y_L P_L + y_R P_R \right) \psi_2 + \mathrm{h.c.},$$
where $P_{L,R} = (1 \mp \gamma_5)/2$ and $\psi_1$, $\psi_2$ are distinct Dirac fermions with masses $m_1$, $m_2$. Compute the partial width for the single channel $\Gamma(\phi \to \psi_1 \bar{\psi}_2)$ — do not include the conjugate channel — for $y_L = 0.31$, $y_R = 0.78$, $m_S = 1240\ \mathrm{GeV}$, $m_1 = 410\ \mathrm{GeV}$, $m_2 = 95\ \mathrm{GeV}$.

## Required output

Write a single file `results/answer.json` containing exactly:

```json
{
  "part_a_width_gev": <number>,
  "part_a_width_formula": "<string>",
  "part_b_width_gev": <number>,
  "part_b_width_formula": "<string>",
  "part_c_width_gev": <number>,
  "part_c_width_formula": "<string>"
}
```

The `*_width_gev` fields are the numeric partial widths in GeV at the parameter values above.

The `*_width_formula` fields are the closed-form symbolic widths as single-line strings parseable by Python/SymPy, using `**` for powers, explicit `*` for products, and only the functions `sqrt` and the constant `pi`. Use exactly these symbol names:

- parts (a) and (b): `y`, `mS`, `mf`
- part (c): `yL`, `yR`, `mS`, `m1`, `m2`

Example of the expected formula style (this is the massless-limit width for part (a), NOT a correct final answer): `"y**2 * mS / (8*pi)"`.

Give exact tree-level results including all mass and threshold dependence, not order-of-magnitude estimates.
