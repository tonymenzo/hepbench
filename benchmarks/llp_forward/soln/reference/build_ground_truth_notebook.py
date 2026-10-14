#!/usr/bin/env python3
"""Build the plain ground-truth notebook for llp_forward.

Just the physics: what the reference says about this model. The exclusion
contour, the signal yield vs coupling, where the sensitivity comes from, and
which parent supplies the phi. No agents, no grading, no error analysis --
those live in reference.ipynb (build comparison, sigma) and strata_fix.ipynb
(the 2026-08-07 sampling fix).

    python build_ground_truth_notebook.py
    jupyter nbconvert --to notebook --execute --inplace ground_truth.ipynb
"""
from __future__ import annotations

from pathlib import Path

import nbformat as nbf

HERE = Path(__file__).resolve().parent
OUT = HERE / "ground_truth.ipynb"


def md(t):
    return nbf.v4.new_markdown_cell(t.strip("\n"))


def code(s):
    compile(s, "<cell>", "exec")          # pre-flight: never emit a broken cell
    return nbf.v4.new_code_cell(s.strip("\n"))


SETUP = r'''
import json, sys, time
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

HERE = Path.cwd()
SOLN = HERE.parent
REPO = SOLN.parents[2]
# The house plot style lives with the analysis layer (hepbench-analysis), a
# separate repository: this one is the benchmark. Used when a sibling checkout
# is present, with a fallback so the reference still rebuilds from a bare clone.
sys.path.insert(0, str(REPO.parent / "hepbench-analysis" / "lib"))
sys.path.insert(0, str(SOLN / "code"))
sys.path.insert(0, str(SOLN / "depr"))
try:
    from style import RCPARAMS, make_savefig
    plt.rcParams.update(RCPARAMS)
    savefig = make_savefig(HERE / "figures")
except ImportError:
    def savefig(fig, name, _d=HERE / "figures"):
        _d.mkdir(parents=True, exist_ok=True)
        fig.savefig(_d / f"{name}.png", bbox_inches="tight")
        fig.savefig(_d / f"{name}.pdf", bbox_inches="tight")

import propagate as PR
import derivation as DV

# The rebuilt reference (fixed decay-length strata, 2M-event flux).
TRUTH = json.loads((HERE / "out" / "truth_a.json").read_text())
FLUXDATA = np.load(HERE / "flux" / "parent_flux_a.npz", allow_pickle=True)
GEOM = DV.DecayVolume(DV.GEOM)
N_INT, N_TARGET = TRUTH["n_int"], TRUTH["n_target"]
THR = 2 * DV.MMU                       # gamma gamma below, mu mu above

PER = {round(float(r["m"]), 4): r for r in TRUTH["_per_mass"]}
MASSES = sorted(PER)
BAND = {m: PER[m]["band"] for m in MASSES if PER[m].get("band")}

print(f"masses          {MASSES}")
print(f"N_int           {N_INT:.3g} proton-proton interactions")
print(f"discovery rule  N_sig >= {N_TARGET:.0f} (zero background)")
print(f"search          gamma gamma below {THR:.4f} GeV, mu mu above")
print(f"has reach       {sorted(BAND)}")
'''

MODEL = r'''
# The model, in the reference's own numbers.
print("phi -> mu mu partial width (g^2-stripped formula):")
print("   ", TRUTH["width_formula_mumu"])
print()
wp = TRUTH["width_probe"]
print(f"at the probe point m_phi={wp['m_phi']} GeV, g={wp['g']}:")
print(f"  Gamma(mu mu)        {TRUTH['width_probe_gev']:.6e} GeV")
print(f"  Gamma(gamma gamma)  {TRUTH['width_gg_probe_gev']:.6e} GeV")
ct = TRUTH["ctau_probe_m"]
ct = ct if isinstance(ct, (list, tuple)) else [ct]
print(f"  c*tau               " + ", ".join(f"{v:.6e}" for v in ct) + " m")
print(f"    (a PAIR: the rubric checks their ratio as well as their values,")
print(f"     which is what tests that g^2 scaling was applied correctly)")
print()
print("Everything scales as g^2, so the lifetime at any coupling follows from")
print("its value at g=1:  c*tau(g) = c*tau(1) / g^2.")
'''

CONTOUR = r'''
# FIGURE 1 -- the exclusion contour.
ms = sorted(BAND)
lo = [BAND[m][0] for m in ms]
hi = [BAND[m][1] for m in ms]

fig, ax = plt.subplots(figsize=(7.4, 5.0))
ax.fill_between(ms, lo, hi, color="tab:blue", alpha=0.22, lw=0,
                label="excluded ($N_{\\rm sig}\\geq3$)")
ax.plot(ms, lo, color="tab:blue", lw=2.0)
ax.plot(ms, hi, color="tab:blue", lw=2.0)

pts = TRUTH["points"]
ax.plot([p["m_phi"] for p in pts], [p["g"] for p in pts], "o", ms=3.5,
        color="k", alpha=0.55, label="declared evaluation points")

ax.axvline(THR, color="0.5", ls=":", lw=1.2)
ax.text(THR * 0.97, 3e-8, "$\\gamma\\gamma$", ha="right", fontsize=10, color="0.35")
ax.text(THR * 1.03, 3e-8, "$\\mu\\mu$", ha="left", fontsize=10, color="0.35")

ax.set_xscale("log"); ax.set_yscale("log")
ax.set_xlabel("$m_\\phi$  [GeV]"); ax.set_ylabel("coupling $g$")
ax.set_title("Ground-truth reach of the forward LLP search")
ax.legend(fontsize=9, loc="upper left")
fig.tight_layout()
savefig(fig, "gt_contour")
plt.show()

print(f"  {'m_phi':>7s} {'g_lo':>12s} {'g_hi':>12s} {'decades':>8s}")
for m in ms:
    print(f"  {m:>7.3f} {BAND[m][0]:>12.4e} {BAND[m][1]:>12.4e} "
          f"{np.log10(BAND[m][1]/BAND[m][0]):>8.2f}")
'''

FINE = r'''
# FIGURE 2 -- the same contour, scanned finely.
FC = json.loads((HERE / "out" / "fine_contour_a.json").read_text())
fine = FC["points"]
print(f"{FC['n_mass']} masses, {FC['m_min']}-{FC['m_max']} GeV, "
      f"{FC['wall_s']:.0f}s  (flux {FC['flux']}, cap {FC['cap']})")

M_PI_CLOSE = 0.13957 - DV.MMU          # pion channel shuts here

fig, ax = plt.subplots(figsize=(7.8, 5.2))
for search, colr in (("gg", "tab:blue"), ("mumu", "tab:orange")):
    seg = [p for p in fine if p["search"] == search and p["band"]]
    if not seg:
        continue
    m = np.array([p["m"] for p in seg])
    lo = np.array([p["band"][0] for p in seg])
    hi = np.array([p["band"][1] for p in seg])
    cen = np.array([bool(p.get("censored_hi")) for p in seg])
    nm = "$\\gamma\\gamma$" if search == "gg" else "$\\mu\\mu$"
    ax.fill_between(m, lo, hi, color=colr, alpha=0.24, lw=0,
                    label=f"{nm} search")
    ax.plot(m, lo, color=colr, lw=1.9)
    ax.plot(m[~cen], hi[~cen], color=colr, lw=1.9)
    if cen.any():                       # upper edge ran past the g=1 scan limit
        ax.plot(m[cen], hi[cen], color=colr, lw=1.9, ls=":")
        ax.annotate("band still open\nat $g=1$", (m[cen][0] * 1.05, 0.5),
                    fontsize=8, color=colr)

pts = TRUTH["points"]
ax.plot([p["m_phi"] for p in pts], [p["g"] for p in pts], "o", ms=3.6,
        color="k", alpha=0.6, label="graded points (12 masses)", zorder=6)

ax.axvline(THR, color="0.45", ls="--", lw=1.1)
ax.text(THR * 1.07, 1.5e-8, "$2m_\\mu$", fontsize=8, color="0.35",
        rotation=90, va="bottom")
ax.axvline(M_PI_CLOSE, color="0.45", ls="--", lw=1.1)
ax.text(M_PI_CLOSE * 0.93, 1.5e-8, "$\\pi$ shuts", fontsize=8, color="0.35",
        rotation=90, va="bottom", ha="right")

ax.set_xscale("log"); ax.set_yscale("log")
ax.set_xlim(FC["m_min"], FC["m_max"]); ax.set_ylim(1e-8, 3.0)
ax.set_xlabel("$m_\\phi$  [GeV]"); ax.set_ylabel("coupling $g$")
ax.set_title(f"Reach contour at full resolution ({FC['n_mass']} masses)")
ax.legend(fontsize=9, loc="lower left")
fig.tight_layout()
savefig(fig, "gt_contour_fine")
plt.show()

reach = [p for p in fine if p["band"]]
print(f"\n  reach ends at m_phi = {max(p['m'] for p in reach):.4f} GeV")
w = max(reach, key=lambda p: p["band"][1] / p["band"][0])
print(f"  widest band: m={w['m']:.4f}, "
      f"{np.log10(w['band'][1]/w['band'][0]):.2f} decades")
'''

SCANS = r'''
# Recompute N_sig(g) for every mass. ~27 s per mass -- the cost is the kappa
# tables, which do not depend on the sample size.
CAP_NB = 40000
GS = np.logspace(-8.5, -0.5, 90)

SCAN = {}
t0 = time.time()
for m in MASSES:
    rng = np.random.default_rng(DV.SEED)
    flux, _ = DV.assemble_all(FLUXDATA, m, rng, cap=CAP_NB)
    pc = PR.precompute(flux, m, GEOM, channel=DV.search_of(m), seed=DV.SEED)
    SCAN[m] = np.array([PR.yield_g(pc, N_INT, g) for g in GS]) if pc else np.zeros_like(GS)
    del flux, pc
print(f"done in {time.time()-t0:.0f}s")
'''

FIG_SCANS = r'''
# FIGURE 3 -- signal yield vs coupling.
fig, ax = plt.subplots(figsize=(7.6, 5.0))
cmap = plt.cm.viridis(np.linspace(0.05, 0.92, len(MASSES)))
for m, c in zip(MASSES, cmap):
    ls = "-" if m <= THR else "--"
    ax.plot(GS, np.maximum(SCAN[m], 1e-12), lw=1.7, color=c, ls=ls,
            label=f"{m:g}")
ax.axhline(N_TARGET, color="tab:red", lw=1.5, ls=":")
ax.text(GS[0] * 1.4, N_TARGET * 1.6, f"$N_{{\\rm sig}}={N_TARGET:.0f}$",
        color="tab:red", fontsize=9)
ax.set_xscale("log"); ax.set_yscale("log")
ax.set_ylim(1e-6, 1e11)
ax.set_xlabel("coupling $g$"); ax.set_ylabel("$N_{\\rm sig}$")
ax.set_title("Signal yield vs coupling\n"
             "solid: $\\gamma\\gamma$ search    dashed: $\\mu\\mu$ search")
ax.legend(fontsize=8, ncol=2, title="$m_\\phi$ [GeV]", title_fontsize=8,
          loc="upper left")
fig.tight_layout()
savefig(fig, "gt_nsig_vs_g")
plt.show()
'''

FIG_TURNOVER = r'''
# FIGURE 4 -- why each curve turns over.
m0 = 0.06
fig, ax = plt.subplots(figsize=(7.4, 4.6))
ax.plot(GS, np.maximum(SCAN[m0], 1e-12), lw=2.2, color="tab:blue")
ax.axhline(N_TARGET, color="tab:red", lw=1.4, ls=":")
b = BAND[m0]
ax.axvspan(b[0], b[1], color="tab:blue", alpha=0.13, lw=0)
for g, lab in ((b[0], "$g_{\\rm lo}$"), (b[1], "$g_{\\rm hi}$")):
    ax.axvline(g, color="tab:blue", ls="--", lw=1.2)
    ax.annotate(lab, (g, 1e8), fontsize=10, color="tab:blue",
                ha="center", backgroundcolor="white")
ax.set_xscale("log"); ax.set_yscale("log"); ax.set_ylim(1e-3, 1e11)
ax.set_xlabel("coupling $g$"); ax.set_ylabel("$N_{\\rm sig}$")
ax.set_title(f"Anatomy of one mass point ($m_\\phi={m0}$ GeV)")
ax.text(b[0] * 0.05, 1e2, "too weakly\ncoupled:\nfew produced",
        fontsize=9, color="0.3", ha="center")
ax.text(b[1] * 12, 1e2, "too strongly\ncoupled: decays\nbefore the volume",
        fontsize=9, color="0.3", ha="center")
fig.tight_layout()
savefig(fig, "gt_anatomy")
plt.show()
'''

FIG_PEAK = r'''
# FIGURE 5 -- best-case sensitivity vs mass.
peaks = [PER[m]["peak"] for m in MASSES]
fig, ax = plt.subplots(figsize=(7.2, 4.4))
colors = ["tab:blue" if m <= THR else "tab:orange" for m in MASSES]
ax.bar([str(m) for m in MASSES], np.maximum(peaks, 1e-8), color=colors,
       alpha=0.85, width=0.68)
ax.axhline(N_TARGET, color="tab:red", lw=1.5, ls=":")
ax.text(-0.4, N_TARGET * 2.2, f"$N_{{\\rm sig}}={N_TARGET:.0f}$",
        color="tab:red", fontsize=9)
ax.set_yscale("log")
ax.set_xlabel("$m_\\phi$  [GeV]")
ax.set_ylabel("peak $N_{\\rm sig}$ over all $g$")
ax.set_title("Best achievable yield at each mass\n"
             "blue: $\\gamma\\gamma$    orange: $\\mu\\mu$")
fig.tight_layout()
savefig(fig, "gt_peak")
plt.show()

print(f"  {'m_phi':>7s} {'search':>7s} {'peak N_sig':>13s}   reach?")
for m in MASSES:
    print(f"  {m:>7.3f} {PER[m]['search']:>7s} {PER[m]['peak']:>13.4e}   "
          f"{'yes' if m in BAND else 'no'}")
'''

FIG_COMPO = r'''
# FIGURE 6 -- which parent supplies the phi.
names = ["K", "D", "Ds", "Jpsi", "psi2S", "rho", "omega", "phi"]
LBL = {"K": "$K$", "D": "$D$", "Ds": "$D_s$", "Jpsi": "$J/\\psi$",
       "psi2S": "$\\psi(2S)$", "rho": "$\\rho$", "omega": "$\\omega$",
       "phi": "$\\phi$"}
frac = np.array([[PER[m]["frac"].get(n, 0.0) for m in MASSES] for n in names])
keep = frac.max(axis=1) > 0.01

fig, ax = plt.subplots(figsize=(7.4, 4.4))
ax.stackplot(range(len(MASSES)), frac[keep],
             labels=[LBL[n] for n, k in zip(names, keep) if k], alpha=0.9)
ax.set_xticks(range(len(MASSES)))
ax.set_xticklabels([f"{m:g}" for m in MASSES])
ax.set_xlim(0, len(MASSES) - 1); ax.set_ylim(0, 1)
ax.set_xlabel("$m_\\phi$  [GeV]"); ax.set_ylabel("fraction of the $\\phi$ flux")
ax.set_title("Which parent makes the $\\phi$")
ax.legend(fontsize=9, loc="center left", bbox_to_anchor=(1.01, 0.5))
fig.tight_layout()
savefig(fig, "gt_composition")
plt.show()
'''

KAPPA = r'''
# kappa(M -> mu nu phi) at g=1, on a fine mass grid.
# Pseudoscalars are ~0.4 s per point, vectors ~3 s, hence the two grids.
import parents as PA
import production_vector as PV

PS = ["pi", "K", "D", "Ds"]
VE = ["rho", "omega", "phi", "Jpsi", "psi2S"]
LBL = {"pi": "$\\pi$", "K": "$K$", "D": "$D$", "Ds": "$D_s$", "rho": "$\\rho$",
       "omega": "$\\omega$", "phi": "$\\phi$", "Jpsi": "$J/\\psi$",
       "psi2S": "$\\psi(2S)$"}

M_PS = np.logspace(np.log10(0.02), np.log10(2.6), 55)
M_VE = np.logspace(np.log10(0.02), np.log10(2.6), 16)

t0 = time.time()
KAP = {}
for n in PS:
    KAP[n] = (M_PS, np.array([PA.kappa(n, m) if PA.is_open(n, m) else 0.0
                              for m in M_PS]))
for n in VE:
    KAP[n] = (M_VE, np.array([PV.kappa(n, m) if PV.is_open(n, m) else 0.0
                              for m in M_VE]))
print(f"computed in {time.time()-t0:.0f}s")
'''

FIG_KAPPA = r'''
# FIGURE 7 -- the production branching ratios.
fig, ax = plt.subplots(figsize=(7.6, 5.0))
for n in PS:
    m, k = KAP[n]
    ok = k > 0
    ax.plot(m[ok], k[ok], lw=2.0, label=LBL[n])
for n in VE:
    m, k = KAP[n]
    ok = k > 0
    ax.plot(m[ok], k[ok], lw=1.5, ls="--", label=LBL[n])
ax.set_xscale("log"); ax.set_yscale("log")
ax.set_ylim(1e-12, 1e-1)
ax.set_xlabel("$m_\\phi$  [GeV]")
ax.set_ylabel("$\\kappa=\\mathrm{Br}(M\\to\\phi\\,X)$ at $g=1$")
ax.set_title("Production branching ratio per parent\n"
             "solid: pseudoscalar $M\\to\\mu\\nu\\phi$    "
             "dashed: vector $V\\to\\mu^+\\mu^-\\phi$")
ax.legend(fontsize=9, ncol=3, loc="lower left")
fig.tight_layout()
savefig(fig, "gt_kappa")
plt.show()

print("kinematic closing points (kappa -> 0):")
for n in PS + VE:
    m, k = KAP[n]
    op = m[k > 0]
    print(f"  {n:7s} open for m_phi <= {op.max():.3f} GeV" if len(op)
          else f"  {n:7s} closed everywhere on this grid")
'''

FIG_XSPEC = r'''
# FIGURE 8 -- the spectrum that gets integrated to give kappa.
# x = 2E*_phi/m_M is the phi energy fraction in the parent rest frame.
import production as prod
rng = np.random.default_rng(1)
fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.2))

mK = PA.PARENTS["K"][0]
for m_phi in (0.02, 0.06, 0.12, 0.18, 0.24):
    if not PA.is_open("K", m_phi):
        continue
    x = prod.sample_x(mK, PA.MMU, m_phi, 200000, rng, n_grid=400)
    axes[0].hist(x, bins=90, histtype="step", lw=1.7, density=True,
                 label=f"{m_phi:g}")
axes[0].set_xlabel("$x = 2E^*_\\phi/m_K$")
axes[0].set_ylabel("normalised $d\\Gamma/dx$")
axes[0].set_title("$K\\to\\mu\\nu\\phi$: $\\phi$ energy fraction\n"
                  "(parent rest frame)")
axes[0].legend(fontsize=8, title="$m_\\phi$ [GeV]", title_fontsize=8)

for name in ("K", "D", "Ds"):
    mM = PA.PARENTS[name][0]
    m_phi = 0.18
    if not PA.is_open(name, m_phi):
        continue
    x = prod.sample_x(mM, PA.MMU, m_phi, 200000, rng, n_grid=400)
    axes[1].hist(x, bins=90, histtype="step", lw=1.7, density=True,
                 label=LBL[name])
axes[1].set_xlabel("$x = 2E^*_\\phi/m_M$")
axes[1].set_title("$m_\\phi=0.18$ GeV: different parents")
axes[1].legend(fontsize=9)
fig.tight_layout()
savefig(fig, "gt_x_spectrum")
plt.show()

print("As m_phi approaches threshold the allowed x window pinches shut --")
print("that is what drives kappa to zero:")
for m_phi in (0.02, 0.12, 0.24, 0.34):
    if PA.is_open("K", m_phi):
        lo, hi = prod.x_domain(mK, PA.MMU, m_phi)
        print(f"  m_phi={m_phi:5.2f}  x in [{lo:.4f}, {hi:.4f}]  "
              f"width {hi-lo:.4f}   kappa={PA.kappa('K', m_phi):.3e}")
'''

FIG_YIELD_PER_PARENT = r'''
# FIGURE 9 -- kappa alone does not decide anything; abundance x kappa does.
ABUND = {}
for n in PS + VE:
    key = f"{n}_w"
    ABUND[n] = float(FLUXDATA[key].sum()) if key in FLUXDATA else 0.0

fig, axes = plt.subplots(1, 2, figsize=(11.8, 4.4))
names = [n for n in PS + VE if ABUND[n] > 0]
axes[0].bar([LBL[n] for n in names], [ABUND[n] for n in names],
            color=["tab:blue"] * len([n for n in names if n in PS])
                  + ["tab:orange"] * len([n for n in names if n in VE]))
axes[0].set_yscale("log")
axes[0].set_ylabel("parents per $pp$ collision")
axes[0].set_title("How abundant each parent is\n(forward, $\\theta<0.05$)")

for n in names:
    m, k = KAP[n]
    y = k * ABUND[n]
    ok = y > 0
    axes[1].plot(m[ok], y[ok], lw=2.0 if n in PS else 1.5,
                 ls="-" if n in PS else "--", label=LBL[n])
axes[1].set_xscale("log"); axes[1].set_yscale("log")
axes[1].set_ylim(1e-12, 1e-1)
axes[1].set_xlabel("$m_\\phi$  [GeV]")
axes[1].set_ylabel("$\\phi$ per collision at $g=1$")
axes[1].set_title("abundance $\\times\\ \\kappa$ = actual $\\phi$ production")
axes[1].legend(fontsize=8, ncol=3, loc="lower left")
fig.tight_layout()
savefig(fig, "gt_kappa_times_abundance")
plt.show()

print(f"  {'parent':8s} {'per collision':>14s} {'kappa(0.06)':>13s} {'kappa(1.9)':>12s}")
for n in names:
    m, k = KAP[n]
    k06 = np.interp(0.06, m, k)
    k19 = np.interp(1.9, m, k)
    print(f"  {n:8s} {ABUND[n]:>14.4e} {k06:>13.3e} {k19:>12.3e}")
'''

POINTS = r'''
# The 48 points an agent is graded against.
print(f"  {'search':>7s} {'m_phi':>7s} {'g':>12s} {'N_sig':>13s}")
for p in TRUTH["points"]:
    print(f"  {p['search']:>7s} {p['m_phi']:>7.3f} {p['g']:>12.4e} {p['nsig']:>13.4e}")
print(f"\n  {len(TRUTH['points'])} points total")
'''


def build():
    nb = nbf.v4.new_notebook()
    nb.cells = [
        md(r"""
# `llp_forward` — the ground truth

What the reference actually says about this model. No agents, no grading.

**The model.** A scalar $\phi$ that couples only to muons,
$\mathcal{L}\supset-\tfrac12 m_\phi^2\phi^2-g\,\phi\,\bar\mu\mu$. It is produced
in meson decays ($K\to\mu\nu\phi$ and friends), flies downstream, and decays back
to $\mu^+\mu^-$ (or to $\gamma\gamma$ through a muon loop, which is all that is
open below $2m_\mu$).

**The experiment.** A forward decay volume 112–163 m from the collision point,
behind shielding that ends at 50 m. A signal event is a $\phi$ that is produced
before the shielding, survives to the volume, and decays inside it. With zero
background, the sensitivity rule is simply $N_{\rm sig}\geq3$.

*Source: the rebuilt reference (`out/truth_a.json`) — decay-length strata
concentrated in the accepted region, 2M-event flux. See `strata_fix.ipynb`.*
"""),
        code(SETUP),
        code(MODEL),

        md(r"""
## 1. The exclusion contour

The headline result: for each mass, the range of couplings the experiment can
exclude. It is a **band**, not a threshold — bounded below *and* above.
"""),
        code(CONTOUR),

        md(r"""
That is the contour as the *graded* reference knows it — only 5 of the 12
declared masses have reach, so it is 5 points. Enough to grade an agent, far too
coarse to draw.

## 2. The contour at full resolution

The same physics through the same pipeline, on 88 masses instead of 12
(`build_fine_contour.py`, a few minutes on 8 workers). This is the picture; the
graded points are overlaid in black.

Two things only a fine scan shows:

- the scan reaches down to 0.012 GeV, below $m_\pi-m_\mu=0.034$ GeV, where the
  **pion** channel is open and feeds a low-mass lobe the declared grid (starting
  at 0.06) never samples
- the band is **discontinuous** at $2m_\mu$: below it the $\phi$ can only decay
  to $\gamma\gamma$ through a muon loop, above it $\mu^+\mu^-$ opens and the
  reach in $g$ drops by three orders of magnitude. They are different searches,
  so the two segments are drawn separately rather than joined.
"""),
        code(FINE),

        md(r"""
The dotted upper edge at the far left is **censored**, not physical: below
~0.02 GeV the $\phi$ is so long-lived that the band is still open at $g=1$,
where the scan stops.

Reach ends at $m_\phi\simeq0.267$ GeV. Above that the parents that could make a
heavy $\phi$ (charm, charmonium) are too rare in the forward direction, and the
peak yield never reaches 3 events.

## 3. Signal yield vs coupling

Recomputed from the flux. Every curve rises, peaks, and falls — that shape is
what makes the exclusion a band.
"""),
        code(SCANS),
        code(FIG_SCANS),

        md(r"""
## 4. Why the curves turn over

Both edges of the band are lifetime effects, in opposite directions:

- **Left edge** — the coupling is too weak. Production goes as $g^2$, so too few
  $\phi$ are made, and the ones that are live so long they fly straight through
  the volume without decaying.
- **Right edge** — the coupling is too strong. Now $c\tau\propto1/g^2$ is short,
  so the $\phi$ decays *before* reaching the volume. This is the edge that the
  old sampling got wrong.
"""),
        code(FIG_TURNOVER),

        md(r"""
## 5. Best-case sensitivity per mass

Peak yield over all couplings, against the 3-event rule. This is what decides
whether a mass has any reach at all.
"""),
        code(FIG_PEAK),

        md(r"""
## 6. Where the $\phi$ comes from

The composition explains the shape of everything above — and why the reference
is far more precise at low mass than at high mass.
"""),
        code(FIG_COMPO),

        md(r"""
Kaons dominate up to ~0.3 GeV, then charm ($D$, $D_s$) takes over, and past the
charm threshold only $J/\psi$ and $\psi(2S)$ remain. The forward flux has
millions of kaons but only thousands of $J/\psi$, which is why the high-mass end
is the noisy end.

## 7. $\kappa$ — the production branching ratios

$\kappa$ is the branching ratio for a parent to make a $\phi$, evaluated at
$g=1$. Because every rate scales as $g^2$, this single number carries all the
mass dependence of production; the coupling factors out.

Two families contribute, with different mechanisms:

- pseudoscalars, $M\to\mu\nu\phi$ ($\pi$, $K$, $D$, $D_s$) — three-body, the
  $\phi$ radiated off the muon leg
- vectors, $V\to\mu^+\mu^-\phi$ ($\rho$, $\omega$, $\phi$, $J/\psi$,
  $\psi(2S)$) — suppressed by an extra power of $\alpha$, but they are the only
  parents heavy enough to reach past the charm wall
"""),
        code(KAPPA),
        code(FIG_KAPPA),

        md(r"""
Each curve falls steeply and then terminates at its kinematic limit
($m_\phi \leq m_M - m_\mu$ for the pseudoscalars). That staircase of closing
thresholds is what carves the reach contour in §2: the kaon closes near
0.39 GeV, and everything above must come from charm.

### What $\kappa$ is an integral of

$\kappa$ comes from integrating a differential spectrum over the $\phi$ energy
fraction $x=2E^*_\phi/m_M$ in the parent rest frame. Watching that spectrum
makes the threshold behaviour obvious — the allowed $x$ window pinches shut.
"""),
        code(FIG_XSPEC),

        md(r"""
### Why $\kappa$ alone decides nothing

A large branching ratio is useless if the parent is never made. The physically
meaningful quantity is abundance $\times\ \kappa$, and that product is what
actually sets the composition seen in §6.
"""),
        code(FIG_YIELD_PER_PARENT),

        md(r"""
This is the whole production story in one panel. Kaons have a $\kappa$ millions
of times larger than $J/\psi$ *and* are far more abundant — but they shut off at
0.39 GeV. $J/\psi$ is rare and $\alpha$-suppressed, yet past the charm wall it
is the only thing left, which is why the high-mass reach is so thin.

## 8. The graded points

The reference declares four couplings per mass, bracketing the sensitive region.
These are what an agent's answer is compared against.
"""),
        code(POINTS),
    ]
    OUT.write_text(nbf.writes(nb))
    print("wrote", OUT)


if __name__ == "__main__":
    build()
