Compute the tree-level widths for a real scalar $\phi$ (mass $m_S$) decaying into two massive neutral vectors. The $g$ have mass dimension one and are real; sum over the vectors' polarizations.

(a) Identical vectors: $\mathcal{L} = g\, \phi\, V_\mu V^\mu$, $V$ of mass $m_V$. Compute $\Gamma(\phi \to VV)$ at $g = 130$ GeV, $m_S = 400$, $m_V = 90$ GeV.

(b) Distinct vectors: $\mathcal{L} = g\, \phi\, V_{1\mu} V_2^\mu$, masses $m_1, m_2$. Compute $\Gamma(\phi \to V_1 V_2)$ at $g = 110$ GeV, $m_S = 400$, $m_1 = 90$, $m_2 = 150$ GeV.

`results/answer.json`: widths in GeV under `part_a_width_gev`, `part_b_width_gev`; closed forms as sympy-parseable strings under `part_a_width_formula`, `part_b_width_formula`. Symbols `g,mS,mV` for (a), `g,mS,m1,m2` for (b).

Record the derivation in `results/derivation.md`: the conventions adopted (metric signature, spinor and polarization normalizations, spin/polarization averaging, identical-particle symmetry factors), the vertex factors read off the Lagrangian, the amplitude and its spin/polarization sum, the phase-space factor, and the intermediate expressions at each step, in enough detail for the result to be checked line by line. State any limits or consistency checks performed and their outcome.
