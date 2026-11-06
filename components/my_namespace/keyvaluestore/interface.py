"""The public interface of the keyvaluestore component.

Bases and other components depend on this protocol only, never on a
concrete implementation. The backend is chosen by the factory (or the
project's composition root), not by importing implementation modules.
"""

from typing import Protocol


class KeyValueStore(Protocol):
    """A simple string-to-string key-value store."""

    def get(self, key: str) -> str | None:
        """Return the value stored under ``key``, or None if absent or expired."""
        ...

    def set(self, key: str, value: str, ttl: int | None = None) -> None:
        """Store ``value`` under ``key``.

        If ``ttl`` is given, the entry expires (and reads as missing)
        after that many seconds.
        """
        ...

    def set_if_absent(self, key: str, value: str, ttl: int | None = None) -> bool:
        """Atomically store ``value`` under ``key`` only if no live entry exists.

        Returns True if the entry was written, False if ``key`` was already
        taken. TTL semantics match ``set``.
        """
        ...

    def delete(self, key: str) -> None:
        """Remove ``key``. Deleting a missing key is a no-op."""
        ...
