"""Bounded native checks of independent warm starts and early convergence."""
import argparse
import json
from pathlib import Path
import subprocess

from run_parity_tests import DEFAULT_OFFICIAL, run_case
from run_state_sweep_regression import copy_inputs, read_rows, replace_setup_values, run_sweep
from run_state_continuation_regression import CONTINUATION_OPTIONS


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--solver', type=Path, required=True)
    parser.add_argument('--official', type=Path, default=DEFAULT_OFFICIAL)
    parser.add_argument('--baseline', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists(), 'Use a fresh isolated output directory'
    args.output.mkdir(parents=True)
    results = []
    for geometry in ('thin', 'thick'):
        source = args.output/f'source_{geometry}'
        run_case(args.official.resolve(), geometry, 'base', source, 600)
        def execute(name, options, solver=None):
            directory = args.output/geometry/name
            copy_inputs(source, directory)
            replace_setup_values(directory/'parity_wing.vspaero',
                dict(AoA='0, 1, 2', Beta='0', Mach='0.05', ReCref='1000000', WakeIters='6',
                     NonLinearConvergenceFactor='1e-12'))
            run_sweep((solver or args.solver).resolve(), directory, options, 600,
                      profile=True, fast_order=True)
            output = directory/'parity_wing.state_sweep'
            rows = read_rows(output)
            manifest = json.loads((output/'manifest.json').read_text())
            profile = json.loads((output/'profile.json').read_text())
            assert len(rows[1]) == 3
            return directory, rows, manifest, profile
        modes = {}
        tight = ['-state-continuation-min-wake-iters','6',
                 '-state-continuation-circulation-tol','1e-12',
                 '-state-continuation-wake-tol','1e-12',
                 '-state-continuation-load-tol','1e-12']
        for warm, early in ((False,False),(True,False),(False,True),(True,True)):
            name = f'warm_{int(warm)}_early_{int(early)}'
            options = (['-state-warm-start'] if warm else []) + (['-state-early-convergence',*tight] if early else [])
            directory, rows, manifest, profile = execute(name, options)
            assert manifest['continuation']['enabled'] is warm
            assert manifest['early_wake_convergence'] is early
            assert (profile['continuation_attempts'] > 0) is warm
            assert profile['total_wake_iterations'] > 0
            modes[warm,early] = (directory, rows, manifest, profile)
            results.append(dict(geometry=geometry, warm=warm, early=early, status='PASS',profile=profile))
        assert len({value[2]['configuration_hash'] for value in modes.values()}) == 4
        legacy = execute('legacy_combined', ['-state-continuation',*tight])
        assert legacy[1] == modes[True,True][1]
        assert legacy[2]['configuration_hash'] == modes[True,True][2]['configuration_hash']
        # Early-only must stop without retaining any previous case's solution.
        loose = ['-state-early-convergence','-state-continuation-min-wake-iters','2',
                 '-state-continuation-circulation-tol','1e6',
                 '-state-continuation-wake-tol','1e6',
                 '-state-continuation-load-tol','1e6']
        early = execute('early_only_stops', loose)
        assert early[3]['continuation_attempts'] == 0
        assert early[3]['total_wake_iterations'] == 6  # Three cold cases, two iterations each.
        assert early[3]['total_wake_iterations'] < modes[False,True][3]['total_wake_iterations']
        # Inactive early-convergence tolerances cannot alter warm-only identity/results.
        warm = execute('warm_only_ignores_tolerances', ['-state-warm-start',*tight])
        assert warm[1] == modes[True,False][1]
        assert warm[2]['configuration_hash'] == modes[True,False][2]['configuration_hash']
        directory = modes[True,False][0]
        checkpoint = directory/'parity_wing.state_sweep/checkpoint.txt'
        before = checkpoint.read_bytes()
        try:
            run_sweep(args.solver.resolve(), directory, ['-state-early-convergence',*tight], 600,
                      resume=True, profile=True, fast_order=True)
        except subprocess.CalledProcessError:
            pass
        else:
            raise AssertionError('Resume must reject a changed mode')
        assert checkpoint.read_bytes() == before
        if args.baseline:
            assert execute('old_cold', [], args.baseline)[1] == modes[False,False][1]
            old = execute('old_combined', ['-state-continuation',*tight], args.baseline)
            assert old[1] == legacy[1]
            assert old[2]['configuration_hash'] == legacy[2]['configuration_hash']
    (args.output/'report.json').write_text(json.dumps(dict(status='PASS',checks=results),indent=2))
    print('Independent native warm-start/early-convergence modes: PASS')


if __name__ == '__main__':
    main()
