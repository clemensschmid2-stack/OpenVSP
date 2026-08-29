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
the manifest and every CSV row, using `name` directly as its CSV column. The
automation supplies the OpenVSP parameter name or configured alias plus its
unit suffix (for example, `Y_Rel_Rotation_deg`). It is metadata: VSPAERO does not regenerate
OpenVSP geometry. The repository automation performs that regeneration and
launches one native State Sweep per design-variable combination.

Only one physical/reduced form may be supplied for each axis. An omitted rate
axis contains zero. An omitted control axis contains the control group's case
file deflection. `-state-control` uses the one-based control-group index from
the `.vspaero` case file and takes deflections in degrees. Its CSV column uses
the sanitized control-group name followed by `_deflection_deg`.

## Output and memory behavior

Results are streamed to `<model>.state_sweep/`:

- `manifest.json` records the format, case counts, rate conventions, control
  columns, chunk size, and configuration hash. With component loads enabled it
  also records each physical wing's center and representative chord/span/normal
  frame, and each physical hinge's owning wing, origin, and direction.
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

`-state-profile` writes an aggregated `profile.json` beside the streamed CSV
parts. It records process/solver time plus wake initialization, interaction-list
construction, preconditioner construction, wake iterations, linear solves,
force integration, additional Reynolds force recalculation, and CSV/checkpoint
output. Profiling is opt-in and is excluded from the aerodynamic configuration
hash, so it can be enabled for a resumed run without invalidating results.

`-state-fast-order` enables a performance-oriented case mapping. P/Q/R and
incidence states vary inside each contiguous Mach/control block. Within that
block, VSPAERO reuses the initial surface interaction list and matrix
preconditioner because geometry, control deflection, and Mach are unchanged.
Every case still performs its own free-stream/wake initialization, wake
iterations, linear solution, and force integration; this is not a warm start.
During each steady solve, the fixed-surface interaction list is also retained
across wake iterations. Relaxed wake locations do not participate in building
that list; wake geometry and the aerodynamic solution continue to update every
iteration.
The option is included in the configuration hash because it changes the mapping
between `case_id` and physical state. Therefore it may not be enabled or
disabled while resuming an existing sweep. Older checkpoints remain compatible
when the option is omitted.

`-state-continuation` additionally preserves converged circulation and relaxed
wake geometry between adjacent cases whose Mach and control state are
unchanged. Alpha, beta, and physical/reduced rates may change; the free stream
and local rotational velocities are reinitialized for every case. The first
case of each process, every changed Mach/control block, every alpha or beta
jump greater than 10 degrees, and every resumed process starts cold. The
flow-direction guard prevents a relaxed wake from crossing a large incidence
change where limited wake iterations can otherwise produce path dependence.

The exact warm-start decision is made independently inside each process:

- continuation must be enabled;
- a previous case must exist in that process;
- the Mach index and every control-state index must match the previous case;
- both `abs(alpha - previous_alpha)` and `abs(beta - previous_beta)` must be at
  most 10 degrees.

P/Q/R differences do not reject a warm start because the new physical rates
are applied when local velocities are refreshed. Reynolds values do not select
separate aerodynamic solves: as in the regular sweep, additional Reynolds rows
reuse the solved state and recalculate viscous forces. Independent range
workers cannot share continuation state. Likewise, automation-level Vinf and
design-variable cases launch separate native processes and therefore start
cold.

Continuation also enables convergence-based wake termination. `WakeIters` is
the hard maximum and the following options control the early-exit gate:

```text
-state-continuation-min-wake-iters <count>
-state-continuation-circulation-tol <relative-change>
-state-continuation-wake-tol <wake-residual>
-state-continuation-load-tol <absolute-CF/CM-change>
```

All three changes must satisfy their tolerances after the minimum number of
iterations. The implemented convergence quantities are:

```text
circulation_change = max_i(abs(Gamma_i[k] - Gamma_i[k-1]) / max(1, abs(Gamma_i[k])))
wake_residual      = abs(MaxResidual)
load_change        = max(abs(delta CFx/y/z), abs(delta CMx/y/z))
```

Defaults are 4, `0.005`, `0.2`, and `0.0005`, respectively. `WakeIters` remains
the maximum; if the minimum is greater than or equal to that maximum, early
termination provides no iteration saving. Before an early return, velocities
and forces are recalculated for the final wake/circulation state. A criterion
that has not converged simply continues to `WakeIters`. A non-finite warm
solution is discarded and that same case is retried cold.

The configuration hash includes continuation and its tolerances, so they
cannot change while resuming an existing output. Continuation cache state is
not serialized: completed CSV rows are resumable, but the first unfinished
case in every new process starts cold. `profile.json` records attempts,
accepted warm starts, cold starts, fallbacks, and total wake iterations.

For independent parallel workers, `-state-range <start> <count>` restricts a
process to a contiguous range of global aerodynamic-case IDs. Its CSV rows keep
the original global `case_id`. Ranged workers must use isolated working/output
directories; their manifests record `range_start`, `range_count`, and the
unranged `base_configuration_hash` used when merging. Omitting `-state-range`
preserves the original sequential behavior and checkpoint hash. With
`-state-fast-order`, global range IDs refer to the fast-order mapping.

## Optional physical-surface loads

`-state-wing-load <surface> <name> <x> <y> <z>` may be repeated to append a
decomposed load for every physical wing surface. The supplied point is the
common vehicle aerodynamic reference point; moments use this point and the
standard `Bref/Cref/Bref` normalization. Each wing emits `CFo*`/`CMo*`
(empirical viscous/profile), `CFi*`/`CMi*` (near-field inviscid), and `CFiw*`
(Trefftz/wake inviscid force). The total columns follow VSPAERO's vehicle
convention exactly: `CF* = CFo* + CFiw*`, while
`CM* = CMo* + CMi*` because VSPAERO has no corresponding far-field moment.
Component columns use quantity-first names such as `CFo_x_wing_ypos`,
`CFiw_z_elevator`, and `CM_y_mast`.

Each wing additionally emits `CM_x_center_*`, `CM_y_center_*`, and
`CM_z_center_*` about its geometric planform-area centroid. The centroid is the
area-weighted mean of VSPAERO strip centers, using each strip's leading/trailing
edge midpoint and planform area. Translation uses `CFo+CFi`, matching the
near-field total `CMo+CMi`, and the standard `Bref/Cref/Bref` normalization.
The manifest records `planform_area` and `planform_center` for every physical
surface.

Symmetry copies are passed as separate surfaces and accumulated from their own
solved loops; loads are never mirrored from another copy. When two or more
physical names share a compact side suffix (`ypos`, `yneg`, `xpos`, `xneg`,
`zpos`, or `zneg`), an additional parent-wing set of columns is emitted as the
exact sum of those physical instances. Because every moment has the same
reference point, parent force and moment coefficients are directly additive.
For an all-lifting-surface model, summing all parent-wing totals reproduces the
vehicle `CFx/y/z` and `CMx/y/z` columns. Non-lifting components remain outside
this optional wing-only partition.
Physical symmetry sides each retain their own center-moment columns. The
parent center moment is evaluated about the area-weighted center of all sides;
unlike moments about the shared vehicle reference point, it is not the direct
sum of moments taken about the separate side centers.

`-state-hinge-loads` appends one pressure hinge-moment coefficient per physical
control surface. Every surface uses its own loop list, hinge origin, and hinge
direction, keeping symmetric controls separate. `Cm_hinge` is normalized by
`q*Sref*Cref`. Columns use the control-surface name and append the compact side
token `ypos`, `yneg`, `xpos`, `xneg`, `zpos`, or `zneg` for
symmetric copies. The manifest records wing centers and
hinge-column names. Hinge columns are also quantity-first, for example
`Cm_hinge_aileron_ypos`.

ADB state storage, unsteady analysis, trim, adjoint analysis, stability
derivatives, explicit coupled-state lists, and distributed sharding are not
part of this mode.

The continuation correctness tolerances, mandatory test matrix, and merge
gates are documented in
[`parity_tests/CONTINUATION_VALIDATION.md`](parity_tests/CONTINUATION_VALIDATION.md).

## Optional optimization of existing analysis modes

The same convergence measurements can be enabled for the existing steady and
stability modes without selecting State Sweep:

```text
vspaero -steady-optimize [convergence options] model
vspaero -stab -stab-optimize [convergence options] model
```

`-steady-optimize` keeps every operating point cold-started and enables the
three-part early-convergence gate. Tested wake continuation and cross-case
interaction-list/preconditioner caches were deliberately rejected: at strict
official-reference tolerances they introduced measurable coefficient changes,
especially with small `WakeIters`.

`-stab-optimize` enables only the early-convergence gate. Positive, negative,
Mach, rate, and control perturbations remain independent cold solves and do
not share interaction lists or preconditioners. Reuse across perturbations was
tested and rejected because small coefficient changes were amplified by the
finite-difference division. This preserves forward/backward/central derivative
parity when early termination does not trigger.

Both modes accept the four `-state-continuation-*-tol`/minimum-iteration options
listed above. `-solver-opt-profile` prints a `VSPAERO_OPT_PROFILE` timing line;
it does not change the solution. When early termination triggers, the result is
an explicitly tolerance-controlled approximation to running every configured
wake iteration; strict official-reference parity is expected only when the
gate does not terminate early. All new behavior is opt-in.

### Selecting stability control groups

The modified stability mode can restrict control perturbations to explicit
one-based group indices:

```text
vspaero -stab -stab-select p,q,r,controls -stab-control-select 1,3 model
```

The base case and selected non-control derivatives are unchanged. Only groups
1 and 3 receive positive and negative control-deflection solves. The explicit
Forward, Backward, and Central tables contain only `ConGrp_1` and `ConGrp_3`;
the metadata still lists every model group and marks whether it was selected.
An unavailable or non-positive index is rejected. Omitting
`-stab-control-select` preserves the existing all-control-groups behavior.
