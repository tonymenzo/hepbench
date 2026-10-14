Compute the tree-level widths for a massive neutral vector $V^\mu$ (mass $m_V$) decaying to a scalar $S$ plus a second massive vector $V'$ (mass $m_{V'}$), via $\mathcal{L} = g\, S\, V_\mu V'^\mu$ with $g$ of mass dimension one and real. Average over the parent's three polarizations, sum over $V'$'s. Tree-level width for each case:

(a) Massive scalar daughter (mass $m_S$). Compute $\Gamma(V \to S\,V')$ at $g = 180$ GeV, $m_V = 700$, $m_S = 160$, $m_{V'} = 250$ GeV.

(b) Massless scalar daughter ($m_S = 0$). Compute $\Gamma(V \to S\,V')$ at $g = 150$ GeV, $m_V = 700$, $m_{V'} = 250$ GeV.

`results/answer.json`: widths in GeV under `part_a_width_gev`, `part_b_width_gev`; closed forms as sympy-parseable strings under `part_a_width_formula`, `part_b_width_formula`. Symbols `g,mV,mS,mVp` for (a), with $m_{V'}$ written `mVp`, and `g,mV,mVp` for (b).

Record the derivation in `results/derivation.md`: the conventions adopted (metric signature, spinor and polarization normalizations, spin/polarization averaging, identical-particle symmetry factors), the vertex factors read off the Lagrangian, the amplitude and its spin/polarization sum, the phase-space factor, and the intermediate expressions at each step, in enough detail for the result to be checked line by line. State any limits or consistency checks performed and their outcome.
