# Benchmarks

HEPBench includes symbolic calculations and a forward long-lived-particle search. Run commands from the repository root, using the task directory as the `--benchmark` argument. See [Run a benchmark](../README.md#run-a-benchmark) for installation, execution, and dashboard instructions.

| Benchmark | Tasks | Description |
|---|:---:|---|
| [`symbolic`](symbolic/README.md) | 14 | Tree-level decay widths and cross sections in toy field theories, with numerical and closed-form answers. |
| [`llp_forward`](llp_forward/README.md) | 1 | A forward long-lived-particle search: meson flux generation, scalar production and decay, detector propagation, signal yields, and sensitivity. |

## Symbolic calculations

Select an individual task directory rather than the `symbolic/` parent directory. The [symbolic README](symbolic/README.md) describes the physics, variants, loadouts, and grading; [CONVENTIONS.md](symbolic/CONVENTIONS.md) defines the shared conventions.

| Task | `--benchmark` path |
|---|---|
| [`composite_toy_model`](symbolic/composite_toy_model/) | `benchmarks/symbolic/composite_toy_model` |
| [`decay_F_to_3body`](symbolic/decay_F_to_3body/) | `benchmarks/symbolic/decay_F_to_3body` |
| [`decay_F_to_FpV`](symbolic/decay_F_to_FpV/) | `benchmarks/symbolic/decay_F_to_FpV` |
| [`decay_F_to_FprimeS`](symbolic/decay_F_to_FprimeS/) | `benchmarks/symbolic/decay_F_to_FprimeS` |
| [`decay_S_to_FFbar`](symbolic/decay_S_to_FFbar/) | `benchmarks/symbolic/decay_S_to_FFbar` |
| [`decay_S_to_SS`](symbolic/decay_S_to_SS/) | `benchmarks/symbolic/decay_S_to_SS` |
| [`decay_S_to_SpV`](symbolic/decay_S_to_SpV/) | `benchmarks/symbolic/decay_S_to_SpV` |
| [`decay_S_to_VV`](symbolic/decay_S_to_VV/) | `benchmarks/symbolic/decay_S_to_VV` |
| [`decay_V_to_FFbar`](symbolic/decay_V_to_FFbar/) | `benchmarks/symbolic/decay_V_to_FFbar` |
| [`decay_V_to_SS`](symbolic/decay_V_to_SS/) | `benchmarks/symbolic/decay_V_to_SS` |
| [`decay_V_to_SVp`](symbolic/decay_V_to_SVp/) | `benchmarks/symbolic/decay_V_to_SVp` |
| [`decay_V_to_VVp`](symbolic/decay_V_to_VVp/) | `benchmarks/symbolic/decay_V_to_VVp` |
| [`xsec_FFbar_to_FFbar`](symbolic/xsec_FFbar_to_FFbar/) | `benchmarks/symbolic/xsec_FFbar_to_FFbar` |
| [`xsec_SS_to_SS`](symbolic/xsec_SS_to_SS/) | `benchmarks/symbolic/xsec_SS_to_SS` |

## Forward long-lived-particle search

Use `--benchmark benchmarks/llp_forward`. The [forward-LLP README](llp_forward/README.md) describes the simulation pipeline, variants, loadouts, and grading.

## Recorded campaigns

The benchmark definitions above specify tasks for new runs. To inspect the existing results, see the [campaign index](../campaigns/README.md), including dashboard commands and instructions for downloading trial evidence.
