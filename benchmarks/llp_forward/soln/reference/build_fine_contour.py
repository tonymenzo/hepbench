#!/usr/bin/env python3
"""Scan the reach contour on a FINE mass grid.

The graded reference declares only 12 masses, of which 5 have reach -- enough to
grade an agent, far too coarse to *draw* the exclusion contour. This scans an
arbitrary number of masses through the same pipeline (`derivation.assemble_all`
+ `propagate.precompute` + `propagate.band`, the reference's own functions) and
writes the result to JSON so plotting is instant.

It is NOT the graded contract and never touches `soln/truth.json`. It is the
high-resolution picture of the same physics.

Note this differs from the older `soln/code/leptonic_contour.py`, which
assembles only the pseudoscalars and hardcodes `channel="mumu"`. This uses the
full flux (pseudoscalar + vector) and the reference's own per-mass search
choice, so it is directly comparable to `truth.json`.

    python build_fine_contour.py --tag a --n-mass 64
    python build_fine_contour.py --tag a --n-mass 96 --m-min 0.012 --m-max 0.8

Cost is ~30 s per mass, dominated by the per-mass kappa tables, so it runs in a
process pool. 64 masses on 8 workers takes a few minutes.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
SOLN = HERE.parent
sys.path.insert(0, str(SOLN / "code"))
sys.path.insert(0, str(SOLN / "depr"))

_G = {}


def _init(flux_path: str, cap: int):
    """Load the flux once per worker, not once per mass."""
    import derivation as DV
    import propagate as PR
    _G["DV"] = DV
    _G["PR"] = PR
    _G["data"] = np.load(flux_path, allow_pickle=True)
    _G["geom"] = DV.DecayVolume(DV.GEOM)
    _G["cap"] = cap


def _one(m: float):
    """(band, peak) at one mass, through the reference's own pipeline."""
    DV, PR = _G["DV"], _G["PR"]
    t0 = time.time()
    search = DV.search_of(m)
    rng = np.random.default_rng(DV.SEED)
    flux, _lab = DV.assemble_all(_G["data"], m, rng, cap=_G["cap"])
    pc = PR.precompute(flux, m, _G["geom"], channel=search, seed=DV.SEED)
    G_LO, G_HI = 1e-9, 1.0
    bnd, peak = PR.band(pc, DV.N_INT, DV.N_TARGET, g_lo=G_LO, g_hi=G_HI)
    # PR.band searches g in [G_LO, G_HI]; if a crossing is not bracketed it
    # returns the boundary. That is a CENSORED edge, not a physical one -- at
    # very low mass the phi is so long-lived the band stays open past g=1.
    # Flag it so the plot can dash it instead of drawing a fake contour.
    cens_hi = bool(bnd is not None and bnd[1] >= G_HI * 0.999)
    cens_lo = bool(bnd is not None and bnd[0] <= G_LO * 1.001)
    return dict(m=float(m), search=search,
                band=[float(bnd[0]), float(bnd[1])] if bnd else None,
                censored_hi=cens_hi, censored_lo=cens_lo,
                peak=float(peak), wall_s=round(time.time() - t0, 1))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tag", default="a")
    ap.add_argument("--n-mass", type=int, default=64)
    # default lower edge sits below m_pi - m_mu = 0.0339 GeV so the scan
    # resolves the pion-fed low-mass gamma gamma lobe, which the declared grid
    # (starting at 0.06) never samples
    ap.add_argument("--m-min", type=float, default=0.015)
    ap.add_argument("--m-max", type=float, default=0.60)
    ap.add_argument("--cap", type=int, default=40000)
    ap.add_argument("--workers", type=int,
                    default=max(1, min(8, (os.cpu_count() or 4) - 2)))
    a = ap.parse_args(argv)

    flux = HERE / "flux" / f"parent_flux_{a.tag}.npz"
    if not flux.is_file():
        print(f"no such flux: {flux}", file=sys.stderr)
        return 2

    masses = np.geomspace(a.m_min, a.m_max, a.n_mass)
    print(f"scanning {a.n_mass} masses {a.m_min}-{a.m_max} GeV "
          f"on {a.workers} workers (cap={a.cap})")
    t0 = time.time()
    with Pool(a.workers, initializer=_init,
              initargs=(str(flux), a.cap)) as pool:
        rows = []
        for i, r in enumerate(pool.imap(_one, masses), 1):
            rows.append(r)
            tag = (f"band {r['band'][0]:.3e}-{r['band'][1]:.3e}"
                   if r["band"] else f"no reach (peak {r['peak']:.2e})")
            print(f"  [{i:>3d}/{a.n_mass}] m={r['m']:.4f} {r['search']:>5s}  {tag}")
    dt = time.time() - t0

    out = HERE / "out" / f"fine_contour_{a.tag}.json"
    out.write_text(json.dumps(dict(
        flux=flux.name, cap=a.cap, n_mass=a.n_mass,
        m_min=a.m_min, m_max=a.m_max, wall_s=round(dt, 1),
        created_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        note=("full pipeline (pseudoscalar+vector), reference search choice "
              "per mass; NOT the graded contract"),
        points=rows), indent=2))
    n_reach = sum(1 for r in rows if r["band"])
    print(f"\nwrote {out}  ({dt:.0f}s, {n_reach}/{len(rows)} masses with reach)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
