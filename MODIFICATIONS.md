# Modifications

This fork is derived from NASA's OpenVSP project.

## 2026-08-24 — Clemens Schmid

- Added an isolated native VSPAERO `-state-sweep` mode in
  `src/vsp_aero/Solver/vspaero.C`. It lazily evaluates the Cartesian product of
  the existing Mach/Reynolds/alpha/beta axes with physical or reduced P/Q/R
  axes and control-group deflections. Integrated results stream to bounded CSV
  chunks with a manifest and resumable 64-bit checkpoint; the mode does not
  retain the expanded grid in memory or emit per-case ADB solution records.
  Existing steady and `-stab` paths are unchanged. See `STATE_SWEEP.md`.
- Added repeatable `-state-design <name> <value>` metadata to State Sweep. The
  values are included in its configuration hash, manifest, and CSV rows so
  externally regenerated OpenVSP design states remain self-describing.
- Extended the black-box parity suite with cross-mode State Sweep checks:
  zero-rate output is compared with the official steady sweep, and positive
  P/Q/R and control states with official `-stab` perturbation cases.
- Changed native `vspaero -stab` output generation in
  `src/vsp_aero/Solver/vspaero.C`, inside `CalculateStabilityDerivatives()`.
  Replaced the legacy forward-only derivative matrix and vertical explicit
  derivative list with three aligned, complete matrices for forward, backward,
  and central finite differences. Each matrix repeats the unperturbed total
  coefficient so it can be read independently.

## 2026-08-23 — Clemens Schmid

- Made the bundled CMinpack configuration work with multi-configuration CMake
  generators by defaulting its otherwise-empty `CMAKE_BUILD_TYPE` to `Release`.
- Replaced Code-Eli's locale-sensitive Windows date parsing during its dependency
  patch step with CMake's portable timestamp function.
- Escaped libxml's native Windows configuration path in its generated CMake
  script, preserving the backslashes required by its legacy batch installer.
- Pointed OpenABF at Eigen's installed CMake package directory.
- Generated OpenVSP's build date with CMake instead of parsing localized shell
  output, preventing malformed version headers on non-English Windows systems.
- Propagated the active configuration to the superproject's install and package
  steps so Visual Studio Release builds do not fall back to Debug.
- Forwarded an explicitly selected SWIG executable from the superproject to the
  OpenVSP build so API wrappers are not silently skipped.
- Ignored the local `build-msvc` and `build-msvc-full` output directories.
- Added the unmodified official OpenVSP 3.51.2 Windows/Python 3.13 distribution
  under `reference_builds` as a behavioral parity baseline.
- Added `build_openvsp.py` and its batch launcher for a reproducible full
  Visual Studio 2022 x64 build, including the GUI, VSPAERO, tools, docs, and
  Python API wrapper. Limited the default parallel build to four jobs to reduce
  peak RAM use; `--jobs` remains available for explicit tuning.
- Added black-box parity tests comparing official and local VSPAERO thin/thick
  base and stability results with configurable floating-point tolerances.
- Extended `vspaero -stab` with symmetric positive/negative perturbations and
  forward, backward, and central derivative output. Added `-stab-select` for
  choosing any combination of alpha, beta, Mach, P, Q, R, and all control
  groups, with symmetric nonnegative Mach-step handling. Reynolds derivatives
  remain intentionally unsupported. Added configurable alpha, beta, Mach,
  control, physical-rate, and reduced-rate perturbation steps. The `.stab`
  output records the resolved operating point, references, and physical and
  reduced rate steps. See `STABILITY_DERIVATIVES.md`.
