import sys
from pathlib import Path


def test_onnx_backend_compat_model_loads():
    """Ensure ONNXBackend will load the compat model that we vendored/produced.

    This test verifies the fallback path (`*_compat.onnx`) works and that the
    backend reports itself as available when the compat model is loadable.
    """
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))

    from nodupe.ai.backends.onnx import ONNXBackend

    compat = root / 'nodupe' / 'models' / 'nsfw_small_compat.onnx'
    assert compat.exists(), 'compat model must exist for this test'

    be = ONNXBackend(compat)
    assert be.available(
    ), (
        f'ONNXBackend should be available for compat model, '
        f'got reason={be.unavailable_reason()}'
    )

    # Call predict on a small sample to ensure the runtime actually responds
    sample = root / 'nsfw_test_set' / 'safe' / '6017856.jpg'
    assert sample.exists(), 'Expected sample test image to exist'
    res = be.predict(sample)
    assert isinstance(res, tuple) and len(res) == 2
