"""Build pinned VSPAERO and execute bounded native regressions on hosted runners.

This is not a full OpenVSP geometry build or the official-reference parity gate.
No generated candidate can replace a fixed reference distribution.
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
OPENVSP = ROOT
BUILD = ROOT / 'build/ci-vspaero'
REPORTS = ROOT / 'build/ci/vspaero'
sys.path.insert(0, str(Path(__file__).resolve().parent))
from reference_manifest import verify_openvsp  # noqa: E402
import xml.etree.ElementTree as ET

def check_junit(path, allowed_skips=frozenset()):
    cases = list(ET.parse(path).getroot().iter('testcase'))
    if not cases:
        raise ValueError(f'No tests executed in {path}')
    skipped = []
    passed = 0
    for case in cases:
        name = case.get('classname', '').rsplit('.', 1)[-1]+'::'+case.get('name', '').split('[')[0]
        if case.find('failure') is not None or case.find('error') is not None:
            raise ValueError(f'Test failed: {name}')
        if case.find('skipped') is not None:
            if name not in allowed_skips:
                raise ValueError(f'Unexpected skipped test: {name}')
            skipped.append(name)
        else:
            passed += 1
    if not passed:
        raise ValueError(f'No passing tests in {path}')
    return dict(passed=passed, deferred_native_tests=skipped)



REQUIRED_LOOKUP_CHECKS = frozenset({
    'empirical_reynolds_dimensional_invariance',
    'fast_order_matches_ordinary_batch',
    'physical_reduced_pitch_equivalence',
    'fresh_beta_symmetry_and_order_diagnostics',
    'wake_metadata_grid_ownership',
    'degenerate_cell_rejected_before_checkpoint',
    'nonfinite_result_rejected_before_checkpoint',
    'duplicate_physical_name_rejected',
    'physical_aggregate_name_collision_rejected',
})


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def git(path, *args):
    return subprocess.check_output(['git', *args], cwd=path, text=True).strip()


def verify_source_pin():
    actual = git(OPENVSP, 'rev-parse', 'HEAD')
    if git(OPENVSP, 'status', '--porcelain', '--untracked-files=no'):
        raise ValueError('OpenVSP tracked sources are modified')
    return actual


def read_executables(build):
    paths = (build / 'executables-Release.txt').read_text(encoding='utf-8').splitlines()
    if len(paths) != 2:
        raise ValueError('CMake executable manifest must contain solver and checkpoint probe')
    solver, probe = (Path(value).resolve() for value in paths)
    for path in (solver, probe):
        if not path.is_relative_to(build.resolve()) or not path.is_file():
            raise ValueError(f'Missing or out-of-build executable: {path}')
    return solver, probe


def require_regression_pass(path):
    result = json.loads(path.read_text(encoding='utf-8'))
    checks = result.get('checks') if isinstance(result, dict) else None
    if (not isinstance(result, dict) or result.get('status') != 'PASS'
            or not isinstance(checks, list) or not checks
            or any(not isinstance(check, dict) or check.get('status') != 'PASS'
                   for check in checks)):
        raise ValueError(f'Lookup-review numerical regressions did not pass: {path}')
    names = [check.get('name') for check in checks]
    if (any(not isinstance(name, str) for name in names)
            or len(set(names)) != len(names) or set(names) != REQUIRED_LOOKUP_CHECKS):
        raise ValueError(f'Lookup-review regression names are incomplete, duplicate or unexpected: {path}')
    return result


def run(report, name, command, *, env=None, timeout=1200):
    command = [str(value) for value in command]
    log_path = REPORTS / (name + '.log')
    record = dict(command=command, log=str(log_path), passed=False)
    report['checks'][name] = record
    started = time.monotonic()
    print(subprocess.list2cmdline(command), flush=True)
    try:
        with log_path.open('w', encoding='utf-8') as log:
            subprocess.run(command, cwd=ROOT, env=env, stdout=log,
                           stderr=subprocess.STDOUT, check=True, timeout=timeout)
        record['passed'] = True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        print(log_path.read_text(encoding='utf-8', errors='replace')[-24000:], flush=True)
        raise
    finally:
        record['duration_seconds'] = time.monotonic() - started


def main():
    import argparse
    global BUILD, REPORTS
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-dir', type=Path, default=BUILD)
    parser.add_argument('--reports', type=Path, default=REPORTS)
    args = parser.parse_args()
    BUILD, REPORTS = args.build_dir.resolve(), args.reports.resolve()
    if (REPORTS / 'report.json').exists():
        raise ValueError(f'Preserve the previous evidence and use a fresh checkout/output: {REPORTS}')
    REPORTS.mkdir(parents=True, exist_ok=True)
    report = dict(format='vds-hosted-vspaero-v1', revision=git(ROOT, 'rev-parse', 'HEAD'),
                  platform=platform.platform(), python=sys.version, checks={}, passed=False,
                  coverage='candidate solver build and focused regressions; not full official parity')
    try:
        report['openvsp_revision'] = verify_source_pin()
        report['solver_source_url'] = ('https://github.com/clemensschmid2-stack/OpenVSP/tree/'
                                       + report['openvsp_revision'])
        report['dependencies'] = {name: importlib.metadata.version(name)
                                  for name in ('pytest', 'numpy', 'matplotlib')}
        if sys.platform == 'win32':
            verify_openvsp()
            report['official_manifest_sha256'] = digest(
                ROOT / 'reference_builds/openvsp-3.52.2-manifest.json')
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='1',
                   MPLBACKEND='Agg', PYTHONPATH=str(ROOT / 'parity_tests'))
        run(report, 'harness-tests', [sys.executable, '-m', 'pytest', '-q',
            OPENVSP / 'parity_tests/test_lookup_review_harness.py',
            OPENVSP / 'parity_tests/test_native_checks.py',
            OPENVSP / 'parity_tests/test_reference_manifest.py',
            f'--junitxml={REPORTS / "harness-tests.xml"}'], env=env)
        report['checks']['harness-tests']['results'] = check_junit(REPORTS / 'harness-tests.xml')
        run(report, 'configure', ['cmake', '-S', ROOT / 'parity_tests/native', '-B', BUILD,
                                 '-DCMAKE_BUILD_TYPE=Release'], env=env)
        run(report, 'build', ['cmake', '--build', BUILD, '--config', 'Release',
                             '--parallel', '2'], env=env)
        solver, probe = read_executables(BUILD)
        report['solver_sha256'] = digest(solver)
        report['checkpoint_probe_sha256'] = digest(probe)
        run(report, 'ctest', ['ctest', '--test-dir', BUILD, '-C', 'Release',
                             '--output-on-failure', '--no-tests=error',
                             '--output-junit', REPORTS / 'ctest.xml'], env=env)
        report['checks']['ctest']['results'] = check_junit(REPORTS / 'ctest.xml')
        if sys.platform == 'win32':
            numerical = REPORTS / 'lookup-review'
            if numerical.exists():
                raise ValueError(f'Numerical output must be fresh: {numerical}')
            run(report, 'lookup-review', [sys.executable,
                OPENVSP / 'parity_tests/run_lookup_review_regression.py',
                '--solver', solver,
                '--official', OPENVSP / 'reference_builds/OpenVSP-3.52.2-win64',
                '--output', numerical], env=env, timeout=1800)
            report['checks']['lookup-review']['results'] = require_regression_pass(numerical / 'report.json')
            # Importing the geometry API must not modify the fixed distribution.
            verify_openvsp()
        run(report, 'install-artifact', ['cmake', '--install', BUILD, '--config', 'Release',
                                        '--prefix', BUILD / 'install'], env=env)
        installed = BUILD / 'install' / solver.name
        if digest(installed) != report['solver_sha256']:
            raise ValueError('Packaged solver differs from tested solver')
        report['artifacts'] = {p.relative_to(BUILD / 'install').as_posix(): digest(p)
                               for p in sorted((BUILD / 'install').rglob('*')) if p.is_file()}
        report['passed'] = True
    except Exception as exc:
        report['error'] = f'{type(exc).__name__}: {exc}'
        raise
    finally:
        (REPORTS / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
