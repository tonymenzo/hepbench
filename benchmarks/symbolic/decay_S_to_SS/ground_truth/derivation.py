"""
# benchmarks/symbolic/decay_S_to_SS/ground_truth/derivation.py is a part of HEPBench.
# Copyright (C) 2026 HEPBench authors (see AUTHORS for details).
# HEPBench is licensed under the GNU GPL v3 or later, see LICENSE for details.
"""
"""
Ground truth for decay_S_to_SS: tree-level two-body widths of a real
scalar phi into scalar pairs. The physics content is the constant
matrix element, the exact two-body phase space, and above all the
identical-particle symmetry factor in part (a).

Part (a)  L = -(mu/2) phi chi^2   (identical real scalars chi)
    Feynman rule: -i mu (the 1/2 is eaten by the two-fold functional
    derivative); |M|^2 = mu^2; symmetry factor S = 2.
    Gamma = mu^2 / (32 pi m_S) * sqrt(1 - 4 m_chi^2 / m_S^2)

Part (b)  L = -mu phi chi_1 chi_2  (distinct real scalars)
    Gamma = mu^2 sqrt(lambda(m_S^2, m_1^2, m_2^2)) / (16 pi m_S^3)

Literature: the constant-amplitude two-body width
Gamma = |M|^2 |p| / (8 pi M^2 S) is the master formula PDG eq. 50.18
(R.L. Workman et al. (Particle Data Group), Prog. Theor. Exp. Phys.
2022, 083C01, "Kinematics" review) including the 1/S statement for
identical particles; the toy-model decay A -> B C with a constant
coupling is worked in D. Griffiths, "Introduction to Elementary
Particles" (2nd ed.), sec. 6.3 ("the ABC theory"). The phi -> chi chi
symmetry-factor case appears in M.D. Schwartz, "Quantum Field Theory
and the Standard Model", ch. 5 examples.

Verified against _shared/dirac_numeric.py phase space (constant |M|^2,
explicit symmetry factor).

Run from the repo root:
    python benchmarks/symbolic/decay_S_to_SS/ground_truth/derivation.py
"""

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))
import dirac_numeric as dn  # noqa: E402

OUT = Path(__file__).resolve().parent / "truth.json"

# --- task parameters (quoted in the prompt) ---
MU_A, MS, MCHI = 480.0, 950.0, 270.0   # part (a), identical chi chi
MU_B, M1, M2 = 315.0, 350.0, 410.0     # part (b), distinct chi_1 chi_2


def analytic_a():
    beta = np.sqrt(1 - 4 * MCHI**2 / MS**2)
    return MU_A**2 * beta / (32 * np.pi * MS)


def analytic_b():
    lam = dn.kallen(MS**2, M1**2, M2**2)
    return MU_B**2 * np.sqrt(lam) / (16 * np.pi * MS**3)


def numeric_a():
    return dn.two_body_width(MS, MCHI, MCHI, lambda p1, p2: MU_A**2,
                             symmetry=2.0)


def numeric_b():
    return dn.two_body_width(MS, M1, M2, lambda p1, p2: MU_B**2)


def main():
    rows = [
        ("part_a_width_gev", analytic_a(), numeric_a()),
        ("part_b_width_gev", analytic_b(), numeric_b()),
    ]
    for name, ana, num in rows:
        rel = abs(ana - num) / ana
        print(f"{name}: analytic {ana:.10g}  numeric {num:.10g}  rel {rel:.2e}")
        assert rel < 1e-10, f"{name}: analytic vs numeric mismatch"

    truth = {
        "part_a_width_gev": analytic_a(),
        "part_a_width_formula":
            "mu**2 * sqrt(1 - 4*mchi**2/mS**2) / (32*pi*mS)",
        "part_b_width_gev": analytic_b(),
        "part_b_width_formula":
            "mu**2 * sqrt((mS**2 - (m1 + m2)**2) * (mS**2 - (m1 - m2)**2))"
            " / (16*pi*mS**3)",
        "_metadata": {
            "generated_by": "ground_truth/derivation.py",
            "parameters": {
                "part_a": {"mu_gev": MU_A, "mS_gev": MS, "mchi_gev": MCHI},
                "part_b": {"mu_gev": MU_B, "mS_gev": MS,
                           "m1_gev": M1, "m2_gev": M2},
            },
            "verification": "analytic formulas reproduced to <1e-10 by "
                            "independent numeric phase-space computation "
                            "(_shared/dirac_numeric.py)",
            "citations": [
                "PDG, Prog. Theor. Exp. Phys. 2022, 083C01, Kinematics "
                "review, eq. 50.18 (two-body width incl. 1/S)",
                "D. Griffiths, Introduction to Elementary Particles "
                "(2nd ed.), sec. 6.3 (ABC toy theory)",
                "M.D. Schwartz, Quantum Field Theory and the Standard "
                "Model, ch. 5 (phi -> chi chi with symmetry factor)",
            ],
        },
    }
    OUT.write_text(json.dumps(truth, indent=2) + "\n")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
