"""
# benchmarks/llp_forward/_shared/parents.py is a part of HEPBench.
# Copyright (C) 2026 HEPBench authors (see AUTHORS for details).
# HEPBench is licensed under the GNU GPL v3 or later, see LICENSE for details.
"""
"""
Leptonic-parent registry and the exact M -> mu nu phi production engine
sourced by an external parent-meson flux (e.g. Pythia forward K/D/Ds).

Each parent contributes the muon-philic scalar via the single tree diagram
with phi radiated off the (off-shell) muon leg -- the exact 3-body matrix
element of production.py. This module supplies, per parent:
  - the pinned SM inputs (mass, decay constant f_M, CKM factor, lifetime),
  - kappa_M(m_phi) = Br(M -> mu nu phi) at g = 1 (from the exact Gamma_3),
  - a sampler that takes lab-frame parent four-momenta and returns weighted
    lab-frame phi four-momenta with the g^2-stripped convention.

The parent flux itself is EXTERNAL (an analytic kernel or a generated file);
this module never invents it -- it only decays the parents it is given.

Parent inputs (PDG 2024): D+ and Ds+ are the charm leptonic parents (kaon is
the light-meson parent). Charge conjugates are identical and assumed included
in the supplied flux.
"""

import numpy as np

import production as prod

MMU = 0.1056584          # GeV
GF = 1.1663788e-5        # GeV^-2

# name -> (mass_gev, f_M_gev, |V_CKM|, lifetime_s)
PARENTS = {
    "pi": (0.139570, 0.1302, 0.97435, 2.6033e-8),  # f_pi, |V_ud| -- only opens
                                                   # for m_phi < m_pi - m_mu =
                                                   # 0.034 GeV (very-low-mass
                                                   # gamma gamma lobe); c*tau =
                                                   # 7.8 m so decay-in-flight
    "K":  (0.493677, 0.1557, 0.2243, 1.2380e-8),   # f_K,  |V_us|
    "D":  (1.86966,  0.2120, 0.2210, 1.0330e-12),  # f_D,  |V_cd|  (D+-)
    "Ds": (1.96835,  0.2499, 0.9750, 5.0400e-13),  # f_Ds, |V_cs|
}
HBAR_GEV_S = 6.582119569e-25
C_LIGHT_M_S = 2.99792458e8      # m/s (for the parent lab decay length beta*gamma*c*tau)


def coupling_const_sq(name):
    """C_M^2 = (G_F/sqrt(2) |V| f_M)^2 for a parent's M -> mu nu (phi) vertex."""
    _, fM, V, _ = PARENTS[name]
    return (GF / np.sqrt(2.0) * V * fM) ** 2


def gamma2_munu(name):
    """Exact 2-body Gamma(M -> mu nu) [GeV], helicity-suppressed."""
    mM, fM, V, _ = PARENTS[name]
    return (GF ** 2 * fM ** 2 * V ** 2 * mM * MMU ** 2
            * (1.0 - MMU ** 2 / mM ** 2) ** 2 / (8.0 * np.pi))


def gamma3_munuphi(name, m_phi, **quad):
    """Exact 3-body Gamma(M -> mu nu phi) [GeV] at g = 1 (C_M^2 included)."""
    mM = PARENTS[name][0]
    return coupling_const_sq(name) * prod.gamma3(mM, MMU, m_phi, **quad)


def kappa(name, m_phi, **quad):
    """kappa_M(m_phi) = Br(M -> mu nu phi) at g = 1 = Gamma_3 / Gamma_tot,M."""
    mM, fM, V, tau = PARENTS[name]
    gamma_tot = HBAR_GEV_S / tau
    return gamma3_munuphi(name, m_phi, **quad) / gamma_tot


def is_open(name, m_phi):
    """Whether M -> mu nu phi is kinematically open (m_phi < m_M - m_mu)."""
    return m_phi < PARENTS[name][0] - MMU


def decay_parents_to_phi(name, parent_p4, m_phi, rng, kappa_val=None,
                         parent_w=None, n_x=400, n_c=60, n_strata=1,
                         z_prod_m=None):
    """Decay a supplied lab-frame parent-meson flux to a weighted phi flux,
    with STRATIFIED parent-decay-length sampling.

    Parameters
    ----------
    name : parent key in PARENTS.
    parent_p4 : (N, 4) lab-frame parent four-momenta (E, px, py, pz).
    m_phi : scalar mass [GeV].
    rng : numpy Generator.
    kappa_val : Br(M -> mu nu phi) at g=1 (computed if None).
    parent_w : (N,) per-parent (per-collision) weights. If given, the returned
        per-phi weight is the FINAL g^2-stripped value parent_w * kappa /
        n_strata; if None, a uniform 1/N is used (legacy).
    n_strata : K deterministic decay-length strata per parent (see below).
    z_prod_m : if given, CONCENTRATE the strata in z < z_prod_m -- the only
        region that can contribute (see below). None (default) reproduces the
        historical full-exponential stratification exactly.

    Returns
    -------
    dict with 'p4' (N*K, 4) lab phi momenta, 'weight' (final g^2-stripped),
    'parent', and 'vertex' (N*K, 3) phi PRODUCTION points.

    Physics: each parent is replicated into K copies; copy k is given an
    INDEPENDENT phi decay (x-marginal energy + isotropic direction, boosted to
    the lab) and a DETERMINISTIC decay length at the stratum-k quantile of the
    parent's lab decay-length distribution Exp(lambda), lambda = beta*gamma
    c*tau_M: ell_k = -lambda ln(1 - (k+1/2)/K). Each stratum carries 1/K of the
    parent's decay probability, so the phi weight is parent_w * kappa / K and
    the g^2 reweighting stays exact.

    STRATUM PLACEMENT (`z_prod_m`)
    ------------------------------
    Stratifying the FULL exponential keeps the flux geometry-independent -- the
    absorber cut is applied downstream in DecayVolume.segment_from_vertex, so
    one flux serves any geometry. That is why it was the original choice, and
    it is kept as the default.

    It is, however, very wasteful and -- at finite K -- BIASED. The geometry
    accepts a phi only if its parent decayed upstream of z_prod, and for a
    forward kaon lambda = beta*gamma c*tau_K ~ 740 m against a 50 m cut, so the
    entire accepted region is the bottom ~7% of the exponential. At K = 40 just
    three strata land inside it; at K = 6 the lowest stratum (u = 0.083,
    ell = 0.087 lambda ~ 64 m) already sits PAST the cut, and the parent
    contributes nothing at all. Because the quantiles are deterministic this is
    a systematic, not Monte-Carlo noise: it does not average away over seeds.

    Passing `z_prod_m` stratifies the exponential TRUNCATED at the largest
    decay length that can still be accepted,

        ell_max = z_prod_m / d_z,     u_max = 1 - exp(-ell_max / lambda),
        ell_k   = -lambda ln(1 - u_max (k + 1/2)/K),
        weight  = parent_w * kappa * u_max / K,

    which is the same integral -- u_max is exactly the probability mass of the
    accepted region, and the K strata now sample the conditional distribution
    inside it. Every stratum is usable, so K strata here are worth ~K/u_max of
    the untruncated kind (a factor ~15 for kaons), and the resolution near
    ell_max improves too, which is what sets the upper (decay-too-soon) branch
    of the reach band. Short-lived parents (D, Ds) have u_max -> 1 and the two
    schemes coincide, as they must.

    The cost is that the flux now knows about z_prod, so it is tied to one
    geometry. Backward-going parents (d_z <= 0) can never be accepted and are
    given zero weight.
    """
    mM = PARENTS[name][0]
    p4 = np.asarray(parent_p4, dtype=float)
    N = len(p4)
    if N == 0 or not is_open(name, m_phi):
        return {"p4": np.zeros((0, 4)), "weight": np.zeros(0),
                "parent": name, "vertex": np.zeros((0, 3))}
    if kappa_val is None:
        kappa_val = kappa(name, m_phi)
    if parent_w is None:
        parent_w = np.full(N, 1.0 / N)
    K = int(n_strata)
    rep = np.repeat(np.arange(N), K)          # parent index per phi row
    p4r = p4[rep]
    pwr = np.asarray(parent_w, dtype=float)[rep]
    n = N * K

    # phi in the parent rest frame: independent per stratum
    x = prod.sample_x(mM, MMU, m_phi, n, rng, n_grid=n_x)
    estar = 0.5 * x * mM
    pstar = np.sqrt(np.maximum(estar ** 2 - m_phi ** 2, 0.0))
    cth = rng.uniform(-1.0, 1.0, n)
    sth = np.sqrt(1.0 - cth ** 2)
    az = rng.uniform(0.0, 2.0 * np.pi, n)
    kstar = pstar[:, None] * np.stack(
        [sth * np.cos(az), sth * np.sin(az), cth], axis=1)

    # boost phi from the parent rest frame to the lab (validated formula)
    E_par, pvec_par = p4r[:, 0], p4r[:, 1:]
    pdotk = np.einsum("ij,ij->i", pvec_par, kstar)
    E_lab = (estar * E_par + pdotk) / mM
    coef = pdotk / (mM * (E_par + mM)) + estar / mM
    klab = kstar + coef[:, None] * pvec_par
    phi_p4 = np.concatenate([E_lab[:, None], klab], axis=1)

    # stratified decay length: deterministic quantiles of the parent's
    # exponential, over the FULL support or (z_prod_m given) truncated to the
    # only stretch a phi can be accepted from
    p_par_mag = np.linalg.norm(pvec_par, axis=1)
    ctau_par_m = C_LIGHT_M_S * PARENTS[name][3]
    lam_par = (p_par_mag / mM) * ctau_par_m
    strat = np.tile(np.arange(K), N)          # stratum index 0..K-1 per parent
    d_par = pvec_par / np.maximum(p_par_mag, 1e-300)[:, None]
    frac = (strat + 0.5) / K

    if z_prod_m is None:
        u = frac
        u_max = 1.0
    else:
        # ell_max = z_prod / d_z is the longest parent flight that still leaves
        # the phi upstream of the absorber; u_max is its probability mass.
        # -expm1(-x) is 1-exp(-x) without the cancellation for small x, which
        # is the normal case here (u_max ~ 0.07 for kaons).
        d_z = d_par[:, 2]
        fwd = d_z > 0.0
        ell_max = np.where(fwd, float(z_prod_m) / np.where(fwd, d_z, 1.0), 0.0)
        u_max = np.where(fwd, -np.expm1(-ell_max / np.maximum(lam_par, 1e-300)),
                         0.0)
        u = u_max * frac
    ell = -lam_par * np.log1p(-u)             # -lam ln(1-u)
    vertex = ell[:, None] * d_par

    # each stratum carries u_max/K of the parent's decay probability
    w = pwr * kappa_val * u_max / K
    return {"p4": phi_p4, "weight": w, "parent": name, "vertex": vertex}
