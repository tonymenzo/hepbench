Compute the exact tree-level partial decay widths of a scalar $\phi$ with mass $m_S$ into a lighter scalar $\phi'$ (mass $m_{S'}$) plus a massive neutral vector $V$ (mass $m_V$), via the derivative coupling
$$\mathcal{L} = g\, V^\mu\left(\phi\,\partial_\mu \phi' - \phi'\,\partial_\mu \phi\right),$$
with $g$ dimensionless and real. Sum over the vector's three polarizations. Work in natural units; report widths in GeV.

**Part (a) — massive scalar daughter.** Compute $\Gamma(\phi \to \phi'\,V)$ for $g = 0.90$, $m_S = 600\ \mathrm{GeV}$, $m_{S'} = 140\ \mathrm{GeV}$, $m_V = 250\ \mathrm{GeV}$.

**Part (b) — massless scalar daughter** ($m_{S'} = 0$). Compute $\Gamma(\phi \to \phi'\,V)$ for $g = 0.70$, $m_S = 600\ \mathrm{GeV}$, $m_V = 250\ \mathrm{GeV}$.

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

The `*_width_gev` fields are the numeric partial widths in GeV at the parameter values above. The `*_width_formula` fields are the closed-form widths as single-line Python/SymPy strings using `**`, explicit `*`, `sqrt` and `pi` only. Use exactly these symbol names ($m_{S'}$ is written `mSp`):

- part (a): `g`, `mS`, `mSp`, `mV`
- part (b): `g`, `mS`, `mV`

Give exact tree-level results, not order-of-magnitude estimates.
