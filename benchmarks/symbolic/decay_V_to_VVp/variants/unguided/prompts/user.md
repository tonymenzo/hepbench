Compute the tree-level widths for a massive neutral vector $V^\mu$ (mass $m_V$) decaying to two distinct massive vectors $V_1$, $V_2$ (masses $m_1$, $m_2$) through the standard Yang-Mills triple-gauge vertex
$$\Gamma^{\mu_1\mu_2\mu_3}(k_1,k_2,k_3) = g\left[\eta^{\mu_1\mu_2}(k_1-k_2)^{\mu_3} + \eta^{\mu_2\mu_3}(k_2-k_3)^{\mu_1} + \eta^{\mu_3\mu_1}(k_3-k_1)^{\mu_2}\right],$$
written with all three momenta flowing **into** the vertex, so that $k_1+k_2+k_3=0$; for $V(P)\to V_1(q_1)V_2(q_2)$ the legs therefore enter as $(k_1,k_2,k_3)=(P,-q_1,-q_2)$, with $\varepsilon(P)$, $\varepsilon^*(q_1)$, $\varepsilon^*(q_2)$ on the three legs, $g$ real and dimensionless. Average over the parent's three polarizations, sum over the daughters'. Two parameter points:

(a) $g = 0.80$, $m_V = 900$, $m_1 = 200$, $m_2 = 250$ GeV.

(b) $g = 0.65$, $m_V = 1200$, $m_1 = 180$, $m_2 = 400$ GeV.

Numeric values only; the closed form is not required. `results/answer.json` with the widths in GeV under `part_a_width_gev` and `part_b_width_gev`.

Record the derivation in `results/derivation.md`: the conventions adopted (metric signature, spinor and polarization normalizations, spin/polarization averaging, identical-particle symmetry factors), the vertex factors read off the Lagrangian, the amplitude and its spin/polarization sum, the phase-space factor, and the intermediate expressions at each step, in enough detail for the result to be checked line by line. State any limits or consistency checks performed and their outcome.
