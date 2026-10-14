"""
# benchmarks/symbolic/decay_S_to_VV/ground_truth/derivation.py is a part of HEPBench.
# Copyright (C) 2026 HEPBench authors (see AUTHORS for details).
# HEPBench is licensed under the GNU GPL v3 or later, see LICENSE for details.
"""
"""
Ground truth for decay_S_to_VV: tree-level two-body width of a real
scalar S (mass m_S) into two massive vectors. The coupling g has mass
dimension one; the SVV vertex carries the factor 2 from the two
functional derivatives (CONVENTIONS.md sec. 4), and identical final
vectors carry the symmetry factor S = 2 (sec. 7) -- the two traps here.

Part (a)  L = g S V_mu V^mu  (identical vectors, mass m_V):
    vertex 2 i g eta^munu; <|M|^2> = g^2 [12 - 4 m_S^2/m_V^2 + m_S^4/m_V^4]
    = g^2 (m_S^4/m_V^4)(1 - 4x + 12x^2), x = m_V^2/m_S^2 -- the
    longitudinal-enhancement factor of the Higgs->VV width.
    Gamma = g^2 beta / (32 pi m_S) [12 - 4 m_S^2/m_V^2 + m_S^4/m_V^4],
    beta = sqrt(1 - 4 m_V^2/m_S^2).   (includes the 1/S = 1/2)

Part (b)  L = g S V1_mu V2^mu  (distinct vectors, masses m_1, m_2):
    vertex i g eta^munu (no factor 2; no symmetry factor):
    <|M|^2> = g^2 [2 + (m_S^2 - m_1^2 - m_2^2)^2 / (4 m_1^2 m_2^2)],
    Gamma = sqrt(lambda(m_S^2,m_1^2,m_2^2)) / (16 pi m_S^3) * <|M|^2>.

Literature: the (1 - 4x + 12x^2) structure is the textbook H -> VV
partial width, A. Djouadi, "The anatomy of electroweak symmetry breaking
I", Phys.Rept. 457 (2008), arXiv:hep-ph/0503172, sec. 2.2 (decays to
massive gauge bosons); J.F. Gunion et al., The Higgs Hunter's Guide,
ch. 2. Verified against the explicit-polarization numeric computation in
_shared/dirac_numeric.py.

Run from the repo root:
    python benchmarks/symbolic/decay_S_to_VV/ground_truth/derivation.py
"""

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))
import dirac_numeric as dn  # noqa: E402

OUT = Path(__file__).resolve().parent / "truth.json"

# --- task parameters (quoted in the prompt) ---
G_A, MS, MV = 130.0, 400.0, 90.0       # part (a) identical vectors
G_B, M1, M2 = 110.0, 400.0, 150.0      # part (b); m1 reuses 90 below
M1_B, M2_B = 90.0, 150.0


def analytic_a():
    beta = np.sqrt(1 - 4 * MV**2 / MS**2)
    msq = G_A**2 * (12 - 4 * MS**2 / MV**2 + MS**4 / MV**4)
    return beta / (32 * np.pi * MS) * msq


def analytic_b():
    lam = dn.kallen(MS**2, M1_B**2, M2_B**2)
    msq = G_B**2 * (2 + (MS**2 - M1_B**2 - M2_B**2)**2 / (4 * M1_B**2 * M2_B**2))
    return np.sqrt(lam) / (16 * np.pi * MS**3) * msq


def _msq_identical(q1, q2):
    # M = 2 i g (eps1* . eps2*); |M|^2 summed over both polarizations
    e1 = dn.pol_vectors(q1, MV)
    e2 = dn.pol_vectors(q2, MV)
    total = 0.0
    for a in e1:
        for b in e2:
            dot = sum(dn.ETA[m, m] * np.conjugate(a[m]) * np.conjugate(b[m])
                      for m in range(4))
            total += abs(2 * G_A * dot) ** 2
    return total  # scalar parent: no average


def _msq_distinct(q1, q2):
    e1 = dn.pol_vectors(q1, M1_B)
    e2 = dn.pol_vectors(q2, M2_B)
    total = 0.0
    for a in e1:
        for b in e2:
            dot = sum(dn.ETA[m, m] * np.conjugate(a[m]) * np.conjugate(b[m])
                      for m in range(4))
            total += abs(G_B * dot) ** 2
    return total


def main():
    rows = [
        ("part_a_width_gev", analytic_a(),
         dn.two_body_width(MS, MV, MV, _msq_identical, symmetry=2.0)),
        ("part_b_width_gev", analytic_b(),
         dn.two_body_width(MS, M1_B, M2_B, _msq_distinct)),
    ]
    for name, ana, num in rows:
        rel = abs(ana - num) / ana
        print(f"{name}: analytic {ana:.10g}  numeric {num:.10g}  rel {rel:.2e}")
        assert rel < 1e-9, f"{name}: analytic vs numeric mismatch"

    truth = {
        "part_a_width_gev": analytic_a(),
        "part_a_width_formula":
            "g**2 * sqrt(1 - 4*mV**2/mS**2) / (32*pi*mS)"
            " * (12 - 4*mS**2/mV**2 + mS**4/mV**4)",
        "part_b_width_gev": analytic_b(),
        "part_b_width_formula":
            "sqrt((mS**2-(m1+m2)**2)*(mS**2-(m1-m2)**2))/(16*pi*mS**3)"
            " * g**2 * (2 + (mS**2 - m1**2 - m2**2)**2/(4*m1**2*m2**2))",
        "_metadata": {
            "generated_by": "ground_truth/derivation.py",
            "conventions": "../CONVENTIONS.md",
            "parameters": {
                "part_a": {"g_gev": G_A, "mS_gev": MS, "mV_gev": MV},
                "part_b": {"g_gev": G_B, "mS_gev": MS,
                           "m1_gev": M1_B, "m2_gev": M2_B},
            },
            "verification": "analytic formulas reproduced to <1e-9 by "
                            "independent numeric computation with explicit "
                            "massive-vector polarization vectors",
            "citations": [
                "A. Djouadi, Phys.Rept. 457 (2008), arXiv:hep-ph/0503172, "
                "sec. 2.2 (H -> VV, the 1 - 4x + 12x^2 factor)",
                "J.F. Gunion, H.E. Haber, G. Kane, S. Dawson, The Higgs "
                "Hunter's Guide, ch. 2",
            ],
        },
    }
    OUT.write_text(json.dumps(truth, indent=2) + "\n")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
