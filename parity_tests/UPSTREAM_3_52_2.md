# OpenVSP 3.52.2 integration

Status: Unreleased; validation in progress, not installed.
Recorded: 2026-09-28.

Current decision: the user authorized [removing the three rotational refresh
additions](ROTATIONAL_REFRESH_REMOVAL.md) after the independent wing benchmark
was inconclusive. The blocked validation below describes the pre-removal build;
fresh integration validation is recorded in the parent repository.

The user authorized integrating upstream `OpenVSP_3.52.2` and migrating the
official reference together. This continues `fix/foil04-lookup-integrity` from
`f8962ef`; upstream is merged with its actual common ancestor, preserving fork
history. OpenVSP 3.53.0 skinning changes are outside this update.

## Compatibility and conflict resolution

Upstream includes Reynolds scaling, solid/shell inertia, lower-wing tessellation,
CompGeom scaling, geometry identity and surface-key fixes. The fork retains
State Sweep/Stability Map extensions, XFOIL profile/stall tables, checkpoint
sharing and result validity checks. Old physics checkpoints remain incompatible.

The only textual conflict was `src/vsp_aero/Solver/VSP_Solver.C`: four overlapping
Reynolds/derivative blocks. The fork's helper computes the same
`ReCref * (Velocity/Vinf) * (Chord/Cref)` as upstream. Resolution retains that
helper, positive-input guards and reference-Re chain rule; no double scaling
or tolerance change is introduced. Other upstream geometry changes merge cleanly.
The updated Code-Eli archive still needs the fork's portable Windows timestamp
patch and explicit Eigen dependency path; both are retained.

## Official reference provenance

Source: <https://openvsp.org/zips/old/windows/OpenVSP-3.52.2-win64-Python3.13.zip>

Archive SHA-256:
`da47e542d5406a65194f72383a7ab128007af1e85d861ea648a147dfe404bd8e`.

The unmodified distribution is stored at
`reference_builds/OpenVSP-3.52.2-win64`; its full file manifest and upstream
commit are recorded in the parent VDS repository. The 3.51.2 distribution and
old reports remain historical evidence. References are never rebuilt or
downloaded by a test, and active comparison tolerances remain unchanged.

The old shell-inertia exception is inactive against corrected upstream 3.52.2;
strict geometry comparison and the analytical shell check remain required.
The harness now supplies support Python packages from the selected distribution
and rejects OpenVSP silently falling back to a different solver directory.

## Build and validation

Use a short isolated Windows build path such as `C:/repos/vds/build/v3522`:

```powershell
python build_openvsp.py --build-dir C:/repos/vds/build/v3522 --jobs 4 --python <venv/Scripts/python.exe>
python parity_tests/run_parity_tests.py --custom C:/repos/vds/build/v3522/install --keep-work
```

Use CMake 3.31.x (validated with 3.31.10), SWIG 4.3.1 and Python 3.13 development
files. Put these tools first on PATH; CMake 4 drops policy support still needed
by the 3.52.2 dependency archives. The CMake 4 migration belongs to upstream
3.53.0 and is intentionally excluded here. A deeply nested worktree
build exceeded MSBuild file-tracker path limits; the short path avoids that
environment failure without changing application-control policy.

The selected Python environment must contain NumPy. The launcher resolves the
base installation's development files for virtual environments, checks NumPy
before configuring, and requires both Python extension outputs. Otherwise CMake
can silently omit the API while successfully building the executables.

The full GUI/API/optimizer build and ZIP packaging pass. Strict geometry parity
passes all nine cases without an exception; both base-flow cases pass all 1,991
values each. Stability parity fails 105 thin and 103 thick comparisons. A separate
diagnostic source copy disabling only the three rotational-flow refresh additions
matches all 2,550 stability values in each fixture. This isolates the existing
fork difference but does not prove either rotational solution physically correct.
The diagnostic is not the integrated candidate; no numerical rule is weakened.

Parent release Python/native suites and GUI smoke pass. The full release gate
stops at the failed stability comparison; current hosted checks and merging
remain blocked. Parent `docs/openvsp-3.52.2-integration.md` records revisions,
artifact hashes, counts and completion conditions. This is local WIP, unpublished,
unmerged and not installed.
