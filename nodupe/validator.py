# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""JSON Schema validation for nodupe_meta_v1 manifests.

This module validates metadata dictionaries against the nodupe_meta_v1
JSON Schema specification. Provides both strict JSON Schema validation
(when jsonschema library available) and fallback structural validation.

Validation Strategy:
    1. Check spec field matches 'nodupe_meta_v1'
    2. If jsonschema available: Full JSON Schema Draft 2020-12 validation
    3. Otherwise: Fallback to basic structural assertions

Fallback Validation Checks:
    - meta is dict
    - entries field exists and is list
    - Each entry has file_hash and hash_algo
    - Hash length between 32-128 characters

Key Features:
    - Strict schema compliance when jsonschema available
    - Graceful degradation to structural checks
    - Clear error messages with validation details
    - Two-phase validation (spec check + schema/structure)

Dependencies:
    - json: Schema file loading
    - pathlib: Schema file path resolution
    - jsonschema (optional): Full JSON Schema validation
        - Falls back to structural checks if unavailable

Example:
    >>> meta = {
    ...     'spec': 'nodupe_meta_v1',
    ...     'generated_at': '2025-12-03T14:30:00Z',
    ...     'summary': {'files_total': 1, 'bytes_total': 1024},
    ...     'entries': [
    ...         {'name': 'file.txt', 'file_hash': 'abc123...',
    ...          'hash_algo': 'sha512'}
    ...     ]
    ... }
    >>> valid, error = validate_meta_dict(meta)
    >>> print(valid)
    True
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from .deps import check_dep


def get_schema() -> Dict[str, Any]:
    """Load nodupe_meta_v1 JSON Schema from schemas directory.

    Returns:
        Dict containing JSON Schema specification (Draft 2020-12)

    Example:
        >>> schema = get_schema()
        >>> print(schema['$schema'])
        'https://json-schema.org/draft/2020-12/schema'
    """
    p = Path(__file__).parent / "schemas" / "nodupe_meta_v1.schema.json"
    return json.loads(p.read_text(encoding="utf-8"))


def validate_meta_dict(meta: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Validate metadata dictionary against nodupe_meta_v1 schema.

    Performs two-phase validation:
    1. Checks spec field matches 'nodupe_meta_v1'
    2. Validates structure using JSON Schema (if available) or
       fallback structural assertions

    Args:
        meta: Metadata dictionary to validate, expected to contain:
            - spec: Schema version (must be 'nodupe_meta_v1')
            - generated_at: ISO 8601 timestamp
            - summary: Aggregate statistics dict
            - entries: List of file entry dicts

    Returns:
        Tuple of (valid, error_message):
            - valid: True if validation passed, False otherwise
            - error_message: None if valid, error string if invalid

    Raises:
        No exceptions raised. All errors returned via tuple.

    Validation Methods:
        - With jsonschema: Full JSON Schema Draft 2020-12 validation
        - Without jsonschema: Basic structural assertions
            - meta is dict
            - entries exists and is list
            - Each entry has file_hash (32-128 chars) and hash_algo

    Example:
        >>> meta = {'spec': 'nodupe_meta_v1', 'entries': [
        ...     {'file_hash': 'a' * 64, 'hash_algo': 'sha512'}
        ... ]}
        >>> valid, err = validate_meta_dict(meta)
        >>> print(valid)
        True
        >>> invalid = {'spec': 'wrong_version'}
        >>> valid, err = validate_meta_dict(invalid)
        >>> print(err)
        Invalid spec: wrong_version
    """
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
        except (OSError, ValueError, ImportError) as e:
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
