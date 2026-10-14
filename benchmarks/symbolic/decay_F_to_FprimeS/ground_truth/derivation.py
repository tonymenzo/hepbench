"""
# benchmarks/symbolic/decay_F_to_FprimeS/ground_truth/derivation.py is a part of HEPBench.
# Copyright (C) 2026 HEPBench authors (see AUTHORS for details).
# HEPBench is licensed under the GNU GPL v3 or later, see LICENSE for details.
"""
"""
Ground truth for decay_F_to_FprimeS: tree-level two-body width of a
heavy Dirac fermion Psi (mass m_F) into a lighter Dirac fermion psi
(mass m_f) and a real scalar phi (mass m_S). Initial spin is averaged
(factor 1/2); lambda is the Kallen function.

Part (a)  L = - y phi psibar Psi + h.c.   (scalar Yukawa)
    (1/2) Sum_spins |M|^2 = (y^2/2) (4 P.p1 + 4 m_F m_f)
                          = y^2 [ (m_F + m_f)^2 - m_S^2 ]
    with 2 P.p1 = m_F^2 + m_f^2 - m_S^2, giving
    Gamma = y^2 sqrt(lambda(m_F^2, m_f^2, m_S^2)) / (16 pi m_F^3)
            * [ (m_F + m_f)^2 - m_S^2 ]

Part (b)  L = - phi psibar (yL PL + yR PR) Psi + h.c.   (chiral)
    Gamma = sqrt(lambda(m_F^2, m_f^2, m_S^2)) / (32 pi m_F^3)
            * [ (yL^2 + yR^2)(m_F^2 + m_f^2 - m_S^2)
                + 4 yL yR m_F m_f ]
    Part (a) is the yL = yR = y limit.

Literature: this is the structure of the top decay t -> b H+ and of
heavy vector-like-fermion decays F -> f S:
  - A. Djouadi, "The anatomy of electroweak symmetry breaking II",
    Phys.Rept. 459 (2008), arXiv:hep-ph/0503173, sec. 1.3.4 (the
    t -> b H+ width, with (yL, yR) -> g/(sqrt(2) M_W) x
    (m_t cot(beta), m_b tan(beta)));
  - J.A. Aguilar-Saavedra, "Identifying top partners at LHC",
    JHEP 0911:030 (2009), arXiv:0907.3155, appendix (partial widths
    of heavy quarks into q + scalar).

Verified against the independent numeric Dirac-spinor computation in
_shared/dirac_numeric.py.

Run from the repo root:
    python benchmarks/symbolic/decay_F_to_FprimeS/ground_truth/derivation.py
"""

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))
import dirac_numeric as dn  # noqa: E402

OUT = Path(__file__).resolve().parent / "truth.json"

# --- task parameters (quoted in the prompt) ---
MF, MFP, MS = 880.0, 130.0, 340.0    # parent, daughter fermion, scalar
Y_A = 0.66                            # part (a)
YL, YR = 0.45, 0.18                   # part (b)


def analytic_a():
    lam = dn.kallen(MF**2, MFP**2, MS**2)
    return Y_A**2 * np.sqrt(lam) / (16 * np.pi * MF**3) * (
        (MF + MFP)**2 - MS**2)


def analytic_b():
    lam = dn.kallen(MF**2, MFP**2, MS**2)
    return np.sqrt(lam) / (32 * np.pi * MF**3) * (
        (YL**2 + YR**2) * (MF**2 + MFP**2 - MS**2) + 4 * YL * YR * MF * MFP)


def _msq(vertex):
    """(1/2) sum_spins |ubar(p1) V u(P)|^2 with the parent at rest."""
    P = np.array([MF, 0.0, 0.0, 0.0])

    def msq(p1, p2):
        total = 0.0
        for sF in (0, 1):
            uF = dn.u_spinor(P, MF, sF)
            for s1 in (0, 1):
                amp = dn.ubar(p1, MFP, s1) @ vertex @ uF
                total += abs(amp) ** 2
        return total / 2.0
    return msq


def numeric_a():
    return dn.two_body_width(MF, MFP, MS, _msq(Y_A * dn.ID4))


def numeric_b():
    return dn.two_body_width(MF, MFP, MS, _msq(YL * dn.PL + YR * dn.PR))


def main():
    rows = [
        ("part_a_width_gev", analytic_a(), numeric_a()),
        ("part_b_width_gev", analytic_b(), numeric_b()),
    ]
    for name, ana, num in rows:
        rel = abs(ana - num) / ana
        print(f"{name}: analytic {ana:.10g}  numeric {num:.10g}  rel {rel:.2e}")
        assert rel < 1e-10, f"{name}: analytic vs numeric mismatch"

    # consistency: (b) with yL = yR = y must reproduce (a)
    lam = dn.kallen(MF**2, MFP**2, MS**2)
    b_at_a = np.sqrt(lam) / (32 * np.pi * MF**3) * (
        2 * Y_A**2 * (MF**2 + MFP**2 - MS**2) + 4 * Y_A**2 * MF * MFP)
    assert abs(b_at_a - analytic_a()) / analytic_a() < 1e-12

    truth = {
        "part_a_width_gev": analytic_a(),
        "part_a_width_formula":
            "y**2 * sqrt((mF**2 - (mf + mS)**2) * (mF**2 - (mf - mS)**2))"
            " / (16*pi*mF**3) * ((mF + mf)**2 - mS**2)",
        "part_b_width_gev": analytic_b(),
        "part_b_width_formula":
            "sqrt((mF**2 - (mf + mS)**2) * (mF**2 - (mf - mS)**2))"
            " / (32*pi*mF**3)"
            " * ((yL**2 + yR**2)*(mF**2 + mf**2 - mS**2)"
            " + 4*yL*yR*mF*mf)",
        "_metadata": {
            "generated_by": "ground_truth/derivation.py",
            "parameters": {
                "common": {"mF_gev": MF, "mf_gev": MFP, "mS_gev": MS},
                "part_a": {"y": Y_A},
                "part_b": {"yL": YL, "yR": YR},
            },
            "verification": "analytic formulas reproduced to <1e-10 by "
                            "independent numeric Dirac-spinor computation; "
                            "(b) reproduces (a) at yL = yR = y",
            "citations": [
                "A. Djouadi, Phys.Rept. 459 (2008), arXiv:hep-ph/0503173, "
                "sec. 1.3.4 (t -> b H+, chiral structure)",
                "J.A. Aguilar-Saavedra, JHEP 0911:030 (2009), "
                "arXiv:0907.3155, appendix (heavy-fermion -> fermion + "
                "scalar partial widths)",
            ],
        },
    }
    OUT.write_text(json.dumps(truth, indent=2) + "\n")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
