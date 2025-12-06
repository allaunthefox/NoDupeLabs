import subprocess
import sys
from pathlib import Path


def test_upgrade_or_fallback_exit_code_zero():
    root = Path(__file__).resolve().parents[1]
    script = root / 'scripts' / 'upgrade_or_fallback_onnxruntime.py'
    assert script.exists(), 'upgrade_or_fallback helper must exist'

    rc = subprocess.run([
        sys.executable, str(script), '--model',
        'nodupe/models/nsfw_small.onnx', '--force'
    ]).returncode
    assert rc == 0, f'script failed with exit code {rc}'
