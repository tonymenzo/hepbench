"""
# benchmarks/llp_forward/_shared/leptonic_contour.py -- part of HEPBench.
# Copyright (C) 2026 HEPBench authors (see AUTHORS for details).
# HEPBench is licensed under the GNU GPL v3 or later, see LICENSE for details.
"""
"""
Assemble the leptonic-exact reach contour: a generated forward parent flux
(K, D, Ds; generate_parent_flux.py) -> exact M->mu nu phi decay per parent
(parents.py) -> decay-in-volume yields over a coupling grid (pipeline.py) ->
the N_sig = N* contour in (m_phi, g).

Per-parent phi weight is g^2-stripped and carries the exact branching
kappa_M(m_phi) and the per-inelastic-collision parent weight; the yield is
N_sig(g) = N_int * g^2 * sum_i w_i * P_dec,i(g) * acc_i, summed over all
parents, so one flux + one decay sampling covers the whole coupling axis by
exact reweighting.
"""

import numpy as np

import parents as P
import propagate as PR
from pipeline import DecayVolume


def phi_flux_from_parents(flux_npz, m_phi, rng, n_x=140):
    """Decay a loaded parent flux to a combined g^2-stripped phi flux via the
    single reference assembler (subsample + stratified decay length).

    Returns dict: p4 (N,4) lab phi momenta, weight (g^2-stripped, incl.
    kappa_M), vertex (phi production points), parent (per-phi labels).
    """
    data = np.load(flux_npz, allow_pickle=True)
    flux, labs = PR.assemble_pseudoscalar(data, m_phi, rng, n_x=n_x)
    flux["parent"] = labs
    return flux


def precompute(flux, m_phi, geom, seed=1, require_two_track=True):
    """g-independent mu mu precompute -- delegates to the canonical
    propagate.precompute (vertex-aware decay-in-flight, total width + BR_mumu,
    midpoint two-track). One source of truth for the propagation physics."""
    return PR.precompute(flux, m_phi, geom, channel="mumu", seed=seed)


def yield_of_g(pc, n_int, g):
    """N_sig(g) from a precompute (exact g^2 reweight)."""
    return PR.yield_g(pc, n_int, g)


def contour_slice(flux, m_phi, geom, n_int, n_target=3.0,
                  g_lo=1e-9, g_hi=1e-1, n_scan=241, seed=1):
    """[g_low, g_high] solving N_sig = n_target, or None (peak below target)."""
    pc = PR.precompute(flux, m_phi, geom, channel="mumu", seed=seed)
    return PR.band(pc, n_int, n_target=n_target, g_lo=g_lo, g_hi=g_hi,
                   n_scan=n_scan)


def build_contour(flux_npz, grid_m, geom_spec, n_int, seed=7, n_mc_x=400):
    """Full contour over a mass grid from a generated parent flux."""
    geom = DecayVolume(geom_spec)
    rng = np.random.default_rng(seed)
    rows = []
    for m in grid_m:
        flux = phi_flux_from_parents(flux_npz, m, rng, n_x=n_mc_x)
        sl, peak = contour_slice(flux, m, geom, n_int)
        frac = {}
        if len(flux["weight"]):
            tot = flux["weight"].sum()
            for name in ("K", "D", "Ds"):
                sel = flux["parent"] == name
                frac[name] = float(flux["weight"][sel].sum() / tot) if tot else 0.0
        rows.append({"m": m, "band": sl, "peak_nsig": peak, "prod_frac": frac})
    return rows
