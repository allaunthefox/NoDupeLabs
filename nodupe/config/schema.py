# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Configuration schema definition.

Defines the structure and validation rules for NoDupeLabs configuration.
Uses dataclasses for immutability with frozen=True.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class HashAlgorithm(Enum):
    """Supported content hashing algorithms used for deduplication.

    Use these values when configuring the project's default hashing
    algorithm. They map to algorithm identifiers emitted in manifest
    metadata (e.g. "sha512").
    """
    SHA256 = "sha256"
    SHA512 = "sha512"
    BLAKE2B = "blake2b"


class DedupStrategy(Enum):
    """Strategies used to select which files are kept when duplicates are
    discovered.
    """
    CONTENT_HASH = "content_hash"


@dataclass(frozen=True)
class NSFWConfig:
    """Configuration options for NSFW detection and automatic handling.

    Fields:
        enabled: Whether NSFW classification is enabled.
        threshold: Score threshold for classifying content as NSFW.
        auto_quarantine: Whether to move or quarantine NSFW files automatically.
    """
    enabled: bool = False
    threshold: int = 2
    auto_quarantine: bool = False


@dataclass(frozen=True)
class AIConfig:
    """Configuration for AI/ML backends used by the application.

    Fields:
        enabled: Controls whether AI features are used ('auto', 'true', 'false').
        backend: Preferred backend name (e.g., 'onnxruntime').
        model_path: Default location of the model artifact.
    """
    enabled: str = "auto"  # "auto", "true", "false"
    backend: str = "onnxruntime"
    model_path: str = "models/nsfw_small.onnx"


@dataclass(frozen=True)
class SimilarityConfig:
    """Configuration related to similarity indexing.

    Fields:
        dim: Dimensionality of numeric embeddings used by similarity indices.
    """
    dim: int = 16


@dataclass(frozen=True)
class LoggingConfig:
    """Logging-related configuration values.

    Fields:
        rotate_mb: Maximum MB per rotated log file.
        keep: Number of rotated log files to retain.
        level: Logging level (e.g., 'INFO', 'DEBUG').
    """
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
        """Retrieve a configuration value using dict-like semantics.

        This method mirrors the behaviour of ``dict.get`` for backwards
        compatibility with older call-sites that treat the configuration
        object like a mapping.

        Args:
            key: Name of the configuration attribute to retrieve.
            default: Value to return when the attribute is not present.

        Returns:
            The attribute value when present, otherwise ``default``.
        """
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
        """Create a JSON-serializable mapping of the configuration.

        Returns:
            A dictionary containing all configuration values. Nested
            datatypes are converted to plain Python containers (eg. tuples
            -> lists, nested dict-like fields preserved as dicts) so the
            result is safe to serialize to YAML/JSON.
        """
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
        if ("ignore_patterns" in data
                and isinstance(data["ignore_patterns"], list)):
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
