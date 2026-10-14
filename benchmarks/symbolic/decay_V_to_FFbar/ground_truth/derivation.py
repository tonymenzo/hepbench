"""
# benchmarks/symbolic/decay_V_to_FFbar/ground_truth/derivation.py is a part of HEPBench.
# Copyright (C) 2026 HEPBench authors (see AUTHORS for details).
# HEPBench is licensed under the GNU GPL v3 or later, see LICENSE for details.
"""
"""
Ground truth for decay_V_to_FFbar: tree-level width of a massive
neutral vector boson V (mass m_V) into a Dirac fermion pair. Average
over the three initial polarizations; x = m_f^2 / m_V^2.

Part (a)  L = g V_mu psibar gamma^mu psi   (pure vector)
    Gamma = g^2 m_V / (12 pi) * (1 + 2 x) * sqrt(1 - 4 x)

Part (b)  L = V_mu psibar gamma^mu (gV - gA gamma_5) psi
    Gamma = m_V / (12 pi) * sqrt(1 - 4 x)
            * [ gV^2 (1 + 2 x) + gA^2 (1 - 4 x) ]
    Part (a) is the (gV, gA) = (g, 0) limit; the axial part carries the
    extra beta^2 threshold suppression.

Literature: this is the Z / Z' partial-width formula:
  - V.D. Barger and R.J.N. Phillips, "Collider Physics" (updated ed.),
    ch. on electroweak interactions: Gamma(Z -> f fbar) with massive
    fermions, identical structure with (gV, gA) the SM neutral-current
    couplings times g_Z/2;
  - P. Langacker, "The physics of heavy Z' gauge bosons",
    Rev.Mod.Phys. 81 (2009) 1199, arXiv:0801.1345 (Z' -> f fbar
    partial widths);
  - PDG, "Electroweak model and constraints on new physics" review
    (massless limit Gamma ~ m_Z (gV^2 + gA^2) / 12 pi per color).

Verified against the independent numeric computation (explicit Dirac
spinors AND explicit massive-vector polarization vectors) in
_shared/dirac_numeric.py.

Run from the repo root:
    python benchmarks/symbolic/decay_V_to_FFbar/ground_truth/derivation.py
"""

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))
import dirac_numeric as dn  # noqa: E402

OUT = Path(__file__).resolve().parent / "truth.json"

# --- task parameters (quoted in the prompt) ---
MV, MF = 2150.0, 640.0
G_A = 0.47            # part (a)
GV, GA = 0.52, 0.36   # part (b)


def analytic_a():
    x = MF**2 / MV**2
    return G_A**2 * MV / (12 * np.pi) * (1 + 2 * x) * np.sqrt(1 - 4 * x)


def analytic_b():
    x = MF**2 / MV**2
    return MV / (12 * np.pi) * np.sqrt(1 - 4 * x) * (
        GV**2 * (1 + 2 * x) + GA**2 * (1 - 4 * x))


def _msq(vertex_of_mu):
    """(1/3) sum_pol sum_spins |ubar(p1) eps_mu Gamma^mu v(p2)|^2."""
    P = np.array([MV, 0.0, 0.0, 0.0])
    eps_list = dn.pol_vectors(P, MV)

    def msq(p1, p2):
        total = 0.0
        for eps in eps_list:
            gam = sum(eps[mu] * dn.ETA[mu, mu] * vertex_of_mu(mu)
                      for mu in range(4))
            # eps^mu Gamma_mu = eps^mu eta_mumu Gamma^mu (diagonal metric)
            for s1 in (0, 1):
                for s2 in (0, 1):
                    amp = dn.ubar(p1, MF, s1) @ gam @ dn.v_spinor(p2, MF, s2)
                    total += abs(amp) ** 2
        return total / 3.0
    return msq


def numeric_a():
    return dn.two_body_width(MV, MF, MF,
                             _msq(lambda mu: G_A * dn.GAMMA[mu]))


def numeric_b():
    return dn.two_body_width(
        MV, MF, MF,
        _msq(lambda mu: dn.GAMMA[mu] @ (GV * dn.ID4 - GA * dn.GAMMA5)))


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
            "g**2 * mV / (12*pi) * (1 + 2*mf**2/mV**2)"
            " * sqrt(1 - 4*mf**2/mV**2)",
        "part_b_width_gev": analytic_b(),
        "part_b_width_formula":
            "mV / (12*pi) * sqrt(1 - 4*mf**2/mV**2)"
            " * (gV**2 * (1 + 2*mf**2/mV**2)"
            " + gA**2 * (1 - 4*mf**2/mV**2))",
        "_metadata": {
            "generated_by": "ground_truth/derivation.py",
            "parameters": {
                "common": {"mV_gev": MV, "mf_gev": MF},
                "part_a": {"g": G_A},
                "part_b": {"gV": GV, "gA": GA},
            },
            "verification": "analytic formulas reproduced to <1e-10 by "
                            "independent numeric computation with explicit "
                            "polarization vectors and Dirac spinors",
            "citations": [
                "V.D. Barger, R.J.N. Phillips, Collider Physics, "
                "electroweak ch. (Z -> f fbar with massive fermions)",
                "P. Langacker, Rev.Mod.Phys. 81 (2009) 1199, "
                "arXiv:0801.1345 (Z' -> f fbar partial widths)",
                "PDG, Electroweak model and constraints on new physics "
                "review (massless limit)",
            ],
        },
    }
    OUT.write_text(json.dumps(truth, indent=2) + "\n")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
