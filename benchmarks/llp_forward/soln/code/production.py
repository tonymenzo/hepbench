"""
# benchmarks/llp_forward/_shared/production.py is a part of HEPBench.
# Copyright (C) 2026 HEPBench authors (see AUTHORS for details).
# HEPBench is licensed under the GNU GPL v3 or later, see LICENSE for details.
"""
"""
Production physics for the `llp_forward` family: the tree-level matrix
element and differential branching for

    M^-(P) -> mu^-(p1) nubar(p2) phi(p3),

a muon-philic scalar phi radiated off the charged-lepton leg of an
ordinary leptonic weak decay (M = K^-, D_s^-; charge conjugates
identical). The single diagram attaches phi to the external muon line
through the muon propagator; there is no hadronic-side or neutrino-side
attachment for a leptophilic scalar, and no gauge-invariance contact
term is required for scalar emission.

Amplitude (conventions follow benchmarks/symbolic/_shared/dirac_numeric):

    A = g * C / D * ubar(p1) (slash(l) + m_mu) slash(P) (1 - gamma5) v(p2),

    l = p1 + p3,   D = l^2 - m_mu^2 = 2 p1.p3 + m_phi^2,
    C = (G_F / sqrt(2)) |V_CKM| f_M .

Two independent evaluation routes are provided and cross-checked:

  1. `msq_spinor`  -- explicit Dirac spinors and 4x4 gamma matrices
                      (numeric, from dirac_numeric primitives);
  2. `msq_trace`   -- a closed form obtained from the standard 4- and
                      6-gamma trace recursion over Minkowski dot
                      products (derived symbolically once, transcribed
                      below; epsilon-tensor terms vanish identically
                      because only three independent momenta exist).

All production quantities are computed with g = 1 and C = 1 unless
stated otherwise ("g^2- and C^2-stripped"); the physical rate carries
g^2 C^2 by exact factorization.

Differential-branching convention (the model-card contract):

    dBr/(dx dc) (M -> mu nu phi) = g^2 * kappa_M * f_M(x, c; m_phi),

with x = 2 E_phi / m_M and c = cos(theta_star) the helicity angle of
the muon in the (mu nu) rest frame relative to the recoil direction
(-p_phi). f_M is normalized to unit integral over the physical domain,
so kappa_M = Br(M -> mu nu phi) at g = 1. For a spin-0 parent the
overall orientation of the final state is isotropic, so (x, c) plus a
uniform azimuth is kinematically sufficient.
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
    GAMMA, GAMMA5, ID4, mdot, slash, u_spinor, v_spinor, ubar,
    three_body_width, three_body_momenta, dalitz_bounds_m23sq,
    two_body_width, kallen,
)

HBARC_M_GEV = 1.973269804e-16  # hbar*c in GeV*m


# ---------------------------------------------------------------------------
# matrix element, route 1: explicit spinors
# ---------------------------------------------------------------------------
def msq_spinor(P, p1, p2, p3, m_mu, m_phi):
    """Spin-summed |A|^2 at g = C = 1 from explicit Dirac spinors.

    Sums both mu spins and both formal nu spins (the (1 - gamma5)
    projector annihilates the wrong-helicity massless-nu term)."""
    l = p1 + p3
    D = mdot(l, l) - m_mu * m_mu
    vertex = (slash(l) + m_mu * ID4) @ slash(P) @ (ID4 - GAMMA5)
    total = 0.0
    for s1 in (0, 1):
        ub = ubar(p1, m_mu, s1)
        for s2 in (0, 1):
            v = v_spinor(p2, 0.0, s2)
            amp = ub @ vertex @ v
            total += float(np.real(amp * np.conj(amp)))
    return total / (D * D)


# ---------------------------------------------------------------------------
# matrix element, route 2: closed form from the trace recursion
# ---------------------------------------------------------------------------
def _tr4(a, b, c, d, dots):
    """Tr[slash(a) slash(b) slash(c) slash(d)] / 4."""
    return dots[a, b] * dots[c, d] - dots[a, c] * dots[b, d] \
        + dots[a, d] * dots[b, c]


def _tr6(a, b, c, d, e, f, dots):
    """Tr[slash(a)...slash(f)] / 4 by the standard recursion."""
    return (dots[a, b] * _tr4(c, d, e, f, dots)
            - dots[a, c] * _tr4(b, d, e, f, dots)
            + dots[a, d] * _tr4(b, c, e, f, dots)
            - dots[a, e] * _tr4(b, c, d, f, dots)
            + dots[a, f] * _tr4(b, c, d, e, dots))


def msq_trace(P, p1, p2, p3, m_mu, m_phi):
    """Spin-summed |A|^2 at g = C = 1 from the trace closed form.

    T = 2 { Tr[slash(p1) slash(l) slash(P) slash(p2) slash(P) slash(l)]
            + m^2 Tr[slash(P)  slash(p2) slash(P) slash(l)]
            + m^2 Tr[slash(p1) slash(P)  slash(p2) slash(P)]
            + m^2 Tr[slash(l)  slash(P)  slash(p2) slash(P)] },

    epsilon terms vanishing for three independent momenta. Divide by
    D^2 with D = 2 p1.p3 + m_phi^2."""
    l = p1 + p3
    vecs = {"p1": p1, "p2": p2, "P": P, "l": l}
    names = list(vecs)
    dots = {}
    for i in names:
        for j in names:
            dots[i, j] = mdot(vecs[i], vecs[j])
    m2 = m_mu * m_mu
    T = 2.0 * 4.0 * (
        _tr6("p1", "l", "P", "p2", "P", "l", dots)
        + m2 * _tr4("P", "p2", "P", "l", dots)
        + m2 * _tr4("p1", "P", "p2", "P", dots)
        + m2 * _tr4("l", "P", "p2", "P", dots)
    )
    D = 2.0 * mdot(p1, p3) + m_phi * m_phi
    return T / (D * D)


# ---------------------------------------------------------------------------
# kinematics: (x, cos(theta_star)) <-> Dalitz invariants
# ---------------------------------------------------------------------------
def momenta_from_x_c(mM, m_mu, m_phi, x, c):
    """Parent-rest-frame momenta (P, p1, p2, p3) at (x, cos(theta*)).

    x = 2 E_phi / mM; theta_star is the muon helicity angle in the
    (mu nu) rest frame measured from the (mu nu) direction of flight
    (i.e. from -p_phi). phi is placed along -z, the (mu nu) system
    along +z, and the muon decayed in the x-z plane (azimuth is
    physically irrelevant for a spin-0 parent)."""
    E3 = 0.5 * x * mM
    if E3 < m_phi:
        raise ValueError("x below phi threshold")
    p3mag = np.sqrt(E3 * E3 - m_phi * m_phi)
    m12sq = mM * mM + m_phi * m_phi - 2.0 * mM * E3
    if m12sq <= m_mu * m_mu:
        raise ValueError("(x, c) outside Dalitz domain")
    m12 = np.sqrt(m12sq)
    # muon in the (mu nu) rest frame
    Es = (m12sq + m_mu * m_mu) / (2.0 * m12)
    ps = (m12sq - m_mu * m_mu) / (2.0 * m12)
    # boost of the (mu nu) system in the parent frame (along +z)
    E12 = mM - E3
    gam = E12 / m12
    gb = p3mag / m12  # gamma * beta
    s = np.sqrt(max(1.0 - c * c, 0.0))
    E1 = gam * Es + gb * ps * c
    p1z = gam * ps * c + gb * Es
    p1x = ps * s
    p1 = np.array([E1, p1x, 0.0, p1z])
    p3 = np.array([E3, 0.0, 0.0, -p3mag])
    P = np.array([mM, 0.0, 0.0, 0.0])
    p2 = P - p1 - p3
    return P, p1, p2, p3


def jacobian_x_c(mM, m_mu, m_phi, x):
    """|d(m12^2, m23^2) / d(x, c)| at fixed x (c-independent).

    m12^2 = mM^2 + m_phi^2 - x mM^2  ->  |dm12^2/dx| = mM^2.
    m23^2 = mM^2 + m_mu^2 - 2 mM E1 with
    E1 = gam Es + gb ps c              ->  |dm23^2/dc| = 2 mM gb ps."""
    E3 = 0.5 * x * mM
    p3mag = np.sqrt(max(E3 * E3 - m_phi * m_phi, 0.0))
    m12sq = mM * mM + m_phi * m_phi - 2.0 * mM * E3
    m12 = np.sqrt(max(m12sq, 0.0))
    if m12 <= m_mu:
        return 0.0
    ps = (m12sq - m_mu * m_mu) / (2.0 * m12)
    gb = p3mag / m12
    return (mM * mM) * (2.0 * mM * gb * ps)


def x_domain(mM, m_mu, m_phi):
    """Physical range of x = 2 E_phi / mM."""
    x_min = 2.0 * m_phi / mM
    x_max = 1.0 + (m_phi * m_phi - m_mu * m_mu) / (mM * mM)
    return x_min, x_max


def d2gamma_dx_dc(mM, m_mu, m_phi, x, c, msq=msq_trace):
    """d^2Gamma/(dx dc) at g = C = 1 [PDG 50.22 + Jacobian]."""
    try:
        P, p1, p2, p3 = momenta_from_x_c(mM, m_mu, m_phi, x, c)
    except ValueError:
        return 0.0
    val = msq(P, p1, p2, p3, m_mu, m_phi)
    J = jacobian_x_c(mM, m_mu, m_phi, x)
    return val * J / ((2.0 * np.pi) ** 3 * 32.0 * mM ** 3)


def gamma3(mM, m_mu, m_phi, n_x=240, n_c=120, msq=msq_trace):
    """Gamma(M -> mu nu phi) at g = C = 1 by (x, c) quadrature."""
    x_lo, x_hi = x_domain(mM, m_mu, m_phi)
    xs = x_lo + (np.arange(n_x) + 0.5) * (x_hi - x_lo) / n_x
    cs = -1.0 + (np.arange(n_c) + 0.5) * 2.0 / n_c
    total = 0.0
    for x in xs:
        for c in cs:
            total += d2gamma_dx_dc(mM, m_mu, m_phi, x, c, msq=msq)
    return total * (x_hi - x_lo) / n_x * 2.0 / n_c


def sample_x(mM, m_mu, m_phi, n, rng, n_grid=400):
    """Draw x = 2 E_phi*/m_M from the exact 3-body x-marginal by inverse-CDF.

    The c integral (over the muon helicity angle) is done on a fixed grid;
    only the phi energy marginal matters for the isotropic-parent phi flux."""
    x_lo, x_hi = x_domain(mM, m_mu, m_phi)
    xs = np.linspace(x_lo + 1e-9, x_hi - 1e-9, n_grid)
    cs = np.linspace(-1.0 + 1e-9, 1.0 - 1e-9, 60)
    dens = np.array([
        np.trapezoid([d2gamma_dx_dc(mM, m_mu, m_phi, x, c) for c in cs], cs)
        for x in xs])
    cdf = np.concatenate([[0.0], np.cumsum(dens)])
    cdf /= cdf[-1]
    grid = np.concatenate([[x_lo + 1e-9], xs])
    return np.interp(rng.uniform(0.0, 1.0, n), cdf, grid)


def gamma3_dalitz(mM, m_mu, m_phi, n12=200, n23=200, msq=msq_trace):
    """Independent route: Gamma_3 via the shared PDG-50.22 integrator
    (mu = 1, nu = 2, phi = 3), validating the (x, c) Jacobian."""
    def msq_avg(p1, p2, p3):
        P = p1 + p2 + p3
        return msq(P, p1, p2, p3, m_mu, m_phi)
    return three_body_width(mM, m_mu, 0.0, m_phi, msq_avg,
                            n12=n12, n23=n23)


# ---------------------------------------------------------------------------
# model-card quantities
# ---------------------------------------------------------------------------
def coupling_constant_sq(G_F, V_ckm, f_M):
    """C^2 for a given parent, C = (G_F/sqrt(2)) |V| f_M."""
    return (G_F * V_ckm * f_M / np.sqrt(2.0)) ** 2


def kappa(mM, m_mu, m_phi, G_F, V_ckm, f_M, gamma_tot, **quad):
    """kappa_M = Br(M -> mu nu phi) at g = 1."""
    return coupling_constant_sq(G_F, V_ckm, f_M) \
        * gamma3(mM, m_mu, m_phi, **quad) / gamma_tot


def f_density(mM, m_mu, m_phi, x, c, norm=None):
    """The normalized model-card density f_M(x, c; m_phi).

    `norm` is Gamma_3 at g = C = 1 (computed once via gamma3)."""
    if norm is None:
        norm = gamma3(mM, m_mu, m_phi)
    return d2gamma_dx_dc(mM, m_mu, m_phi, x, c) / norm


def gamma_mumu(m_phi, m_mu, g=1.0):
    """Gamma(phi -> mu+ mu-) = g^2 m_phi beta^3 / (8 pi), the
    scalar-Yukawa archetype (symbolic family decay_S_to_FFbar)."""
    if m_phi <= 2.0 * m_mu:
        return 0.0
    beta = np.sqrt(1.0 - 4.0 * m_mu * m_mu / (m_phi * m_phi))
    return g * g * m_phi * beta ** 3 / (8.0 * np.pi)


# ---------------------------------------------------------------------------
# one-loop phi -> gamma gamma (the muon loop; present at ALL masses and the
# ONLY decay below 2 m_mu). The loop amplitude carries exactly one g phi mubar
# mu vertex, so Gamma_gg ∝ g^2 like Gamma_mumu -- the exact g^2 reweighting of
# the whole pipeline is preserved. Q_mu^2 = 1, N_c = 1 (muon-philic scalar).
# ---------------------------------------------------------------------------
ALPHA_EM = 1.0 / 137.035999084


def _loop_f(tau):
    """Loop function f(tau); real for tau <= 1, analytically continued above."""
    if tau <= 1.0:
        return np.arcsin(np.sqrt(tau)) ** 2
    r = np.sqrt(1.0 - 1.0 / tau)
    eta = np.log((1.0 + r) / (1.0 - r)) - 1j * np.pi
    return -0.25 * eta * eta


def a_half_scalar(tau):
    """Spin-1/2 fermion-loop form factor for a CP-even scalar:
    A(tau) = 2[tau + (tau-1) f(tau)] / tau^2, with A -> 4/3 as tau -> 0
    and A(1) = 2 at the 2 m_mu threshold (tau = m_phi^2 / 4 m_mu^2)."""
    return 2.0 * (tau + (tau - 1.0) * _loop_f(tau)) / (tau * tau)


def gamma_gammagamma(m_phi, m_mu, g=1.0):
    """Gamma(phi -> gamma gamma) [GeV] via the muon loop, at coupling g.

    Standard Higgs-portal form with the Yukawa m_f/v -> g:
        Gamma = alpha^2 g^2 m_phi^3 / (256 pi^3 m_mu^2) * |A_{1/2}(tau)|^2.
    Exactly ∝ g^2; below 2 m_mu this is the total (BR = 1)."""
    if m_phi <= 0.0:
        return 0.0
    tau = m_phi * m_phi / (4.0 * m_mu * m_mu)
    amp2 = abs(a_half_scalar(tau)) ** 2
    return (ALPHA_EM ** 2 * g * g * m_phi ** 3
            / (256.0 * np.pi ** 3 * m_mu ** 2)) * amp2


def width_ref_mumu(m_phi, m_mu):
    """g^2-stripped mu+mu- partial width (the visible dimuon channel)."""
    return gamma_mumu(m_phi, m_mu, g=1.0)


def width_ref_gammagamma(m_phi, m_mu):
    """g^2-stripped gamma gamma partial width (the only decay below 2 m_mu)."""
    return gamma_gammagamma(m_phi, m_mu, g=1.0)


def width_ref_total(m_phi, m_mu):
    """g^2-stripped TOTAL width = mu+mu- (tree) + gamma gamma (loop). This is
    the physically correct width for c*tau; above 2 m_mu the loop is a <1e-3
    correction, below 2 m_mu it is the whole width."""
    return width_ref_mumu(m_phi, m_mu) + width_ref_gammagamma(m_phi, m_mu)


def br_mumu(m_phi, m_mu):
    """BR(phi -> mu+ mu-) = Gamma_mumu / Gamma_tot (g-independent, = 0 below
    threshold, -> 1 quickly above it)."""
    tot = width_ref_total(m_phi, m_mu)
    return width_ref_mumu(m_phi, m_mu) / tot if tot > 0.0 else 0.0


def br_gammagamma(m_phi, m_mu):
    """BR(phi -> gamma gamma) = Gamma_gg / Gamma_tot (= 1 below threshold)."""
    tot = width_ref_total(m_phi, m_mu)
    return width_ref_gammagamma(m_phi, m_mu) / tot if tot > 0.0 else 0.0


def width_ref(m_phi, m_mu):
    """g^2-stripped reference width used by the c*tau reweighting convention.

    NOTE: currently the mu+mu- partial only, matching the committed v0
    ground truth. The physically correct total is `width_ref_total` (adds
    the loop gamma gamma); above threshold they differ by <1e-3, so switching
    is within the contour tolerance ladder -- see the diphoton note before
    finalizing pins."""
    return width_ref_mumu(m_phi, m_mu)


def ctau_m(m_phi, m_mu, g, total=False):
    """c*tau in meters (visible-channel width by default; total incl. loop
    if total=True -- the correct lifetime)."""
    wref = width_ref_total(m_phi, m_mu) if total else width_ref(m_phi, m_mu)
    w = g * g * wref
    if w <= 0.0:
        return np.inf
    return HBARC_M_GEV / w


def gamma_mumu_numeric(m_phi, m_mu, g=1.0):
    """Independent check of gamma_mumu via the shared two-body
    integrator with an explicit scalar-vertex spinor amplitude."""
    def msq_avg(p1, p2):
        total = 0.0
        for s1 in (0, 1):
            ub = ubar(p1, m_mu, s1)
            for s2 in (0, 1):
                v = v_spinor(p2, m_mu, s2)
                amp = ub @ v
                total += float(np.real(amp * np.conj(amp)))
        return g * g * total
    return two_body_width(m_phi, m_mu, m_mu, msq_avg)


# ---------------------------------------------------------------------------
# validation (run as a script)
# ---------------------------------------------------------------------------
def _random_boost(rng):
    """A random Lorentz boost matrix (|beta| < 0.9)."""
    n = rng.normal(size=3)
    n /= np.linalg.norm(n)
    b = n * rng.uniform(0.05, 0.9)
    b2 = float(b @ b)
    if b2 < 1e-12:
        return np.eye(4)
    gam = 1.0 / np.sqrt(1.0 - b2)
    L = np.eye(4)
    L[0, 0] = gam
    L[0, 1:] = L[1:, 0] = -gam * b
    L[1:, 1:] = np.eye(3) + (gam - 1.0) * np.outer(b, b) / b2
    return L


def validate(mM=0.493677, m_mu=0.1056584, m_phi=0.25, seed=7):
    rng = np.random.default_rng(seed)
    x_lo, x_hi = x_domain(mM, m_mu, m_phi)
    # 1. trace closed form vs explicit spinors, random Dalitz points
    worst = 0.0
    for _ in range(200):
        x = rng.uniform(x_lo + 1e-6, x_hi - 1e-6)
        c = rng.uniform(-1.0, 1.0)
        try:
            P, p1, p2, p3 = momenta_from_x_c(mM, m_mu, m_phi, x, c)
        except ValueError:
            continue
        a = msq_spinor(P, p1, p2, p3, m_mu, m_phi)
        b = msq_trace(P, p1, p2, p3, m_mu, m_phi)
        worst = max(worst, abs(a - b) / max(abs(a), 1e-300))
    assert worst < 1e-10, f"trace vs spinor mismatch: {worst}"
    # 2. frame invariance of the trace form
    P, p1, p2, p3 = momenta_from_x_c(mM, m_mu, m_phi,
                                     0.5 * (x_lo + x_hi), 0.3)
    ref = msq_trace(P, p1, p2, p3, m_mu, m_phi)
    for _ in range(20):
        L = _random_boost(rng)
        val = msq_trace(L @ P, L @ p1, L @ p2, L @ p3, m_mu, m_phi)
        assert abs(val - ref) / abs(ref) < 1e-9, "frame dependence"
    # 3. (x, c) quadrature vs independent Dalitz integrator
    g_xc = gamma3(mM, m_mu, m_phi, n_x=300, n_c=150)
    g_da = gamma3_dalitz(mM, m_mu, m_phi, n12=300, n23=300)
    assert abs(g_xc - g_da) / g_da < 2e-3, (g_xc, g_da)
    # 4. phi -> mumu closed form vs spinor numerics
    for m in (0.25, 0.5, 1.2):
        a, b = gamma_mumu(m, m_mu), gamma_mumu_numeric(m, m_mu)
        assert abs(a - b) / b < 1e-10, (m, a, b)
    return {"trace_vs_spinor": worst, "gamma3_xc": g_xc,
            "gamma3_dalitz": g_da}


if __name__ == "__main__":
    print(validate())
