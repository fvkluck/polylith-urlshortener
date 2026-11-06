"""Shortener orchestration: the functional core of the URL shortener.

All I/O goes through the injected ``KeyValueStore`` port (the keyvaluestore
component's interface). The functions here take and return plain data, so
they are testable without mocks — an InMemoryStore suffices.
"""

import random
from dataclasses import dataclass

from my_namespace.keyvaluestore.interface import KeyValueStore
from my_namespace.shortener import codes, validation

# Number of times a colliding code is regenerated before giving up.
MAX_COLLISION_RETRIES = 3


class CodeCollisionError(RuntimeError):
    """Raised when a unique code could not be generated after retries."""


@dataclass(frozen=True)
class ShortenedUrl:
    code: str
    url: str


def shorten(
    store: KeyValueStore,
    url: str,
    *,
    code_length: int = codes.DEFAULT_CODE_LENGTH,
    rng: random.Random | None = None,
) -> ShortenedUrl:
    """Validate ``url`` and store it under a fresh code.

    ``rng`` may be injected for deterministic testing; defaulting to a fresh
    ``random.Random`` keeps this component free of global mutable state.
    Each call produces a new code even for a repeated URL.
    """
    url = validation.validate_url(url)
    rng = rng if rng is not None else random.Random()
    for _ in range(MAX_COLLISION_RETRIES + 1):
        code = codes.generate_code(rng, code_length)
        if store.get(code) is None:
            store.set(code, url)
            return ShortenedUrl(code=code, url=url)
    raise CodeCollisionError(
        f"Could not find a free {code_length}-character code after "
        f"{MAX_COLLISION_RETRIES + 1} attempts"
    )


def resolve(store: KeyValueStore, code: str) -> str | None:
    """Return the URL stored under ``code``, or None if unknown."""
    return store.get(code)
