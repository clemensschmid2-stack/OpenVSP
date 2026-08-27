#!/usr/bin/env python3
"""Validate experimental State Sweep continuation against cold solutions."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

from run_parity_tests import DEFAULT_CUSTOM, HERE, run_case
from run_state_sweep_regression import (
    checkpoint_counts,
    compare_rows,
    copy_inputs,
    read_rows,
    rekey_by_state,
    replace_setup_values,
    run_sweep,
    run_to_completion,
)


CONTINUATION_OPTIONS = [
    "-state-continuation",
    "-state-continuation-min-wake-iters", "2",
    "-state-continuation-circulation-tol", "1e-5",
    "-state-continuation-wake-tol", "1e-4",
    "-state-continuation-load-tol", "1e-5",
]
BASE_AXES = [
    "-state-p", "-0.01,0.01",
    "-state-q", "-0.01,0.01",
    "-state-r", "-0.01,0.01",
    "-state-control", "1", "-0.1,0.1",
]
REVERSE_AXES = [
    "-state-p", "0.01,-0.01",
    "-state-q", "0.01,-0.01",
    "-state-r", "0.01,-0.01",
    "-state-control", "1", "0.1,-0.1",
]
DIFFICULT_AXES = [
    "-state-p", "-0.05,0.05",
    "-state-q", "-0.04,0.04",
    "-state-r", "-0.05,0.05",
    "-state-control", "1", "-10,10",
]
PROFILE_COUNTERS = {
    "continuation_attempts",
    "continuation_accepted",
    "continuation_cold_starts",
    "continuation_fallbacks",
    "total_wake_iterations",
}
CONTINUATION_FLAGS = {
    "-state-continuation",
    "-state-continuation-min-wake-iters",
    "-state-continuation-circulation-tol",
    "-state-continuation-wake-tol",
    "-state-continuation-load-tol",
}


def test_matrix() -> list[dict[str, object]]:
    return [
        {"name": "cold_vs_forward", "modes": ["thin", "thick"], "mandatory": True},
        {"name": "reverse_traversal", "modes": ["thin", "thick"], "mandatory": True},
        {"name": "repeat_determinism", "repetitions": 2, "mandatory": True},
        {"name": "batch_resume", "process_cases": 3, "mandatory": True},
        {"name": "ranged_workers", "ranges": [[0, 8], [8, 8]], "mandatory": True},
        {"name": "forced_interruption_resume", "mandatory": True},
        {"name": "difficult_states", "modes": ["thin", "thick"], "mandatory": True},
        {"name": "warm_start_fallback", "mandatory": True},
        {"name": "wing_and_hinge_loads", "mandatory": True},
        {"name": "continuation_profile_schema", "fields": sorted(PROFILE_COUNTERS),
         "mandatory": True},
    ]


def advertised_options(executable: Path) -> str:
    completed = subprocess.run(
        [str(executable)], text=True, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, timeout=30, check=False,
    )
    return completed.stdout


def comparison(
    reference: tuple[list[str], dict[int, list[float]]],
    candidate: tuple[list[str], dict[int, list[float]]],
    name: str, mode: str, rtol: float, atol: float,
) -> dict[str, object]:
    result = compare_rows(
        rekey_by_state(reference), rekey_by_state(candidate), rtol, atol,
    )
    result.update({"scenario": name, "mode": mode})
    return result


def validate_profile(path: Path) -> dict[str, object]:
    failures: list[dict[str, object]] = []
    try:
        profile = json.loads(path.read_text(encoding="utf-8"))
        missing = sorted(PROFILE_COUNTERS - profile.keys())
        if missing:
            failures.append({"kind": "missing_profile_counters", "fields": missing})
        for field in PROFILE_COUNTERS & profile.keys():
            value = int(profile[field])
            if value < 0:
                failures.append({"kind": "negative_profile_counter", "field": field})
        attempts = int(profile.get("continuation_attempts", 0))
        accepted = int(profile.get("continuation_accepted", 0))
        fallbacks = int(profile.get("continuation_fallbacks", 0))
        if accepted + fallbacks > attempts:
            failures.append({"kind": "invalid_attempt_accounting"})
        cases = int(profile.get("aerodynamic_cases", 0))
        iterations = int(profile.get("total_wake_iterations", 0))
        if cases > 0 and not 2 * cases <= iterations <= 12 * cases:
            failures.append({"kind": "wake_iteration_bounds", "cases": cases,
                             "iterations": iterations, "minimum": 2 * cases,
                             "maximum": 12 * cases})
    except (OSError, ValueError, TypeError) as exc:
        failures.append({"kind": "invalid_profile", "error": str(exc)})
    return {"scenario": "continuation_profile_schema", "mode": "thin",
            "status": "PASS" if not failures else "FAIL", "failures": failures}


def run_continuation(
    executable: Path, directory: Path, axes: list[str], timeout: int,
    *, output_name: str, profile: bool = True,
) -> tuple[list[str], dict[int, list[float]]]:
    run_sweep(
        executable, directory, [*axes, *CONTINUATION_OPTIONS], timeout,
        output_name=output_name, profile=profile, fast_order=True,
    )
    return read_rows(directory / output_name)


def start_and_interrupt(
    executable: Path, directory: Path, axes: list[str], timeout: int,
    output_name: str,
) -> bool:
    command = [
        str(executable), "-omp", "1", "-state-sweep", *axes,
        *CONTINUATION_OPTIONS, "-state-fast-order", "-state-profile",
        "-state-chunk-size", "100", "-state-output-dir", output_name,
        "parity_wing",
    ]
    log_path = directory / "forced_interruption.log"
    with log_path.open("w", encoding="utf-8") as log:
        process = subprocess.Popen(
            command, cwd=directory, stdout=log, stderr=subprocess.STDOUT,
            env={**os.environ, "OMP_NUM_THREADS": "1"},
        )
        deadline = time.monotonic() + min(timeout, 60)
        checkpoint = directory / output_name / "checkpoint.txt"
        interrupted = False
        while process.poll() is None and time.monotonic() < deadline:
            if checkpoint.is_file():
                try:
                    completed, total = checkpoint_counts(checkpoint)
                    if 0 < completed < total:
                        process.terminate()
                        interrupted = True
                        break
                except (OSError, ValueError):
                    pass
            time.sleep(0.02)
        if process.poll() is None:
            process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=10)
    return interrupted


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, default=DEFAULT_CUSTOM / "vspaero.exe")
    parser.add_argument("--custom-distribution", type=Path, default=DEFAULT_CUSTOM)
    parser.add_argument("--rtol", type=float, default=1e-4)
    parser.add_argument("--atol", type=float, default=5e-4)
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--plan-only", action="store_true")
    parser.add_argument("--require-feature", action="store_true")
    parser.add_argument("--keep-work", action="store_true")
    args = parser.parse_args()

    candidate = args.candidate.resolve()
    plan = {
        "format": "vspaero-state-continuation-test-plan",
        "candidate": str(candidate),
        "continuation_options": CONTINUATION_OPTIONS,
        "rtol": args.rtol,
        "atol": args.atol,
        "tests": test_matrix(),
    }
    plan_path = HERE / "state_continuation_test_plan.json"
    plan_path.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    if args.plan_only:
        print(f"Continuation test plan: {plan_path}")
        return 0
    if not candidate.is_file():
        parser.error(f"Candidate VSPAERO does not exist: {candidate}")

    help_text = advertised_options(candidate)
    missing_options = sorted(option for option in CONTINUATION_FLAGS
                             if option not in help_text)
    if missing_options:
        message = f"Candidate does not advertise continuation options: {', '.join(missing_options)}"
        if args.require_feature:
            print(message, file=os.sys.stderr)
            return 2
        print(f"SKIP: {message}")
        return 0

    work = HERE / "_state_continuation_work"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir()
    report: dict[str, object] = {
        "format": "vspaero-state-continuation-regression",
        "candidate": str(candidate), "rtol": args.rtol, "atol": args.atol,
        "cases": [],
    }
    failures = 0

    references: dict[str, tuple[list[str], dict[int, list[float]]]] = {}
    sources: dict[str, Path] = {}
    for mode in ("thin", "thick"):
        source = work / f"source_{mode}"
        run_case(args.custom_distribution.resolve(), mode, "stab", source, args.timeout)
        sources[mode] = source
        mode_root = work / mode
        cold_dir = mode_root / "cold"
        copy_inputs(source, cold_dir)
        replace_setup_values(cold_dir / "parity_wing.vspaero", {"WakeIters": "12"})
        run_sweep(candidate, cold_dir, BASE_AXES, args.timeout,
                  output_name="cold.state_sweep", profile=True, fast_order=True)
        cold = read_rows(cold_dir / "cold.state_sweep")
        references[mode] = cold

        forward_dir = mode_root / "forward"
        copy_inputs(source, forward_dir)
        replace_setup_values(forward_dir / "parity_wing.vspaero", {"WakeIters": "12"})
        forward = run_continuation(candidate, forward_dir, BASE_AXES, args.timeout,
                                   output_name="forward.state_sweep")
        result = comparison(cold, forward, "cold_vs_forward", mode, args.rtol, args.atol)
        report["cases"].append(result); failures += result["status"] != "PASS"

        reverse_dir = mode_root / "reverse"
        copy_inputs(source, reverse_dir)
        replace_setup_values(reverse_dir / "parity_wing.vspaero", {"WakeIters": "12"})
        reverse = run_continuation(candidate, reverse_dir, REVERSE_AXES, args.timeout,
                                   output_name="reverse.state_sweep")
        result = comparison(cold, reverse, "reverse_traversal", mode, args.rtol, args.atol)
        report["cases"].append(result); failures += result["status"] != "PASS"

        difficult_cold_dir = mode_root / "difficult_cold"
        copy_inputs(source, difficult_cold_dir)
        replace_setup_values(
            difficult_cold_dir / "parity_wing.vspaero",
            {"WakeIters": "12", "AoA": "-8, 12", "Beta": "-10, 10"},
        )
        run_sweep(candidate, difficult_cold_dir, DIFFICULT_AXES, args.timeout,
                  output_name="difficult_cold.state_sweep", fast_order=True)
        difficult_cold = read_rows(difficult_cold_dir / "difficult_cold.state_sweep")
        difficult_warm_dir = mode_root / "difficult_warm"
        copy_inputs(source, difficult_warm_dir)
        replace_setup_values(
            difficult_warm_dir / "parity_wing.vspaero",
            {"WakeIters": "12", "AoA": "-8, 12", "Beta": "-10, 10"},
        )
        difficult_warm = run_continuation(
            candidate, difficult_warm_dir, DIFFICULT_AXES, args.timeout,
            output_name="difficult_warm.state_sweep",
        )
        result = comparison(difficult_cold, difficult_warm, "difficult_states", mode,
                            args.rtol, args.atol)
        report["cases"].append(result); failures += result["status"] != "PASS"

    # Repeat determinism and optional physical-side loads on thin geometry.
    repeat_dir = work / "repeat"
    copy_inputs(sources["thin"], repeat_dir)
    replace_setup_values(repeat_dir / "parity_wing.vspaero", {"WakeIters": "12"})
    repeated = run_continuation(candidate, repeat_dir, BASE_AXES, args.timeout,
                                output_name="repeat.state_sweep")
    result = comparison(references["thin"], repeated, "repeat_determinism", "thin",
                        args.rtol, args.atol)
    report["cases"].append(result); failures += result["status"] != "PASS"

    # Two independent ranges must merge to the same set of physical states.
    ranges_dir = work / "ranges"
    copy_inputs(sources["thin"], ranges_dir)
    replace_setup_values(ranges_dir / "parity_wing.vspaero", {"WakeIters": "12"})
    ranged_options = [*BASE_AXES, "-state-fast-order", *CONTINUATION_OPTIONS]
    run_sweep(candidate, ranges_dir, ranged_options, args.timeout,
              range_start=0, range_count=8, output_name="range_0.state_sweep")
    run_sweep(candidate, ranges_dir, ranged_options, args.timeout,
              range_start=8, range_count=8, output_name="range_1.state_sweep")
    header0, rows0 = read_rows(ranges_dir / "range_0.state_sweep")
    header1, rows1 = read_rows(ranges_dir / "range_1.state_sweep")
    if header0 != header1:
        ranged = {"scenario": "ranged_workers", "mode": "thin", "status": "FAIL",
                  "failures": [{"kind": "range_header_mismatch"}]}
    else:
        ranged = comparison(references["thin"], (header0, {**rows0, **rows1}),
                            "ranged_workers", "thin", args.rtol, args.atol)
    report["cases"].append(ranged); failures += ranged["status"] != "PASS"

    # Canonical ordering changes control geometry every adjacent case. A warm
    # state must be rejected or cold-fallback rather than crossing that boundary.
    fallback_dir = work / "fallback"
    copy_inputs(sources["thin"], fallback_dir)
    replace_setup_values(fallback_dir / "parity_wing.vspaero", {"WakeIters": "12"})
    fallback_axes = ["-state-p", "-0.01,0.01", "-state-control", "1", "-10,10"]
    fallback_cold_dir = work / "fallback_cold"
    copy_inputs(sources["thin"], fallback_cold_dir)
    replace_setup_values(fallback_cold_dir / "parity_wing.vspaero", {"WakeIters": "12"})
    run_sweep(candidate, fallback_cold_dir, fallback_axes, args.timeout,
              output_name="fallback_cold.state_sweep")
    fallback_cold = read_rows(fallback_cold_dir / "fallback_cold.state_sweep")
    run_sweep(candidate, fallback_dir, [*fallback_axes, *CONTINUATION_OPTIONS],
              args.timeout, output_name="fallback.state_sweep", profile=True)
    fallback_warm = read_rows(fallback_dir / "fallback.state_sweep")
    fallback_profile = json.loads(
        (fallback_dir / "fallback.state_sweep" / "profile.json").read_text(encoding="utf-8")
    )
    fallback_events = int(fallback_profile.get("continuation_fallbacks", 0))
    cold_starts = int(fallback_profile.get("continuation_cold_starts", 0))
    fallback_failures = []
    fallback_comparison = comparison(fallback_cold, fallback_warm, "warm_start_fallback",
                                     "thin", args.rtol, args.atol)
    fallback_failures.extend(fallback_comparison.get("failures", []))
    if fallback_events == 0 and cold_starts <= 1:
        fallback_failures.append({"kind": "incompatible_predecessor_not_rejected"})
    fallback_result = {"scenario": "warm_start_fallback", "mode": "thin",
                       "status": "PASS" if not fallback_failures else "FAIL",
                       "fallbacks": fallback_events, "cold_starts": cold_starts,
                       "failures": fallback_failures}
    report["cases"].append(fallback_result)
    failures += fallback_result["status"] != "PASS"

    loads_dir = work / "optional_loads"
    copy_inputs(sources["thin"], loads_dir)
    replace_setup_values(loads_dir / "parity_wing.vspaero", {"WakeIters": "12"})
    load_options = [*BASE_AXES, "-state-wing-load", "1", "wing_1", "0", "0", "0",
                    "-state-hinge-loads"]
    run_sweep(candidate, loads_dir, load_options, args.timeout,
              output_name="loads_cold.state_sweep", fast_order=True)
    cold_loads = read_rows(loads_dir / "loads_cold.state_sweep")
    loads_warm_dir = work / "optional_loads_warm"
    copy_inputs(sources["thin"], loads_warm_dir)
    replace_setup_values(loads_warm_dir / "parity_wing.vspaero", {"WakeIters": "12"})
    warm_loads = run_continuation(candidate, loads_warm_dir, load_options, args.timeout,
                                  output_name="loads_warm.state_sweep")
    result = comparison(cold_loads, warm_loads, "wing_and_hinge_loads", "thin",
                        args.rtol, args.atol)
    report["cases"].append(result); failures += result["status"] != "PASS"

    # Frequent process boundaries exercise cold recovery on resume.
    batch_dir = work / "batch_resume"
    copy_inputs(sources["thin"], batch_dir)
    replace_setup_values(batch_dir / "parity_wing.vspaero", {"WakeIters": "12"})
    run_to_completion(candidate, batch_dir,
                      [*BASE_AXES, "-state-fast-order", *CONTINUATION_OPTIONS],
                      args.timeout, 3, "batch.state_sweep")
    result = comparison(references["thin"], read_rows(batch_dir / "batch.state_sweep"),
                        "batch_resume", "thin", args.rtol, args.atol)
    report["cases"].append(result); failures += result["status"] != "PASS"

    # Forced termination after a published row, followed by ordinary resume.
    interrupted_dir = work / "forced_interruption"
    copy_inputs(sources["thin"], interrupted_dir)
    replace_setup_values(interrupted_dir / "parity_wing.vspaero", {"WakeIters": "12"})
    did_interrupt = start_and_interrupt(candidate, interrupted_dir, BASE_AXES,
                                        args.timeout, "interrupted.state_sweep")
    interruption_failures: list[dict[str, object]] = []
    if not did_interrupt:
        interruption_failures.append({"kind": "could_not_inject_interruption"})
    else:
        for _launch in range(1000):
            run_sweep(
                candidate, interrupted_dir,
                [*BASE_AXES, "-state-fast-order", *CONTINUATION_OPTIONS],
                args.timeout, process_cases=3, resume=True,
                output_name="interrupted.state_sweep",
            )
            completed, total = checkpoint_counts(
                interrupted_dir / "interrupted.state_sweep" / "checkpoint.txt"
            )
            if completed == total:
                break
        else:
            interruption_failures.append({"kind": "resume_launch_limit"})
        result = comparison(
            references["thin"], read_rows(interrupted_dir / "interrupted.state_sweep"),
            "forced_interruption_resume", "thin", args.rtol, args.atol,
        )
        interruption_failures.extend(result.get("failures", []))
    interruption = {"scenario": "forced_interruption_resume", "mode": "thin",
                    "status": "PASS" if not interruption_failures else "FAIL",
                    "failures": interruption_failures}
    report["cases"].append(interruption); failures += interruption["status"] != "PASS"

    profile_result = validate_profile(
        work / "thin" / "forward" / "forward.state_sweep" / "profile.json"
    )
    report["cases"].append(profile_result); failures += profile_result["status"] != "PASS"

    report["status"] = "PASS" if failures == 0 else "FAIL"
    report["failed_cases"] = failures
    report_path = HERE / "state_continuation_regression_report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if not args.keep_work:
        shutil.rmtree(work)
    print(f"Overall: {report['status']} ({failures} failed scenarios)")
    print(f"Report: {report_path}")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
