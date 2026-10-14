# Conventions — the symbolic benchmark family

This is the single source of truth for the physics conventions used by
every benchmark under `benchmarks/symbolic/`. Three things must agree
with it: (1) the interaction Lagrangian quoted in each task prompt,
(2) the analytic formula committed to each `ground_truth/truth.json`,
and (3) the independent numeric check in `_shared/dirac_numeric.py`.

The conventions below are **operationally enforced**, not just
documented: every `ground_truth/derivation.py` asserts that its analytic
result reproduces, to a relative error < 1e-10 (1e-3 for Monte-Carlo'd
3-body), a from-scratch numeric computation built on
`_shared/dirac_numeric.py`. That module's own conventions are anchored
to textbook results in `tests/test_symbolic_dirac_numeric.py` (spinor
completeness, the muon width, the QED point cross section), and
`tests/test_symbolic_conventions_audit.py` re-runs every derivation to
prove the whole family is mutually consistent. If you change a
convention here, change `dirac_numeric.py` and re-run all derivations;
the tests will flag any benchmark that drifts.

Primary references: M.E. Peskin & D.V. Schroeder, *An Introduction to
Quantum Field Theory* (P&S); the PDG *Kinematics* review (R.L. Workman
et al. (Particle Data Group), Prog. Theor. Exp. Phys. 2022, 083C01),
section 50. Section numbers below refer to these.

## 1. Units

Natural units, ℏ = c = 1; all dimensionful quantities in powers of GeV.
Numeric conversions (PDG physical constants):

- ℏ = 6.582119569×10⁻²⁵ GeV·s  → lifetime τ = ℏ / Γ.
- (ℏc)² = 3.893793721×10⁸ GeV²·pb → σ[pb] = σ[GeV⁻²] × 3.893793721×10⁸.

## 2. Metric and Dirac algebra

- Metric η_μν = diag(+1, −1, −1, −1). Four-vector dot
  p·q = p⁰q⁰ − **p**·**q**. Slash p̸ = γ^μ p_μ.
- Clifford algebra {γ^μ, γ^ν} = 2 η^μν 𝟙₄.
- γ⁵ = i γ⁰γ¹γ²γ³, (γ⁵)² = 𝟙, {γ⁵, γ^μ} = 0.
- Chiral projectors **P_L = (1 − γ⁵)/2, P_R = (1 + γ⁵)/2** (so the sign
  convention is P_{L,R} = (1 ∓ γ⁵)/2). P_L + P_R = 𝟙.
- σ^μν = (i/2)[γ^μ, γ^ν] (appears only in dim-5 dipole operators, which
  are out of scope for the dim-4 family).
- The numeric check uses the Dirac representation explicitly, but every
  committed result is representation-independent (traces only).

## 3. Spinors and external states

- Normalization ū(p,s) u(p,s) = 2m, v̄(p,s) v(p,s) = −2m,
  u†u = v†v = 2E (P&S 3.50).
- Spin sums (P&S 3.66):
  Σ_s u(p,s) ū(p,s) = p̸ + m,  Σ_s v(p,s) v̄(p,s) = p̸ − m.
- Massive vector of mass M, momentum p: three physical polarizations
  ε(p,λ) with p·ε = 0, ε(λ)·ε*(λ′) = −δ_{λλ′}, and completeness
  **Σ_λ ε^μ(p,λ) ε*^ν(p,λ) = −η^μν + p^μ p^ν / M²**.
  (Massless vectors never appear as a 2-body decay parent or as a
  massive→massless threshold; all vectors in this family are massive.)

## 4. Couplings and Feynman rules

Each prompt states the interaction Lagrangian explicitly; the vertex
factor follows from it by the standard prescription (i × the functional
derivative of 𝓛_int w.r.t. the fields, momenta incoming). Couplings are
real unless a prompt says otherwise. The canonical operators and their
vertex factors (the operative check is always that `dirac_numeric.py`
reproduces the closed form):

| operator (𝓛_int) | vertex factor |
|---|---|
| −y φ ψ̄ψ (scalar Yukawa) | −i y |
| −i y φ ψ̄γ⁵ψ (pseudoscalar) | y γ⁵ |
| −φ ψ̄(y_L P_L + y_R P_R)ψ′ + h.c. (chiral) | −i (y_L P_L + y_R P_R) |
| V_μ ψ̄γ^μ(g_V − g_A γ⁵)ψ (vector/axial) | i γ^μ(g_V − g_A γ⁵) |
| g V_μ ψ̄γ^μ P_L ψ′ + h.c. (chiral gauge) | i g γ^μ P_L |
| −(μ/2) φ χ² (identical cubic scalar) | −i μ |
| −μ φ χ₁χ₂ (distinct cubic scalar) | −i μ |
| g S V_μ V^μ (scalar–vector–vector, g has mass dim 1) | 2 i g η^μν |
| g V^μ (S₁ ∂_μ S₂ − S₂ ∂_μ S₁) (derivative SSV) | g (p₁ − p₂)_μ for the two scalars |
| triple-gauge g[η^μν(p₁−p₂)^ρ + cyclic] (VVV) | standard non-abelian form |

The factor-of-2 in the cubic-scalar and SVV rules (from the two
identical functional derivatives) is part of the convention; it is the
most common place an ad-hoc derivation slips, which is exactly why every
result is numerically gated.

## 5. Spin / polarization averaging

Average over initial states, sum over final:

- average factor 1/(2s+1) per initial fermion (=1/2) and 1/3 per initial
  massive vector;
- a scalar parent carries no averaging factor;
- sum over all final spins and polarizations.

The squared matrix element symbol ⟨|𝓜|²⟩ in a `truth.json` derivation
always denotes the spin-**averaged**, spin-summed quantity.

## 6. Phase space and rate master formulas

Let λ(a,b,c) = a² + b² + c² − 2ab − 2bc − 2ca (Källén). For a parent of
mass M decaying to masses m₁, m₂ the c.m. momentum is
|p| = √λ(M², m₁², m₂²) / (2M).

- **Two-body width** (PDG 50.18):
  Γ = |p| / (8π M²) · ⟨|𝓜|²⟩ / S.
- **Three-body width** (PDG 50.22), parent at rest:
  dΓ = (1/(2π)³)(1/32M³) ⟨|𝓜|²⟩ dm₁₂² dm₂₃², integrated over the Dalitz
  region (PDG 50.23a bounds).
- **2 → 2 cross section** (PDG 50.32), c.m. frame:
  dσ/dΩ = ⟨|𝓜|²⟩ |p_f| / (64π² s |p_i|);
  total σ obtained by angular integration.

## 7. Identical-particle symmetry factor

A final state with n identical particles of a given species carries a
factor 1/S in the rate, with **S = ∏_species (n_species!)** — i.e. 1/2
for two identical final particles, and likewise for cross sections into
identical pairs. The Feynman rule's combinatoric factor (Section 4) and
this final-state S are tracked separately and must not be double-counted;
`dirac_numeric.py` applies S explicitly via its `symmetry=` argument and
the analytic formula must match.

## 8. What is in scope

Dim-4 (renormalizable) Lorentz-invariant interactions among scalars,
Dirac fermions, and massive vectors, at tree level. The complete set of
dim-4 2-body decay archetypes is enumerated in `README.md`. Out of
scope here (documented for clarity): derivative dim-5 operators
(dipole/field-strength), loop-induced decays, spin-2/graviton couplings,
and Majorana fermions (all fermions are Dirac).
