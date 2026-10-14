"""
# benchmarks/llp_forward/_shared/production_vector.py is a part of HEPBench.
# Copyright (C) 2026 HEPBench authors (see AUTHORS for details).
# HEPBench is licensed under the GNU GPL v3 or later, see LICENSE for details.
"""
"""
Vector-meson production of the muon-philic scalar for the `llp_forward`
family:

    V(P) -> mu^+(p1) mu^-(p2) phi(p3),

a scalar phi radiated off one of the two muon legs of the leptonic vector
decay V -> mu^+ mu^-. The vector couples to the muon current through its
V -> gamma* -> mu mu vertex (VMD), characterized by a single constant C_V;
phi attaches to EITHER muon leg through the muon propagator, so there are
TWO diagrams (contrast the single-diagram pseudoscalar M -> mu nu phi).

Because the muon electromagnetic current is conserved, the amplitude obeys
a Ward identity: replacing the vector polarization by P gives zero. This is
the primary cross-check here (it fixes the relative sign / propagator
momenta of the two diagrams), alongside the 2-body normalization.

Normalization (the model-card contract, parallel to the pseudoscalar kappa):
The only hadronic input is the DIMENSIONLESS branching BR(V -> mu mu). The
V->mu mu coupling C_V drops out of the ratio, so the g^2-stripped branching
to the scalar is

    kappa_V(m_phi) = BR(V -> mu mu) * R_V(m_phi),
    R_V(m_phi)    = Gamma(V -> mu mu phi) / Gamma(V -> mu mu)  |_{C_V = g = 1},

i.e. the per-(V->mu mu) probability of radiating a g^2-stripped phi. The phi
yield per vector meson is then w_V * kappa_V * g^2, exactly as for the
pseudoscalar parents -- one flux, exact g^2 reweighting.

All matrix elements are at C_V = g = 1 ("C_V^2- and g^2-stripped").
"""

import os
import sys

import numpy as np

# Locate benchmarks/symbolic/_shared (dirac_numeric) by walking up from this
# file, so it resolves regardless of how deep this engine sits under benchmarks/.
_here = os.path.dirname(os.path.abspath(__file__))
for _ in range(6):
    _cand = os.path.join(_here, "symbolic", "_shared")
    if os.path.isdir(_cand):
        if _cand not in sys.path:
            sys.path.insert(0, _cand)
        break
    _here = os.path.dirname(_here)

from dirac_numeric import (  # noqa: E402
    ID4, mdot, slash, v_spinor, ubar, two_body_width, three_body_width,
)

MMU = 0.1056584  # GeV


# rest-frame vector polarizations (parent at rest: P = (mV, 0, 0, 0))
_EPS = (np.array([0.0, 1.0, 0.0, 0.0]),
        np.array([0.0, 0.0, 1.0, 0.0]),
        np.array([0.0, 0.0, 0.0, 1.0]))


# ---------------------------------------------------------------------------
# matrix elements (explicit Dirac spinors; rest-frame polarizations)
# ---------------------------------------------------------------------------
def _amp_vector(p1, p2, p3, m_mu, eps):
    """A_A + A_B for one polarization: phi off the mu^- (p2) leg plus phi off
    the mu^+ (p1) leg. p1 = mu^+ (v-spinor), p2 = mu^- (ubar)."""
    se = slash(eps)
    DA = mdot(p2 + p3, p2 + p3) - m_mu * m_mu          # = 2 p2.p3 + m_phi^2
    DB = mdot(p1 + p3, p1 + p3) - m_mu * m_mu          # = 2 p1.p3 + m_phi^2
    propA = slash(p2 + p3) + m_mu * ID4                # internal mom +(p2+p3)
    propB = -slash(p1 + p3) + m_mu * ID4               # internal mom -(p1+p3)
    MA = propA @ se / DA
    MB = se @ propB / DB
    return MA + MB


def msq_vector(p1, p2, p3, m_mu=MMU):
    """Spin-summed, polarization-AVERAGED |M(V->mu mu phi)|^2 at C_V = g = 1."""
    total = 0.0
    for eps in _EPS:
        core = _amp_vector(p1, p2, p3, m_mu, eps)
        for s1 in (0, 1):                              # mu^+ (v)
            v = v_spinor(p1, m_mu, s1)
            for s2 in (0, 1):                          # mu^- (ubar)
                ub = ubar(p2, m_mu, s2)
                amp = ub @ core @ v
                total += float(np.real(amp * np.conj(amp)))
    return total / 3.0


def msq_vector_munu(p1, p2, eps_mom, m_mu=MMU):
    """|M(V->mu mu)|^2 (no phi) contracted with a given polarization 4-vector,
    spin-summed. Used for the Ward-identity check (eps_mom = P must give 0)."""
    se = slash(eps_mom)
    total = 0.0
    for s1 in (0, 1):
        v = v_spinor(p1, m_mu, s1)
        for s2 in (0, 1):
            ub = ubar(p2, m_mu, s2)
            amp = ub @ se @ v
            total += float(np.real(amp * np.conj(amp)))
    return total


def msq_vector_2body(p1, p2, m_mu=MMU):
    """Spin-summed, pol-averaged |M(V->mu mu)|^2 at C_V = 1."""
    total = 0.0
    for eps in _EPS:
        total += msq_vector_munu(p1, p2, eps, m_mu)
    return total / 3.0


# ---------------------------------------------------------------------------
# rates (C_V = g = 1)
# ---------------------------------------------------------------------------
def gamma2_unit(mV, m_mu=MMU):
    """Gamma(V -> mu mu) at C_V = 1 [GeV] via the shared 2-body integrator."""
    return two_body_width(mV, m_mu, m_mu, lambda a, b: msq_vector_2body(a, b))


def gamma2_closed(mV, m_mu=MMU):
    """Closed form: C_V=1 => Gamma = mV/(12 pi)(1 + 2 m^2/mV^2) beta."""
    if mV <= 2 * m_mu:
        return 0.0
    r = m_mu * m_mu / (mV * mV)
    beta = np.sqrt(1.0 - 4.0 * r)
    return mV / (12.0 * np.pi) * (1.0 + 2.0 * r) * beta


def gamma3_unit(mV, m_phi, m_mu=MMU, n12=140, n23=140):
    """Gamma(V -> mu mu phi) at C_V = g = 1 [GeV] via the shared Dalitz
    integrator (mu^+ = 1, mu^- = 2, phi = 3; distinguishable, symmetry=1)."""
    if m_phi >= mV - 2.0 * m_mu:
        return 0.0
    return three_body_width(mV, m_mu, m_mu, m_phi,
                            lambda a, b, c: msq_vector(a, b, c, m_mu),
                            n12=n12, n23=n23)


def radiation_factor(mV, m_phi, m_mu=MMU, **quad):
    """R_V(m_phi) = Gamma(V->mu mu phi)/Gamma(V->mu mu) at g=1 (C_V cancels)."""
    g2 = gamma2_unit(mV, m_mu)
    return gamma3_unit(mV, m_phi, m_mu, **quad) / g2 if g2 > 0 else 0.0


# ---------------------------------------------------------------------------
# vector-parent registry (masses PDG; BR(V->mu mu) are [PIN] toy-ish inputs)
# ---------------------------------------------------------------------------
# name -> (mass_gev, BR_mumu)
VECTORS = {
    "rho":   (0.77526, 4.55e-5),
    "omega": (0.78266, 1.30e-4),
    "phi":   (1.01946, 2.85e-4),
    "Jpsi":  (3.09690, 5.961e-2),
    "psi2S": (3.68610, 8.00e-3),
}


def is_open(name, m_phi):
    mV = VECTORS[name][0]
    return m_phi < mV - 2.0 * MMU


def kappa(name, m_phi, **quad):
    """kappa_V(m_phi) = BR(V->mu mu) * R_V(m_phi) = Br(V->mu mu phi)|_{g=1}."""
    mV, br = VECTORS[name]
    if not is_open(name, m_phi):
        return 0.0
    return br * radiation_factor(mV, m_phi, **quad)


def decay_vector_to_phi(name, parent_p4, m_phi, rng, kappa_val=None,
                        n_x=200, n_c=60):
    """Decay a supplied lab-frame vector-meson flux to a weighted phi flux.

    Mirrors parents.decay_parents_to_phi: phi energy fraction drawn from the
    exact V->mu mu phi x-marginal, isotropic in the parent rest frame, boosted
    to the lab; weight carries kappa_V (g^2-stripped)."""
    mV = VECTORS[name][0]
    p4 = np.asarray(parent_p4, dtype=float)
    n = len(p4)
    if n == 0 or not is_open(name, m_phi):
        return {"p4": np.zeros((0, 4)), "weight": np.zeros(0), "parent": name,
                "vertex": np.zeros((0, 3))}
    if kappa_val is None:
        kappa_val = kappa(name, m_phi)
    x = _sample_x_vector(mV, m_phi, n, rng, n_grid=n_x, n_c=n_c)
    estar = 0.5 * x * mV
    pstar = np.sqrt(np.maximum(estar ** 2 - m_phi ** 2, 0.0))
    cth = rng.uniform(-1.0, 1.0, n)
    sth = np.sqrt(1.0 - cth ** 2)
    az = rng.uniform(0.0, 2.0 * np.pi, n)
    kstar = pstar[:, None] * np.stack(
        [sth * np.cos(az), sth * np.sin(az), cth], axis=1)
    E_par, pvec = p4[:, 0], p4[:, 1:]
    pdotk = np.einsum("ij,ij->i", pvec, kstar)
    E_lab = (estar * E_par + pdotk) / mV
    coef = pdotk / (mV * (E_par + mV)) + estar / mV
    klab = kstar + coef[:, None] * pvec
    phi_p4 = np.concatenate([E_lab[:, None], klab], axis=1)
    # Vector mesons are prompt (c*tau ~ fm-pm), so the phi is produced at the
    # IP: a zero production vertex (segment_from_vertex then reduces to the
    # origin-based intersection). Kept for a uniform combined-flux interface.
    return {"p4": phi_p4, "weight": np.full(n, kappa_val / n), "parent": name,
            "vertex": np.zeros((n, 3))}


def _phi_energy_density(mV, m_phi, x, m_mu=MMU, n_c=40):
    """d Gamma/dx marginal (up to norm) of the phi energy fraction x=2E_phi/mV
    in V->mu mu phi, integrating the di-muon invariant over a fixed grid."""
    E3 = 0.5 * x * mV
    if E3 <= m_phi:
        return 0.0
    # m12^2 = (mu mu) invariant = mV^2 + m_phi^2 - 2 mV E3
    m12sq = mV * mV + m_phi * m_phi - 2.0 * mV * E3
    if m12sq <= 4.0 * m_mu * m_mu:
        return 0.0
    # integrate the Dalitz density at fixed m12^2 over m23^2
    from dirac_numeric import dalitz_bounds_m23sq, three_body_momenta
    lo, hi = dalitz_bounds_m23sq(mV, m_mu, m_mu, m_phi, m12sq)
    if hi <= lo:
        return 0.0
    cs = lo + (np.arange(n_c) + 0.5) * (hi - lo) / n_c
    tot = 0.0
    for m23sq in cs:
        p1, p2, p3 = three_body_momenta(mV, m_mu, m_mu, m_phi, m12sq, m23sq)
        tot += msq_vector(p1, p2, p3, m_mu)
    return tot * (hi - lo) / n_c


def _sample_x_vector(mV, m_phi, n, rng, n_grid=200, n_c=40, m_mu=MMU):
    x_lo = 2.0 * m_phi / mV
    x_hi = 1.0 + (m_phi * m_phi - 4.0 * m_mu * m_mu) / (mV * mV)
    xs = np.linspace(x_lo + 1e-9, x_hi - 1e-9, n_grid)
    dens = np.array([_phi_energy_density(mV, m_phi, x, m_mu, n_c) for x in xs])
    dens = np.maximum(dens, 0.0)
    cdf = np.concatenate([[0.0], np.cumsum(dens)])
    if cdf[-1] <= 0:
        return np.full(n, 0.5 * (x_lo + x_hi))
    cdf /= cdf[-1]
    grid = np.concatenate([[x_lo + 1e-9], xs])
    return np.interp(rng.uniform(0.0, 1.0, n), cdf, grid)


# ---------------------------------------------------------------------------
# validation
# ---------------------------------------------------------------------------
def validate(mV=1.01946, m_phi=0.30, m_mu=MMU, seed=3):
    rng = np.random.default_rng(seed)
    # 1. 2-body normalization: spinor vs closed form
    g2s = gamma2_unit(mV, m_mu)
    g2c = gamma2_closed(mV, m_mu)
    assert abs(g2s - g2c) / g2c < 1e-9, (g2s, g2c)
    # 2. Ward identity: replace polarization by P -> amplitude^2 vanishes,
    #    at random Dalitz points of V -> mu mu phi.
    from dirac_numeric import dalitz_bounds_m23sq, three_body_momenta
    worst = 0.0
    for _ in range(200):
        lo12, hi12 = (2 * m_mu) ** 2, (mV - m_phi) ** 2
        m12sq = rng.uniform(lo12, hi12)
        lo23, hi23 = dalitz_bounds_m23sq(mV, m_mu, m_mu, m_phi, m12sq)
        if hi23 <= lo23:
            continue
        m23sq = rng.uniform(lo23, hi23)
        p1, p2, p3 = three_body_momenta(mV, m_mu, m_mu, m_phi, m12sq, m23sq)
        P = p1 + p2 + p3
        # <|M . P|^2> using the same two-diagram core, eps -> P
        num = 0.0
        core = _amp_vector(p1, p2, p3, m_mu, P)
        for s1 in (0, 1):
            v = v_spinor(p1, m_mu, s1)
            for s2 in (0, 1):
                ub = ubar(p2, m_mu, s2)
                amp = ub @ core @ v
                num += abs(amp) ** 2
        scale = msq_vector(p1, p2, p3, m_mu) * 3.0  # un-averaged magnitude
        worst = max(worst, num / max(scale, 1e-300))
    assert worst < 1e-12, f"Ward identity violated: {worst}"
    return {"gamma2_spinor": g2s, "gamma2_closed": g2c, "ward_worst": worst}


if __name__ == "__main__":
    print(validate())
