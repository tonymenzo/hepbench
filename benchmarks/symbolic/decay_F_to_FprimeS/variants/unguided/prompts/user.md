Compute the tree-level widths for a heavy Dirac fermion $\Psi$ (mass $m_F$) decaying to a lighter Dirac fermion $\psi$ (mass $m_f$) plus a real scalar $\phi$ (mass $m_S$). Average over the initial spin. Tree-level width for each of two couplings; couplings real.

(a) $\mathcal{L} = -\,y\,\phi\,\bar{\psi}\Psi + \mathrm{h.c.}$. Compute $\Gamma(\Psi \to \psi\,\phi)$ at $y = 0.66$, $m_F = 880$, $m_f = 130$, $m_S = 340$ GeV.

(b) $\mathcal{L} = -\,\phi\,\bar{\psi}(y_L P_L + y_R P_R)\Psi + \mathrm{h.c.}$, $P_{L,R} = (1\mp\gamma_5)/2$. Compute $\Gamma(\Psi \to \psi\,\phi)$ at $y_L = 0.45$, $y_R = 0.18$, $m_F = 880$, $m_f = 130$, $m_S = 340$ GeV.

`results/answer.json`: widths in GeV under `part_a_width_gev`, `part_b_width_gev`; closed forms as sympy-parseable strings under `part_a_width_formula`, `part_b_width_formula`. Symbols `y,mF,mf,mS` for (a), `yL,yR,mF,mf,mS` for (b).

Record the derivation in `results/derivation.md`: the conventions adopted (metric signature, spinor and polarization normalizations, spin/polarization averaging, identical-particle symmetry factors), the vertex factors read off the Lagrangian, the amplitude and its spin/polarization sum, the phase-space factor, and the intermediate expressions at each step, in enough detail for the result to be checked line by line. State any limits or consistency checks performed and their outcome.
