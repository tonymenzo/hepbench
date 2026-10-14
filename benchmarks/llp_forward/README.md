# `llp_forward` — forward long-lived-particle reach

An agent runs the forward-LLP phenomenology pipeline for a muon-philic scalar: generate a forward meson flux with Pythia, decay it to the scalar across every open production channel, propagate the scalars through a decay volume, and report the expected signal yield at a declared set of mass and coupling points. The result is graded against a committed, rerunnable reference.

## Physics

A real scalar with $\mathcal L \supset -\tfrac12 m_\phi^2\phi^2 - g\,\phi\,\bar\mu\mu$. The single coupling $g$ controls production and decay, and the kinematics are independent of it, so one event sample reweights exactly across the coupling axis.

- **Production** ($\propto g^2$): pseudoscalar $M\to\mu\nu\phi$ for $\pi, K, D, D_s$ and vector $V\to\mu^+\mu^-\phi$ for $\rho,\omega,\phi,J/\psi,\psi(2S)$, from a Pythia forward flux.
- **Decay** ($\propto g^2$): $\phi\to\mu^+\mu^-$ at tree level above $2m_\mu$, and $\phi\to\gamma\gamma$ through the one-loop muon triangle, the only visible mode below it.
- **Geometry**: a forward cylindrical decay volume behind an absorber, with the parent's decay-in-flight vertex taken into account.

Two searches, a two-track $\mu\mu$ acceptance and a collinear $\gamma\gamma$ acceptance, each with its own yield.

## Deliverable and grading

The agent writes `results/answer.json` with the width probes and the signal yield $N_{\rm sig}$ at the declared $(\text{search}, m_\phi, g)$ points, a flat yield scan in `results/scan.csv`, and the sensitivity region in `results/reach.pdf`. The grader, not the agent, reduces the yields to the $N_{\rm sig}=3$ boundary, so the graded quantity is the well-conditioned yield and a hand-drawn contour cannot pass.

The rubric has a structural gate followed by independently credited stages: widths and lifetime, channel coverage, the yield scan (the largest weight), the lower and upper sensitivity boundaries, false reach outside the reference-sensitive region, and the plot. Yields and boundaries are scored on a log-ratio distance to the reference, standardised by the reference's own measured Monte Carlo precision. The complete check parameters are in [`benchmark.yaml`](benchmark.yaml); the reference and its derivation are in [`soln/`](soln/README.md).

## Variants

The variant axis is how much the prompt supplies.

| Variant | What the agent is given |
|---|---|
| `bare` | The task in the user prompt and one file, the output schema. The out-of-the-box condition used in the paper. |
| `defined` (default) | Full sandbox data products, with the decay widths stated, so the graded task is the simulation pipeline. |
| `derived` | The same sandbox with the widths withheld; the agent derives them from the Lagrangian first. |
| `recipes` | The `defined` task with a core-tools system prompt in place of the tool-oriented one. |
| `defined_nonorm`, `recipes_nonorm` | The normalisation ablation: the same task with the flux-normalisation procedure withheld. |

## Loadouts

| Loadout | Serves |
|---|---|
| `core_only` | The harness's own shell, file, and Python tools. |
| `tools_defined` (default) | HEPTAPOD's `llp` pipeline and `PythiaFromRunCard`, the run-card skill, and a short addendum stating the toolkit is the intended path. |
| `tools_defined_unprompted` | The same tools and skill without the addendum. |
| `tools_derived` | `tools_defined` plus the `eda` symbolic tools, for the `derived` variant. |

No loadout serves literature, particle-data, or web tools.

## Running

```bash
toolbench run --benchmark benchmarks/llp_forward \
    --harnesses claude-code/default --model claude-opus-4-8 \
    --variants bare --loadouts core_only,tools_defined --n 5 --max-cost-usd 20
```

The tools arms need HEPTAPOD installed and selected (`tb use heptapod@3.0.0`); `tools_derived` also needs `wolframscript_path` configured. A trial takes tens of minutes, most of it Pythia.
