# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from .deps import check_dep

def get_schema() -> Dict[str, Any]:
    p = Path(__file__).parent / "schemas" / "nodupe_meta_v1.schema.json"
    return json.loads(p.read_text(encoding="utf-8"))

def validate_meta_dict(meta: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Validate metadata dictionary against schema."""
    spec = meta.get("spec")
    if spec != "nodupe_meta_v1":
        return False, f"Invalid spec: {spec}"

    # Try jsonschema validation
    if check_dep("jsonschema"):
        try:
            from jsonschema import Draft202012Validator, ValidationError
            Draft202012Validator(get_schema()).validate(meta)
            return True, None
        except ValidationError as e:
            return False, str(e)
        except Exception as e:
            return False, str(e)

    # Fallback: structural checks
    try:
        assert isinstance(meta, dict), "meta must be object"
        assert "entries" in meta, "missing entries"
        assert isinstance(meta["entries"], list), "entries must be list"

        for entry in meta["entries"]:
            assert "file_hash" in entry, "missing file_hash"
            assert "hash_algo" in entry, "missing hash_algo"
            h = entry["file_hash"]
            assert 32 <= len(h) <= 128, f"hash length invalid: {len(h)}"

        return True, None
    except AssertionError as e:
        return False, str(e)
