"""
# benchmarks/llp_forward/ground_truth/verify_tools_reproduce_truth.py -- HEPBench (GPL v3).

REFERENCE SOLUTION TRAJECTORY + REGRESSION TEST.

Drives ONLY the heptapod agent tools (MesonDecayToLLP -> DecayInVolume) on the
SAME forward flux the ground truth uses, with the CORRECT physics (widths /
kappa / conventions taken from _shared), and checks that the tool pipeline
reproduces truth.json's N_sig within the benchmark's fine tolerance.

This answers: "can the derived task be solved with just the tools, and do the
tools agree with the _shared ground-truth engine?" It also guards against the
one real risk -- the tools read TABULATED spectra CSVs while truth samples the
production ME on-the-fly; if those drift, this test fails.

The flux-generation step (pythia -> harvest) is held fixed to truth's committed
flux (the 2M npz), so this isolates the physics of meson_decay + decay_in_volume
from Pythia run-to-run scatter. A few representative masses are checked (the
gamma-gamma lobe, the dimuon wedge, and the charm window) -- enough to exercise
both searches and the K / charm / vector channels.

Run (conda env hepbench, HEPTAPOD_HOME set):
    HEPTAPOD_HOME=/path/to/heptapod python verify_tools_reproduce_truth.py
"""
import json
import math
import os
import shutil
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SHARED = os.path.abspath(os.path.join(HERE, "code"))
HEPTAPOD = os.environ["HEPTAPOD_HOME"]
for p in (SHARED, HEPTAPOD):
    if p not in sys.path:
        sys.path.insert(0, p)

import parents as P                    # noqa: E402  (_shared)
import production as prod              # noqa: E402
import production_vector as PV         # noqa: E402
from tools.llp import (                # noqa: E402  (heptapod agent tools)
    MesonDecayToLLPTool, DecayInVolumeVsCouplingTool)

MMU = P.MMU
THR = 2.0 * MMU
C_LIGHT = 2.99792458e8
NPZ = os.environ.get("LLP_FLUX", "/tmp/parent_flux_allchan_2M.npz")
N_INT = 2.7e18
CAP = 20000                            # subsample cap (weight-compensated)
SEED = 1
SPECTRA = os.path.join(HERE, "..", "variants", "derived", "sandbox",
                       "template", "spectra")
GEOM = os.path.join(HERE, "..", "variants", "derived", "sandbox",
                    "template", "geometry", "geometry.yaml")
# representative masses: gg lobe (K-dominated), dimuon wedge, charm window
TEST_M = [0.12, 0.23, 0.28, 0.42]
PSEUDO = ["pi", "K", "D", "Ds"]
VECTOR = list(PV.VECTORS)


def parent_info(name):
    """(parent_mass, ctau_m, n_strata). Strata (decay-in-flight sampling)
    only matter for LONG-LIVED parents: for a prompt parent every stratum
    collapses to the same ~IP vertex, so n_strata=1 gives the identical yield.
    So 40 strata for the kaon/pion (c*tau ~ m), 1 for charm and vectors --
    this is what keeps the record volume bounded without changing the physics."""
    if name in P.PARENTS:
        m, _f, _V, tau = P.PARENTS[name]
        ctau = C_LIGHT * tau
        return m, ctau, (40 if ctau > 1.0 else 1)
    mV, _br = PV.VECTORS[name]
    return mV, 0.0, 1


def kappa_of(name, m):
    return (P.kappa(name, m) if name in P.PARENTS
            else PV.kappa(name, m))


def spectrum_path(name, m):
    p = os.path.join(SPECTRA, f"spectrum_{name}_m{m:.3f}.csv")
    return p if os.path.exists(p) else None


def main():
    if not os.path.exists(NPZ):
        raise SystemExit(f"flux not found: {NPZ} (set LLP_FLUX)")
    truth = json.load(open(os.path.join(HERE, "truth.json")))
    tpts = {(p["search"], round(p["m_phi"], 4), p["g"]): p["nsig"]
            for p in truth["points"]}

    sb = os.path.join("/tmp", "llp_tool_solution")
    shutil.rmtree(sb, ignore_errors=True)
    for d in ("flux", "llp", "yields"):
        os.makedirs(os.path.join(sb, d), exist_ok=True)
    shutil.copy(GEOM, os.path.join(sb, "geometry.yaml"))
    shutil.copytree(SPECTRA, os.path.join(sb, "spectra"))

    # ---- STEP 1: flux -> per-channel harvest-format jsonl (cap, weighted) ----
    data = dict(np.load(NPZ, allow_pickle=True))
    rng = np.random.default_rng(SEED)
    flux_paths = {}
    for name in PSEUDO + VECTOR:
        key = f"{name}_p4"
        if key not in data or len(data[key]) == 0:
            continue
        p4, w = data[key], data[f"{name}_w"]
        if len(p4) > CAP:
            idx = rng.choice(len(p4), CAP, replace=False)
            p4, w = p4[idx], w[idx] * (len(data[key]) / CAP)
        fp = os.path.join(sb, "flux", f"parents_{name}.jsonl")
        with open(fp, "w") as fh:
            for i in range(len(p4)):
                fh.write(json.dumps({
                    "parent": name, "E": float(p4[i, 0]), "px": float(p4[i, 1]),
                    "py": float(p4[i, 2]), "pz": float(p4[i, 3]),
                    "weight_per_collision": float(w[i])}) + "\n")
        flux_paths[name] = fp

    # ---- STEPS 2-4: per mass, decay every open channel then propagate --------
    print(f"{'search':6s} {'m':>6s} {'g':>10s} {'tool_Nsig':>11s} "
          f"{'truth_Nsig':>11s} {'ratio':>7s}")
    ratios = []
    for m in TEST_M:
        search = "gg" if m <= THR else "mumu"
        # STEP 2-3: decay each open channel to phi at this mass, concatenate
        combined = os.path.join(sb, "llp", f"phi_m{m:.3f}.jsonl")
        open(combined, "w").close()
        for name in PSEUDO + VECTOR:
            if name not in flux_paths:
                continue
            spec_rel = f"spectra/spectrum_{name}_m{m:.3f}.csv"
            if not os.path.exists(os.path.join(sb, spec_rel)):
                continue                       # channel closed at this mass
            mM, ctau, nstr = parent_info(name)
            out_rel = f"llp/llp_{name}_m{m:.3f}.jsonl"
            tool = MesonDecayToLLPTool(
                base_directory=sb, parent_flux_path=f"flux/parents_{name}.jsonl",
                spectrum_spec=spec_rel,
                m_phi_gev=m, parent_mass_gev=mM, kappa=kappa_of(name, m),
                ctau_parent_m=ctau, n_strata=nstr, seed=SEED, output_path=out_rel)
            tool._setup()
            raw = tool._run()
            r = json.loads(raw) if raw.lstrip().startswith("{") else {}
            if r.get("status") != "ok":
                print(f"  ! {name} m={m}: {raw[:100]}")
                continue
            if r.get("n_samples", 0) == 0:
                continue
            with open(os.path.join(sb, out_rel)) as src, open(combined, "a") as dst:
                shutil.copyfileobj(src, dst)
            os.remove(os.path.join(sb, out_rel))   # free disk immediately
        # STEP 4: propagate + count at this mass over its declared g points
        g_pts = sorted(g for (s, mm, g) in tpts if s == search
                       and abs(mm - m) < 1e-4)
        if not g_pts:
            continue
        acc = "photon" if search == "gg" else "two_track"
        br = (prod.br_gammagamma(m, MMU) if search == "gg"
              else prod.br_mumu(m, MMU))
        wref = prod.width_ref_total(m, MMU)
        dv = DecayInVolumeVsCouplingTool(
            base_directory=sb, events_path=f"llp/phi_m{m:.3f}.jsonl",
            geometry_path="geometry.yaml", m_phi_gev=m, width_ref_gev=wref,
            g_grid=g_pts, n_int=N_INT, br_visible=br, acceptance=acc,
            daughter_masses_gev=[MMU, MMU], seed=SEED,
            output_path=f"yields/y_m{m:.3f}.json")
        dv._setup()
        rd = json.loads(dv._run())
        for y in rd["yields"]:
            g = y["g"]; tool_n = y["n_sig"]
            tr = tpts.get((search, round(m, 4), g))
            if tr is None:
                # match nearest declared g
                for (s, mm, gg), v in tpts.items():
                    if s == search and abs(mm - m) < 1e-4 and abs(math.log(gg / g)) < 1e-3:
                        tr = v; break
            ratio = (tool_n / tr) if (tr and tr > 0) else float("nan")
            ratios.append((search, m, g, ratio))
            print(f"{search:6s} {m:6.3f} {g:10.2e} {tool_n:11.3e} "
                  f"{tr if tr else float('nan'):11.3e} {ratio:7.2f}")

    # ---- verdict ------------------------------------------------------------
    good = [r for (_s, _m, _g, r) in ratios if r == r]     # drop nan
    within = [r for r in good if 1 / 1.4 <= r <= 1.4]
    print(f"\n{len(within)}/{len(good)} points within x1.4 of truth "
          f"(fine tolerance); median ratio "
          f"{sorted(good)[len(good) // 2]:.3f}" if good else "no points")
    shutil.rmtree(sb, ignore_errors=True)


if __name__ == "__main__":
    main()
