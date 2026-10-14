"""All-channel reach 'staircase': pseudoscalar K/D/Ds (parents.py) + vector
J/psi, psi(2S) (production_vector.py) feed one phi flux; mu+mu- search with the
TOTAL width (incl. the loop gamma gamma) for the lifetime and BR_mumu for the
rate. Shows the production hand-off K -> Ds -> J/psi extending the mass reach
past the charm wall. Light rho/omega/phi are omitted from the contour: the
composition study shows them >100x below the leading channel everywhere.

Run in the hepbench env with the all-channel flux. Saves fig_staircase.{pdf,png}.
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
import production_vector as PV  # noqa: E402
import production as prod  # noqa: E402
from pipeline import DecayVolume  # noqa: E402
import propagate as PR  # noqa: E402

MMU = P.MMU
FLUX = sys.argv[1] if len(sys.argv) > 1 else "/tmp/parent_flux_allchan_1M.npz"
GEOM = {"z_min_m": 112.0, "z_max_m": 163.0, "r_volume_m": 0.92,
        "z_det_m": 165.0, "r_det_m": 0.92, "z_prod_m": 50.0}
N_INT = 2.7e18
PSEUDO = ("K", "D", "Ds")
VECT = ("Jpsi", "psi2S")


def combined_flux(data, m, rng):
    """One g^2-stripped phi flux (dict with p4/weight/vertex) from all dominant
    channels, plus a per-event channel label for the composition panel.
    Pseudoscalars via the reference assembler; vectors are prompt (vertex 0)."""
    flux, labs = PR.assemble_pseudoscalar(data, m, rng, names=PSEUDO)
    p4s, ws, vtxs, labl = [flux["p4"]], [flux["weight"]], [flux["vertex"]], [labs]
    for name in VECT:
        if not PV.is_open(name, m) or len(data[f"{name}_p4"]) == 0:
            continue
        kap = PV.kappa(name, m, n12=56, n23=56)
        out = PV.decay_vector_to_phi(name, data[f"{name}_p4"], m, rng,
                                     kappa_val=1.0, n_x=120)
        p4s.append(out["p4"]); ws.append(data[f"{name}_w"] * kap)
        vtxs.append(out["vertex"])
        labl.append(np.full(len(out["p4"]), name, dtype=object))
    return ({"p4": np.concatenate(p4s), "weight": np.concatenate(ws),
             "vertex": np.concatenate(vtxs)}, np.concatenate(labl))


def main():
    data = dict(np.load(FLUX, allow_pickle=True))
    geom = DecayVolume(GEOM)
    grid = [0.215, 0.230, 0.250, 0.275, 0.305, 0.340, 0.375, 0.410, 0.470,
            0.560, 0.680, 0.820, 1.00, 1.25, 1.50, 1.75, 1.95, 2.20, 2.45,
            2.70]
    rows = []
    for m in grid:
        rng = np.random.default_rng(7)
        flux, labs = combined_flux(data, m, rng)
        pc = PR.precompute(flux, m, geom, "mumu")
        b, pk = PR.band(pc, N_INT, g_hi=1e-1)
        frac = {}
        w = flux["weight"]
        tot = w.sum()
        for n in PSEUDO + VECT:
            frac[n] = float(w[labs == n].sum() / tot) if tot > 0 else 0.0
        rows.append((m, b, pk, frac))
        bs = f"[{b[0]:.2e},{b[1]:.2e}]" if b else "null"
        dom = max(frac, key=frac.get) if tot > 0 else "-"
        print(f"  m={m:5.3f} band={bs:24s} peakN={pk:.2e} dom={dom}")

    fig, ax = plt.subplots(1, 3, figsize=(15.5, 4.4))
    m = [r[0] for r in rows if r[1]]
    lo = [r[1][0] for r in rows if r[1]]
    hi = [r[1][1] for r in rows if r[1]]
    ax[0].fill_between(m, lo, hi, alpha=0.25, color="C0")
    ax[0].plot(m, lo, "o-", color="C0", ms=4, label=r"$g_{\rm low}$")
    ax[0].plot(m, hi, "s-", color="C3", ms=4, label=r"$g_{\rm high}$")
    for cut, lab in ((0.388, "K"), (1.863, r"$D_s$"), (2.886, r"J/$\psi$")):
        ax[0].axvline(cut, ls=":", color="0.6")
        ax[0].text(cut * 1.005, 2e-7, lab, rotation=90, fontsize=7, color="0.5")
    ax[0].set_xscale("log"); ax[0].set_yscale("log")
    ax[0].set_xlabel(r"$m_\phi$ [GeV]"); ax[0].set_ylabel(r"coupling $g$")
    ax[0].set_title(r"$\mu\mu$ reach band")
    ax[0].legend(fontsize=8); ax[0].grid(alpha=0.3, which="both")

    # middle: peak N_sig(m) -- WHY the band closes. The crest slides under 3.
    allm = [r[0] for r in rows]
    pks = [r[2] for r in rows]
    ax[1].plot(allm, pks, "o-", color="C0", ms=4)
    ax[1].axhline(3.0, color="C3", ls="--", lw=1.3)
    ax[1].text(allm[-6], 4.5, r"$N_{\rm sig}=3$", color="C3", fontsize=9)
    # shade the reachable region (peak >= 3)
    reach_m = [r[0] for r in rows if r[2] >= 3.0]
    if reach_m:
        ax[1].axvspan(min(reach_m), max(reach_m), color="C0", alpha=0.08)
        ax[1].text(0.5 * (min(reach_m) + max(reach_m)), 2e-9, "reach",
                   fontsize=7, ha="center", color="C0")
    for cut, lab in ((0.388, "K"), (1.863, r"$D_s$"), (2.886, r"J/$\psi$")):
        ax[1].axvline(cut, ls=":", color="0.6")
    ax[1].set_xscale("log"); ax[1].set_yscale("log")
    ax[1].set_ylim(1e-9, 1e6)
    ax[1].set_xlabel(r"$m_\phi$ [GeV]")
    ax[1].set_ylabel(r"peak $N_{\rm sig}$ (optimized over $g$)")
    ax[1].set_title(r"Why it closes: crest sinks under 3 at $\sim\!0.32$")
    ax[1].grid(alpha=0.3, which="both")

    COL = {"K": "C0", "D": "C2", "Ds": "C4", "Jpsi": "C3", "psi2S": "C1"}
    for n in PSEUDO + VECT:
        ax[2].plot(allm, [r[3].get(n, 0) for r in rows], "o-", color=COL[n],
                   ms=3, label=n)
    ax[2].set_xscale("log")
    ax[2].set_xlabel(r"$m_\phi$ [GeV]"); ax[2].set_ylabel("production fraction")
    ax[2].set_title(r"Production composition")
    ax[2].legend(fontsize=8); ax[2].grid(alpha=0.3)
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(HERE, f"fig_staircase.{ext}"), dpi=110)
    print("wrote fig_staircase.{pdf,png}")


if __name__ == "__main__":
    main()
