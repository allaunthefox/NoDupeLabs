# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""ONNX Runtime backend for AI inference.

This backend uses ONNX Runtime to execute machine learning models for
NSFW classification and embedding generation. It supports hardware
acceleration (CUDA, ROCm, DirectML) if available.

Key Features:
    - High-performance inference via ONNX Runtime
    - Hardware acceleration support
    - Robust error handling and fallback logic
    - Automatic input resizing and normalization

Classes:
    - ONNXBackend: Implementation of BaseBackend using ONNX Runtime
"""
from __future__ import annotations
from pathlib import Path
from typing import Optional, Tuple, List
from .base import BaseBackend
from .cpu import CPUBackend
import re

try:
    import onnxruntime as ort  # type: ignore # pylint: disable=import-error
except Exception:  # pylint: disable=broad-except
    ort = None  # type: ignore


class ONNXBackend(BaseBackend):
    """ONNX Runtime backend.

    Looks up a provided ONNX model path and attempts to use the best available
    execution provider (CUDA, ROCm, DirectML). If ORT isn't installed or the
    model is missing the backend is not available.
    NOTE: This backend purposely keeps the runtime import optional and handles
    failures gracefully.
    """

    def __init__(self, model_path: Optional[Path] = None):
        self.model_path = Path(model_path) if model_path else None
        self.sess = None
        self._unavailable_reason: Optional[str] = None

        # If ORT wasn't importable, mark unavailable with a reason
        if ort is None:
            self._available = False
            self._unavailable_reason = 'onnxruntime_not_installed'
            return

        if not self.model_path or not self.model_path.exists():
            self._available = False
            self._unavailable_reason = 'model_missing'
            return

        try:
            # Create session with available GPU providers if possible
            providers = ort.get_available_providers()
            # Preferred order: CUDA, ROCm, DirectML, CPU
            ep = []
            for p in (
                "CUDAExecutionProvider", "ROCMExecutionProvider",
                "DmlExecutionProvider"
            ):
                if p in providers:
                    ep.append(p)
            # Always include CPU as fallback
            ep.append("CPUExecutionProvider")

            self.sess = ort.InferenceSession(
                str(self.model_path), providers=ep
            )
            self._available = True
        except Exception as exc:  # pylint: disable=broad-except
            # Capture the exception message so callers can produce better
            # diagnostics if the model cannot be loaded (for example an
            # unsupported ONNX IR version or incompatible opset).
            try:
                msg = str(exc)
                # Common ORT error for unsupported IR looks like:
                m = re.search(
                    r'Unsupported model IR version:\s*(\d+).*'
                    r'max supported IR version:\s*(\d+)',
                    msg
                )
                if m:
                    self._unavailable_reason = (
                        f"model_ir={m.group(1)}, ort_max_ir={m.group(2)}"
                    )
                else:
                    import traceback
                    self._unavailable_reason = traceback.format_exc()[:1000]
            except Exception:
                self._unavailable_reason = 'onnx_inference_session_failed'
            # Attempt a fallback: if a compat model explicitly exists in the
            # same models directory ("*_compat.onnx"), try to load that. This
            # is useful for workflows that keep a converted model alongside the
            # original; loading that model may succeed with older ORT builds.
            # Attempt a fallback: if a compat model explicitly exists in the
            # same models directory ("*_compat.onnx"), try to load that. If
            # that succeeds, keep the backend available. If it fails, preserve
            # the original reason and mark unavailable.
            try:
                compat = self.model_path.with_name(
                    self.model_path.stem + '_compat.onnx'
                )
                if compat.exists():
                    try:
                        self.sess = ort.InferenceSession(
                            str(compat), providers=ep
                        )
                        # fallback succeeded — keep backend available
                        # and clear reason
                        self._available = True
                        self._unavailable_reason = None
                        # early return — we have a valid session
                        return
                    except Exception:  # pylint: disable=broad-except
                        # fallback failed — fall through and preserve
                        # original reason
                        pass
            except Exception:  # pylint: disable=broad-except
                # ignore any errors while probing the compat file
                pass

            # If we get here, fallback didn't produce a usable session — mark
            # backend unavailable (original _unavailable_reason preserved).
            self._available = False

    def available(self) -> bool:
        return bool(self._available)

    def unavailable_reason(self) -> Optional[str]:
        """Return a short-text reason why the backend isn't available.

        Useful for diagnostics in higher-level code paths so the CLI can
        give actionable advice (upgrade onnxruntime, vendor a wheel, or
        provide a compatible model file).
        """
        return self._unavailable_reason

    def predict(self, path: Path) -> Tuple[int, str]:
        # Offload heavy model I/O to ORT -> returns score 0-3
        # Implementation assumes the model accepts an image input
        # and returns a single float [0,1]
        # For compatibility we map prob->score
        if not self.sess:
            return 0, "onnx_no_session"

        try:
            import numpy as np  # type: ignore # pylint: disable=import-error
            # type: ignore # pylint: disable=import-error
            from PIL import Image

            # Handle video inputs by extracting a representative frame first
            try:
                from nodupe.utils.filesystem import get_mime_safe
                from nodupe.utils.media import extract_representative_frame
                mime = get_mime_safe(path)
                if mime and mime.startswith("video/"):
                    frame = extract_representative_frame(path)
                    img_path = frame if frame else path
                else:
                    img_path = path
            except Exception:  # pylint: disable=broad-except
                img_path = path

            # Make the input shape follow the model's required layout. Many
            # small/demo models expect NCHW with small spatial dims (eg 32x32).
            # We'll inspect the session input shape and adapt the image resize
            # / channel ordering accordingly.
            img = Image.open(img_path).convert("RGB")

            # Default resize (if model shape is unknown)
            target_h, target_w = 224, 224

            try:
                inp = self.sess.get_inputs()[0]
                # Expected shape like ['N', C, H, W]
                shp = inp.shape
                # If ONNX session exposes dimensions as ints, use them
                if isinstance(shp, (list, tuple)) and len(shp) == 4:
                    _, c_dim, h_dim, w_dim = shp
                    # only use numeric dims for resize
                    if isinstance(h_dim, int) and isinstance(w_dim, int):
                        target_h, target_w = int(h_dim), int(w_dim)
            except Exception:
                # If we can't introspect, fall back to defaults
                pass

            img = img.resize((target_w, target_h))
            arr = (np.asarray(img).astype("float32") / 255.0)[None, :]

            # Convert to NCHW if the model expects channels-first
            try:
                inp = self.sess.get_inputs()[0]
                shp = inp.shape
                # If shape looks like NCHW (len==4 and second dim is 3),
                # convert
                if isinstance(shp, (list, tuple)) and len(shp) == 4:
                    c_dim = shp[1]
                    if isinstance(c_dim, int) and c_dim == 3:
                        # arr is currently NHWC; transpose to NCHW
                        arr = arr.transpose(0, 3, 1, 2)
            except Exception:
                # best-effort conversion — if anything goes wrong, keep arr
                pass

            # Try to find an input name and run the model
            inp_name = self.sess.get_inputs()[0].name
            out = self.sess.run(None, {inp_name: arr})

            # Take first scalar or first value
            out_arr = np.asarray(out).reshape(-1)
            prob = float(out_arr[0]) if out_arr.size > 0 else 0.0
            prob = max(0.0, min(1.0, prob))

            # Map probability to 0-3
            if prob > 0.8:
                score = 3
            elif prob > 0.6:
                score = 2
            elif prob > 0.35:
                score = 1
            else:
                score = 0

            return score, f"onnx_prob={prob:.3f}"
        except Exception:  # pylint: disable=broad-except
            return 0, "onnx_predict_error"

    def compute_embedding(self, path: Path, dim: int = 16) -> List[float]:
        """Attempt to produce an embedding using the ONNX model.

        Our demo model may only produce a scalar; if so, fall back to the
        CPU embedding.
        """
        try:
            # If the model returns a vector-like output use it
            if not self.sess:
                raise RuntimeError('no_session')
            import numpy as np  # type: ignore # pylint: disable=import-error
            # type: ignore # pylint: disable=import-error
            from PIL import Image
            # Video handling - extract frame if needed
            try:
                from nodupe.utils.filesystem import get_mime_safe
                from nodupe.utils.media import extract_representative_frame
                mime = get_mime_safe(path)
                if mime and mime.startswith("video/"):
                    frame = extract_representative_frame(path)
                    img_path = frame if frame else path
                else:
                    img_path = path
            except Exception:  # pylint: disable=broad-except
                img_path = path

            img = Image.open(img_path).convert('RGB').resize((32, 32))
            arr = (np.asarray(img).astype('float32') / 255.0)[None, :]
            inp_name = self.sess.get_inputs()[0].name
            out = self.sess.run(None, {inp_name: arr})
            # Flatten and return up to dim values
            vec = np.asarray(out).reshape(-1)
            if vec.size >= dim:
                return vec[:dim].astype('float32').tolist()
            # pad or repeat
            outv = np.zeros(dim, dtype='float32')
            for i in range(dim):
                outv[i] = vec[i % vec.size] if vec.size > 0 else 0.0
            return outv.tolist()
        except Exception:  # pylint: disable=broad-except
            # fallback to CPU heuristic
            return CPUBackend().compute_embedding(path, dim=dim)
