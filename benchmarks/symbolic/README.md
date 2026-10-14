# `symbolic` — tree-level widths and cross sections

The symbolic benchmark family contains fourteen tasks in generic toy field theories. Each prompt specifies the interaction Lagrangian and coupling normalisation, allowing the task to be solved without recalling particle data. For example, a Yukawa decay task describes a generic scalar decaying to a fermion pair rather than a Higgs decay. The agent returns numerical values and closed-form expressions, graded against an independently verified reference.

From the repository root, open the recorded symbolic campaign in the toolbench dashboard:

```bash
toolbench dashboard campaigns/symbolic/trials --port 0
```

The `--port 0` option selects an available port and prints the dashboard URL in the terminal. Open that URL in your browser, select a run, then select a trial to inspect its grades. See the [campaign README](../../campaigns/symbolic/README.md) for transcripts, preserved files, and regrading notes, or the [Quickstart](../../README.md#quickstart) to install the runner.

## Tasks

Ten two-body decays cover every renormalisable three-point vertex among scalars (S), Dirac fermions (F), and massive vectors (V), with each leg in turn as the parent.

| Task | Vertex | What it probes |
|---|---|---|
| `decay_S_to_FFbar` | Yukawa | $\beta^3$ against $\beta$, the sign of chiral interference |
| `decay_S_to_SS` | cubic scalar | identical-particle symmetry factor, Källén phase space |
| `decay_F_to_FprimeS` | Yukawa, fermion parent | the $+4y_Ly_R m_F m_f$ interference term |
| `decay_V_to_FFbar` | gauge, $V$ and $V-A$ | polarisation average, $(1+2x)$ and $(1-4x)$ factors |
| `decay_F_to_FpV` | gauge, fermion parent | the longitudinal $p^\mu p^\nu/m_V^2$ term |
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
| `unguided` (default) | Physics, parameters, conventions, and the grading interface, without a schema, example, or exactness instruction. Also requests `results/derivation.md`, which is preserved but not graded. |
| `scaffold_minimal` | The same task with an explicit minimal grading interface. Available for eight tasks. |
| `guided` | Fully specified: output schema, symbol names, an example formula, and an instruction to give the exact result. |

## Loadouts

| Loadout | Serves |
|---|---|
| `core_only` | The harness's own tools. The agent derives the result and evaluates it in Python. |
| `tools_eda` | The same plus HEPTAPOD's `ComputeDecayRate` and `ComputeCrossSection`, served from the `symbolic-eda` loadout, and an addendum declaring them the intended path. Needs `wolframscript_path` configured with FeynCalc installed. |

Both loadouts retain Python for numerical evaluation. The domain loadout serves only these two tools; the selection is documented in [`symbolic-eda.yaml`](../../.toolbase/loadouts/symbolic-eda.yaml).

The harness definitions and both loadouts are shared by every task. They live in [`_shared/`](_shared/) together with the checks, and each task's `benchmark.yaml` declares `extends: ../_shared` to inherit them. A file of the same name inside a task directory takes precedence.

## Deliverable and grading

The agent writes `results/answer.json`, evaluated by three checks in [`_shared/checks.py`](_shared/checks.py):

- `answer_value`: numerical answers receive credit at successive tolerances: order of magnitude, 10%, and 1%.
- `answer_formula`: a closed form is parsed with SymPy against a declared symbol alphabet and compared with the reference at fixed points of the declared domain. Algebraically equivalent expressions are accepted.
- `answer_consistency`: relations among the agent's own fields, used by the composite task.

A missing or malformed answer file is a delivery failure. After this structural check passes, each quantity receives credit independently.

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

Run this command from the repository root after installing and selecting HEPTAPOD (`tb use heptapod@3.0.0`). The `tools_eda` loadout also requires FeynCalc and a configured `wolframscript_path`; see [Configure domain tools](../../README.md#configure-domain-tools). Use `--loadouts core_only` to run with only the agent's built-in tools.

To inspect the latest local run, open another terminal in the repository root and launch:

```bash
toolbench dashboard --port 0
```

Open the URL printed in the terminal. Stop the dashboard with `Ctrl+C` when finished.
