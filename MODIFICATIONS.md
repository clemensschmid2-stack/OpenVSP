# Modifications

This fork is derived from NASA's OpenVSP project.

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
- Ignored the local `build-msvc` output directory.
