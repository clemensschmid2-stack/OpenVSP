#!/usr/bin/env python3
"""Focused tests for mandatory official-parity output contracts."""

from __future__ import annotations

import copy
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from run_parity_tests import (
    COEFFICIENTS,
    check_explicit_derivative_identities,
    check_state_sweep_output_identities,
    compare,
    compare_stability_map_to_state_sweep,
    wing_center_moment_column,
    wing_load_column,
)


SIDES = ("paritywing_ypos", "paritywing_yneg")


def valid_manifest() -> dict[str, object]:
    return {
        "control_groups": [{
            "index": 1,
            "name": "paritywing_ss_cont_0",
            "column": "paritywing_ss_cont_0_deflection_deg",
        }],
        "wing_loads": [
            {
                "name": SIDES[0], "surface": 1, "reference_point": [0.0, 0.0, 0.0],
                "planform_area": 1.0, "planform_center": [0.5, 1.0, 0.0],
                "frame": {
                    "chord": [1.0, 0.0, 0.0], "span": [0.0, 1.0, 0.0],
                    "normal": [0.0, 0.0, 1.0],
                },
            },
            {
                "name": SIDES[1], "surface": 2, "reference_point": [0.0, 0.0, 0.0],
                "planform_area": 1.0, "planform_center": [0.5, -1.0, 0.0],
                "frame": {
                    "chord": [1.0, 0.0, 0.0], "span": [0.0, -1.0, 0.0],
                    "normal": [0.0, 0.0, -1.0],
                },
            },
        ],
        "combined_wings": ["paritywing"],
        "hinge_pressure_loads": [
            {
                "index": 1, "name": "right", "column": "Cm_hinge_0_ypos",
                "wing": SIDES[0], "origin": [0.75, 1.0, 0.0],
                "direction": [1.0, 0.0, 0.0],
            },
            {
                "index": 2, "name": "left", "column": "Cm_hinge_0_yneg",
                "wing": SIDES[1], "origin": [0.75, -1.0, 0.0],
                "direction": [1.0, -0.0, 0.0],
            },
        ],
    }


def valid_state_row() -> dict[str, str]:
    row: dict[str, str] = {
        "case_id": "0", "mach": "0.15", "reynolds": "10000000",
        "vinf_m_per_s": "100", "alpha_deg": "4", "beta_deg": "0",
        "p_hat": "0", "q_hat": "0", "r_hat": "0",
        "p_rad_per_tunit": "0", "q_rad_per_tunit": "0", "r_rad_per_tunit": "0",
        "paritywing_ss_cont_0_deflection_deg": "0",
    }
    for coefficient in COEFFICIENTS:
        row[coefficient] = "0"
    row["stall_factor"] = "1"
    suffixes = (
        "CFox", "CFoy", "CFoz", "CFix", "CFiy", "CFiz", "CFx", "CFy", "CFz",
        "CMox", "CMoy", "CMoz", "CMix", "CMiy", "CMiz", "CMx", "CMy", "CMz",
        "CFiwx", "CFiwy", "CFiwz",
    )
    for wing in (*SIDES, "paritywing"):
        for suffix in suffixes:
            row[wing_load_column(wing, suffix)] = "0"
        for axis in "xyz":
            row[wing_center_moment_column(wing, axis)] = "0"
    row["Cm_hinge_0_ypos"] = "0.1"
    row["Cm_hinge_0_yneg"] = "-0.1"
    return row


def stability_and_state_rows() -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    manifest = valid_manifest()
    control_column = str(manifest["control_groups"][0]["column"])
    control_derivative = f"{manifest['control_groups'][0]['name']}_per_deg"
    cases = (
        ("base", "base", (0.0, 0.0, 0.0, 0.0)),
        ("p_rad_per_tunit", "positive", (0.01, 0.0, 0.0, 0.0)),
        ("p_rad_per_tunit", "negative", (-0.01, 0.0, 0.0, 0.0)),
        ("q_rad_per_tunit", "positive", (0.0, 0.01, 0.0, 0.0)),
        ("q_rad_per_tunit", "negative", (0.0, -0.01, 0.0, 0.0)),
        ("r_rad_per_tunit", "positive", (0.0, 0.0, 0.01, 0.0)),
        ("r_rad_per_tunit", "negative", (0.0, 0.0, -0.01, 0.0)),
        (control_derivative, "positive", (0.0, 0.0, 0.0, 0.1)),
        (control_derivative, "negative", (0.0, 0.0, 0.0, -0.1)),
    )
    state_rows: list[dict[str, str]] = []
    stability_rows: list[dict[str, str]] = []
    for index, (derivative, direction, state) in enumerate(cases):
        state_row = valid_state_row()
        state_row["case_id"] = str(index)
        for column, value in zip(
            ("p_rad_per_tunit", "q_rad_per_tunit", "r_rad_per_tunit", control_column), state,
        ):
            state_row[column] = str(value)
        state_row["CFx"] = str(index * 0.01)
        state_rows.append(state_row)
        stability_row = {
            "map_point_id": str(index), "derivative": derivative,
            "direction": direction, "coordinate": "0", **state_row,
        }
        stability_rows.append(stability_row)
    return stability_rows, state_rows


def derivative_text(nonfinite: bool = False) -> str:
    blocks = []
    for method, value in (("Forward", 2.0), ("Backward", 4.0), ("Central", 3.0)):
        lines = [
            f"# {method} finite-difference derivatives",
            "Coef Total p",
            "# - reduced_rate",
            "#",
        ]
        for coefficient in COEFFICIENTS:
            second = "nan" if nonfinite and method == "Central" and coefficient == "CFx" else str(value)
            lines.append(f"{coefficient} 0 {second}")
        lines.append("#")
        blocks.append("\n".join(lines))
    return "\n".join(blocks) + "\n"


class ParityHarnessTests(unittest.TestCase):
    def test_official_comparison_rejects_nonfinite_values(self) -> None:
        _, failures = compare({"value": 1.0}, {"value": float("nan")}, 1e-6, 1e-8)
        self.assertEqual(failures, 1)

    def test_explicit_derivative_tables_are_mandatory_and_finite(self) -> None:
        with TemporaryDirectory() as temporary:
            path = Path(temporary) / "case.stab"
            path.write_text(derivative_text(), encoding="utf-8")
            self.assertEqual(check_explicit_derivative_identities(path), [])
            path.write_text(derivative_text(nonfinite=True), encoding="utf-8")
            failures = check_explicit_derivative_identities(path)
            self.assertTrue(any(item["status"] == "non-finite derivative value" for item in failures))
            path.write_text("# no derivative tables\n", encoding="utf-8")
            self.assertTrue(check_explicit_derivative_identities(path))

    def test_state_output_contract_accepts_symmetric_finite_fixture(self) -> None:
        check, failures = check_state_sweep_output_identities(
            [valid_state_row()], valid_manifest(), 2.0, 1.0,
        )
        self.assertEqual(failures, 0, check)

    def test_state_output_contract_rejects_zero_side_geometry_and_nan(self) -> None:
        manifest = valid_manifest()
        manifest["wing_loads"][1]["planform_area"] = 0.0
        manifest["wing_loads"][1]["frame"] = {
            "chord": [0.0, 0.0, 0.0], "span": [0.0, 0.0, 0.0],
            "normal": [0.0, 0.0, 0.0],
        }
        row = valid_state_row()
        row["Cm_hinge_0_yneg"] = "nan"
        check, failures = check_state_sweep_output_identities([row], manifest, 2.0, 1.0)
        self.assertGreater(failures, 0)
        fields = {str(item["field"]) for item in check["differences"]}
        self.assertIn("manifest.paritywing_yneg.planform_area", fields)
        self.assertIn("Cm_hinge_0_yneg", fields)

    def test_stability_map_requires_negative_rate_and_control_rows(self) -> None:
        stability_rows, state_rows = stability_and_state_rows()
        check, failures = compare_stability_map_to_state_sweep(
            stability_rows, state_rows, valid_manifest(), 1e-6, 1e-8,
        )
        self.assertEqual(failures, 0, check)

        incomplete = [
            row for row in stability_rows
            if not (row["derivative"] == "q_rad_per_tunit" and row["direction"] == "negative")
        ]
        check, failures = compare_stability_map_to_state_sweep(
            incomplete, state_rows, valid_manifest(), 1e-6, 1e-8,
        )
        self.assertGreater(failures, 0)
        self.assertTrue(any(item["field"] == "q_negative" for item in check["differences"]))

    def test_stability_map_rejects_nonfinite_output(self) -> None:
        stability_rows, state_rows = stability_and_state_rows()
        corrupt = copy.deepcopy(stability_rows)
        corrupt[2]["CFx"] = "nan"
        check, failures = compare_stability_map_to_state_sweep(
            corrupt, state_rows, valid_manifest(), 1e-6, 1e-8,
        )
        self.assertGreater(failures, 0)
        self.assertTrue(any(item.get("status") == "non-finite" for item in check["differences"]))


if __name__ == "__main__":
    unittest.main()
