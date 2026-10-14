"""
# benchmarks/symbolic/decay_F_to_3body/ground_truth/derivation.py is a part of HEPBench.
# Copyright (C) 2026 HEPBench authors (see AUTHORS for details).
# HEPBench is licensed under the GNU GPL v3 or later, see LICENSE for details.
"""
"""
Ground truth for decay_F_to_3body: three-body decay of a heavy Dirac
fermion F (mass m_F) into three massless Dirac fermions through a HEAVY
mediator (M >> m_F), at leading order in m_F / M. The muon-decay
topology with generic couplings.

Master phase-space integral (massless finals; PDG-normalized dPhi_3,
parent at rest, {b, c} the pair complementary to a):
    I = Int dPhi_3 (P.p_a)(p_b.p_c) = m_F^6 / (6144 pi^3)
Derivation (factorized recursion): with s = (p_b + p_c)^2,
p_b.p_c = s/2 and P.p_a = (m^2 - s)/2;
Int dPhi_2(bc) = 1/(8 pi); Int dPhi_2(F -> a X_s) = (m^2 - s)/(8 pi m^2);
I = Int_0^{m^2} ds/(2 pi) * [(m^2-s)/(8 pi m^2)] * (1/(8 pi))
        * [(m^2-s)/2] * [s/2]
  = m^6/(512 pi^3 m^2) * Int_0^1 x (1-x)^2 dx * m^4 ... = m^6/(6144 pi^3).
Calibration against the muon: with <|M|^2> = 64 G_F^2 (P.p_a)(p_b.p_c)
this gives Gamma = (1/2m) * 64 G_F^2 * I = G_F^2 m^5 / (192 pi^3) —
the textbook muon width, which tests/test_symbolic_dirac_numeric.py
reproduces numerically from explicit spinors.

Part (a)  heavy VECTOR mediator, left-handed couplings:
    L = g V_mu (psibar_a gamma^mu P_L Psi)
      + g V_mu (psibar_b gamma^mu P_L psi_c) + h.c.,  M_V >> m_F
    Contact limit: M = (g^2/M_V^2) [ubar_a gamma^mu P_L u_F]
                                   [ubar_b gamma_mu P_L v_c],
    <|M|^2> = 8 (g^2/M_V^2)^2 (P.p_a)(p_b.p_c)   [muon trace, with
    2 sqrt(2) G_F <-> g^2/M_V^2]
    Gamma = g^4 m_F^5 / (1536 pi^3 M_V^4)
    (Equivalently: G_eff = g^2 / (2 sqrt(2) M_V^2) in the Fermi form.)

Part (b)  heavy SCALAR mediator, Yukawa couplings:
    L = - y1 phi (psibar_a Psi) - y2 phi (psibar_b psi_c) + h.c.,
    M_S >> m_F
    Contact limit: M = (y1 y2 / M_S^2) [ubar_a u_F][ubar_b v_c],
    Sum |M|^2 = (y1 y2/M_S^2)^2 Tr[(slash_P + m_F) slash_p_a]
                               * Tr[slash_p_b slash_p_c]
              = 16 (y1 y2/M_S^2)^2 (P.p_a)(p_b.p_c);  averaged: /2
    Gamma = y1^2 y2^2 m_F^5 / (1536 pi^3 M_S^4)
    The identical 1536 is NOT generic — it follows from the two squared
    currents reducing to the same (P.p_a)(p_b.p_c) pairing.

Literature: the muon width Gamma = G_F^2 m_mu^5 / (192 pi^3) and the
matching G_F / sqrt(2) = g_w^2 / (8 M_W^2): F. Halzen, A.D. Martin,
"Quarks and Leptons", ch. 12; PDG, "Electroweak model and constraints
on new physics" review; M.E. Peskin, D.V. Schroeder, sec. 5.? (muon
lifetime is worked as an example of (V-A)x(V-A) contact theory in most
texts). The scalar-mediator coefficient is fixed by the master
integral above and verified numerically below.

Both parts are verified against the independent numeric Dalitz
integration of the explicit-spinor contact amplitudes in
_shared/dirac_numeric.py.

Run from the repo root:
    python benchmarks/symbolic/decay_F_to_3body/ground_truth/derivation.py
"""

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))
import dirac_numeric as dn  # noqa: E402

OUT = Path(__file__).resolve().parent / "truth.json"

# --- task parameters (quoted in the prompt) ---
MFERM = 17.3            # parent mass (GeV); finals massless
G_A, MV = 0.62, 1450.0  # part (a): vector mediator
Y1, Y2, MSC = 0.71, 0.58, 1450.0  # part (b): scalar mediator


def analytic_a():
    return G_A**4 * MFERM**5 / (1536 * np.pi**3 * MV**4)


def analytic_b():
    return (Y1 * Y2)**2 * MFERM**5 / (1536 * np.pi**3 * MSC**4)


def numeric_a():
    pref = G_A * G_A / (MV * MV)
    P = np.array([MFERM, 0.0, 0.0, 0.0])

    def msq(p1, p2, p3):
        # p1 = a, p2 = b, p3 = cbar
        total = 0.0
        for sF in (0, 1):
            uF = dn.u_spinor(P, MFERM, sF)
            for s1 in (0, 1):
                c1 = [dn.ubar(p1, 0.0, s1) @ dn.GAMMA[k] @ dn.PL @ uF
                      for k in range(4)]
                for s2 in (0, 1):
                    for s3 in (0, 1):
                        c2 = [dn.ubar(p2, 0.0, s2) @ dn.GAMMA[k] @ dn.PL
                              @ dn.v_spinor(p3, 0.0, s3) for k in range(4)]
                        amp = pref * (c1[0] * c2[0] - c1[1] * c2[1]
                                      - c1[2] * c2[2] - c1[3] * c2[3])
                        total += abs(amp) ** 2
        return total / 2.0
    return dn.three_body_width(MFERM, 0.0, 0.0, 0.0, msq, n12=200, n23=200)


def numeric_b():
    pref = Y1 * Y2 / (MSC * MSC)
    P = np.array([MFERM, 0.0, 0.0, 0.0])

    def msq(p1, p2, p3):
        total = 0.0
        for sF in (0, 1):
            uF = dn.u_spinor(P, MFERM, sF)
            for s1 in (0, 1):
                c1 = dn.ubar(p1, 0.0, s1) @ uF
                for s2 in (0, 1):
                    for s3 in (0, 1):
                        c2 = dn.ubar(p2, 0.0, s2) @ dn.v_spinor(p3, 0.0, s3)
                        total += abs(pref * c1 * c2) ** 2
        return total / 2.0
    return dn.three_body_width(MFERM, 0.0, 0.0, 0.0, msq, n12=200, n23=200)


def main():
    rows = [
        ("part_a_width_gev", analytic_a(), numeric_a()),
        ("part_b_width_gev", analytic_b(), numeric_b()),
    ]
    for name, ana, num in rows:
        rel = abs(ana - num) / ana
        print(f"{name}: analytic {ana:.10g}  numeric {num:.10g}  rel {rel:.2e}")
        assert rel < 1e-3, f"{name}: analytic vs numeric mismatch"

    truth = {
        "part_a_width_gev": analytic_a(),
        "part_a_width_formula":
            "g**4 * mF**5 / (1536*pi**3 * MV**4)",
        "part_b_width_gev": analytic_b(),
        "part_b_width_formula":
            "y1**2 * y2**2 * mF**5 / (1536*pi**3 * MS**4)",
        "_metadata": {
            "generated_by": "ground_truth/derivation.py",
            "parameters": {
                "common": {"mF_gev": MFERM, "final_masses_gev": 0.0},
                "part_a": {"g": G_A, "MV_gev": MV},
                "part_b": {"y1": Y1, "y2": Y2, "MS_gev": MSC},
            },
            "verification": "analytic coefficients reproduced to <1e-3 "
                            "(midpoint Dalitz grid) by independent numeric "
                            "integration of explicit-spinor contact "
                            "amplitudes; integrator itself reproduces the "
                            "muon width in tests/",
            "citations": [
                "F. Halzen, A.D. Martin, Quarks and Leptons, ch. 12 "
                "(muon decay, G_F^2 m^5/(192 pi^3))",
                "PDG, Electroweak model review (G_F/sqrt(2) = "
                "g_w^2/(8 M_W^2) matching)",
                "M.E. Peskin, D.V. Schroeder, An Introduction to QFT "
                "(V-A contact theory of weak decays)",
            ],
        },
    }
    OUT.write_text(json.dumps(truth, indent=2) + "\n")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
