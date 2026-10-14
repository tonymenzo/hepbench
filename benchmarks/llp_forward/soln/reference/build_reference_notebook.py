#!/usr/bin/env python3
"""Build the ground-truth reference notebook for llp_forward.

This is about the REFERENCE, not about any agent. It plots the observables the
benchmark grades against, for the two independently-generated builds produced
by `build_reference.py`, alongside the committed `soln/truth.json`:

  1. the exclusion contour (band edges in the (m_phi, g) plane)
  2. peak N_sig vs mass, against the N_sig = 3 sensitivity rule
  3. reproducibility: |dex| between builds a and b, per point -- this IS the
     measurement of sigma_ref, and it shows that a single scalar sigma is a bad
     summary because the precision is strongly mass-dependent
  4. production composition: which parent supplies the phi at each mass
  5. N_sig(g) at the declared evaluation points

Two independent same-size samples are the honest way to measure the reference's
Monte-Carlo precision: their pair difference is sqrt(2)*sigma, with no
sample-size deconvolution and no cross-pipeline contamination.

    python build_reference_notebook.py
    jupyter nbconvert --to notebook --execute --inplace reference.ipynb
"""
from __future__ import annotations

from pathlib import Path
import nbformat as nbf

HERE = Path(__file__).resolve().parent
OUT = HERE / "reference.ipynb"


def md(t):
    return nbf.v4.new_markdown_cell(t.strip("\n"))


def code(s):
    return nbf.v4.new_code_cell(s.strip("\n"))


SETUP = r'''
import json, math, sys, statistics as st
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

HERE = Path.cwd()
SOLN = HERE.parent
REPO = SOLN.parents[2]
# The house plot style lives with the analysis layer (hepbench-analysis), which
# is a separate repository: this one is the benchmark. Use it when a sibling
# checkout is present, otherwise fall back so the reference still rebuilds from
# a bare hepbench clone.
sys.path.insert(0, str(REPO.parent / "hepbench-analysis" / "lib"))
try:
    from style import STYLE, RCPARAMS, make_savefig
    plt.rcParams.update(RCPARAMS)
    savefig = make_savefig(HERE / "figures")
except ImportError:
    STYLE = dict(color_best="#0072B2", color_worst="#D55E00", color_mean="#777777",
                 band_alpha=0.18, mean_alpha=0.8, grid_alpha=0.25, grid_lw=0.6,
                 fontsize=13, dpi=300, save_pdf=True)
    def savefig(fig, name, _d=HERE / "figures"):
        _d.mkdir(parents=True, exist_ok=True)
        fig.savefig(_d / f"{name}.png", bbox_inches="tight")
        fig.savefig(_d / f"{name}.pdf", bbox_inches="tight")

BUILDS = {}
for tag in ("a", "b"):
    p = HERE / "out" / f"truth_{tag}.json"
    if p.is_file():
        BUILDS[tag] = json.loads(p.read_text())
BUILDS["committed"] = json.loads((SOLN / "truth.json").read_text())

MAN = json.loads((HERE / "manifest.json").read_text())
COL = {"a": "#0072B2", "b": "#D55E00", "committed": "0.25"}

def per_mass(t):
    return {(r["search"], round(float(r["m"]), 4)): r for r in t["_per_mass"]}

PM = {k: per_mass(v) for k, v in BUILDS.items()}
KEYS = sorted(PM["committed"], key=lambda k: (k[0], k[1]))
NTGT = float(BUILDS["committed"]["n_target"])

print("builds loaded:")
for tag, t in BUILDS.items():
    f = MAN["flux"].get(tag, {})
    src = (f"{f.get('n_soft', '?'):,} soft events, seed {f.get('seed')}, "
           f"theta_max {f.get('theta_max')}" if f else "archived reference (flux LOST: /tmp)")
    print(f"  {tag:10s} {len(t['_per_mass']):2d} mass points   {src}")
print(f"\nN_int = {BUILDS['committed']['n_int']:.3g}   N* = {NTGT}")
'''

CONTOUR = r'''
fig, ax = plt.subplots(figsize=(8.4, 6.0))
for tag, pm in PM.items():
    for ch, ls in (("gg", "-"), ("mumu", "--")):
        ks = [k for k in KEYS if k[0] == ch and pm.get(k, {}).get("band")]
        if not ks:
            continue
        ms = [k[1] for k in ks]
        lo = [pm[k]["band"][0] for k in ks]
        hi = [pm[k]["band"][1] for k in ks]
        lw = 2.6 if tag == "committed" else 1.7
        if len(ks) == 1:
            ax.plot([ms[0], ms[0]], [lo[0], hi[0]], color=COL[tag], lw=lw + 1.5,
                    alpha=0.75, solid_capstyle="butt")
            continue
        ax.plot(ms, lo, color=COL[tag], lw=lw, ls=ls, marker="o", ms=4)
        ax.plot(ms, hi, color=COL[tag], lw=lw, ls=ls, marker="o", ms=4)
        if tag == "committed":
            ax.fill_between(ms, lo, hi, color="0.55", alpha=0.20, lw=0, zorder=0)
ax.set_xscale("log"); ax.set_yscale("log")
ax.set_xlabel(r"$m_\phi$ [GeV]"); ax.set_ylabel(r"coupling $g$")
ax.grid(alpha=STYLE["grid_alpha"], lw=STYLE["grid_lw"])
h = [plt.Line2D([], [], color=COL[t], lw=2.4) for t in ("committed", "a", "b")]
ax.legend(h, ["committed truth.json", "rebuild a (seed 1000)", "rebuild b (seed 2000)"],
          frameon=False, fontsize=10.5)
ax.set_title(r"Reference exclusion contour, $N_{\rm sig}=3$", fontsize=13)
fig.tight_layout(); savefig(fig, "fig_ref_contour"); plt.show()

print("band edges, committed vs the two rebuilds:")
print(f"  {'point':14s} {'committed lo':>13s} {'a lo':>11s} {'b lo':>11s}"
      f" {'committed hi':>13s} {'a hi':>11s} {'b hi':>11s}")
for k in KEYS:
    row = [PM[t].get(k, {}).get("band") for t in ("committed", "a", "b")]
    if not row[0]:
        continue
    f = lambda b, i: (f"{b[i]:.3e}" if b else "     --")
    print(f"  {k[0]+'@'+str(k[1]):14s} {f(row[0],0):>13s} {f(row[1],0):>11s} {f(row[2],0):>11s}"
          f" {f(row[0],1):>13s} {f(row[1],1):>11s} {f(row[2],1):>11s}")
'''

PEAKS = r'''
fig, (ax, axr) = plt.subplots(2, 1, figsize=(8.6, 7.4), height_ratios=[2.2, 1.0],
                              sharex=True, gridspec_kw=dict(hspace=0.08))
for tag, pm in PM.items():
    ks = [k for k in KEYS if pm.get(k, {}).get("peak", 0) > 0]
    ms = [k[1] for k in ks]
    pk = [pm[k]["peak"] for k in ks]
    ax.plot(ms, pk, color=COL[tag], lw=2.6 if tag == "committed" else 1.7,
            marker="s" if tag == "committed" else "o", ms=5)
    if tag != "committed":
        base = [PM["committed"][k]["peak"] for k in ks]
        axr.plot(ms, [p / b for p, b in zip(pk, base)], color=COL[tag], lw=1.7,
                 marker="o", ms=4)
ax.axhline(NTGT, color="0.45", ls=":", lw=1.6)
ax.text(1.3, NTGT * 2, r"$N_{\rm sig}=3$", fontsize=10, color="0.35")
ax.set_yscale("log"); ax.set_xscale("log")
ax.set_ylabel(r"peak $N_{\rm sig}$")
ax.grid(alpha=STYLE["grid_alpha"], lw=STYLE["grid_lw"])
ax.set_title("Reference peak yield, committed vs two independent rebuilds", fontsize=12.5)
h = [plt.Line2D([], [], color=COL[t], lw=2.4) for t in ("committed", "a", "b")]
ax.legend(h, ["committed", "rebuild a", "rebuild b"], frameon=False, fontsize=10)
axr.axhline(1.0, color="0.2", lw=1.3)
axr.axhspan(0.9, 1.1, color="0.55", alpha=0.25, lw=0)
axr.set_yscale("log"); axr.set_xscale("log")
axr.set_xlabel(r"$m_\phi$ [GeV]"); axr.set_ylabel("rebuild / committed")
axr.grid(alpha=STYLE["grid_alpha"], lw=STYLE["grid_lw"])
fig.subplots_adjust(left=0.11, right=0.985, top=0.94, bottom=0.09)
savefig(fig, "fig_ref_peaks"); plt.show()
'''

SIGMA = r'''
# sigma_ref, measured: two INDEPENDENT same-size builds. Their pair difference
# is sqrt(2)*sigma. No deconvolution, no cross-pipeline contamination.
rows = []
for k in KEYS:
    A, B = PM["a"].get(k), PM["b"].get(k)
    if not (A and B):
        continue
    r = {"point": f"{k[0]}@{k[1]}", "m": k[1]}
    if A.get("peak", 0) > 0 and B.get("peak", 0) > 0:
        r["peak"] = abs(math.log10(B["peak"] / A["peak"]))
    if A.get("band") and B.get("band"):
        r["lo"] = abs(math.log10(B["band"][0] / A["band"][0]))
        r["hi"] = abs(math.log10(B["band"][1] / A["band"][1]))
    rows.append(r)

fig, ax = plt.subplots(figsize=(8.4, 5.0))
ms = [r["m"] for r in rows if "peak" in r]
ax.plot(ms, [r["peak"] / math.sqrt(2) for r in rows if "peak" in r],
        color="#0072B2", lw=1.9, marker="o", ms=5.5, label=r"peak $N_{\rm sig}$")
mb = [r["m"] for r in rows if "lo" in r]
if mb:
    ax.plot(mb, [r["lo"] / math.sqrt(2) for r in rows if "lo" in r],
            color="#D55E00", lw=1.9, marker="s", ms=5.5, label=r"band edge $g_{\rm lo}$")
    ax.plot(mb, [r["hi"] / math.sqrt(2) for r in rows if "hi" in r],
            color="#009E73", lw=1.9, ls="--", marker="^", ms=5.5,
            label=r"band edge $g_{\rm hi}$")
ax.set_xscale("log"); ax.set_yscale("log")
ax.set_xlabel(r"$m_\phi$ [GeV]"); ax.set_ylabel(r"$\sigma_{\rm ref}$ [dex]")
ax.grid(alpha=STYLE["grid_alpha"], lw=STYLE["grid_lw"])
ax.legend(frameon=False, fontsize=10.5)
ax.set_title(r"Reference Monte-Carlo precision, per point", fontsize=12.5)
fig.tight_layout(); savefig(fig, "fig_ref_sigma"); plt.show()

pk = [r["peak"] / math.sqrt(2) for r in rows if "peak" in r]
bd = [r[s] / math.sqrt(2) for r in rows for s in ("lo", "hi") if s in r]
print(f"  sigma_peak : mean {st.mean(pk):.4f}   range {min(pk):.4f}-{max(pk):.4f} dex")
print(f"  sigma_band : mean {st.mean(bd):.4f}   range {min(bd):.4f}-{max(bd):.4f} dex")
print()
print("A SINGLE SCALAR sigma IS A BAD SUMMARY. The peak precision degrades by")
print("~70x from the gamma-gamma lobe to the high-mass end, where only J/psi and")
print("psi(2S) supply the phi and the sample is thin. Any z should divide by the")
print("sigma AT THAT POINT, not by a campaign-wide mean.")
'''

COMPO = r'''
# Which parent supplies the phi at each mass -- this is what sets where the
# reference is statistically thin, and therefore where sigma is worst.
parents = ["K", "D", "Ds", "rho", "omega", "phi", "Jpsi", "psi2S"]
pal = ["#0072B2", "#009E73", "#E69F00", "#CC79A7", "#56B4E9", "#D55E00", "#F0E442", "#999999"]
fig, ax = plt.subplots(figsize=(8.6, 5.0))
ms = [k[1] for k in KEYS]
bottom = np.zeros(len(KEYS))
for name, c in zip(parents, pal):
    v = np.array([PM["committed"][k]["frac"].get(name, 0.0) for k in KEYS])
    ax.bar(range(len(KEYS)), v, bottom=bottom, color=c, label=name, width=0.82,
           edgecolor="white", linewidth=0.6)
    bottom += v
ax.set_xticks(range(len(KEYS)))
ax.set_xticklabels([f"{k[1]}\n{k[0]}" for k in KEYS], fontsize=8.5)
ax.set_xlabel(r"$m_\phi$ [GeV] / search"); ax.set_ylabel("production fraction")
ax.set_ylim(0, 1)
ax.legend(frameon=False, fontsize=9, ncol=4, loc="lower left")
ax.set_title("Which parent supplies the $\\phi$ (committed reference)", fontsize=12.5)
fig.tight_layout(); savefig(fig, "fig_ref_composition"); plt.show()
'''

POINTS = r'''
# The 48 declared (search, m_phi, g, N_sig) evaluation points -- what the rubric
# actually grades an agent against.
TP = {}
for tag, t in BUILDS.items():
    d = {}
    for p in t["points"]:
        d.setdefault((p["search"], round(float(p["m_phi"]), 4)), []).append(
            (float(p["g"]), float(p["nsig"])))
    for v in d.values():
        v.sort()
    TP[tag] = d

keys = sorted(TP["committed"], key=lambda k: (k[0], k[1]))
ncol = 4
nrow = math.ceil(len(keys) / ncol)
fig, axes = plt.subplots(nrow, ncol, figsize=(12.2, 2.7 * nrow))
axes = np.atleast_1d(axes).ravel()
for ax, k in zip(axes, keys):
    for tag in ("committed", "a", "b"):
        pts = TP[tag].get(k)
        if not pts:
            continue
        ax.plot([p[0] for p in pts], [p[1] for p in pts], color=COL[tag],
                lw=1.6 if tag != "committed" else 2.2, marker="o", ms=4.5,
                alpha=0.95 if tag == "committed" else 0.8)
    ax.axhline(NTGT, color="0.45", ls=":", lw=1.3)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_title(rf"{k[0]}  $m_\phi={k[1]}$", fontsize=9.5)
    ax.tick_params(labelsize=8)
    ax.grid(alpha=STYLE["grid_alpha"], lw=STYLE["grid_lw"])
for ax in axes[len(keys):]:
    ax.set_visible(False)
for i, ax in enumerate(axes[:len(keys)]):
    if i % ncol == 0:
        ax.set_ylabel(r"$N_{\rm sig}$", fontsize=9)
    if i >= len(keys) - ncol:
        ax.set_xlabel(r"$g$", fontsize=9)
h = [plt.Line2D([], [], color=COL[t], lw=2.2) for t in ("committed", "a", "b")]
fig.legend(h, ["committed", "rebuild a", "rebuild b"], loc="upper center", ncol=3,
           frameon=False, fontsize=10.5, bbox_to_anchor=(0.5, 1.005))
fig.suptitle("The 48 declared evaluation points", fontsize=13, y=1.035)
fig.tight_layout(rect=(0, 0, 1, 0.985))
savefig(fig, "fig_ref_points"); plt.show()
'''


def build():
    nb = nbf.v4.new_notebook()
    nb.cells = [
        md("# llp_forward — ground-truth reference\n\n"
           "The observables the benchmark grades against, for the committed\n"
           "`soln/truth.json` and for two **independently generated** rebuilds.\n\n"
           "**Why the rebuilds exist.** `derivation.py` defaulted its flux to\n"
           "`/tmp/parent_flux_allchan_2M.npz`. `/tmp` is purged by the OS, so the sample the\n"
           "committed reference was built from is gone and `truth.json` had not been\n"
           "reproducible since. Everything here is archived under `soln/reference/` with a\n"
           "checksummed manifest instead."),
        code(SETUP),
        md("## 1. The exclusion contour\n\n"
           "Only five of the twelve graded masses carry a finite reach band: the four\n"
           "$\\gamma\\gamma$ points below the dimuon threshold, and a single dimuon point\n"
           "at 0.23 GeV (drawn as a bar, since one mass cannot form a band)."),
        code(CONTOUR),
        md("## 2. Peak signal yield\n\n"
           "Defined at all twelve masses, and spanning sixteen orders of magnitude. The\n"
           "lower panel is each rebuild against the committed reference."),
        code(PEAKS),
        md("## 3. How precisely is the reference known?\n\n"
           "Two independent same-size samples through the same pipeline: their pair\n"
           "difference is $\\sqrt2\\,\\sigma$.\n\n"
           "This supersedes an earlier estimate that compared `truth.json` against\n"
           "`fine_reach_contour.json`. Those are **different pipelines** — the latter\n"
           "assembles only the pseudoscalars (K, D, D$_s$) and hardcodes\n"
           "`channel=\"mumu\"` — so their disagreement is a physics difference and cannot\n"
           "calibrate a noise floor."),
        code(SIGMA),
        md("## 4. Production composition\n\n"
           "Which parent supplies the $\\phi$. This is what makes $\\sigma$\n"
           "mass-dependent: below 0.3 GeV the kaons dominate and the sample is enormous;\n"
           "above 1 GeV only J/$\\psi$ and $\\psi(2S)$ contribute and it is thin."),
        code(COMPO),
        md("## 5. The declared evaluation points\n\n"
           "The 48 $(search, m_\\phi, g, N_{\\rm sig})$ points an agent is graded against —\n"
           "four couplings per mass, chosen to bracket the sensitive region."),
        code(POINTS),
    ]
    OUT.write_text(nbf.writes(nb))
    print("wrote", OUT)


if __name__ == "__main__":
    build()
