# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

import hashlib
from pathlib import Path

CHUNK = 1024 * 1024  # 1MB

SUPPORTED_HASH_ALGOS = {"sha512", "sha256", "blake2b", "sha1", "md5"}


def validate_hash_algo(algo: str) -> str:
    algo = algo.lower().strip()
    if algo not in SUPPORTED_HASH_ALGOS:
        raise ValueError(
            f"Unsupported hash algorithm: '{algo}'. "
            f"Supported: {', '.join(sorted(SUPPORTED_HASH_ALGOS))}"
        )
    return algo


def hash_file(p: Path, algo: str = "sha512") -> str:
    """Compute hash of file using specified algorithm."""
    if algo == "sha512":
        h = hashlib.sha512()
    elif algo == "sha256":
        h = hashlib.sha256()
    elif algo == "blake2b":
        h = hashlib.blake2b()
    elif algo == "sha1":
        h = hashlib.sha1()
    elif algo == "md5":
        h = hashlib.md5()
    else:
        h = hashlib.sha512()

    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()
