#!/usr/bin/env python3
"""Convergence of the reference yields in the parent decay-length stratum count.

WHY THIS EXISTS
---------------
`parents.decay_parents_to_phi` replaces the parent's exponential decay-length
distribution by K DETERMINISTIC quantiles,

    ell_k = -lambda ln(1 - (k + 1/2)/K),    lambda = beta*gamma * c*tau_parent.

That is a variance-reduction device, and it is unbiased only where the
integrand is smooth across a stratum. It is NOT smooth here: the geometry
imposes a hard production cut (phi must be made upstream of z_prod = 50 m) and
a hard decay window (112-163 m). When a stratum straddles one of those edges,
its single representative point passes or fails WHOLESALE instead of
contributing its true partial weight. The result is a systematic bias, not
Monte-Carlo noise -- rerunning with a different seed does not move it.

The bias is worst where the parent is long-lived compared with the cut. For a
forward kaon, lambda = beta*gamma * c*tau_K ~ 200 * 3.711 m ~ 742 m, so the
whole accepted region is ell < 50 m = 0.067 lambda -- inside the FIRST stratum
unless K is large. Short-lived parents (D, Ds; c*tau ~ 1e-4 m) decay promptly,
vz ~ 0 always, and no stratum can straddle anything.

WHAT IT FOUND (2026-08-07, flux/parent_flux_a.npz)
--------------------------------------------------
  * The three lower declared couplings at every mass are converged at the
    reference's K = N_STRATA = 40, to 1-4%.
  * The HIGHEST declared coupling at every K-dominated mass is NOT: K=40 sits
    a factor 2.6-3.5 below the K>=160 limit. That point probes the upper
    (decay-length) branch of the band, which is set by the sparse parents
    decaying just upstream of the volume -- precisely the region the
    stratification resolves worst.
    Affected: gg@0.06, gg@0.12, gg@0.18, gg@0.205, mumu@0.23, mumu@0.28
    (~3x), and mumu@0.34 (1.13x). Masses >= 0.42 are unaffected (D/Ds).
  * Convergence sets in by K ~ 160; K = 640 and 2560 agree to 1%.

This also explains the agents' low-mass gamma-gamma deficit. Every tooled
trial in the 2026-08 campaign chose K between 1 and 24 (the served tool's
default is K=1), and at gg@0.06 the yields land exactly where this scan
predicts for their K -- see benchmarks/llp_forward/soln/notes/strata_convergence.md.

USAGE
-----
    python check_strata_convergence.py                  # all declared points
    python check_strata_convergence.py --point gg 0.06 --strata 1 4 6 8 40 160
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent          # soln/reference
SOLN = HERE.parent
sys.path.insert(0, str(SOLN / "code"))

import propagate as PR                          # noqa: E402
from pipeline import DecayVolume                # noqa: E402

GEOM = DecayVolume({"z_min_m": 112.0, "z_max_m": 163.0, "r_volume_m": 0.92,
                    "z_det_m": 165.0, "r_det_m": 0.92, "z_prod_m": 50.0,
                    "x_off_m": 0.0})


def yields(data, search, m, gs, K, cap, seed=7):
    """N_sig at each g for one (search, mass) at stratum count K."""
    rng = np.random.default_rng(seed)
    flux, _ = PR.assemble_pseudoscalar(data, m, rng, cap=cap, n_strata=K)
    pc = PR.precompute(flux, m, GEOM, channel=search)
    n_int = yields.n_int
    return [PR.yield_g(pc, n_int, g) for g in gs]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--flux", default=str(HERE / "flux" / "parent_flux_a.npz"))
    ap.add_argument("--truth", default=str(SOLN / "truth.json"))
    ap.add_argument("--strata", type=int, nargs="+", default=[40, 640])
    ap.add_argument("--cap", type=int, default=10000,
                    help="parents kept; held FIXED across K so only K varies")
    ap.add_argument("--point", nargs=2, metavar=("SEARCH", "MASS"),
                    help="restrict to one declared (search, mass)")
    a = ap.parse_args(argv)

    truth = json.loads(Path(a.truth).read_text())
    yields.n_int = truth["n_int"]
    data = np.load(a.flux, allow_pickle=True)

    by = collections.defaultdict(list)
    for p in truth["points"]:
        by[(p["search"], p["m_phi"])].append(p)
    if a.point:
        key = (a.point[0], float(a.point[1]))
        by = {key: by[key]} if key in by else {}
        if not by:
            print(f"no declared point {a.point}", file=sys.stderr)
            return 2

    ref = max(a.strata)
    print(f"  flux {Path(a.flux).name}   cap={a.cap} parents (fixed)   "
          f"reference column K={ref}")
    print(f"  ratio N_sig(K) / N_sig(K={ref}) at the declared couplings\n")
    hdr = "  ".join(f"g{i+1}" for i in range(4))
    print(f"  {'point':16s} {'K':>6s}   {hdr}")
    worst = []
    for (search, m), pts in sorted(by.items(), key=lambda x: (x[0][0], x[0][1])):
        gs = [p["g"] for p in pts]
        out = {K: yields(data, search, m, gs, K, a.cap) for K in sorted(a.strata)}
        base = out[ref]
        for K in sorted(a.strata):
            r = [(v / b if b > 0 else float("nan")) for v, b in zip(out[K], base)]
            tag = f"{search}@{m}" if K == sorted(a.strata)[0] else ""
            print(f"  {tag:16s} {K:>6d}   " +
                  "  ".join(f"{x:>4.2f}" for x in r))
            if K == 40 and len(r) == 4 and r[-1] == r[-1] and r[-1] < 0.8:
                worst.append((f"{search}@{m}", r[-1]))
        print()

    if worst:
        print("  UNDER-CONVERGED at the reference's K=40 (highest coupling):")
        for name, r in worst:
            print(f"    {name:16s} {1/r:>5.2f}x low")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
