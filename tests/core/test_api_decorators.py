import time
import warnings
from unittest.mock import Mock

import pytest

from nodupe.core.api import decorators as dec


def test_api_endpoint_decorator_preserves_call():
    @dec.api_endpoint(['GET'])
    def f(x):
        return x * 2

    assert f(3) == 6


def test_cors_adds_header_on_dict_return():
    @dec.cors(origins=["https://a"])
    def respond():
        return {"ok": True}

    out = respond()
    assert out["ok"] is True
    assert "_cors" in out
    assert "Access-Control-Allow-Origin" in out["_cors"]


def test_require_auth_raises_without_token_and_passes_with_token():
    @dec.require_auth
    def secured(**kwargs):
        return "ok"

    with pytest.raises(PermissionError):
        secured()

    assert secured(auth_TOKEN_REMOVED="token") == "ok"
    assert secured(authorization="token") == "ok"


def test_cache_response_caches_and_respects_ttl(monkeypatch):
    calls = {"n": 0}

    @dec.cache_response(ttl=1)
    def expensive(x):
        calls["n"] += 1
        return x

    assert expensive(1) == 1
    assert expensive(1) == 1
    # function executed only once because result cached
    assert calls["n"] == 1

    # advance time beyond TTL
    monkeypatch.setattr("time.time", lambda: time.time() + 2)
    assert expensive(1) == 1
    assert calls["n"] == 2


def test_retry_retries_on_exception(monkeypatch):
    seq = {"c": 0}

    @dec.retry(max_attempts=3, delay=0)
    def flaky():
        seq["c"] += 1
        if seq["c"] < 3:
            raise ValueError("fail")
        return "ok"

    assert flaky() == "ok"

    @dec.retry(max_attempts=2, delay=0)
    def always_fail():
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        always_fail()


def test_deprecated_emits_warning():
    @dec.deprecated("use new")
    def old():
        return 1

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        assert old() == 1
        assert any("use new" in str(x.message) for x in w)
