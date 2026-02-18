import time
import warnings
from unittest.mock import Mock

import pytest

from nodupe.core.api import decorators as api_decorators


def test_api_endpoint_preserves_function_metadata_and_return():
    @api_decorators.api_endpoint(methods=["GET"])
    def hello(name: str) -> str:
        """Return greeting"""
        return f"hi {name}"

    assert hello("you") == "hi you"
    assert hello.__name__ == "hello"
    assert "Return greeting" in hello.__doc__


def test_cors_adds_headers_for_dict_response_and_uses_default_origin():
    @api_decorators.cors()
    def produce() -> dict:
        return {"ok": True}

    res = produce()
    assert "_cors" in res
    assert res["_cors"]["Access-Control-Allow-Origin"] == "*"


def test_cors_joins_allowed_origins_and_leaves_non_dict_untouched():
    @api_decorators.cors(origins=["https://a.example", "https://b.example"])
    def p() -> dict:
        return {"status": "ok"}

    out = p()
    assert ", ".join(["https://a.example", "https://b.example"]) in out["_cors"]["Access-Control-Allow-Origin"]

    @api_decorators.cors()
    def plain() -> str:
        return "ok"

    assert plain() == "ok"


def test_require_auth_enforces_authorization_kwarg():
    @api_decorators.require_auth
    def protected(**kwargs):
        return True

    with pytest.raises(PermissionError):
        protected()

    assert protected(auth_TOKEN_REMOVED="secret") is True
    # also accept 'authorization' key
    assert protected(authorization="x") is True


def test_cache_response_caches_results_within_ttl(monkeypatch):
    calls = {"n": 0}

    @api_decorators.cache_response(ttl=5)
    def f(x):
        calls["n"] += 1
        return x * 2

    assert f(2) == 4
    assert f(2) == 4
    assert calls["n"] == 1  # cached on second call


def test_retry_retries_then_succeeds_and_raises_after_exhaustion():
    state = {"count": 0}

    @api_decorators.retry(max_attempts=3, delay=0)
    def flaky():
        state["count"] += 1
        if state["count"] < 3:
            raise RuntimeError("boom")
        return "ok"

    assert flaky() == "ok"

    @api_decorators.retry(max_attempts=2, delay=0)
    def always_fail():
        raise ValueError("nope")

    with pytest.raises(ValueError):
        always_fail()


def test_deprecated_emits_warning():
    @api_decorators.deprecated("use v2")
    def old():
        return 1

    with pytest.warns(DeprecationWarning, match="use v2"):
        assert old() == 1
