"""
Tests for the Redis cache layer.
All tests mock the Redis client so no live Redis instance is needed.
"""
import json
import sys
import os
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Patch config before importing cache so DATABASE_URL doesn't need to exist
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

import cache  # noqa: E402


def _mock_client(get_return=None, setex_raises=None):
    client = MagicMock()
    client.get.return_value = get_return
    if setex_raises:
        client.setex.side_effect = setex_raises
    return client


def test_get_cached_returns_none_on_miss():
    with patch.object(cache, "get_client", return_value=_mock_client(get_return=None)):
        result = cache.get_cached("missing:key")
    assert result is None


def test_get_cached_returns_dict_on_hit():
    payload = {"predicted_return": 0.0012, "horizon_days": 1}
    with patch.object(cache, "get_client", return_value=_mock_client(get_return=json.dumps(payload))):
        result = cache.get_cached("hit:key")
    assert result == payload


def test_get_cached_returns_none_on_redis_error():
    import redis as redis_lib
    client = _mock_client()
    client.get.side_effect = redis_lib.RedisError("connection refused")
    with patch.object(cache, "get_client", return_value=client):
        result = cache.get_cached("any:key")
    assert result is None


def test_set_cached_calls_setex():
    client = _mock_client()
    payload = {"predicted_return": 0.005}
    with patch.object(cache, "get_client", return_value=client):
        cache.set_cached("some:key", payload)
    client.setex.assert_called_once()
    args = client.setex.call_args[0]
    assert args[0] == "some:key"
    assert json.loads(args[2]) == payload


def test_set_cached_swallows_redis_error():
    import redis as redis_lib
    client = _mock_client(setex_raises=redis_lib.RedisError("timeout"))
    with patch.object(cache, "get_client", return_value=client):
        # Should not raise
        cache.set_cached("any:key", {"x": 1})


def test_set_cached_uses_configured_ttl():
    client = _mock_client()
    with patch.object(cache, "get_client", return_value=client):
        cache.set_cached("ttl:key", {"v": 1})
    ttl_arg = client.setex.call_args[0][1]
    assert ttl_arg == cache.CACHE_TTL_SECONDS
