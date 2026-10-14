Compute the tree-level widths for a scalar $\phi$ (mass $m_S$) decaying to a lighter scalar $\phi'$ (mass $m_{S'}$) plus a massive neutral vector $V$ (mass $m_V$), via
$$\mathcal{L} = g\, V^\mu\left(\phi\,\partial_\mu \phi' - \phi'\,\partial_\mu \phi\right),$$
$g$ dimensionless and real. Sum over the vector's three polarizations. Tree-level width for each case:

(a) Massive scalar daughter. Compute $\Gamma(\phi \to \phi'\,V)$ at $g = 0.90$, $m_S = 600$, $m_{S'} = 140$, $m_V = 250$ GeV.

(b) Massless scalar daughter ($m_{S'} = 0$). Compute $\Gamma(\phi \to \phi'\,V)$ at $g = 0.70$, $m_S = 600$, $m_V = 250$ GeV.

`results/answer.json`: widths in GeV under `part_a_width_gev`, `part_b_width_gev`; closed forms as sympy-parseable strings under `part_a_width_formula`, `part_b_width_formula`. Symbols `g,mS,mSp,mV` for (a), with $m_{S'}$ written `mSp`, and `g,mS,mV` for (b).

Record the derivation in `results/derivation.md`: the conventions adopted (metric signature, spinor and polarization normalizations, spin/polarization averaging, identical-particle symmetry factors), the vertex factors read off the Lagrangian, the amplitude and its spin/polarization sum, the phase-space factor, and the intermediate expressions at each step, in enough detail for the result to be checked line by line. State any limits or consistency checks performed and their outcome.
