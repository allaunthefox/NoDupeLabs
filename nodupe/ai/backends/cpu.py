# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""CPU-based fallback backend.

This backend provides basic heuristics for NSFW classification and
embedding computation without requiring heavy dependencies like
ONNX Runtime or PyTorch. It uses Pillow for basic image analysis
if available, or file metadata as a last resort.

Key Features:
    - Zero heavy dependencies (optional Pillow)
    - Heuristic-based classification (aspect ratio, resolution)
    - Deterministic embedding generation from file stats

Classes:
    - CPUBackend: Implementation of BaseBackend
"""
from __future__ import annotations
from pathlib import Path
from typing import Tuple, List
from .base import BaseBackend


class CPUBackend(BaseBackend):
    """Very small CPU fallback: no external deps required.

    It implements a minimal image feature heuristic: if Pillow is available
    it checks resolution and EXIF like the existing classifier; otherwise
    it returns a neutral score 0.
    """

    def __init__(self):
        try:
            # type: ignore # noqa: F401 # pylint: disable=import-error
            import PIL
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

            # type: ignore # pylint: disable=import-error
            from PIL import Image
            # If the provided path points at a video, extract a representative
            # frame first and operate on that image. This keeps embedding logic
            # compatible with videos (mp4/webm/mkv etc.) as well as images.
            try:
                from nodupe.utils.filesystem import get_mime_safe
                from nodupe.utils.media import extract_representative_frame
                mime = get_mime_safe(path)
                if mime and mime.startswith("video/"):
                    frame = extract_representative_frame(path)
                    if frame:
                        path_for_image = frame
                    else:
                        path_for_image = path
                else:
                    path_for_image = path
            except Exception:  # pylint: disable=broad-except
                path_for_image = path
            try:
                # type: ignore # pylint: disable=import-error
                import numpy as np
            except ImportError:
                # Fallback if numpy missing even if PIL present
                st = path.stat()
                v = float(st.st_size) % 9973 / 9973.0
                return [(v * (i + 1)) % 1.0 for i in range(dim)]

            with Image.open(path_for_image) as img:
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
                    out[i] = float(vals[i % len(vals)]) * (
                        1.0 + (i % 5) * 0.01
                    )
                return out
        except Exception:  # pylint: disable=broad-except
            # On any error, return neutral vector
            return out
