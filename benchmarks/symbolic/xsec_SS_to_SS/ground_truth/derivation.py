"""
# benchmarks/symbolic/xsec_SS_to_SS/ground_truth/derivation.py is a part of HEPBench.
# Copyright (C) 2026 HEPBench authors (see AUTHORS for details).
# HEPBench is licensed under the GNU GPL v3 or later, see LICENSE for details.
"""
"""
Ground truth for xsec_SS_to_SS: tree-level 2 -> 2 scalar scattering
cross sections from quartic contact interactions. The content is the
vertex combinatorics (4!/4 conventions), the identical-particle factor
in the total cross section, and the flux/phase-space ratio |p_f|/|p_i|.

Master formula (c.m. frame): dsigma/dOmega = |M|^2 |p_f| /
(64 pi^2 s |p_i|), M.E. Peskin, D.V. Schroeder, "An Introduction to
Quantum Field Theory", eq. (4.84); total cross sections for identical
final particles carry an extra 1/2 (P&S below eq. (4.85); PDG
Kinematics review).

Part (a)  L = -(lambda/4!) phi^4, process phi phi -> phi phi
    Feynman rule: -i lambda (the 4! is eaten by the contractions);
    |M|^2 = lambda^2, |p_f| = |p_i|:
    sigma = lambda^2 / (32 pi s)            [exact for s >= 4 m_phi^2]
    Literature: the -i lambda rule and |M| = -lambda for phi^4 at tree
    level: P&S sec. 4.6 (and figure below eq. (4.104)); M. Srednicki,
    "Quantum Field Theory", ch. 11 master formulas.

Part (b)  L = -(lambda12/4) phi^2 chi^2, process phi phi -> chi chi
    Feynman rule: -i lambda12 (2! * 2! / 4 = 1); |M|^2 = lambda12^2:
    sigma = lambda12^2 / (32 pi s)
            * sqrt((s - 4 m_chi^2) / (s - 4 m_phi^2))
    The sqrt is |p_f|/|p_i|; the 1/2 is the identical chi chi pair.

Verified against the independent numeric angular integration in
_shared/dirac_numeric.py (constant |M|^2, identical=True).

Numeric answers are requested in picobarns; the conversion
1 GeV^-2 = 3.893793721e8 pb uses the PDG value of (hbar c)^2.

Run from the repo root:
    python benchmarks/symbolic/xsec_SS_to_SS/ground_truth/derivation.py
"""

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))
import dirac_numeric as dn  # noqa: E402

OUT = Path(__file__).resolve().parent / "truth.json"

# --- task parameters (quoted in the prompt) ---
LAM_A, MPHI, RS = 2.3, 75.0, 480.0       # part (a)
LAM_B, MCHI = 1.7, 210.0                  # part (b); same mphi, sqrt(s)
S = RS * RS


def analytic_a_gev2():
    return LAM_A**2 / (32 * np.pi * S)


def analytic_b_gev2():
    return LAM_B**2 / (32 * np.pi * S) * np.sqrt(
        (S - 4 * MCHI**2) / (S - 4 * MPHI**2))


def numeric_a_gev2():
    return dn.two_to_two_xsec(S, MPHI, MPHI, MPHI, MPHI,
                              lambda p1, p2, p3, p4: LAM_A**2,
                              identical=True)


def numeric_b_gev2():
    return dn.two_to_two_xsec(S, MPHI, MPHI, MCHI, MCHI,
                              lambda p1, p2, p3, p4: LAM_B**2,
                              identical=True)


def main():
    rows = [
        ("part_a", analytic_a_gev2(), numeric_a_gev2()),
        ("part_b", analytic_b_gev2(), numeric_b_gev2()),
    ]
    for name, ana, num in rows:
        rel = abs(ana - num) / ana
        print(f"{name}: analytic {ana:.10g} GeV^-2  numeric {num:.10g}  "
              f"rel {rel:.2e}")
        assert rel < 1e-10, f"{name}: analytic vs numeric mismatch"

    truth = {
        "part_a_xsec_pb": analytic_a_gev2() * dn.GEV2_TO_PB,
        "part_a_xsec_formula": "lam**2 / (32*pi*s)",
        "part_b_xsec_pb": analytic_b_gev2() * dn.GEV2_TO_PB,
        "part_b_xsec_formula":
            "lam**2 / (32*pi*s)"
            " * sqrt((s - 4*mchi**2) / (s - 4*mphi**2))",
        "_metadata": {
            "generated_by": "ground_truth/derivation.py",
            "parameters": {
                "part_a": {"lambda": LAM_A, "mphi_gev": MPHI,
                           "sqrt_s_gev": RS},
                "part_b": {"lambda12": LAM_B, "mphi_gev": MPHI,
                           "mchi_gev": MCHI, "sqrt_s_gev": RS},
            },
            "units": "values in pb (1 GeV^-2 = 3.893793721e8 pb); "
                     "formulas in natural units (GeV^-2)",
            "verification": "analytic formulas reproduced to <1e-10 by "
                            "independent numeric angular integration "
                            "(_shared/dirac_numeric.py)",
            "citations": [
                "M.E. Peskin, D.V. Schroeder, An Introduction to QFT, "
                "eq. (4.84) (c.m. dsigma/dOmega) and sec. 4.6 "
                "(-i lambda rule for phi^4)",
                "M. Srednicki, Quantum Field Theory, ch. 11 "
                "(2->2 master formulas)",
                "PDG, Kinematics review (identical-particle 1/2; "
                "(hbar c)^2 conversion)",
            ],
        },
    }
    OUT.write_text(json.dumps(truth, indent=2) + "\n")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
