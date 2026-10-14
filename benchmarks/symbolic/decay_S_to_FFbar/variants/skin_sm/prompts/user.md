Compute the exact tree-level partial decay widths for the scalar sector of a two-Higgs-doublet-like model, for three states. **Use the hypothetical parameter values given below — do NOT substitute real-world measured masses or couplings.** All couplings are real. Work in natural units; report widths in GeV. In every part $m_S$ denotes the mass of the decaying scalar.

**Part (a) — CP-even scalar.** The neutral CP-even scalar $H$ (mass $m_S$) couples to a Dirac fermion $f$ (mass $m_f$) via
$$\mathcal{L}_a = -\, y\, H\, \bar{f}f .$$
Compute $\Gamma(H \to f\bar{f})$ for $y = 0.87$, $m_S = 1240\ \mathrm{GeV}$, $m_f = 320\ \mathrm{GeV}$.

**Part (b) — CP-odd scalar.** The neutral CP-odd scalar $A$ (mass $m_S$) couples to the same fermion via
$$\mathcal{L}_b = -\, i\, y\, A\, \bar{f}\gamma_5 f .$$
Compute $\Gamma(A \to f\bar{f})$ for $y = 0.54$, $m_S = 1240\ \mathrm{GeV}$, $m_f = 320\ \mathrm{GeV}$.

**Part (c) — charged scalar.** The charged scalar $H^+$ (mass $m_S$) couples to an up-type fermion $u$ (mass $m_1$) and a down-type fermion $d$ (mass $m_2$) via
$$\mathcal{L}_c = -\, H^+\, \bar{u}\left( y_L P_L + y_R P_R \right) d + \mathrm{h.c.},$$
where $P_{L,R} = (1 \mp \gamma_5)/2$. Compute the single channel $\Gamma(H^+ \to u\bar{d})$ — do not include the conjugate channel — for $y_L = 0.31$, $y_R = 0.78$, $m_S = 1240\ \mathrm{GeV}$, $m_1 = 410\ \mathrm{GeV}$, $m_2 = 95\ \mathrm{GeV}$.

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

The `*_width_formula` fields are the closed-form symbolic widths as single-line strings parseable by Python/SymPy, using `**` for powers, explicit `*` for products, and only the function `sqrt` and the constant `pi`. Use exactly these symbol names ($m_S$ is the decaying scalar's mass in each part):

- parts (a) and (b): `y`, `mS`, `mf`
- part (c): `yL`, `yR`, `mS`, `m1`, `m2`

Example of the expected formula style (this is the massless-limit width for part (a), NOT a correct final answer): `"y**2 * mS / (8*pi)"`.

Give exact tree-level results including all mass and threshold dependence, not order-of-magnitude estimates.
