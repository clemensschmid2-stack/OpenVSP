# OpenVSP/VSPAERO parity tests

This suite creates a deterministic NACA 0012-style wing and compares the
official OpenVSP 3.51.2 distribution with the local full build. It runs thin
and thick geometry modes, each with a base alpha sweep and a default stability
analysis. VSPAERO is restricted to one OpenMP thread for repeatability.

Run from a Python 3.13 environment compatible with the packaged OpenVSP API:

```bat
run_parity_tests.bat
```

The default comparison accepts a value when:

```text
abs(custom - official) <= 1e-8 + 1e-6 * abs(official)
```

Use `--rtol` and `--atol` to change the tolerances. The detailed result is
written to `parity_report.json`. Pass `--keep-work` to retain solver inputs,
outputs, and logs under `_work` for diagnosis.

The report, `_work` directory, and generated parity-wing solver files are
ignored by Git. They are reproducible test artifacts and must not be committed.
Cp slicing is explicitly disabled because it is unrelated to coefficient
parity and would otherwise launch the separate `vsploads` postprocessor.

These are build-parity tests, not validation against experimental or
analytical aerodynamic data.

The suite also runs the custom `-state-sweep` mode and performs cross-mode
checks against official-build results. Zero-rate states are compared with the
official normal sweep, while positive P/Q/R and control states are compared
with the corresponding official `-stab` perturbation cases. These checks use
`--state-atol` (default `5e-4`) and `--state-rtol` (default `1e-4`) because a
different case order can produce small wake-convergence differences even when
the solver implementation is equivalent.
