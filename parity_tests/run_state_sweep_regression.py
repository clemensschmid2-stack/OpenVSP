#!/usr/bin/env python3
"""Compare optimized State Sweep output with a frozen stable-main VSPAERO."""

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
import time

from run_parity_tests import DEFAULT_CUSTOM, HERE, run_case


DEFAULT_BASELINE = HERE / "baselines" / "stable-main" / "vspaero.exe"
INPUT_SUFFIXES = {".vspaero", ".vspgeom", ".vsptri", ".vkey", ".csf", ".tag", ".taglist"}

SCENARIOS = {
    "operating": {
        "setup": {"Mach": "0.05, 0.15", "AoA": "-2, 4, 8", "Beta": "-5, 0, 5",
                  "ReCref": "1000000, 2000000"},
    },
    "p_physical": {"options": ["-state-p", "-0.01,0,0.01"]},
    "q_physical": {"options": ["-state-q", "-0.01,0,0.01"]},
    "r_physical": {"options": ["-state-r", "-0.01,0,0.01"]},
    "control": {"options": ["-state-control", "1", "-0.1,0,0.1"]},
    "p_reduced": {"options": ["-state-phat", "-0.01,0,0.01"]},
    "q_reduced": {"options": ["-state-qhat", "-0.01,0,0.01"]},
    "r_reduced": {"options": ["-state-rhat", "-0.01,0,0.01"]},
    "coupled": {"options": [
        "-state-p", "-0.01,0.01", "-state-q", "-0.01,0.01",
        "-state-r", "-0.01,0.01", "-state-control", "1", "-0.1,0.1",
    ]},
}


def copy_inputs(source: Path, destination: Path) -> str:
    destination.mkdir(parents=True, exist_ok=True)
    model = source / "parity_wing.vspaero"
    if not model.is_file():
        raise FileNotFoundError(f"Missing generated solver input: {model}")
    for path in source.glob("parity_wing*"):
        if path.is_file() and path.suffix.casefold() in INPUT_SUFFIXES:
            shutil.copy2(path, destination / path.name)
    return "parity_wing"


def replace_setup_values(path: Path, replacements: dict[str, str]) -> None:
    text = path.read_text(encoding="utf-8", errors="replace")
    for key, value in replacements.items():
        pattern = rf"(?m)^{re.escape(key)}\s*=.*$"
        text, count = re.subn(pattern, f"{key} = {value}", text)
        if count != 1:
            raise ValueError(f"Expected one {key} entry in {path}, found {count}")
    path.write_text(text, encoding="utf-8")


def run_sweep(
    executable: Path, directory: Path, options: list[str], timeout: int,
    *, process_cases: int = 0, resume: bool = False,
    range_start: int | None = None, range_count: int | None = None,
    output_name: str = "parity_wing.state_sweep",
) -> None:
    command = [str(executable), "-omp", "1", "-state-sweep", *options,
               "-state-chunk-size", "100", "-state-output-dir", output_name]
    if process_cases:
        command.extend(("-state-process-cases", str(process_cases)))
    if resume:
        command.append("-state-resume")
    if range_start is not None and range_count is not None:
        command.extend(("-state-range", str(range_start), str(range_count)))
    command.append("parity_wing")
    with (directory / f"{output_name.replace('/', '_')}.log").open("a", encoding="utf-8") as log:
        subprocess.run(
            command, cwd=directory, stdout=log, stderr=subprocess.STDOUT,
            check=True, timeout=timeout, env={**os.environ, "OMP_NUM_THREADS": "1"},
        )


def read_rows(directory: Path) -> tuple[list[str], dict[int, list[float]]]:
    header: list[str] | None = None
    rows: dict[int, list[float]] = {}
    for part in sorted(directory.glob("part-*.csv")):
        with part.open(newline="", encoding="utf-8") as stream:
            reader = csv.reader(stream)
            current_header = next(reader)
            if header is None:
                header = current_header
            elif current_header != header:
                raise ValueError(f"CSV header mismatch in {part}")
            for fields in reader:
                row_id = int(fields[0])
                if row_id in rows:
                    raise ValueError(f"Duplicate case_id {row_id}")
                rows[row_id] = [float(value) for value in fields[1:]]
    return header or [], rows


def compare_rows(
    expected: tuple[list[str], dict[int, list[float]]],
    actual: tuple[list[str], dict[int, list[float]]], rtol: float, atol: float,
    ignore_columns: frozenset[str] = frozenset(),
) -> dict[str, object]:
    expected_header, expected_rows = expected
    actual_header, actual_rows = actual
    failures: list[dict[str, object]] = []
    maximum_error = 0.0
    if expected_header != actual_header:
        failures.append({"kind": "header", "expected": expected_header, "actual": actual_header})
    if expected_rows.keys() != actual_rows.keys():
        failures.append({"kind": "case_ids", "expected": sorted(expected_rows),
                         "actual": sorted(actual_rows)})
    columns = expected_header[1:]
    for row_id in expected_rows.keys() & actual_rows.keys():
        for column, reference, candidate in zip(columns, expected_rows[row_id], actual_rows[row_id]):
            if column in ignore_columns:
                continue
            error = abs(candidate - reference)
            maximum_error = max(maximum_error, error)
            tolerance = atol + rtol * abs(reference)
            if not math.isfinite(error) or error > tolerance:
                if len(failures) < 100:
                    failures.append({"kind": "value", "case_id": row_id, "column": column,
                                     "baseline": reference, "candidate": candidate,
                                     "absolute_error": error, "tolerance": tolerance})
    return {"status": "PASS" if not failures else "FAIL", "rows": len(actual_rows),
            "ignored_columns": sorted(ignore_columns),
            "maximum_absolute_error": maximum_error, "failures": failures}


def checkpoint_counts(path: Path) -> tuple[int, int]:
    fields = path.read_text(encoding="ascii").split()
    if len(fields) != 3:
        raise ValueError(f"Invalid checkpoint: {path}")
    return int(fields[1]), int(fields[2])


def run_to_completion(executable: Path, directory: Path, options: list[str], timeout: int,
                      process_cases: int, output_name: str) -> None:
    resume = False
    for _launch in range(1000):
        run_sweep(executable, directory, options, timeout, process_cases=process_cases,
                  resume=resume, output_name=output_name)
        completed, total = checkpoint_counts(directory / output_name / "checkpoint.txt")
        if completed == total:
            return
        resume = True
    raise RuntimeError("Batched regression did not complete after 1000 launches")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--candidate", type=Path, default=DEFAULT_CUSTOM / "vspaero.exe")
    parser.add_argument("--custom-distribution", type=Path, default=DEFAULT_CUSTOM)
    parser.add_argument("--rtol", type=float, default=1e-6)
    parser.add_argument("--atol", type=float, default=1e-8)
    parser.add_argument("--invariance-rtol", type=float, default=1e-4)
    parser.add_argument("--invariance-atol", type=float, default=5e-4)
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--keep-work", action="store_true")
    parser.add_argument("--smoke", action="store_true", help="Run thin p/control/coupled cases only")
    args = parser.parse_args()
    baseline, candidate = args.baseline.resolve(), args.candidate.resolve()
    for executable in (baseline, candidate):
        if not executable.is_file():
            parser.error(f"VSPAERO executable not found: {executable}")
    work = HERE / "_state_sweep_regression_work"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir()
    report: dict[str, object] = {"baseline": str(baseline), "candidate": str(candidate),
                                 "rtol": args.rtol, "atol": args.atol, "cases": []}
    total_failures = 0
    modes = ("thin",) if args.smoke else ("thin", "thick")
    scenario_names = ("p_physical", "control", "coupled") if args.smoke else tuple(SCENARIOS)
    for mode in modes:
        source = work / f"source_{mode}"
        print(f"Generating deterministic {mode} solver input", flush=True)
        run_case(args.custom_distribution.resolve(), mode, "stab", source, args.timeout)
        for scenario_name in scenario_names:
            scenario = SCENARIOS[scenario_name]
            print(f"Running {mode}/{scenario_name}: stable then candidate", flush=True)
            scenario_root = work / mode / scenario_name
            outputs = []
            for label, executable in (("baseline", baseline), ("candidate", candidate)):
                directory = scenario_root / label
                copy_inputs(source, directory)
                replace_setup_values(directory / "parity_wing.vspaero", scenario.get("setup", {}))
                started = time.monotonic()
                run_sweep(executable, directory, list(scenario.get("options", [])), args.timeout)
                outputs.append(read_rows(directory / "parity_wing.state_sweep"))
                print(f"  {label}: {time.monotonic() - started:.1f}s", flush=True)
            # Stable main emitted CFy/CFz from surface-inviscid rather than
            # wake-induced components. Official parity independently verifies
            # the corrected totals; do not preserve that known baseline bug.
            comparison = compare_rows(
                outputs[0], outputs[1], args.rtol, args.atol,
                frozenset(("CFy", "CFz")),
            )
            comparison.update({"mode": mode, "scenario": scenario_name})
            report["cases"].append(comparison)
            total_failures += comparison["status"] != "PASS"

    # Candidate-only execution invariance: batching/resume and disjoint ranges
    # must reproduce its canonical coupled sweep regardless of process boundaries.
    source = work / "source_thin"
    options = list(SCENARIOS["coupled"]["options"])
    invariant = work / "execution_invariance"
    canonical_dir = invariant / "canonical"
    copy_inputs(source, canonical_dir)
    run_sweep(candidate, canonical_dir, options, args.timeout)
    canonical = read_rows(canonical_dir / "parity_wing.state_sweep")
    batched_dir = invariant / "batched"
    copy_inputs(source, batched_dir)
    run_to_completion(candidate, batched_dir, options, args.timeout, 3, "batched.state_sweep")
    batch_comparison = compare_rows(
        canonical, read_rows(batched_dir / "batched.state_sweep"),
        args.invariance_rtol, args.invariance_atol,
    )
    batch_comparison.update({"mode": "thin", "scenario": "batch_resume_invariance"})
    report["cases"].append(batch_comparison)
    total_failures += batch_comparison["status"] != "PASS"

    range_dir = invariant / "ranges"
    copy_inputs(source, range_dir)
    run_sweep(candidate, range_dir, options, args.timeout, range_start=0, range_count=8,
              output_name="range_0.state_sweep")
    run_sweep(candidate, range_dir, options, args.timeout, range_start=8, range_count=8,
              output_name="range_1.state_sweep")
    header0, rows0 = read_rows(range_dir / "range_0.state_sweep")
    header1, rows1 = read_rows(range_dir / "range_1.state_sweep")
    range_comparison = compare_rows(
        canonical, (header0, {**rows0, **rows1}),
        args.invariance_rtol, args.invariance_atol,
    )
    range_comparison.update({"mode": "thin", "scenario": "range_invariance"})
    report["cases"].append(range_comparison)
    total_failures += range_comparison["status"] != "PASS"

    report["status"] = "PASS" if total_failures == 0 else "FAIL"
    report["failed_cases"] = total_failures
    report_path = HERE / "state_sweep_regression_report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if not args.keep_work:
        shutil.rmtree(work)
    print(f"Overall: {report['status']} ({total_failures} failed scenarios)")
    print(f"Report: {report_path}")
    return 0 if total_failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
