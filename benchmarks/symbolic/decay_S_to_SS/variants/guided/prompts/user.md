Compute the exact tree-level partial decay widths of a generic real scalar $\phi$ with mass $m_S$ into scalar pairs, for two independent interaction structures. The trilinear couplings $\mu$ carry mass dimension one and are real. Work in natural units; report widths in GeV.

**Part (a) — identical final-state scalars.** The interaction is
$$\mathcal{L}_a = -\, \frac{\mu}{2}\, \phi\, \chi^2 ,$$
where $\chi$ is a real scalar of mass $m_\chi$. Compute $\Gamma(\phi \to \chi\chi)$ for $\mu = 480\ \mathrm{GeV}$, $m_S = 950\ \mathrm{GeV}$, $m_\chi = 270\ \mathrm{GeV}$.

**Part (b) — distinct final-state scalars.** The interaction is
$$\mathcal{L}_b = -\, \mu\, \phi\, \chi_1 \chi_2 ,$$
where $\chi_1$, $\chi_2$ are distinct real scalars with masses $m_1$, $m_2$. Compute $\Gamma(\phi \to \chi_1\chi_2)$ for $\mu = 315\ \mathrm{GeV}$, $m_S = 950\ \mathrm{GeV}$, $m_1 = 350\ \mathrm{GeV}$, $m_2 = 410\ \mathrm{GeV}$.

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

- part (a): `mu`, `mS`, `mchi`
- part (b): `mu`, `mS`, `m1`, `m2`

Give exact tree-level results including all mass, threshold, and statistics effects, not order-of-magnitude estimates.
