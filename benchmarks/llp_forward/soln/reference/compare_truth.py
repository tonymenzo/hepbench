#!/usr/bin/env python3
"""Compare two truth builds point by point.

    python compare_truth.py out/truth_a_k40untruncated.json out/truth_a.json

Prints the declared-point yields and the reach-band edges side by side, in
decades, so a rebuild can be inspected before it is promoted to the graded
`soln/truth.json`. Written for the 2026-08-07 stratification fix, but it is
generic: any two files with the same schema will do.
"""
from __future__ import annotations

import argparse
import json
import math
import statistics as st
from pathlib import Path


def load(p):
    d = json.loads(Path(p).read_text())
    pts = {(r["search"], round(float(r["m_phi"]), 4), float(r["g"])): float(r["nsig"])
           for r in d.get("points", [])}
    per = {(r["search"], round(float(r["m"]), 4)): r for r in d.get("_per_mass", [])}
    return d, pts, per


def dex(new, old):
    if not (new > 0 and old > 0):
        return None
    return math.log10(new / old)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("old")
    ap.add_argument("new")
    a = ap.parse_args(argv)

    _, po, mo = load(a.old)
    _, pn, mn = load(a.new)

    print(f"  OLD  {a.old}")
    print(f"  NEW  {a.new}\n")

    keys = sorted(set(po) & set(pn), key=lambda k: (k[0], k[1], k[2]))
    print(f"  DECLARED POINTS ({len(keys)} shared)")
    print(f"  {'point':16s} {'g':>11s} {'old N_sig':>12s} {'new N_sig':>12s} "
          f"{'ratio':>8s} {'dex':>7s}")
    ds, bymass = [], {}
    for k in keys:
        d = dex(pn[k], po[k])
        if d is not None:
            ds.append(abs(d))
            bymass.setdefault((k[0], k[1]), []).append(d)
        r = pn[k] / po[k] if po[k] > 0 else float("nan")
        print(f"  {k[0]+'@'+str(k[1]):16s} {k[2]:>11.4e} {po[k]:>12.4e} "
              f"{pn[k]:>12.4e} {r:>8.3f} {(d if d is not None else float('nan')):>7.3f}")

    if ds:
        print(f"\n  median |dex| {st.median(ds):.4f}   max |dex| {max(ds):.4f}"
              f"   points moving >0.1 dex: {sum(1 for x in ds if x > 0.1)}/{len(ds)}")

    bk = sorted(set(mo) & set(mn), key=lambda k: (k[0], k[1]))
    if bk:
        print(f"\n  REACH BAND EDGES")
        print(f"  {'point':16s} {'g_lo old':>11s} {'g_lo new':>11s} {'dex':>7s}"
              f"   {'g_hi old':>11s} {'g_hi new':>11s} {'dex':>7s}")
        for k in bk:
            bo, bn = mo[k].get("band"), mn[k].get("band")
            if not (bo and bn):
                continue
            dlo, dhi = dex(bn[0], bo[0]), dex(bn[1], bo[1])
            f = lambda v: (f"{v:>7.3f}" if v is not None else "     --")
            print(f"  {k[0]+'@'+str(k[1]):16s} {bo[0]:>11.4e} {bn[0]:>11.4e} {f(dlo)}"
                  f"   {bo[1]:>11.4e} {bn[1]:>11.4e} {f(dhi)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
