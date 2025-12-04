from pathlib import Path


def test_demo_model_present():
    # Resolve path relative to the repository root (don't rely on CWD)
    repo_root = Path(__file__).resolve().parents[1]
    p = repo_root / 'nodupe' / 'models' / 'nsfw_small.onnx'
    assert p.exists()
    assert p.stat().st_size > 200  # ensure it's non-trivial
