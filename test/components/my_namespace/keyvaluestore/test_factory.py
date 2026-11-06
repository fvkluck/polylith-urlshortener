"""Factory behaviour: backend selection via argument or environment."""

import pytest

from my_namespace.keyvaluestore import factory
from my_namespace.keyvaluestore import memory as memory_impl
from my_namespace.keyvaluestore import redis as redis_impl


def test_defaults_to_memory(monkeypatch) -> None:
    monkeypatch.delenv("KV_BACKEND", raising=False)
    assert isinstance(factory.create_store(), memory_impl.InMemoryStore)


def test_kv_backend_env_var_selects_backend(monkeypatch) -> None:
    monkeypatch.setenv("KV_BACKEND", "memory")
    assert isinstance(factory.create_store(), memory_impl.InMemoryStore)


def test_explicit_backend_overrides_env_var(monkeypatch) -> None:
    monkeypatch.setenv("KV_BACKEND", "memory")
    store = factory.create_store("redis")
    assert isinstance(store, redis_impl.RedisStore)


def test_redis_uses_kv_redis_url(monkeypatch) -> None:
    monkeypatch.setenv("KV_REDIS_URL", "redis://kv.example.com:6380/2")
    store = factory.create_store("redis")
    pool = store._client.connection_pool
    assert pool.connection_kwargs["host"] == "kv.example.com"
    assert pool.connection_kwargs["port"] == 6380
    assert pool.connection_kwargs["db"] == 2


def test_unknown_backend_raises(monkeypatch) -> None:
    monkeypatch.delenv("KV_BACKEND", raising=False)
    with pytest.raises(ValueError, match="Unknown keyvaluestore backend: 'memcached'"):
        factory.create_store("memcached")
