Compute the exact tree-level total annihilation cross sections $\sigma(\psi_1\bar{\psi}_1 \to \psi_2\bar{\psi}_2)$ for two distinct MASSLESS Dirac fermion species $\psi_1$, $\psi_2$ that couple only through an s-channel mediator (there is no t-channel diagram). Average over the four initial spin states. All couplings are real. Work in natural units, then convert the numeric answers to picobarns.

**Part (a) — massless vector mediator.** The interaction is
$$\mathcal{L}_a = g\, V_\mu \left( \bar{\psi}_1\gamma^\mu\psi_1 + \bar{\psi}_2\gamma^\mu\psi_2 \right),$$
where $V$ is a massless vector boson. Compute the total cross section at $\sqrt{s} = 730\ \mathrm{GeV}$ for $g = 0.55$.

**Part (b) — heavy scalar mediator, below resonance.** The interaction is
$$\mathcal{L}_b = -\, y_1\, \phi\, \bar{\psi}_1\psi_1 \;-\; y_2\, \phi\, \bar{\psi}_2\psi_2 ,$$
where $\phi$ is a real scalar of mass $M_S = 1900\ \mathrm{GeV}$ whose width is negligible. Compute the total cross section at $\sqrt{s} = 730\ \mathrm{GeV}$ for $y_1 = 0.92$, $y_2 = 0.34$.

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

- part (a): `g`, `s`
- part (b): `y1`, `y2`, `s`, `MS`

Give exact tree-level results, not order-of-magnitude estimates.
