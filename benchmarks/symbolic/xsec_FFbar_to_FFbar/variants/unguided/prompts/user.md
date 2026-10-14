Compute the tree-level total annihilation cross sections $\sigma(\psi_1\bar{\psi}_1 \to \psi_2\bar{\psi}_2)$ for two distinct massless Dirac species coupling only through an s-channel mediator (there is no t-channel diagram). Average over the four initial spin states. Couplings real. Report the numeric values in picobarns.

(a) Massless vector mediator: $\mathcal{L} = g\,V_\mu(\bar{\psi}_1\gamma^\mu\psi_1 + \bar{\psi}_2\gamma^\mu\psi_2)$. Evaluate at $g = 0.55$, $\sqrt{s} = 730$ GeV.

(b) Heavy scalar mediator (real scalar of mass $M_S = 1900$ GeV, negligible width, below resonance): $\mathcal{L} = -\,y_1\,\phi\,\bar{\psi}_1\psi_1 - y_2\,\phi\,\bar{\psi}_2\psi_2$. Evaluate at $y_1 = 0.92$, $y_2 = 0.34$, $\sqrt{s} = 730$ GeV.

`results/answer.json`: cross sections in pb under `part_a_xsec_pb`, `part_b_xsec_pb`; the closed forms in natural units (GeV$^{-2}$, no pb conversion inside the formula) as sympy-parseable strings under `part_a_xsec_formula`, `part_b_xsec_formula`, with `s` the squared centre-of-mass energy. Symbols `g,s` for (a), `y1,y2,s,MS` for (b).

Record the derivation in `results/derivation.md`: the conventions adopted (metric signature, spinor and polarization normalizations, spin/polarization averaging, identical-particle symmetry factors), the vertex factors read off the Lagrangian, the amplitude and its spin/polarization sum, the phase-space factor, and the intermediate expressions at each step, in enough detail for the result to be checked line by line. State any limits or consistency checks performed and their outcome.
