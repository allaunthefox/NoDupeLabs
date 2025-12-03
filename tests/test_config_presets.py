import os
import tempfile
from pathlib import Path
from nodupe.config import ensure_config, PRESETS
import yaml

def test_ensure_config_presets():
    with tempfile.TemporaryDirectory() as td:
        cwd = Path.cwd()
        try:
            os.chdir(td)
            
            # Test default
            ensure_config("nodupe.yml", preset="default")
            with open("nodupe.yml") as f:
                cfg = yaml.safe_load(f)
            assert cfg["hash_algo"] == "sha512"
            os.unlink("nodupe.yml")
            
            # Test performance
            ensure_config("nodupe.yml", preset="performance")
            with open("nodupe.yml") as f:
                cfg = yaml.safe_load(f)
            assert cfg["hash_algo"] == "blake2b"
            assert cfg["meta_validate_schema"] is False
            os.unlink("nodupe.yml")
            
            # Test media
            ensure_config("nodupe.yml", preset="media")
            with open("nodupe.yml") as f:
                cfg = yaml.safe_load(f)
            assert cfg["ai"]["enabled"] is True
            assert cfg["similarity"]["dim"] == 64
            
        finally:
            os.chdir(cwd)
