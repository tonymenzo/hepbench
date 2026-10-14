"""Generate the leptonic ground-truth figures for the pedagogical note.
Part of HEPBench (GPL v3). Run in the hepbench env with the 1M parent flux."""
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
_SOLN = HERE
while os.path.basename(_SOLN) != "soln" and os.path.dirname(_SOLN) != _SOLN:
    _SOLN = os.path.dirname(_SOLN)
sys.path.insert(0, os.path.join(_SOLN, "code"))
import leptonic_contour as LC  # noqa: E402
import parents as P  # noqa: E402
import production as prod  # noqa: E402

FLUX = sys.argv[1] if len(sys.argv) > 1 else "/tmp/parent_flux_1M.npz"
GEOM = {"z_min_m": 112.0, "z_max_m": 163.0, "r_volume_m": 0.92,
        "z_det_m": 165.0, "r_det_m": 0.92, "z_prod_m": 50.0}
N_INT = 2.7e18
from pipeline import DecayVolume  # noqa: E402
geom = DecayVolume(GEOM)


def fig_flux_spectra():
    """Parent-meson lab energy/angle spectra from Pythia (per collision)."""
    d = np.load(FLUX, allow_pickle=True)
    fig, ax = plt.subplots(1, 2, figsize=(9.5, 3.8))
    for name, c in (("K", "C0"), ("D", "C2"), ("Ds", "C3")):
        p4 = d[f"{name}_p4"]
        w = d[f"{name}_w"]
        if len(p4) == 0:
            continue
        E = p4[:, 0]
        th = np.arccos(np.clip(p4[:, 3] / np.maximum(
            np.linalg.norm(p4[:, 1:], axis=1), 1e-300), -1, 1))
        ax[0].hist(E, bins=np.logspace(1, 4, 40), weights=w, histtype="step",
                   color=c, label=f"{name} ({w.sum():.2e}/coll)")
        ax[1].hist(th * 1e3, bins=40, weights=w, histtype="step", color=c,
                   label=name)
    ax[0].set_xscale("log")
    ax[0].set_yscale("log")
    ax[0].set_xlabel("parent lab energy $E$ [GeV]")
    ax[0].set_ylabel("d$N$/d$E$ per collision")
    ax[0].legend(fontsize=7)
    ax[0].set_title("Forward parent energy spectrum (Pythia)")
    ax[1].set_yscale("log")
    ax[1].set_xlabel(r"parent angle $\theta$ [mrad]")
    ax[1].set_ylabel("d$N$/d$\\theta$ per collision")
    ax[1].set_title("Forward angular spectrum")
    ax[1].legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "fig_flux_spectra.pdf"))
    plt.close(fig)


def fig_yield_curves():
    """N_sig(g) at three masses: the two branches and the N=3 line."""
    rng = np.random.default_rng(7)
    fig, ax = plt.subplots(figsize=(6.0, 4.3))
    gs = np.geomspace(1e-8, 1e-3, 200)
    for m, c in ((0.229, "C0"), (0.271, "C2"), (0.317, "C3")):
        flux = LC.phi_flux_from_parents(FLUX, m, rng, n_x=300)
        pc = LC.precompute(flux, m, geom, seed=7)
        ns = np.array([LC.yield_of_g(pc, N_INT, g) for g in gs])
        ax.plot(gs, ns, "-", color=c, lw=1.8, label=f"$m_\\phi={m}$ GeV")
    ax.axhline(3.0, color="0.3", ls=":", lw=1.2)
    ax.text(1.3e-8, 4, "$N_{\\rm sig}=3$", fontsize=8, color="0.3")
    g0 = 3e-7
    ax.plot([g0, 3 * g0], [0.3, 0.3 * 81], "k-", lw=0.8)
    ax.text(2.2 * g0, 0.3 * 30, "$g^4$", fontsize=9)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_ylim(1e-2, 1e5)
    ax.set_xlabel("coupling $g$")
    ax.set_ylabel("$N_{\\rm sig}$")
    ax.set_title("Yield curves (real flux): $g^4$ rise, decay-length turnover")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3, which="both")
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "fig_yield_curves.pdf"))
    plt.close(fig)


def fig_contour_and_composition():
    # start just above the dimuon threshold (2 m_mu = 0.2113 GeV) so the
    # full wedge shows: the band is widest at threshold and pinches shut at
    # the high-mass reach edge.
    grid = ([round(x, 4) for x in np.arange(0.2115, 0.286, 0.0015)]
            + [0.30, 0.32, 0.35, 0.40, 0.60])   # dense wedge + null checks
    rows = LC.build_contour(FLUX, grid, GEOM, N_INT, seed=7, n_mc_x=300)
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.3))
    m = [r["m"] for r in rows if r["band"]]
    lo = [r["band"][0] for r in rows if r["band"]]
    hi = [r["band"][1] for r in rows if r["band"]]
    ax[0].fill_between(m, lo, hi, alpha=0.25, color="C0",
                       label="excluded ($N_{\\rm sig}\\geq 3$)")
    ax[0].plot(m, lo, "o-", color="C0", label="$g_{\\rm low}$ ($g^4$ branch)")
    ax[0].plot(m, hi, "s-", color="C3",
               label="$g_{\\rm high}$ (decay-length branch)")
    ax[0].set_yscale("log")
    ax[0].set_xlabel("$m_\\phi$ [GeV]")
    ax[0].set_ylabel("coupling $g$")
    ax[0].legend(fontsize=8)
    ax[0].set_title("Leptonic-exact reach contour (real Pythia flux)")
    ax[0].grid(alpha=0.3, which="both")
    allm = [r["m"] for r in rows]
    for name, c in (("K", "C0"), ("D", "C2"), ("Ds", "C3")):
        ax[1].plot(allm, [r["prod_frac"].get(name, 0) for r in rows], "o-",
                   color=c, label=name)
    ax[1].axvline(0.388, ls=":", color="0.5")
    ax[1].text(0.392, 0.5, "K cutoff", fontsize=7, rotation=90)
    ax[1].set_xlabel("$m_\\phi$ [GeV]")
    ax[1].set_ylabel("production fraction")
    ax[1].legend(fontsize=8)
    ax[1].set_title("Production: $K\\to$ charm transition")
    ax[1].grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "fig_leptonic_contour.pdf"))
    plt.close(fig)
    return [(r["m"], r["band"], r["peak_nsig"], r["prod_frac"]) for r in rows]


if __name__ == "__main__":
    fig_flux_spectra()
    fig_yield_curves()
    rows = fig_contour_and_composition()
    print("wrote fig_flux_spectra.pdf, fig_yield_curves.pdf, "
          "fig_leptonic_contour.pdf")
    for m, b, pk, fr in rows:
        bs = f"[{b[0]:.3e},{b[1]:.3e}]" if b else "null"
        print(f"  m={m:.3f} band={bs} peakN={pk:.3g} "
              f"frac={{{','.join(f'{k}:{v:.2f}' for k,v in fr.items() if v>0.01)}}}")
