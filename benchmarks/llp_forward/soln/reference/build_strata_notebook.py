#!/usr/bin/env python3
"""Build the explainer notebook for the 2026-08-07 stratification fix.

Audience: someone who wants to know, in plain language and with pictures, what
was wrong with the llp_forward ground truth, how it was fixed, why the flux was
regenerated, and where everything now lives.

    python build_strata_notebook.py
    jupyter nbconvert --to notebook --execute --inplace strata_fix.ipynb
"""
from __future__ import annotations

from pathlib import Path

import nbformat as nbf

HERE = Path(__file__).resolve().parent
OUT = HERE / "strata_fix.ipynb"


def md(t):
    return nbf.v4.new_markdown_cell(t.strip("\n"))


def code(s):
    compile(s, "<cell>", "exec")          # pre-flight: never emit a broken cell
    return nbf.v4.new_code_cell(s.strip("\n"))


SETUP = r'''
import json, math, sys, time
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
import parents as PA
from pipeline import DecayVolume

GEOM_SPEC = {"z_min_m": 112.0, "z_max_m": 163.0, "r_volume_m": 0.92,
             "z_det_m": 165.0, "r_det_m": 0.92, "z_prod_m": 50.0,
             "x_off_m": 0.0}
GEOM = DecayVolume(GEOM_SPEC)
Z_PROD = GEOM_SPEC["z_prod_m"]

FLUX = np.load(HERE / "flux" / "parent_flux_a.npz", allow_pickle=True)
TRUTH_NEW = json.loads((HERE / "out" / "truth_a.json").read_text())
TRUTH_OLD = json.loads((SOLN / "truth.json").read_text())
N_INT = TRUTH_NEW["n_int"]

print(f"flux parents : K={len(FLUX['K_p4']):,}  D={len(FLUX['D_p4']):,}  "
      f"Ds={len(FLUX['Ds_p4']):,}  Jpsi={len(FLUX['Jpsi_p4']):,}  "
      f"psi2S={len(FLUX['psi2S_p4']):,}")
print(f"absorber cut : phi must be produced at z < {Z_PROD} m")
print(f"decay volume : {GEOM_SPEC['z_min_m']}-{GEOM_SPEC['z_max_m']} m")
'''

SCALES = r'''
# The numbers that make this whole problem what it is.
M_K   = PA.PARENTS["K"][0]
CTAU_K = PA.C_LIGHT_M_S * PA.PARENTS["K"][3]      # kaon proper decay length [m]

p4 = FLUX["K_p4"]
pmag = np.linalg.norm(p4[:, 1:], axis=1)
bg = pmag / M_K                                    # beta*gamma of each kaon
lam = bg * CTAU_K                                  # lab decay length [m]

theta = np.arctan2(np.hypot(p4[:, 1], p4[:, 2]), p4[:, 3])
COLL = theta < 2e-3                                # the ones aimed at the volume

print(f"kaon c*tau  {CTAU_K:.3f} m       absorber cut  {Z_PROD:.0f} m\n")
print(f"  {'population':34s} {'median bg':>10s} {'median lambda':>14s}")
print(f"  {'all forward kaons':34s} {np.median(bg):>10.1f} {np.median(lam):>12.0f} m")
print(f"  {'collimated (theta<2 mrad)':34s} {np.median(bg[COLL]):>10.1f} "
      f"{np.median(lam[COLL]):>12.0f} m")
print(f"\nthe beta*gamma spectrum is heavy-tailed -- percentiles of all kaons:")
for q in (50, 75, 90, 99):
    print(f"    {q:>2d}th   bg {np.percentile(bg, q):>8.1f}   "
          f"lambda {np.percentile(lam, q):>9.0f} m")
u_acc = -np.expm1(-Z_PROD / lam)
print(f"\nfraction of a typical kaon's decays landing before the cut: "
      f"{np.median(u_acc)*100:.1f}%")
print(f"  ... for the collimated ones: {np.median(-np.expm1(-Z_PROD/lam[COLL]))*100:.2f}%")
'''

FIG_STRATA = r'''
# WHERE THE SAMPLE POINTS LAND.
# Use the COLLIMATED kaons: they are the ones aimed at the decay volume, so they
# carry the signal, and they are the fastest -- which is exactly what makes the
# stratum placement fail for them.
lam0 = float(np.median(lam[COLL]))
x = np.linspace(0, 400, 800)
pdf = np.exp(-x / lam0) / lam0

fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.0), sharey=True)
for ax, K in zip(axes, (6, 40)):
    ax.plot(x, pdf, color="0.25", lw=1.6, zorder=3)
    ax.axvspan(0, Z_PROD, color="tab:green", alpha=0.16, lw=0,
               label=f"accepted: $z<{Z_PROD:.0f}$ m")
    frac = (np.arange(K) + 0.5) / K
    ell = -lam0 * np.log1p(-frac)
    inside = ell < Z_PROD
    ax.vlines(ell[inside], 0, np.exp(-ell[inside] / lam0) / lam0,
              color="tab:green", lw=2.0, zorder=5)
    ax.vlines(ell[~inside], 0, np.exp(-ell[~inside] / lam0) / lam0,
              color="tab:red", lw=1.4, zorder=4, alpha=0.85)
    ax.plot(ell[inside], np.exp(-ell[inside] / lam0) / lam0, "o",
            color="tab:green", ms=6, zorder=6,
            label=f"{inside.sum()} strata inside")
    ax.plot(ell[~inside], np.exp(-ell[~inside] / lam0) / lam0, "x",
            color="tab:red", ms=5, zorder=6,
            label=f"{(~inside).sum()} strata wasted")
    ax.set_xlim(0, 400); ax.set_ylim(0, pdf[0] * 1.05)
    ax.set_xlabel("parent decay length $\\ell$  [m]")
    ax.set_title(f"$K={K}$ strata over the FULL exponential")
    ax.legend(loc="upper right", fontsize=9)
axes[0].set_ylabel("probability density")
fig.suptitle("Where the sample points land vs. the region that can contribute",
             y=1.02)
fig.tight_layout()
savefig(fig, "strata_placement_full")
plt.show()

# How often the LOWEST stratum misses the window entirely, over the real
# population rather than one representative kaon.
print(f"  {'K':>4s} {'lowest stratum':>15s}   {'% of ALL kaons':>15s} "
      f"{'% of COLLIMATED':>16s}")
print(f"  {'':>4s} {'(median coll.)':>15s}   {'contributing 0':>15s} "
      f"{'contributing 0':>16s}")
for K in (1, 6, 8, 16, 40):
    e1_all = -lam * np.log1p(-0.5 / K)
    e1_col = -lam[COLL] * np.log1p(-0.5 / K)
    print(f"  {K:>4d} {-lam0*np.log1p(-0.5/K):>13.0f} m   "
          f"{(e1_all > Z_PROD).mean()*100:>14.1f}% {(e1_col > Z_PROD).mean()*100:>15.1f}%")
'''

YIELDS = r'''
# N_sig(g) at m_phi = 0.06 GeV, as a function of the stratum count.
M_PHI, CAP_NB = 0.06, 20000        # small cap: this is a demo, not the build
GS = np.logspace(-4.2, -1.2, 60)

def scan(K, z_prod=None, cap=CAP_NB):
    rng = np.random.default_rng(7)
    flux, _ = PR.assemble_pseudoscalar(FLUX, M_PHI, rng, cap=cap,
                                       n_strata=K, z_prod_m=z_prod)
    pc = PR.precompute(flux, M_PHI, GEOM, channel="gg")
    return np.array([PR.yield_g(pc, N_INT, g) for g in GS])

t0 = time.time()
CURVES = {K: scan(K) for K in (1, 6, 8, 16, 40)}
GOLD = scan(2560)                                  # converged, full exponential
print(f"computed in {time.time()-t0:.0f}s")
'''

FIG_YIELDS = r'''
fig, ax = plt.subplots(figsize=(7.2, 4.6))
ax.plot(GS, GOLD, color="k", lw=2.4, label="converged ($K=2560$)", zorder=6)
cmap = plt.cm.viridis(np.linspace(0.08, 0.85, len(CURVES)))
for (K, y), c in zip(sorted(CURVES.items()), cmap):
    ax.plot(GS, y, lw=1.7, color=c, label=f"$K={K}$")
ax.axhline(3.0, color="tab:red", ls=":", lw=1.3)
ax.text(GS[0] * 1.1, 4.2, "$N_{\\rm sig}=3$ (reach threshold)",
        color="tab:red", fontsize=9)
ax.set_xscale("log"); ax.set_yscale("log")
ax.set_ylim(1e-1, 1e10)
ax.set_xlabel("coupling $g$"); ax.set_ylabel("$N_{\\rm sig}$")
ax.set_title("Too few strata: the yield collapses, worst at strong coupling\n"
             "($\\gamma\\gamma$ search, $m_\\phi=0.06$ GeV)")
ax.legend(fontsize=9, ncol=2)
fig.tight_layout()
savefig(fig, "nsig_vs_strata")
plt.show()

print("ratio to converged, at the 4 declared couplings:")
DECL = [p["g"] for p in TRUTH_OLD["points"]
        if p["search"] == "gg" and p["m_phi"] == M_PHI]
print(f"  {'K':>5s} " + "".join(f"{g:>11.3e}" for g in DECL))
for K, y in sorted(CURVES.items()):
    r = [np.interp(g, GS, y) / np.interp(g, GS, GOLD) for g in DECL]
    print(f"  {K:>5d} " + "".join(f"{v:>11.3f}" for v in r))
'''

FIG_FIX = r'''
# THE FIX: put every stratum inside the region that can contribute.
fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.0), sharey=True)
K = 8
for ax, (zp, title) in zip(axes, [
        (None, f"BEFORE — $K={K}$ over the full exponential"),
        (Z_PROD, f"AFTER — $K={K}$ truncated at $z<{Z_PROD:.0f}$ m")]):
    xx = np.linspace(0, 300, 600)
    ax.plot(xx, np.exp(-xx / lam0) / lam0, color="0.25", lw=1.6, zorder=3)
    ax.axvspan(0, Z_PROD, color="tab:green", alpha=0.16, lw=0)
    frac = (np.arange(K) + 0.5) / K
    umax = 1.0 if zp is None else -np.expm1(-Z_PROD / lam0)
    ell = -lam0 * np.log1p(-umax * frac)
    inside = ell < Z_PROD
    ax.vlines(ell, 0, np.exp(-ell / lam0) / lam0,
              color=np.where(inside, "tab:green", "tab:red").tolist(), lw=2.0)
    ax.plot(ell[inside], np.exp(-ell[inside] / lam0) / lam0, "o",
            color="tab:green", ms=7, zorder=6)
    ax.plot(ell[~inside], np.exp(-ell[~inside] / lam0) / lam0, "x",
            color="tab:red", ms=6, zorder=6)
    ax.set_xlim(0, 300); ax.set_xlabel("parent decay length $\\ell$  [m]")
    ax.set_title(title + f"\n{inside.sum()}/{K} usable")
axes[0].set_ylabel("probability density")
fig.tight_layout()
savefig(fig, "strata_placement_fix")
plt.show()

FIXED = {K: scan(K, z_prod=Z_PROD) for K in (8, 16, 40)}
print("ratio to converged at the 4 declared couplings:\n")
print(f"  {'scheme':30s} " + "".join(f"{f'g{i+1}':>9s}" for i in range(4)))
for K, y in sorted(FIXED.items()):
    r = [np.interp(g, GS, y) / np.interp(g, GS, GOLD) for g in DECL]
    print(f"  truncated K={K:<18d} " + "".join(f"{v:>9.3f}" for v in r))
for K in (8, 40):
    r = [np.interp(g, GS, CURVES[K]) / np.interp(g, GS, GOLD) for g in DECL]
    print(f"  full-exponential K={K:<12d} " + "".join(f"{v:>9.3f}" for v in r))
'''

SIGMA = r'''
# WHY WE ALSO RE-SIMULATED: the reference's own precision, per point.
def per_point_sigma(fa, fb):
    A = {(r["search"], round(float(r["m"]), 4)): r
         for r in json.loads(Path(fa).read_text())["_per_mass"]}
    B = {(r["search"], round(float(r["m"]), 4)): r
         for r in json.loads(Path(fb).read_text())["_per_mass"]}
    out = {}
    for k in sorted(set(A) & set(B), key=lambda x: x[1]):
        pa, pb = A[k].get("peak", 0), B[k].get("peak", 0)
        if pa > 0 and pb > 0:
            out[k] = abs(math.log10(pb / pa)) / math.sqrt(2)
    return out

S200 = per_point_sigma(HERE / "out/truth_a_200k.json",
                       HERE / "out/truth_b_200k.json")
S2M = per_point_sigma(HERE / "out/truth_a.json", HERE / "out/truth_b.json")

masses = [k[1] for k in S2M]
fig, ax = plt.subplots(figsize=(7.2, 4.4))
ax.plot(masses, [S200[k] for k in S2M], "o-", color="tab:red", lw=1.8,
        label="200k-event flux")
ax.plot(masses, [S2M[k] for k in S2M], "s-", color="tab:blue", lw=1.8,
        label="2M-event flux (now)")
ax.set_yscale("log")
ax.set_xlabel("$m_\\phi$  [GeV]")
ax.set_ylabel("$\\sigma$ of the reference  [dex]")
ax.set_title("Reference precision per mass point\n"
             "(half the pair difference of two independent builds)")
ax.legend(fontsize=9)
for k in S2M:
    if k[1] in (1.9, 2.3):
        ax.annotate("only J/$\\psi$,\n$\\psi(2S)$ here", (k[1], S200[k]),
                    textcoords="offset points", xytext=(-52, -6), fontsize=8,
                    color="tab:red")
fig.tight_layout()
savefig(fig, "sigma_per_point")
plt.show()

print(f"  {'point':14s} {'sigma 200k':>11s} {'sigma 2M':>10s} {'gain':>7s}")
for k in S2M:
    g = S200[k] / S2M[k] if S2M[k] > 0 else float("nan")
    print(f"  {k[0]+'@'+str(k[1]):14s} {S200[k]:>11.4f} {S2M[k]:>10.4f} {g:>7.1f}x")
'''

FIG_BAND = r'''
# WHAT ACTUALLY CHANGED IN THE REFERENCE: the reach band.
def band_of(t):
    out = {}
    for r in t["_per_mass"]:
        if r.get("band"):
            out[round(float(r["m"]), 4)] = r["band"]
    return out

BO, BN = band_of(TRUTH_OLD), band_of(TRUTH_NEW)
ms = sorted(set(BO) & set(BN))
fig, ax = plt.subplots(figsize=(7.2, 4.8))
ax.fill_between(ms, [BO[m][0] for m in ms], [BO[m][1] for m in ms],
                color="tab:red", alpha=0.18, lw=0, label="old reference")
ax.plot(ms, [BO[m][0] for m in ms], color="tab:red", lw=1.6)
ax.plot(ms, [BO[m][1] for m in ms], color="tab:red", lw=1.6)
ax.plot(ms, [BN[m][0] for m in ms], color="tab:blue", lw=2.0, ls="--",
        label="rebuilt reference")
ax.plot(ms, [BN[m][1] for m in ms], color="tab:blue", lw=2.0, ls="--")
ax.set_yscale("log")
ax.set_xlabel("$m_\\phi$  [GeV]"); ax.set_ylabel("coupling $g$")
ax.set_title("The reach band: the LOWER edge was always right,\n"
             "the UPPER edge was cut short")
ax.legend(fontsize=9, loc="lower right")
fig.tight_layout()
savefig(fig, "band_old_vs_new")
plt.show()

print(f"  {'mass':>7s} {'g_lo dex':>10s} {'g_hi dex':>10s}")
for m in ms:
    dlo = math.log10(BN[m][0] / BO[m][0])
    dhi = math.log10(BN[m][1] / BO[m][1])
    print(f"  {m:>7.3f} {dlo:>10.4f} {dhi:>10.4f}")
'''

INVENTORY = r'''
import hashlib, subprocess
man = json.loads((HERE / "manifest.json").read_text())
print("FLUX SAMPLES (reference/flux/)")
for tag, v in sorted(man.get("flux", {}).items()):
    print(f"  parent_flux_{tag}.npz  {v['n_soft']:>9,} events  seed {v['seed']:>5}  "
          f"{v['bytes']/1e6:>6.1f} MB  sha {v['sha256'][:12]}")
print("\nTRUTH BUILDS (reference/out/)")
for p in sorted((HERE / "out").glob("*.json")):
    h = hashlib.sha256(p.read_bytes()).hexdigest()[:12]
    print(f"  {p.name:34s} {p.stat().st_size/1024:>7.1f} kB  sha {h}")
print("\nsigma (manifest)")
s = man.get("sigma", {})
print(f"  sigma_peak {s.get('sigma_peak')}   sigma_band {s.get('sigma_band')}"
      f"   from tags {s.get('tags')}")
'''


def build():
    nb = nbf.v4.new_notebook()
    nb.cells = [
        md(r"""
# What was wrong with the `llp_forward` ground truth, and how it was fixed

*2026-08-07*

**The one-sentence version.** The reference was estimating "how many kaons decay
early enough for the experiment to see the particle they produce" by checking a
handful of fixed representative distances — and those representative distances
were all placed in the wrong part of the range, so it got the answer badly wrong
at strong coupling.

Nothing about the physics was wrong. The formulas, the widths, the geometry and
the propagation code were all correct and unchanged. What was wrong was a
**sampling shortcut**, and at the settings in use it was biased — not noisy.
Re-running with a different random seed would have given the same wrong answer.

This notebook walks through it with pictures:

1. what the calculation has to do, and the two numbers that make it hard
2. where the sample points were landing (**the bug**)
3. what that did to the answer
4. the fix — put the sample points where they count
5. why we also regenerated the events, which is a *separate* issue
6. what changed in the reference
7. what is saved, where, and how to redo any of this
"""),
        code(SETUP),

        md(r"""
## 1. What the calculation has to do

The chain is: proton collisions make kaons → a kaon flies down the beamline and
**decays somewhere**, producing the hypothetical particle $\phi$ → the $\phi$
flies on and must itself decay **inside** the detector volume, 112–163 m away.

There is a hard constraint in the middle. The kaon has to decay **before 50 m** —
past that there is shielding, and its $\phi$ never counts. So the calculation
needs the fraction of kaons that decay unusually early.

Two numbers decide everything:
""" ),
        code(SCALES),

        md(r"""
Those numbers are the whole story, and note the **heavy tail**. A median forward
kaon flies ~390 m before decaying, but the $\beta\gamma$ spectrum runs far past
that — and the kaons that matter are the fast ones. A kaon only helps if it is
aimed at the decay volume, and collimated kaons are fast kaons: restricting to
$\theta<2$ mrad the median flight is **~2900 m**.

So the signal is carried by kaons that typically fly a few kilometres, of which
only those decaying within the first **50 m** can contribute — well under 2% of
them. Everything the experiment can see lives in a thin sliver at the extreme
left edge of the distribution.

## 2. The bug: where the sample points were landing

Averaging over "where did the kaon decay" could be done by rolling dice per
kaon. The code instead uses a cheaper, normally-better trick: pick $K$ fixed
representative distances, evenly spaced *by probability*, and average them.
Stratum $k$ sits at

$$\ell_k = -\lambda \ln\!\left(1 - \frac{k+\tfrac12}{K}\right)$$

The catch: those points were spread over the **entire** distribution, while only
the first few percent can ever contribute. Green = usable, red = wasted:
"""),
        code(FIG_STRATA),

        md(r"""
This is the bug, in one picture. The table under the plot is the sharper
statement, because it runs over the real kaon population rather than one
representative kaon:

- At **$K=6$** (what several agents chose), for **95%** of the collimated kaons
  even the *lowest* sample point lands past the 50 m cut. Those kaons contribute
  **exactly zero**. They are invisible to the calculation.
- At **$K=40$** (what the reference used) that still happens for **36%** of
  them, and the survivors are represented by only a point or two. It works at
  weak coupling and breaks at strong coupling.
- At **$K=1$** (the served tool's *default*) it happens for 90% of all kaons.

And because the points sit at *fixed* positions rather than random ones, this is
a **bias**, not noise. Averaging more runs does not help — you would place the
same points every time.

An everyday version: estimate how many adults are under 5 feet tall by measuring
six people at the 8th, 25th, 42nd… percentile of height. Your shortest sample is
5'2". You report zero. The true answer is small, but it is not zero.

## 3. What that did to the answer

Each curve is the predicted signal count vs. coupling strength, computed with a
different number of sample points. Black is the converged truth:
"""),
        code(YIELDS),
        code(FIG_YIELDS),

        md(r"""
Read the right-hand side of that plot. As the coupling $g$ grows the $\phi$
becomes short-lived, so it only registers if it was produced *just barely* before
the shielding — an even thinner sliver, at the **other** end of the accepted
region. That is why the curves peel away from black at strong coupling and why
too-few-strata is catastrophic exactly there.

Two consequences, and they are different:

- **The agents were wrong.** Every tooled trial in the campaign picked $K$
  between 1 and 24 (the tool's default is 1), biasing their yields low by up to
  20×. This is the low-mass $\gamma\gamma$ deficit we had been chasing.
- **The reference was also wrong**, at the highest coupling only. $K=40$ was fine
  at the peak but ~3× low at the strong-coupling end — see the $K=40$ row above.

## 4. The fix

Rather than just cranking $K$ up and burning compute on points that land in the
shielding, **put every point inside the region that can contribute**. Stratify
the exponential *truncated* at the last acceptable distance:

$$u_{\max} = 1 - e^{-\ell_{\max}/\lambda}, \qquad
\ell_k = -\lambda\ln\!\left(1 - u_{\max}\tfrac{k+1/2}{K}\right), \qquad
w = w_{\rm parent}\,\kappa\,\frac{u_{\max}}{K}$$

This is not an approximation. $u_{\max}$ is exactly the probability of landing in
the accepted region, so carrying it in the weight makes it the same integral —
the points now sample the conditional distribution inside the window. For
short-lived parents ($D$, $D_s$) $u_{\max}\to1$ and it reduces to the old scheme,
as it must.
"""),
        code(FIG_FIX),

        md(r"""
**Truncated $K=8$ beats untruncated $K=200$.** Every point now does work, so the
same compute buys ~15× the resolution — and the strong-coupling end, which was
the broken one, is resolved too.

The remaining ~1% wobble is the $\phi$ direction Monte Carlo, not the decay
length. That one *is* ordinary noise and averages away.

## 5. Why we also regenerated the events — a separate problem

Fixing the strata does nothing for a different limitation: **how many parent
particles the reference was built from.** The precision of the reference at each
mass is set by how many parents supply the $\phi$ there, and at high mass that
was very few — 378 J/$\psi$ and **32** $\psi(2S)$.

So we regenerated the Pythia flux at 2M events (10× the previous rebuild) and
rebuilt. Kaons are capped at 600k either way, so the low-mass end barely moves;
the rare parents are uncapped and grow 10×:
"""),
        code(SIGMA),

        md(r"""
Note the two changes are cleanly separable, which is what lets us describe them
independently in the manuscript:

- the **strata fix** moved the physics (upper band edge by 0.085–0.109 dex)
- the **extra events** moved almost nothing (median declared point 0.004 dex) but
  shrank the error bars a lot

## 6. What changed in the reference

The lower edge of the reach band was never affected — it lives at weak coupling,
where the old sampling was adequate. The upper edge was being cut short:
"""),
        code(FIG_BAND),

        md(r"""
## 7. What is saved, and how to redo any of this

Everything lives under `benchmarks/llp_forward/soln/reference/`, is checksummed,
and is described by `manifest.json`. This is deliberate: the *original* ground
truth was generated from `/tmp/parent_flux_allchan_2M.npz`, the OS deleted it,
and the reference became unauditable. That must not recur.
"""),
        code(INVENTORY),

        md(r"""
### Commands

```bash
# regenerate a flux sample (~28 min for 2M events)
python build_reference.py generate --tag a --seed 1000 --n-soft 2000000 --force

# rebuild truth from it (~17 min); NEVER touches the committed soln/truth.json
python build_reference.py truth --tag a

# measure sigma from two independent same-size builds
python build_reference.py sigma --tags a b

# check the strata are converged (the check that found this bug)
python check_strata_convergence.py --point gg 0.06 --strata 1 6 40 640

# compare any two builds point by point
python compare_truth.py out/truth_a_200k.json out/truth_a.json
```

### Safety property

`build_reference.py truth` snapshots the committed `soln/truth.json` and
`input.json`, lets the generator overwrite them, then puts the originals back —
now in a `finally` with `SIGTERM` handled, so it holds even if the build is
killed. Every run prints `committed soln/truth.json restored unchanged: True`.
A rebuild can never silently mutate the graded contract, which is how the
previous reference became untrustworthy.

### Files kept

| file | what it is |
|---|---|
| `flux/parent_flux_{a,b}.npz` | the 2M-event Pythia samples, seeds 1000 / 2000 |
| `out/truth_{a,b}.json` | the rebuilds — fixed strata, 2M flux |
| `out/truth_{a,b}_200k.json` | fixed strata, 200k flux (the statistics step) |
| `out/truth_{a,b}_k40untruncated.json` | the OLD scheme, kept for comparison |
| `manifest.json` | seeds, sizes, SHA-256, git SHA, wall time, sigma |
| `../../benchmarks/llp_forward/soln/notes/strata_convergence.md` | the written-up finding |

### Still open

1. **Per-point $\sigma$.** The plot in §5 shows precision varies by mass; a
   single scalar over-penalises low mass and under-penalises high mass.
2. **The credit curve.** With $\sigma_{\rm yield}$ now 0.0019 dex, every agent
   sits 50–165$\sigma$ away and `exp(-z²/2)` gives everyone exactly zero. The
   scale used to *score* has to be separated from the scale used to *test*.
3. **`n_hard = 0`.** No flux has ever used the hard-charm sample, so forward
   charm comes from the soft sample alone. Unrelated to this fix; worth a look.
"""),
    ]
    OUT.write_text(nbf.writes(nb))
    print("wrote", OUT)


if __name__ == "__main__":
    build()
