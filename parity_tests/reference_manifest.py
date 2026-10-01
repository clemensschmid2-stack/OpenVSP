"""Validate committed reference artifacts. Never build or download a reference."""
import hashlib
import json
from pathlib import Path
import subprocess
import shlex

ROOT = Path(__file__).resolve().parents[1]
REFERENCES = ROOT/'reference_builds'


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def verify_files(directory, manifest_path=None):
    directory = Path(directory).resolve()
    manifest = json.loads(Path(manifest_path or directory/'manifest.json').read_text(encoding='utf-8'))
    if manifest.get('format') != 'vds-fixed-reference-v1' or not manifest.get('files'):
        raise ValueError('Invalid fixed reference manifest')
    receipt_path = Path(manifest_path or directory/'manifest.json').resolve()
    actual_files = {p.relative_to(directory).as_posix() for p in directory.rglob('*')
                    if p.is_file() and p.resolve() != receipt_path}
    if actual_files != set(manifest['files']):
        raise ValueError('Reference file inventory changed (missing or unexpected files)')
    for relative, expected in manifest['files'].items():
        path = (directory/relative).resolve()
        if not path.is_relative_to(directory) or not path.is_file():
            raise ValueError('Missing or unsafe reference artifact: '+relative)
        if digest(path) != expected:
            raise ValueError('Reference artifact hash mismatch: '+relative)
    return manifest


def verify_openvsp():
    manifest_path = REFERENCES/'openvsp-3.52.2-manifest.json'
    repository = ROOT
    prefix = 'reference_builds/OpenVSP-3.52.2-win64/'
    manifest = verify_files(repository/prefix, manifest_path)
    # Locally present ignored binaries must not conceal an incomplete published reference.
    tracked = subprocess.check_output(
        ['git', 'ls-files', '-z', '--', prefix], cwd=repository, text=True).split('\0')
    inventory = {path.removeprefix(prefix) for path in tracked if path}
    if inventory != set(manifest['files']):
        raise ValueError('OpenVSP reference manifest files are not fully tracked in Git')
    return manifest
