"""In-memory reference implementation, used for local development.

Keys live in a plain dict with monotonic-clock expiry deadlines. State is
process-local and not guaranteed thread-safe; it exists so that local
development and tests can run without a Redis server.
"""

import time

_Entry = tuple[str, float | None]  # (value, expires_at with time.monotonic())


class InMemoryStore:
    def __init__(self) -> None:
        self._data: dict[str, _Entry] = {}

    def get(self, key: str) -> str | None:
        entry = self._data.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if expires_at is not None and time.monotonic() >= expires_at:
            self._data.pop(key, None)
            return None
        return value

    def set(self, key: str, value: str, ttl: int | None = None) -> None:
        expires_at = time.monotonic() + ttl if ttl is not None else None
        self._data[key] = (value, expires_at)

    def delete(self, key: str) -> None:
        self._data.pop(key, None)
