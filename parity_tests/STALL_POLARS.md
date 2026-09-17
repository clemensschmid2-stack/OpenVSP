# Approved XFOIL stall polar tables

Status: Unreleased

`-stall-polar-table <csv>` supplies signed stall limits mapped to the exact native
strips. It uses the same section weights, physical control groups/gains and
linear Reynolds/deflection interpolation as section profile drag. It changes
only the nonlinear stall limit; select profile drag separately if desired.

Columns:

```text
vortex_sheet,strip,section,weight,control_group,gain,deflection,reynolds,lift_sign,limit_magnitude
```

Each section/Re/deflection node must have exactly two positive magnitudes,
with lift_sign -1 and +1. The application swaps signs for inverted geometry
and supplies canonical flap gains. Section weights must sum to one. Missing
strips, extra strips, invalid signs/magnitudes, simultaneous fixed strip limits
and adjoint optimization are rejected. StallModel must be enabled in the input.

Local Re = ReCref * (local speed / Vinf) * (local chord / Cref). Endpoints clip
with a log notice; no new post-stall model is inferred. Scalar and fixed strip
limits keep their existing path when the polar table is absent.

Reynolds-dependent stall limits alter circulation, so additional Reynolds cases
must solve again. This applies to steady sweeps, State Sweeps and the Reynolds
perturbations in stability maps. Multi-Reynolds polar State Sweeps cold-start
rather than continue across Reynolds. The table contents and format tag are
hashed into the State Sweep checkpoint identity.

## Isolated Windows validation

From the OpenVSP root (Visual Studio 2022 and CMake required):

```powershell
cmake -S parity_tests/stall_polars -B build-stall-validation -G "Visual Studio 17 2022" -A x64
cmake --build build-stall-validation --config Release --target vspaero -j 4
cmake -S parity_tests/profile_drag -B build-stall-interpolation
cmake --build build-stall-interpolation --config Release
ctest --test-dir build-stall-interpolation -C Release --output-on-failure
python parity_tests/run_parity_tests.py --custom <installed-distribution> --custom-vspaero build-stall-validation/solver/Release/vspaero.exe --work-dir <new-parity-directory> --report <report.json> --keep-work
python parity_tests/verify_stall_polars.py --solver build-stall-validation/solver/Release/vspaero.exe --fixture <new-parity-directory>/thin_base/custom --work <new-stall-check-directory>
```

The standalone build writes only to its build directory. It does not install a
runtime. For normal full builds use `build_openvsp.py --build-dir <isolated-dir>`;
install only after simulations finish and the parent integration is authorized.
The native regression compares signed steady limits and an eight-state
Reynolds/control sweep against equivalent fixed limits at unchanged 1e-9
coefficient tolerance. It also checks valid resume and changed-table rejection.
Unit coverage includes span/Re/control interpolation, physical gain, clipping
and invalid table rejection. Parent review evidence records actual run results.
