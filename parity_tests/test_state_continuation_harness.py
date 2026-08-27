#!/usr/bin/env python3
"""Unit tests for continuation regression infrastructure."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from run_state_continuation_regression import test_matrix, validate_profile


class ContinuationHarnessTests(unittest.TestCase):
    def test_matrix_contains_every_mandatory_safety_dimension(self) -> None:
        names = {str(case["name"]) for case in test_matrix()}
        self.assertEqual(
            names,
            {
                "cold_vs_forward", "reverse_traversal", "repeat_determinism",
                "batch_resume", "ranged_workers", "forced_interruption_resume",
                "difficult_states", "warm_start_fallback", "wing_and_hinge_loads",
                "continuation_profile_schema",
            },
        )
        self.assertTrue(all(bool(case["mandatory"]) for case in test_matrix()))

    def test_valid_profile_passes(self) -> None:
        with TemporaryDirectory() as temporary:
            path = Path(temporary) / "profile.json"
            path.write_text(json.dumps({
                "aerodynamic_cases": 4,
                "continuation_attempts": 3,
                "continuation_accepted": 2,
                "continuation_cold_starts": 2,
                "continuation_fallbacks": 1,
                "total_wake_iterations": 20,
            }), encoding="utf-8")
            self.assertEqual(validate_profile(path)["status"], "PASS")

    def test_profile_rejects_bad_accounting_and_iteration_limits(self) -> None:
        with TemporaryDirectory() as temporary:
            path = Path(temporary) / "profile.json"
            path.write_text(json.dumps({
                "aerodynamic_cases": 4,
                "continuation_attempts": 1,
                "continuation_accepted": 1,
                "continuation_cold_starts": 1,
                "continuation_fallbacks": 1,
                "total_wake_iterations": 3,
            }), encoding="utf-8")
            result = validate_profile(path)
            self.assertEqual(result["status"], "FAIL")
            kinds = {failure["kind"] for failure in result["failures"]}
            self.assertIn("invalid_attempt_accounting", kinds)
            self.assertIn("wake_iteration_bounds", kinds)


if __name__ == "__main__":
    unittest.main()
