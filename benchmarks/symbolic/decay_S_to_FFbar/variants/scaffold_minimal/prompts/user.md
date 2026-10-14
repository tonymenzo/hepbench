A real scalar $\phi$ (mass $m_S$) couples to fermions in three independent ways; give the tree-level partial width for each. All couplings are real.

(a) $\mathcal{L} = -\,y\,\phi\,\bar{\psi}\psi$, with $\psi$ a Dirac fermion of mass $m_f$: $\Gamma(\phi \to \psi\bar{\psi})$. [$y = 0.87$, $m_S = 1240$, $m_f = 320$ GeV]

(b) $\mathcal{L} = -\,i\,y\,\phi\,\bar{\psi}\gamma_5\psi$, same fields: $\Gamma(\phi \to \psi\bar{\psi})$. [$y = 0.54$, $m_S = 1240$, $m_f = 320$ GeV]

(c) $\mathcal{L} = -\,\phi\,\bar{\psi}_1(y_L P_L + y_R P_R)\psi_2 + \mathrm{h.c.}$, with distinct Dirac fermions of mass $m_1, m_2$ and $P_{L,R} = (1\mp\gamma_5)/2$: the single channel $\Gamma(\phi \to \psi_1\bar{\psi}_2)$ only (not the conjugate). [$y_L = 0.31$, $y_R = 0.78$, $m_S = 1240$, $m_1 = 410$, $m_2 = 95$ GeV]

Write `results/answer.json` with the widths in GeV under keys `part_a_width_gev`, `part_b_width_gev`, `part_c_width_gev`, and the closed-form widths as sympy-parseable strings under `part_a_width_formula`, `part_b_width_formula`, `part_c_width_formula` (symbols `y,mS,mf` for (a) and (b); `yL,yR,mS,m1,m2` for (c)).
