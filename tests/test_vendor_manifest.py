from pathlib import Path
import json


def test_vendor_manifest_present_and_valid():
    root = Path(__file__).resolve().parents[1]
    vendor = root / 'nodupe' / 'vendor' / 'libs'
    mf = vendor / 'vendor_manifest.json'
    assert mf.exists(), 'vendor_manifest.json should exist in nodupe/vendor/libs'

    data = json.loads(mf.read_text(encoding='utf-8'))
    assert 'packages' in data and isinstance(data['packages'], list)
    assert 'files' in data and isinstance(data['files'], list)

    # All declared files should exist on disk
    for f in data['files']:
        p = vendor / f
        assert p.exists(), f'File listed in manifest missing: {f}'
