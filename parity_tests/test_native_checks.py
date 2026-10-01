import importlib.util
from pathlib import Path
import pytest

def load(_name):
    spec = importlib.util.spec_from_file_location('native_checks', Path(__file__).with_name('run_native_checks.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

@pytest.mark.parametrize('result', [
    {}, {'status': 'PASS'}, {'status': 'PASS', 'checks': []},
    {'status': 'PASS', 'checks': [{'status': 'FAIL'}]},
    {'status': 'FAIL', 'checks': [{'status': 'PASS'}]},
    {'status': 'PASS', 'checks': ['PASS']},
])
def test_vspaero_gate_rejects_empty_or_incomplete_numerical_evidence(tmp_path, result):
    module = load('run_vspaero_checks')
    report = tmp_path/'report.json'
    report.write_text(__import__('json').dumps(result))
    with pytest.raises(ValueError, match='did not pass'):
        module.require_regression_pass(report)

def test_vspaero_gate_requires_recorded_individual_successes(tmp_path):
    module = load('run_vspaero_checks')
    report = tmp_path/'report.json'
    result = dict(status='PASS', checks=[dict(name=name, status='PASS')
                                        for name in sorted(module.REQUIRED_LOOKUP_CHECKS)])
    report.write_text(__import__('json').dumps(result))
    assert module.require_regression_pass(report) == result

@pytest.mark.parametrize('change', ['partial', 'missing', 'duplicate', 'unexpected', 'invalid_name'])
def test_vspaero_gate_requires_each_named_regression_exactly_once(tmp_path, change):
    module = load('run_vspaero_checks')
    checks = [dict(name=name, status='PASS') for name in sorted(module.REQUIRED_LOOKUP_CHECKS)]
    if change == 'partial':
        checks = checks[:1]
    elif change == 'missing':
        checks.pop()
    elif change == 'duplicate':
        checks.append(dict(checks[0]))
    elif change == 'unexpected':
        checks[-1]['name'] = 'unreviewed_replacement'
    else:
        checks[-1]['name'] = ['invalid', 'name']
    report = tmp_path/'report.json'
    report.write_text(__import__('json').dumps(dict(status='PASS', checks=checks)))
    with pytest.raises(ValueError, match='regression names'):
        module.require_regression_pass(report)

def test_vspaero_gate_rejects_binary_outside_current_build(tmp_path):
    module = load('run_vspaero_checks')
    build = tmp_path/'build'
    build.mkdir()
    solver = tmp_path/'previous-vspaero.exe'
    solver.write_bytes(b'old build')
    probe = build/'checkpoint_probe.exe'
    probe.write_bytes(b'probe')
    (build/'executables-Release.txt').write_text(f'{solver}\n{probe}\n')
    with pytest.raises(ValueError, match='out-of-build'):
        module.read_executables(build)
