# Restore upstream rotational-flow refresh behavior

Status: Unreleased; local validation passed. Not installed.
Recorded: 2026-09-28.

The user authorized removing the fork's three additional rotational-flow refresh
operations after the TN 1835 wing 7 experiment failed to establish a physical
benefit. These additions previously caused 105 thin-surface and 103 thick-surface
differences against the official 3.52.2 stability fixtures. Restoring upstream
behavior is an implementation decision, not proof that upstream is physically
exact or a relaxation of the acceptance rules.

The solver no longer refreshes edge freestream solely because p/q/r is nonzero
after wake initialization, during wake iterations, or after mesh movement.
The inherited refresh conditions for rotors, engines and time-accurate cases
remain. Wake-dependent interaction/preconditioner rebuilding, Reynolds fixes,
finite-result checks, force conventions and iteration budgets are unchanged.

State Sweep uses physics epoch `lookup-integrity-v2-upstream-rotation` so outputs
from the removed adaptation cannot be silently resumed. Start a new output
directory and regenerate affected tables/packages; existing output is preserved.

## Possible future feature

Position-dependent rotational-field refresh remains a research candidate, not
an enabled or supported option. Reintroduction requires independent field/force
checks, mesh/wake and finite-rate convergence, physical data with sufficient
resolution to discriminate implementations, and an explicit reviewed source and
numerical-acceptance decision. Reference mismatch alone is neither proof of a
bug nor permission to weaken tolerances.

The parent VDS repository retains the model, original three-block ablation patch,
132-solve benchmark and its limitations under `tests/benchmarks/tn1835/` and
`docs/reviews/tn1835-wing7.md`. The two variants differed by about 0.0029% in the
finest/60-iteration case, while mesh sensitivity was much larger. That historical
benchmark does not validate the full vehicle or all rotational derivatives.

## Validation

The isolated full GUI/API/optimizer build and ZIP packaging passed. The unchanged
official 3.52.2 parity gate passes all nine geometry cases, both 1,991-value
base-flow cases and both 2,550-value stability cases; zero comparison failures.
All nine bounded lookup regressions and 17 harness tests pass. A copied old-epoch
checkpoint is rejected without modification. Candidate solver SHA-256:
`73f33f043a41e3afd9dce3bc4d3d290eb8ec845d377757947b87741184561a45`.
The native merge rehearsal against `0ad85f015` is conflict-free and exactly
matches the topic source tree. No numerical acceptance rule changed.

Current integration and hosted-check evidence is recorded in the parent
`docs/openvsp-3.52.2-integration.md`; the earlier blocked results in
[UPSTREAM_3_52_2.md](UPSTREAM_3_52_2.md) remain historical evidence.
