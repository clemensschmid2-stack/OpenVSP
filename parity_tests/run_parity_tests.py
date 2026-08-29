#!/usr/bin/env python3
"""Compare official and locally built OpenVSP/VSPAERO numerical results."""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DEFAULT_OFFICIAL = ROOT / "reference_builds" / "OpenVSP-3.51.2-win64"
DEFAULT_CUSTOM = ROOT / "build-msvc-full" / "install"
CASES = (("thin", "base"), ("thin", "stab"), ("thick", "base"), ("thick", "stab"))
VOLATILE_FIELDS = {"Wall_Time", "WallTime", "Analysis_Duration_Sec"}
COEFFICIENTS = ("CFx", "CFy", "CFz", "CMx", "CMy", "CMz", "CL", "CD", "CS", "CMl", "CMm", "CMn")


def python_package(distribution: Path) -> Path:
    package = distribution / "python" / "openvsp"
    if not package.is_dir():
        raise FileNotFoundError(f"OpenVSP Python package not found: {package}")
    return package


def run_case(
    distribution: Path,
    mode: str,
    analysis: str,
    output_dir: Path,
    timeout: int,
    vspaero_directory: Path | None = None,
) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    result_file = output_dir / "results.json"
    log_file = output_dir / "run.log"
    environment = os.environ.copy()
    environment["OMP_NUM_THREADS"] = "1"
    environment["PYTHONPATH"] = str(python_package(distribution))
    command = [
        sys.executable,
        str(HERE / "run_case.py"),
        "--distribution", str(distribution),
        "--mode", mode,
        "--analysis", analysis,
        "--output", str(result_file),
    ]
    if vspaero_directory is not None:
        command.extend(("--vspaero-directory", str(vspaero_directory)))
    with log_file.open("w", encoding="utf-8") as log:
        subprocess.run(
            command,
            cwd=output_dir,
            env=environment,
            stdout=log,
            stderr=subprocess.STDOUT,
            check=True,
            timeout=timeout,
        )
    return json.loads(result_file.read_text(encoding="utf-8"))


def flatten(value: object, prefix: str = "") -> dict[str, float | int]:
    flattened: dict[str, float | int] = {}
    if isinstance(value, dict):
        for key, child in value.items():
            if key in VOLATILE_FIELDS:
                continue
            flattened.update(flatten(child, f"{prefix}.{key}" if prefix else key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            flattened.update(flatten(child, f"{prefix}[{index}]"))
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        flattened[prefix] = value
    return flattened


def compare(
    official: dict[str, object],
    custom: dict[str, object],
    rtol: float,
    atol: float,
) -> tuple[list[dict[str, object]], int]:
    reference = flatten(official)
    candidate = flatten(custom)
    differences: list[dict[str, object]] = []
    failed = 0
    for key in sorted(reference.keys()):
        if key not in candidate:
            failed += 1
            differences.append({"field": key, "status": "missing"})
            continue
        expected = reference[key]
        actual = candidate[key]
        tolerance = atol + rtol * abs(float(expected))
        absolute_error = abs(float(actual) - float(expected))
        passed = math.isfinite(absolute_error) and absolute_error <= tolerance
        if not passed:
            failed += 1
        differences.append(
            {
                "field": key,
                "official": expected,
                "custom": actual,
                "absolute_error": absolute_error,
                "tolerance": tolerance,
                "status": "pass" if passed else "fail",
            }
        )
    return differences, failed


def finite_difference_tables(path: Path) -> dict[str, dict[str, dict[str, float]]]:
    """Read the explicit Forward/Backward/Central derivative tables from .stab."""
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    tables: dict[str, dict[str, dict[str, float]]] = {}
    for method in ("Forward", "Backward", "Central"):
        heading = f"# {method} finite-difference derivatives"
        try:
            start = lines.index(heading)
        except ValueError as error:
            raise ValueError(f"Missing {method} derivative table: {path}") from error
        headers = lines[start + 1].split()[1:]
        if not headers:
            raise ValueError(f"Empty {method} derivative header: {path}")
        values: dict[str, dict[str, float]] = {}
        for line in lines[start + 4:]:
            fields = line.split()
            if not fields or fields[0] not in COEFFICIENTS:
                if values:
                    break
                continue
            if len(fields) != len(headers) + 1:
                raise ValueError(
                    f"Malformed {method} derivative row for {fields[0]}: {path}"
                )
            values[fields[0]] = {
                header: float(value) for header, value in zip(headers, fields[1:])
            }
        if set(values) != set(COEFFICIENTS):
            raise ValueError(f"Incomplete {method} derivative table: {path}")
        tables[method] = values
    return tables


def check_explicit_derivative_identities(
    path: Path, atol: float = 2e-7,
) -> list[dict[str, object]]:
    """Require finite tables and Central == (Forward + Backward) / 2."""
    try:
        tables = finite_difference_tables(path)
    except (OSError, ValueError) as error:
        return [{"field": str(path), "status": str(error)}]

    failures: list[dict[str, object]] = []
    forward, backward, central = (
        tables["Forward"], tables["Backward"], tables["Central"]
    )
    for coefficient in COEFFICIENTS:
        columns = set(forward[coefficient])
        if set(backward[coefficient]) != columns or set(central[coefficient]) != columns:
            failures.append({
                "field": coefficient,
                "status": "Forward/Backward/Central columns differ",
            })
            continue
        for column in sorted(columns):
            operands = (
                forward[coefficient][column],
                backward[coefficient][column],
                central[coefficient][column],
            )
            if not all(math.isfinite(value) for value in operands):
                failures.append({
                    "field": f"{coefficient}.{column}",
                    "status": "non-finite derivative value",
                    "values": operands,
                })
                continue
            expected = 0.5 * (operands[0] + operands[1])
            error = abs(operands[2] - expected)
            if not math.isfinite(error) or error > atol:
                failures.append({
                    "field": f"{coefficient}.{column}",
                    "absolute_error": error,
                    "tolerance": atol,
                })
    return failures


def final_value(result: dict[str, object], name: str) -> float:
    values = result[name]
    if not isinstance(values, list) or not values:
        raise ValueError(f"Missing result value: {name}")
    return float(values[-1])


def normal_sweep_coefficients(history: dict[str, object]) -> dict[str, float]:
    return {
        "CFx": final_value(history, "CFxo") + final_value(history, "CFxiw"),
        "CFy": final_value(history, "CFyo") + final_value(history, "CFyiw"),
        "CFz": final_value(history, "CFzo") + final_value(history, "CFziw"),
        "CMx": final_value(history, "CMxo") + final_value(history, "CMxi"),
        "CMy": final_value(history, "CMyo") + final_value(history, "CMyi"),
        "CMz": final_value(history, "CMzo") + final_value(history, "CMzi"),
        "CL": final_value(history, "CLo") + final_value(history, "CLiw"),
        "CD": final_value(history, "CDo") + final_value(history, "CDiw"),
        "CS": final_value(history, "CSo") + final_value(history, "CSiw"),
        "CMl": -(final_value(history, "CMxo") + final_value(history, "CMxi")),
        "CMm": final_value(history, "CMyo") + final_value(history, "CMyi"),
        "CMn": -(final_value(history, "CMzo") + final_value(history, "CMzi")),
    }


def compare_coefficients(
    name: str,
    expected: dict[str, float],
    actual: dict[str, str],
    rtol: float,
    atol: float,
) -> tuple[dict[str, object], int]:
    differences = []
    failures = 0
    for coefficient in COEFFICIENTS:
        reference = expected[coefficient]
        candidate = float(actual[coefficient])
        tolerance = atol + rtol * abs(reference)
        error = abs(candidate - reference)
        passed = math.isfinite(error) and error <= tolerance
        failures += not passed
        differences.append({
            "field": coefficient,
            "official": reference,
            "state_sweep": candidate,
            "absolute_error": error,
            "tolerance": tolerance,
            "status": "pass" if passed else "fail",
        })
    return {"name": name, "status": "PASS" if failures == 0 else "FAIL", "differences": differences}, failures


def wing_load_column(name: str, quantity_and_axis: str) -> str:
    """Return the quantity-first State Sweep wing column name."""
    return f"{quantity_and_axis[:-1]}_{quantity_and_axis[-1]}_{name}"


def wing_center_moment_column(name: str, axis: str) -> str:
    """Return a State Sweep moment-about-planform-center column name."""
    return f"CM_{axis}_center_{name}"


def _record_identity(
    differences: list[dict[str, object]], row: int | str, field: str,
    actual: float, expected: float, tolerance: float,
) -> None:
    finite = math.isfinite(actual) and math.isfinite(expected)
    error = abs(actual - expected) if finite else math.inf
    if not finite or not math.isfinite(error) or error > tolerance:
        differences.append({
            "row": row,
            "field": field,
            "actual": actual,
            "expected": expected,
            "error": error,
            "tolerance": tolerance,
            "status": "non-finite" if not finite else "identity mismatch",
        })


def _finite_vector(value: object, length: int = 3) -> list[float] | None:
    if not isinstance(value, list) or len(value) != length:
        return None
    try:
        output = [float(item) for item in value]
    except (TypeError, ValueError):
        return None
    return output if all(math.isfinite(item) for item in output) else None


def check_state_sweep_output_identities(
    rows: list[dict[str, str]], manifest: dict[str, object], bref: float, cref: float,
) -> tuple[dict[str, object], int]:
    """Validate physical-wing, center-translation, and hinge-output contracts."""
    differences: list[dict[str, object]] = []
    if not rows:
        differences.append({"field": "rows", "status": "State Sweep emitted no rows"})
    if not math.isfinite(bref) or bref <= 0.0:
        differences.append({"field": "Bref", "status": "must be finite and positive"})
    if not math.isfinite(cref) or cref <= 0.0:
        differences.append({"field": "Cref", "status": "must be finite and positive"})
    if differences:
        return {
            "name": "wing_and_hinge_output_identities",
            "status": "FAIL",
            "rows": len(rows),
            "failures": len(differences),
            "differences": differences,
        }, len(differences)

    try:
        wing_items = manifest["wing_loads"]
        if not isinstance(wing_items, list):
            raise TypeError("wing_loads is not a list")
        physical_geometry = {
            str(item["name"]): item for item in wing_items if isinstance(item, dict)
        }
        sides = ("paritywing_ypos", "paritywing_yneg")
        if any(side not in physical_geometry for side in sides):
            raise KeyError(f"missing required physical wings {sides}")
    except (KeyError, TypeError, ValueError) as error:
        differences.append({"field": "manifest.wing_loads", "status": str(error)})
        return {
            "name": "wing_and_hinge_output_identities",
            "status": "FAIL",
            "rows": len(rows),
            "failures": len(differences),
            "differences": differences,
        }, len(differences)

    areas: dict[str, float] = {}
    centers: dict[str, list[float]] = {}
    references: dict[str, list[float]] = {}
    frames: dict[str, dict[str, list[float]]] = {}
    for side in sides:
        item = physical_geometry[side]
        try:
            area = float(item["planform_area"])
        except (KeyError, TypeError, ValueError):
            area = math.nan
        areas[side] = area
        if not math.isfinite(area) or area <= 0.0:
            differences.append({
                "field": f"manifest.{side}.planform_area",
                "actual": area,
                "status": "must be finite and positive",
            })
        center = _finite_vector(item.get("planform_center"))
        reference = _finite_vector(item.get("reference_point"))
        if center is None:
            differences.append({
                "field": f"manifest.{side}.planform_center",
                "status": "must contain three finite values",
            })
            center = [math.nan] * 3
        if reference is None:
            differences.append({
                "field": f"manifest.{side}.reference_point",
                "status": "must contain three finite values",
            })
            reference = [math.nan] * 3
        centers[side], references[side] = center, reference

        raw_frame = item.get("frame")
        frame: dict[str, list[float]] = {}
        if not isinstance(raw_frame, dict):
            differences.append({
                "field": f"manifest.{side}.frame", "status": "missing frame",
            })
        else:
            for vector_name in ("chord", "span", "normal"):
                vector = _finite_vector(raw_frame.get(vector_name))
                if vector is None:
                    differences.append({
                        "field": f"manifest.{side}.frame.{vector_name}",
                        "status": "must contain three finite values",
                    })
                else:
                    frame[vector_name] = vector
                    norm = math.sqrt(sum(component * component for component in vector))
                    _record_identity(
                        differences, "manifest", f"{side}.{vector_name}_unit", norm, 1.0, 1e-8,
                    )
            if len(frame) == 3:
                for first, second in (("chord", "span"), ("chord", "normal"), ("span", "normal")):
                    dot = sum(a*b for a, b in zip(frame[first], frame[second]))
                    _record_identity(
                        differences, "manifest", f"{side}.{first}_dot_{second}", dot, 0.0, 1e-8,
                    )
        frames[side] = frame

    _record_identity(
        differences, "manifest", "symmetric_planform_area",
        areas[sides[0]], areas[sides[1]], 1e-8,
    )
    for axis, sign in enumerate((1.0, -1.0, 1.0)):
        _record_identity(
            differences, "manifest", f"symmetric_planform_center_{'xyz'[axis]}",
            centers[sides[0]][axis], sign * centers[sides[1]][axis], 1e-8,
        )
        _record_identity(
            differences, "manifest", f"symmetric_reference_point_{'xyz'[axis]}",
            references[sides[0]][axis], references[sides[1]][axis], 1e-12,
        )
    if all(math.isfinite(centers[side][1]) for side in sides) and max(
        abs(centers[side][1]) for side in sides
    ) <= 1e-8:
        differences.append({
            "field": "manifest.symmetric_planform_center_y",
            "status": "both physical-side centers lie on the symmetry plane",
        })

    parent_area = sum(areas.values())
    if not math.isfinite(parent_area) or parent_area <= 0.0:
        differences.append({
            "field": "manifest.parent_planform_area",
            "actual": parent_area,
            "status": "must be finite and positive",
        })
        parent_center = [math.nan] * 3
    else:
        parent_center = [
            sum(areas[side] * centers[side][axis] for side in sides) / parent_area
            for axis in range(3)
        ]
    output_geometry = {
        side: (centers[side], references[side]) for side in sides
    }
    output_geometry["paritywing"] = (parent_center, references[sides[0]])

    try:
        for row_index, row in enumerate(rows):
            for side in (*sides, "paritywing"):
                for axis in "xyz":
                    for kind, viscous, inviscid in (
                        ("CF", f"CFo{axis}", f"CFiw{axis}"),
                        ("CM", f"CMo{axis}", f"CMi{axis}"),
                    ):
                        total_column = wing_load_column(side, f"{kind}{axis}")
                        expected = float(row[wing_load_column(side, viscous)]) + float(
                            row[wing_load_column(side, inviscid)]
                        )
                        _record_identity(
                            differences, row_index, total_column,
                            float(row[total_column]), expected, 1e-12,
                        )
                center, reference = output_geometry[side]
                dx, dy, dz = (
                    float(center[index]) - float(reference[index]) for index in range(3)
                )
                fx = float(row[wing_load_column(side, "CFox")]) + float(
                    row[wing_load_column(side, "CFix")]
                )
                fy = float(row[wing_load_column(side, "CFoy")]) + float(
                    row[wing_load_column(side, "CFiy")]
                )
                fz = float(row[wing_load_column(side, "CFoz")]) + float(
                    row[wing_load_column(side, "CFiz")]
                )
                expected_center_moments = {
                    "x": float(row[wing_load_column(side, "CMx")]) - (dy*fz-dz*fy)/bref,
                    "y": float(row[wing_load_column(side, "CMy")]) - (dz*fx-dx*fz)/cref,
                    "z": float(row[wing_load_column(side, "CMz")]) - (dx*fy-dy*fx)/bref,
                }
                for axis, expected in expected_center_moments.items():
                    column = wing_center_moment_column(side, axis)
                    _record_identity(
                        differences, row_index, column, float(row[column]), expected, 1e-12,
                    )
            for suffix in (
                "CFox", "CFoy", "CFoz", "CFix", "CFiy", "CFiz", "CFx", "CFy", "CFz",
                "CMox", "CMoy", "CMoz", "CMix", "CMiy", "CMiz", "CMx", "CMy", "CMz",
                "CFiwx", "CFiwy", "CFiwz",
            ):
                expected = float(row[wing_load_column(sides[0], suffix)]) + float(
                    row[wing_load_column(sides[1], suffix)]
                )
                column = wing_load_column("paritywing", suffix)
                _record_identity(
                    differences, row_index, column, float(row[column]), expected, 1e-12,
                )
            for suffix in ("CFx", "CFy", "CFz", "CMx", "CMy", "CMz"):
                _record_identity(
                    differences, row_index, f"all_wings_{suffix}_vs_vehicle",
                    float(row[wing_load_column("paritywing", suffix)]),
                    float(row[suffix]), 1e-7,
                )
    except (KeyError, TypeError, ValueError) as error:
        differences.append({"field": "wing CSV schema", "status": str(error)})

    # At the zero-rate, zero-control state, the deterministic parity wing is
    # mirror symmetric. This catches an apparently valid side sum whose load or
    # geometry was accidentally assigned wholly to one symmetry instance.
    control_columns = [
        str(item["column"]) for item in manifest.get("control_groups", [])
        if isinstance(item, dict) and "column" in item
    ]
    base_rows = []
    for row in rows:
        try:
            state = [float(row[name]) for name in (
                "p_rad_per_tunit", "q_rad_per_tunit", "r_rad_per_tunit", *control_columns,
            )]
        except (KeyError, TypeError, ValueError):
            continue
        if all(math.isfinite(value) and abs(value) <= 1e-12 for value in state):
            base_rows.append(row)
    if not base_rows:
        differences.append({"field": "symmetric_base_state", "status": "missing"})
    else:
        base = base_rows[0]
        try:
            for prefix in ("CFo", "CFi", "CF", "CFiw"):
                for axis, sign in zip("xyz", (1.0, -1.0, 1.0)):
                    _record_identity(
                        differences, "symmetric base", f"{prefix}{axis}_mirror",
                        float(base[wing_load_column(sides[0], f"{prefix}{axis}")]),
                        sign * float(base[wing_load_column(sides[1], f"{prefix}{axis}")]),
                        1e-7,
                    )
            for prefix in ("CMo", "CMi", "CM"):
                for axis, sign in zip("xyz", (-1.0, 1.0, -1.0)):
                    _record_identity(
                        differences, "symmetric base", f"{prefix}{axis}_mirror",
                        float(base[wing_load_column(sides[0], f"{prefix}{axis}")]),
                        sign * float(base[wing_load_column(sides[1], f"{prefix}{axis}")]),
                        1e-7,
                    )
            for axis, sign in zip("xyz", (-1.0, 1.0, -1.0)):
                _record_identity(
                    differences, "symmetric base", f"CM{axis}_center_mirror",
                    float(base[wing_center_moment_column(sides[0], axis)]),
                    sign * float(base[wing_center_moment_column(sides[1], axis)]),
                    1e-7,
                )
        except (KeyError, TypeError, ValueError) as error:
            differences.append({"field": "symmetric wing columns", "status": str(error)})

    hinge_items = manifest.get("hinge_pressure_loads")
    hinges = hinge_items if isinstance(hinge_items, list) else []
    if len(hinges) != 2:
        differences.append({
            "field": "manifest.hinge_pressure_loads",
            "actual": len(hinges),
            "expected": 2,
            "status": "one physical hinge per symmetry side is required",
        })
    hinges_by_wing: dict[str, dict[str, object]] = {}
    for hinge in hinges:
        if not isinstance(hinge, dict):
            differences.append({"field": "manifest.hinge", "status": "entry is not an object"})
            continue
        wing = str(hinge.get("wing", ""))
        column = str(hinge.get("column", ""))
        if wing not in sides or wing in hinges_by_wing:
            differences.append({
                "field": f"manifest.hinge.{column}",
                "status": f"invalid or duplicate physical-wing owner {wing!r}",
            })
            continue
        origin = _finite_vector(hinge.get("origin"))
        direction = _finite_vector(hinge.get("direction"))
        if not column:
            differences.append({"field": f"manifest.hinge.{wing}", "status": "missing column"})
        if origin is None:
            differences.append({"field": f"manifest.hinge.{column}.origin", "status": "non-finite"})
        if direction is None:
            differences.append({"field": f"manifest.hinge.{column}.direction", "status": "non-finite"})
        else:
            norm = math.sqrt(sum(component*component for component in direction))
            _record_identity(
                differences, "manifest", f"{column}.direction_unit", norm, 1.0, 1e-8,
            )
        hinges_by_wing[wing] = hinge
        for row_index, row in enumerate(rows):
            try:
                value = float(row[column])
            except (KeyError, TypeError, ValueError):
                value = math.nan
            if not math.isfinite(value):
                differences.append({
                    "row": row_index, "field": column, "actual": value,
                    "status": "non-finite or missing hinge coefficient",
                })
    if all(side in hinges_by_wing for side in sides):
        positive, negative = (hinges_by_wing[side] for side in sides)
        positive_origin = _finite_vector(positive.get("origin"))
        negative_origin = _finite_vector(negative.get("origin"))
        positive_direction = _finite_vector(positive.get("direction"))
        negative_direction = _finite_vector(negative.get("direction"))
        if positive_origin is not None and negative_origin is not None:
            for axis, sign in enumerate((1.0, -1.0, 1.0)):
                _record_identity(
                    differences, "manifest", f"hinge_origin_mirror_{'xyz'[axis]}",
                    positive_origin[axis], sign * negative_origin[axis], 1e-8,
                )
        if positive_direction is not None and negative_direction is not None:
            for axis, sign in enumerate((1.0, -1.0, 1.0)):
                _record_identity(
                    differences, "manifest", f"hinge_direction_mirror_{'xyz'[axis]}",
                    positive_direction[axis], sign * negative_direction[axis], 1e-8,
                )
        if base_rows:
            try:
                positive_value = float(base_rows[0][str(positive["column"])])
                negative_value = float(base_rows[0][str(negative["column"])])
                _record_identity(
                    differences, "symmetric base", "hinge_coefficient_mirror",
                    positive_value, -negative_value, 1e-5,
                )
            except (KeyError, TypeError, ValueError) as error:
                differences.append({"field": "symmetric hinge columns", "status": str(error)})

    failures = len(differences)
    return {
        "name": "wing_and_hinge_output_identities",
        "status": "PASS" if failures == 0 else "FAIL",
        "rows": len(rows),
        "failures": failures,
        "differences": differences[:100],
    }, failures


def compare_stability_map_to_state_sweep(
    stability_rows: list[dict[str, str]], state_rows: list[dict[str, str]],
    manifest: dict[str, object], rtol: float, atol: float,
) -> tuple[dict[str, object], int]:
    """Compare raw +/- -stab solutions with matching State Sweep rows."""
    differences: list[dict[str, object]] = []
    control_groups = manifest.get("control_groups")
    if not isinstance(control_groups, list) or len(control_groups) != 1:
        differences.append({
            "field": "manifest.control_groups",
            "status": "parity model must expose exactly one control group",
        })
        return {
            "name": "stability_map_vs_state_sweep",
            "status": "FAIL", "failures": 1, "differences": differences,
        }, 1
    control = control_groups[0]
    if not isinstance(control, dict):
        differences.append({"field": "manifest.control_groups[0]", "status": "invalid"})
        return {
            "name": "stability_map_vs_state_sweep",
            "status": "FAIL", "failures": 1, "differences": differences,
        }, 1
    control_column = str(control["column"])
    control_derivative = f"{control['name']}_per_deg"
    cases = (
        ("base", "base", "base", (0.0, 0.0, 0.0, 0.0)),
        ("p_positive", "p_rad_per_tunit", "positive", (0.01, 0.0, 0.0, 0.0)),
        ("p_negative", "p_rad_per_tunit", "negative", (-0.01, 0.0, 0.0, 0.0)),
        ("q_positive", "q_rad_per_tunit", "positive", (0.0, 0.01, 0.0, 0.0)),
        ("q_negative", "q_rad_per_tunit", "negative", (0.0, -0.01, 0.0, 0.0)),
        ("r_positive", "r_rad_per_tunit", "positive", (0.0, 0.0, 0.01, 0.0)),
        ("r_negative", "r_rad_per_tunit", "negative", (0.0, 0.0, -0.01, 0.0)),
        ("control_positive", control_derivative, "positive", (0.0, 0.0, 0.0, 0.1)),
        ("control_negative", control_derivative, "negative", (0.0, 0.0, 0.0, -0.1)),
    )
    if not state_rows or not stability_rows:
        differences.append({"field": "rows", "status": "missing State Sweep or Stability Map rows"})
        return {
            "name": "stability_map_vs_state_sweep",
            "status": "FAIL", "failures": 1, "differences": differences,
        }, 1

    state_fields = list(state_rows[0])
    try:
        first_output = state_fields.index("CFx")
    except ValueError:
        differences.append({"field": "CFx", "status": "missing State Sweep output columns"})
        return {
            "name": "stability_map_vs_state_sweep",
            "status": "FAIL", "failures": 1, "differences": differences,
        }, 1
    output_columns = state_fields[first_output:]
    missing_columns = [column for column in output_columns if column not in stability_rows[0]]
    if missing_columns:
        differences.append({
            "field": "Stability Map columns", "status": "missing", "columns": missing_columns,
        })
        return {
            "name": "stability_map_vs_state_sweep",
            "status": "FAIL", "failures": 1, "differences": differences,
        }, 1

    compared = 0
    matched_cases = 0
    for case_name, derivative, direction, state in cases:
        stability_matches = [
            row for row in stability_rows
            if row.get("derivative") == derivative and row.get("direction") == direction
        ]
        state_matches = []
        for row in state_rows:
            try:
                actual_state = tuple(float(row[column]) for column in (
                    "p_rad_per_tunit", "q_rad_per_tunit", "r_rad_per_tunit", control_column,
                ))
            except (KeyError, TypeError, ValueError):
                continue
            if all(math.isclose(value, target, rel_tol=0.0, abs_tol=1e-12)
                   for value, target in zip(actual_state, state)):
                state_matches.append(row)
        if len(stability_matches) != 1 or len(state_matches) != 1:
            differences.append({
                "field": case_name,
                "status": "case cardinality mismatch",
                "stability_rows": len(stability_matches),
                "state_sweep_rows": len(state_matches),
            })
            continue
        matched_cases += 1
        stability_row, state_row = stability_matches[0], state_matches[0]
        for column in output_columns:
            try:
                reference = float(stability_row[column])
                candidate = float(state_row[column])
            except (KeyError, TypeError, ValueError):
                differences.append({
                    "field": f"{case_name}.{column}", "status": "non-numeric or missing",
                })
                continue
            tolerance = atol + rtol * abs(reference)
            error = abs(candidate - reference)
            compared += 1
            if (not math.isfinite(reference) or not math.isfinite(candidate)
                    or not math.isfinite(error) or error > tolerance):
                differences.append({
                    "field": f"{case_name}.{column}",
                    "stability_map": reference,
                    "state_sweep": candidate,
                    "absolute_error": error,
                    "tolerance": tolerance,
                    "status": "non-finite" if not (
                        math.isfinite(reference) and math.isfinite(candidate)
                    ) else "mismatch",
                })
    failures = len(differences)
    return {
        "name": "stability_map_vs_state_sweep",
        "status": "PASS" if failures == 0 else "FAIL",
        "cases": matched_cases,
        "compared": compared,
        "failures": failures,
        "differences": differences[:200],
    }, failures


def run_state_sweep_cross_checks(
    custom: Path,
    work: Path,
    mode: str,
    official_base: dict[str, object],
    official_stab: dict[str, object],
    timeout: int,
    rtol: float,
    atol: float,
) -> tuple[list[dict[str, object]], int]:
    source = work / f"{mode}_stab" / "custom"
    output = work / f"state_sweep_crosscheck_{mode}"
    stability_output = work / f"stability_map_crosscheck_{mode}"
    output.mkdir(parents=True, exist_ok=True)
    stability_output.mkdir(parents=True, exist_ok=True)
    for pattern in ("parity_wing.vspgeom", "parity_wing.vspaero", "parity_wing.vkey", "parity_wing.csf",
                    "parity_wing*.taglist", "parity_wing*.tag"):
        for path in source.glob(pattern):
            shutil.copy2(path, output / path.name)
            shutil.copy2(path, stability_output / path.name)

    command = [
        str(custom / "vspaero.exe"), "-omp", "1", "-state-sweep",
        "-state-p", "-0.01,0,0.01", "-state-q", "-0.01,0,0.01",
        "-state-r", "-0.01,0,0.01", "-state-control", "1", "-0.1,0,0.1",
        "-state-wing-load", "1", "paritywing_ypos", "0", "0", "0",
        "-state-wing-load", "2", "paritywing_yneg", "0", "0", "0",
        "-state-hinge-loads",
        "-state-chunk-size", "100", "parity_wing",
    ]
    with (output / "run.log").open("w", encoding="utf-8") as log:
        subprocess.run(command, cwd=output, stdout=log, stderr=subprocess.STDOUT,
                       check=True, timeout=timeout, env={**os.environ, "OMP_NUM_THREADS": "1"})
    with (output / "parity_wing.state_sweep" / "part-000000.csv").open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    manifest = json.loads(
        (output / "parity_wing.state_sweep" / "manifest.json").read_text(encoding="utf-8")
    )

    stability_command = [
        str(custom / "vspaero.exe"), "-omp", "1", "-stab", "-stab-map-csv",
        "-stab-select", "p,q,r,controls",
        "-state-wing-load", "1", "paritywing_ypos", "0", "0", "0",
        "-state-wing-load", "2", "paritywing_yneg", "0", "0", "0",
        "-state-hinge-loads", "parity_wing",
    ]
    with (stability_output / "run.log").open("w", encoding="utf-8") as log:
        subprocess.run(
            stability_command, cwd=stability_output, stdout=log, stderr=subprocess.STDOUT,
            check=True, timeout=timeout, env={**os.environ, "OMP_NUM_THREADS": "1"},
        )
    with (stability_output / "parity_wing.stability_cases.csv").open(
        newline="", encoding="utf-8",
    ) as stream:
        stability_rows = list(csv.DictReader(stream))
    setup_text = (output / "parity_wing.vspaero").read_text(encoding="utf-8", errors="replace")
    def setup_value(name: str) -> float:
        match = re.search(rf"(?m)^\s*{re.escape(name)}\s*=\s*([-+0-9.eE]+)", setup_text)
        if not match:
            raise ValueError(f"State Sweep parity setup has no {name} value")
        return float(match.group(1))
    bref, cref = setup_value("Bref"), setup_value("Cref")
    control_column = manifest["control_groups"][0]["column"]

    def select(p: float, q: float, r: float, control: float) -> dict[str, str]:
        for row in rows:
            state = tuple(float(row[key]) for key in
                          ("p_rad_per_tunit", "q_rad_per_tunit", "r_rad_per_tunit", control_column))
            if all(math.isclose(value, target, abs_tol=1e-12)
                   for value, target in zip(state, (p, q, r, control))):
                return row
        raise ValueError(f"State Sweep did not emit state {(p, q, r, control)}")

    checks: list[dict[str, object]] = []
    failures = 0
    identity_check, identity_failures = check_state_sweep_output_identities(
        rows, manifest, bref, cref,
    )
    checks.append(identity_check)
    failures += identity_failures

    map_check, map_failures = compare_stability_map_to_state_sweep(
        stability_rows, rows, manifest, rtol, atol,
    )
    checks.append(map_check)
    failures += map_failures

    base_history = min(official_base["history"], key=lambda item: abs(final_value(item, "Alpha") - 4.0))
    check, count = compare_coefficients("normal_sweep_base", normal_sweep_coefficients(base_history),
                                        select(0, 0, 0, 0), rtol, atol)
    checks.append(check); failures += count

    stab = official_stab["stability"][0]
    for name, state, prefix in (
        ("stab_roll_positive", (0.01, 0, 0, 0), "Roll__Rate_"),
        ("stab_pitch_positive", (0, 0.01, 0, 0), "Pitch_Rate_"),
        ("stab_yaw_positive", (0, 0, 0.01, 0), "Yaw___Rate_"),
        ("stab_control_positive", (0, 0, 0, 0.1), "ParityWing_SS_CONT_0_"),
    ):
        expected = {coefficient: final_value(stab, prefix + coefficient) for coefficient in COEFFICIENTS}
        check, count = compare_coefficients(name, expected, select(*state), rtol, atol)
        checks.append(check); failures += count
    return checks, failures


def run_optimized_mode_check(
    executable: Path, case_dir: Path, analysis: str, timeout: int,
    rtol: float, atol: float,
) -> tuple[dict[str, object], int]:
    """Compare an opt-in optimized rerun with the official-parity custom baseline."""
    suffix = ".stab" if analysis == "stab" else ".polar"
    result_path = case_dir / f"parity_wing{suffix}"
    baseline = result_path.read_text(encoding="utf-8", errors="replace")
    mode_arguments = ["-stab", "-stab-optimize"] if analysis == "stab" else ["-steady-optimize"]
    command = [
        str(executable), "-omp", "1", *mode_arguments,
        "-state-continuation-min-wake-iters", "4",
        "-state-continuation-circulation-tol", "0.005",
        "-state-continuation-wake-tol", "0.2",
        "-state-continuation-load-tol", "0.0005",
        "-solver-opt-profile", "parity_wing",
    ]
    with (case_dir / "optimized_run.log").open("w", encoding="utf-8") as log:
        subprocess.run(command, cwd=case_dir, stdout=log, stderr=subprocess.STDOUT,
                       check=True, timeout=timeout, env={**os.environ, "OMP_NUM_THREADS": "1"})
    optimized = result_path.read_text(encoding="utf-8", errors="replace")
    number = re.compile(r"(?<![A-Za-z_])[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[Ee][-+]?\d+)?")
    expected = [float(value) for value in number.findall(baseline)]
    actual = [float(value) for value in number.findall(optimized)]
    failures = abs(len(expected) - len(actual))
    maximum_error = 0.0
    for reference, candidate in zip(expected, actual):
        error = abs(candidate - reference)
        maximum_error = max(maximum_error, error)
        if not math.isfinite(error) or error > atol + rtol * abs(reference):
            failures += 1
    return {
        "analysis": analysis,
        "status": "PASS" if failures == 0 else "FAIL",
        "values": min(len(expected), len(actual)),
        "failures": failures,
        "maximum_absolute_error": maximum_error,
        "reference_authority": "custom baseline already compared with packaged official build",
    }, failures


def finite_difference_column(path: Path, column: str) -> dict[str, dict[str, float]]:
    """Read one column from the explicit forward/backward/central .stab tables."""
    tables = finite_difference_tables(path)
    output: dict[str, dict[str, float]] = {}
    for method, coefficients in tables.items():
        if any(column not in values for values in coefficients.values()):
            raise ValueError(f"Missing {column} in {method} derivative table: {path}")
        output[method] = {
            coefficient: values[column] for coefficient, values in coefficients.items()
        }
    return output


def run_selective_control_check(
    executable: Path, case_dir: Path, timeout: int,
    rtol: float, atol: float,
) -> tuple[dict[str, object], int]:
    """Verify selected controls match the all-control official-parity baseline."""
    stab_path = case_dir / "parity_wing.stab"
    baseline = finite_difference_column(stab_path, "ConGrp_1")
    command = [
        str(executable), "-omp", "1", "-stab", "-stab-select", "controls",
        "-stab-control-select", "1", "parity_wing",
    ]
    log_path = case_dir / "selective_control_run.log"
    with log_path.open("w", encoding="utf-8") as log:
        subprocess.run(command, cwd=case_dir, stdout=log, stderr=subprocess.STDOUT,
                       check=True, timeout=timeout,
                       env={**os.environ, "OMP_NUM_THREADS": "1"})
    selected = finite_difference_column(stab_path, "ConGrp_1")
    failures = 0
    maximum_error = 0.0
    for method in baseline:
        for coefficient, reference in baseline[method].items():
            candidate = selected[method][coefficient]
            error = abs(candidate - reference)
            maximum_error = max(maximum_error, error)
            if not math.isfinite(error) or error > atol + rtol * abs(reference):
                failures += 1
    solve_count = sum(
        line.startswith("Solving...")
        for line in log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    )
    if solve_count != 3:
        failures += 1
    output = stab_path.read_text(encoding="utf-8", errors="replace")
    if "# Control group 1:" not in output or "selected=yes" not in output:
        failures += 1
    return {
        "status": "PASS" if failures == 0 else "FAIL",
        "values": 3 * len(COEFFICIENTS),
        "failures": failures,
        "maximum_absolute_error": maximum_error,
        "solver_cases": solve_count,
        "reference_authority": "all-control baseline already compared with packaged official build",
    }, failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--custom", type=Path, default=DEFAULT_CUSTOM)
    parser.add_argument(
        "--custom-vspaero", type=Path,
        help="Candidate vspaero.exe; use custom distribution for the Python API",
    )
    parser.add_argument("--rtol", type=float, default=1e-6)
    parser.add_argument("--atol", type=float, default=1e-8)
    parser.add_argument("--state-rtol", type=float, default=1e-4)
    parser.add_argument("--state-atol", type=float, default=5e-4)
    parser.add_argument("--timeout", type=int, default=600, help="seconds allowed per run")
    parser.add_argument("--keep-work", action="store_true")
    args = parser.parse_args()

    # Parity has exactly one authority: the packaged, unmodified official
    # distribution. Do not allow a branch/custom binary to be substituted.
    official = DEFAULT_OFFICIAL.resolve()
    custom = args.custom.resolve()
    custom_vspaero = (
        args.custom_vspaero.resolve() if args.custom_vspaero
        else custom / "vspaero.exe"
    )
    for distribution in (official, custom):
        if not (distribution / "vspaero.exe").is_file():
            parser.error(f"vspaero.exe not found in {distribution}")
        python_package(distribution)
    if not custom_vspaero.is_file():
        parser.error(f"candidate vspaero.exe not found: {custom_vspaero}")

    work = HERE / "_work"
    if work.exists():
        shutil.rmtree(work)
    report: dict[str, object] = {
        "official": str(official),
        "custom": str(custom),
        "rtol": args.rtol,
        "atol": args.atol,
        "cases": [],
    }
    total_failures = 0
    completed: dict[str, tuple[dict[str, object], dict[str, object]]] = {}
    optimized_checks: list[dict[str, object]] = []
    selective_control_checks: list[dict[str, object]] = []

    for mode, analysis in CASES:
        case_name = f"{mode}_{analysis}"
        print(f"Running {case_name}: official", flush=True)
        official_result = run_case(official, mode, analysis, work / case_name / "official", args.timeout)
        print(f"Running {case_name}: custom", flush=True)
        custom_result = run_case(
            custom, mode, analysis, work / case_name / "custom", args.timeout,
            custom_vspaero.parent,
        )
        completed[case_name] = (official_result, custom_result)
        differences, failures = compare(official_result, custom_result, args.rtol, args.atol)
        identity_failures = (
            check_explicit_derivative_identities(
                work / case_name / "custom" / "parity_wing.stab"
            )
            if analysis == "stab" else []
        )
        failures += len(identity_failures)
        total_failures += failures
        compared = len(differences)
        status = "PASS" if failures == 0 else "FAIL"
        print(f"  {status}: {compared - failures}/{compared} values within tolerance")
        report["cases"].append(
            {
                "name": case_name,
                "status": status,
                "compared": compared,
                "failures": failures,
                "differences": differences,
                "finite_difference_identity_failures": identity_failures,
            }
        )
        print(f"Running {case_name}: optimized mode", flush=True)
        optimized_check, optimized_failures = run_optimized_mode_check(
            custom_vspaero, work / case_name / "custom", analysis,
            args.timeout, args.rtol, args.atol,
        )
        optimized_check["geometry_mode"] = mode
        optimized_checks.append(optimized_check)
        total_failures += optimized_failures
        print(
            f"  {optimized_check['status']}: {optimized_check['values'] - optimized_failures}/"
            f"{optimized_check['values']} optimized values within tolerance"
        )
        if analysis == "stab":
            print(f"Running {case_name}: selective control group", flush=True)
            selective_check, selective_failures = run_selective_control_check(
                custom_vspaero, work / case_name / "custom",
                args.timeout, args.rtol, args.atol,
            )
            selective_check["geometry_mode"] = mode
            selective_control_checks.append(selective_check)
            total_failures += selective_failures
            print(
                f"  {selective_check['status']}: {selective_check['solver_cases']} solver cases, "
                f"{selective_check['failures']} derivative mismatches"
            )

    report["optimized_mode_checks"] = optimized_checks
    report["selective_control_checks"] = selective_control_checks

    all_state_checks = []
    state_failures = 0
    for mode in ("thin", "thick"):
        print(f"Running State Sweep cross-mode checks: {mode}", flush=True)
        mode_checks, mode_failures = run_state_sweep_cross_checks(
            custom_vspaero.parent, work, mode,
            completed[f"{mode}_base"][0], completed[f"{mode}_stab"][0],
            args.timeout, args.state_rtol, args.state_atol,
        )
        for check in mode_checks:
            check["geometry_mode"] = mode
        all_state_checks.extend(mode_checks)
        state_failures += mode_failures
    total_failures += state_failures
    report["state_sweep_cross_checks"] = all_state_checks
    report["state_sweep_tolerances"] = {"rtol": args.state_rtol, "atol": args.state_atol}
    print(f"  {'PASS' if state_failures == 0 else 'FAIL'}: {state_failures} coefficient mismatches")

    report["status"] = "PASS" if total_failures == 0 else "FAIL"
    report["failures"] = total_failures
    report_file = HERE / "parity_report.json"
    report_file.write_text(json.dumps(report, indent=2), encoding="utf-8")
    if not args.keep_work:
        shutil.rmtree(work)
    print(f"\nOverall: {report['status']} ({total_failures} failures)")
    print(f"Report: {report_file}")
    return 0 if total_failures == 0 else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as error:
        print(f"Parity worker failed with exit code {error.returncode}.", file=sys.stderr)
        raise SystemExit(error.returncode)
    except subprocess.TimeoutExpired:
        print("Parity worker timed out.", file=sys.stderr)
        raise SystemExit(2)
