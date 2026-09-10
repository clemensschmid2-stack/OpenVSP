"""Compare mass, geometry and drag analyses with the fixed official distribution."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
from run_geometry_case import CASES
from run_parity_tests import DEFAULT_OFFICIAL, DEFAULT_CUSTOM, HERE, flatten, compare, python_package


def run(distribution, case, output, timeout):
    output.mkdir(parents=True)
    command = [sys.executable, str(HERE / 'run_geometry_case.py'), '--distribution', str(distribution),
               '--case', case, '--output', str(output / 'results.json')]
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(python_package(distribution)), OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1')
    with (output / 'run.log').open('w') as log:
        subprocess.run(command, cwd=output, env=env, stdout=log, stderr=subprocess.STDOUT,
                       check=True, timeout=timeout)
    return json.loads((output / 'results.json').read_text())


def compare_geometry(reference, candidate, rtol, atol):
    expected, actual = flatten(reference), flatten(candidate)
    if not expected or not actual:
        return [dict(field='results', status='empty numerical result')], 1
    differences, failures = compare(reference, candidate, rtol, atol)
    for key in sorted(actual.keys() - expected.keys()):
        differences.append(dict(field=key, status='unexpected candidate field'))
        failures += 1
    return differences, failures


def apply_shell_policy(case, differences):
    """User-approved exception for fixed 3.51.2 shell integration regressions.

    Keep strict differences visible. Both builds must reproduce reviewed values;
    changed, missing, additional, or nonfinite results remain failures. The suite
    also independently requires the candidate analytical shell check to pass.
    """
    baseline = json.loads((HERE / 'shell_inertia_exception.json').read_text())
    expected = baseline.get(case, {})
    seen, accepted = set(), 0
    for row in differences:
        field = row['field']
        if field not in expected:
            continue
        seen.add(field)
        values = expected[field]
        valid = row['status'] == 'fail' and all(
            isinstance(row.get(side), (int, float))
            and math.isfinite(row[side])
            and math.isclose(row[side], values[side], rel_tol=1e-9, abs_tol=1e-10)
            for side in ('official', 'custom'))
        if valid:
            row['status'] = 'accepted_shell_correction'
            row['policy'] = 'shell_inertia_exception.json; analytical check required'
            accepted += 1
        else:
            row['status'] = 'shell exception baseline changed'
    for field in expected.keys() - seen:
        differences.append(dict(field=field, status='missing shell exception field'))
    failures = sum(row['status'] not in ('pass', 'accepted_shell_correction') for row in differences)
    return differences, failures, accepted


def run_suite(custom, work, timeout=180, rtol=1e-6, atol=1e-8):
    work = work.resolve()
    work.mkdir(parents=True, exist_ok=False)
    report = dict(status='RUNNING', official=str(DEFAULT_OFFICIAL.resolve()), custom=str(custom.resolve()),
                  rtol=rtol, atol=atol, cases=[], failures=0, strict_failures=0,
                  accepted_shell_differences=0,
                  shell_policy_sha256=hashlib.sha256((HERE / 'shell_inertia_exception.json').read_bytes()).hexdigest())
    for label, distribution in [('official', DEFAULT_OFFICIAL), ('custom', custom)]:
        extension = python_package(distribution) / 'openvsp/_vsp.pyd'
        report[label + '_sha256'] = hashlib.sha256(extension.read_bytes()).hexdigest()
    try:
        for case in CASES:
            print(f'Geometry parity: {case}', flush=True)
            reference = run(DEFAULT_OFFICIAL.resolve(), case, work / case / 'official', timeout)
            candidate = run(custom.resolve(), case, work / case / 'custom', timeout)
            if case == 'shell_analytic':
                differences, failures = compare_geometry(candidate['expected'], candidate['actual'], rtol, atol)
                official_differences, official_failures = compare_geometry(reference['expected'], reference['actual'], rtol, atol)
                report['shell_analytical_check'] = dict(candidate_failures=failures,
                    official_failures=official_failures,
                    official_differences=[{('expected' if k == 'official' else 'actual' if k == 'custom' else k): v
                                           for k, v in d.items()}
                                          for d in official_differences if d['status'] != 'pass'])
            else:
                differences, failures = compare_geometry(reference, candidate, rtol, atol)
            report['strict_failures'] += failures
            differences, failures, accepted = apply_shell_policy(case, differences)
            report['accepted_shell_differences'] += accepted
            report['cases'].append(dict(name=case, status='FAIL' if failures else 'PASS',
                compared=len(differences), failures=failures,
                differences=[d for d in differences if d['status'] != 'pass']))
            report['failures'] += failures
            (work / 'summary.json').write_text(json.dumps(report, indent=2))
        report['status'] = 'FAIL' if report['failures'] else 'PASS'
        report['strict_status'] = 'FAIL' if report['strict_failures'] else 'PASS'
    except Exception as error:
        report.update(status='FAIL', error=str(error))
        report['failures'] += 1
        raise
    finally:
        (work / 'summary.json').write_text(json.dumps(report, indent=2))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--custom', type=Path, default=DEFAULT_CUSTOM)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--timeout', type=int, default=180)
    args = parser.parse_args()
    report = run_suite(args.custom, args.output, args.timeout)
    print(f"Overall: {report['status']} ({report['failures']} failures)")
    raise SystemExit(0 if report['status'] == 'PASS' else 1)
