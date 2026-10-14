A heavy Dirac fermion $\Psi$ (mass $m_F$) decays to three distinct massless Dirac fermions $\psi_a\psi_b\bar{\psi}_c$ through a heavy mediator (mass $\gg m_F$); work at leading order in $m_F/M$ and average over the initial spin. Give the tree-level width for each mediator. All couplings are real.

(a) Heavy vector $V$ (mass $M_V$), left-handed couplings: $\mathcal{L} = g\,V_\mu\,\bar{\psi}_a\gamma^\mu P_L\Psi + g\,V_\mu\,\bar{\psi}_b\gamma^\mu P_L\psi_c + \mathrm{h.c.}$, with $P_L = (1-\gamma_5)/2$: $\Gamma(\Psi \to \psi_a\psi_b\bar{\psi}_c)$. [$g = 0.62$, $m_F = 17.3$, $M_V = 1450$ GeV]

(b) Heavy scalar $\phi$ (mass $M_S$): $\mathcal{L} = -\,y_1\,\phi\,\bar{\psi}_a\Psi - y_2\,\phi\,\bar{\psi}_b\psi_c + \mathrm{h.c.}$: $\Gamma(\Psi \to \psi_a\psi_b\bar{\psi}_c)$. [$y_1 = 0.71$, $y_2 = 0.58$, $m_F = 17.3$, $M_S = 1450$ GeV]

Write `results/answer.json` with the widths in GeV under keys `part_a_width_gev`, `part_b_width_gev`, and the leading-order closed-form widths as sympy-parseable strings under `part_a_width_formula`, `part_b_width_formula` (symbols `g,mF,MV` for (a); `y1,y2,mF,MS` for (b)).
