# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Configuration presets.

Provides pre-configured settings for common use cases.
"""
from typing import Dict

from .schema import Config


# Define presets using Config dataclass
PRESETS: Dict[str, Config] = {
    "default": Config(),

    "performance": Config(
        hash_algo="blake2b",
        meta_validate_schema=False,
        logging={"rotate_mb": 10, "keep": 7, "level": "WARN"},
        ai={"enabled": False, "backend": "onnxruntime",
            "model_path": "models/nsfw_small.onnx"},
    ),

    "paranoid": Config(
        hash_algo="sha512",
        dry_run=True,
        checkpoint=True,
        meta_validate_schema=True,
        nsfw={"enabled": True, "threshold": 2, "auto_quarantine": False},
    ),

    "media": Config(
        hash_algo="blake2b",
        similarity={"dim": 64},
        ai={"enabled": True, "backend": "onnxruntime",
            "model_path": "models/nsfw_small.onnx"},
        nsfw={"enabled": True, "threshold": 2, "auto_quarantine": False},
    ),

    "ebooks": Config(
        hash_algo="sha256",
        ai={"enabled": False, "backend": "onnxruntime",
            "model_path": "models/nsfw_small.onnx"},
        nsfw={"enabled": False, "threshold": 2, "auto_quarantine": False},
        meta_pretty=True,
    ),

    "audiobooks": Config(
        hash_algo="blake2b",
        ai={"enabled": False, "backend": "onnxruntime",
            "model_path": "models/nsfw_small.onnx"},
        nsfw={"enabled": False, "threshold": 2, "auto_quarantine": False},
        meta_pretty=True,
        ignore_patterns=(
            ".git", "node_modules", "__pycache__",
            ".nodupe_duplicates", ".venv", "venv",
            ".DS_Store", "Thumbs.db"
        ),
    ),

    "archives": Config(
        hash_algo="sha512",
        follow_symlinks=False,
        ai={"enabled": False, "backend": "onnxruntime",
            "model_path": "models/nsfw_small.onnx"},
        logging={"rotate_mb": 10, "keep": 7, "level": "DEBUG"},
    ),
}


def get_preset(name: str) -> Config:
    """Get configuration preset by name.

    Args:
        name: Preset name

    Returns:
        Config instance for preset

    Raises:
        ValueError: If preset name unknown
    """
    if name not in PRESETS:
        available = ", ".join(sorted(PRESETS.keys()))
        raise ValueError(
            f"Unknown preset '{name}'. Available: {available}"
        )
    return PRESETS[name]


def get_available_presets():
    """Return list of available preset names."""
    return list(PRESETS.keys())
