# Modifications

This fork is derived from NASA's OpenVSP project.

## 2026-08-28 - Clemens Schmid

- Added `-stab-control-select <csv>` for selecting one-based VSPAERO control
  groups during `-stab`. Only selected groups receive positive and negative
  perturbation solves and appear as control columns in the explicit Forward,
  Backward, and Central derivative tables. Per-group metadata records
  `selected=yes/no`; omitting the option retains the official all-groups
  behavior.
- Added official-reference-anchored parity coverage for the selective-control
  path. The selected group's three derivative tables must match the all-control
  baseline that has already passed the packaged official build, and a
  one-operating-point/one-group run must execute exactly base, positive, and
  negative solver cases.

## 2026-08-27 - Clemens Schmid

- Added opt-in `-steady-optimize` and `-stab-optimize` modes using the validated
  State Sweep early-convergence criteria. Regular sweep cases and stability
  perturbations remain entirely independent because tested cross-case and cross-perturbation
  interaction-list/preconditioner reuse amplified small coefficient changes in
  the finite-difference derivatives. An experimental regular-sweep wake warm
  start was likewise rejected after showing incidence-traversal dependence at
  low wake-iteration counts. Strict optimized-mode tests against baselines
  already passing the packaged official build enforce this decision.
- Added `-solver-opt-profile` timing output for optimized regular and stability
  runs. Default steady and `-stab` execution remains unchanged.
- Added optimized-mode parity checks to the mandatory official-reference suite.
  Thin/thick steady and stability reruns pass exactly when early termination
  does not trigger. A thin 12-iteration smoke case stopped after 7 iterations
  with the documented default tolerances and reduced reported solve time from
  0.334 s to 0.239 s on the test machine; this early-exit result is intentionally
  tolerance-controlled rather than strict full-iteration parity.
- Added opt-in `-state-fast-order` execution for native State Sweep. It makes
  P/Q/R the innermost axes and keeps Mach/control combinations contiguous, then
  reuses the initial surface interaction list and matrix preconditioner while
  those invariant inputs are unchanged. Alpha, beta, and rates remain fully
  solved states; wake initialization, wake relaxation, and force integration
  still run independently for every case.
- Retained the fixed-surface interaction list through steady wake-relaxation
  iterations in fast-order State Sweep. The list is a function of surface
  geometry, Mach, and `FarAway`; wake-node locations are not inputs to its
  construction. Wake geometry, induced velocities, circulation, and loads are
  still updated and solved on every iteration.
- Added regression coverage comparing fast-order results by physical state
  against canonical traversal, in addition to official-reference parity and
  the existing batching/range invariance checks. Numerical parity is defined
  exclusively against the packaged official OpenVSP 3.51.2 reference build;
  frozen custom binaries are retained only for optional historical regression.
- Added a pre-implementation continuation validation harness and acceptance
  specification covering traversal dependence, repetition, process boundaries,
  forced interruption/resume, difficult states, incompatible-state fallback,
  optional physical-side loads, and profiling/iteration accounting.
- Added opt-in State Sweep continuation: compatible adjacent cases warm-start
  both circulation and relaxed wake geometry, while refreshing the free stream
  for each alpha/beta/rate state. Added a three-part early wake-convergence gate
  with configurable minimum iterations and circulation, wake-residual, and
  integrated-load tolerances, plus non-finite warm-state cold fallback and
  profiling counters. A validated 10-degree alpha/beta proximity guard starts
  large flow-direction transitions cold to avoid wake path dependence within a
  finite iteration cap.
- Defined compatibility conservatively: Mach and every control-state index must
  match, alpha and beta may each move by at most 10 degrees, and P/Q/R may vary
  because physical local velocities are refreshed. Every process/range/resume
  boundary starts cold because continuation cache state is intentionally not
  serialized.
- Added configurable continuation defaults of four minimum wake iterations,
  `0.005` relative circulation change, `0.2` maximum wake residual, and
  `0.0005` maximum absolute integrated CF/CM change. `WakeIters` remains the
  maximum, and final velocities/forces are recalculated before an early exit.
- Added continuation settings to the State Sweep configuration hash and
  manifest, plus profile counters for attempts, accepted warm starts, cold
  starts, fallbacks, and total wake iterations.
- Validated continuation with forward/reverse traversal, repeated execution,
  process batching/resume, ranged workers, forced interruption, difficult
  thin/thick states, incompatible-state handling, and optional wing/hinge load
  columns. The 16-state acceptance case reduced wake iterations from 192 to 70
  and ran about 2.4x faster on the test machine.

## 2026-08-26 — Clemens Schmid

- Added opt-in `-state-profile` aggregated native phase timing for State Sweep.
  The JSON report separates solver setup, wake iterations, force work, and
  streamed-output costs without changing case execution or numerical results.
- Corrected State Sweep total body-axis `CFy` and `CFz` output to use the
  wake-induced force components (`CFiwy`, `CFiwz`), matching the official
  normal sweep. The previous implementation used surface-inviscid components
  and produced a visible `CFz` discrepancy for thick/panel geometry.
- Expanded official-build parity to cover State Sweep in thin and thick modes
  and added mass-property parity. Separately added an optional historical
  stable-main State Sweep regression for operating axes, physical/reduced
  rates, controls, batching/resume, and ranged execution.

## 2026-08-25 — Clemens Schmid

- Added isolated `-state-range <start> <count>` execution for parallel State
  Sweep workers. Ranged workers retain global case IDs, use independent output
  directories/checkpoints, and record both their range hash and the compatible
  unranged configuration hash. Existing sequential sweeps and checkpoints are
  unchanged.

## 2026-08-24 — Clemens Schmid

- Added an isolated native VSPAERO `-state-sweep` mode in
  `src/vsp_aero/Solver/vspaero.C`. It lazily evaluates the Cartesian product of
  the existing Mach/Reynolds/alpha/beta axes with physical or reduced P/Q/R
  axes and control-group deflections. Integrated results stream to bounded CSV
  chunks with a manifest and resumable 64-bit checkpoint; the mode does not
  retain the expanded grid in memory or emit per-case ADB solution records.
  Existing steady and `-stab` paths are unchanged. See `STATE_SWEEP.md`.
- Added repeatable `-state-design <name> <value>` metadata to State Sweep. The
  values are included in its configuration hash, manifest, and CSV rows so
  externally regenerated OpenVSP design states remain self-describing.
- Added `-state-process-cases <count>` to stop a State Sweep cleanly after a
  bounded number of aerodynamic solves. The checkpoint remains resumable and
  the execution-only batch size does not alter the aerodynamic configuration
  hash, allowing automation to relaunch VSPAERO periodically and release all
  process-owned solver memory.
- Made Windows checkpoint publication use an atomic replace with retries, so a
  transient indexer or antivirus file lock does not terminate a long sweep.
- Added optional per-physical-wing pressure/viscous `CFxyz` and `CMxyz` output
  about caller-supplied OpenVSP rotation centers, plus pressure hinge-moment
  coefficients for every physical control surface. Symmetry copies use their
  own surface loops and hinge definitions and are never inferred by mirroring
  another copy's loads.
- Extended the black-box parity suite with cross-mode State Sweep checks:
  zero-rate output is compared with the official steady sweep, and positive
  P/Q/R and control states with official `-stab` perturbation cases.
- Changed native `vspaero -stab` output generation in
  `src/vsp_aero/Solver/vspaero.C`, inside `CalculateStabilityDerivatives()`.
  Replaced the legacy forward-only derivative matrix and vertical explicit
  derivative list with three aligned, complete matrices for forward, backward,
  and central finite differences. Each matrix repeats the unperturbed total
  coefficient so it can be read independently.

## 2026-08-23 — Clemens Schmid

- Made the bundled CMinpack configuration work with multi-configuration CMake
  generators by defaulting its otherwise-empty `CMAKE_BUILD_TYPE` to `Release`.
- Replaced Code-Eli's locale-sensitive Windows date parsing during its dependency
  patch step with CMake's portable timestamp function.
- Escaped libxml's native Windows configuration path in its generated CMake
  script, preserving the backslashes required by its legacy batch installer.
- Pointed OpenABF at Eigen's installed CMake package directory.
- Generated OpenVSP's build date with CMake instead of parsing localized shell
  output, preventing malformed version headers on non-English Windows systems.
- Propagated the active configuration to the superproject's install and package
  steps so Visual Studio Release builds do not fall back to Debug.
- Forwarded an explicitly selected SWIG executable from the superproject to the
  OpenVSP build so API wrappers are not silently skipped.
- Ignored the local `build-msvc` and `build-msvc-full` output directories.
- Added the unmodified official OpenVSP 3.51.2 Windows/Python 3.13 distribution
  under `reference_builds` as a behavioral parity baseline.
- Added `build_openvsp.py` and its batch launcher for a reproducible full
  Visual Studio 2022 x64 build, including the GUI, VSPAERO, tools, docs, and
  Python API wrapper. Limited the default parallel build to four jobs to reduce
  peak RAM use; `--jobs` remains available for explicit tuning.
- Added black-box parity tests comparing official and local VSPAERO thin/thick
  base and stability results with configurable floating-point tolerances.
- Extended `vspaero -stab` with symmetric positive/negative perturbations and
  forward, backward, and central derivative output. Added `-stab-select` for
  choosing any combination of alpha, beta, Mach, P, Q, R, and all control
  groups, with symmetric nonnegative Mach-step handling. Reynolds derivatives
  remain intentionally unsupported. Added configurable alpha, beta, Mach,
  control, physical-rate, and reduced-rate perturbation steps. The `.stab`
  output records the resolved operating point, references, and physical and
  reduced rate steps. See `STABILITY_DERIVATIVES.md`.
