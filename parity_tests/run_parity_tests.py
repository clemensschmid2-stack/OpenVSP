#!/usr/bin/env python3
"""Compare official and locally built OpenVSP/VSPAERO numerical results."""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
from pathlib import Path
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
        "-state-chunk-size", "100", "parity_wing",
    ]
    with (output / "run.log").open("w", encoding="utf-8") as log:
        subprocess.run(command, cwd=output, stdout=log, stderr=subprocess.STDOUT,
                       check=True, timeout=timeout, env={**os.environ, "OMP_NUM_THREADS": "1"})
    with (output / "parity_wing.state_sweep" / "part-000000.csv").open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))

    def select(p: float, q: float, r: float, control: float) -> dict[str, str]:
        for row in rows:
            state = tuple(float(row[key]) for key in
                          ("p_rad_per_tunit", "q_rad_per_tunit", "r_rad_per_tunit", "ctrl_001_deg"))
            if all(math.isclose(value, target, abs_tol=1e-12)
                   for value, target in zip(state, (p, q, r, control))):
                return row
        raise ValueError(f"State Sweep did not emit state {(p, q, r, control)}")

    checks: list[dict[str, object]] = []
    failures = 0
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
