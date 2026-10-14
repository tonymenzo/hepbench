---
name: Writing Pythia 8 run cards for forward production
description: Process selection, normalisation and particle harvesting for forward / small-angle Pythia 8 studies - the settings that change the answer, and the traps that silently rescale it.
bundle: llp
---

# Pythia 8 run cards for forward production

Forward studies - anything selecting particles at small polar angle to the beam,
whether a far detector, a beam dump, or a forward tagger - fail differently from
central ones. The hard process is usually irrelevant; the yield comes from the
soft and diffractive components, and the answer is set by three choices that are
easy to get wrong and produce no error message when you do:

1. **which process classes you switch on**,
2. **how you turn generated events into a rate**,
3. **whether the particles you want still exist by the time you look**.

Each can move a forward yield by tens of percent to a factor of several. None of
them announce themselves. This guide is about those three, in that order.

Settings below are quoted with their real names and defaults from the Pythia 8.3
`xmldoc`. Cross-sections are quoted from a 13.6 TeV Monash run and are there for
**orientation only** - regenerate them for your own beam energy and tune rather
than copying the numbers.

---

## 1. Process selection

### The forward region is soft-dominated

At small angle you are looking at the fragmentation region, not the hard
scatter. Light-hadron production there is dominated by non-diffractive
minimum-bias events plus a genuinely important diffractive component: single
diffraction leaves one proton intact and pushes its dissociation products to
very high rapidity, which is exactly where a forward acceptance sits. Selecting
`SoftQCD:nonDiffractive` alone is a common way to quietly lose forward yield.

### The soft switches

| switch | codes | includes |
|---|---|---|
| `SoftQCD:nonDiffractive` | 101 | minimum-bias only |
| `SoftQCD:inelastic` | 101, 103, 104, 105, 106 | non-diffractive + all diffraction, **no elastic** |
| `SoftQCD:all` | + 102 | the above **plus elastic** |

All default `off`. A representative 13.6 TeV Monash breakdown:

```
non-diffractive        101    56.87 mb
elastic                102    22.45 mb     <- produces no hadrons
single diffractive AX  103     6.43 mb
single diffractive XB  104     6.43 mb
double diffractive     105     8.85 mb
                     ---------------
   SoftQCD:all               101.04 mb
   SoftQCD:inelastic          78.58 mb     (the same, less elastic)
```

so `sigma(all)/sigma(inelastic) = 1.286` - the size of the elastic trap below.

**`SoftQCD:inelastic` is the right default for a per-collision flux.** Every
generated event is then one inelastic collision, so the per-event weight is
simply `1/N_gen` and there is nothing to get wrong.

**The elastic trap.** `SoftQCD:all` adds code 102, which is ~22% of the total at
13.6 TeV and produces no hadrons at all. If you use `SoftQCD:all` and then weight
each event as one inelastic collision, you are low by `sigma_gen / sigma_inel`
(~1.28 here) because a fifth of your sample was empty. `SoftQCD:all` is fine, but
only with the cross-section weight of section 2.

### Do not mix soft and hard QCD

Straight from the Pythia documentation (`QCDSoftProcesses.xml`):

> there is a considerable amount of overlap between the soft and hard QCD process
> classes, so that you are likely to double-count if you include both in a run.

The reason is in the `SoftQCD:nonDiffractive` entry: its formalism *"is based on
an eikonalized description of all the hard QCD processes, so includes them in
combination with low-pT events"*. Minimum-bias events already contain hard
scatters, generated through the multiparton-interaction machinery. Adding
`HardQCD:*` on top counts them twice.

If you need hard-process statistics you cannot get from minimum bias, generate a
**separate** sample with its own `PhaseSpace:pTHatMin` and combine the two by
cross section, with an explicit stitching scale - do not switch both on in one
run.

### Onia are a different case, and this one is counter-intuitive

`Onia:all`, `Charmonium:all` and `Bottomonium:all` are separate process classes
from `HardQCD:*`. MPI's eikonalised hard component is QCD 2->2 only, so the NRQCD
onia processes are **not** regenerated inside MPI. Combining them with `SoftQCD`
is therefore additive rather than double-counted, even though Pythia will still
print

```
Warning in Pythia::init: should not combine softQCD processes with hard ones
```

Verified at 13.6 TeV / Monash, forward J/psi per inelastic collision:

```
SoftQCD:all + Onia:all     1.074e-3      <- the two contributions, summed
Onia:all alone             8.07e-4       (NRQCD prompt production)
SoftQCD:all, Onia off      2.48e-4       (string-fragmentation charmonium)
                           --------
                    sum    1.055e-3      consistent with the combined run
```

That decomposition is the check to run if you are unsure whether a given
combination double-counts: generate the combined sample and the two ingredients
separately, and confirm the parts add up. If the combined run **exceeds** the
sum, you are double-counting.

Note the third row. A minimum-bias sample makes quarkonium on its own, through
string fragmentation, with no NRQCD process enabled. Running only a dedicated
onia sample therefore **undercounts** the total quarkonium flux - it is not a
matter of taste, it is a missing production mechanism. Check whether the
quarkonium in your soft sample is prompt or feed-down by walking the mother
chain for a b-hadron ancestor (`|id|` in 500-599 or 5000-5999) before deciding
what to combine.

### Heavy flavour more generally

Charm and beauty hadrons at forward rapidity come predominantly from the soft
sample via gluon splitting and MPI, not from a dedicated hard sample. Reach for
`HardQCD:hardccbar` / `HardQCD:hardbbbar` only to *top up* statistics at high
pT, in a separate run, stitched by cross section.

---

## 2. Normalisation

This is where forward analyses most often go wrong by a constant factor, and a
constant factor is invisible in any shape comparison.

### The general weight

Pythia reports the generated cross section after `stat()`:

```python
sigma_mb = pythia.infoPython().sigmaGen()     # mb, finalised after stat()
```

To express a yield per inelastic collision, the weight carried by each generated
event is

```
w = sigma_gen / (N_gen * sigma_inel)
```

with `sigma_inel` the inelastic cross section you are normalising to. Then a
harvested particle's contribution to an absolute yield is `w * N_int`, with
`N_int` the number of primary interactions in your exposure.

Two special cases worth internalising:

- **`SoftQCD:inelastic`**: `sigma_gen` *is* the inelastic cross section, so
  `w = 1/N_gen`. Simplest and least error-prone.
- **`SoftQCD:all`**: `sigma_gen` includes elastic, so the ratio
  `sigma_gen/sigma_inel > 1` is doing real work - it converts "per generated
  event" into "per inelastic collision" by discounting the empty elastic events.

### Always cross-check your pinned sigma_inel against Pythia's own

If your task pins an inelastic cross section, confirm the generator agrees with
it, because your weight mixes the two. Sum the per-process cross sections and
subtract elastic:

```python
info = pythia.infoPython()
tot = info.sigmaGen()
el  = sum(info.sigmaGen(c) for c in info.codesHard()
          if "elastic" in info.nameProc(c).lower())
print("Pythia inelastic:", tot - el)      # 78.58 mb, SoftQCD:all at 13.6 TeV
```

(that figure is soft processes only; switching `Onia:all` on adds ~1.2 mb to
`sigmaGen`, so compare like with like.)

A few percent is normal - tunes differ. A factor is a bug in your weighting.

### Prescaling

Abundant species blow up memory long before they matter. Keep 1 in `n` and
multiply that species' weight by `n`. This is unbiased, but the prescale factor
must ride with the weight, never with the count.

---

## 3. Harvesting particles before they decay

If you want a *parent flux* - the particles as produced, before the generator
decays them - you must stop the decay, because by the time an event is final
those particles are gone.

Per species, which is the precise instrument:

```
443:mayDecay = off        # J/psi
431:mayDecay = off        # D_s
```

Or by lifetime, which is blunter and catches everything long-lived:

```
ParticleDecays:limitTau0 = on     # default off
ParticleDecays:tau0Max   = 10     # mm/c, default 10
```

Two cautions:

- **Switching off a decay changes the rest of the event.** The daughters are no
  longer there to shower, hadronise or feed the underlying event. Do it only for
  the species you are harvesting, and never for a species whose daughters you
  also count.
- **Feed-down disappears with it.** If species A decays to species B and you
  disable A, you lose B's feed-down component. When both matter, harvest A at
  production and add B's feed-down from a separate accounting.

### Selecting the forward cone

Take the angle from the momentum, not from an approximation:

```python
if part.pz() > 0 and part.p().theta() < theta_max:
    ...
```

**The hemisphere trap.** `pp` collisions are symmetric, so both beam directions
produce a forward cone. If you select on `abs(pz)` - or on `abs(eta)` - you fold
two cones into one and **double** the flux relative to a single-arm detector.
Either select one hemisphere (`pz > 0`), or fold and carry a compensating factor
of `0.5` in the weight. Folding is worth doing for the factor-2 gain in
statistics, but the compensating weight must be there, and it is exactly the kind
of error that survives every shape check and every internal consistency test.

Also note that a decay product is **not** collinear with its parent. Selecting
parents inside your detector's geometric half-angle will lose daughters that
would have hit it; harvest parents in a comfortably wider cone than the
acceptance you ultimately apply, and verify the retention has plateaued.

---

## 4. Tune, PDF and beam

`Tune:pp` (default 14) sets MPI, shower, PDF and fragmentation together. It
changes forward strangeness and charm, so it changes the answer and must be
recorded alongside any forward yield. Common choices:

| value | tune |
|---|---|
| 14 | Monash 2013 - the usual reference point |
| 18 | CMS CUETP8M1 (NNPDF2.3LO) |
| 21 | ATLAS A14 (NNPDF2.3LO) |
| 33 | Detroit (2021), UE+MB to RHIC and Tevatron |

Setting `PDF:pSet` after a tune overrides that tune's PDF and silently
decorrelates it from the parameters it was fitted with - if you change the PDF,
say so explicitly and expect to revalidate.

Forward production probes very asymmetric parton momenta (one large `x`, one
small), so it is more PDF-sensitive than a central measurement at the same
energy. Treat the PDF as a systematic, not a detail.

Beam basics: `Beams:idA` / `Beams:idB` (default 2212), `Beams:frameType`
(1 = collider CM), `Beams:eCM`.

---

## 5. Reproducibility

```
Random:setSeed = on        # without this, every run repeats the same sequence
Random:seed    = 12345     # default -1; 0 seeds from the clock
```

`Random:seed = -1` (the default) means **every job produces identical events**.
Parallel jobs need distinct seeds or you will merge N copies of one sample and
mistake the shrinking error bar for real statistics.

Quiet, machine-friendly output:

```
Print:quiet                        = on
Next:numberCount                   = 0      # default 1000
Init:showChangedSettings           = off
Init:showChangedParticleData       = off
Init:showProcesses                 = off
Init:showMultipartonInteractions   = off
Check:event                        = off    # only once validated
```

Record with every flux you produce: **Pythia version, tune, `sigma_gen`,
`N_gen`, the seed, the process switches, and the angular cut**. A forward flux
without these is not reproducible, and version matters - forward hadron rates
shift between releases.

---

## 6. Checklist

Before trusting a forward flux:

- [ ] Process class covers diffraction, not just non-diffractive
- [ ] Elastic either excluded (`SoftQCD:inelastic`) or paid for by the
      cross-section weight
- [ ] No `SoftQCD` + `HardQCD` in one run
- [ ] Any soft+onia combination verified additive (parts sum to the whole)
- [ ] Pythia's own inelastic cross section agrees with the one you normalise to
- [ ] Harvested species have `mayDecay = off`, and nothing you count is a
      daughter of something you disabled
- [ ] One hemisphere selected, or folded **with** the 0.5 weight
- [ ] Harvest cone wider than the final acceptance, retention plateaued
- [ ] Seeds distinct across parallel jobs
- [ ] Version, tune, `sigma_gen`, `N_gen`, seed all recorded

## 7. Common failure modes

| symptom | likely cause |
|---|---|
| yield low by ~1.3 at 13.6 TeV | `SoftQCD:all` weighted as `1/N_gen` (elastic dilution) |
| yield high by exactly 2 | both hemispheres folded without the 0.5 weight |
| quarkonium low by ~1.3 | dedicated onia sample only; missing the soft-sample component |
| hard-tail yield too high | `SoftQCD` and `HardQCD` in the same run |
| error bars shrink but the mean does not settle | identical seeds across jobs |
| forward yield low, shape right | diffraction dropped (`nonDiffractive` alone) |
| parents absent from the record | `mayDecay` left on; they decayed before you looked |
| `Pythia.init()` returns False, no message | `PYTHIA8DATA` / xmldoc problem, not physics |

---

## 8. Starting-point run cards

Both are also on disk beside this file in `cards/`, but they are reproduced here
so this guide is self-contained wherever it is delivered.

### Baseline forward light-hadron flux

```
! SoftQCD:inelastic covers non-diffractive AND diffractive production
! (101, 103, 104, 105, 106) but excludes elastic (102), so every generated
! event is one inelastic collision and the per-event weight is exactly
! 1/N_gen with no cross-section bookkeeping. Use SoftQCD:all only with the
! sigma_gen/(N_gen*sigma_inel) weight. Never add HardQCD:* here.
Beams:idA       = 2212
Beams:idB       = 2212
Beams:frameType = 1                  ! collider CM frame
Beams:eCM       = 13600.             ! CHANGE ME
Tune:pp         = 14                 ! Monash 2013

SoftQCD:inelastic = on
HardQCD:all       = off

! Harvest parents at production -- list every species you intend to count.
! Anything not listed decays normally. Never disable a species whose
! daughters you also count.
! 321:mayDecay    = off              ! K+-
! 431:mayDecay    = off              ! D_s+-

Random:setSeed  = on
Random:seed     = 12345              ! CHANGE ME -- distinct per parallel job

Print:quiet                      = on
Next:numberCount                 = 0
Init:showChangedSettings         = off
Init:showChangedParticleData     = off
Init:showProcesses               = off
Init:showMultipartonInteractions = off
Check:event                      = off   ! turn on while validating
```

### Forward flux including quarkonium

```
! ONE inclusive run, Onia switched on alongside the soft processes. This is
! NOT the same as running a dedicated onia sample separately: a minimum-bias
! sample makes quarkonium on its own through string fragmentation, which the
! dedicated NRQCD run does not have. See section 1.
Beams:idA       = 2212
Beams:idB       = 2212
Beams:frameType = 1
Beams:eCM       = 13600.             ! CHANGE ME
Tune:pp         = 14

SoftQCD:inelastic = on               ! or SoftQCD:all, with the sigma_gen weight
HardQCD:all       = off              ! never on together with SoftQCD
Onia:all          = on               ! Charmonium:all / Bottomonium:all to narrow

! 443:mayDecay    = off              ! J/psi
! 100443:mayDecay = off              ! psi(2S)

Random:setSeed  = on
Random:seed     = 12345              ! CHANGE ME -- distinct per parallel job

Print:quiet                      = on
Next:numberCount                 = 0
Init:showChangedSettings         = off
Init:showChangedParticleData     = off
Init:showProcesses               = off
Init:showMultipartonInteractions = off
Check:event                      = off
```
