from pathlib import Path

def test_demo_model_present():
    p = Path('nodupe/models/nsfw_small.onnx')
    assert p.exists()
    assert p.stat().st_size > 200  # ensure it's non-trivial
