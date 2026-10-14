"""
# benchmarks/symbolic/decay_S_to_SpV/ground_truth/derivation.py is a part of HEPBench.
# Copyright (C) 2026 HEPBench authors (see AUTHORS for details).
# HEPBench is licensed under the GNU GPL v3 or later, see LICENSE for details.
"""
"""
Ground truth for decay_S_to_SpV: tree-level two-body width of a scalar S
(mass m_S) into a lighter scalar S' (mass m_Sp) and a massive vector V
(mass m_V), via the derivative coupling
    L = g V^mu (S d_mu S' - S' d_mu S),   g dimensionless.
The vector daughter's three polarizations are summed (CONVENTIONS.md
sec. 3); the scalar parent carries no spin average.

Using p.eps* = 0 the amplitude is M = 2 g (eps* . p_S'), and the
polarization sum collapses to the Kallen function:
    <|M|^2> = g^2 lambda(m_S^2, m_Sp^2, m_V^2) / m_V^2,
    Gamma = g^2 [lambda(m_S^2, m_Sp^2, m_V^2)]^(3/2) / (16 pi m_S^3 m_V^2),
again a pure p-wave (Gamma ~ |p|^3) rate. (Same vertex as decay_V_to_SS,
but with the scalar as parent, so no 1/3 polarization average -- hence
16 pi here vs 48 pi there.)

Part (a)  scalar daughter of mass m_Sp.
Part (b)  massless scalar daughter (m_Sp = 0): Gamma = g^2 (m_S^2-m_V^2)^3
          / (16 pi m_S^3 m_V^2).

Literature: the scalar-QED emission vertex i g (p + p')_mu and the
resulting p-wave rate, e.g. M.D. Schwartz, Quantum Field Theory and the
Standard Model (scalar QED); the structure is that of A -> Z h /
H+- -> W+- h type decays in extended scalar sectors (A. Djouadi,
arXiv:hep-ph/0503173, Higgs-to-Higgs+gauge decays). Verified against the
explicit-polarization numeric computation in _shared/dirac_numeric.py.

Run from the repo root:
    python benchmarks/symbolic/decay_S_to_SpV/ground_truth/derivation.py
"""

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))
import dirac_numeric as dn  # noqa: E402

OUT = Path(__file__).resolve().parent / "truth.json"

# --- task parameters (quoted in the prompt) ---
G_A, MS, MSP, MV = 0.90, 600.0, 140.0, 250.0   # part (a)
G_B = 0.70                                       # part (b) m_Sp = 0


def analytic_a():
    lam = dn.kallen(MS**2, MSP**2, MV**2)
    return G_A**2 * lam**1.5 / (16 * np.pi * MS**3 * MV**2)


def analytic_b():
    return G_B**2 * (MS**2 - MV**2)**3 / (16 * np.pi * MS**3 * MV**2)


def _numeric(g, msp):
    def msq(p1, p2):  # p1 = scalar S', p2 = vector V
        eps = dn.pol_vectors(p2, MV)
        total = 0.0
        for ev in eps:
            ed = sum(dn.ETA[m, m] * np.conjugate(ev[m]) * p1[m]
                     for m in range(4))
            total += abs(2 * g * ed) ** 2
        return total  # scalar parent: no average
    return dn.two_body_width(MS, msp, MV, msq)


def main():
    rows = [("part_a_width_gev", analytic_a(), _numeric(G_A, MSP)),
            ("part_b_width_gev", analytic_b(), _numeric(G_B, 0.0))]
    for name, ana, num in rows:
        rel = abs(ana - num) / ana
        print(f"{name}: analytic {ana:.10g}  numeric {num:.10g}  rel {rel:.2e}")
        assert rel < 1e-9, f"{name}: analytic vs numeric mismatch"

    truth = {
        "part_a_width_gev": analytic_a(),
        "part_a_width_formula":
            "g**2 * ((mS**2-(mSp+mV)**2)*(mS**2-(mSp-mV)**2))**(3/2)"
            " / (16*pi*mS**3*mV**2)",
        "part_b_width_gev": analytic_b(),
        "part_b_width_formula":
            "g**2 * (mS**2 - mV**2)**3 / (16*pi*mS**3*mV**2)",
        "_metadata": {
            "generated_by": "ground_truth/derivation.py",
            "conventions": "../CONVENTIONS.md",
            "parameters": {
                "part_a": {"g": G_A, "mS_gev": MS, "mSp_gev": MSP,
                           "mV_gev": MV},
                "part_b": {"g": G_B, "mS_gev": MS, "mSp_gev": 0.0,
                           "mV_gev": MV},
            },
            "verification": "analytic formulas reproduced to <1e-9 by "
                            "independent numeric computation with explicit "
                            "polarization vectors",
            "citations": [
                "M.D. Schwartz, Quantum Field Theory and the Standard "
                "Model (scalar-QED emission vertex)",
                "A. Djouadi, Phys.Rept. 459 (2008), arXiv:hep-ph/0503173 "
                "(Higgs-to-Higgs+gauge-boson decays)",
            ],
        },
    }
    OUT.write_text(json.dumps(truth, indent=2) + "\n")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
