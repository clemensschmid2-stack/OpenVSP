# State Sweep continuation validation

This document is the acceptance specification for the experimental State
Sweep continuation mode. Continuation combines three optimizations:

1. initialize circulation from a nearby converged state;
2. initialize the relaxed wake from that state;
3. stop wake relaxation after convergence, subject to minimum and maximum
   iteration limits.

The feature must remain opt-in until every mandatory test below passes. A
checkpoint stores completed aerodynamic results, not continuation cache state.
The first solve after process start or resume must therefore be a valid cold
start.

## Proposed command-line contract

The regression runner reserves these options:

```text
-state-continuation
-state-continuation-min-wake-iters <count>
-state-continuation-circulation-tol <value>
-state-continuation-wake-tol <value>
-state-continuation-load-tol <value>
```

`WakeIters` remains the maximum. The implementation must publish continuation
counters in `profile.json`: attempts, accepted warm starts, cold starts,
fallbacks, and total wake iterations.

## Mandatory comparisons

`run_state_continuation_regression.py` generates deterministic thin and thick
wing cases and compares results by physical state rather than `case_id`.

- **Cold reference:** fixed maximum wake iterations, no continuation.
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

- Existing official parity and stable-main regression: zero failures.
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

Use `--plan-only` before the native feature exists to validate paths, emit the
machine-readable test matrix, and check that the candidate advertises the
reserved CLI contract. Use `--require-feature` in mandatory gates so a missing
or renamed feature fails rather than silently skipping tests.
