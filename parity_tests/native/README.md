# Standalone VSPAERO validation

This repository owns the solver CMake test entry point, native/lookup regression
runner, immutable reference manifest, and their unit tests. They do not require
the VDS superproject. The existing official distribution remains unchanged.

From the OpenVSP repository root:

```powershell
python -m pip install pytest numpy matplotlib
python parity_tests/run_native_checks.py
```

Use Python 3.13, CMake 3.24+, and a C++17/OpenMP compiler. Windows also runs the
bounded lookup-point checks using the pinned official geometry API; Linux runs
the portable native checks. `--build-dir` and `--reports` select isolated output
locations. Existing evidence is never overwritten. The report retains source
revision, dependency versions, test results and hashes of the tested/packaged
solver and checkpoint probe. Missing or failed tests remain failures.

The `native-validation.yml` workflow runs this suite for changes to solver code,
parity tests, references or its own workflow. The complete official comparison
remains `python parity_tests/run_parity_tests.py --custom <candidate-install>`.
Reference bytes and tolerances have not changed.

VDS retains tests of its checkpoint reader, wake/pressure reader, and far-field
input translation against native output. Its orchestrator invokes this owned
runner before those integration checks, only when the OpenVSP pin or an affected
VDS/native interface changes. Simulator-only changes do not select this suite.
