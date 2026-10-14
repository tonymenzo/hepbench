Consider the following toy extension of a free theory. A heavy real scalar $\Phi$ with mass $m_\Phi = 1850\ \mathrm{GeV}$ couples to two Dirac fermion species $\psi_1$ (mass $m_1 = 230\ \mathrm{GeV}$), $\psi_2$ (massless), and a light real scalar $\chi$ (mass $m_\chi = 410\ \mathrm{GeV}$):

$$\mathcal{L}_{\mathrm{int}} = -\, y_1\, \Phi\, \bar{\psi}_1\psi_1 \;-\; y_2\, \Phi\, \bar{\psi}_2\psi_2 \;-\; \frac{\mu}{2}\, \Phi\, \chi^2 ,$$

with $y_1 = 0.42$, $y_2 = 0.16$, and $\mu = 590\ \mathrm{GeV}$ (all real). These are the only interactions. Work at tree level, in natural units unless stated otherwise.

Compute the complete decay and annihilation profile of $\Phi$:

1. The partial widths $\Gamma(\Phi \to \psi_1\bar{\psi}_1)$, $\Gamma(\Phi \to \psi_2\bar{\psi}_2)$, and $\Gamma(\Phi \to \chi\chi)$, in GeV.
2. The total width $\Gamma_\Phi$ in GeV and all three branching ratios.
3. The lifetime $\tau_\Phi$ in SECONDS.
4. The total annihilation cross section $\sigma(\psi_2\bar{\psi}_2 \to \psi_1\bar{\psi}_1)$ via s-channel $\Phi$ exchange at $\sqrt{s} = 1100\ \mathrm{GeV}$, averaged over initial spins, in PICOBARNS. (The $\Phi$ width is negligible this far below the resonance; there are no other diagrams.)

## Required output

Write a single file `results/answer.json` containing exactly:

```json
{
  "width_psi1_gev": <number>,
  "width_psi2_gev": <number>,
  "width_chichi_gev": <number>,
  "width_total_gev": <number>,
  "br_psi1": <number>,
  "br_psi2": <number>,
  "br_chichi": <number>,
  "lifetime_s": <number>,
  "xsec_pb": <number>
}
```

All values are plain JSON numbers in the units stated above. Give exact tree-level results including all mass, threshold, and statistics effects; check that your branching ratios sum to one and that your lifetime is consistent with your total width before writing the file.
