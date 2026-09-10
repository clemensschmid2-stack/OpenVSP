# Approved shell-inertia compatibility exception

On 2026-09-10 the user approved retaining the custom build's correct triangle
integration while accepting the 30 documented differences from official 3.51.2.
The baseline lists 14 MassProp and 16 DegenGeom fields. Both official and custom
values must match the reviewed fixture results within 1e-9 relative / 1e-10
absolute tolerance. No additional fields, missing values, nonfinite values, or
changed baselines are accepted. The independent exact tetrahedral-shell test
must still pass for the custom build. Strict parity failures remain in the
report alongside the explicit accepted-difference count and policy hash.

TODO: Track the upstream triangle integration fix, independently validate more
shell geometries and mesh refinements, and retire this exception when the
official reference is corrected. Do not regenerate the baseline automatically.
