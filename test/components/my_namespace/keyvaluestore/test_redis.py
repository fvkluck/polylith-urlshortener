"""RedisStore-specific behaviour (TTL is forwarded to the server)."""

import fakeredis

from my_namespace.keyvaluestore import redis as redis_impl


def test_set_with_ttl_expires_key() -> None:
    store = redis_impl.RedisStore(client=fakeredis.FakeRedis(decode_responses=True))
    store.set("key", "value", ttl=42)
    assert 0 < store._client.ttl("key") <= 42
    assert store.get("key") == "value"
