#!/usr/bin/env python3
"""Bounded native regressions for the Foil04 review fixes (no complete table).

Generate a small rectangular wing with the pinned official API, without running
its solver. Then test the candidate using isolated points and two-point batches.
This tests intended corrections; it does not replace official-reference gates.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

STEM = "lookup_review_wing"
LOADS = ("CFx", "CFy", "CFz", "CMx", "CMy", "CMz", "CL", "CD", "CS")


def generate_fixture(official: Path, directory: Path) -> None:
    dll_directory = os.add_dll_directory(str(official)) if os.name == "nt" else None
    import openvsp_config
    openvsp_config._IGNORE_IMPORTS = True
    import openvsp as vsp
    vsp.VSPRenew()
    if not vsp.SetVSPAEROPath(str(official)):
        raise RuntimeError("Official distribution lacks VSPAERO")
    wing = vsp.AddGeom("WING", "")
    vsp.SetGeomName(wing, "LookupReviewWing")
    vsp.SetDriverGroup(wing, 1, vsp.SPAN_WSECT_DRIVER, vsp.ROOTC_WSECT_DRIVER, vsp.TIPC_WSECT_DRIVER)
    for name, value in (("Span", .5), ("Root_Chord", .2), ("Tip_Chord", .2),
                        ("Sweep", 0.), ("Dihedral", 0.), ("Twist", 0.)):
        vsp.SetParmVal(wing, name, "XSec_1", value)
    vsp.SetParmVal(wing, "Tess_W", "Shape", 13)
    vsp.SetParmVal(wing, "SectTess_U", "XSec_1", 9)
    vsp.Update()
    for name, expected in (("Span", .5), ("Root_Chord", .2), ("Tip_Chord", .2)):
        assert_close(vsp.GetParmVal(wing, name, "XSec_1"), expected, f"fixture {name}")
    settings = vsp.FindContainer("VSPAEROSettings", 0)
    vsp.SetParmVal(vsp.FindParm(settings, "CpSliceFlag", "VSPAERO"), 0.)
    vsp.WriteVSPFile(str(directory / f"{STEM}.vsp3"), vsp.SET_ALL)
    for analysis in ("VSPAEROComputeGeometry", "VSPAEROSweep"):
        vsp.SetAnalysisInputDefaults(analysis)
        vsp.SetIntAnalysisInput(analysis, "GeomSet", [vsp.SET_NONE], 0)
        vsp.SetIntAnalysisInput(analysis, "ThinGeomSet", [vsp.SET_ALL], 0)
        if analysis == "VSPAEROSweep":
            for name, value in (("StopBeforeRun", 1), ("RefFlag", vsp.MANUAL_REF),
                                ("AlphaNpts", 1), ("BetaNpts", 1), ("MachNpts", 1),
                                ("WakeNumIter", 6), ("NumWakeNodes", 8), ("NCPU", 1),
                                ("UnsteadyType", vsp.STABILITY_OFF), ("StallModel", 0)):
                vsp.SetIntAnalysisInput(analysis, name, [value], 0)
            for name, value in (("Sref", .2), ("bref", 1.), ("cref", .2),
                                ("AlphaStart", 5.), ("AlphaEnd", 5.),
                                ("BetaStart", 0.), ("BetaEnd", 0.),
                                ("MachStart", .007), ("MachEnd", .007),
                                ("ReCref", 1e6), ("Vinf", 10.),
                                ("Xcg", .05), ("Ycg", 0.), ("Zcg", 0.)):
                vsp.SetDoubleAnalysisInput(analysis, name, [value], 0)
        vsp.ExecAnalysis(analysis)
        if vsp.ErrorMgrSingleton.getInstance().GetNumTotalErrors():
            raise RuntimeError(f"Official API error generating {analysis}")
    if not (directory / f"{STEM}.vspaero").is_file():
        raise RuntimeError("Official API did not write setup")
    if dll_directory:
        dll_directory.close()


def replace_setup(path: Path, values: dict[str, object]) -> None:
    content = path.read_text(encoding="utf-8")
    for name, value in values.items():
        content, count = re.subn(rf"(?m)^{re.escape(name)}\s*=.*$", f"{name} = {value}", content)
        if count != 1:
            raise ValueError(f"Expected one setup field {name}, found {count}")
    path.write_text(content, encoding="utf-8")


def read_rows(directory: Path) -> list[dict[str, float]]:
    rows = []
    for path in sorted((directory / f"{STEM}.state_sweep").glob("part-*.csv")):
        with path.open(newline="", encoding="utf-8") as stream:
            reader = csv.DictReader(stream)
            if not reader.fieldnames or len(reader.fieldnames) != len(set(reader.fieldnames)):
                raise AssertionError("Duplicate or absent native CSV header")
            for raw in reader:
                row = {name: float(value) for name, value in raw.items()}
                if not all(math.isfinite(value) for value in row.values()):
                    raise AssertionError("Nonfinite native CSV result")
                rows.append(row)
    if not rows:
        raise AssertionError("No native CSV rows")
    checkpoint = (directory / f"{STEM}.state_sweep" / "checkpoint.txt").read_text().split()
    if len(checkpoint) != 3 or int(checkpoint[1]) != len(rows) or checkpoint[1] != checkpoint[2]:
        raise AssertionError("Checkpoint does not certify all expected rows")
    return rows


def assert_close(left: float, right: float, label: str, *, rtol=1e-8, atol=1e-10) -> None:
    if not math.isclose(left, right, rel_tol=rtol, abs_tol=atol):
        raise AssertionError(f"{label}: {left:.17g} != {right:.17g}")


def corrupt_zero_edge(path: Path) -> None:
    """Make two distinct vertex IDs geometrically coincident in one polygon."""
    lines = path.read_text().splitlines()
    version = lines[0]
    count_index = 2 if "v3" in version else 1 if "v2" in version else 0
    node_count = int(lines[count_index].split()[0])
    node_start = count_index + 1
    polygon_start = node_start + node_count + 1
    fields = lines[polygon_start].split()
    first, second = int(fields[1]), int(fields[2])
    lines[node_start + second - 1] = lines[node_start + first - 1]
    path.write_text("\n".join(lines) + "\n")


def run_regressions(solver: Path, official: Path, output: Path, timeout: int) -> dict:
    report = {"status": "FAIL", "solver": str(solver),
              "solver_sha256": hashlib.sha256(solver.read_bytes()).hexdigest(), "checks": []}
    source = output / "fixture"
    source.mkdir()
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "OMP_NUM_THREADS": "1",
           "PYTHONPATH": os.pathsep.join(str(official / "python" / package)
                                        for package in ("openvsp", "openvsp_config"))}
    with (source / "geometry.log").open("w") as log:
        subprocess.run([sys.executable, str(Path(__file__).resolve()), "--generate-fixture",
                        "--official", str(official), "--output", str(source)],
                       cwd=source, env=env, stdout=log, stderr=subprocess.STDOUT,
                       check=True, timeout=timeout)

    def run(name, setup=None, options=(), *, corrupt=False, expect_failure=None):
        directory = output / name
        directory.mkdir()
        for path in source.glob(f"{STEM}.*"):
            if path.suffix in {".vspaero", ".vspgeom", ".vkey", ".vsptri", ".csf", ".tag", ".taglist"}:
                shutil.copy2(path, directory / path.name)
        replace_setup(directory / f"{STEM}.vspaero", setup or {})
        if corrupt:
            corrupt_zero_edge(directory / f"{STEM}.vspgeom")
        command = [str(solver), "-omp", "1", "-state-sweep", *options, STEM]
        with (directory / "solver.log").open("w") as log:
            completed = subprocess.run(command, cwd=directory, env=env, stdout=log,
                                       stderr=subprocess.STDOUT, timeout=timeout)
        if expect_failure is not None:
            log = (directory / "solver.log").read_text(errors="replace")
            if completed.returncode == 0 or expect_failure.casefold() not in log.casefold():
                raise AssertionError(f"{name}: expected rejection {expect_failure!r}, exit={completed.returncode}")
            checkpoint = directory / f"{STEM}.state_sweep" / "checkpoint.txt"
            if checkpoint.exists():
                fields = checkpoint.read_text().split()
                if len(fields) != 3 or int(fields[1]) != 0:
                    raise AssertionError(f"{name}: invalid case advanced checkpoint")
            return directory
        if completed.returncode:
            raise AssertionError(f"{name}: solver failed, see {directory / 'solver.log'}")
        return read_rows(directory)

    def check(name, function):
        try:
            details = function()
            report["checks"].append({"name": name, "status": "PASS", "details": details})
        except Exception as exc:
            report["checks"].append({"name": name, "status": "FAIL", "error": str(exc)})

    def reynolds():
        # Fixed wake isolates the dimensional scaling from stopping-history differences.
        low = run("fixed_re_v5", {"Vinf": 5, "WakeIters": 0})[0]
        high = run("fixed_re_v15", {"Vinf": 15, "WakeIters": 0})[0]
        for key in LOADS:
            assert_close(low[key], high[key], key)
        return {"CD_v5": low["CD"], "CD_v15": high["CD"]}

    def fast_order():
        normal = run("beta_pair", {"Beta": "-10, 10"})
        fast = run("beta_pair_fast", {"Beta": "-10, 10"}, ("-state-fast-order", "-state-profile"))
        if len(normal) != 2 or len(fast) != 2:
            raise AssertionError("Expected exactly two beta points")
        for before, after in zip(normal, fast):
            for key in LOADS:
                assert_close(before[key], after[key], key, rtol=1e-11, atol=1e-12)
        profile = json.loads((output / "beta_pair_fast" / f"{STEM}.state_sweep" / "profile.json").read_text())
        if profile["reused_invariant_setup_cases"] != 0:
            raise AssertionError("Unsafe wake-dependent setup cache still reused")
        return {"ordinary_cd": [row["CD"] for row in normal], "fast_cd": [row["CD"] for row in fast]}

    def rates():
        physical = run("pitch_physical", {"Vinf": 5}, ("-state-q", "-1.5"))[0]
        reduced = run("pitch_reduced", {"Vinf": 5}, ("-state-qhat", "-0.03"))[0]
        for key in LOADS:
            assert_close(physical[key], reduced[key], key)
        return {"CD": physical["CD"], "q": physical["q_rad_per_tunit"], "q_hat": physical["q_hat"]}

    def symmetry():
        negative = run("beta_fresh_negative", {"Beta": -10})[0]
        positive = run("beta_fresh_positive", {"Beta": 10})[0]
        for key in LOADS:
            sign = -1 if key in ("CFy", "CMx", "CMz", "CS") else 1
            assert_close(negative[key], sign * positive[key], f"fresh beta symmetry {key}",
                         rtol=1e-6, atol=1e-8)
        forward = run("beta_order_forward", {"Beta": "-10, 10"})
        reverse = run("beta_order_reverse", {"Beta": "10, -10"})
        if len(forward) != 2 or len(reverse) != 2:
            raise AssertionError("Order diagnostic requires exactly two points per batch")
        # Report finite-budget wake history, without making order-independence
        # or convergence a new acceptance rule.
        deltas = [{key: before[key] - after[key] for key in LOADS}
                  for before, after in zip(forward, reversed(reverse))]
        return {"fresh_negative": {key: negative[key] for key in LOADS},
                "fresh_positive": {key: positive[key] for key in LOADS},
                "forward_minus_reversed": deltas,
                "wake_iterations": 6, "order_diagnostic_only": True}

    def metadata():
        args = ("-state-wing-load", "1", "wing_ypos", "0", "0", "0",
                "-state-wing-load", "2", "wing_yneg", "0", "0", "0")
        run("metadata", {"WakeIters": 0}, args)
        directory = output / "metadata"
        manifest = json.loads((directory / f"{STEM}.state_sweep" / "manifest.json").read_text())
        wings = manifest["wing_loads"]
        if len(wings) != 2:
            raise AssertionError("Expected both physical wing copies")
        for wing in wings:
            for value, expected in zip(wing["frame"]["chord"], (1., 0., 0.)):
                assert_close(value, expected, "rectangular wing chord", atol=1e-7)
        with (directory / "strip-template.log").open("w") as log:
            subprocess.run([str(solver), "-omp", "1", "-stall-strip-template", "strips.csv", STEM],
                           cwd=directory, env=env, stdout=log, stderr=subprocess.STDOUT,
                           check=True, timeout=timeout)
        with (directory / "strips.csv").open(newline="") as stream:
            strips = list(csv.DictReader(stream))
        if not strips or {int(row["surface_id"]) for row in strips} != {1, 2}:
            raise AssertionError("Wake strip surface IDs do not identify both wing copies")
        for row in strips:
            assert_close(float(row["te_x"]), .2, "rectangular wing trailing edge", atol=1e-7)
            assert_close(float(row["te_z"]), 0., "rectangular wing trailing edge", atol=1e-7)
        return {"frames": [wing["frame"] for wing in wings], "strips": len(strips)}

    check("empirical_reynolds_dimensional_invariance", reynolds)
    check("fast_order_matches_ordinary_batch", fast_order)
    check("physical_reduced_pitch_equivalence", rates)
    check("fresh_beta_symmetry_and_order_diagnostics", symmetry)
    check("wake_metadata_grid_ownership", metadata)
    check("degenerate_cell_rejected_before_checkpoint", lambda: str(run("degenerate", corrupt=True,
                                                                       expect_failure="Invalid VSPGEOM")))
    check("nonfinite_result_rejected_before_checkpoint", lambda: str(run("nonfinite", {"ReCref": "nan"},
                                                                        expect_failure="Nonfinite")))
    duplicate = ("-state-wing-load", "1", "wing", "0", "0", "0",
                 "-state-wing-load", "2", "wing", "0", "0", "0")
    check("duplicate_physical_name_rejected", lambda: str(run("duplicate_names", options=duplicate,
                                                               expect_failure="Duplicate State Sweep physical wing name")))
    aggregate = ("-state-wing-load", "1", "wing_ypos", "0", "0", "0",
                 "-state-wing-load", "2", "wing_yneg", "0", "0", "0",
                 "-state-wing-load", "1", "wing", "0", "0", "0")
    check("physical_aggregate_name_collision_rejected", lambda: str(run("aggregate_collision", options=aggregate,
                                                                         expect_failure="aggregate wing name collides")))
    report["status"] = "PASS" if all(item["status"] == "PASS" for item in report["checks"]) else "FAIL"
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--solver", type=Path)
    parser.add_argument("--official", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--generate-fixture", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    output, official = args.output.resolve(), args.official.resolve()
    if args.generate_fixture:
        generate_fixture(official, output)
        return 0
    if args.solver is None:
        parser.error("--solver is required")
    output.mkdir(parents=True, exist_ok=True)
    try:
        report = run_regressions(args.solver.resolve(), official, output, args.timeout)
    except Exception as exc:
        report = {"status": "FAIL", "checks": [{"name": "fixture_or_runner", "status": "FAIL", "error": str(exc)}]}
    (output / "report.json").write_text(json.dumps(report, indent=2, allow_nan=False), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
