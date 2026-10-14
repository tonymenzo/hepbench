"""
# benchmarks/symbolic/decay_S_to_FFbar/ground_truth/derivation.py is a part of HEPBench.
# Copyright (C) 2026 HEPBench authors (see AUTHORS for details).
# HEPBench is licensed under the GNU GPL v3 or later, see LICENSE for details.
"""
"""
Ground truth for decay_S_to_FFbar: tree-level two-body widths of a real
scalar phi into fermion pairs, for three interaction structures.

Conventions: all Lagrangian terms are stated explicitly in the task
prompt; couplings are real; widths are partial widths in GeV for the
single specified final state. beta = sqrt(1 - 4 m_f^2 / m_S^2);
lambda(a,b,c) = a^2 + b^2 + c^2 - 2ab - 2bc - 2ca (Kallen).

Part (a)  L = - y phi psibar psi          (scalar Yukawa)
    Gamma = y^2 m_S beta^3 / (8 pi)
    Literature: this is the textbook H -> f fbar width with the SM
    identification y = m_f (sqrt(2) G_F)^(1/2):
    Gamma(H -> f fbar) = G_F N_c m_H m_f^2 / (4 sqrt(2) pi) * beta^3,
    A. Djouadi, "The anatomy of electroweak symmetry breaking I",
    Phys.Rept. 457 (2008), arXiv:hep-ph/0503172, sec. 2.3 (decays to
    quarks and leptons); also J.F. Gunion et al., "The Higgs Hunter's
    Guide", ch. 2. The beta^3 threshold law distinguishes the scalar
    coupling.

Part (b)  L = - i y phi psibar gamma_5 psi (pseudoscalar)
    Gamma = y^2 m_S beta / (8 pi)
    Literature: pseudoscalar A -> f fbar carries beta^1 (P-wave vs
    S-wave): Gamma(A -> f fbar) = G_F N_c m_A m_f^2 / (4 sqrt(2) pi) *
    beta, A. Djouadi, "The anatomy of electroweak symmetry breaking
    II", Phys.Rept. 459 (2008), arXiv:hep-ph/0503173, sec. 1.2.2.

Part (c)  L = - phi psibar_1 (yL PL + yR PR) psi_2 + h.c.  (chiral,
    distinct fermions; partial width for the single channel
    phi -> psi_1 psibar_2)
    Sum_spins |M|^2 = (yL^2 + yR^2)(m_S^2 - m_1^2 - m_2^2)
                      - 4 yL yR m_1 m_2
    Gamma = sqrt(lambda(m_S^2, m_1^2, m_2^2)) / (16 pi m_S^3)
            * [ (yL^2 + yR^2)(m_S^2 - m_1^2 - m_2^2) - 4 yL yR m_1 m_2 ]
    Literature: same structure as the charged-Higgs width
    Gamma(H+ -> t bbar), e.g. A. Djouadi, arXiv:hep-ph/0503173,
    sec. 1.3.4 (charged Higgs decays), with
    (yL, yR) -> g/(sqrt(2) M_W) (m_t cot(beta), m_b tan(beta)); the
    generic form is also implemented in HDECAY (A. Djouadi, J.
    Kalinowski, M. Spira, arXiv:hep-ph/9704448).

Every value below is cross-checked against an independent numeric
computation (explicit Dirac spinors + phase space) from
benchmarks/symbolic/_shared/dirac_numeric.py, whose conventions are
themselves anchored to textbook results in
tests/test_symbolic_dirac_numeric.py.

Run from the repo root:  python benchmarks/symbolic/decay_S_to_FFbar/ground_truth/derivation.py
"""

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))
import dirac_numeric as dn  # noqa: E402

OUT = Path(__file__).resolve().parent / "truth.json"

# --- task parameters (deliberately non-round; quoted in the prompt) ---
Y_A, MS, MF = 0.87, 1240.0, 320.0          # part (a) scalar
Y_B = 0.54                                  # part (b) pseudoscalar
YL, YR, M1, M2 = 0.31, 0.78, 410.0, 95.0   # part (c) chiral


def analytic_a():
    beta = np.sqrt(1 - 4 * MF**2 / MS**2)
    return Y_A**2 * MS * beta**3 / (8 * np.pi)


def analytic_b():
    beta = np.sqrt(1 - 4 * MF**2 / MS**2)
    return Y_B**2 * MS * beta / (8 * np.pi)


def analytic_c():
    lam = dn.kallen(MS**2, M1**2, M2**2)
    return np.sqrt(lam) / (16 * np.pi * MS**3) * (
        (YL**2 + YR**2) * (MS**2 - M1**2 - M2**2) - 4 * YL * YR * M1 * M2)


def _msq_vertex(vertex, m1, m2):
    """Spin-summed |ubar(p1) V v(p2)|^2 at explicit momenta."""
    def msq(p1, p2):
        total = 0.0
        for s1 in (0, 1):
            for s2 in (0, 1):
                amp = dn.ubar(p1, m1, s1) @ vertex @ dn.v_spinor(p2, m2, s2)
                total += abs(amp) ** 2
        return total  # scalar parent: no initial-spin average
    return msq


def numeric_a():
    return dn.two_body_width(MS, MF, MF, _msq_vertex(Y_A * dn.ID4, MF, MF))


def numeric_b():
    # vertex -i y gamma5; |.|^2 kills the phase
    return dn.two_body_width(MS, MF, MF,
                             _msq_vertex(Y_B * dn.GAMMA5, MF, MF))


def numeric_c():
    vertex = YL * dn.PL + YR * dn.PR
    return dn.two_body_width(MS, M1, M2, _msq_vertex(vertex, M1, M2))


def main():
    rows = [
        ("part_a_width_gev", analytic_a(), numeric_a()),
        ("part_b_width_gev", analytic_b(), numeric_b()),
        ("part_c_width_gev", analytic_c(), numeric_c()),
    ]
    for name, ana, num in rows:
        rel = abs(ana - num) / ana
        print(f"{name}: analytic {ana:.10g}  numeric {num:.10g}  rel {rel:.2e}")
        assert rel < 1e-10, f"{name}: analytic vs numeric mismatch"

    truth = {
        "part_a_width_gev": analytic_a(),
        "part_a_width_formula":
            "y**2 * mS * (1 - 4*mf**2/mS**2)**(3/2) / (8*pi)",
        "part_b_width_gev": analytic_b(),
        "part_b_width_formula":
            "y**2 * mS * sqrt(1 - 4*mf**2/mS**2) / (8*pi)",
        "part_c_width_gev": analytic_c(),
        "part_c_width_formula":
            "sqrt((mS**2 - (m1 + m2)**2) * (mS**2 - (m1 - m2)**2))"
            " / (16*pi*mS**3)"
            " * ((yL**2 + yR**2)*(mS**2 - m1**2 - m2**2)"
            " - 4*yL*yR*m1*m2)",
        "_metadata": {
            "generated_by": "ground_truth/derivation.py",
            "parameters": {
                "part_a": {"y": Y_A, "mS_gev": MS, "mf_gev": MF},
                "part_b": {"y": Y_B, "mS_gev": MS, "mf_gev": MF},
                "part_c": {"yL": YL, "yR": YR, "mS_gev": MS,
                           "m1_gev": M1, "m2_gev": M2},
            },
            "verification": "analytic formulas reproduced to <1e-10 by "
                            "independent numeric Dirac-spinor computation "
                            "(_shared/dirac_numeric.py)",
            "citations": [
                "A. Djouadi, Phys.Rept. 457 (2008), arXiv:hep-ph/0503172, "
                "sec. 2.3 (H -> f fbar, beta^3)",
                "A. Djouadi, Phys.Rept. 459 (2008), arXiv:hep-ph/0503173, "
                "sec. 1.2.2 (A -> f fbar, beta^1) and sec. 1.3.4 "
                "(H+ -> t bbar, chiral structure)",
                "J.F. Gunion, H.E. Haber, G. Kane, S. Dawson, The Higgs "
                "Hunter's Guide, ch. 2",
                "A. Djouadi, J. Kalinowski, M. Spira (HDECAY), "
                "arXiv:hep-ph/9704448",
            ],
        },
    }
    OUT.write_text(json.dumps(truth, indent=2) + "\n")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
