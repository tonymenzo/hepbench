# The low-mass gamma-gamma discrepancy: parent decay-length stratification

*2026-08-07. Closes the "unexplained" caveat in the 2026-08 score table.*

## Summary

The low-mass gamma-gamma deficit is **not a physics disagreement**. Agents and
the reference run line-for-line identical propagation code on statistically
identical phi fluxes. They differ in one integer: the number of deterministic
strata `K` used to sample the *parent* decay length.

Two separate findings fell out:

1. **The agents are wrong at mid coupling.** Every tooled trial in the 2026-08
   campaign chose `K` between 1 and 24; the reference uses `K = 40`. Too-small
   `K` biases the yields *low* by up to 20x.
2. **The reference is wrong at the highest declared coupling.** `K = 40` is
   itself under-converged there, sitting a factor **2.6-3.5 low** against the
   `K >= 160` limit, for every mass where a long-lived parent dominates. This
   affects 6 of the 48 graded points and the upper edge of the reach band.

## Mechanism

`parents.decay_parents_to_phi` replaces the parent's exponential decay-length
distribution with `K` deterministic quantiles:

```
ell_k = -lambda * ln(1 - (k + 1/2)/K),    lambda = beta*gamma * c*tau_parent
```

This is variance reduction, and it is unbiased only where the integrand is
smooth across a stratum. It is not smooth here. The geometry imposes a hard
production cut -- the phi must be made upstream of `z_prod = 50 m` -- and a hard
decay window, 112-163 m. A stratum that straddles an edge passes or fails
*wholesale* rather than contributing its true partial weight.

For a forward kaon, `lambda = beta*gamma * c*tau_K ~ 200 * 3.711 m ~ 742 m`, so
the entire accepted region is `ell < 50 m = 0.067 lambda`:

| K | lowest quantile | `ell` for a typical kaon | inside the 50 m cut? |
|---|---|---|---|
| 6 (agent) | `u = 0.083` | 64 m | **no** |
| 40 (reference) | `u = 0.0125` | 9.3 m | yes (3 of 40 strata) |

At `K = 6` the coarsest stratum already lands *past* the cut, so typical kaons
contribute nothing and only the low-`beta*gamma` tail survives. This is a
systematic, not noise: it does not move with the seed.

It is confined to the low-mass gamma-gamma region for a simple reason. There
the phi comes from kaons. At higher mass it comes from D/Ds, whose
`c*tau ~ 1e-4 m` means everything decays promptly, `vz ~ 0` always, and no
stratum can straddle anything.

## Evidence

Re-running the *reference* at `K = 6` reproduces the agent to a few percent on
every kinematic quantity, on the same code and the same flux:

| quantity | agent (Opus, seed1001) | ref K=6 | ref K=40 |
|---|---|---|---|
| `P(vz < 50 m)` | 0.1938 | 0.1875 | 0.1953 |
| `P(geometry)` | **0.01665** | **0.01616** | **0.02367** |
| `P(geometry \| vz < 50)` | 0.0859 | 0.0862 | 0.1212 |
| median `beta*gamma \| vz < 50` | 49.3 | 51.0 | 54.2 |
| `sum(weight)` | (scaled) | 0.08194 | 0.08194 |

Note the weight sum is identical -- normalization is preserved. The bias is
purely in the acceptance.

`N_sig` at the four declared `gg@0.06` couplings, as a ratio to the converged
`K = 160` value (50k parents held fixed, only `K` varying):

| K | g1 = 9.01e-4 | g2 = 2.26e-3 | g3 = 5.65e-3 | g4 = 1.41e-2 |
|---|---|---|---|---|
| 1 | 0.048 | 0.004 | 0.014 | 0.036 |
| 4 | 0.562 | 0.219 | 0.017 | 0.038 |
| 6 | 0.703 | 0.413 | 0.050 | 0.037 |
| 8 | 0.858 | 0.627 | 0.137 | 0.038 |
| 12 | 0.942 | 0.837 | 0.368 | 0.038 |
| 16 | 0.998 | 0.949 | 0.588 | 0.047 |
| 24 | 0.994 | 0.989 | 0.845 | 0.109 |
| **40 (reference)** | 0.999 | 1.010 | 0.993 | **0.363** |
| 160 | 1.000 | 1.000 | 1.000 | 1.000 |

The measured agent yields at `gg@0.06` match the `K = 6` row, which is what
closes the case:

| | g1 | g2 | g3 |
|---|---|---|---|
| predicted at K=6 | 0.70 | 0.41 | 0.050 |
| measured agent/reference | 0.95 | 0.34 | 0.065 |

Stratum count chosen per trial (period of the constant-direction block in
`llp/K/llp_K_m0.0600.jsonl`):

| system | K per trial |
|---|---|
| Haiku 4.5 | 5, 1, 1, 1 |
| Opus 4.8 | 6, 8, 8, 8, 16 |
| GPT-5.5 | 12, 4, 8, 24, 8 |
| GPT-5.6 | 16, 4, 8, 4, 4 |

**No trial reached 40.** Three Haiku trials used `K = 1`, the served tool's
default, meaning they never set the parameter at all.

## Scope of the reference defect

`N_sig(K=640) / N_sig(K=40)`, per declared point:

| point | g1 | g2 | g3 | g4 |
|---|---|---|---|---|
| gg@0.06 | 1.01 | 1.00 | 1.04 | **3.06** |
| gg@0.12 | 1.01 | 1.00 | 1.02 | **3.05** |
| gg@0.18 | 1.01 | 1.00 | 1.01 | **3.13** |
| gg@0.205 | 1.01 | 1.00 | 1.01 | **3.45** |
| mumu@0.23 | 1.02 | 1.00 | 1.01 | **3.13** |
| mumu@0.28 | 1.01 | 1.00 | 1.02 | **2.60** |
| mumu@0.34 | 1.01 | 1.00 | 1.02 | 1.13 |
| mumu@0.42 ... 1.2 | 1.00 | 1.00 | 1.00 | ~0.98 |

Convergence sets in by `K ~ 160`; `K = 640` and `K = 2560` agree to 1%.

`mumu@1.9` and `mumu@2.3` are not covered -- there the phi comes from J/psi and
psi(2S) through the *vector* assembler, and those parents are prompt, so the
stratification cannot bias them.

Note that `sigma` (0.0325 dex yield, 0.0036 dex contour) was measured between
two `K = 40` builds. It therefore measures Monte-Carlo noise correctly but is
**blind to this systematic**, which both builds share.

## Recommendations

1. **Raise `N_STRATA` from 40 to at least 160 and rebuild the ground truth.**
   Cost is linear in `K`: 4x memory and time. The three lower couplings will
   not move; the highest will rise by ~3x at the seven affected points, and the
   upper band edge with it.
2. **Change the served tool's default.** `meson_decay_to_llp.n_strata` defaults
   to `1`, the most biased possible value, and its description
   (">1 for a long-lived parent to sample the decay-length branch") gives no
   scale. It should default to a converged value and say what sets it -- the
   parent's `beta*gamma * c*tau` against the production cut. Three trials were
   penalised for accepting a default that cannot be right.
3. **Consider integrating the decay length analytically** rather than
   stratifying. The `ell`-dependence enters only through the geometry
   intersection and `P_dec`; a per-parent semi-analytic treatment would remove
   the convergence parameter entirely.
4. Whether this should be *graded* is a separate call. Choosing a converged
   `K` is a real part of doing the calculation correctly, so penalising it is
   defensible -- but only against a reference that is itself converged, which
   at the highest coupling this one is not.

## The fix, as applied (2026-08-07)

Rather than simply raising `K`, the strata are now **concentrated inside the
region that can contribute**. The geometry accepts a phi only if its parent
decayed upstream of `z_prod = 50 m`, so the exponential is stratified
*truncated* at the longest still-acceptable flight:

```
ell_max = z_prod / d_z          u_max = 1 - exp(-ell_max / lambda)
ell_k   = -lambda ln(1 - u_max (k + 1/2)/K)
weight  = parent_w * kappa * u_max / K
```

`u_max` is exactly the probability mass of the accepted region, so this is the
same integral -- the K strata now sample the conditional distribution inside
it. Short-lived parents have `u_max -> 1` and the two schemes coincide, as they
must. Backward-going parents (`d_z <= 0`) can never be accepted and get zero
weight.

This is strictly better than raising `K`. Measured against a converged
full-exponential `K = 2560` baseline, at `gg@0.06`:

| scheme | g1 | g2 | g3 | g4 |
|---|---|---|---|---|
| truncated K=8 | 0.995 | 0.998 | 0.996 | 1.032 |
| truncated K=16 | 1.005 | 1.007 | 1.002 | 1.000 |
| truncated K=40 | 0.994 | 0.991 | 0.996 | 1.015 |
| full-exp K=40 (old) | 0.989 | 1.000 | 0.959 | **0.328** |
| full-exp K=200 | 0.998 | 1.000 | 0.997 | 1.115 |

**Truncated K=8 beats untruncated K=200.** The residual ~1% is phi-direction
Monte Carlo, not the decay length.

Implementation:

- `parents.decay_parents_to_phi(..., z_prod_m=None)` -- opt-in. `None`
  reproduces the historical behaviour bit-for-bit (verified), so the figure
  scripts and `leptonic_contour.py` are untouched. Note this means
  `soln/figs/make_diphoton_figs.py` still carries the old bias; it is
  illustrative, not graded.
- `propagate.assemble_pseudoscalar(..., z_prod_m=None)` -- threads it through.
- `depr/derivation.py` -- passes `GEOM["z_prod_m"]`, and `CAP` raised
  100000 -> 600000. With the stratum axis converged by `K ~ 16`, the sampling
  budget is better spent on independent parents; 600000 exceeds the kaon count
  of a 200k-event flux, i.e. no subsampling at all.
- `reference/build_reference.py` -- the restore of the committed
  `soln/truth.json` now runs in a `finally` with SIGTERM converted to
  SystemExit. Previously it ran only on the success path, so a timeout landing
  between derivation's write and ours would have silently overwritten the
  committed reference with a partial rebuild. (This nearly happened: the first
  rebuild attempt was killed at a 10-minute cap.)

### Effect on the reference

Rebuilt from the same 200k flux, old vs new:

- Declared points that are shared between builds agree to **<= 0.003 dex**.
- `g_lo` (lower band edge) moves **<= 0.002 dex** -- it was never affected.
- `g_hi` (upper band edge) moves **up 0.085-0.109 dex**: the reach band extends
  22-29% further in coupling at every mass fed by a long-lived parent.
- Peak yields move <= 1.7% -- the peak sits at mid coupling, already converged.
- The declared couplings themselves re-place, because they bracket the peak
  using the band (e.g. `gg@0.06` g4: 1.41e-2 -> 1.93e-2).

sigma, re-measured from two independent same-size builds:

| | before | after |
|---|---|---|
| `sigma_peak` (yield) | 0.0325 | 0.0330 |
| `sigma_band` (contour) | 0.0036 | **0.00154** |

The contour floor improves 2.3x -- the upper edge is no longer set by a handful
of badly-placed strata. The yield floor is unchanged, as expected: it is set by
parent counts, not by stratification.

### Remaining limitation: parent statistics

Per-point `sigma_peak` tracks the number of available parents, not anything
physical:

| point | sigma_peak | parents |
|---|---|---|
| gg@0.06 | 0.0012 | 562,616 K |
| mumu@1.2 | 0.0712 | 1,765 Ds |
| mumu@1.9 | 0.1533 | 378 J/psi |
| mumu@2.3 | 0.1570 | **32 psi(2S)** |

The high-mass end is calibrated off 32 events. This is why a single scalar
sigma over-penalises the low-mass points and under-penalises the high-mass
ones, and why every `z` is provisional until per-point sigma lands. The flux is
being regenerated at 2M events (10x) to address it; kaons stay capped at
`CAP = 600000` so peak memory is unchanged (~7.5 GB), while the uncapped rare
parents grow 10x.

Note also `n_hard = 0` in every flux built so far: the generator supports
stitching a hard-charm sample at a pTHat cut, but it has never been used, so
forward charm comes from the soft sample alone. That is a separate question
from this one, and is not changed here.

## Reproducing

```bash
python benchmarks/llp_forward/soln/reference/check_strata_convergence.py
python benchmarks/llp_forward/soln/reference/check_strata_convergence.py \
    --point gg 0.06 --strata 1 6 40 640

# old vs new reference, point by point
python benchmarks/llp_forward/soln/reference/compare_truth.py \
    out/truth_a_k40untruncated.json out/truth_a.json
```
