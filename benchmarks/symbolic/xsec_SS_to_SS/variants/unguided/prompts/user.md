Compute the tree-level total cross sections for $2\to2$ scattering of real scalars via quartic contact interactions, in the centre-of-mass frame. Couplings real and dimensionless. Report the numeric values in picobarns.

(a) $\mathcal{L} = -\,\frac{\lambda}{4!}\,\phi^4$, $\phi$ a real scalar of mass $m_\phi$. Compute $\sigma(\phi\phi \to \phi\phi)$ at $\lambda = 2.3$, $m_\phi = 75$ GeV, $\sqrt{s} = 480$ GeV.

(b) $\mathcal{L} = -\,\frac{\lambda_{12}}{4}\,\phi^2\chi^2$, $\chi$ a real scalar of mass $m_\chi$. Compute $\sigma(\phi\phi \to \chi\chi)$ at $\lambda_{12} = 1.7$, $m_\phi = 75$, $m_\chi = 210$ GeV, $\sqrt{s} = 480$ GeV.

`results/answer.json`: cross sections in pb under `part_a_xsec_pb`, `part_b_xsec_pb`; closed forms in natural units (GeV$^{-2}$, no pb conversion inside the formula) as sympy-parseable strings under `part_a_xsec_formula`, `part_b_xsec_formula`, with `s` the squared centre-of-mass energy and `lam` the part's quartic coupling. Symbols `lam,s,mphi` for (a), `lam,s,mphi,mchi` for (b). Only include the dependence that actually shows up.

Record the derivation in `results/derivation.md`: the conventions adopted (metric signature, spinor and polarization normalizations, spin/polarization averaging, identical-particle symmetry factors), the vertex factors read off the Lagrangian, the amplitude and its spin/polarization sum, the phase-space factor, and the intermediate expressions at each step, in enough detail for the result to be checked line by line. State any limits or consistency checks performed and their outcome.
