"""
# benchmarks/symbolic/composite_toy_model/ground_truth/derivation.py is a part of HEPBench.
# Copyright (C) 2026 HEPBench authors (see AUTHORS for details).
# HEPBench is licensed under the GNU GPL v3 or later, see LICENSE for details.
"""
"""
Ground truth for composite_toy_model: the full phenomenological profile
of one toy theory. A heavy real scalar Phi couples to two Dirac fermion
species and a light real scalar:

    L_int = - y1 Phi psibar_1 psi_1
            - y2 Phi psibar_2 psi_2
            - (mu/2) Phi chi^2

with m_Phi = 1850 GeV, m_1 = 230 GeV, m_2 = 0, m_chi = 410 GeV,
y1 = 0.42, y2 = 0.16, mu = 590 GeV.

Requested quantities (each an ingredient benchmark elsewhere in the
family; here they must be assembled consistently):
  - the three partial widths (decay_S_to_FFbar part (a) structure for
    the fermion channels; decay_S_to_SS part (a) for chi chi),
  - total width, branching ratios, lifetime in SECONDS
    (tau = hbar / Gamma, hbar = 6.582119569e-25 GeV s, PDG),
  - sigma(psi_2 psibar_2 -> psi_1 psibar_1) at sqrt(s) = 1100 GeV via
    s-channel Phi exchange (below resonance; Phi width negligible at
    this s), in pb. With massless initial fermions and beta_f the
    final-state velocity:
        sigma = y1^2 y2^2 s beta_f^3 / (16 pi (s - m_Phi^2)^2)
    (the beta^3 is the S-wave scalar-coupling threshold law; the trace
    algebra is in xsec_FFbar_to_FFbar/ground_truth/derivation.py,
    extended to massive finals).

Literature: per-ingredient citations live in the sibling benchmarks'
derivation scripts (Djouadi arXiv:hep-ph/0503172 sec. 2.3 for the
beta^3 fermionic widths; PDG Kinematics review for the two-body master
formula and hbar; P&S eq. (5.13)-adjacent trace algebra for the
s-channel annihilation). Everything below is verified against the
independent explicit-spinor numerics in _shared/dirac_numeric.py.

Run from the repo root:
    python benchmarks/symbolic/composite_toy_model/ground_truth/derivation.py
"""

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))
import dirac_numeric as dn  # noqa: E402

OUT = Path(__file__).resolve().parent / "truth.json"

# --- task parameters (quoted in the prompt) ---
MPHI = 1850.0
M1, M2, MCHI = 230.0, 0.0, 410.0
Y1, Y2, MU = 0.42, 0.16, 590.0
RS = 1100.0
S = RS * RS


def width_psi1():
    beta = np.sqrt(1 - 4 * M1**2 / MPHI**2)
    return Y1**2 * MPHI * beta**3 / (8 * np.pi)


def width_psi2():
    return Y2**2 * MPHI / (8 * np.pi)


def width_chichi():
    beta = np.sqrt(1 - 4 * MCHI**2 / MPHI**2)
    return MU**2 * beta / (32 * np.pi * MPHI)


def xsec_gev2():
    beta_f = np.sqrt(1 - 4 * M1**2 / S)
    return Y1**2 * Y2**2 * S * beta_f**3 / (16 * np.pi * (S - MPHI**2)**2)


# ---- independent numeric checks ----
def _msq_yukawa(y, mf):
    def msq(p1, p2):
        total = 0.0
        for s1 in (0, 1):
            for s2 in (0, 1):
                amp = y * (dn.ubar(p1, mf, s1) @ dn.v_spinor(p2, mf, s2))
                total += abs(amp) ** 2
        return total
    return msq


def numeric_widths():
    w1 = dn.two_body_width(MPHI, M1, M1, _msq_yukawa(Y1, M1))
    w2 = dn.two_body_width(MPHI, M2, M2, _msq_yukawa(Y2, M2))
    wc = dn.two_body_width(MPHI, MCHI, MCHI, lambda p1, p2: MU**2,
                           symmetry=2.0)
    return w1, w2, wc


def numeric_xsec_gev2():
    pref = Y1 * Y2 / (S - MPHI**2)

    def msq(p1, p2, p3, p4):
        total = 0.0
        for s1 in (0, 1):
            for s2 in (0, 1):
                c1 = dn.vbar(p2, 0.0, s2) @ dn.u_spinor(p1, 0.0, s1)
                for s3 in (0, 1):
                    for s4 in (0, 1):
                        c2 = dn.ubar(p3, M1, s3) @ dn.v_spinor(p4, M1, s4)
                        total += abs(pref * c1 * c2) ** 2
        return total / 4.0
    return dn.two_to_two_xsec(S, 0.0, 0.0, M1, M1, msq, n=400)


def main():
    w1, w2, wc = width_psi1(), width_psi2(), width_chichi()
    n1, n2, nc = numeric_widths()
    for name, ana, num in (("psi1", w1, n1), ("psi2", w2, n2),
                           ("chichi", wc, nc)):
        rel = abs(ana - num) / ana
        print(f"width_{name}: analytic {ana:.10g}  numeric {num:.10g}  "
              f"rel {rel:.2e}")
        assert rel < 1e-10

    xs_ana, xs_num = xsec_gev2(), numeric_xsec_gev2()
    rel = abs(xs_ana - xs_num) / xs_ana
    print(f"xsec: analytic {xs_ana:.10g} GeV^-2  numeric {xs_num:.10g}  "
          f"rel {rel:.2e}")
    assert rel < 1e-10

    total = w1 + w2 + wc
    truth = {
        "width_psi1_gev": w1,
        "width_psi2_gev": w2,
        "width_chichi_gev": wc,
        "width_total_gev": total,
        "br_psi1": w1 / total,
        "br_psi2": w2 / total,
        "br_chichi": wc / total,
        "lifetime_s": dn.HBAR_GEV_S / total,
        "xsec_pb": xs_ana * dn.GEV2_TO_PB,
        "_metadata": {
            "generated_by": "ground_truth/derivation.py",
            "parameters": {
                "mPhi_gev": MPHI, "m1_gev": M1, "m2_gev": M2,
                "mchi_gev": MCHI, "y1": Y1, "y2": Y2, "mu_gev": MU,
                "sqrt_s_gev": RS,
            },
            "verification": "all widths and the cross section reproduced "
                            "to <1e-10 by independent explicit-spinor "
                            "numerics (_shared/dirac_numeric.py)",
            "citations": [
                "A. Djouadi, arXiv:hep-ph/0503172, sec. 2.3 (beta^3 "
                "fermionic widths)",
                "PDG, Kinematics review (two-body master formula; "
                "identical-particle 1/S) and PDG physical constants "
                "(hbar = 6.582119569e-25 GeV s)",
                "M.E. Peskin, D.V. Schroeder, ch. 5 (s-channel "
                "annihilation trace algebra)",
            ],
        },
    }
    OUT.write_text(json.dumps(truth, indent=2) + "\n")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
