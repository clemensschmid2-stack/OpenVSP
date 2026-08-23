# Selectable finite-difference stability derivatives

The standard `vspaero -stab` calculation supports symmetric perturbations and
reports forward, backward, and central finite differences. A base case is
always calculated.

## Selecting derivatives

Without a selector, `-stab` retains the legacy full selection:

```text
vspaero -stab model
```

Use `-stab-select` with one comma-separated argument to avoid calculations that
are not needed:

```text
vspaero -stab -stab-select p,q,r,controls model
```

Recognized names are `alpha`, `beta`, `mach`, `p`, `q`, `r`, `controls`, and
`all`. `controls` selects every configured control-surface group. Reynolds
number derivatives are intentionally not implemented.

## Difference methods

For a coefficient `C`, base value `C0`, and equal positive/negative step `h`:

```text
forward = (C(+h) - C0) / h
backward = (C0 - C(-h)) / h
central = (C(+h) - C(-h)) / (2 h)
```

The original VSPAERO derivative table remains the forward result for backward
compatibility. Explicit fields such as `CMm_q_Forward`, `CMm_q_Backward`, and
`CMm_q_Central` follow it. Unselected columns in the legacy fixed-width table
are written as `nan`; no zero derivative is implied.

Alpha, beta, and control derivatives are per radian. P, Q, and R derivatives
are with respect to the conventional reduced rates:

```text
p_hat = p * Bref / (2 * Vinf)
q_hat = q * Cref / (2 * Vinf)
r_hat = r * Bref / (2 * Vinf)
```

By default, the physical perturbations applied to the solver remain the legacy
`0.01 rad/Tunit`. For comparable derivative steps across different speeds and
vehicles, set reduced-rate steps explicitly:

```text
vspaero -stab -stab-select p,q,r \
  -stab-step-phat 0.005 -stab-step-qhat 0.005 -stab-step-rhat 0.005 model
```

VSPAERO converts these to physical solver rates at every operating point:

```text
p = 2 * Vinf * p_hat / Bref
q = 2 * Vinf * q_hat / Cref
r = 2 * Vinf * r_hat / Bref
```

Physical steps remain available for special studies through `-stab-step-p`,
`-stab-step-q`, and `-stab-step-r`, in `rad/Tunit`. A physical and reduced
option for the same axis cannot be combined.

All finite-difference steps can be configured:

```text
-stab-step-alpha <deg>
-stab-step-beta <deg>
-stab-step-mach <value>
-stab-step-phat <value> | -stab-step-p <rad/Tunit>
-stab-step-qhat <value> | -stab-step-q <rad/Tunit>
-stab-step-rhat <value> | -stab-step-r <rad/Tunit>
-stab-step-control <deg>
```

Every value must be positive. The `.stab` header records the operating point,
reference quantities, selected derivatives, requested step source, and both
the physical and reduced P/Q/R steps. `Vinf` continues to come from the
`.vspaero` case file; no duplicate CLI override is introduced.

`Tunit` follows the consistent unit system of the input. For example, geometry
in metres and `Vinf` in metres per second makes `Tunit` seconds.

## Mach safety

Mach uses one common positive/negative step so the central formula remains
symmetric. The requested step is reduced only when necessary to keep `Mach - h`
nonnegative and to avoid placing a perturbation too close to Mach 1. A
symmetric Mach derivative at a nonpositive base Mach is rejected with an
error instead of running an invalid negative-Mach case.
