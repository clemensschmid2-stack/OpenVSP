# Polar lookup overhead

Recorded: 2026-09-19. Base source: `d365cb5`.

The forward/adjoint matrix products and stall derivative expressions reuse a
local result instead of calling the identical signed limit interpolation twice.
This is expression-local reuse, not a cache across changing flow states. Drag
clipping prints its first strip/Re/Cl example and explicitly suppresses further
warnings for the process, using an atomic guard like the existing stall warning.
Limits, interpolation order, derivatives, force equations and tolerances do not
change. The log is no longer a list of every clipped strip or occurrence.

`Polar solver checks` now builds the C++17 solver and runs both profile-drag and
stall interpolation tests for affected pull requests. The existing full build
workflow only triggers on the `build` branch; it provided no PR gate. This focused
gate supplements, rather than replaces, the local official-reference parity run.

Built the Solver CMake subdirectory as Release x64 with MSVC 19.44, OpenMP and
C++17, with `VSP_NO_VSPAERO_OPT=ON`, in an isolated directory. A first scratch
wrapper used C++11 and failed on existing filesystem code; correcting it to the
documented C++17 requirement produced a successful build. Existing Xmax compiler
warning remains unrelated to this change.

Validation:

- `run_parity_tests.py --custom <canonical install> --custom-vspaero <candidate>
  --work-dir <isolated directory> --report <report> --keep-work`: official OpenVSP
  3.51.2 geometry, thin/thick base/stability, optimized, selective control and
  State Sweep checks passed with zero failures and unchanged tolerances.
- `verify_stall_polars.py`: four signed/Re/flap endpoint comparisons (300 values
  each), multi-Re circulation, Reynolds derivatives and input rejection passed.
- Four-angle polar stall/drag regression against installed `d365cb5`: every
  non-time history field was exactly equal. Clipping messages decreased 200 to 1.
  Three alternating timing samples gave median 0.3671 s baseline and 0.3746 s
  candidate: no measurable solver speedup on this small fixture. Logging volume
  and duplicate lookup calls are reduced; do not infer whole-sweep speedup.

Workspace evidence is retained in ignored `build/polar-overhead-official-parity.json`,
`build/polar-overhead-stall-validation/report.json` and
`build/polar-overhead-benchmark/report.json`. No active solver was replaced during
validation. Installation is done only after checking that simulations are idle.
