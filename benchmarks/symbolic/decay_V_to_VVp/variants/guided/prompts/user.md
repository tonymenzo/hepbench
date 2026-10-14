Compute the exact tree-level partial decay widths of a massive neutral vector $V^\mu$ with mass $m_V$ into two distinct massive vectors $V_1$, $V_2$ (masses $m_1$, $m_2$) via the standard Yang-Mills triple-gauge vertex
$$\Gamma^{\mu_1\mu_2\mu_3}(k_1,k_2,k_3) = g\left[\eta^{\mu_1\mu_2}(k_1-k_2)^{\mu_3} + \eta^{\mu_2\mu_3}(k_2-k_3)^{\mu_1} + \eta^{\mu_3\mu_1}(k_3-k_1)^{\mu_2}\right],$$
written with all three momenta flowing **into** the vertex, so that $k_1+k_2+k_3=0$; for $V(P)\to V_1(q_1)V_2(q_2)$ the legs therefore enter as $(k_1,k_2,k_3)=(P,-q_1,-q_2)$, with $\varepsilon(P)$, $\varepsilon^*(q_1)$, $\varepsilon^*(q_2)$ on the three legs and $g$ real and dimensionless. Average over the parent's three polarizations and sum over the daughters'. Work in natural units; report widths in GeV.

**Part (a).** Compute $\Gamma(V \to V_1 V_2)$ for $g = 0.80$, $m_V = 900\ \mathrm{GeV}$, $m_1 = 200\ \mathrm{GeV}$, $m_2 = 250\ \mathrm{GeV}$.

**Part (b).** Compute $\Gamma(V \to V_1 V_2)$ for $g = 0.65$, $m_V = 1200\ \mathrm{GeV}$, $m_1 = 180\ \mathrm{GeV}$, $m_2 = 400\ \mathrm{GeV}$.

## Required output

Write a single file `results/answer.json` containing exactly:

```json
{
  "part_a_width_gev": <number>,
  "part_b_width_gev": <number>
}
```

Both fields are the numeric partial widths in GeV at the parameter values above. This task is graded on the numeric values only (the closed form is intentionally not requested). Give exact tree-level results including the full longitudinal-polarization structure, not order-of-magnitude estimates.
