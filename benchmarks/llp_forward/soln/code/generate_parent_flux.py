"""
# benchmarks/llp_forward/_shared/generate_parent_flux.py -- part of HEPBench.
# Copyright (C) 2026 HEPBench authors (see AUTHORS for details).
# HEPBench is licensed under the GNU GPL v3 or later, see LICENSE for details.
"""
"""
Ground-truth forward parent-meson flux generator (K+-, D+-, Ds+-) for the
llp_forward family, via Pythia 8 (pythia8mc). Config adapted from Hostert
et al. tauALP (arXiv:2507.15271), taus -> muon parents.

Soft and hard-charm samples are generated separately and stitched at a
pTHat cut (keep soft pTHat < cut, hard pTHat > cut), so the light-meson
(soft) and forward-charm (hard ccbar) regions are each covered without
double counting. Each harvested parent carries a per-primary-interaction
weight w = sigmaGen / (N_gen * sigma_inel), so summed weights give the
mean number of that parent per inelastic pp collision.

The parents are made stable (mayDecay off) so their production momenta are
harvested directly; the exact M -> mu nu phi decay is applied downstream
(parents.py). Output: an npz with per-parent lab four-momenta and weights,
plus provenance.
"""

import argparse
import os
import time

import numpy as np

# Pseudoscalar leptonic parents (M -> mu nu phi) and vector parents
# (V -> mu+ mu- phi). Vectors are made stable and harvested at production too;
# the light rho/omega are as abundant as kaons but their mu+mu- branching is
# alpha^2-suppressed, so they are negligible -- J/psi is the vector channel
# that matters (it carries the high-mass reach past the charm wall).
PARENT_IDS = {
    211: "pi",                                          # pion (low-mass lobe)
    321: "K", 411: "D", 431: "Ds",                      # pseudoscalar
    113: "rho", 223: "omega", 333: "phi",               # light vectors
    443: "Jpsi", 100443: "psi2S",                       # charmonium vectors
}
SIGMA_INEL_MB = 80.0   # pp inelastic at 13.6 TeV [PUBLIC_PIN, ~PDG/TOTEM]

# Store only 1 in PRESCALE[name] of these abundant-but-physics-negligible
# parents (weight multiplied by the factor to preserve the total) -- keeps the
# file/memory bounded. pi/rho/omega are ~as abundant as kaons forward but their
# phi yield is sub-dominant (pi: narrow low-mass lobe only; rho/omega:
# alpha^2-suppressed dimuon). The physics channels (K/D/Ds/phi/Jpsi/psi2S) are
# kept in full.
PRESCALE = {"pi": 20, "rho": 10, "omega": 10}

_COMMON = [
    "Tune:pp = 14", "Beams:idA = 2212", "Beams:idB = 2212",
    "Beams:frameType = 1", "Beams:eCM = 13600.",
    "Print:quiet = on", "Next:numberCount = 0",
    "Init:showChangedSettings = off", "Init:showChangedParticleData = off",
    "Init:showProcesses = off", "Init:showMultipartonInteractions = off",
    "Check:event = off",
] + [f"{pid}:mayDecay = off" for pid in PARENT_IDS]
_SOFT = ["SoftQCD:all = on", "HardQCD:all = off", "Onia:all = on"]
_HARD = ["SoftQCD:all = off", "HardQCD:all = off",
         "HardQCD:hardccbar = on", "HardQCD:hardbbbar = on",
         "Onia:all = on"]


def _run_sample(mode, n_gen, pt_cut, seed, theta_max):
    """Generate one sample; return dict parent -> (p4 list, weights)."""
    try:
        import pythia8mc as p8
    except ImportError:
        # Same API. In the hepbench env this fallback is not even a different
        # build: `pythia8` there is a shim aliasing this very wheel, because
        # conda-forge's 8.312 package cannot share a prefix with the 8.317
        # wheel (see scripts/fix_pythia_env.py). Kept for other environments.
        import pythia8 as p8
    py = p8.Pythia("", False)
    for s in _COMMON + (_SOFT if mode == "soft" else _HARD):
        py.readString(s)
    if mode == "hard":
        py.readString(f"PhaseSpace:pTHatMin = {pt_cut}")
    py.readString("Random:setSeed = on")
    py.readString(f"Random:seed = {seed}")
    if not py.init():
        raise RuntimeError(f"Pythia init failed ({mode})")

    info = py.infoPython()
    p4 = {name: [] for name in PARENT_IDS.values()}
    seen = {name: 0 for name in PARENT_IDS.values()}   # for prescaling
    n_acc = 0
    while n_acc < n_gen:
        if not py.next():
            continue
        pthat = info.pTHat()
        # stitch: soft keeps low-pThat, hard keeps high-pThat (no overlap)
        if mode == "soft" and pthat > pt_cut:
            n_acc += 1
            continue
        if mode == "hard" and pthat < pt_cut:
            n_acc += 1
            continue
        ev = py.event
        for i in range(ev.size()):
            pid = abs(ev[i].id())
            if pid not in PARENT_IDS:
                continue
            pr = ev[i]
            # forward acceptance: keep parents within theta_max of the beam
            # (both directions; the detector sits on one side but the flux
            # is symmetric, folded downstream). pz sign selects a hemisphere.
            pz = pr.pz()
            pmag = np.sqrt(pr.px()**2 + pr.py()**2 + pz**2)
            if pmag <= 0:
                continue
            theta = np.arccos(abs(pz) / pmag)
            if theta > theta_max:
                continue
            name = PARENT_IDS[pid]
            ps = PRESCALE.get(name, 1)          # keep only 1 in ps if prescaled
            if ps > 1:
                seen[name] += 1
                if seen[name] % ps != 0:
                    continue
            p4[name].append([pr.e(), pr.px(), pr.py(), abs(pz)])
        n_acc += 1

    py.stat()
    sigma = py.infoPython().sigmaGen()   # mb, finalized after stat()
    # per-inelastic-collision weight for each harvested parent
    w_per = sigma / (n_gen * SIGMA_INEL_MB)
    # HEMISPHERE FOLD. The theta cut above is taken about the beam AXIS
    # (arccos(|pz|/p)), so parents from BOTH cones are harvested, and they are
    # stored with pz -> |pz|, i.e. all as forward-going. That doubles the
    # sample, so each parent must carry HALF the per-collision weight -- the
    # same compensating factor PRESCALE already carries. The detector is
    # single-arm (z_shield .. z_max at positive z, and DecayVolume requires
    # u_z > 0), so a genuinely backward parent can never reach it: folding is
    # variance reduction, not extra flux.
    #
    # Omitting this factor made every flux, and every yield built on one, 2x
    # too large. It was invisible for two campaigns because the served tool
    # folded the same way, so the reference and the tooled agents agreed --
    # while agents who kept only pz > 0, which is correct, were scored as 2x
    # low. See benchmarks/llp_forward/soln/notes/strata_convergence.md.
    FOLD_FACTOR = 0.5
    out = {}
    for name, arr in p4.items():
        a = np.array(arr, dtype=float) if arr else np.zeros((0, 4))
        # prescaled species carry a compensating weight so sum(weight) is intact
        out[name] = (a, np.full(len(a),
                                w_per * PRESCALE.get(name, 1) * FOLD_FACTOR))
    out["_sigma_mb"] = sigma
    out["_n_gen"] = n_gen
    return out


def generate(n_soft, n_hard, pt_cut=1.0, seed=1000, theta_max=1e-2,
             out_path="parent_flux.npz"):
    """Generate + stitch soft and hard samples; write the combined flux."""
    t0 = time.time()
    # Forward production (low theta = low pT) lives in the soft sample;
    # the hard-ccbar sample gives CENTRAL charm and is off the forward
    # acceptance, so it is optional (n_hard=0) and, when used, only tops up
    # the higher-pT tail. Forward charm statistics come from a large soft run.
    print(f"soft sample ({n_soft} events, pThat<{pt_cut})...")
    soft = _run_sample("soft", n_soft, pt_cut, seed, theta_max)
    print(f"  sigmaGen = {soft['_sigma_mb']:.3g} mb; "
          f"parents/coll: " + ", ".join(
              f"{k}={soft[k][1].sum():.3e}" for k in PARENT_IDS.values()))
    samples = [soft]
    if n_hard > 0:
        print(f"hard ccbar sample ({n_hard} events, pThat>{pt_cut})...")
        hard = _run_sample("hard", n_hard, pt_cut, seed + 1, theta_max)
        print(f"  sigmaGen = {hard['_sigma_mb']:.3g} mb; "
              f"parents/coll: " + ", ".join(
                  f"{k}={hard[k][1].sum():.3e}" for k in PARENT_IDS.values()))
        samples.append(hard)

    combined = {}
    for name in PARENT_IDS.values():
        p4 = np.concatenate([s[name][0] for s in samples], axis=0)
        w = np.concatenate([s[name][1] for s in samples], axis=0)
        combined[f"{name}_p4"] = p4
        combined[f"{name}_w"] = w
    meta = dict(
        sqrt_s_gev=13600.0, sigma_inel_mb=SIGMA_INEL_MB, pt_cut_gev=pt_cut,
        theta_max_rad=theta_max, n_soft=n_soft, n_hard=n_hard,
        sigma_soft_mb=soft["_sigma_mb"],
        sigma_hard_mb=(samples[1]["_sigma_mb"] if n_hard > 0 else 0.0),
        seed=seed, tune="Monash(14)",
        provenance="pythia8mc; soft+hardccbar stitched at pTHat; "
                   "parents stable, harvested at production; "
                   "config adapted from tauALP (arXiv:2507.15271)")
    combined["_meta"] = np.array([str(meta)], dtype=object)
    np.savez(out_path, **combined)
    for name in PARENT_IDS.values():
        n = len(combined[f"{name}_p4"])
        wsum = combined[f"{name}_w"].sum()
        print(f"  {name}: {n} harvested, {wsum:.3e} per collision")
    print(f"wrote {out_path}  ({time.time()-t0:.1f}s)")
    return out_path


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-soft", type=int, default=20000)
    ap.add_argument("--n-hard", type=int, default=20000)
    ap.add_argument("--pt-cut", type=float, default=1.0)
    ap.add_argument("--theta-max", type=float, default=1e-2)
    ap.add_argument("--seed", type=int, default=1000)
    ap.add_argument("--out", default="parent_flux.npz")
    a = ap.parse_args()
    generate(a.n_soft, a.n_hard, a.pt_cut, a.seed, a.theta_max, a.out)
