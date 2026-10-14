Compute the tree-level widths for a massive neutral vector $V^\mu$ (mass $m_V$) decaying into a Dirac fermion pair $\psi\bar{\psi}$ (mass $m_f$), averaging over the three initial polarizations. Two couplings, both real.

(a) $\mathcal{L} = g\,V_\mu\,\bar{\psi}\gamma^\mu\psi$. Compute $\Gamma(V \to \psi\bar{\psi})$ at $g = 0.47$, $m_V = 2150$, $m_f = 640$ GeV.

(b) $\mathcal{L} = V_\mu\,\bar{\psi}\gamma^\mu(g_V - g_A\gamma_5)\psi$. Compute $\Gamma(V \to \psi\bar{\psi})$ at $g_V = 0.52$, $g_A = 0.36$, $m_V = 2150$, $m_f = 640$ GeV.

`results/answer.json`: widths in GeV under `part_a_width_gev`, `part_b_width_gev`; closed forms as sympy-parseable strings under `part_a_width_formula`, `part_b_width_formula`. Symbols `g,mV,mf` for (a), `gV,gA,mV,mf` for (b).

Record the derivation in `results/derivation.md`: the conventions adopted (metric signature, spinor and polarization normalizations, spin/polarization averaging, identical-particle symmetry factors), the vertex factors read off the Lagrangian, the amplitude and its spin/polarization sum, the phase-space factor, and the intermediate expressions at each step, in enough detail for the result to be checked line by line. State any limits or consistency checks performed and their outcome.
