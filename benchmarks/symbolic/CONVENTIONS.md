# Conventions for the symbolic benchmark family

This document defines the physics conventions used by all benchmarks in `benchmarks/symbolic/`. The interaction Lagrangian stated in each task prompt, the analytic formula committed to each `ground_truth/truth.json`, and the independent numerical check in `_shared/dirac_numeric.py` must all conform to these conventions.

Each `ground_truth/derivation.py` verifies agreement with `_shared/dirac_numeric.py` to a relative error below $10^{-10}$ ($10^{-3}$ for three-body Monte Carlo integration). The numerical implementation is checked against textbook results for spinor completeness, the muon width, and the QED point cross section in `tests/test_symbolic_dirac_numeric.py`; `tests/test_symbolic_conventions_audit.py` reruns all derivations to verify consistency. Changes to these conventions require updating `dirac_numeric.py` and rerunning all derivations.

Primary references are M. E. Peskin and D. V. Schroeder, *An Introduction to Quantum Field Theory* (P&S), and the PDG *Kinematics* review (R. L. Workman et al. (Particle Data Group), Prog. Theor. Exp. Phys. 2022, 083C01), Section 50. Section numbers below refer to these sources.

## 1. Units

Natural units are used, with $\hbar = c = 1$. All dimensionful quantities are expressed in powers of $\mathrm{GeV}$. Numerical conversions use the PDG physical constants:

- $\hbar = 6.582119569 \times 10^{-25}\,\mathrm{GeV}\,\mathrm{s}$, giving the lifetime $\tau = \hbar / \Gamma$.
- $(\hbar c)^2 = 3.893793721 \times 10^8\,\mathrm{GeV}^2\,\mathrm{pb}$, giving $\sigma[\mathrm{pb}] = \sigma[\mathrm{GeV}^{-2}] \times 3.893793721 \times 10^8$.

## 2. Metric and Dirac algebra

- The metric is $\eta_{\mu\nu} = \operatorname{diag}(+1, -1, -1, -1)$. The four-vector inner product is $p \cdot q = p^0 q^0 - \mathbf{p} \cdot \mathbf{q}$, and slash notation denotes $\not{p} = \gamma^\mu p_\mu$.
- The Clifford algebra is $\{\gamma^\mu, \gamma^\nu\} = 2\eta^{\mu\nu}\mathbf{1}_4$.
- $\gamma^5 = i\gamma^0\gamma^1\gamma^2\gamma^3$, $(\gamma^5)^2 = \mathbf{1}$, and $\{\gamma^5, \gamma^\mu\} = 0$.
- The chiral projectors are $P_L = (1 - \gamma^5)/2$ and $P_R = (1 + \gamma^5)/2$, fixing the sign convention as $P_{L,R} = (1 \mp \gamma^5)/2$. They satisfy $P_L + P_R = \mathbf{1}$.
- $\sigma^{\mu\nu} = (i/2)[\gamma^\mu, \gamma^\nu]$. This tensor appears only in dimension-five dipole operators, which are outside the scope of the dimension-four family.
- The numerical check explicitly uses the Dirac representation. All committed results are representation-independent and involve only traces.

## 3. Spinors and external states

- Spinors are normalized as $\bar{u}(p,s)u(p,s) = 2m$, $\bar{v}(p,s)v(p,s) = -2m$, and $u^\dagger u = v^\dagger v = 2E$ (P&S 3.50).
- The spin sums are $\sum_s u(p,s)\bar{u}(p,s) = \not{p} + m$ and $\sum_s v(p,s)\bar{v}(p,s) = \not{p} - m$ (P&S 3.66).
- A massive vector with mass $M$ and momentum $p$ has three physical polarizations $\epsilon(p,\lambda)$ satisfying $p \cdot \epsilon = 0$ and $\epsilon(\lambda) \cdot \epsilon^*(\lambda') = -\delta_{\lambda\lambda'}$. Their completeness relation is

  $$
  \sum_\lambda \epsilon^\mu(p,\lambda)\epsilon^{*\nu}(p,\lambda)
  = -\eta^{\mu\nu} + \frac{p^\mu p^\nu}{M^2}.
  $$

  Massless vectors do not appear as two-body decay parents or as a massive-to-massless threshold; all vectors in this family are massive.

## 4. Couplings and Feynman rules

Each prompt explicitly states the interaction Lagrangian. The vertex factor follows from the standard prescription: $i$ times the functional derivative of $\mathcal{L}_{\mathrm{int}}$ with respect to the fields, with all momenta incoming. Couplings are real unless stated otherwise in the prompt. The canonical operators and vertex factors are listed below. In every case, validation requires that `dirac_numeric.py` reproduce the closed-form result.

| Operator ($\mathcal{L}_{\mathrm{int}}$) | Vertex factor |
|---|---|
| $-y\phi\bar{\psi}\psi$ (scalar Yukawa) | $-iy$ |
| $-iy\phi\bar{\psi}\gamma^5\psi$ (pseudoscalar) | $y\gamma^5$ |
| $-\phi\bar{\psi}(y_L P_L + y_R P_R)\psi' + \mathrm{h.c.}$ (chiral) | $-i(y_L P_L + y_R P_R)$ |
| $V_\mu\bar{\psi}\gamma^\mu(g_V - g_A\gamma^5)\psi$ (vector/axial) | $i\gamma^\mu(g_V - g_A\gamma^5)$ |
| $gV_\mu\bar{\psi}\gamma^\mu P_L\psi' + \mathrm{h.c.}$ (chiral gauge) | $ig\gamma^\mu P_L$ |
| $-(\mu/2)\phi\chi^2$ (identical cubic scalar) | $-i\mu$ |
| $-\mu\phi\chi_1\chi_2$ (distinct cubic scalar) | $-i\mu$ |
| $gSV_\mu V^\mu$ (scalar-vector-vector, with $g$ of mass dimension one) | $2ig\eta^{\mu\nu}$ |
| $gV^\mu(S_1\partial_\mu S_2 - S_2\partial_\mu S_1)$ (derivative SSV) | $g(p_1 - p_2)_\mu$ for the two scalars |
| Triple-gauge $g[\eta^{\mu\nu}(p_1-p_2)^\rho + \text{cyclic}]$ (VVV) | Standard non-Abelian form |

The factor of two arising from the two identical functional derivatives in the cubic-scalar and SVV rules is part of the convention. This is a common source of errors in derivations and motivates the numerical validation of every result.

## 5. Spin and polarization averaging

Initial states are averaged and final states are summed:

- Apply an averaging factor of $1/(2s+1) = 1/2$ per initial fermion and $1/3$ per initial massive vector.
- A scalar parent requires no averaging factor.
- Sum over all final spins and polarizations.

The squared matrix element $\langle |\mathcal{M}|^2 \rangle$ in a `truth.json` derivation always denotes the quantity averaged over initial spins and summed over final spins.

## 6. Phase space and rate master formulas

The Källén function is defined as

$$
\lambda(a,b,c) = a^2 + b^2 + c^2 - 2ab - 2bc - 2ca.
$$

For a parent of mass $M$ decaying to particles of masses $m_1$ and $m_2$, the center-of-mass momentum is

$$
|\mathbf{p}| = \frac{\sqrt{\lambda(M^2,m_1^2,m_2^2)}}{2M}.
$$

**Two-body width** (PDG 50.18):

$$
\Gamma = \frac{|\mathbf{p}|}{8\pi M^2}
\frac{\langle |\mathcal{M}|^2 \rangle}{S}.
$$

**Three-body width** (PDG 50.22), with the parent at rest:

$$
\mathrm{d}\Gamma = \frac{1}{(2\pi)^3}\frac{1}{32M^3}
\langle |\mathcal{M}|^2 \rangle\,
\mathrm{d}m_{12}^2\,\mathrm{d}m_{23}^2.
$$

This expression is integrated over the Dalitz region, with bounds given in PDG 50.23a.

**$2 \to 2$ cross section** (PDG 50.32), in the center-of-mass frame:

$$
\frac{\mathrm{d}\sigma}{\mathrm{d}\Omega}
= \frac{\langle |\mathcal{M}|^2 \rangle\,|\mathbf{p}_f|}
{64\pi^2 s\,|\mathbf{p}_i|}.
$$

The total cross section $\sigma$ is obtained by angular integration.

## 7. Identical-particle symmetry factor

A final state containing $n$ identical particles of a given species carries a factor $1/S$ in the rate, where

$$
S = \prod_{\mathrm{species}} (n_{\mathrm{species}}!).
$$

Thus, two identical final particles contribute a factor of $1/2$, which also applies to cross sections into identical pairs. The combinatorial factor in the Feynman rule (Section 4) and the final-state symmetry factor $S$ are tracked separately and must not be counted twice. `dirac_numeric.py` applies $S$ explicitly through its `symmetry=` argument; the analytic formula must use the same convention.

## 8. Scope

The family covers dimension-four (renormalizable), Lorentz-invariant interactions among scalars, Dirac fermions, and massive vectors at tree level. The complete set of dimension-four two-body decay archetypes is listed in `README.md`.

Derivative dimension-five operators (dipole and field-strength), loop-induced decays, spin-two and graviton couplings, and Majorana fermions are outside this scope. All fermions in the family are Dirac.