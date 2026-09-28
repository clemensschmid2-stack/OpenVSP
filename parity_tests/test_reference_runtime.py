"""Reference migration must not permit a silent solver or Python fallback."""
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import os
import unittest
from unittest.mock import patch

from run_case import select_solver_directory
from run_parity_tests import python_path
import run_geometry_parity as geometry


class ReferenceRuntimeTests(unittest.TestCase):
    def test_active_reference_does_not_apply_historical_shell_exception(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'openvsp').mkdir()
            (root / 'openvsp/_vsp.pyd').write_bytes(b'test-only identity')
            differences = [dict(field='inertia', status='fail', official=1., custom=2.)]
            with patch.object(geometry, 'CASES', ['mass_shell']), \
                 patch.object(geometry, 'python_package', return_value=root), \
                 patch.object(geometry, 'run', return_value={}), \
                 patch.object(geometry, 'compare_geometry', return_value=(differences, 1)), \
                 patch.object(geometry, 'apply_shell_policy', side_effect=AssertionError('legacy waiver used')):
                report = geometry.run_suite(root, root / 'results')
            self.assertEqual(report['status'], 'FAIL')
            self.assertEqual(report['failures'], 1)
            self.assertEqual(report['accepted_shell_differences'], 0)

    def test_rejected_solver_directory_fails(self):
        vsp = SimpleNamespace(SetVSPAEROPath=lambda path: None,
                              GetVSPAEROPath=lambda: str(Path('old-runtime').resolve()))
        with self.assertRaisesRegex(RuntimeError, 'rejected solver directory'):
            select_solver_directory(vsp, Path('candidate'))

    def test_accepted_solver_directory(self):
        selected = []
        vsp = SimpleNamespace(SetVSPAEROPath=selected.append,
                              GetVSPAEROPath=lambda: selected[-1])
        select_solver_directory(vsp, Path('candidate'))
        self.assertEqual(selected, [str(Path('candidate').resolve())])

    def test_support_packages_come_from_selected_distribution(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ('openvsp', 'degen_geom', 'utilities'):
                (root / 'python' / name).mkdir(parents=True)
            paths = python_path(root).split(os.pathsep)
            self.assertEqual(paths[0], str(root / 'python/openvsp'))
            self.assertEqual(set(paths), {str(root / 'python' / name)
                                         for name in ('openvsp', 'degen_geom', 'utilities')})
