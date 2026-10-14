"""
# tests/test_symbolic_dirac_numeric.py is a part of HEPBench.
# Copyright (C) 2026 HEPBench authors (see AUTHORS for details).
# HEPBench is licensed under the GNU GPL v3 or later, see LICENSE for details.
"""
"""
Anchors benchmarks/symbolic/_shared/dirac_numeric.py against textbook
results, so every ground truth verified with it inherits checked
conventions:

  - spinor completeness relations (P&S eq. 3.66)
  - massive-vector polarization completeness
  - Gamma(S -> f fbar) for L = -y phi psibar psi (beta^3 law)
  - muon decay Gamma = G_F^2 m^5 / (192 pi^3) via an explicit
    (V-A)(V-A) contact amplitude (P&S sec. 5.3 / PDG)
  - sigma(e+ e- -> mu+ mu-) = 4 pi alpha^2 / (3 s) via an s-channel
    vector exchange (P&S eq. 5.13)
"""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]
                       / "benchmarks" / "symbolic" / "_shared"))
import dirac_numeric as dn  # noqa: E402


def _rand_momentum(m, seed):
    rng = np.random.default_rng(seed)
    pv = rng.uniform(-50, 50, 3)
    e = np.sqrt(m * m + pv @ pv)
    return np.array([e, *pv])


@pytest.mark.parametrize("m", [0.0, 0.105, 4.7, 173.0])
def test_spinor_completeness(m):
    p = _rand_momentum(m, 7)
    su = sum(np.outer(dn.u_spinor(p, m, s), dn.ubar(p, m, s)) for s in (0, 1))
    sv = sum(np.outer(dn.v_spinor(p, m, s), dn.vbar(p, m, s)) for s in (0, 1))
    assert np.allclose(su, dn.slash(p) + m * dn.ID4, atol=1e-9 * max(p[0], 1))
    assert np.allclose(sv, dn.slash(p) - m * dn.ID4, atol=1e-9 * max(p[0], 1))


def test_polarization_completeness():
    M = 91.19
    p = _rand_momentum(M, 11)
    eps = dn.pol_vectors(p, M)
    total = sum(np.outer(e, e.conj()) for e in eps)
    expected = -dn.ETA + np.outer(p, p) / (M * M)
    assert np.allclose(total, expected, atol=1e-9)
    for e in eps:
        assert abs(dn.mdot(p, e)) < 1e-9 * p[0]


def test_scalar_to_ffbar_beta_cubed():
    """L = -y phi psibar psi: Gamma = y^2 m_S beta^3 / (8 pi)."""
    y, mS, mf = 0.8, 1000.0, 230.0

    def msq(p1, p2):
        total = 0.0
        for s1 in (0, 1):
            for s2 in (0, 1):
                amp = y * (dn.ubar(p1, mf, s1) @ dn.v_spinor(p2, mf, s2))
                total += abs(amp) ** 2
        return total  # scalar parent: no spin average

    beta = np.sqrt(1 - 4 * mf * mf / (mS * mS))
    analytic = y * y * mS * beta ** 3 / (8 * np.pi)
    numeric = dn.two_body_width(mS, mf, mf, msq)
    assert numeric == pytest.approx(analytic, rel=1e-10)


def test_muon_decay_formula():
    """(V-A)(V-A) contact: Gamma = G_F^2 m^5 / (192 pi^3), massless finals.

    M = 2 sqrt(2) G_F [ubar_3 gamma^mu P_L u_1][ubar_4 gamma_mu P_L v_5]."""
    GF = 1.1663787e-5
    m_mu = 0.1056583755
    pref = 2.0 * np.sqrt(2.0) * GF

    def msq(p1, p2, p3):
        # p1 = e (paired with the muon current), p2 = nu, p3 = nubar
        total = 0.0
        pmu = np.array([m_mu, 0.0, 0.0, 0.0])
        for smu in (0, 1):
            umu = dn.u_spinor(pmu, m_mu, smu)
            for s1 in (0, 1):
                cur1 = [dn.ubar(p1, 0.0, s1) @ dn.GAMMA[k] @ dn.PL @ umu
                        for k in range(4)]
                for s2 in (0, 1):
                    for s3 in (0, 1):
                        cur2 = [dn.ubar(p2, 0.0, s2) @ dn.GAMMA[k] @ dn.PL
                                @ dn.v_spinor(p3, 0.0, s3) for k in range(4)]
                        amp = pref * (cur1[0] * cur2[0] - cur1[1] * cur2[1]
                                      - cur1[2] * cur2[2] - cur1[3] * cur2[3])
                        total += abs(amp) ** 2
        return total / 2.0  # average over the muon spin

    analytic = GF ** 2 * m_mu ** 5 / (192 * np.pi ** 3)
    numeric = dn.three_body_width(m_mu, 0.0, 0.0, 0.0, msq, n12=120, n23=120)
    assert numeric == pytest.approx(analytic, rel=2e-3)


def test_ee_to_mumu_point_xsec():
    """s-channel massless vector: sigma = g^4 / (12 pi s) (P&S 5.13)."""
    g, rs = 0.31, 200.0
    s = rs * rs

    def msq(p1, p2, p3, p4):
        total = 0.0
        for s1 in (0, 1):
            for s2 in (0, 1):
                cur1 = [dn.vbar(p2, 0.0, s2) @ dn.GAMMA[k]
                        @ dn.u_spinor(p1, 0.0, s1) for k in range(4)]
                for s3 in (0, 1):
                    for s4 in (0, 1):
                        cur2 = [dn.ubar(p3, 0.0, s3) @ dn.GAMMA[k]
                                @ dn.v_spinor(p4, 0.0, s4) for k in range(4)]
                        amp = (g * g / s) * (
                            cur1[0] * cur2[0] - cur1[1] * cur2[1]
                            - cur1[2] * cur2[2] - cur1[3] * cur2[3])
                        total += abs(amp) ** 2
        return total / 4.0  # average over both initial spins

    analytic = g ** 4 / (12 * np.pi * s)
    numeric = dn.two_to_two_xsec(s, 0, 0, 0, 0, msq, n=400)
    assert numeric == pytest.approx(analytic, rel=1e-4)
