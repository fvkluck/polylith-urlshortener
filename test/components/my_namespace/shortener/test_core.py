"""Orchestration tests for shorten/resolve against the in-memory port fake.

These run without redis and without mocks: the InMemoryStore stands in for
the port, exactly as in production wiring with a different adapter.
"""

import random

import pytest

from my_namespace import shortener
from my_namespace.keyvaluestore.memory import InMemoryStore


class ScriptedRng(random.Random):
    """Yields a scripted character sequence, so codes are predictable."""

    def __init__(self, chars: str) -> None:
        super().__init__()
        self._chars = iter(chars)

    def choice(self, seq):  # type: ignore[override]
        return next(self._chars)


def test_shorten_stores_url_and_returns_code() -> None:
    store = InMemoryStore()
    result = shortener.shorten(store, "https://example.com")
    assert store.get(result.code) == "https://example.com"
    assert result.url == "https://example.com"


def test_shorten_then_resolve_round_trips() -> None:
    store = InMemoryStore()
    result = shortener.shorten(store, "https://example.com/some/path")
    assert shortener.resolve(store, result.code) == "https://example.com/some/path"


def test_shorten_is_deterministic_with_injected_rng() -> None:
    store_a = InMemoryStore()
    store_b = InMemoryStore()
    url = "https://example.com"
    code_a = shortener.shorten(store_a, url, rng=random.Random(99)).code
    code_b = shortener.shorten(store_b, url, rng=random.Random(99)).code
    assert code_a == code_b


def test_shorten_retries_on_collision() -> None:
    store = InMemoryStore()
    store.set("AAAAAAA", "https://already-taken.example.com")
    # first attempt collides with AAAAAAA, second lands on BBBBBBB
    result = shortener.shorten(
        store,
        "https://example.com",
        rng=ScriptedRng("AAAAAAABBBBBBB"),
    )
    assert result.code == "BBBBBBB"
    assert store.get("BBBBBBB") == "https://example.com"


def test_code_collision_error_after_max_retries() -> None:
    store = InMemoryStore()
    store.set("AAAAAAA", "https://already-taken.example.com")
    rng = ScriptedRng("AAAAAAA" * 10)
    with pytest.raises(shortener.CodeCollisionError, match="4 attempts"):
        shortener.shorten(store, "https://example.com", rng=rng)


def test_shorten_propagates_invalid_url() -> None:
    store = InMemoryStore()
    with pytest.raises(shortener.InvalidUrlError, match="scheme"):
        shortener.shorten(store, "ftp://example.com")
    assert store._data == {}


def test_shorten_uses_custom_code_length() -> None:
    store = InMemoryStore()
    result = shortener.shorten(store, "https://example.com", code_length=11)
    assert len(result.code) == 11


def test_resolve_unknown_code_returns_none() -> None:
    assert shortener.resolve(InMemoryStore(), "missing") is None
