Compute the tree-level width for a heavy Dirac fermion $\Psi$ (mass $m_F$) decaying to three distinct massless Dirac fermions $\psi_a\psi_b\bar{\psi}_c$ through a heavy mediator (mass $\gg m_F$). Leading order in $m_F/M$, averaged over the initial spin. Tree-level width for each mediator; couplings real.

(a) Heavy vector $V$ (mass $M_V$), left-handed: $\mathcal{L} = g\,V_\mu\,\bar{\psi}_a\gamma^\mu P_L\Psi + g\,V_\mu\,\bar{\psi}_b\gamma^\mu P_L\psi_c + \mathrm{h.c.}$, $P_L = (1-\gamma_5)/2$. Compute $\Gamma(\Psi \to \psi_a\psi_b\bar{\psi}_c)$ at $g = 0.62$, $m_F = 17.3$, $M_V = 1450$ GeV.

(b) Heavy scalar $\phi$ (mass $M_S$): $\mathcal{L} = -\,y_1\,\phi\,\bar{\psi}_a\Psi - y_2\,\phi\,\bar{\psi}_b\psi_c + \mathrm{h.c.}$. Compute $\Gamma(\Psi \to \psi_a\psi_b\bar{\psi}_c)$ at $y_1 = 0.71$, $y_2 = 0.58$, $m_F = 17.3$, $M_S = 1450$ GeV.

`results/answer.json`: widths in GeV under `part_a_width_gev`, `part_b_width_gev`; leading-order closed forms as sympy-parseable strings under `part_a_width_formula`, `part_b_width_formula`. Symbols `g,mF,MV` for (a), `y1,y2,mF,MS` for (b).

Record the derivation in `results/derivation.md`: the conventions adopted (metric signature, spinor and polarization normalizations, spin/polarization averaging, identical-particle symmetry factors), the vertex factors read off the Lagrangian, the amplitude and its spin/polarization sum, the phase-space factor, and the intermediate expressions at each step, in enough detail for the result to be checked line by line. State any limits or consistency checks performed and their outcome.
