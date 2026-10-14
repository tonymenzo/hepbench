"""
# benchmarks/symbolic/decay_F_to_FpV/ground_truth/derivation.py is a part of HEPBench.
# Copyright (C) 2026 HEPBench authors (see AUTHORS for details).
# HEPBench is licensed under the GNU GPL v3 or later, see LICENSE for details.
"""
"""
Ground truth for decay_F_to_FpV: tree-level two-body width of a heavy
Dirac fermion F (mass m_F) into a lighter Dirac fermion f (mass m_f) and
a massive vector V (mass m_V). Initial spin averaged (1/2); the vector's
three polarizations are summed via the completeness relation
sum_pol eps^mu eps*^nu = -eta^munu + q^mu q^nu / m_V^2 (CONVENTIONS.md
sec. 3).

Interaction  L = fbar gamma^mu (g_L P_L + g_R P_R) F V_mu + h.c.

Spin-averaged squared amplitude (the antisymmetric epsilon term in the
trace drops against the symmetric polarization tensor, so it does not
enter the total rate):
    <|M|^2> = (g_L^2 + g_R^2) * A - 6 m_F m_f g_L g_R,
    A = (1/2)[ m_F^2 + m_f^2 - 2 m_V^2 + (m_F^2 - m_f^2)^2 / m_V^2 ].
    Gamma = sqrt(lambda(m_F^2, m_f^2, m_V^2)) / (16 pi m_F^3) * <|M|^2>.

Part (a) pure vector coupling g_L = g_R = g:
    <|M|^2> = g^2 [ m_F^2 + m_f^2 - 2 m_V^2 + (m_F^2-m_f^2)^2/m_V^2
                   - 6 m_F m_f ].

Part (b) general chiral (g_L, g_R independent).

Literature / cross-check: in the limit g_R = 0, m_f -> 0,
g_L = g/sqrt(2) this reproduces the Standard-Model top-quark width
    Gamma(t -> b W) = (g^2 / 64 pi)(m_t^3/m_W^2)(1 - x)^2 (1 + 2x),
    x = m_W^2/m_t^2,
the textbook result (e.g. A. Denner, "Techniques for the calculation of
electroweak radiative corrections...", Fortsch.Phys. 41 (1993) 307; PDG
Top Quark review, born-level width). That reduction is asserted below in
addition to the full numeric check (explicit Dirac spinors + explicit
massive-vector polarization vectors, _shared/dirac_numeric.py).

Run from the repo root:
    python benchmarks/symbolic/decay_F_to_FpV/ground_truth/derivation.py
"""

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))
import dirac_numeric as dn  # noqa: E402

OUT = Path(__file__).resolve().parent / "truth.json"

# --- task parameters (quoted in the prompt) ---
MF, MFP, MV = 900.0, 180.0, 240.0   # parent fermion, daughter fermion, vector
G_A = 0.74                           # part (a) pure vector
GL, GR = 0.58, 0.29                  # part (b) chiral


def _A():
    return 0.5 * (MF**2 + MFP**2 - 2 * MV**2 + (MF**2 - MFP**2)**2 / MV**2)


def analytic_a():
    lam = dn.kallen(MF**2, MFP**2, MV**2)
    msq = G_A**2 * (MF**2 + MFP**2 - 2 * MV**2
                    + (MF**2 - MFP**2)**2 / MV**2 - 6 * MF * MFP)
    return np.sqrt(lam) / (16 * np.pi * MF**3) * msq


def analytic_b():
    lam = dn.kallen(MF**2, MFP**2, MV**2)
    msq = (GL**2 + GR**2) * _A() - 6 * MF * MFP * GL * GR
    return np.sqrt(lam) / (16 * np.pi * MF**3) * msq


def _numeric(gL, gR):
    """(1/2) sum_{F spin, f spin, V pol} |fbar gamma.eps* (gL PL+gR PR) uF|^2,
    integrated by the two-body master formula. Daughter 1 = fermion f,
    daughter 2 = vector V."""
    P = np.array([MF, 0.0, 0.0, 0.0])
    vert = gL * dn.PL + gR * dn.PR

    def msq(p1, p2):
        eps = dn.pol_vectors(p2, MV)
        total = 0.0
        for sP in (0, 1):
            uF = dn.u_spinor(P, MF, sP)
            for s1 in (0, 1):
                for ev in eps:
                    gam = sum(np.conjugate(ev[mu]) * dn.ETA[mu, mu]
                              * (dn.GAMMA[mu] @ vert) for mu in range(4))
                    amp = dn.ubar(p1, MFP, s1) @ gam @ uF
                    total += abs(amp) ** 2
        return total / 2.0
    return dn.two_body_width(MF, MFP, MV, msq)


def _sm_top_check():
    """g_R=0, m_f=0: must equal (g^2/64pi)(mF^3/mV^2)(1-x)^2(1+2x)."""
    g = 0.65
    x = MV**2 / MF**2
    lam = dn.kallen(MF**2, 0.0, MV**2)
    msq = (g / np.sqrt(2))**2 * 0.5 * (MF**2 - 2 * MV**2 + MF**4 / MV**2)
    full = np.sqrt(lam) / (16 * np.pi * MF**3) * msq
    textbook = g**2 / (64 * np.pi) * MF**3 / MV**2 * (1 - x)**2 * (1 + 2 * x)
    return full, textbook


def main():
    rows = [("part_a_width_gev", analytic_a(), _numeric(G_A, G_A)),
            ("part_b_width_gev", analytic_b(), _numeric(GL, GR))]
    for name, ana, num in rows:
        rel = abs(ana - num) / ana
        print(f"{name}: analytic {ana:.10g}  numeric {num:.10g}  rel {rel:.2e}")
        assert rel < 1e-9, f"{name}: analytic vs numeric mismatch"

    full, tb = _sm_top_check()
    print(f"SM t->bW reduction: derived {full:.10g}  textbook {tb:.10g}  "
          f"rel {abs(full-tb)/tb:.2e}")
    assert abs(full - tb) / tb < 1e-12

    truth = {
        "part_a_width_gev": analytic_a(),
        "part_a_width_formula":
            "sqrt((mF**2-(mf+mV)**2)*(mF**2-(mf-mV)**2))/(16*pi*mF**3)"
            " * g**2 * (mF**2 + mf**2 - 2*mV**2 + (mF**2-mf**2)**2/mV**2"
            " - 6*mF*mf)",
        "part_b_width_gev": analytic_b(),
        "part_b_width_formula":
            "sqrt((mF**2-(mf+mV)**2)*(mF**2-(mf-mV)**2))/(16*pi*mF**3)"
            " * ((gL**2+gR**2)"
            "*(mF**2+mf**2-2*mV**2+(mF**2-mf**2)**2/mV**2)/2"
            " - 6*mF*mf*gL*gR)",
        "_metadata": {
            "generated_by": "ground_truth/derivation.py",
            "conventions": "../CONVENTIONS.md",
            "parameters": {
                "common": {"mF_gev": MF, "mf_gev": MFP, "mV_gev": MV},
                "part_a": {"g": G_A}, "part_b": {"gL": GL, "gR": GR},
            },
            "verification": "analytic formulas reproduced to <1e-9 by "
                            "independent numeric computation with explicit "
                            "Dirac spinors and massive-vector polarization "
                            "vectors; reduces to the textbook t->bW width "
                            "in the g_R=0, m_f=0 limit",
            "citations": [
                "A. Denner, Fortsch.Phys. 41 (1993) 307 (gauge-boson "
                "fermionic widths)",
                "PDG, Top Quark review (born-level Gamma(t->bW) = "
                "(g^2/64pi)(m_t^3/m_W^2)(1-x)^2(1+2x))",
            ],
        },
    }
    OUT.write_text(json.dumps(truth, indent=2) + "\n")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
