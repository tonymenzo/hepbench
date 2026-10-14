"""Geometry scan with BOTH channels: for four pinned geometry/exposure regimes,
the same K-dominated forward flux and toolchain give qualitatively distinct
reach shapes -- now each panel shows the gamma gamma LOBE (below 2 m_mu) and the
mu mu WEDGE (above), self-consistently (total width + BR_vis). Reach is
kaon-dominated in both channels, so a K-only (subsampled) flux suffices.

Run in the hepbench env with the all-channel flux. Saves fig_geometry_scan.{pdf,png}.
"""
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
import parents as P  # noqa: E402
import production as prod  # noqa: E402
from pipeline import DecayVolume  # noqa: E402
import propagate as PR  # noqa: E402

MMU = P.MMU
THR = 2.0 * MMU
FLUX = sys.argv[1] if len(sys.argv) > 1 else "/tmp/parent_flux_allchan_1M.npz"

# name, geometry [PIN], N_int [PIN]
REGIMES = [
    ("A: balanced sliver",
     dict(z_min_m=112, z_max_m=163, r_volume_m=0.92, z_det_m=165, r_det_m=0.92,
          z_prod_m=50),
     2.7e18),
    ("B: deep tower (hi-lumi)",
     dict(z_min_m=112, z_max_m=163, r_volume_m=0.92, z_det_m=165, r_det_m=0.92,
          z_prod_m=50),
     1.0e20),
    ("C: near short-baseline",
     dict(z_min_m=32, z_max_m=83, r_volume_m=0.92, z_det_m=85, r_det_m=0.92,
          z_prod_m=15),
     2.7e18),
    ("D: far compact (FASER-like)",
     dict(z_min_m=480, z_max_m=531, r_volume_m=0.92, z_det_m=533, r_det_m=0.92,
          z_prod_m=50),
     3.0e18),
    ("E: off-axis (A + x_off=1 m)",
     dict(z_min_m=112, z_max_m=163, r_volume_m=0.92, z_det_m=165, r_det_m=0.92,
          z_prod_m=50, x_off_m=1.0),
     2.7e18),
]


def parent_flux(data, m, rng):
    """K/D/Ds phi flux via the reference assembler (subsample + stratified
    decay length). Reach is pseudoscalar-dominated; charm is kept so the
    high-luminosity regime can show its charm-driven mass extension."""
    flux, _ = PR.assemble_pseudoscalar(data, m, rng)
    return flux


def _spec_text(g, n_int):
    """Full geometry/exposure spec of one regime, for the panel corner."""
    return (f"z_prod = {g['z_prod_m']:.0f} m\n"
            f"z_min  = {g['z_min_m']:.0f} m\n"
            f"z_max  = {g['z_max_m']:.0f} m\n"
            f"r_vol  = {g['r_volume_m']:.2f} m\n"
            f"z_det  = {g['z_det_m']:.0f} m\n"
            f"r_det  = {g['r_det_m']:.2f} m\n"
            f"x_off  = {g.get('x_off_m', 0.0):.1f} m\n"
            f"N_int  = {n_int:.1e}")


def _make_fig(res, logx):
    """One 2x2 geometry-scan figure; logx=True gives the log-log version."""
    fig, axes = plt.subplots(2, 3, figsize=(15.5, 8), sharex=True, sharey=True)
    for ax, (name, gspec, n_int) in zip(axes.flat, REGIMES):
        for key, col, lab in (("gg", "C1", r"$\gamma\gamma$ lobe"),
                              ("mm", "C0", r"$\mu\mu$ wedge")):
            pts = [(m, b) for m, b in res[name][key] if b]
            if pts:
                mm = [p[0] for p in pts]
                lo = [p[1][0] for p in pts]
                hi = [p[1][1] for p in pts]
                ax.fill_between(mm, lo, hi, alpha=0.25, color=col)
                ax.plot(mm, lo, "o-", color=col, ms=3, label=lab)
                ax.plot(mm, hi, "o-", color=col, ms=3)
        ax.axvline(THR, ls=":", color="0.4")
        ax.set_yscale("log")
        if logx:
            ax.set_xscale("log")
        ax.set_title(name, fontsize=10, loc="left")
        ax.text(0.975, 0.965, _spec_text(gspec, n_int), transform=ax.transAxes,
                ha="right", va="top", fontsize=6.5, family="monospace",
                bbox=dict(boxstyle="round,pad=0.35", fc="white", alpha=0.78,
                          ec="0.7"))
        ax.grid(alpha=0.3, which="both")
        ax.legend(fontsize=7, loc="lower left" if logx else "lower right")
    for ax in axes.flat[len(REGIMES):]:      # hide unused panels (2x3 vs 5)
        ax.axis("off")
    fig.supxlabel(r"$m_\phi$ [GeV]")
    fig.supylabel(r"coupling $g$")
    fig.suptitle("Geometry scan, both channels: one flux + one toolchain, "
                 "five reach morphologies" + (" (log-log)" if logx else ""),
                 fontsize=11)
    fig.tight_layout()
    suffix = "_loglog" if logx else ""
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(HERE, f"fig_geometry_scan{suffix}.{ext}"), dpi=110)
    plt.close(fig)
    print(f"wrote fig_geometry_scan{suffix}.{{pdf,png}}")


def main():
    import pickle
    cache = os.path.join(HERE, "fig_geometry_scan_res.pkl")
    if os.path.exists(cache):
        with open(cache, "rb") as fh:
            res = pickle.load(fh)
        print(f"loaded cached contours from {cache} (delete to recompute)")
    else:
        data = dict(np.load(FLUX, allow_pickle=True))
        grid = [0.015, 0.020, 0.025, 0.030, 0.040, 0.050, 0.065, 0.080, 0.10,
                0.12, 0.14, 0.16, 0.18, 0.20, 0.213, 0.220, 0.230, 0.245,
                0.260, 0.28, 0.30, 0.33, 0.36, 0.40, 0.44, 0.48]
        res = {name: {"gg": [], "mm": []} for name, _, _ in REGIMES}
        for m in grid:
            rng = np.random.default_rng(7)
            flux = parent_flux(data, m, rng)
            for name, gspec, n_int in REGIMES:
                geom = DecayVolume(gspec)
                gg, _ = PR.band(PR.precompute(flux, m, geom, "gg"), n_int)
                mm, _ = PR.band(PR.precompute(flux, m, geom, "mumu"), n_int)
                res[name]["gg"].append((m, gg))
                res[name]["mm"].append((m, mm))
            print(f"m={m:5.3f} " + " | ".join(
                f"{name[0]}:gg={_b(res[name]['gg'][-1][1])},mm={_b(res[name]['mm'][-1][1])}"
                for name, _, _ in REGIMES))
        with open(cache, "wb") as fh:
            pickle.dump(res, fh)

    _make_fig(res, logx=False)
    _make_fig(res, logx=True)

    # summary table (for the note)
    print("\nregime  gg_lobe_glow  gg_lobe_ghigh  mm_glow  mm_ghigh  mm_massmax")
    for name, _, _ in REGIMES:
        gg = [b for _, b in res[name]["gg"] if b]
        mm = [(m, b) for m, b in res[name]["mm"] if b]
        gglo = min(b[0] for b in gg) if gg else None
        gghi = max(b[1] for b in gg) if gg else None
        mmlo = min(b[1][0] for b in mm) if mm else None
        mmhi = max(b[1][1] for b in mm) if mm else None
        mmax = max(m for m, _ in mm) if mm else None
        print(f"  {name[0]}  {_e(gglo)}  {_e(gghi)}  {_e(mmlo)}  {_e(mmhi)}  "
              f"{mmax}")


def _b(b):
    return f"[{b[0]:.1e},{b[1]:.1e}]" if b else "null"


def _e(x):
    return f"{x:.2e}" if x is not None else "--"


if __name__ == "__main__":
    main()
