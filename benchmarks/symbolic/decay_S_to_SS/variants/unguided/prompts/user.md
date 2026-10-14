Compute the tree-level partial widths for a real scalar $\phi$ (mass $m_S$) with two trilinear couplings. The $\mu$ have mass dimension one and are real. One width for each:

(a) $\mathcal{L} = -\,\frac{\mu}{2}\,\phi\,\chi^2$, $\chi$ a real scalar of mass $m_\chi$. Compute $\Gamma(\phi \to \chi\chi)$ at $\mu = 480$, $m_S = 950$, $m_\chi = 270$ GeV.

(b) $\mathcal{L} = -\,\mu\,\phi\,\chi_1\chi_2$, distinct real scalars of mass $m_1, m_2$. Compute $\Gamma(\phi \to \chi_1\chi_2)$ at $\mu = 315$, $m_S = 950$, $m_1 = 350$, $m_2 = 410$ GeV.

Write `results/answer.json`: widths in GeV under `part_a_width_gev`, `part_b_width_gev`, closed forms as sympy-parseable strings under `part_a_width_formula`, `part_b_width_formula`. Symbols `mu,mS,mchi` for (a), `mu,mS,m1,m2` for (b).

Record the derivation in `results/derivation.md`: the conventions adopted (metric signature, spinor and polarization normalizations, spin/polarization averaging, identical-particle symmetry factors), the vertex factors read off the Lagrangian, the amplitude and its spin/polarization sum, the phase-space factor, and the intermediate expressions at each step, in enough detail for the result to be checked line by line. State any limits or consistency checks performed and their outcome.
