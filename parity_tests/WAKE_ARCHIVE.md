# Optional final-wake recording

Status: Unreleased

`vspaero -state-sweep -state-save-wakes MODEL` records accepted final vehicle/wake
snapshots alongside State Sweep CSV chunks. The flag is off by default and is
included in checkpoint identity only when enabled. It does not enable the full
ADB stream or change solve/continuation/force calculations. Capture happens after
fallback/re-solves, after result validation, and before CSV/checkpoint publication.

`WakeArchive.H` writes little-endian `VDSWAK01` journals. A row has three uint64
fields (row ID, geometry payload bytes, wake payload bytes), the payloads and an
`ENDW` footer. Zero lengths reuse the last geometry or wake in the same journal;
the first record always carries both. Process-start row and CSV chunk identify
each journal, so resumed processes preserve previous files. Writes/flush failures
stop before advancing the CSV checkpoint. Memory use is bounded to current and
previous snapshots, not sweep size.

Geometry starts with vertex, triangle and control-polyline uint64 counts. It
contains float64 xyz vertices, uint64 zero-based triangle indices, then a uint64
count and float64 xyz points per deflected control outline. SurfaceID-zero wake
panels are excluded. Polygons are triangulated as fans. Wake payloads contain a
uint64 trailing-line count, then each line's uint64 node count and float64 xyz
points. As in native ADB output, concave trailing regions emit one point.

The parent Vehicle Design Suite archive reader owns result manifests, case/row
selection and parallel-worker preservation. Its `scripts/verify_wake_archive.py`
checks exact coefficients with recording on/off at matching batch boundaries,
resumed snapshots, vehicle counts, byte budgets and coordinates against native
ADB output. Solver reference gates remain required. These records do not contain
enough state for a solver restart.
