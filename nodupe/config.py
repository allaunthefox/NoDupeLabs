# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

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
            return json.dumps(obj, sort_keys=sort_keys, ensure_ascii=False, indent=2)
    yaml = _YAMLShim()

DEFAULTS = {
    "hash_algo": "sha512",
    "dedup_strategy": "content_hash",
    "parallelism": 0,  # 0 = auto-detect
    "follow_symlinks": False,
    "dry_run": True,
    "overwrite": False,
    "checkpoint": True,
    "ignore_patterns": [".git", "node_modules", "__pycache__", ".nodupe_duplicates", ".venv", "venv"],
    "nsfw": {"enabled": False, "threshold": 2, "auto_quarantine": False},
    "ai": {"enabled": "auto", "backend": "onnxruntime", "model_path": "models/nsfw_small.onnx"},
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

def ensure_config(path: str = "nodupe.yml") -> None:
    """Create default configuration file if it doesn't exist."""
    p = Path(path)
    if not p.exists():
        p.write_text(
            "# Auto-generated config. Edit as needed.\n"
            + yaml.safe_dump(DEFAULTS, sort_keys=False),
            encoding="utf-8",
        )

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
    except Exception as e:
        print(f"[config][WARN] Environment detection failed: {e}")

    return cfg
