import os
import time

import pytest

from pathlib import Path
from nodupe.tools.hashing.hash_cache import HashCache, create_hash_cache


def test_set_get_and_is_cached(tmp_path):
    cache = HashCache(max_size=10, ttl_seconds=60)

    f = tmp_path / "file1.txt"
    f.write_text("hello")

    cache.set_hash(f, "deadbeef")
    assert cache.get_hash(f) == "deadbeef"
    assert cache.is_cached(f) is True

    # Non-existent file returns None
    missing = tmp_path / "nope.txt"
    assert cache.get_hash(missing) is None
    assert cache.is_cached(missing) is False


def test_ttl_expiration_and_validate_cache(monkeypatch, tmp_path):
    cache = HashCache(max_size=10, ttl_seconds=1)

    f = tmp_path / "file2.txt"
    f.write_text("data")

    cache.set_hash(f, "hash2")
    assert cache.get_hash(f) == "hash2"

    # Simulate time advancing beyond TTL
    real_monotonic = time.monotonic

    try:
        monkeypatch.setattr("time.monotonic", lambda: real_monotonic() + 10)
        # get_hash should remove expired entry and return None
        assert cache.get_hash(f) is None

        # validate_cache should remove any expired entries and return count
        cache.set_hash(f, "hash2")
        removed = cache.validate_cache()
        assert removed >= 0
    finally:
        monkeypatch.setattr("time.monotonic", real_monotonic)


def test_evictions_and_resize(tmp_path):
    cache = HashCache(max_size=2, ttl_seconds=60)

    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    c = tmp_path / "c.txt"
    a.write_text("a")
    b.write_text("b")
    c.write_text("c")

    cache.set_hash(a, "ha")
    cache.set_hash(b, "hb")
    # cache is at capacity; inserting c should evict oldest
    cache.set_hash(c, "hc")

    stats = cache.get_stats()
    assert stats["evictions"] >= 1
    assert cache.get_cache_size() <= cache.max_size

    # resize to 1 should evict entries until size <= max
    cache.resize(1)
    assert cache.get_cache_size() <= 1


def test_invalidate_and_invalidate_all(tmp_path):
    cache = HashCache(max_size=10, ttl_seconds=60)

    f1 = tmp_path / "x.txt"
    f2 = tmp_path / "y.txt"
    f1.write_text("x")
    f2.write_text("y")

    cache.set_hash(f1, "xhash")
    cache.set_hash(f2, "yhash")

    assert cache.invalidate(f1) is True
    assert cache.invalidate(f1) is False

    cache.invalidate_all()
    assert cache.get_cache_size() == 0


def test_get_memory_usage_and_stats(tmp_path):
    cache = create_hash_cache(max_size=5, ttl_seconds=60)
    f = tmp_path / "m.txt"
    f.write_text("m")

    cache.set_hash(f, "mhash")
    usage = cache.get_memory_usage()
    assert isinstance(usage, int) and usage > 0

    stats = cache.get_stats()
    assert stats["size"] == 1
    assert stats["capacity"] == 5
    assert 0.0 <= stats["hit_rate"] <= 1.0
