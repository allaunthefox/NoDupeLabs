# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""AI backend selection and initialization.

This module manages the selection of AI backends for NSFW classification
and embedding computation. It attempts to load the ONNX backend first,
falling back to the CPU backend if ONNX Runtime is unavailable or the
model file is missing.

Key Features:
    - Automatic backend selection (ONNX > CPU)
    - Graceful degradation
    - Diagnostic reporting for backend failures

Functions:
    - choose_backend: Factory function to get the best available backend
"""
from __future__ import annotations
from pathlib import Path
from typing import Optional
from .base import BaseBackend
from .cpu import CPUBackend
from .onnx import ONNXBackend

try:
    import onnxruntime as ort  # type: ignore # pylint: disable=import-error
except Exception:  # pylint: disable=broad-except
    ort = None  # type: ignore


def choose_backend(model_hint: Optional[str] = None) -> BaseBackend:
    """Select best backend available.

    model_hint: optional path override for the model file
    """
    # Prefer ONNX if available and model exists
    try:
        if ort is not None:
            if model_hint:
                model_path = Path(model_hint)
            else:
                model_path = (
                    Path(__file__).parent.parent.parent
                    / "models" / "nsfw_small.onnx"
                )
            be = ONNXBackend(model_path)
            if be.available():
                return be
            # If ONNXBackend couldn't initialize help users by surfacing the
            # reason. This is intentionally informative — callers will fall
            # back to the CPU backend but having a diagnostic message helps
            # when troubleshooting model/ORT mismatches.
            try:
                reason = (
                    be.unavailable_reason() or 'onnx_backend_unknown_error'
                )
                print(f'[ai.backends] ONNXBackend not usable: {reason}')
            except Exception:
                # Never raise here — fallback to CPU below is still desirable
                pass
    except Exception:  # pylint: disable=broad-except
        pass

    # Fallback to CPU
    return CPUBackend()
