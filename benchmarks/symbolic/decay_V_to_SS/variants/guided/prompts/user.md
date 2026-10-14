Compute the exact tree-level partial decay widths of a massive neutral vector $V^\mu$ with mass $m_V$ into two scalars, via the derivative coupling
$$\mathcal{L} = g\, V^\mu\left(S_1\,\partial_\mu S_2 - S_2\,\partial_\mu S_1\right),$$
with $g$ dimensionless and real. Average over the three initial polarizations. Work in natural units; report widths in GeV.

**Part (a) — distinct massive scalars** of masses $m_1$, $m_2$. Compute $\Gamma(V \to S_1 S_2)$ for $g = 0.85$, $m_V = 500\ \mathrm{GeV}$, $m_1 = 120\ \mathrm{GeV}$, $m_2 = 210\ \mathrm{GeV}$.

**Part (b) — one massless scalar** ($m_2 = 0$, the other scalar of mass $m_1$). Compute $\Gamma(V \to S_1 S_2)$ for $g = 0.62$, $m_V = 500\ \mathrm{GeV}$, $m_1 = 180\ \mathrm{GeV}$.

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

- part (a): `g`, `mV`, `m1`, `m2`
- part (b): `g`, `mV`, `m1`

Give exact tree-level results, not order-of-magnitude estimates.
