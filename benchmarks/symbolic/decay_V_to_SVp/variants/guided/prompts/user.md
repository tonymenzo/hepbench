Compute the exact tree-level partial decay widths of a massive neutral vector $V^\mu$ with mass $m_V$ into a scalar $S$ plus a second massive vector $V'$ (mass $m_{V'}$), via the coupling
$$\mathcal{L} = g\, S\, V_\mu V'^\mu ,$$
where $g$ has mass dimension one and is real. Average over the parent's three polarizations and sum over $V'$'s polarizations. Work in natural units; report widths in GeV.

**Part (a) — massive scalar daughter** (mass $m_S$). Compute $\Gamma(V \to S\,V')$ for $g = 180\ \mathrm{GeV}$, $m_V = 700\ \mathrm{GeV}$, $m_S = 160\ \mathrm{GeV}$, $m_{V'} = 250\ \mathrm{GeV}$.

**Part (b) — massless scalar daughter** ($m_S = 0$). Compute $\Gamma(V \to S\,V')$ for $g = 150\ \mathrm{GeV}$, $m_V = 700\ \mathrm{GeV}$, $m_{V'} = 250\ \mathrm{GeV}$.

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

The `*_width_gev` fields are the numeric partial widths in GeV at the parameter values above. The `*_width_formula` fields are the closed-form widths as single-line Python/SymPy strings using `**`, explicit `*`, `sqrt` and `pi` only. Use exactly these symbol names ($m_{V'}$ is written `mVp`):

- part (a): `g`, `mV`, `mS`, `mVp`
- part (b): `g`, `mV`, `mVp`

Give exact tree-level results, not order-of-magnitude estimates.
