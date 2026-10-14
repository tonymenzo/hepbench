Compute the exact tree-level partial decay widths of a real scalar $\phi$ with mass $m_S$ into two massive neutral vectors, for two interaction structures. The couplings $g$ have mass dimension one and are real. Sum over the vectors' polarizations. Work in natural units; report widths in GeV.

**Part (a) — identical vectors.** The interaction is
$$\mathcal{L}_a = g\, \phi\, V_\mu V^\mu ,$$
where $V$ is a massive vector of mass $m_V$. Compute $\Gamma(\phi \to VV)$ for $g = 130\ \mathrm{GeV}$, $m_S = 400\ \mathrm{GeV}$, $m_V = 90\ \mathrm{GeV}$.

**Part (b) — distinct vectors.** The interaction is
$$\mathcal{L}_b = g\, \phi\, V_{1\mu} V_2^\mu ,$$
where $V_1$, $V_2$ are distinct massive vectors of masses $m_1$, $m_2$. Compute $\Gamma(\phi \to V_1 V_2)$ for $g = 110\ \mathrm{GeV}$, $m_S = 400\ \mathrm{GeV}$, $m_1 = 90\ \mathrm{GeV}$, $m_2 = 150\ \mathrm{GeV}$.

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

- part (a): `g`, `mS`, `mV`
- part (b): `g`, `mS`, `m1`, `m2`

Give exact tree-level results including the symmetry factor for identical final states and the full polarization structure, not order-of-magnitude estimates.
