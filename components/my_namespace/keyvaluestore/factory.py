"""Backend selection for the keyvaluestore component.

Only the composition root (project entry point or a base) should call
``create_store()``; everything else depends on the ``KeyValueStore``
protocol it returns.
"""

import os

from my_namespace.keyvaluestore.interface import KeyValueStore
from my_namespace.keyvaluestore.memory import InMemoryStore

DEFAULT_REDIS_URL = "redis://localhost:6379/0"


def create_store(backend: str | None = None, redis_url: str | None = None) -> KeyValueStore:
    """Create a store for ``backend``, defaulting to $KV_BACKEND or "memory".

    The redis implementation is imported lazily, so environments that only
    use the in-memory backend do not need the redis client installed.
    """
    backend = backend or os.environ.get("KV_BACKEND", "memory")
    if backend == "memory":
        return InMemoryStore()
    if backend == "redis":
        from my_namespace.keyvaluestore import redis as redis_impl

        url = redis_url or os.environ.get("KV_REDIS_URL", DEFAULT_REDIS_URL)
        return redis_impl.RedisStore(url=url)
    raise ValueError(f"Unknown keyvaluestore backend: {backend!r}")
