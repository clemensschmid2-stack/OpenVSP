# Optional final-wake recording

Status: Unreleased

MSVC Windows builds embed `longPathAware` in both solver executables. Windows
10 version 1607 or later must also have `LongPathsEnabled=1` (the **Enable Win32
long paths** policy); the solver does not change this system setting. See
[Microsoft's requirements](https://learn.microsoft.com/windows/win32/fileio/maximum-file-path-limitation).
This removes the legacy 260-character restriction for supported runtime file
operations, including deeply nested State Sweep wake files. Existing native
buffer and filesystem component limits still apply; this is not a guarantee of
arbitrary-length or Unicode-path support. Rebuild and install the executable to
activate the manifest; an existing installation does not change on source merge.
The parent VDS `scripts/verify_wake_archive.py` exercises solving, recording,
checkpoint resume and archive decoding beyond 260 characters, comparing the
coefficients exactly with the same short-path run on Windows.

`vspaero -state-sweep -state-save-wakes MODEL` records accepted final vehicle/wake
snapshots alongside State Sweep CSV chunks. The flag is off by default and is
included in checkpoint identity only when enabled. It does not enable the full
ADB stream or change solve/continuation/force calculations. Capture happens after
fallback/re-solves, after result validation, and before CSV/checkpoint publication.

`WakeArchive.H` writes little-endian `VDSWAK02` journals. A row has four uint64
fields (row ID, geometry bytes, wake bytes, pressure bytes), the payloads and an
`ENDW` footer. Zero lengths reuse the corresponding previous payload in the same
journal; the first record always carries all three. Process-start row and CSV chunk identify
each journal, so resumed processes preserve previous files. Writes/flush failures
stop before advancing the CSV checkpoint. Memory use is bounded to current and
previous snapshots, not sweep size.

Geometry starts with vertex, triangle and control-polyline uint64 counts. It
contains float64 xyz vertices, uint64 zero-based triangle indices, then a uint64
count and float64 xyz points per deflected control outline. SurfaceID-zero wake
panels are excluded. Polygons are triangulated as fans. Control outlines use
boundary edges of tagged panels, since current VSPGEOM control surfaces need not
provide polygon nodes. Wake payloads contain a
uint64 trailing-line count, then each line's uint64 node count and float64 xyz
points. As in native ADB output, concave trailing regions emit one point.

Pressure payloads start with a uint64 triangle count, then a uint64 kind array
(1 = thick-surface Cp, 2 = thin-surface ΔCp), then float64 values. Both arrays
follow the displayed triangle order. Each fan triangle copies its source loop's
`dCp()` and `SurfaceType()`. These are the final grid-0 values used by native ADB,
with native signs and reference normalization; no new smoothing or solve is
performed. Nonfinite values or unsupported surface types fail before checkpoint
publication. Pressure deduplicates independently, so identical geometry does
not imply identical loads. Added uncompressed payload is 8 + 16*N triangles,
plus 8 bytes per record header.

The parent reader supports legacy `VDSWAK01` geometry/wake archives without
pressure. Recording-enabled fingerprints use `wake-archive-v2`, rejecting mixed
v1/v2 resume; CSV-only fingerprints are unchanged. A new recorded run is required
to obtain pressure data. Merging does not install the solver.

Parent `scripts/verify_wake_pressure.py` compares thin, thick and mixed archives
to independent ADB solutions, exactly at ADB float32 precision, and checks
recording-on/off coefficient equality. The optional `--gui-smoke` exercises real
Tk pressure controls. The parent release/reference gate remains mandatory.

The parent Vehicle Design Suite archive reader owns result manifests, case/row
selection and parallel-worker preservation. Its `scripts/verify_wake_archive.py`
checks exact coefficients with recording on/off at matching batch boundaries,
resumed snapshots, vehicle counts, byte budgets and coordinates against native
ADB output. Solver reference gates remain required. These records do not contain
enough state for a solver restart.
