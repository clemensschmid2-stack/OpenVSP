"""Geometry parity must not accept empty or incomplete API results."""
import unittest
import json
from run_geometry_parity import compare_geometry, apply_shell_policy, HERE


class GeometryParityTests(unittest.TestCase):
    def test_only_exact_reviewed_shell_differences_are_accepted(self):
        baseline = json.loads((HERE / 'shell_inertia_exception.json').read_text())
        self.assertEqual(sum(map(len, baseline.values())), 30)
        for case, fields in baseline.items():
            rows = [dict(field=key, status='fail', **values) for key, values in fields.items()]
            self.assertEqual(apply_shell_policy(case, rows)[1:], (0, len(fields)))
            rows[0]['custom'] *= 1.0001
            self.assertGreater(apply_shell_policy(case, rows)[1], 0)

    def test_missing_or_extra_shell_fields_fail(self):
        baseline = json.loads((HERE / 'shell_inertia_exception.json').read_text())['mass_shell']
        rows = [dict(field=key, status='fail', **values) for key, values in baseline.items()]
        rows.pop()
        rows.append(dict(field='unexpected.inertia', status='fail', official=1, custom=2))
        self.assertEqual(apply_shell_policy('mass_shell', rows)[1], 2)

    def test_empty_results_fail(self):
        self.assertEqual(compare_geometry({}, {}, 1e-6, 1e-8)[1], 1)

    def test_missing_and_extra_results_fail(self):
        reference = {'mass': [5.], 'cg': [1., 2., 3.]}
        self.assertGreater(compare_geometry(reference, {'mass': [5.]}, 1e-6, 1e-8)[1], 0)
        self.assertGreater(compare_geometry(reference, dict(reference, extra=[1]), 1e-6, 1e-8)[1], 0)

    def test_nonfinite_and_changed_inertia_fail(self):
        for inertia in (float('nan'), float('inf'), 1.1):
            self.assertGreater(compare_geometry({'Ixx': [1.]}, {'Ixx': [inertia]}, 1e-6, 1e-8)[1], 0)

    def test_duration_is_ignored(self):
        self.assertEqual(compare_geometry({'mass': [1.], 'Wall_Time': 1},
                                         {'mass': [1.], 'Wall_Time': 9}, 1e-6, 1e-8)[1], 0)
