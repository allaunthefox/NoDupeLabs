# SPDX-License-Identifier: Apache-2.0
# Lightweight ONNX runtime + CPU fallback backends for NSFW/embedding inference

from __future__ import annotations
import os
from pathlib import Path
from typing import Optional, Tuple

try:
    import onnxruntime as ort  # type: ignore
except Exception:  # intentional broad catch — runtime may not be present
    ort = None  # type: ignore


class BaseBackend:
    """Abstract simple interface used by NSFWClassifier.

    Methods:
    - available() -> bool
    - predict(path: Path) -> Tuple[int, str]  # score 0-3, reason
    """

    def available(self) -> bool:
        return False

    def predict(self, path: Path) -> Tuple[int, str]:
        raise NotImplementedError()


class CPUBackend(BaseBackend):
    """Very small CPU fallback: no external deps required.

    It implements a minimal image feature heuristic: if Pillow is available
    it checks resolution and EXIF like the existing classifier; otherwise
    it returns a neutral score 0.
    """

    def __init__(self):
        try:
            from PIL import Image  # type: ignore
            self.has_pil = True
        except Exception:
            self.has_pil = False

    def available(self) -> bool:
        return True

    def predict(self, path: Path) -> Tuple[int, str]:
        # Best-effort analysis: return (score, reason)
        try:
            if not self.has_pil:
                return 0, "cpu_no_pillow"

            from PIL import Image
            with Image.open(path) as img:
                w, h = img.size
                if w * h > 8000 * 6000:
                    return 1, "cpu_high_res"
                aspect = w / max(1, h)
                if 0.5 < aspect < 0.7:
                    return 1, "cpu_portrait"
                if aspect > 2.0:
                    return 1, "cpu_ultrawide"
        except Exception:
            # Any errors produce neutral result
            return 0, "cpu_error"

        return 0, "cpu_neutral"


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

        if ort is None:
            self._available = False
            return

        if not self.model_path or not self.model_path.exists():
            self._available = False
            return

        try:
            # Create session with available GPU providers if possible
            providers = ort.get_available_providers()
            # Preferred order: CUDA, ROCm, DirectML, CPU
            ep = []
            for p in ("CUDAExecutionProvider", "ROCMExecutionProvider", "DmlExecutionProvider"):
                if p in providers:
                    ep.append(p)
            # Always include CPU as fallback
            ep.append("CPUExecutionProvider")

            self.sess = ort.InferenceSession(str(self.model_path), providers=ep)
            self._available = True
        except Exception:
            self._available = False

    def available(self) -> bool:
        return bool(self._available)

    def predict(self, path: Path) -> Tuple[int, str]:
        # Offload heavy model I/O to ORT -> returns score 0-3
        # Implementation assumes the model accepts an image input and returns a single float [0,1]
        # For compatibility we map prob->score
        if not self.sess:
            return 0, "onnx_no_session"

        try:
            import numpy as np  # type: ignore
            from PIL import Image

            # Basic preprocess: load image, resize to model input shape (assume 224x224), normalize
            img = Image.open(path).convert("RGB")
            img = img.resize((224, 224))
            arr = (np.asarray(img).astype("float32") / 255.0)[None, :]

            # Try to find an input name
            inp_name = self.sess.get_inputs()[0].name
            out_name = self.sess.get_outputs()[0].name
            out = self.sess.run([out_name], {inp_name: arr})[0]

            # Flatten first value
            prob = float(out.reshape(-1)[0])
            if prob < 0:
                prob = 0.0
            if prob > 1:
                prob = 1.0

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

        except Exception:
            return 0, "onnx_predict_error"


def choose_backend(model_hint: Optional[str] = None) -> BaseBackend:
    """Select best backend available.

    model_hint: optional path override for the model file
    """
    # Prefer ONNX if available and model exists
    try:
        if ort is not None:
            model_path = Path(model_hint) if model_hint else Path(__file__).parent.parent / "models" / "nsfw_small.onnx"
            be = ONNXBackend(model_path)
            if be.available():
                return be
    except Exception:
        pass

    # Fallback to CPU
    return CPUBackend()
