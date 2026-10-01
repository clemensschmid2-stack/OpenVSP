import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import pytest
import reference_manifest as refs


def test_committed_reference_inventory_and_hashes():
    assert refs.verify_openvsp()['files']

def fixture(tmp_path, data=b'fixed executable'):
    (tmp_path/'binary').write_bytes(data)
    receipt=dict(format='vds-fixed-reference-v1',files={'binary':hashlib.sha256(data).hexdigest()})
    (tmp_path/'manifest.json').write_text(json.dumps(receipt))
    return receipt


def test_reference_is_verified_without_rebuild(tmp_path):
    expected=fixture(tmp_path)
    assert refs.verify_files(tmp_path)==expected


@pytest.mark.parametrize('change',['missing','tampered'])
def test_missing_or_changed_reference_fails(tmp_path,change):
    fixture(tmp_path)
    if change=='missing': (tmp_path/'binary').unlink()
    else: (tmp_path/'binary').write_bytes(b'changed')
    with pytest.raises(ValueError,match='reference|Reference'):
        refs.verify_files(tmp_path)


def test_reference_manifest_cannot_escape_directory(tmp_path):
    manifest=fixture(tmp_path)
    manifest['files']={'../outside':'not a hash'}
    (tmp_path/'manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(ValueError,match='unsafe|inventory'):
        refs.verify_files(tmp_path)


def test_unexpected_reference_dll_fails(tmp_path):
    fixture(tmp_path)
    (tmp_path/'untracked.dll').write_bytes(b'could affect loading')
    with pytest.raises(ValueError,match='inventory'):
        refs.verify_files(tmp_path)


@pytest.mark.parametrize('tracked', [False, True])
def test_openvsp_requires_reference_files_to_be_tracked(monkeypatch, tracked):
    # An ignored .pyd passed local file/hash validation, but fresh checkouts missed it.
    relative = 'python/openvsp/openvsp/_vsp.pyd'
    manifest = {'files': {relative: 'already-verified-hash'}}
    monkeypatch.setattr(refs, 'verify_files', lambda *args: manifest)
    listing = 'reference_builds/OpenVSP-3.52.2-win64/'+relative+'\0' if tracked else ''
    monkeypatch.setattr(refs.subprocess, 'check_output', lambda *args, **kwargs: listing)
    if tracked:
        assert refs.verify_openvsp() == manifest
    else:
        with pytest.raises(ValueError, match='not fully tracked'):
            refs.verify_openvsp()
