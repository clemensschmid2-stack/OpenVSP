# VSPAERO State Sweep

`-state-sweep` is a separate steady analysis mode for evaluating a Cartesian
grid of aerodynamic states. It does not change the existing steady sweep or
`-stab` implementations.

The Mach, Reynolds number, angle-of-attack, and sideslip axes come from the
normal `.vspaero` case file. The command line adds physical or reduced body-rate
axes and optional control-group axes:

```text
vspaero -state-sweep -state-phat "-0.05,0,0.05" -state-qhat "-0.03,0,0.03" -state-rhat "-0.05,0,0.05" -state-control 1 "-10,0,10" -state-chunk-size 25000 -state-process-cases 500 model
```

Physical rate options are `-state-p`, `-state-q`, and `-state-r`, in radians
per model time unit. Reduced alternatives are `-state-phat`, `-state-qhat`, and
`-state-rhat`, using:

```text
p_hat = p * Bref / (2 * Vinf)
q_hat = q * Cref / (2 * Vinf)
r_hat = r * Bref / (2 * Vinf)
```

`-state-design <name> <value>` records an externally applied design state in
the manifest and every CSV row. It is metadata: VSPAERO does not regenerate
OpenVSP geometry. The repository automation performs that regeneration and
launches one native State Sweep per design-variable combination.

Only one physical/reduced form may be supplied for each axis. An omitted rate
axis contains zero. An omitted control axis contains the control group's case
file deflection. `-state-control` uses the one-based control-group index from
the `.vspaero` case file and takes deflections in degrees.

## Output and memory behavior

Results are streamed to `<model>.state_sweep/`:

- `manifest.json` records the format, case counts, rate conventions, control
  columns, chunk size, and configuration hash.
- `checkpoint.txt` records the next output row and is replaced atomically.
- `part-000000.csv`, `part-000001.csv`, ... contain integrated coefficients.

The Cartesian product is decoded from a 64-bit case index as each case is
needed. VSPAERO does not allocate an expanded case grid or retain coefficient
rows in memory. Reynolds values share one aerodynamic solve and use force
recalculation, as in the existing steady sweep. The state-sweep path also
suppresses per-case ADB solution records; the chunked CSV files are its result
store.

After interruption, rerun the identical command with `-state-resume`. The
configuration hash rejects changed axes, references, counts, rate conventions,
or chunk size. Starting without `-state-resume` refuses to overwrite an
existing sweep. Keep the model and `.vspaero` input unchanged while resuming.

`-state-process-cases <count>` limits one process to that many aerodynamic
solves and then closes native output files and exits successfully. Relaunch
with `-state-resume` to continue. This execution limit is deliberately excluded
from the configuration hash, so it may be changed between launches without
invalidating the checkpoint. The repository automation defaults to 500 solves
per process and preserves each launch's standard `.history` and `.lod` files
under `native_batches/` before starting the next process.
Checkpoint publication uses a temporary file and atomic replacement. On
Windows, transient sharing violations are retried before the solver reports an
error.

For independent parallel workers, `-state-range <start> <count>` restricts a
process to a contiguous range of global aerodynamic-case IDs. Its CSV rows keep
the original global `case_id`. Ranged workers must use isolated working/output
directories; their manifests record `range_start`, `range_count`, and the
unranged `base_configuration_hash` used when merging. Omitting `-state-range`
preserves the original sequential behavior and checkpoint hash.

## Optional physical-surface loads

`-state-wing-load <surface> <name> <x> <y> <z>` may be repeated to append
`CFx/CFy/CFz` and `CMx/CMy/CMz` for individual physical wing surfaces. Moments
use the supplied OpenVSP rotation center and standard `Bref/Cref/Bref`
normalization. Pressure and VSPAERO's strip-wise viscous wing loads are
included. Symmetry copies are passed as separate surfaces and are accumulated
from their own solved loops; loads are never mirrored from another copy.

`-state-hinge-loads` appends one pressure hinge-moment coefficient per physical
control surface. Every surface uses its own loop list, hinge origin, and hinge
direction, keeping symmetric controls separate. `Ch` is normalized by
`q*Sref*Cref`. The manifest records wing centers and hinge-column names.

ADB state storage, unsteady analysis, trim, adjoint analysis, stability
derivatives, explicit coupled-state lists, and distributed sharding are not
part of this mode.
