# `symbolic` — tree-level widths and cross sections

Fourteen tasks on **generic toy field theories**: a scalar decaying to a fermion pair through a stated Yukawa term, never the Higgs. Every interaction Lagrangian is given in the prompt, which fixes the coupling normalisation and makes the task computable without particle-data recall. The agent returns numerical values and closed-form expressions, graded against an independently verified ground truth.

## Tasks

Ten two-body decays cover every renormalisable three-point vertex among scalars (S), Dirac fermions (F), and massive vectors (V), with each leg in turn as the parent.

| Task | Vertex | What it probes |
|---|---|---|
| `decay_S_to_FFbar` | Yukawa | $\beta^3$ against $\beta$, the sign of chiral interference |
| `decay_S_to_SS` | cubic scalar | identical-particle symmetry factor, Källén phase space |
| `decay_F_to_FprimeS` | Yukawa, fermion parent | the $+4y_Ly_R m_F m_f$ interference term |
| `decay_V_to_FFbar` | gauge, V and V−A | polarisation average, $(1+2x)$ and $(1-4x)$ factors |
| `decay_F_to_FpV` | gauge, fermion parent | the longitudinal $p^\mu p^\nu/m_V^2$ piece |
| `decay_S_to_VV` | SVV | the $(1-4x+12x^2)$ factor, the identical-vector symmetry factor |
| `decay_V_to_SS` | derivative SSV, vector parent | p-wave $\Gamma\sim\lambda^{3/2}$ |
| `decay_S_to_SpV` | derivative SSV, scalar parent | p-wave $\Gamma\sim\lambda^{3/2}$ |
| `decay_V_to_SVp` | SVV, vector parent | the $Z'\to hZ$ structure |
| `decay_V_to_VVp` | triple gauge | the $m_V^5/(m_1^2m_2^2)$ enhancement; values only |

Four further tasks: `decay_F_to_3body`, a three-body decay through a heavy mediator; `xsec_SS_to_SS` and `xsec_FFbar_to_FFbar`, $2\to2$ cross sections; and `composite_toy_model`, a full profile of one Lagrangian with widths, branching ratios, a lifetime, and an annihilation cross section.

Conventions are fixed in [`CONVENTIONS.md`](CONVENTIONS.md) and enforced by `tests/test_symbolic_conventions_audit.py`.

## Variants

The ground truth and rubric are shared, so reach is comparable across variants.

| Variant | What the prompt supplies |
|---|---|
| `unguided` (default) | The request as a physicist would type it: physics, parameters, conventions, and the grading interface. No schema, example, or exactness instruction. Also asks for `results/derivation.md`, which is kept but not graded. |
| `scaffold_minimal` | The same with the minimal grading interface spelled out. Eight tasks. |
| `guided` | Fully specified: output schema, symbol names, an example formula, and an instruction to give the exact result. |
| `skin_sm` | `guided` for `decay_S_to_FFbar` with real particle names and non-SM values, to separate recall from computation. |

## Loadouts

| Loadout | Serves |
|---|---|
| `core_only` | The harness's own tools. The agent derives the result and evaluates it in Python. |
| `tools_eda` | The same plus HEPTAPOD's `ComputeDecayRate` and `ComputeCrossSection`, served from the `symbolic-eda` loadout, and an addendum declaring them the intended path. Needs `wolframscript_path` configured with FeynCalc installed. |

Both arms keep Python, so numerical evaluation is not part of the difference. The loadout serves two tools and no others; [`symbolic-eda.yaml`](../../.toolbase/loadouts/symbolic-eda.yaml) says why.

## Grading

The deliverable is `results/answer.json`. Three checks in [`_shared/checks.py`](_shared/checks.py):

- `answer_value`: each number climbs a ladder of order of magnitude, 10%, and 1%.
- `answer_formula`: a closed form is parsed with SymPy against a declared symbol alphabet and compared with the reference at fixed points of the declared domain. Equivalent rearrangements pass; a wrong factor cannot.
- `answer_consistency`: relations among the agent's own fields, used by the composite task.

A missing or malformed answer file is a delivery failure. Once that gate passes, each quantity earns credit independently.

## Ground truth

Each task's `ground_truth/derivation.py` states its conventions, cites the literature for every formula, and asserts agreement with an independent numerical computation in [`_shared/dirac_numeric.py`](_shared/dirac_numeric.py): explicit Dirac matrices, spinors, and polarisation vectors with direct phase-space integration. `tests/test_symbolic_rubrics.py` self-grades every task. Parameter values are deliberately non-round.

## Oracle policy

The answers are committed, since the grader needs them. Under Claude Code and Codex every harness definition sets `sandbox: true` and disallows web tools, so the benchmark directory and the git object store are unreadable from the trial. Under the orchestral harness the file tools are jailed and the shell and web tools are removed. After any run, scan the transcripts for answer-key access:

```bash
python scripts/audit_oracle_access.py runs/<run_id> --zero
```

## Running

```bash
toolbench run --benchmark benchmarks/symbolic/decay_S_to_FFbar \
    --harnesses claude-code/default --model claude-haiku-4-5 \
    --variants unguided --loadouts core_only,tools_eda --n 10 --max-cost-usd 10
```
