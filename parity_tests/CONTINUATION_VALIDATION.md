# State Sweep continuation validation

This document is the acceptance specification for experimental State Sweep
warm starts and early wake convergence. The independent controls select:

1. initialize circulation from a nearby converged state;
2. initialize the relaxed wake from that state;
3. separately stop wake relaxation after convergence, subject to minimum and maximum
   iteration limits.

The feature must remain opt-in until every mandatory test below passes. A
checkpoint stores completed aerodynamic results, not continuation cache state.
The first solve after process start or resume must therefore be a valid cold
start.

## Implemented command-line contract

The solver accepts these options:

```text
-state-warm-start
-state-early-convergence
-state-continuation  (legacy alias: enables both)
-state-continuation-min-wake-iters <count>
-state-continuation-circulation-tol <value>
-state-continuation-wake-tol <value>
-state-continuation-load-tol <value>
```

`WakeIters` remains the maximum. The implementation must publish continuation
counters in `profile.json`: attempts, accepted warm starts, cold starts,
fallbacks, and total wake iterations.

Either independent option may be enabled alone; new invocations default both
off. Tolerances and minimum iterations affect early convergence only. Warm
starts alone retain the ordinary native residual stopping rule. Manifests
record warm starts in `continuation.enabled` and the independent
`early_wake_convergence` boolean. The both-off and legacy combined hashes
are preserved; warm-only and early-only modes have distinct checkpoint hashes.
Changing modes on resume is rejected, and inactive early-convergence tolerance
edits do not change warm-only checkpoint identity.

Run `run_split_state_controls.py --solver <candidate> --output <fresh-directory>`
for thin/thick checks of all four modes, legacy equivalence, early-only stopping,
inactive tolerances and incompatible resumes. Optional `--baseline <old-solver>`
also verifies unchanged cold/combined coefficients and combined hashes against
the prior installed binary. This historical custom comparison supplements the
fixed official gate; it cannot replace that gate or its tolerances.

The experimental defaults are 4 minimum iterations, `0.005` relative
circulation change, `0.2` maximum wake residual, and `0.0005` absolute integrated
load change. These values are acceptance-tested defaults, not universal
physical constants; difficult geometries may require tighter settings.
Continuation automatically starts cold after an alpha or beta jump greater
than 10 degrees; the difficult-state cases exercise this path-dependence guard.

## Mandatory comparisons

`run_state_continuation_regression.py` generates deterministic thin and thick
wing cases and compares results by physical state rather than `case_id`. These
are candidate cold-versus-continuation correctness comparisons, not parity.
Current parity uses the pinned official OpenVSP 3.52.2 reference distribution.

- **Candidate cold control:** fixed maximum wake iterations, no continuation.
- **Forward continuation:** normal P/Q/R/control traversal.
- **Reverse traversal:** reversed rate/control values; catches path dependence.
- **Repeated execution:** identical continuation run repeated; characterizes
  OpenMP nondeterminism.
- **Batch/resume:** frequent clean process boundaries; every new process starts
  cold and must reproduce the continuous result.
- **Ranged workers:** disjoint global ranges merged by physical state.
- **Difficult states:** larger alpha, beta, combined rates, and control
  deflections in thin and thick modes.
- **Interrupted process:** terminate after a published checkpoint, resume, and
  verify complete, unique rows and cold-start recovery.
- **Fallback:** a deliberately incompatible predecessor must be rejected or
  fall back to a cold solve, with the event recorded in profiling.
- **Optional loads:** when wing and hinge columns are requested, compare every
  physical-side column as well as integrated vehicle coefficients.

## Acceptance gates

- Official OpenVSP 3.52.2 reference-build parity: zero failures.
- No missing or duplicate physical states; all values finite.
- Integrated and optional-load values satisfy
  `abs(candidate-reference) <= 5e-4 + 1e-4*abs(reference)`.
- Forward/reverse, repeat, resume, and range differences do not exceed the same
  bound or the measured repeated-run noise, whichever is larger.
- Every rejected warm start completes through a recorded cold fallback.
- Minimum and maximum wake-iteration limits are honored.
- Representative real-geometry throughput improves by at least 15 percent
  beyond fast ordering without continuation.

The detailed report is `state_continuation_regression_report.json`. Generated
inputs, logs, CSV parts, and reports are reproducible ignored artifacts and are
not committed.

Use `--plan-only` to emit the machine-readable test matrix before execution.
Use `--require-feature` in mandatory gates so a missing
or renamed feature fails rather than silently skipping tests.

## Historical 2026-08-27 acceptance result

All mandatory continuation scenarios and official OpenVSP 3.51.2 parity
passed. The optional historical stable-main regression also passed but was not
used as parity. On the deterministic 16-state acceptance case, continuation
reduced wake iterations from 192 to 70. Process time changed
from 4.56 s to 1.93 s for the thin model and from 15.23 s to 6.26 s for the
thick model (about 2.4x faster on this machine). The difficult-state maximum
absolute coefficient differences were `3.76e-4` thin and `4.97e-4` thick,
within the documented mixed tolerance.
