"""
# benchmarks/llp_forward/_shared/propagate.py is a part of HEPBench.
# Copyright (C) 2026 HEPBench authors (see AUTHORS for details).
# HEPBench is licensed under the GNU GPL v3 or later, see LICENSE for details.
"""
"""
Canonical decay-in-volume propagation + contour core for the llp_forward
family -- the single source of truth used by every driver.

A phi flux is a dict with 'p4' (N,4) lab momenta, 'weight' (g^2-stripped, incl.
kappa), and 'vertex' (N,3) PRODUCTION points (the parent decay point; zero for
prompt parents). Given a DecayVolume geometry and a channel, `precompute`
returns the g-INDEPENDENT kept-event data (in-volume path [L1,L2] measured from
the production vertex, beta*gamma, weight, the total-width reference, and
BR_vis); `yield_g` reweights it to N_sig(g) exactly (only c*tau scales with g);
`band` root-finds the N_sig = n_target contour.

Conventions (all declared study definitions):
  - c*tau uses the TOTAL width (mu+mu- tree + gamma gamma loop); BR_vis
    partitions the visible channel ('mumu' or 'gg'), g-independent per mass.
  - The phi is produced at 'vertex' (parent decay point) and travels along its
    lab direction; the in-volume segment is the general ray-cylinder
    intersection with the ABSORBER convention (parent must decay upstream of
    z_min) -- see DecayVolume.segment_from_vertex.
  - Two-track ('mumu') / photon ('gg') acceptance is evaluated at the in-volume
    MIDPOINT, keeping the acceptance flag g-independent so one sample reweights
    the whole coupling axis.
"""

import numpy as np

import production as prod
import parents as P
from pipeline import decay_probability, two_track_pass

MMU = P.MMU

# Reference-flux defaults: subsample the abundant kaon and stratify the parent
# decay length into this many deterministic strata (see parents.py). Chosen so
# g_high (the decay-length branch) is well-converged given the z_prod gap.
KAON_CAP = 100000
N_STRATA = 40


def assemble_pseudoscalar(data, m_phi, rng, names=("pi", "K", "D", "Ds"),
                          cap=KAON_CAP, n_strata=N_STRATA, n_x=140,
                          z_prod_m=None):
    """pi/K/D/Ds -> phi flux dict (p4, weight, vertex, parent) with abundant-
    parent subsampling and STRATIFIED parent-decay-length sampling -- the single
    reference-flux assembler. Also returns a per-phi channel label array. The
    pion only opens for m_phi < m_pi - m_mu = 0.034 GeV (low-mass gamma gamma
    lobe) and is skipped gracefully for fluxes generated without it."""
    p4s, ws, vtxs, labs = [], [], [], []
    for name in names:
        if f"{name}_p4" not in data:          # flux generated without this parent
            continue
        if not P.is_open(name, m_phi) or len(data[f"{name}_p4"]) == 0:
            continue
        pp, pw = data[f"{name}_p4"], data[f"{name}_w"]
        if len(pp) > cap:
            idx = rng.choice(len(pp), cap, replace=False)
            pp, pw = pp[idx], pw[idx] * (len(data[f"{name}_p4"]) / cap)
        kap = P.kappa(name, m_phi, n_x=160, n_c=48)
        out = P.decay_parents_to_phi(name, pp, m_phi, rng, kappa_val=kap,
                                     parent_w=pw, n_x=n_x, n_strata=n_strata,
                                     z_prod_m=z_prod_m)
        p4s.append(out["p4"]); ws.append(out["weight"]); vtxs.append(out["vertex"])
        labs.append(np.full(len(out["p4"]), name, dtype=object))
    if not p4s:
        return ({"p4": np.zeros((0, 4)), "weight": np.zeros(0),
                 "vertex": np.zeros((0, 3))}, np.array([], dtype=object))
    return ({"p4": np.concatenate(p4s), "weight": np.concatenate(ws),
             "vertex": np.concatenate(vtxs)}, np.concatenate(labs))


def photon_pass(p4, vertex, geom):
    """gamma gamma acceptance: for a light, highly boosted phi the two photons
    are collinear with it, so require the phi line-of-flight from the decay
    vertex to reach the detector face within r_det."""
    pmag = np.linalg.norm(p4[:, 1:], axis=1)
    dirs = p4[:, 1:] / np.maximum(pmag, 1e-300)[:, None]
    fwd = dirs[:, 2] > 0
    dz = geom.z_det - vertex[:, 2]
    t = np.where(fwd, dz / np.where(fwd, dirs[:, 2], 1.0), np.inf)
    xy = vertex[:, :2] + t[:, None] * dirs[:, :2]
    dx = xy[:, 0] - geom.x_off          # detector plane centred off-axis
    r = np.sqrt(dx * dx + xy[:, 1] ** 2)
    return fwd & (r < geom.r_det)


def precompute(flux, m_phi, geom, channel="mumu", seed=7):
    """g-independent kept-event data for one visible channel. Returns None if
    the channel has no rate at this mass (mu mu below 2 m_mu) or no events."""
    p4, w = flux["p4"], flux["weight"]
    if len(p4) == 0:
        return None
    if channel == "mumu" and m_phi <= 2.0 * MMU:
        return None
    vtx = flux.get("vertex")
    if vtx is None:
        vtx = np.zeros((len(p4), 3))
    pmag = np.linalg.norm(p4[:, 1:], axis=1)
    u = p4[:, 1:] / np.maximum(pmag, 1e-300)[:, None]
    L1, L2, ok = geom.segment_from_vertex(vtx, u)
    bg = pmag / m_phi
    decay_vertex = vtx + (0.5 * (L1 + L2))[:, None] * u
    rng = np.random.default_rng(seed)
    if channel == "mumu":
        acc = two_track_pass(p4, decay_vertex, m_phi, MMU, geom, rng)
        br = prod.br_mumu(m_phi, MMU)
    elif channel == "gg":
        acc = photon_pass(p4, decay_vertex, geom)
        br = prod.br_gammagamma(m_phi, MMU)
    else:
        raise ValueError(f"unknown channel {channel!r}")
    keep = ok & acc
    return {"L1": L1[keep], "L2": L2[keep], "bg": bg[keep], "w": w[keep],
            "wref": prod.width_ref_total(m_phi, MMU), "br": br}


def yield_g(pc, n_int, g):
    """N_sig(g) from a precompute -- exact g^2 reweight (total-width c*tau)."""
    if pc is None or pc["br"] == 0.0:
        return 0.0
    ctau = prod.HBARC_M_GEV / (g * g * pc["wref"])
    lam = pc["bg"] * ctau
    pdec = decay_probability(pc["L1"], pc["L2"], lam)
    return n_int * g * g * pc["br"] * float(np.sum(pc["w"] * pdec))


def band(pc, n_int, n_target=3.0, g_lo=1e-9, g_hi=1.0, n_scan=321):
    """[g_low, g_high] solving N_sig = n_target, or None (peak below target).
    Returns (band_or_None, peak_nsig)."""
    if pc is None:
        return None, 0.0
    gs = np.geomspace(g_lo, g_hi, n_scan)
    ns = np.array([yield_g(pc, n_int, g) for g in gs])
    i = int(np.argmax(ns))
    if ns[i] < n_target:
        return None, float(ns[i])

    def bis(a, b, rising):
        for _ in range(60):
            mid = np.sqrt(a * b)
            if (yield_g(pc, n_int, mid) > n_target) == rising:
                b = mid
            else:
                a = mid
        return np.sqrt(a * b)

    lo = np.where(ns[:i + 1] < n_target)[0]
    hi = np.where(ns[i:] < n_target)[0]
    gl = bis(gs[lo[-1]], gs[i], True) if len(lo) else gs[0]
    gh = bis(gs[i], gs[i + hi[0]], False) if len(hi) else gs[-1]
    return (gl, gh), float(ns[i])
