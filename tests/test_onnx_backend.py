import sys
from pathlib import Path


def test_onnx_backend_model_load_behavior():
    """Ensure ONNX backend either loads the model or returns a useful
    unavailable reason when the runtime can't load it.

    This test is intentionally tolerant: CI runners may have different
    onnxruntime builds. We ensure the backend provides diagnostic info so
    users can take corrective action.
    """
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))

    from nodupe.ai.backends.onnx import ONNXBackend

    model_path = root / 'nodupe' / 'models' / 'nsfw_small.onnx'
    assert model_path.exists(), 'expected sample model to be present for this test'

    be = ONNXBackend(model_path)

    # Either the backend is available (can load the model) OR it should
    # provide a short unavailable_reason suggesting why (eg model IR mismatch)
    if be.available():
        assert be.unavailable_reason() is None
    else:
        r = be.unavailable_reason() or ''
        assert r, 'backend is unavailable but returned no reason; expect diagnostics'
