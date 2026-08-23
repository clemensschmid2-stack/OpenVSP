#!/usr/bin/env python3
"""Compare official and locally built OpenVSP/VSPAERO numerical results."""

from __future__ import annotations

import argparse
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
VOLATILE_FIELDS = {"Wall_Time", "WallTime"}


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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--official", type=Path, default=DEFAULT_OFFICIAL)
    parser.add_argument("--custom", type=Path, default=DEFAULT_CUSTOM)
    parser.add_argument("--rtol", type=float, default=1e-6)
    parser.add_argument("--atol", type=float, default=1e-8)
    parser.add_argument("--timeout", type=int, default=600, help="seconds allowed per run")
    parser.add_argument("--keep-work", action="store_true")
    args = parser.parse_args()

    official = args.official.resolve()
    custom = args.custom.resolve()
    for distribution in (official, custom):
        if not (distribution / "vspaero.exe").is_file():
            parser.error(f"vspaero.exe not found in {distribution}")
        python_package(distribution)

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

    for mode, analysis in CASES:
        case_name = f"{mode}_{analysis}"
        print(f"Running {case_name}: official", flush=True)
        official_result = run_case(official, mode, analysis, work / case_name / "official", args.timeout)
        print(f"Running {case_name}: custom", flush=True)
        custom_result = run_case(custom, mode, analysis, work / case_name / "custom", args.timeout)
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
