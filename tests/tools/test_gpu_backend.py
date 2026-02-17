import math

import numpy as np
import pytest
import sys
import types

# Provide a lightweight stub for the optional gpu_tool module that the
# package-level import expects (some environments don't include the plugin
# file). This prevents import-time failures during tests.
if "nodupe.tools.gpu.gpu_tool" not in sys.modules:
    mod = types.ModuleType("nodupe.tools.gpu.gpu_tool")
    mod.register_tool = lambda: None
    sys.modules["nodupe.tools.gpu.gpu_tool"] = mod

from nodupe.tools.gpu import (
    CPUFallbackBackend,
    create_gpu_backend,
    get_gpu_backend,
)


def test_cpu_fallback_is_available():
    backend = CPUFallbackBackend()
    assert backend.is_available() is True


def test_compute_embeddings_normalizes_vectors():
    backend = CPUFallbackBackend()
    vec = [3.0, 4.0]
    res = backend.compute_embeddings([vec])

    assert isinstance(res, list)
    assert len(res) == 1
    emb = res[0]
    # normalized vector should have length 1.0 (within tolerance)
    norm = math.sqrt(sum(x * x for x in emb))
    assert pytest.approx(1.0, rel=1e-3) == norm


def test_compute_embeddings_fallback_for_non_sequence():
    backend = CPUFallbackBackend()
    res = backend.compute_embeddings([42, "text"])
    assert isinstance(res, list)
    assert len(res) == 2
    # non-sequence fallback produces 128-dim vector
    assert len(res[0]) == 128 or len(res[1]) == 128


def test_matrix_multiply_simple_case():
    backend = CPUFallbackBackend()
    a = [[1, 2], [3, 4]]
    b = [[5], [6]]
    out = backend.matrix_multiply(a, b)
    assert out == [[17.0], [39.0]]


def test_get_device_info_and_create_backend_cpu():
    # ensure explicit cpu backend creation works
    backend = create_gpu_backend("cpu")
    assert isinstance(backend, CPUFallbackBackend)
    info = backend.get_device_info()
    assert "type" in info and info["type"] == "cpu"

    # get_gpu_backend returns a backend instance (module-level)
    gw = get_gpu_backend()
    assert hasattr(gw, "is_available")
