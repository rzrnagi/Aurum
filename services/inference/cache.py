import json
import redis
from config import REDIS_URL, CACHE_TTL_SECONDS

_client: redis.Redis | None = None


def get_client() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.from_url(REDIS_URL, decode_responses=True)
    return _client


def get_cached(key: str) -> dict | None:
    try:
        val = get_client().get(key)
        return json.loads(val) if val else None
    except redis.RedisError:
        return None


def set_cached(key: str, value: dict) -> None:
    try:
        get_client().setex(key, CACHE_TTL_SECONDS, json.dumps(value))
    except redis.RedisError:
        pass  # cache is best-effort — never block a prediction
