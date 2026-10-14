"""
# benchmarks/llp_forward/_shared/spectra.py is a part of HEPBench.
# Copyright (C) 2026 HEPBench authors (see AUTHORS for details).
# HEPBench is licensed under the GNU GPL v3 or later, see LICENSE for details.
"""
"""
Export the declared parent-rest-frame LLP energy spectra as pinned data
products for the `llp_forward` sandbox.

The heptapod `LLPFluxFromMesonDecay` tool consumes a spectrum table
rather than a hard-coded amplitude, so the benchmark-specific production
physics lives here, in the sandbox, as a CSV per (parent, m_phi). The
table is the x-marginal of the declared tree-level density,

    rho_M(x) = INT_{-1}^{1} d^2Gamma/(dx dc) dc          (g = C = 1),

with x = 2 E_phi / m_M. This is exactly the 1-D marginal the reference
pipeline (_shared/pipeline.sample_x) samples internally, so feeding this
table to the tool reproduces the reference flux. The pdf is written
unnormalized (the tool normalizes on load); its shape is all that
matters. One file per (parent, m_phi) where the channel is open.
"""

import os

import numpy as np

import production as prod


def x_marginal(mM, m_mu, m_phi, n_x=400, n_c=60):
    """(xs, rho) with rho(x) = INT d^2Gamma/(dx dc) dc at g = C = 1.

    Same x-grid convention as the reference sampler; the returned rho is
    unnormalized (proportional to the true density)."""
    x_lo, x_hi = prod.x_domain(mM, m_mu, m_phi)
    xs = np.linspace(x_lo + 1e-9, x_hi - 1e-9, n_x)
    cs = np.linspace(-1.0 + 1e-9, 1.0 - 1e-9, n_c)
    rho = np.array([
        np.trapezoid([prod.d2gamma_dx_dc(mM, m_mu, m_phi, x, c) for c in cs], cs)
        for x in xs])
    return xs, rho


def write_spectrum_csv(path, xs, rho, *, parent, m_phi, provenance):
    """Write a spectrum table CSV (columns x, pdf) with a provenance header."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as fh:
        fh.write(f"# Parent-rest-frame LLP energy spectrum (pinned data product).\n")
        fh.write(f"# parent = {parent}, m_phi = {m_phi:.4f} GeV\n")
        fh.write(f"# x = 2 E_phi / m_parent; pdf = INT d^2Gamma/(dx dc) dc "
                 f"(g = C = 1, unnormalized).\n")
        fh.write(f"# {provenance}\n")
        fh.write("x,pdf\n")
        for x, p in zip(xs, rho):
            fh.write(f"{x:.8e},{p:.8e}\n")


def export_grid_spectra(out_dir, *, parents, grid_m_gev, m_mu,
                        provenance, n_x=400, n_c=60):
    """Write spectrum_<parent>_m<mass>.csv for every open (parent, mass).

    A channel is open when m_phi < m_parent - m_mu. Returns the list of
    files written. Masses are taken from grid_m_gev only, so no hidden
    (off-grid) probe mass is ever exposed.
    """
    written = []
    for pname, pmass in parents.items():
        for m in grid_m_gev:
            if m >= pmass - m_mu:
                continue  # channel kinematically closed at this mass
            xs, rho = x_marginal(pmass, m_mu, m, n_x=n_x, n_c=n_c)
            fname = f"spectrum_{pname}_m{m:.3f}.csv"
            path = os.path.join(out_dir, fname)
            write_spectrum_csv(path, xs, rho, parent=pname, m_phi=m,
                               provenance=provenance)
            written.append(fname)
    return written
