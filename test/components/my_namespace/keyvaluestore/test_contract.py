"""Contract tests: behaviour every KeyValueStore implementation must provide.

Both implementations run the same suite, so they stay interchangeable —
which is what makes the later move to separate implementation components
 cheap.
"""

import pytest

from my_namespace.keyvaluestore import memory
from my_namespace.keyvaluestore.interface import KeyValueStore


def _make_redis_store() -> KeyValueStore:
    import fakeredis

    from my_namespace.keyvaluestore import redis as redis_impl

    # fake redis services the client protocol, so no server is needed here
    return redis_impl.RedisStore(client=fakeredis.FakeRedis(decode_responses=True))


@pytest.fixture(params=["memory", "redis"])
def store(request: pytest.FixtureRequest) -> KeyValueStore:
    if request.param == "memory":
        return memory.InMemoryStore()
    return _make_redis_store()


def test_set_then_get(store: KeyValueStore) -> None:
    store.set("greeting", "hello")
    assert store.get("greeting") == "hello"


def test_get_missing_key_returns_none(store: KeyValueStore) -> None:
    assert store.get("missing") is None


def test_set_overwrites_existing_value(store: KeyValueStore) -> None:
    store.set("key", "first")
    store.set("key", "second")
    assert store.get("key") == "second"


def test_delete_removes_key(store: KeyValueStore) -> None:
    store.set("key", "value")
    store.delete("key")
    assert store.get("key") is None


def test_delete_missing_key_is_noop(store: KeyValueStore) -> None:
    store.delete("missing")


def test_set_if_absent_writes_free_key(store: KeyValueStore) -> None:
    assert store.set_if_absent("key", "value") is True
    assert store.get("key") == "value"


def test_set_if_absent_rejects_taken_key(store: KeyValueStore) -> None:
    store.set("key", "original")
    assert store.set_if_absent("key", "other") is False
    assert store.get("key") == "original"


def test_set_if_absent_is_claimable_again_after_delete(store: KeyValueStore) -> None:
    store.set("key", "value")
    store.delete("key")
    assert store.set_if_absent("key", "new") is True
    assert store.get("key") == "new"
