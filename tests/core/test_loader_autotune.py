import logging
from unittest.mock import Mock, patch

import pytest

from nodupe.core.loader import CoreLoader


class DummyContainer:
    def __init__(self):
        self.services = {}

    def register_service(self, name, svc):
        self.services[name] = svc

    def get_service(self, name):
        return self.services.get(name)


class SimpleHasher:
    def __init__(self):
        self.algo_set = None

    def set_algorithm(self, a):
        self.algo_set = a

    def hash_file(self, p):
        return "deadbeef"


def test_create_autotuned_hasher_registers_hasher_and_results():
    loader = CoreLoader()
    loader.container = DummyContainer()

    dummy_hasher = SimpleHasher()
    autotune_results = {"optimal_algorithm": "sha3-256"}

    with patch("nodupe.core.loader.create_autotuned_hasher", return_value=(dummy_hasher, autotune_results)):
        # ensure autotune helper isn't None
        loader._perform_hash_autotuning()

    assert loader.container.get_service("hasher") is dummy_hasher
    assert loader.container.get_service("hash_autotune_results") == autotune_results


def test_autotune_results_configures_existing_hasher():
    loader = CoreLoader()
    c = DummyContainer()
    loader.container = c

    existing = SimpleHasher()
    c.register_service("hasher", existing)

    with patch("nodupe.core.loader.autotune_hash_algorithm", return_value={"optimal_algorithm": "sha512"}), patch(
        "nodupe.core.loader.create_autotuned_hasher", new=None
    ):
        loader._perform_hash_autotuning()

    assert c.get_service("hash_autotune_results")["optimal_algorithm"] == "sha512"
    assert existing.algo_set == "sha512"


def test_no_helpers_registers_fallback_file_hasher():
    loader = CoreLoader()
    loader.container = DummyContainer()

    # ensure both helpers are absent
    with patch("nodupe.core.loader.autotune_hash_algorithm", new=None), patch(
        "nodupe.core.loader.create_autotuned_hasher", new=None
    ):
        loader._perform_hash_autotuning()

    hasher = loader.container.get_service("hasher")
    assert hasher is not None
    # basic behavior check
    assert hasattr(hasher, "hash_file")
    assert loader.container.get_service("hash_autotune_results") == {}


def test_autotune_exception_logs_and_registers_fallback(caplog):
    loader = CoreLoader()
    loader.container = DummyContainer()

    # make autotune raise to exercise outer except path
    with patch("nodupe.core.loader.autotune_hash_algorithm", side_effect=Exception("boom")):
        caplog.set_level(logging.ERROR)
        loader._perform_hash_autotuning()

    assert "Hash autotuning failed" in caplog.text or "autotuning failed" in caplog.text.lower()
    assert loader.container.get_service("hasher") is not None
