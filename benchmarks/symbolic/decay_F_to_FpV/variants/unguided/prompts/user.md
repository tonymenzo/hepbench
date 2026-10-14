Compute the tree-level widths for a heavy Dirac fermion $\Psi$ (mass $m_F$) decaying to a lighter Dirac fermion $\psi$ (mass $m_f$) plus a massive neutral vector $V$ (mass $m_V$). Average over the initial spin, sum over the vector's three polarizations. Tree-level width for each of two couplings; all real.

(a) Pure vector: $\mathcal{L} = g\, \bar{\psi}\gamma^\mu \Psi\, V_\mu + \mathrm{h.c.}$. Compute $\Gamma(\Psi \to \psi\,V)$ at $g = 0.74$, $m_F = 900$, $m_f = 180$, $m_V = 240$ GeV.

(b) Chiral: $\mathcal{L} = \bar{\psi}\gamma^\mu(g_L P_L + g_R P_R)\Psi\, V_\mu + \mathrm{h.c.}$, $P_{L,R}=(1\mp\gamma_5)/2$. Compute $\Gamma(\Psi \to \psi\,V)$ at $g_L = 0.58$, $g_R = 0.29$, $m_F = 900$, $m_f = 180$, $m_V = 240$ GeV.

`results/answer.json`: widths in GeV under `part_a_width_gev`, `part_b_width_gev`; closed forms as sympy-parseable strings under `part_a_width_formula`, `part_b_width_formula`. Symbols `g,mF,mf,mV` for (a), `gL,gR,mF,mf,mV` for (b).

Record the derivation in `results/derivation.md`: the conventions adopted (metric signature, spinor and polarization normalizations, spin/polarization averaging, identical-particle symmetry factors), the vertex factors read off the Lagrangian, the amplitude and its spin/polarization sum, the phase-space factor, and the intermediate expressions at each step, in enough detail for the result to be checked line by line. State any limits or consistency checks performed and their outcome.
