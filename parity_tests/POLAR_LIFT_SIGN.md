# Oriented lift query for profile drag

Status: Unreleased. Recorded: 2026-09-21.

The profile drag query now converts raw mesh-edge circulation to ordered
wake-strip circulation, consistently with mapped polar CL and the stall model:

`CL_query = sign(TE_Edge) * Gamma_edge / (0.5 * local_speed * chord)`.

Only the polar query and its clipping diagnostic change. Empirical drag,
induced-force equations, stall behavior, iteration policy, Windows path handling
and checkpoint schema are unchanged. Rebuild and validate the solver, then
regenerate affected polar-corrected sweeps and downstream packages; saved
coefficients are not repaired by installing a new executable. Do not mix old and
new solver results through resume.

## Validation

MSVC 19.44 Release x64 build succeeded. Both native CTest tests passed. The
profile test uses an asymmetric CD(CL) curve, both signed edge indices, both
physical loading directions and two control-deflection nodes. Candidate solver
launch succeeded on Windows; version mode prints 7.2.2 (its normal exit is 1).
No application-control block occurred for this candidate or these checks.

Existing `verify_profile_drag.py` passed against the official thin-wing fixture:
default coefficient parity, unchanged inviscid terms, zero/constant CD force
integration, Reynolds interpolation and clipping diagnostics. Report:
`build/polar-sign-only-force-check/report.json` in the parent workspace.

An additional native asymmetric-polar check used the same 10-strip fixture
(five positive and five negative TE indices) at alpha -4 and +4 degrees. The
unchanged installed solver was given a polar whose CL axis was reversed only
for negative TE indices, independently converting the physical table to its old
raw-edge convention. The candidate received the original ordered-strip table.
All history rows matched across profile forces/moments, CD and inviscid
coefficients to output precision (maximum difference 0, tolerance 1e-10).
Running the old solver with the unconverted table differed in CD by
0.003828555856 and 0.002754843101 respectively, demonstrating test sensitivity.
This is implementation parity, not experimental physical validation.

Evidence: parent `build/check_polar_sign_asymmetric.py`,
`build/polar-sign-asymmetric-check/report.json` and per-case logs. TE signs came
from the previously reviewed diagnostic entry point `review_sign.exe`, linked
to the unchanged baseline solver library; its only diagnostic addition prints
sheet, strip and signed TE index during template export.

Candidate: parent `build/polar-sign-only-build/solver/Release/vspaero.exe`.
SHA256: `df61f4d74dee23ae94801266f506bea799a160009b3c97c01b5a443f408a0473`.
Build log: parent `build/polar-sign-only-build.log`.
No installation, publication or merge occurred. The adjoint target and alternate
compilers were not tested; arbitrary geometries and actual flapped-geometry
force parity remain outside this bounded check (control interpolation is unit
covered). Existing separated-flow/model limitations remain unchanged.
