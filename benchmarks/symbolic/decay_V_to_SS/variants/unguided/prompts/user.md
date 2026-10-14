Compute the tree-level widths for a massive neutral vector $V^\mu$ (mass $m_V$) decaying to two scalars through the derivative coupling
$$\mathcal{L} = g\, V^\mu\left(S_1\,\partial_\mu S_2 - S_2\,\partial_\mu S_1\right),$$
$g$ dimensionless and real. Average over the three initial polarizations. Tree-level width for each case:

(a) Distinct massive scalars of masses $m_1$, $m_2$. Compute $\Gamma(V \to S_1 S_2)$ at $g = 0.85$, $m_V = 500$, $m_1 = 120$, $m_2 = 210$ GeV.

(b) One scalar massless ($m_2 = 0$), the other of mass $m_1$. Compute $\Gamma(V \to S_1 S_2)$ at $g = 0.62$, $m_V = 500$, $m_1 = 180$ GeV.

`results/answer.json`: widths in GeV under `part_a_width_gev`, `part_b_width_gev`; closed forms as sympy-parseable strings under `part_a_width_formula`, `part_b_width_formula`. Symbols `g,mV,m1,m2` for (a), `g,mV,m1` for (b).

Record the derivation in `results/derivation.md`: the conventions adopted (metric signature, spinor and polarization normalizations, spin/polarization averaging, identical-particle symmetry factors), the vertex factors read off the Lagrangian, the amplitude and its spin/polarization sum, the phase-space factor, and the intermediate expressions at each step, in enough detail for the result to be checked line by line. State any limits or consistency checks performed and their outcome.
