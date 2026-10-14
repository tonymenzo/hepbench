Compute the tree-level partial widths of a real scalar $\phi$ (mass $m_S$) going to fermion pairs, in three separate coupling structures. Couplings are all real.

(a) Scalar Yukawa, $\mathcal{L} = -\,y\,\phi\,\bar{\psi}\psi$, with $\psi$ a Dirac fermion of mass $m_f$. Compute $\Gamma(\phi \to \psi\bar{\psi})$ at $y = 0.87$, $m_S = 1240$, $m_f = 320$ GeV.

(b) Same fields, pseudoscalar coupling $\mathcal{L} = -\,i\,y\,\phi\,\bar{\psi}\gamma_5\psi$. Compute $\Gamma(\phi \to \psi\bar{\psi})$ at $y = 0.54$, $m_S = 1240$, $m_f = 320$ GeV.

(c) Chiral, to two distinct Dirac fermions of mass $m_1, m_2$: $\mathcal{L} = -\,\phi\,\bar{\psi}_1(y_L P_L + y_R P_R)\psi_2 + \mathrm{h.c.}$ with $P_{L,R} = (1\mp\gamma_5)/2$. Just the single channel $\Gamma(\phi \to \psi_1\bar{\psi}_2)$, not the conjugate. $y_L = 0.31$, $y_R = 0.78$, $m_S = 1240$, $m_1 = 410$, $m_2 = 95$ GeV.

Write `results/answer.json`: widths in GeV under `part_a_width_gev`, `part_b_width_gev`, `part_c_width_gev`, and the closed forms as sympy-parseable strings under `part_a_width_formula`, `part_b_width_formula`, `part_c_width_formula`. Use symbols `y,mS,mf` for (a) and (b), `yL,yR,mS,m1,m2` for (c).

Record the derivation in `results/derivation.md`: the conventions adopted (metric signature, spinor and polarization normalizations, spin/polarization averaging, identical-particle symmetry factors), the vertex factors read off the Lagrangian, the amplitude and its spin/polarization sum, the phase-space factor, and the intermediate expressions at each step, in enough detail for the result to be checked line by line. State any limits or consistency checks performed and their outcome.
