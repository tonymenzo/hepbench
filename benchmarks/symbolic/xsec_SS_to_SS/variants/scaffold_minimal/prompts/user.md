Tree-level total cross sections for $2\to2$ scattering of real scalars via quartic contact interactions, in the centre-of-mass frame; give the numeric answers in picobarns. All couplings are real and dimensionless.

(a) $\mathcal{L} = -\,\frac{\lambda}{4!}\,\phi^4$, with $\phi$ a real scalar of mass $m_\phi$: $\sigma(\phi\phi \to \phi\phi)$. [$\lambda = 2.3$, $m_\phi = 75$ GeV, $\sqrt{s} = 480$ GeV]

(b) $\mathcal{L} = -\,\frac{\lambda_{12}}{4}\,\phi^2\chi^2$, with $\chi$ a real scalar of mass $m_\chi$: $\sigma(\phi\phi \to \chi\chi)$. [$\lambda_{12} = 1.7$, $m_\phi = 75$, $m_\chi = 210$ GeV, $\sqrt{s} = 480$ GeV]

Write `results/answer.json` with the cross sections in pb under keys `part_a_xsec_pb`, `part_b_xsec_pb`, and the closed-form cross sections in natural units (GeV$^{-2}$, no pb conversion inside the formula) as sympy-parseable strings under `part_a_xsec_formula`, `part_b_xsec_formula`, where `s` is the squared centre-of-mass energy and `lam` is the part's quartic coupling (symbols `lam,s,mphi` for (a); `lam,s,mphi,mchi` for (b)).
