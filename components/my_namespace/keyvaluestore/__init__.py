"""Public surface of the keyvaluestore component.

``RedisStore`` is intentionally not re-exported here: importing it would
pull in the redis client for every consumer. Use ``create_store()``
instead; reach for ``my_namespace.keyvaluestore.redis`` only in the
composition root (and in tests).
"""

from my_namespace.keyvaluestore.factory import create_store
from my_namespace.keyvaluestore.interface import KeyValueStore
from my_namespace.keyvaluestore.memory import InMemoryStore

__all__ = ["KeyValueStore", "InMemoryStore", "create_store"]
