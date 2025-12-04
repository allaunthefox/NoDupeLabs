from pathlib import Path


def test_onnxruntime_wheel_vendored():
    root = Path(__file__).resolve().parents[1]
    vendor_dir = root / 'nodupe' / 'vendor' / 'libs'
    assert vendor_dir.exists(), 'vendor libs dir should exist'

    wheels = [
        p for p in vendor_dir.iterdir()
        if p.suffix == '.whl' and 'onnxruntime' in p.name.lower()
    ]
    assert wheels, (
        'expected at least one vendored onnxruntime wheel in '
        'nodupe/vendor/libs'
    )


def test_minimum_vendored_wheels():
    """Ensure the minimum set of vendor wheels are present for offline use.

    This test looks for wheels for the required packages listed in pyproject
    as well as a small curated set of optional packages we rely on for tests
    and features (onnxruntime, pillow, numpy, psutil, etc.).
    """
    root = Path(__file__).resolve().parents[1]
    vendor_dir = root / 'nodupe' / 'vendor' / 'libs'
    assert vendor_dir.exists(), 'vendor libs dir should exist'

    expected = [
        'pyyaml',
        'jsonschema',
        'numpy',
        'onnxruntime',
        'pillow',
        'psutil',
        'py7zr',
        'rarfile',
        'tqdm',
        'xxhash',
        'zstandard',
    ]

    present = {
        p.name.lower() for p in vendor_dir.iterdir() if p.suffix == '.whl'
    }
    missing = [n for n in expected if not any(n in name for name in present)]
    assert not missing, (
        f'Missing vendored wheels for: {missing} '
        f'(present: {sorted(present)})'
    )
