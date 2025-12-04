# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Configuration management for NoDupeLabs.

This module handles loading, merging, and validating configuration
files. It supports YAML format with automatic fallback to JSON if
PyYAML is not available.

Key Features:
    - Configuration presets for common use cases
    - Environment-aware auto-tuning (desktop, NAS, cloud, container)
    - Graceful degradation when PyYAML is unavailable
    - Automatic config file generation with sensible defaults

Presets:
    - default: Balanced settings (SHA-512, safe defaults)
    - performance: Faster hashing (BLAKE2b), less logging, validation
        disabled
    - paranoid: Maximum safety (SHA-512, strict validation,
        dry-run enabled)
    - media: Optimized for images/video (BLAKE2b, AI enabled,
        larger similarity index)
    - ebooks: Optimized for text/PDFs (SHA-256, AI disabled,
        pretty metadata)
    - audiobooks: Optimized for audio collections (BLAKE2b,
        AI disabled, extra ignore patterns)
    - archives: Optimized for long-term storage (SHA-512, debug logging)

Configuration Keys:
    - hash_algo: Hash algorithm (sha256, sha512, blake2b)
    - dedup_strategy: Deduplication strategy (content_hash)
    - parallelism: Number of worker threads (0 = auto-detect)
    - dry_run: If True, no destructive operations are performed
    - ignore_patterns: List of glob patterns to skip during scanning
    - nsfw: NSFW detection settings (enabled, threshold, auto_quarantine)
    - ai: AI backend settings (enabled, backend, model_path)
    - similarity: Similarity index settings (dim)
    - logging: Log rotation and verbosity settings
    - db_path: SQLite database path
    - export_folder_meta: Generate meta.json files in scanned directories

Dependencies:
    - PyYAML (optional, falls back to JSON if unavailable)

Example:
    >>> cfg = load_config('nodupe.yml')
    >>> print(cfg['hash_algo'])
    'sha512'
"""

from pathlib import Path
from typing import Any, Dict

try:
    import yaml
except ImportError:
    import json

    class _YAMLShim:
        class YAMLError(Exception):
            pass

        @staticmethod
        def safe_load(text: str):
            try:
                return json.loads(text)
            except json.JSONDecodeError as e:
                raise _YAMLShim.YAMLError(e)

        @staticmethod
        def safe_dump(obj: Any, sort_keys: bool = False) -> str:
            return json.dumps(
                obj, sort_keys=sort_keys, ensure_ascii=False, indent=2
            )
    yaml = _YAMLShim()

DEFAULTS = {
    "hash_algo": "sha512",
    "dedup_strategy": "content_hash",
    "parallelism": 0,  # 0 = auto-detect
    "follow_symlinks": False,
    "dry_run": True,
    "overwrite": False,
    "checkpoint": True,
    "ignore_patterns": [
        ".git", "node_modules", "__pycache__", ".nodupe_duplicates", ".venv",
        "venv"
    ],
    "nsfw": {"enabled": False, "threshold": 2, "auto_quarantine": False},
    "ai": {
        "enabled": "auto",
        "backend": "onnxruntime",
        "model_path": "models/nsfw_small.onnx"
    },
    "similarity": {"dim": 16},
    "logging": {"rotate_mb": 10, "keep": 7, "level": "INFO"},
    "db_path": "output/index.db",
    "log_dir": "output/logs",
    "metrics_path": "output/metrics.json",
    "export_folder_meta": True,
    "meta_format": "nodupe_meta_v1",
    "meta_pretty": False,
    "meta_validate_schema": True,
    "auto_install_deps": True,
}

PRESETS = {
    "default": DEFAULTS,
    "performance": {
        **DEFAULTS,
        "hash_algo": "blake2b",
        "meta_validate_schema": False,
        "logging": {**DEFAULTS["logging"], "level": "WARN"},
        "ai": {**DEFAULTS["ai"], "enabled": False},
    },
    "paranoid": {
        **DEFAULTS,
        "hash_algo": "sha512",
        "dry_run": True,
        "checkpoint": True,
        "meta_validate_schema": True,
        "nsfw": {
            **DEFAULTS["nsfw"], "enabled": True, "auto_quarantine": False
        },
    },
    "media": {
        **DEFAULTS,
        "hash_algo": "blake2b",
        "similarity": {"dim": 64},
        "ai": {**DEFAULTS["ai"], "enabled": True},
        "nsfw": {**DEFAULTS["nsfw"], "enabled": True},
    },
    "ebooks": {
        **DEFAULTS,
        "hash_algo": "sha256",
        "ai": {**DEFAULTS["ai"], "enabled": False},
        "nsfw": {**DEFAULTS["nsfw"], "enabled": False},
        "meta_pretty": True,
    },
    "audiobooks": {
        **DEFAULTS,
        "hash_algo": "blake2b",
        "ai": {**DEFAULTS["ai"], "enabled": False},
        "nsfw": {**DEFAULTS["nsfw"], "enabled": False},
        "meta_pretty": True,
        "ignore_patterns": DEFAULTS["ignore_patterns"] + [
            ".DS_Store", "Thumbs.db"
        ],
    },
    "archives": {
        **DEFAULTS,
        "hash_algo": "sha512",
        "follow_symlinks": False,
        "ai": {**DEFAULTS["ai"], "enabled": False},
        "logging": {**DEFAULTS["logging"], "level": "DEBUG"},
    }
}


def ensure_config(path: str = "nodupe.yml", preset: str = "default") -> None:
    """Create default configuration file if it doesn't exist.

    Args:
        path: Path to configuration file (default: nodupe.yml)
        preset: Preset name to use for initial config (default: 'default')

    Returns:
        None
    """
    p = Path(path)
    if not p.exists():
        cfg = PRESETS.get(preset, DEFAULTS)
        p.write_text(
            f"# Auto-generated config using '{preset}' preset. "
            f"Edit as needed.\n"
            + yaml.safe_dump(cfg, sort_keys=False),
            encoding="utf-8",
        )


def get_available_presets():
    """Return list of available preset names."""
    return list(PRESETS.keys())


def load_config(path: str = "nodupe.yml") -> Dict[str, Any]:
    """Load configuration."""
    ensure_config(path)
    p = Path(path)
    cfg = DEFAULTS.copy()

    if p.exists():
        try:
            data = yaml.safe_load(p.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                cfg.update(data)
        except (yaml.YAMLError, OSError) as e:
            print(f"[config][WARN] Failed to load {path}: {e}")

    # Apply environment auto-tuning
    try:
        from .environment import Environment
        env = Environment()
        cfg = env.apply_to_config(cfg)
    except (ImportError, OSError, ValueError) as e:
        print(f"[config][WARN] Environment detection failed: {e}")

    return cfg
