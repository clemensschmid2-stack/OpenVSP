# Aerodynamic lookup integrity

The Foil04 review corrections are implemented in source. No native builds ran
locally for this task. [Hosted validation](https://github.com/clemensschmid2-stack/vds/actions/runs/36193471742)
passed on Windows and Linux for native revision `1ea6fa995c349c0adeb35e661533bfe9941d5eac`:
both solver builds, three CTests per platform, 17 runner tests per platform,
checkpoint integration (two Windows tests, one Linux test), and all nine Windows
point regressions below. The official distribution manifest remained unchanged.
The initial Windows macro/header failure is corrected and covered by the
include-order regression. Full OpenVSP/optimizer/reference gates remain pending;
focused success does not certify the full physics or installed runtime.

Windows solver SHA-256: `fb87d253841a06a7152af210e72c30259a2807848d87e5c6a81f75cc05e7661f`.
Linux solver SHA-256: `24ba005bfa2e63ef7faeb6a1183b043ca1039e9e7d66fbcb6b61a74660bdc134`.
These results describe the solver jobs; the same run's separate VDS application
job found an outdated body-axis test expectation, tracked in the companion PR.

## Behavior

- VSPGEOM polygon and triangulation connectivity is checked before geometric
  normalization. Invalid indices, nonfinite coordinates, zero edges and triangle
  areas indistinguishable from zero at local floating-point scale are rejected
  with cell/node diagnostics. The solver never welds nodes or repairs the model.
  Concave polygons remain valid and are checked through their triangulations.
- Nonfinite residuals and force/moment components are rejected. A failed warm
  start restores deflected controls and closes per-attempt resources before the
  existing cold retry. Vehicle totals, optional wing/hinge loads and reduced-rate
  coordinates must be finite before any row bytes are emitted. Failed cases do
  not advance the checkpoint. Finite negative drag is retained; no new residual
  tolerance, convergence gate or wake-iteration requirement is introduced.
- Wake leading/trailing-edge node and edge references use `SolveOnMGLevel()`.
  Physical-wing planform centroids still integrate grid-0 panels. This corrects
  the older grid-0 ownership rationale in the historical modification log.
- Empirical strip Reynolds is
  `ReCref * (local_speed / Vinf) * (local_chord / Cref)`.
  The geometry/local-speed derivatives include the reference-speed divisor, and
  the reference-Re derivative includes the local/reference ratio and the existing
  `max(2, Re)` clamp. The optional XFOIL profile-drag formula is unchanged.
- Fast-order traversal and continuation remain available, but spatial wake
  interaction lists and preconditioners are rebuilt rather than reused merely
  because Mach/control indices match. Position-dependent rotational freestream
  values are refreshed after wake initialization, before solve iterations, and
  after wake movement before force evaluation. Fixed iteration budgets can still
  expose wake-history dependence; convergence is not asserted by these checks.
- Physical wing names and generated aggregate names must be unambiguous.
  Only a terminal `_copy_<digits>` is treated as a copy suffix; internal label
  text is preserved. Repeated hinge labels receive unique column suffixes.
- State Sweep keeps wake-based total forces (`CFo + CFiw`) and surface-based
  total moments (`CMo + CMi`). CSV field order and checkpoint file format remain
  unchanged. A new physics hash epoch rejects old checkpoints, including when
  using native `-state-resume` outside VDS. Start a new output for corrected runs.

## Focused validation

Run Python-only runner checks from a development Python environment:

```text
python -m pytest parity_tests/test_lookup_review_harness.py
```

The portable CMake project `case_validity/` provides the `solver_case_validity`
CTest. It checks geometry degeneracy across length scales, finite-value rejection,
dimensional Reynolds invariance, and the empirical force reference-Re derivative
against central finite differences both above and below the existing clamp.

On Windows, use Python 3.13 compatible with the pinned official 3.51.2 API:

```text
python parity_tests/run_lookup_review_regression.py --solver <candidate-vspaero.exe> --official reference_builds/OpenVSP-3.51.2-win64 --output <new-empty-directory>
```

The official API creates one small rectangular wing without invoking its solver.
All solver runs use the candidate in isolated directories, one thread, individual
points or two-point batches, and at most six wake iterations. `report.json` is
PASS only when every named check passes; logs and inputs remain in the output.
The harness checks:

- Fixed reference-Re coefficient invariance at 5 and 15 m/s with a fixed wake.
- Same-order fast/ordinary two-point equivalence and zero unsafe setup reuse.
- Physical/reduced pitch equivalence at 5 m/s and -1.5 rad/s. This validates rate
  forwarding, not the numerical accuracy of the rotational wake refresh itself.
- Fresh-process beta +/-10-degree symmetry at zero rates. Forward/reverse batch
  differences are reported as diagnostics at the same wake budget; no equality
  between history-dependent orders is required.
- Rectangular-wing chord frames and trailing-edge strip coordinates.
- Invalid geometry/nonfinite result rejection without checkpoint advancement.
- Physical-name duplication and physical/aggregate-name collision rejection.

These tests do not regenerate the Foil04 lookup table or validate cavitation,
free-surface effects, stall accuracy, or all analytic optimization derivatives.
Direct numerical validation of the moved-wake rotational field remains open;
close it with a bounded field/force comparison at independently sampled wake
positions. The complete optimizer build and official-reference gate remain
required where applicable.

The Reynolds correction intentionally changes empirical viscous coefficients
relative to official 3.51.2's dimensional formula. Existing reference binaries,
comparison fields and tolerances are untouched. Any resulting strict parity
failure must remain visible and be resolved under the repository acceptance
policy; these targeted checks do not waive it.
