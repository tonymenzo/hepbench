"""
# benchmarks/symbolic/xsec_FFbar_to_FFbar/ground_truth/derivation.py is a part of HEPBench.
# Copyright (C) 2026 HEPBench authors (see AUTHORS for details).
# HEPBench is licensed under the GNU GPL v3 or later, see LICENSE for details.
"""
"""
Ground truth for xsec_FFbar_to_FFbar: tree-level s-channel annihilation
of a massless Dirac fermion pair into a distinct massless Dirac fermion
pair (no t-channel; the two species couple only through the mediator).
Spin-averaged over the four initial spin states.

Part (a)  MASSLESS vector mediator (QED-like):
    L = g V_mu (psibar_1 gamma^mu psi_1 + psibar_2 gamma^mu psi_2)
    sigma(psi_1 psibar_1 -> psi_2 psibar_2) = g^4 / (12 pi s)
    Literature: this is e+ e- -> mu+ mu- with g -> e:
    sigma = 4 pi alpha^2 / (3 s), alpha = e^2/(4 pi), M.E. Peskin,
    D.V. Schroeder, "An Introduction to Quantum Field Theory",
    eq. (5.13).

Part (b)  HEAVY scalar mediator (off resonance, s < M_S^2):
    L = - y1 phi psibar_1 psi_1 - y2 phi psibar_2 psi_2,
    phi mass M_S, width negligible
    M = y1 y2 / (s - M_S^2) [vbar_1 u_1][ubar_2 v_2];
    <|M|^2> = (1/4) (y1 y2)^2 / (s - M_S^2)^2 * Tr[p2 p1] Tr[p3 p4]
            = (y1 y2)^2 s^2 / (4 (s - M_S^2)^2) * ... = isotropic, and
    sigma = y1^2 y2^2 s / (16 pi (s - M_S^2)^2)
    Literature: the scalar s-channel structure (isotropic, no 1 +
    cos^2 theta) is the standard contrast to the vector case, cf. the
    s-channel Higgs exchange amplitudes worked in P&S ch. 5 / final
    project, and muon-collider s-channel Higgs studies; the
    coefficient here is fixed by the trace algebra in this docstring
    and verified numerically below.

Both parts verified against the independent numeric angular
integration of explicit-spinor amplitudes in _shared/dirac_numeric.py
(the same machinery that reproduces P&S eq. (5.13) in tests/).

Numeric answers are requested in picobarns
(1 GeV^-2 = 3.893793721e8 pb, PDG).

Run from the repo root:
    python benchmarks/symbolic/xsec_FFbar_to_FFbar/ground_truth/derivation.py
"""

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))
import dirac_numeric as dn  # noqa: E402

OUT = Path(__file__).resolve().parent / "truth.json"

# --- task parameters (quoted in the prompt) ---
RS = 730.0
S = RS * RS
G_A = 0.55                      # part (a): massless vector mediator
Y1, Y2, MSC = 0.92, 0.34, 1900.0  # part (b): heavy scalar mediator


def analytic_a_gev2():
    return G_A**4 / (12 * np.pi * S)


def analytic_b_gev2():
    return Y1**2 * Y2**2 * S / (16 * np.pi * (S - MSC**2)**2)


def numeric_a_gev2():
    def msq(p1, p2, p3, p4):
        total = 0.0
        for s1 in (0, 1):
            for s2 in (0, 1):
                c1 = [dn.vbar(p2, 0.0, s2) @ dn.GAMMA[k]
                      @ dn.u_spinor(p1, 0.0, s1) for k in range(4)]
                for s3 in (0, 1):
                    for s4 in (0, 1):
                        c2 = [dn.ubar(p3, 0.0, s3) @ dn.GAMMA[k]
                              @ dn.v_spinor(p4, 0.0, s4) for k in range(4)]
                        amp = (G_A * G_A / S) * (
                            c1[0] * c2[0] - c1[1] * c2[1]
                            - c1[2] * c2[2] - c1[3] * c2[3])
                        total += abs(amp) ** 2
        return total / 4.0
    return dn.two_to_two_xsec(S, 0, 0, 0, 0, msq, n=400)


def numeric_b_gev2():
    pref = Y1 * Y2 / (S - MSC**2)

    def msq(p1, p2, p3, p4):
        total = 0.0
        for s1 in (0, 1):
            for s2 in (0, 1):
                c1 = dn.vbar(p2, 0.0, s2) @ dn.u_spinor(p1, 0.0, s1)
                for s3 in (0, 1):
                    for s4 in (0, 1):
                        c2 = dn.ubar(p3, 0.0, s3) @ dn.v_spinor(p4, 0.0, s4)
                        total += abs(pref * c1 * c2) ** 2
        return total / 4.0
    return dn.two_to_two_xsec(S, 0, 0, 0, 0, msq, n=400)


def main():
    rows = [
        ("part_a", analytic_a_gev2(), numeric_a_gev2(), 1e-4),
        ("part_b", analytic_b_gev2(), numeric_b_gev2(), 1e-10),
    ]
    for name, ana, num, tol in rows:
        rel = abs(ana - num) / ana
        print(f"{name}: analytic {ana:.10g} GeV^-2  numeric {num:.10g}  "
              f"rel {rel:.2e}")
        assert rel < tol, f"{name}: analytic vs numeric mismatch"

    truth = {
        "part_a_xsec_pb": analytic_a_gev2() * dn.GEV2_TO_PB,
        "part_a_xsec_formula": "g**4 / (12*pi*s)",
        "part_b_xsec_pb": analytic_b_gev2() * dn.GEV2_TO_PB,
        "part_b_xsec_formula":
            "y1**2 * y2**2 * s / (16*pi*(s - MS**2)**2)",
        "_metadata": {
            "generated_by": "ground_truth/derivation.py",
            "parameters": {
                "common": {"sqrt_s_gev": RS, "fermion_masses_gev": 0.0},
                "part_a": {"g": G_A},
                "part_b": {"y1": Y1, "y2": Y2, "MS_gev": MSC},
            },
            "units": "values in pb (1 GeV^-2 = 3.893793721e8 pb); "
                     "formulas in natural units (GeV^-2)",
            "verification": "part (a) reproduced to <1e-4 (angular grid) "
                            "and part (b) to <1e-10 by independent numeric "
                            "integration of explicit-spinor amplitudes",
            "citations": [
                "M.E. Peskin, D.V. Schroeder, An Introduction to QFT, "
                "eq. (5.13) (e+e- -> mu+mu-, with g -> e)",
                "P&S ch. 5 (s-channel scalar exchange: isotropic "
                "angular distribution)",
            ],
        },
    }
    OUT.write_text(json.dumps(truth, indent=2) + "\n")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
