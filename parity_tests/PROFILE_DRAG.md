# Optional XFOIL section profile drag

`-profile-drag-table <csv>` replaces the lifting-strip empirical viscous term
with tabulated CD. With the option absent, the existing model and its stall
multiplier are unchanged. Non-lifting-body drag and induced forces are retained.
The polar path does not add the empirical wing term or its stall multiplier.

Rows are `vortex_sheet,strip,section,weight,control_group,gain,deflection,reynolds,cl,cd`.
Each strip must be covered; section weights sum to one. Control group zero means
an unflapped section. Other groups use their current deflection times gain, so
finite-difference stability and native State Sweep control changes query the
matching polar data. Empty polars use a reserved CD=-1 marker, which is never
returned as a coefficient: a lookup requiring that polar fails explicitly.

Interpolation is linear in signed section CL, Reynolds, deflection, and section
weight. Requests beyond valid endpoints clip, with strip/Re/CL diagnostics in
the solver log. A one-point polar is a constant with clipping outside that point.
Local Reynolds is ReCref*(local speed/freestream speed)*(local chord/Cref).
Profile force uses local dynamic pressure and strip area, acts along local flow,
and contributes moments at the existing section-force location.

The table is included in the native State Sweep checkpoint hash. Adjoint
optimization is rejected because its empirical viscous gradients have not been
replaced. This option does not replace inviscid section moments or provide a
validated 3D separated-flow, junction, cavitation, or ventilation model.

Validation commands:

```powershell
cmake -S parity_tests/profile_drag -B build-profile-tests
cmake --build build-profile-tests --config Release
ctest --test-dir build-profile-tests -C Release --output-on-failure
python parity_tests/verify_profile_drag.py --solver <candidate.exe> --fixture <thin_base/custom> --work <new-directory>
```

The fixture comes from the existing official-reference parity suite. The force
test verifies no empirical double counting with zero CD, constant-CD force
accuracy, unchanged inviscid coefficients, and clipping diagnostics.
