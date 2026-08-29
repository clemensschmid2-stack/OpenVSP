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


def check_central_identities(custom: dict[str, object], atol: float = 2e-7) -> list[dict[str, object]]:
    values = flatten(custom)
    failures = []
    for central_key, central in values.items():
        marker = "_Central_Value"
        if marker not in central_key:
            continue
        forward_key = central_key.replace(marker, "_Forward_Value")
        backward_key = central_key.replace(marker, "_Backward_Value")
        if forward_key not in values or backward_key not in values:
            failures.append({"field": central_key, "status": "missing derivative partner"})
            continue
        expected = 0.5 * (float(values[forward_key]) + float(values[backward_key]))
        error = abs(float(central) - expected)
        if error > atol:
            failures.append({"field": central_key, "absolute_error": error, "tolerance": atol})
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
    output.mkdir(parents=True, exist_ok=True)
    for pattern in ("parity_wing.vspgeom", "parity_wing.vspaero", "parity_wing.vkey", "parity_wing.csf",
                    "parity_wing*.taglist", "parity_wing*.tag"):
        for path in source.glob(pattern):
            shutil.copy2(path, output / path.name)

    command = [
        str(custom / "vspaero.exe"), "-omp", "1", "-state-sweep",
        "-state-p", "-0.01,0,0.01", "-state-q", "-0.01,0,0.01",
        "-state-r", "-0.01,0,0.01", "-state-control", "1", "0,0.1",
        "-state-wing-load", "1", "paritywing_ypos", "0", "0", "0",
        "-state-wing-load", "2", "paritywing_yneg", "0", "0", "0",
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

    # The optional physical-instance output must remain algebraically exact:
    # total = viscous + surface inviscid, and the parent wing is the sum of
    # its independently solved symmetry instances. Wake/Trefftz force is an
    # alternative inviscid diagnostic and is checked only for side summation.
    identity_differences = []
    identity_failures = 0
    physical_geometry = {item["name"]: item for item in manifest["wing_loads"]}
    parent_area = sum(float(physical_geometry[name]["planform_area"])
                      for name in ("paritywing_ypos", "paritywing_yneg"))
    parent_center = [
        sum(float(physical_geometry[name]["planform_area"])
            * float(physical_geometry[name]["planform_center"][axis])
            for name in ("paritywing_ypos", "paritywing_yneg")) / parent_area
        for axis in range(3)
    ]
    output_geometry = {
        name: (physical_geometry[name]["planform_center"], physical_geometry[name]["reference_point"])
        for name in ("paritywing_ypos", "paritywing_yneg")
    }
    output_geometry["paritywing"] = (parent_center, physical_geometry["paritywing_ypos"]["reference_point"])
    for row_index, row in enumerate(rows):
        for side in ("paritywing_ypos", "paritywing_yneg", "paritywing"):
            for axis in "xyz":
                for kind, viscous, inviscid in (
                    ("CF", f"CFo{axis}", f"CFiw{axis}"),
                    ("CM", f"CMo{axis}", f"CMi{axis}"),
                ):
                    total_column = wing_load_column(side, f"{kind}{axis}")
                    expected = float(row[wing_load_column(side, viscous)]) + float(
                        row[wing_load_column(side, inviscid)]
                    )
                    error = abs(float(row[total_column]) - expected)
                    if error > 1e-12:
                        identity_failures += 1
                        identity_differences.append({"row": row_index, "field": total_column, "error": error})
            center, reference = output_geometry[side]
            dx, dy, dz = (float(center[index]) - float(reference[index]) for index in range(3))
            fx = float(row[wing_load_column(side, "CFox")]) + float(row[wing_load_column(side, "CFix")])
            fy = float(row[wing_load_column(side, "CFoy")]) + float(row[wing_load_column(side, "CFiy")])
            fz = float(row[wing_load_column(side, "CFoz")]) + float(row[wing_load_column(side, "CFiz")])
            expected_center_moments = {
                "x": float(row[wing_load_column(side, "CMx")]) - (dy*fz-dz*fy)/bref,
                "y": float(row[wing_load_column(side, "CMy")]) - (dz*fx-dx*fz)/cref,
                "z": float(row[wing_load_column(side, "CMz")]) - (dx*fy-dy*fx)/bref,
            }
            for axis, expected in expected_center_moments.items():
                column = wing_center_moment_column(side, axis)
                error = abs(float(row[column])-expected)
                if error > 1e-12:
                    identity_failures += 1
                    identity_differences.append({"row": row_index, "field": column, "error": error})
        for suffix in (
            "CFox", "CFoy", "CFoz", "CFix", "CFiy", "CFiz", "CFx", "CFy", "CFz",
            "CMox", "CMoy", "CMoz", "CMix", "CMiy", "CMiz", "CMx", "CMy", "CMz",
            "CFiwx", "CFiwy", "CFiwz",
        ):
            expected = float(row[wing_load_column("paritywing_ypos", suffix)]) + float(
                row[wing_load_column("paritywing_yneg", suffix)]
            )
            parent_column = wing_load_column("paritywing", suffix)
            error = abs(float(row[parent_column]) - expected)
            if error > 1e-12:
                identity_failures += 1
                identity_differences.append({"row": row_index, "field": parent_column, "error": error})
        for suffix in ("CFx", "CFy", "CFz", "CMx", "CMy", "CMz"):
            error = abs(float(row[wing_load_column("paritywing", suffix)]) - float(row[suffix]))
            # The partition changes floating-point summation order relative to
            # the monolithic vehicle accumulator. Require coefficient agreement
            # well below solver parity tolerances without demanding bit identity.
            if error > 1e-7:
                identity_failures += 1
                identity_differences.append({
                    "row": row_index,
                    "field": f"all_wings_{suffix}_vs_vehicle",
                    "error": error,
                })
    checks.append({
        "name": "wing_side_parent_identities",
        "status": "PASS" if identity_failures == 0 else "FAIL",
        "rows": len(rows),
        "failures": identity_failures,
        "differences": identity_differences[:100],
    })
    failures += identity_failures

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
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    tables: dict[str, dict[str, float]] = {}
    for method in ("Forward", "Backward", "Central"):
        heading = f"# {method} finite-difference derivatives"
        start = lines.index(heading)
        headers = lines[start + 1].split()[1:]
        if column not in headers:
            raise ValueError(f"Missing {column} in {method} derivative table: {path}")
        value_index = headers.index(column) + 1
        values: dict[str, float] = {}
        for line in lines[start + 4:]:
            fields = line.split()
            if not fields or fields[0] not in COEFFICIENTS:
                if values:
                    break
                continue
            values[fields[0]] = float(fields[value_index])
        if set(values) != set(COEFFICIENTS):
            raise ValueError(f"Incomplete {method} derivative table: {path}")
        tables[method] = values
    return tables


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
        identity_failures = check_central_identities(custom_result) if analysis == "stab" else []
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
                "central_identity_failures": identity_failures,
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
