"""
# benchmarks/symbolic/_shared/dirac_numeric.py is a part of HEPBench.
# Copyright (C) 2026 HEPBench authors (see AUTHORS for details).
# HEPBench is licensed under the GNU GPL v3 or later, see LICENSE for details.
"""
"""
Independent numeric verifier for the `symbolic` family's ground truth.

Every analytic formula committed to a `ground_truth/truth.json` is
cross-checked by a derivation script against a from-scratch numeric
computation built from the primitives here: explicit Dirac matrices and
spinors (Dirac representation, normalization ubar u = 2m), explicit
massive-vector polarization vectors, and direct phase-space integration.
No trace identities or width formulas are reused from the analytic side,
so a convention slip (coupling normalization, symmetry factor, spin
average) shows up as a mismatch instead of propagating silently.

Conventions (Peskin & Schroeder, "An Introduction to Quantum Field
Theory", ch. 3-5):
  - metric eta = diag(+,-,-,-); slash(p) = p^mu gamma_mu
  - spin sums: sum_s u ubar = slash(p) + m, sum_s v vbar = slash(p) - m
    (asserted numerically in tests/test_symbolic_dirac_numeric.py)
  - 2-body width: Gamma = |p| / (8 pi M^2) <|M|^2>            [PDG 50.18]
  - 3-body width: dGamma = (2 pi)^-3 (32 M^3)^-1 |M|^2 dm12^2 dm23^2
                                                              [PDG 50.22]
  - 2->2: dsigma/dOmega = |M|^2 |p_f| / (64 pi^2 s |p_i|)     [PDG 50.32]
(PDG section numbers from the "Kinematics" review, R.L. Workman et al.
(Particle Data Group), Prog. Theor. Exp. Phys. 2022, 083C01.)
"""

import numpy as np

ETA = np.diag([1.0, -1.0, -1.0, -1.0])

_I2 = np.eye(2, dtype=complex)
_SIG = np.array([
    [[0, 1], [1, 0]],
    [[0, -1j], [1j, 0]],
    [[1, 0], [0, -1]],
], dtype=complex)

_Z2 = np.zeros((2, 2), dtype=complex)
GAMMA = np.array([
    np.block([[_I2, _Z2], [_Z2, -_I2]]),
    np.block([[_Z2, _SIG[0]], [-_SIG[0], _Z2]]),
    np.block([[_Z2, _SIG[1]], [-_SIG[1], _Z2]]),
    np.block([[_Z2, _SIG[2]], [-_SIG[2], _Z2]]),
])
GAMMA5 = 1j * GAMMA[0] @ GAMMA[1] @ GAMMA[2] @ GAMMA[3]
PL = (np.eye(4) - GAMMA5) / 2.0
PR = (np.eye(4) + GAMMA5) / 2.0
ID4 = np.eye(4, dtype=complex)


def mdot(p, q):
    """Minkowski dot product of contravariant 4-vectors."""
    return p[0] * q[0] - p[1] * q[1] - p[2] * q[2] - p[3] * q[3]


def slash(p):
    return p[0] * GAMMA[0] - p[1] * GAMMA[1] - p[2] * GAMMA[2] - p[3] * GAMMA[3]


def kallen(a, b, c):
    return a * a + b * b + c * c - 2 * a * b - 2 * b * c - 2 * c * a


def _chi(s):
    return np.array([1, 0], dtype=complex) if s == 0 else \
        np.array([0, 1], dtype=complex)


def u_spinor(p, m, s):
    """Dirac-rep u spinor, ubar u = 2m, u+ u = 2E. s in {0, 1}."""
    E = p[0]
    sp = sum(p[i + 1] * _SIG[i] for i in range(3))
    chi = _chi(s)
    n = np.sqrt(E + m)
    return np.concatenate([n * chi, (sp @ chi) / n])


def v_spinor(p, m, s):
    """Dirac-rep v spinor; sum_s v vbar = slash(p) - m."""
    E = p[0]
    sp = sum(p[i + 1] * _SIG[i] for i in range(3))
    chi = _chi(s)
    n = np.sqrt(E + m)
    return np.concatenate([(sp @ chi) / n, n * chi])


def ubar(p, m, s):
    return u_spinor(p, m, s).conj() @ GAMMA[0]


def vbar(p, m, s):
    return v_spinor(p, m, s).conj() @ GAMMA[0]


def pol_vectors(p, M):
    """The three polarization vectors of a massive vector with momentum p.

    Satisfy eps_i . eps_j* = -delta_ij, p . eps_i = 0 and the completeness
    relation sum_i eps_i^mu eps_i*^nu = -eta^munu + p^mu p^nu / M^2."""
    E, pv = p[0], np.asarray(p[1:], dtype=float)
    pm = np.linalg.norm(pv)
    if pm < 1e-12 * max(M, 1.0):
        return [np.array([0, 1, 0, 0], dtype=complex),
                np.array([0, 0, 1, 0], dtype=complex),
                np.array([0, 0, 0, 1], dtype=complex)]
    n = pv / pm
    a = np.array([1.0, 0.0, 0.0]) if abs(n[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
    e1 = np.cross(n, a)
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(n, e1)
    eL = np.concatenate([[pm / M], (E / M) * n])
    return [np.concatenate([[0.0], e1]).astype(complex),
            np.concatenate([[0.0], e2]).astype(complex),
            eL.astype(complex)]


# ---------------------------------------------------------------------------
# kinematics builders
# ---------------------------------------------------------------------------
def two_body_momenta(M, m1, m2):
    """Daughter momenta for a decay at rest, daughter 1 along +z."""
    if M < m1 + m2:
        raise ValueError("below threshold")
    pcm = np.sqrt(kallen(M * M, m1 * m1, m2 * m2)) / (2 * M)
    e1 = np.sqrt(pcm * pcm + m1 * m1)
    e2 = np.sqrt(pcm * pcm + m2 * m2)
    return (np.array([e1, 0, 0, pcm]), np.array([e2, 0, 0, -pcm]))


def three_body_momenta(M, m1, m2, m3, m12sq, m23sq):
    """Explicit momenta in the parent rest frame for a Dalitz point.

    p1 along +z, p2 in the x-z plane; energies fixed by the invariants
    (m13^2 follows from the sum rule)."""
    m13sq = M * M + m1 * m1 + m2 * m2 + m3 * m3 - m12sq - m23sq
    e1 = (M * M + m1 * m1 - m23sq) / (2 * M)
    e2 = (M * M + m2 * m2 - m13sq) / (2 * M)
    e3 = (M * M + m3 * m3 - m12sq) / (2 * M)
    p1m = np.sqrt(max(e1 * e1 - m1 * m1, 0.0))
    p2m = np.sqrt(max(e2 * e2 - m2 * m2, 0.0))
    # cos(theta_12) from m12^2 = (p1 + p2)^2
    if p1m * p2m < 1e-300:
        c12 = 0.0
    else:
        c12 = (e1 * e2 - (m12sq - m1 * m1 - m2 * m2) / 2.0) / (p1m * p2m)
        c12 = min(1.0, max(-1.0, c12))
    s12 = np.sqrt(max(1.0 - c12 * c12, 0.0))
    p1 = np.array([e1, 0.0, 0.0, p1m])
    p2 = np.array([e2, p2m * s12, 0.0, p2m * c12])
    p3 = np.array([e3, -p2[1], 0.0, -(p1[3] + p2[3])])
    return p1, p2, p3


def dalitz_bounds_m23sq(M, m1, m2, m3, m12sq):
    """PDG eq. 50.23a: m23^2 range at fixed m12^2."""
    m12 = np.sqrt(m12sq)
    e2 = (m12sq - m1 * m1 + m2 * m2) / (2 * m12)
    e3 = (M * M - m12sq - m3 * m3) / (2 * m12)
    p2 = np.sqrt(max(e2 * e2 - m2 * m2, 0.0))
    p3 = np.sqrt(max(e3 * e3 - m3 * m3, 0.0))
    lo = (e2 + e3) ** 2 - (p2 + p3) ** 2
    hi = (e2 + e3) ** 2 - (p2 - p3) ** 2
    return lo, hi


# ---------------------------------------------------------------------------
# rates
# ---------------------------------------------------------------------------
def two_body_width(M, m1, m2, msq_avg, symmetry=1.0):
    """Gamma = |p| / (8 pi M^2) * <|M|^2> / S.

    `msq_avg(p1, p2)` returns the spin-AVERAGED, spin-summed squared
    matrix element at the given daughter momenta."""
    p1, p2 = two_body_momenta(M, m1, m2)
    pcm = p1[3]
    return pcm / (8.0 * np.pi * M * M) * float(np.real(msq_avg(p1, p2))) \
        / symmetry


def three_body_width(M, m1, m2, m3, msq_avg, n12=160, n23=160, symmetry=1.0):
    """Numeric Dalitz integration of PDG eq. 50.22.

    `msq_avg(p1, p2, p3)` is evaluated at explicit momenta per Dalitz
    cell (midpoint rule on a uniform grid; adequate for the smooth
    tree-level integrands used here)."""
    lo12 = (m1 + m2) ** 2
    hi12 = (M - m3) ** 2
    total = 0.0
    d12 = (hi12 - lo12) / n12
    for i in range(n12):
        m12sq = lo12 + (i + 0.5) * d12
        lo23, hi23 = dalitz_bounds_m23sq(M, m1, m2, m3, m12sq)
        if hi23 <= lo23:
            continue
        d23 = (hi23 - lo23) / n23
        for j in range(n23):
            m23sq = lo23 + (j + 0.5) * d23
            p1, p2, p3 = three_body_momenta(M, m1, m2, m3, m12sq, m23sq)
            total += float(np.real(msq_avg(p1, p2, p3))) * d23
        # (inner loop accumulated f * d23 already)
    total *= d12
    return total / ((2 * np.pi) ** 3 * 32.0 * M ** 3) / symmetry


def two_to_two_xsec(s, m1, m2, m3, m4, msq_avg, n=400, identical=False):
    """sigma(1 2 -> 3 4) by numeric integration of PDG eq. 50.32.

    `msq_avg(p1, p2, p3, p4)` is the spin-averaged squared amplitude at
    explicit c.m. momenta. Returns sigma in GeV^-2."""
    rs = np.sqrt(s)
    pi_cm = np.sqrt(kallen(s, m1 * m1, m2 * m2)) / (2 * rs)
    pf_cm = np.sqrt(kallen(s, m3 * m3, m4 * m4)) / (2 * rs)
    e1 = np.sqrt(pi_cm ** 2 + m1 * m1)
    e2 = np.sqrt(pi_cm ** 2 + m2 * m2)
    e3 = np.sqrt(pf_cm ** 2 + m3 * m3)
    e4 = np.sqrt(pf_cm ** 2 + m4 * m4)
    p1 = np.array([e1, 0, 0, pi_cm])
    p2 = np.array([e2, 0, 0, -pi_cm])
    total = 0.0
    dc = 2.0 / n
    for i in range(n):
        c = -1.0 + (i + 0.5) * dc
        sn = np.sqrt(max(1.0 - c * c, 0.0))
        p3 = np.array([e3, pf_cm * sn, 0.0, pf_cm * c])
        p4 = np.array([e4, -p3[1], 0.0, -p3[3]])
        total += float(np.real(msq_avg(p1, p2, p3, p4))) * dc
    # dsigma/dcos = 2 pi dsigma/dOmega = |M|^2 pf / (32 pi s pi_cm)
    sigma = total * pf_cm / (32.0 * np.pi * s * pi_cm)
    if identical:
        sigma *= 0.5
    return sigma


GEV2_TO_PB = 3.893793721e8  # (hbar c)^2 in GeV^2 pb, PDG physical constants
HBAR_GEV_S = 6.582119569e-25  # hbar in GeV s, PDG physical constants
