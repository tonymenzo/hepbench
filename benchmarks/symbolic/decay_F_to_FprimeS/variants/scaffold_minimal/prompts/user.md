A heavy Dirac fermion $\Psi$ (mass $m_F$) decays to a lighter Dirac fermion $\psi$ (mass $m_f$) plus a real scalar $\phi$ (mass $m_S$); average over the initial spin. Give the tree-level width for each coupling. All couplings are real.

(a) $\mathcal{L} = -\,y\,\phi\,\bar{\psi}\Psi + \mathrm{h.c.}$: $\Gamma(\Psi \to \psi\,\phi)$. [$y = 0.66$, $m_F = 880$, $m_f = 130$, $m_S = 340$ GeV]

(b) $\mathcal{L} = -\,\phi\,\bar{\psi}(y_L P_L + y_R P_R)\Psi + \mathrm{h.c.}$, $P_{L,R} = (1\mp\gamma_5)/2$: $\Gamma(\Psi \to \psi\,\phi)$. [$y_L = 0.45$, $y_R = 0.18$, $m_F = 880$, $m_f = 130$, $m_S = 340$ GeV]

Write `results/answer.json` with the widths in GeV under keys `part_a_width_gev`, `part_b_width_gev`, and the closed-form widths as sympy-parseable strings under `part_a_width_formula`, `part_b_width_formula` (symbols `y,mF,mf,mS` for (a); `yL,yR,mF,mf,mS` for (b)).
