"""
# benchmarks/symbolic/decay_V_to_SS/ground_truth/derivation.py is a part of HEPBench.
# Copyright (C) 2026 HEPBench authors (see AUTHORS for details).
# HEPBench is licensed under the GNU GPL v3 or later, see LICENSE for details.
"""
"""
Ground truth for decay_V_to_SS: tree-level two-body width of a massive
neutral vector V (mass m_V) into two scalars via the derivative coupling
    L = g V^mu (S1 d_mu S2 - S2 d_mu S1),   g dimensionless.
Average over the three initial polarizations (CONVENTIONS.md sec. 5).

The V S1 S2 vertex is i g (p1 - p2)_mu (the scalar-QED / rho->pi pi
structure). Because the vertex is antisymmetric under S1<->S2, a vector
cannot decay to two IDENTICAL scalars (the amplitude vanishes), so both
parts use distinct scalars. Summing the polarization tensor against
(p1-p2) collapses to the Kallen function:
    <|M|^2> = (1/3) g^2 lambda(m_V^2, m_1^2, m_2^2) / m_V^2,
    Gamma = g^2 [lambda(m_V^2, m_1^2, m_2^2)]^(3/2) / (48 pi m_V^5),
a pure p-wave (Gamma ~ |p|^3) rate.

Part (a)  distinct massive scalars m_1, m_2.
Part (b)  one massless scalar (m_2 = 0): Gamma = g^2 (m_V^2-m_1^2)^3
          / (48 pi m_V^5).

Literature: the i g (p1-p2)_mu derivative vertex and the resulting
p-wave |p|^3 rate are the textbook vector->two-scalar / rho->pi pi
structure, e.g. M.D. Schwartz, "Quantum Field Theory and the Standard
Model", ch. on scalar QED; J.J. Sakurai, "Currents and Mesons" (vector-
meson dominance, rho->pi pi). Verified against the explicit-polarization
numeric computation in _shared/dirac_numeric.py.

Run from the repo root:
    python benchmarks/symbolic/decay_V_to_SS/ground_truth/derivation.py
"""

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))
import dirac_numeric as dn  # noqa: E402

OUT = Path(__file__).resolve().parent / "truth.json"

# --- task parameters (quoted in the prompt) ---
G_A, MV, M1, M2 = 0.85, 500.0, 120.0, 210.0   # part (a) distinct massive
G_B, M1_B = 0.62, 180.0                         # part (b) m_2 = 0


def analytic_a():
    lam = dn.kallen(MV**2, M1**2, M2**2)
    return G_A**2 * lam**1.5 / (48 * np.pi * MV**5)


def analytic_b():
    return G_B**2 * (MV**2 - M1_B**2)**3 / (48 * np.pi * MV**5)


def _numeric(g, m1, m2):
    def msq(p1, p2):
        P = p1 + p2  # = (MV, 0, 0, 0)
        eps = dn.pol_vectors(P, MV)
        delta = p1 - p2
        total = 0.0
        for ev in eps:
            ed = sum(dn.ETA[m, m] * ev[m] * delta[m] for m in range(4))
            total += abs(g * ed) ** 2
        return total / 3.0
    return dn.two_body_width(MV, m1, m2, msq)


def main():
    rows = [("part_a_width_gev", analytic_a(), _numeric(G_A, M1, M2)),
            ("part_b_width_gev", analytic_b(), _numeric(G_B, M1_B, 0.0))]
    for name, ana, num in rows:
        rel = abs(ana - num) / ana
        print(f"{name}: analytic {ana:.10g}  numeric {num:.10g}  rel {rel:.2e}")
        assert rel < 1e-9, f"{name}: analytic vs numeric mismatch"

    truth = {
        "part_a_width_gev": analytic_a(),
        "part_a_width_formula":
            "g**2 * ((mV**2-(m1+m2)**2)*(mV**2-(m1-m2)**2))**(3/2)"
            " / (48*pi*mV**5)",
        "part_b_width_gev": analytic_b(),
        "part_b_width_formula":
            "g**2 * (mV**2 - m1**2)**3 / (48*pi*mV**5)",
        "_metadata": {
            "generated_by": "ground_truth/derivation.py",
            "conventions": "../CONVENTIONS.md",
            "parameters": {
                "part_a": {"g": G_A, "mV_gev": MV, "m1_gev": M1, "m2_gev": M2},
                "part_b": {"g": G_B, "mV_gev": MV, "m1_gev": M1_B,
                           "m2_gev": 0.0},
            },
            "verification": "analytic formulas reproduced to <1e-9 by "
                            "independent numeric computation with explicit "
                            "polarization vectors",
            "citations": [
                "M.D. Schwartz, Quantum Field Theory and the Standard "
                "Model, scalar-QED vertex i g (p1-p2)_mu",
                "J.J. Sakurai, Currents and Mesons (rho -> pi pi, p-wave "
                "vector-to-two-scalar rate)",
            ],
        },
    }
    OUT.write_text(json.dumps(truth, indent=2) + "\n")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
