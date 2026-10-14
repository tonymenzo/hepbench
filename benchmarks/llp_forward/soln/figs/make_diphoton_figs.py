"""Self-consistent lobe+wedge figure for the diphoton note. BOTH channels use
the TOTAL width (mu+mu- tree + gamma gamma loop) for the lifetime and the
g-independent BR_vis partition for the rate:

  mu mu search : N = N_int g^2 BR_mumu(m) sum w P_dec(ctau_tot) A_2track
  gamma gamma  : N = N_int g^2 BR_gg(m)   sum w P_dec(ctau_tot) A_photon

Below 2 m_mu, BR_gg = 1 (the lobe); above it BR_gg collapses (~1e-4) as mu mu
opens and steals the branching, so the gamma-gamma contour dies just above
threshold and the mu mu wedge takes over. Run in the hepbench env with the 1M
parent flux. Saves fig_lobe_vs_wedge.{pdf,png} in this dir."""
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
import production as prod  # noqa: E402
import parents as P  # noqa: E402
from pipeline import DecayVolume  # noqa: E402
import propagate as PR  # noqa: E402

MMU = P.MMU
THR = 2.0 * MMU
FLUX = sys.argv[1] if len(sys.argv) > 1 else "/tmp/parent_flux_1M.npz"
GEOM = {"z_min_m": 112.0, "z_max_m": 163.0, "r_volume_m": 0.92,
        "z_det_m": 165.0, "r_det_m": 0.92, "z_prod_m": 50.0}
N_INT = 2.7e18


# ---------------------------------------------------------------------------
# flux assembly (preloaded once; phi still radiated off the muon leg for both
# channels -- only the DECAY differs, so the production flux is shared)
# ---------------------------------------------------------------------------
def phi_flux(data, m, rng):
    """Shared production flux (K/D/Ds -> phi) via the reference assembler;
    the decay channel (mumu vs gg) is applied downstream in propagate."""
    flux, _ = PR.assemble_pseudoscalar(data, m, rng)
    return flux


def main():
    data = dict(np.load(FLUX, allow_pickle=True))
    geom = DecayVolume(GEOM)
    grid = ([round(x, 4) for x in np.arange(0.015, 0.205, 0.007)]      # lobe
            + [0.208, 0.210, 0.212]                                    # cliff
            + [round(x, 4) for x in np.arange(0.213, 0.280, 0.003)])   # wedge
    rows = []
    for m in grid:
        rng = np.random.default_rng(7)
        flux = phi_flux(data, m, rng)
        gg, _ = PR.band(PR.precompute(flux, m, geom, "gg"), N_INT)
        mm, _ = PR.band(PR.precompute(flux, m, geom, "mumu"), N_INT)
        rows.append((m, gg, mm))
        print(f"  m={m:6.4f}  gg={_fmt(gg):26s}  mumu={_fmt(mm):26s}")

    fig, ax = plt.subplots(1, 2, figsize=(12, 4.6))
    _panel_contours(ax[0], rows)
    _panel_br(ax[1])
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(HERE, f"fig_lobe_vs_wedge.{ext}"), dpi=110)
    print("wrote fig_lobe_vs_wedge.{pdf,png} in", HERE)


def _fmt(b):
    return f"[{b[0]:.2e}, {b[1]:.2e}]" if b else "null"


def _panel_contours(ax, rows):
    for key, col, lab, mk in (
            (1, "C1", r"$\gamma\gamma$ search (total width, BR$_{\gamma\gamma}$)", "o"),
            (2, "C0", r"$\mu\mu$ search (total width, BR$_{\mu\mu}$)", "s")):
        m = [r[0] for r in rows if r[key]]
        lo = [r[key][0] for r in rows if r[key]]
        hi = [r[key][1] for r in rows if r[key]]
        ax.fill_between(m, lo, hi, alpha=0.25, color=col)
        ax.plot(m, lo, mk + "-", color=col, label=lab, ms=4)
        ax.plot(m, hi, mk + "-", color=col, ms=4)
    ax.axvline(THR, ls=":", color="0.4")
    ax.text(THR * 1.008, 3e-6, r"$2m_\mu$", rotation=90, fontsize=8, color="0.4")
    ax.set_yscale("log")
    ax.set_xlabel(r"$m_\phi$ [GeV]")
    ax.set_ylabel(r"coupling $g$")
    ax.set_title("Self-consistent contours: total width + BR$_{\\rm vis}$")
    ax.legend(fontsize=8, loc="lower left")
    ax.grid(alpha=0.3, which="both")


def _panel_br(ax):
    ms = np.linspace(0.02, 0.34, 500)
    ax.plot(ms, [prod.br_gammagamma(m, MMU) for m in ms], "-", color="C1",
            label=r"BR$_{\gamma\gamma}$")
    ax.plot(ms, [max(prod.br_mumu(m, MMU), 1e-12) for m in ms], "-", color="C0",
            label=r"BR$_{\mu\mu}$")
    ax.axvline(THR, ls=":", color="0.4")
    ax.set_yscale("log")
    ax.set_ylim(1e-6, 3.0)
    ax.set_xlabel(r"$m_\phi$ [GeV]")
    ax.set_ylabel("branching ratio")
    ax.set_title(r"BR partition: $\gamma\gamma\to\mu\mu$ handoff at $2m_\mu$")
    ax.legend(fontsize=9, loc="center right")
    ax.grid(alpha=0.3, which="both")


if __name__ == "__main__":
    main()
