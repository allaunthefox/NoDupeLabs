# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Configuration schema definition.

Defines the structure and validation rules for NoDupeLabs configuration.
Uses dataclasses for immutability with frozen=True.
"""
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class HashAlgorithm(Enum):
    """Supported hash algorithms."""
    SHA256 = "sha256"
    SHA512 = "sha512"
    BLAKE2B = "blake2b"


class DedupStrategy(Enum):
    """Deduplication strategies."""
    CONTENT_HASH = "content_hash"


@dataclass(frozen=True)
class NSFWConfig:
    """NSFW detection configuration."""
    enabled: bool = False
    threshold: int = 2
    auto_quarantine: bool = False


@dataclass(frozen=True)
class AIConfig:
    """AI backend configuration."""
    enabled: str = "auto"  # "auto", "true", "false"
    backend: str = "onnxruntime"
    model_path: str = "models/nsfw_small.onnx"


@dataclass(frozen=True)
class SimilarityConfig:
    """Similarity search configuration."""
    dim: int = 16


@dataclass(frozen=True)
class LoggingConfig:
    """Logging configuration."""
    rotate_mb: int = 10
    keep: int = 7
    level: str = "INFO"


@dataclass(frozen=True)
class Config:
    """Main NoDupeLabs configuration.

    Immutable configuration object validated on construction.
    Cannot be modified after creation (frozen dataclass).
    """
    # Core settings
    hash_algo: str = "sha512"
    dedup_strategy: str = "content_hash"
    parallelism: int = 0  # 0 = auto-detect
    follow_symlinks: bool = False
    dry_run: bool = True
    overwrite: bool = False
    checkpoint: bool = True

    # Paths
    db_path: str = "output/index.db"
    log_dir: str = "output/logs"
    metrics_path: str = "output/metrics.json"

    # Patterns
    ignore_patterns: tuple = (
        ".git", "node_modules", "__pycache__",
        ".nodupe_duplicates", ".venv", "venv"
    )

    # Nested configs (using dicts for JSON compatibility)
    nsfw: Dict[str, Any] = field(default_factory=lambda: {
        "enabled": False, "threshold": 2, "auto_quarantine": False
    })
    ai: Dict[str, Any] = field(default_factory=lambda: {
        "enabled": "auto", "backend": "onnxruntime",
        "model_path": "models/nsfw_small.onnx"
    })
    similarity: Dict[str, Any] = field(default_factory=lambda: {"dim": 16})
    logging: Dict[str, Any] = field(default_factory=lambda: {
        "rotate_mb": 10, "keep": 7, "level": "INFO"
    })

    # Export settings
    export_folder_meta: bool = True
    meta_format: str = "nodupe_meta_v1"
    meta_pretty: bool = False
    meta_validate_schema: bool = True

    # Dependencies
    auto_install_deps: bool = True

    # Plugins
    plugins_dir: Optional[str] = None

    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.parallelism < 0:
            raise ValueError("parallelism must be >= 0")

    def get(self, key: str, default: Any = None) -> Any:
        """Dict-like access for backwards compatibility."""
        return getattr(self, key, default)

    def __getitem__(self, key: str) -> Any:
        """Dict-like access for backwards compatibility."""
        if hasattr(self, key):
            return getattr(self, key)
        raise KeyError(key)

    def __contains__(self, key: str) -> bool:
        """Dict-like 'in' check."""
        return hasattr(self, key)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "hash_algo": self.hash_algo,
            "dedup_strategy": self.dedup_strategy,
            "parallelism": self.parallelism,
            "follow_symlinks": self.follow_symlinks,
            "dry_run": self.dry_run,
            "overwrite": self.overwrite,
            "checkpoint": self.checkpoint,
            "db_path": self.db_path,
            "log_dir": self.log_dir,
            "metrics_path": self.metrics_path,
            "ignore_patterns": list(self.ignore_patterns),
            "nsfw": dict(self.nsfw),
            "ai": dict(self.ai),
            "similarity": dict(self.similarity),
            "logging": dict(self.logging),
            "export_folder_meta": self.export_folder_meta,
            "meta_format": self.meta_format,
            "meta_pretty": self.meta_pretty,
            "meta_validate_schema": self.meta_validate_schema,
            "auto_install_deps": self.auto_install_deps,
            "plugins_dir": self.plugins_dir,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Config':
        """Create Config from dictionary.

        Args:
            data: Dictionary with config values

        Returns:
            New Config instance
        """
        # Convert ignore_patterns list to tuple for immutability
        if "ignore_patterns" in data and isinstance(data["ignore_patterns"], list):
            data = dict(data)  # Copy to avoid mutating input
            data["ignore_patterns"] = tuple(data["ignore_patterns"])

        # Filter to only known fields
        known_fields = {
            "hash_algo", "dedup_strategy", "parallelism", "follow_symlinks",
            "dry_run", "overwrite", "checkpoint", "db_path", "log_dir",
            "metrics_path", "ignore_patterns", "nsfw", "ai", "similarity",
            "logging", "export_folder_meta", "meta_format", "meta_pretty",
            "meta_validate_schema", "auto_install_deps", "plugins_dir"
        }

        filtered = {k: v for k, v in data.items() if k in known_fields}
        return cls(**filtered)
