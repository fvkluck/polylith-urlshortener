"""Redis-backed implementation, used outside local development.

``decode_responses=True`` keeps ``get()`` returning ``str`` so both
implementations satisfy the same interface contract.
"""

from redis import Redis


class RedisStore:
    def __init__(self, client: Redis | None = None, url: str = "redis://localhost:6379/0") -> None:
        self._client = client if client is not None else Redis.from_url(url, decode_responses=True)

    def get(self, key: str) -> str | None:
        return self._client.get(key)

    def set(self, key: str, value: str, ttl: int | None = None) -> None:
        self._client.set(key, value, ex=ttl)

    def delete(self, key: str) -> None:
        self._client.delete(key)
