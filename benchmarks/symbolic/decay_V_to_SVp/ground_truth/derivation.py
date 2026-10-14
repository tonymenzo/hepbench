"""
# benchmarks/symbolic/decay_V_to_SVp/ground_truth/derivation.py is a part of HEPBench.
# Copyright (C) 2026 HEPBench authors (see AUTHORS for details).
# HEPBench is licensed under the GNU GPL v3 or later, see LICENSE for details.
"""
"""
Ground truth for decay_V_to_SVp: tree-level two-body width of a massive
vector V (mass m_V) into a scalar S (mass m_S) and a second massive
vector V' (mass m_Vp), via the SVV coupling
    L = g S V_mu V'^mu,   g of mass dimension one.
Average over the parent's three polarizations (CONVENTIONS.md sec. 5);
sum over V''s three polarizations. The S V V' vertex is i g eta^munu (V
and V' distinct, so no factor 2).

    M = i g eps(P) . eps*(q'),
    <|M|^2> = (1/3) g^2 [ 2 + (m_V^2 - m_S^2 + m_Vp^2)^2
                              / (4 m_V^2 m_Vp^2) ],
    Gamma = sqrt(lambda(m_V^2, m_S^2, m_Vp^2)) / (16 pi m_V^3) * <|M|^2>.

This is the same SVV operator as decay_S_to_VV, here with a vector as
parent (the V' -> S V / "vector to scalar + vector" channel, e.g. a
heavy Z' -> h Z type decay).

Part (a)  scalar daughter of mass m_S.
Part (b)  massless scalar daughter (m_S = 0).

Literature: SVV gauge-Higgs coupling and V -> V S widths, A. Djouadi,
arXiv:hep-ph/0503172/0503173 (gauge-boson + Higgs final states); the
Lorentz structure is the massive-vector analogue of the H -> VV
contraction. Verified against the explicit-polarization numeric
computation in _shared/dirac_numeric.py.

Run from the repo root:
    python benchmarks/symbolic/decay_V_to_SVp/ground_truth/derivation.py
"""

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))
import dirac_numeric as dn  # noqa: E402

OUT = Path(__file__).resolve().parent / "truth.json"

# --- task parameters (quoted in the prompt) ---
G_A, MV, MS, MVP = 180.0, 700.0, 160.0, 250.0   # part (a)
G_B = 150.0                                       # part (b) m_S = 0


def analytic_a():
    lam = dn.kallen(MV**2, MS**2, MVP**2)
    msq = (1 / 3) * G_A**2 * (2 + (MV**2 - MS**2 + MVP**2)**2
                             / (4 * MV**2 * MVP**2))
    return np.sqrt(lam) / (16 * np.pi * MV**3) * msq


def analytic_b():
    lam = dn.kallen(MV**2, 0.0, MVP**2)
    msq = (1 / 3) * G_B**2 * (2 + (MV**2 + MVP**2)**2 / (4 * MV**2 * MVP**2))
    return np.sqrt(lam) / (16 * np.pi * MV**3) * msq


def _numeric(g, ms):
    def msq(p1, p2):  # p1 = scalar S, p2 = vector V'
        P = np.array([MV, 0.0, 0.0, 0.0])
        epsP = dn.pol_vectors(P, MV)
        epsq = dn.pol_vectors(p2, MVP)
        total = 0.0
        for a in epsP:
            for b in epsq:
                dot = sum(dn.ETA[m, m] * a[m] * np.conjugate(b[m])
                          for m in range(4))
                total += abs(g * dot) ** 2
        return total / 3.0
    return dn.two_body_width(MV, ms, MVP, msq)


def main():
    rows = [("part_a_width_gev", analytic_a(), _numeric(G_A, MS)),
            ("part_b_width_gev", analytic_b(), _numeric(G_B, 0.0))]
    for name, ana, num in rows:
        rel = abs(ana - num) / ana
        print(f"{name}: analytic {ana:.10g}  numeric {num:.10g}  rel {rel:.2e}")
        assert rel < 1e-9, f"{name}: analytic vs numeric mismatch"

    truth = {
        "part_a_width_gev": analytic_a(),
        "part_a_width_formula":
            "sqrt((mV**2-(mS+mVp)**2)*(mV**2-(mS-mVp)**2))/(16*pi*mV**3)"
            " * g**2 * (2 + (mV**2 - mS**2 + mVp**2)**2"
            "/(4*mV**2*mVp**2)) / 3",
        "part_b_width_gev": analytic_b(),
        "part_b_width_formula":
            "(mV**2 - mVp**2)/(16*pi*mV**3)"
            " * g**2 * (2 + (mV**2 + mVp**2)**2/(4*mV**2*mVp**2)) / 3",
        "_metadata": {
            "generated_by": "ground_truth/derivation.py",
            "conventions": "../CONVENTIONS.md",
            "parameters": {
                "part_a": {"g_gev": G_A, "mV_gev": MV, "mS_gev": MS,
                           "mVp_gev": MVP},
                "part_b": {"g_gev": G_B, "mV_gev": MV, "mS_gev": 0.0,
                           "mVp_gev": MVP},
            },
            "verification": "analytic formulas reproduced to <1e-9 by "
                            "independent numeric computation with explicit "
                            "polarization vectors",
            "citations": [
                "A. Djouadi, Phys.Rept. 457/459 (2008), "
                "arXiv:hep-ph/0503172, 0503173 (gauge-boson + Higgs "
                "final states, SVV coupling)",
            ],
        },
    }
    OUT.write_text(json.dumps(truth, indent=2) + "\n")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
