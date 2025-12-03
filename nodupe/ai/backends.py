# SPDX-License-Identifier: Apache-2.0
# Lightweight ONNX runtime + CPU fallback backends for NSFW/embedding inference

from __future__ import annotations
from pathlib import Path
from typing import Optional, Tuple, List

try:
    import onnxruntime as ort  # type: ignore # pylint: disable=import-error
except Exception:  # pylint: disable=broad-except
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
            import PIL  # type: ignore # noqa: F401 # pylint: disable=import-error
            _ = PIL
            self.has_pil = True
        except Exception:  # pylint: disable=broad-except
            self.has_pil = False

    def available(self) -> bool:
        return True

    def predict(self, path: Path) -> Tuple[int, str]:
        # Best-effort analysis: return (score, reason)
        try:
            if not self.has_pil:
                return 0, "cpu_no_pillow"

            from PIL import Image  # pylint: disable=import-error
            with Image.open(path) as img:
                w, h = img.size
                if w * h > 8000 * 6000:
                    return 1, "cpu_high_res"
                aspect = w / max(1, h)
                if 0.5 < aspect < 0.7:
                    return 1, "cpu_portrait"
                if aspect > 2.0:
                    return 1, "cpu_ultrawide"
        except Exception:  # pylint: disable=broad-except
            # Any errors produce neutral result
            return 0, "cpu_error"

        return 0, "cpu_neutral"

    def compute_embedding(self, path: Path, dim: int = 16) -> List[float]:
        """Compute a small embedding vector using simple image statistics.

        Returns a fixed-length float list length=dim. If PIL missing, return
        a lightweight fallback using file size and mtime.
        """
        out = [0.0] * dim
        try:
            if not self.has_pil:
                st = path.stat()
                # spread size and mtime across vector
                v = float(st.st_size) % 9973 / 9973.0
                m = float(st.st_mtime) % 9973 / 9973.0
                for i in range(dim):
                    out[i] = (v * (i + 1) + m * (dim - i)) / (dim + 1)
                return out

            from PIL import Image  # type: ignore # pylint: disable=import-error
            try:
                import numpy as np  # type: ignore # pylint: disable=import-error
            except ImportError:
                # Fallback if numpy missing even if PIL present
                st = path.stat()
                v = float(st.st_size) % 9973 / 9973.0
                return [(v * (i + 1)) % 1.0 for i in range(dim)]

            with Image.open(path) as img:
                img = img.convert('RGB').resize((32, 32))
                arr = np.asarray(img).astype('float32') / 255.0
                # compute mean per-channel and some moments
                means = arr.mean(axis=(0, 1)).tolist()
                std = arr.std(axis=(0, 1)).mean().item()
                s = path.stat()
                size_norm = (s.st_size % 1000000) / 1000000.0
                vals = means + [std, size_norm]
                # expand/repeat/truncate into dim
                for i in range(dim):
                    out[i] = float(vals[i % len(vals)]) * (1.0 + (i % 5) * 0.01)
                return out
        except Exception:  # pylint: disable=broad-except
            # On any error, return neutral vector
            return out


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
        except Exception:  # pylint: disable=broad-except
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
            import numpy as np  # type: ignore # pylint: disable=import-error
            from PIL import Image  # type: ignore # pylint: disable=import-error

            # Basic preprocess: load image, resize to model input shape (assume 224x224), normalize
            img = Image.open(path).convert("RGB").resize((224, 224))
            arr = (np.asarray(img).astype("float32") / 255.0)[None, :]

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
        """Attempt to produce an embedding using the ONNX model if it yields a vector.

        Our demo model may only produce a scalar; if so, fall back to the CPU embedding.
        """
        try:
            # If the model returns a vector-like output use it
            if not self.sess:
                raise RuntimeError('no_session')
            import numpy as np  # type: ignore # pylint: disable=import-error
            from PIL import Image  # type: ignore # pylint: disable=import-error
            img = Image.open(path).convert('RGB').resize((32, 32))
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
    except Exception:  # pylint: disable=broad-except
        pass

    # Fallback to CPU
    return CPUBackend()