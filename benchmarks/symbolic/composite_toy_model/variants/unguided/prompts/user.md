Compute the full tree-level profile of one toy model. Heavy real scalar $\Phi$ (mass $m_\Phi = 1850$ GeV) with
$$\mathcal{L}_{\mathrm{int}} = -\,y_1\,\Phi\,\bar{\psi}_1\psi_1 - y_2\,\Phi\,\bar{\psi}_2\psi_2 - \frac{\mu}{2}\,\Phi\,\chi^2 ,$$
Dirac fermions $\psi_1$ (mass $m_1 = 230$ GeV) and $\psi_2$ (massless), real scalar $\chi$ (mass $m_\chi = 410$ GeV), $y_1 = 0.42$, $y_2 = 0.16$, $\mu = 590$ GeV, all real. Those are the only interactions.

Compute: the three partial widths $\Gamma(\Phi\to\psi_1\bar{\psi}_1)$, $\Gamma(\Phi\to\psi_2\bar{\psi}_2)$, $\Gamma(\Phi\to\chi\chi)$ in GeV; the total width and the three branching ratios; the lifetime in seconds; and $\sigma(\psi_2\bar{\psi}_2 \to \psi_1\bar{\psi}_1)$ via s-channel $\Phi$ exchange at $\sqrt{s} = 1100$ GeV (spin-averaged, below resonance, no other diagrams) in pb.

`results/answer.json`, plain JSON numbers in the units above, keys `width_psi1_gev`, `width_psi2_gev`, `width_chichi_gev`, `width_total_gev`, `br_psi1`, `br_psi2`, `br_chichi`, `lifetime_s`, `xsec_pb`.

Record the derivation in `results/derivation.md`: the conventions adopted (metric signature, spinor and polarization normalizations, spin/polarization averaging, identical-particle symmetry factors), the vertex factors read off the Lagrangian, the amplitude and its spin/polarization sum, the phase-space factor, and the intermediate expressions at each step, in enough detail for the result to be checked line by line. State any limits or consistency checks performed and their outcome.
