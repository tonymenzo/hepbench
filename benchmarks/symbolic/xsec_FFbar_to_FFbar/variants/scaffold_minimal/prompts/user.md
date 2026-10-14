Tree-level total annihilation cross sections $\sigma(\psi_1\bar{\psi}_1 \to \psi_2\bar{\psi}_2)$ for two distinct massless Dirac species coupling only through an s-channel mediator (there is no t-channel diagram); average over the four initial spin states; give the numeric answers in picobarns. All couplings are real.

(a) Massless vector mediator: $\mathcal{L} = g\,V_\mu(\bar{\psi}_1\gamma^\mu\psi_1 + \bar{\psi}_2\gamma^\mu\psi_2)$. [$g = 0.55$, $\sqrt{s} = 730$ GeV]

(b) Heavy scalar mediator (real scalar of mass $M_S = 1900$ GeV, negligible width, below resonance): $\mathcal{L} = -\,y_1\,\phi\,\bar{\psi}_1\psi_1 - y_2\,\phi\,\bar{\psi}_2\psi_2$. [$y_1 = 0.92$, $y_2 = 0.34$, $\sqrt{s} = 730$ GeV]

Write `results/answer.json` with the cross sections in pb under keys `part_a_xsec_pb`, `part_b_xsec_pb`, and the closed-form cross sections in natural units (GeV$^{-2}$, no pb conversion inside the formula) as sympy-parseable strings under `part_a_xsec_formula`, `part_b_xsec_formula`, where `s` is the squared centre-of-mass energy (symbols `g,s` for (a); `y1,y2,s,MS` for (b)).
