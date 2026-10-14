"""
# benchmarks/llp_forward/_shared/pipeline.py is a part of HEPBench.
# Copyright (C) 2026 HEPBench authors (see AUTHORS for details).
# HEPBench is licensed under the GNU GPL v3 or later, see LICENSE for details.
"""
"""
Reference yield pipeline for the `llp_forward` family: geometry,
decay-in-volume weighting with exact coupling reweighting, and contour
extraction. This is the ground-truth implementation; the agent-facing
heptapod `llp` tools mirror the same declared conventions.

Conventions (all declared in the model card / geometry spec):
  - The phi is produced at the primary interaction point and travels in
    a straight line at its lab angle theta; the parent flight length is
    absorbed into the kernel (decaying parents only).
  - Decay volume: on-axis cylinder, z in [z_min, z_max], radius r_vol.
    The in-volume path segment [L1, L2] is the intersection of the ray
    with the cylinder; P_dec = exp(-L1/lam) - exp(-L2/lam) with
    lam = beta*gamma*ctau and ctau = hbar c / (g^2 * width_ref).
  - Two-track acceptance is evaluated at the decay-volume MIDPOINT of
    the in-volume segment (declared convention): the phi -> mu+ mu-
    decay is sampled isotropically in the phi rest frame, both muons
    are boosted to the lab and propagated from the midpoint vertex to
    the detector plane z_det, and both must satisfy r < r_det with
    forward-going momentum. The convention makes the two-track flag
    g-independent, preserving exact per-event coupling reweighting.
  - Event weights are g^2-stripped: w_i = n_per_int * kappa_M / n_mc,
    and N_sig(g) = N_int * g^2 * sum_i w_i * P_dec,i(g) * twotrack_i.
    (One factor g^2 from production; the g^2 in the lifetime enters
    through P_dec.)
"""

import numpy as np
import yaml

from production import (
    x_domain, gamma3, d2gamma_dx_dc, width_ref, HBARC_M_GEV,
)


# ---------------------------------------------------------------------------
# geometry
# ---------------------------------------------------------------------------
class DecayVolume:
    """On-axis cylindrical decay volume + downstream detector plane."""

    def __init__(self, spec):
        g = spec["geometry"] if "geometry" in spec else spec
        self.z_min = float(g["z_min_m"])
        self.z_max = float(g["z_max_m"])
        self.r_vol = float(g["r_volume_m"])
        self.z_det = float(g["z_det_m"])
        self.r_det = float(g["r_det_m"])
        # End of the parent production region (parents decay/are swept in
        # [0, z_prod]; the gap [z_prod, z_min] is empty baseline). Defaults to
        # z_min (absorber at the fiducial face). A gap z_prod < z_min imposes a
        # minimum phi survival distance, so the upper contour branch is bounded.
        self.z_prod = float(g.get("z_prod_m", self.z_min))
        # Transverse (off-axis) displacement of the detector from the beam line:
        # the cylinder axis and the two-track/photon plane are centred on
        # (x_off, 0) at all z. Default 0 = on-axis. Off-axis sees a softer,
        # lower-rate phi flux (the forward spectrum is peaked on-axis).
        self.x_off = float(g.get("x_off_m", 0.0))

    @classmethod
    def from_yaml(cls, path):
        with open(path) as fh:
            return cls(yaml.safe_load(fh))

    def segment(self, theta):
        """In-volume path segment [L1, L2] for rays at angle theta.

        Vectorized; returns (L1, L2, ok). The ray r(z) = z tan(theta)
        must satisfy r < r_vol, capping the usable z at
        z_cap = r_vol / tan(theta)."""
        theta = np.asarray(theta, dtype=float)
        tan_t = np.tan(theta)
        cos_t = np.cos(theta)
        with np.errstate(divide="ignore"):
            z_cap = np.where(tan_t > 0.0, self.r_vol / tan_t, np.inf)
        z_hi = np.minimum(self.z_max, z_cap)
        ok = z_hi > self.z_min
        L1 = self.z_min / cos_t
        L2 = np.where(ok, z_hi / cos_t, self.z_min / cos_t)
        return L1, L2, ok

    def segment_from_vertex(self, vtx, u):
        """In-volume path segment [L1, L2] for a phi produced at `vtx` (N,3)
        travelling along unit direction `u` (N,3). General ray--cylinder
        intersection: the segment is where the ray {vtx + s u : s>0} is inside
        the radius (r < r_vol) AND in the z-window [z_min, z_max]. L1, L2 are
        path lengths measured FROM vtx (the phi decay clock starts at vtx).

        Reduces to segment(theta) when vtx = 0. A phi produced past z_max
        (parent decayed downstream) yields ok = False."""
        vtx = np.asarray(vtx, dtype=float)
        u = np.asarray(u, dtype=float)
        x0, y0, z0 = vtx[:, 0], vtx[:, 1], vtx[:, 2]
        ux, uy, uz = u[:, 0], u[:, 1], u[:, 2]
        n = len(vtx)
        # radius about the (off-axis) cylinder centre (x_off, 0): a s^2+b s+c<0
        xr = x0 - self.x_off
        a = ux * ux + uy * uy
        b = 2.0 * (xr * ux + y0 * uy)
        c = xr * xr + y0 * y0 - self.r_vol ** 2
        disc = b * b - 4.0 * a * c
        sq = np.sqrt(np.maximum(disc, 0.0))
        a_safe = np.where(a > 1e-30, a, 1e-30)
        r_lo = np.minimum((-b - sq) / (2 * a_safe), (-b + sq) / (2 * a_safe))
        r_hi = np.maximum((-b - sq) / (2 * a_safe), (-b + sq) / (2 * a_safe))
        # a ~ 0 (ray parallel to axis): radius constant, inside iff c < 0
        small = a <= 1e-30
        r_lo = np.where(small, np.where(c < 0, -np.inf, np.inf), r_lo)
        r_hi = np.where(small, np.where(c < 0, np.inf, -np.inf), r_hi)
        # no real root with a>0 (never crosses radius): quadratic sign = +
        noroot = (disc < 0) & (~small)
        r_lo = np.where(noroot, np.inf, r_lo)
        r_hi = np.where(noroot, -np.inf, r_hi)
        # z-window (forward: uz > 0)
        fwd = uz > 0
        uz_safe = np.where(fwd, uz, 1.0)
        z_lo = (self.z_min - z0) / uz_safe
        z_hi = (self.z_max - z0) / uz_safe
        s_lo = np.maximum(np.maximum(r_lo, z_lo), 0.0)
        s_hi = np.minimum(r_hi, z_hi)
        # Absorber convention: z_prod (z_shield in the write-up) is where the
        # SHIELDING BEGINS. [0, z_prod] upstream of it is the open parent decay
        # region; from z_prod onward the absorber stops everything of the
        # Standard Model, so a parent decaying inside it yields nothing that can
        # reach the detector -- hence the cut is on the phi's PRODUCTION vertex,
        # z0 < z_prod. The phi itself passes through the absorber freely. The
        # stretch [z_prod, z_min] gives it a minimum survival distance, which is
        # what bounds the upper (decay-too-soon) contour branch.
        upstream = z0 < self.z_prod
        ok = fwd & upstream & (s_hi > s_lo)
        L1 = np.where(ok, s_lo, 0.0)
        L2 = np.where(ok, s_hi, 0.0)
        return L1, L2, ok


def decay_probability(L1, L2, lam):
    """P(decay in [L1, L2]) for decay length lam (vectorized)."""
    return np.exp(-L1 / lam) - np.exp(-L2 / lam)


def two_track_pass(p4_phi, vertex, m_phi, m_mu, geom, rng):
    """g-independent two-track acceptance at the midpoint convention.

    p4_phi: (n, 4) lab four-momenta; vertex: (n, 3) decay positions.
    Samples one isotropic phi -> mu mu decay per event, boosts both
    muons to the lab, propagates straight lines to z_det, and requires
    both to hit r < r_det moving forward."""
    n = len(p4_phi)
    pstar = np.sqrt(m_phi ** 2 / 4.0 - m_mu ** 2)
    estar = m_phi / 2.0
    cth = rng.uniform(-1.0, 1.0, n)
    sth = np.sqrt(1.0 - cth ** 2)
    az = rng.uniform(0.0, 2.0 * np.pi, n)
    kstar = pstar * np.stack(
        [sth * np.cos(az), sth * np.sin(az), cth], axis=1)
    # boost to lab
    E, pvec = p4_phi[:, 0], p4_phi[:, 1:]
    ok = np.ones(n, dtype=bool)
    for sign in (+1.0, -1.0):
        k = sign * kstar
        # boost of (estar, k) from the phi rest frame to the lab:
        # k_lab = k + P [ (P.k)/(m(E+m)) + estar/m ]
        pdotk = np.einsum("ij,ij->i", pvec, k)
        coef = pdotk / (m_phi * (E + m_phi)) + estar / m_phi
        klab = k + coef[:, None] * pvec
        forward = klab[:, 2] > 0.0
        dz = geom.z_det - vertex[:, 2]
        t = np.where(forward, dz / np.where(forward, klab[:, 2], 1.0), np.inf)
        xy = vertex[:, :2] + t[:, None] * klab[:, :2]
        dx = xy[:, 0] - geom.x_off      # detector plane centred off-axis
        r = np.sqrt(dx * dx + xy[:, 1] ** 2)
        ok &= forward & (r < geom.r_det)
    return ok


# ---------------------------------------------------------------------------
# event generation from a kernel + production density
# ---------------------------------------------------------------------------
def sample_x(mM, m_mu, m_phi, n, rng, n_grid=400):
    """Draw x = 2E_phi/mM from the 1D marginal of the model-card
    density via inverse-CDF on a fine grid (c integrated; the overall
    orientation of the final state is isotropic for a spin-0 parent,
    so only the x marginal matters for the phi flux)."""
    x_lo, x_hi = x_domain(mM, m_mu, m_phi)
    xs = np.linspace(x_lo + 1e-9, x_hi - 1e-9, n_grid)
    cs = np.linspace(-1.0 + 1e-9, 1.0 - 1e-9, 60)
    dens = np.array([
        np.trapezoid([d2gamma_dx_dc(mM, m_mu, m_phi, x, c) for c in cs], cs)
        for x in xs])
    cdf = np.cumsum(dens)
    cdf = np.concatenate([[0.0], cdf]) / cdf[-1]
    grid = np.concatenate([[x_lo + 1e-9], xs])
    return np.interp(rng.uniform(0.0, 1.0, n), cdf, grid)


def simulate_channel(kernel, mM, m_mu, m_phi, kappa_M, n_mc, seed):
    """Sample g^2-stripped phi events for one parent channel.

    Returns a dict of arrays: p4 (n, 4) lab four-momenta, theta_lab,
    and per-event weight w = n_per_int * kappa_M / n_mc (per primary
    interaction, g^2-stripped)."""
    if m_phi >= mM - m_mu:
        return None
    rng = np.random.default_rng(seed)
    p_par, th_par, az_par = kernel.sample(n_mc, rng)
    e_par = np.sqrt(p_par ** 2 + kernel.parent_mass ** 2)
    # phi in the parent rest frame: energy from x, direction isotropic
    x = sample_x(mM, m_mu, m_phi, n_mc, rng)
    estar = 0.5 * x * mM
    pstar = np.sqrt(np.maximum(estar ** 2 - m_phi ** 2, 0.0))
    cth = rng.uniform(-1.0, 1.0, n_mc)
    sth = np.sqrt(1.0 - cth ** 2)
    azs = rng.uniform(0.0, 2.0 * np.pi, n_mc)
    kstar = pstar[:, None] * np.stack(
        [sth * np.cos(azs), sth * np.sin(azs), cth], axis=1)
    # parent lab momentum vector
    dir_par = np.stack([np.sin(th_par) * np.cos(az_par),
                        np.sin(th_par) * np.sin(az_par),
                        np.cos(th_par)], axis=1)
    pvec_par = p_par[:, None] * dir_par
    # boost phi from the parent rest frame to the lab:
    # k_lab = k* + P [ (P.k*)/(M(E+M)) + E*/M ]
    mMv = kernel.parent_mass
    pdotk = np.einsum("ij,ij->i", pvec_par, kstar)
    elab = (estar * e_par + pdotk) / mMv
    coef = pdotk / (mMv * (e_par + mMv)) + estar / mMv
    klab = kstar + coef[:, None] * pvec_par
    p4 = np.concatenate([elab[:, None], klab], axis=1)
    w = np.full(n_mc, kernel.n_per_int * kappa_M / n_mc)
    theta_lab = np.arccos(np.clip(klab[:, 2] / np.maximum(
        np.linalg.norm(klab, axis=1), 1e-300), -1.0, 1.0))
    return {"p4": p4, "theta": theta_lab, "w": w}


# ---------------------------------------------------------------------------
# yields and contour
# ---------------------------------------------------------------------------
def yield_curve(events, m_phi, m_mu, g_grid, geom, N_int, seed=1):
    """N_sig(g) over g_grid from g^2-stripped events (all channels
    concatenated). Exact reweighting: one event set covers the grid."""
    rng = np.random.default_rng(seed)
    p4, w = events["p4"], events["w"]
    theta = events["theta"]
    L1, L2, ok = geom.segment(theta)
    pmag = np.linalg.norm(p4[:, 1:], axis=1)
    beta_gamma = pmag / m_phi
    # midpoint vertices for the two-track convention
    Lmid = 0.5 * (L1 + L2)
    dirs = p4[:, 1:] / np.maximum(pmag, 1e-300)[:, None]
    vertex = Lmid[:, None] * dirs
    tt = two_track_pass(p4, vertex, m_phi, m_mu, geom, rng)
    keep = ok & tt
    wref = width_ref(m_phi, m_mu)
    out = np.zeros(len(g_grid))
    for i, g in enumerate(g_grid):
        ctau = HBARC_M_GEV / (g * g * wref)
        lam = beta_gamma[keep] * ctau
        pdec = decay_probability(L1[keep], L2[keep], lam)
        out[i] = N_int * g * g * np.sum(w[keep] * pdec)
    return out


def contour_slice(events, m_phi, m_mu, geom, N_int, n_target=3.0,
                  g_lo=1e-9, g_hi=1e-1, n_scan=241, seed=1):
    """[g_low, g_high] solving N_sig = n_target at fixed mass, or None.

    N_sig(g) rises as g^4 at weak coupling and is exponentially cut off
    at strong coupling, so the solution set is a closed interval
    located by a log-grid scan plus bisection on each branch."""
    gs = np.geomspace(g_lo, g_hi, n_scan)
    ns = yield_curve(events, m_phi, m_mu, gs, geom, N_int, seed=seed)
    i_pk = int(np.argmax(ns))
    if ns[i_pk] < n_target:
        return None

    def n_of(g):
        return yield_curve(events, m_phi, m_mu, np.array([g]), geom,
                           N_int, seed=seed)[0]

    def bisect(a, b, rising):
        for _ in range(60):
            mid = np.sqrt(a * b)
            if (n_of(mid) > n_target) == rising:
                b = mid
            else:
                a = mid
        return np.sqrt(a * b)

    lo_idx = np.where(ns[:i_pk + 1] < n_target)[0]
    hi_idx = np.where(ns[i_pk:] < n_target)[0]
    g_low = bisect(gs[lo_idx[-1]], gs[i_pk], rising=True) \
        if len(lo_idx) else gs[0]
    g_high = bisect(gs[i_pk], gs[i_pk + hi_idx[0]], rising=False) \
        if len(hi_idx) else gs[-1]
    return g_low, g_high
