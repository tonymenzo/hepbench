"""
# benchmarks/symbolic/decay_V_to_VVp/ground_truth/derivation.py is a part of HEPBench.
# Copyright (C) 2026 HEPBench authors (see AUTHORS for details).
# HEPBench is licensed under the GNU GPL v3 or later, see LICENSE for details.
"""
"""
Ground truth for decay_V_to_VVp: tree-level two-body width of a massive
vector V (mass m_V) into two distinct massive vectors V1, V2 (masses
m_1, m_2) via the standard (Yang-Mills) triple-gauge vertex
    Gamma^{mu nu rho}(P,q1,q2) =
        g[ eta^{mu nu}(P-q1)^rho + eta^{nu rho}(q1-q2)^mu
           + eta^{rho mu}(q2-P)^nu ],
with eps(P), eps*(q1), eps*(q2) on the three legs (CONVENTIONS.md
sec. 4). Average over the parent's three polarizations; sum over the two
daughters'. The non-abelian structure constant forbids two IDENTICAL
final vectors (f^{aab}=0), so both parts use distinct vectors (this is
the Z'->W+W- archetype).

This is the one archetype whose closed form in (m_V, m_1, m_2) is
unwieldy (longitudinal modes give a strong m_V^5/(m_1^2 m_2^2)
enhancement), so the benchmark grades NUMERIC widths only (no formula
stage). The committed values are validated by TWO independent
contractions of the same vertex:
  (1) an explicit sum over polarization vectors (pol_vectors), and
  (2) a completeness-tensor einsum using
      sum_pol eps_mu eps*_nu = -eta_{mu nu} + p_mu p_nu / m^2,
agreeing to < 1e-9. The vertex itself is the textbook YM triple-gauge
vertex; its longitudinal m_V^5/(m_1^2 m_2^2) scaling is sanity-checked.

Literature: the triple-gauge V -> V V width is the heavy-vector
resonance / Z'->W+W- result, e.g. J.L. Hewett, T.G. Rizzo,
"Low-energy phenomenology of superstring-inspired E6 models",
Phys.Rept. 183 (1989) 193 (Z' decays); the YM vertex is standard
(M.E. Peskin & D.V. Schroeder, ch. 16).

Run from the repo root:
    python benchmarks/symbolic/decay_V_to_VVp/ground_truth/derivation.py
"""

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))
import dirac_numeric as dn  # noqa: E402

OUT = Path(__file__).resolve().parent / "truth.json"

# --- task parameters (quoted in the prompt) ---
G_A, MVA, M1A, M2A = 0.80, 900.0, 200.0, 250.0   # part (a)
G_B, MVB, M1B, M2B = 0.65, 1200.0, 180.0, 400.0  # part (b)


def _mdot(a, b):
    return sum(dn.ETA[m, m] * a[m] * b[m] for m in range(4))


def _vertex_momenta(P, q1, q2):
    """The three momentum differences of the YM triple-gauge vertex.

    THE VERTEX IS DERIVED UNDER ALL-INCOMING MOMENTA, k1 + k2 + k3 = 0:

        V^{m1 m2 m3}(k1,k2,k3) = g[ eta^{m1 m2}(k1-k2)^{m3}
                                  + eta^{m2 m3}(k2-k3)^{m1}
                                  + eta^{m3 m1}(k3-k1)^{m2} ]

    The cyclic structure IS momentum conservation at the vertex, so the
    assignment is not a free choice. A leg whose physical momentum flows
    outward enters as -p: for the decay P -> q1 q2 that makes
    (k1,k2,k3) = (P, -q1, -q2), and the differences below follow.

    THIS FILE PREVIOUSLY USED (P-q1, q1-q2, q2-P) -- the same expression
    evaluated at the physical momenta as drawn, which sum to 2P rather than
    0. That is the formula applied outside its domain, not an alternative
    convention, and it is wrong at finite masses. Both committed widths sat
    at m_V/m ~ 4, deep in the regime where the two disagree, so part (a) was
    low by a factor of ~2.9.

    IT SURVIVED REVIEW because the two cross-checks here -- explicit
    polarization vectors and the completeness-tensor einsum -- share this
    function. They agree to 1e-15 either way: they test the contraction
    algebra, not the vertex. Only _check_against_literature below can see
    the difference, which is why it exists.
    """
    return P + q1, q2 - q1, -q2 - P


def _msq_explicit(g, mV, m1, m2, q1, q2):
    P = q1 + q2
    eP = dn.pol_vectors(P, mV)
    e1 = dn.pol_vectors(q1, m1)
    e2 = dn.pol_vectors(q2, m2)
    d12, d23, d31 = _vertex_momenta(P, q1, q2)
    total = 0.0
    for a in eP:
        for b in e1:
            bc = np.conjugate(b)
            for c in e2:
                cc = np.conjugate(c)
                M = g * (_mdot(a, bc) * _mdot(d12, cc)
                         + _mdot(bc, cc) * _mdot(d23, a)
                         + _mdot(cc, a) * _mdot(d31, bc))
                total += abs(M) ** 2
    return total / 3.0


def _msq_tensor(g, mV, m1, m2, q1, q2):
    P = q1 + q2
    d12, d23, d31 = _vertex_momenta(P, q1, q2)
    eta = dn.ETA
    G = np.zeros((4, 4, 4))
    for mu in range(4):
        for nu in range(4):
            for rho in range(4):
                G[mu, nu, rho] = g * (eta[mu, nu] * d12[rho]
                                      + eta[nu, rho] * d23[mu]
                                      + eta[rho, mu] * d31[nu])

    def Dlow(p, m):
        pl = dn.ETA @ p
        return -dn.ETA + np.outer(pl, pl) / m**2

    DP, D1, D2 = Dlow(P, mV), Dlow(q1, m1), Dlow(q2, m2)
    val = np.einsum('mnr,MNR,mM,nN,rR->', G, G, DP, D1, D2)
    return val / 3.0


def width(g, mV, m1, m2):
    q1, q2 = dn.two_body_momenta(mV, m1, m2)
    me_e = _msq_explicit(g, mV, m1, m2, q1, q2)
    me_t = _msq_tensor(g, mV, m1, m2, q1, q2)
    rel = abs(me_e - me_t) / abs(me_e)
    assert rel < 1e-9, f"explicit vs tensor |M|^2 mismatch: {rel:.2e}"
    return dn.two_body_width(mV, m1, m2, lambda p1, p2: me_e), me_e


def _check_against_literature():
    """Validate the vertex against Gamma(Z' -> W+W-), an EXTERNAL number.

    The two contractions in this file share _vertex_momenta, so they cannot
    detect a wrong momentum assignment. This can: for equal daughter masses
    the triple-gauge width has the closed form

        Gamma = g^2/(192 pi) * mV * (mV/m)^4 * (1-4x)^{3/2} * [1 + 20x + 12x^2],
        x = m^2/mV^2

    (Hewett & Rizzo, Phys.Rept. 183 (1989) 193). All-incoming reproduces it
    exactly at every mass ratio; the as-drawn assignment converges to it only
    asymptotically -- 0.209 of it at mV/m = 3, 0.800 at mV/m = 10. Both share
    the leading longitudinal coefficient 1/192, which is why a high-mV limit
    check cannot discriminate and the old `me_hi/me_lo > 10` growth assertion
    passed on the wrong vertex.

    The ratios below are therefore the real regression guard for this task.
    """
    def literature(g, mV, m):
        x = m * m / (mV * mV)
        return (g * g / (192 * np.pi)) * mV * (mV / m) ** 4 \
            * (1 - 4 * x) ** 1.5 * (1 + 20 * x + 12 * x * x)

    worst = 0.0
    for g, mV, m in ((0.80, 900.0, 300.0),    # mV/m = 3, maximal discrimination
                     (0.80, 900.0, 180.0),    # mV/m = 5
                     (0.65, 1200.0, 120.0),   # mV/m = 10
                     (0.80, 900.0, 3.0)):     # mV/m = 300, the asymptotic end
        got, _ = width(g, mV, m, m)
        ref = literature(g, mV, m)
        rel = abs(got - ref) / ref
        worst = max(worst, rel)
        print(f"  Z'->W+W- at mV/m = {mV/m:5.0f}:  {got:.10g} vs {ref:.10g} "
              f"(rel {rel:.1e})")
        assert rel < 1e-9, (
            f"triple-gauge vertex disagrees with the literature Z'->W+W- "
            f"width at mV/m = {mV/m:.0f} by {rel:.3e}. Check _vertex_momenta: "
            f"the all-incoming assignment (P, -q1, -q2) is required."
        )
    return worst


def main():
    wa, mea = width(G_A, MVA, M1A, M2A)
    wb, meb = width(G_B, MVB, M1B, M2B)
    print(f"part_a: width {wa:.10g} GeV  (explicit==tensor |M|^2 = {mea:.6g})")
    print(f"part_b: width {wb:.10g} GeV  (explicit==tensor |M|^2 = {meb:.6g})")

    # The vertex itself, against an external closed form. This is the check
    # that discriminates the momentum assignment; the explicit-vs-tensor
    # agreement inside width() does not (see _vertex_momenta).
    print("vertex validation against the literature Z' -> W+W- width:")
    worst = _check_against_literature()

    # Longitudinal enhancement: |M|^2 grows ~ (mV^2/(m1 m2))^2 for mV >> m.
    # Kept as a shape check, but note it passes on EITHER assignment -- both
    # share the leading 1/192 coefficient -- so it is not a convention guard.
    _, me_lo = width(G_A, 900.0, 200.0, 250.0)
    _, me_hi = width(G_A, 1800.0, 200.0, 250.0)
    assert me_hi / me_lo > 10, "expected strong longitudinal growth with m_V"
    print(f"longitudinal scaling check: |M|^2(2x m_V)/|M|^2 = "
          f"{me_hi/me_lo:.1f} (>10 expected)")

    truth = {
        "part_a_width_gev": wa,
        "part_b_width_gev": wb,
        "_metadata": {
            "generated_by": "ground_truth/derivation.py",
            "conventions": "../CONVENTIONS.md",
            "grading": "numeric widths only; the closed form in "
                       "(m_V,m_1,m_2) is unwieldy (no formula stage)",
            "parameters": {
                "part_a": {"g": G_A, "mV_gev": MVA, "m1_gev": M1A,
                           "m2_gev": M2A},
                "part_b": {"g": G_B, "mV_gev": MVB, "m1_gev": M1B,
                           "m2_gev": M2B},
            },
            "verification": "vertex validated against the literature "
                            "Z'->W+W- closed form at m_V/m = 3, 5, 10 and "
                            "300 (rel <1e-9, the check that discriminates "
                            "the all-incoming momentum assignment); each "
                            "width then computed by two independent "
                            "contractions (explicit polarization vectors vs "
                            "completeness-tensor einsum) agreeing <1e-9; "
                            "longitudinal m_V^5/(m1^2 m2^2) scaling checked",
            "convention": "YM triple-gauge vertex with ALL-INCOMING momenta "
                          "(k1+k2+k3=0); for P -> q1 q2 that is "
                          "(P, -q1, -q2). Superseded the as-drawn "
                          "(P, q1, q2) assignment on 2026-09-11, which was "
                          "the formula outside its domain and gave widths "
                          "low by ~2.9x at these mass ratios.",
            "citations": [
                "J.L. Hewett, T.G. Rizzo, Phys.Rept. 183 (1989) 193 "
                "(Z' -> W+W- and heavy-vector decays)",
                "M.E. Peskin, D.V. Schroeder, An Introduction to QFT, "
                "ch. 16 (Yang-Mills triple-gauge vertex)",
            ],
        },
    }
    OUT.write_text(json.dumps(truth, indent=2) + "\n")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
