# OpenVSP/VSPAERO parity tests

This suite creates a deterministic NACA 0012-style wing and compares the
official OpenVSP 3.51.2 distribution with the local full build. It runs thin
and thick geometry modes, each with a base alpha sweep and a default stability
analysis. Each generated model also runs `MassProp` with 81 slices and compares
mass, center of gravity, and inertia results. VSPAERO is restricted to one
OpenMP thread for repeatability.
Runtime fields such as `Analysis_Duration_Sec` are excluded from numerical
comparison.

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
Use `--custom-vspaero <path-to-vspaero.exe>` to test an incrementally built
solver without replacing a currently running or locked installed executable;
the custom distribution still supplies the matching OpenVSP Python package.

The report, `_work` directory, and generated parity-wing solver files are
ignored by Git. They are reproducible test artifacts and must not be committed.
Cp slicing is explicitly disabled because it is unrelated to coefficient
parity and would otherwise launch the separate `vsploads` postprocessor.

These are build-parity tests, not validation against experimental or
analytical aerodynamic data.

The suite also runs the custom `-state-sweep` mode in both thin and thick modes
and performs cross-mode checks against official-build results. Zero-rate states
are compared with the official normal sweep, while positive P/Q/R and control
states are compared with the corresponding official `-stab` perturbation cases. These checks use
`--state-atol` (default `5e-4`) and `--state-rtol` (default `1e-4`) because a
different case order can produce small wake-convergence differences even when
the solver implementation is equivalent.

## State Sweep optimization regression

Before changing native State Sweep behavior, snapshot the tested stable-main
executable. The snapshot and its SHA-256 metadata are local ignored artifacts:

```bat
python snapshot_stable_vspaero.py
```

Then run the optimization regression after every native solver change:

```bat
run_state_sweep_regression.bat
```

The regression generates deterministic thin and thick wing inputs and compares
every CSV value from the candidate solver with stable main. Separate scenarios
cover Alpha/Beta/Mach/Reynolds, negative/zero/positive physical P/Q/R, reduced
P/Q/R, negative/zero/positive control deflection, and a coupled rate/control
grid. Candidate-only checks verify that bounded process batches plus resume and
two disjoint global case ranges reproduce the canonical single-process output.
Stable-versus-candidate defaults are `atol=1e-8` and `rtol=1e-6`. Process and
range invariance use `atol=5e-4` and `rtol=1e-4`, matching the existing measured
wake-convergence sensitivity when a case begins in a fresh solver process.
Override them explicitly only when a documented numerical change requires it.
`--smoke` runs a smaller thin-wing
subset, and `--keep-work` retains all inputs, CSV files, checkpoints, and logs.
The detailed result is written to `state_sweep_regression_report.json`.

The stable snapshot protects custom functionality that the official executable
cannot run. It complements rather than replaces `run_parity_tests.bat`: native
changes must pass both suites.

Stable main's State Sweep used surface-inviscid rather than wake-induced
components for total `CFy/CFz`. Those two columns are therefore excluded only
from stable-snapshot comparison and are instead checked against the official
normal sweep and `-stab` results in both thin and thick modes. Candidate-only
batch/resume/range invariance continues to compare `CFy/CFz` normally.

`run_native_regression.bat` is the mandatory combined gate and runs official
parity first, followed by stable-main State Sweep regression. The batch launchers
prefer the active Conda environment's Python executable when available.
