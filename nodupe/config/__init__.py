# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Configuration management for NoDupeLabs.

This package provides the configuration loading functionality.

Public API:
    - Config: Immutable configuration dataclass
    - load_config: Load configuration from file
    - ensure_config: Create default config file if needed
    - get_available_presets: List available presets
"""
from pathlib import Path
from typing import Any, Dict

from .schema import Config
from .presets import PRESETS, get_preset, get_available_presets

try:
    import yaml
except ImportError:
    import json

    class _YAMLShim:
        class YAMLError(Exception):
            """Raised when the YAML/JSON parsing shim encounters an error.

            This mirrors PyYAML's YAMLError to provide compatible behaviour when
            PyYAML is not installed and a lightweight JSON-based shim is used.
            """

        @staticmethod
        def safe_load(text: str):
            """Parse YAML/JSON text in a safe manner for environments without
            PyYAML.

            Args:
                text: YAML or JSON text to parse

            Returns:
                Parsed Python object (typically a dict)
            """
            try:
                return json.loads(text)
            except json.JSONDecodeError as e:
                raise _YAMLShim.YAMLError(e)

        @staticmethod
        def safe_dump(obj: Any, sort_keys: bool = False) -> str:
            """Serialize a Python object to YAML/JSON text.

            This shim uses JSON formatting when PyYAML is unavailable.
            """
            return json.dumps(
                obj, sort_keys=sort_keys, ensure_ascii=False, indent=2
            )
    yaml = _YAMLShim()  # type: ignore[assignment]


def ensure_config(path: str = "nodupe.yml", preset: str = "default") -> None:
    """Write a default configuration file when no config exists.

    The function uses the named preset (from `PRESETS`) to populate an
    initial configuration at `path`. If the file already exists the
    function is a no-op.

    Args:
        path: Filesystem path where the configuration should be created.
        preset: Name of the preset to use when generating the default
            configuration.
    """
    p = Path(path)
    if not p.exists():
        # Fallback to default locations if explicit path not found
        cfg = PRESETS.get(preset, PRESETS["default"])
        p.write_text(
            f"# Auto-generated config using '{preset}' preset. "
            f"Edit as needed.\n"
            + yaml.safe_dump(cfg.to_dict(), sort_keys=False),
            encoding="utf-8",
        )


def load_config(path: str = "nodupe.yml") -> Dict[str, Any]:
    """Load the configuration file and return it as a plain dict.

    Behavior:
        - Ensures a config file exists (via `ensure_config`).
        - Loads YAML or JSON content if present and overlays user values
          on top of the default preset values.
        - Performs runtime environment tuning when the environment helper
          is available.

    Args:
        path: Path to the configuration file to load.

    Returns:
        A plain dictionary containing the merged configuration values.
    """
    ensure_config(path)
    p = Path(path)

    # Start with defaults
    cfg = PRESETS["default"].to_dict()

    if p.exists():
        try:
            data = yaml.safe_load(p.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                cfg.update(data)
        except (yaml.YAMLError, OSError) as e:
            print(f"[config][WARN] Failed to load {path}: {e}")

    # Apply environment auto-tuning
    try:
        from ..environment import Environment
        env = Environment()
        cfg = env.apply_to_config(cfg)
    except (ImportError, OSError, ValueError) as e:
        print(f"[config][WARN] Environment detection failed: {e}")

    return cfg


def load_config_object(path: str = "nodupe.yml") -> Config:
    """Load configuration and convert it into a `Config` instance.

    Args:
        path: Path to the configuration file to load.

    Returns:
        An immutable `Config` instance representing the loaded
        configuration.
    """
    cfg_dict = load_config(path)
    return Config.from_dict(cfg_dict)


__all__ = [
    "Config",
    "load_config",
    "load_config_object",
    "ensure_config",
    "get_available_presets",
    "get_preset",
    "PRESETS",
]
