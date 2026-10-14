Compute the exact tree-level total cross sections for 2 to 2 scattering of real scalars via quartic contact interactions, in the center-of-mass frame. All couplings are real and dimensionless. Work in natural units, then convert the numeric answers to picobarns.

**Part (a) — self-scattering of identical scalars.** The interaction is
$$\mathcal{L}_a = -\, \frac{\lambda}{4!}\, \phi^4 ,$$
where $\phi$ is a real scalar of mass $m_\phi$. Compute the total cross section $\sigma(\phi\phi \to \phi\phi)$ for $\lambda = 2.3$, $m_\phi = 75\ \mathrm{GeV}$, at center-of-mass energy $\sqrt{s} = 480\ \mathrm{GeV}$.

**Part (b) — scattering into a distinct scalar pair.** The interaction is
$$\mathcal{L}_b = -\, \frac{\lambda_{12}}{4}\, \phi^2 \chi^2 ,$$
where $\chi$ is a real scalar of mass $m_\chi$. Compute the total cross section $\sigma(\phi\phi \to \chi\chi)$ for $\lambda_{12} = 1.7$, $m_\phi = 75\ \mathrm{GeV}$, $m_\chi = 210\ \mathrm{GeV}$, at $\sqrt{s} = 480\ \mathrm{GeV}$.

## Required output

Write a single file `results/answer.json` containing exactly:

```json
{
  "part_a_xsec_pb": <number>,
  "part_a_xsec_formula": "<string>",
  "part_b_xsec_pb": <number>,
  "part_b_xsec_formula": "<string>"
}
```

The `*_xsec_pb` fields are the numeric total cross sections in PICOBARNS at the parameter values above.

The `*_xsec_formula` fields are the closed-form total cross sections in NATURAL UNITS (GeV^-2, no pb conversion inside the formula) as single-line strings parseable by Python/SymPy, using `**` for powers, explicit `*` for products, and only the function `sqrt` and the constant `pi`. The symbol `s` denotes the squared center-of-mass energy. Use exactly these symbol names:

- part (a): `lam`, `s`, `mphi`
- part (b): `lam`, `s`, `mphi`, `mchi`

(`lam` denotes the quartic coupling of the respective part.) Include only the dependence that actually appears in the exact result.

Give exact tree-level results including all statistics, flux, and threshold factors, not order-of-magnitude estimates.
