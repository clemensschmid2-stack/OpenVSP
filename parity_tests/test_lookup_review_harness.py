"""Runner contract tests; these do not build or execute a native solver."""
import importlib.util
import json
import os
from pathlib import Path
import sys

import pytest

SPEC = importlib.util.spec_from_file_location("lookup_review_harness", Path(__file__).with_name("run_lookup_review_regression.py"))
harness = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(harness)


def write_rows(tmp_path, content, checkpoint="123 1 1"):
    directory = tmp_path / f"{harness.STEM}.state_sweep"
    directory.mkdir()
    (directory / "part-000000.csv").write_text(content)
    (directory / "checkpoint.txt").write_text(checkpoint)


def test_negative_finite_coefficient_is_not_clipped(tmp_path):
    write_rows(tmp_path, "CD,CL\n-0.1,0.3\n")
    assert harness.read_rows(tmp_path) == [{"CD": -.1, "CL": .3}]


@pytest.mark.parametrize("content", ["CD,CD\n0.1,0.1\n", "CD,CL\nnan,0.1\n", "CD,CL\n0.1,inf\n", "CD,CL\n0.1\n", "CD,CL\n"])
def test_invalid_rows_fail_closed(tmp_path, content):
    write_rows(tmp_path, content)
    with pytest.raises((AssertionError, TypeError, ValueError)):
        harness.read_rows(tmp_path)


@pytest.mark.parametrize("checkpoint", ["123 0 1", "123 1 2", "123 2 2", "123 1", "garbage"])
def test_incomplete_or_inconsistent_checkpoint_fails(tmp_path, checkpoint):
    write_rows(tmp_path, "CD\n0.1\n", checkpoint)
    with pytest.raises((AssertionError, ValueError)):
        harness.read_rows(tmp_path)


def test_setup_replacements_require_exactly_one_key(tmp_path):
    path = tmp_path / "input.vspaero"
    path.write_text("Vinf = 10\nBeta = 0\n")
    harness.replace_setup(path, {"Vinf": 5, "Beta": "-10, 10"})
    assert path.read_text() == "Vinf = 5\nBeta = -10, 10\n"
    with pytest.raises(ValueError):
        harness.replace_setup(path, {"missing": 0})
    path.write_text("Vinf = 5\nVinf = 15\n")
    with pytest.raises(ValueError):
        harness.replace_setup(path, {"Vinf": 10})


@pytest.mark.parametrize("prefix", ["", "# v2\n", "# v3\n0\n"])
def test_zero_edge_injection_uses_distinct_vertex_ids(tmp_path, prefix):
    path = tmp_path / "input.vspgeom"
    path.write_text(prefix + "3\n0 0 0\n1 0 0\n0 1 0\n1\n3 1 2 3\n")
    harness.corrupt_zero_edge(path)
    lines = path.read_text().splitlines()
    start = len(prefix.splitlines()) + 1
    assert lines[start] == lines[start+1]
    assert lines[-1] == "3 1 2 3"


def test_fixture_subprocess_receives_both_official_packages(tmp_path, monkeypatch):
    solver = tmp_path / "solver"
    solver.write_bytes(b"test placeholder, never executed")
    official = tmp_path / "official"
    seen = []

    def inspect_run(command, **kwargs):
        seen.append(kwargs["env"])
        raise RuntimeError("stop before fixture execution")

    monkeypatch.setattr(harness.subprocess, "run", inspect_run)
    with pytest.raises(RuntimeError, match="stop before fixture"):
        harness.run_regressions(solver, official, tmp_path, 1)
    assert seen[0]["PYTHONPATH"].split(os.pathsep) == [
        str(official / "python" / "openvsp"), str(official / "python" / "openvsp_config")]
    assert seen[0]["PYTHONDONTWRITEBYTECODE"] == "1"


def test_fixture_failure_emits_failed_report(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["runner", "--official", str(tmp_path),
                                    "--solver", str(tmp_path / "absent"), "--output", str(tmp_path / "out")])
    assert harness.main() == 1
    report = json.loads((tmp_path / "out" / "report.json").read_text())
    assert report["status"] == "FAIL"
    assert report["checks"] and all(check["status"] == "FAIL" for check in report["checks"])
