"""InMemoryStore-specific behaviour (TTL via the monotonic clock)."""

from my_namespace.keyvaluestore import memory


def test_ttl_expires_key(monkeypatch) -> None:
    store = memory.InMemoryStore()
    now = {"t": 1000.0}
    monkeypatch.setattr(memory.time, "monotonic", lambda: now["t"])

    store.set("key", "value", ttl=30)
    now["t"] += 29
    assert store.get("key") == "value"
    now["t"] += 2
    assert store.get("key") is None


def test_expired_key_is_removed_from_underlying_dict(monkeypatch) -> None:
    store = memory.InMemoryStore()
    monkeypatch.setattr(memory.time, "monotonic", lambda: 1000.0)
    store.set("key", "value", ttl=10)
    store.get("gone")  # no expiry triggered here
    monkeypatch.setattr(memory.time, "monotonic", lambda: 2000.0)
    assert store.get("key") is None
    assert "key" not in store._data


def test_entry_without_ttl_never_expires(monkeypatch) -> None:
    store = memory.InMemoryStore()
    monkeypatch.setattr(memory.time, "monotonic", lambda: 1000.0)
    store.set("key", "value")
    monkeypatch.setattr(memory.time, "monotonic", lambda: 1e9)
    assert store.get("key") == "value"


def test_set_if_absent_treats_expired_entry_as_free(monkeypatch) -> None:
    store = memory.InMemoryStore()
    now = {"t": 1000.0}
    monkeypatch.setattr(memory.time, "monotonic", lambda: now["t"])
    assert store.set_if_absent("key", "first", ttl=10) is True
    now["t"] += 11  # the first entry expired
    assert store.set_if_absent("key", "second") is True
    assert store.get("key") == "second"


def test_set_if_absent_forwards_ttl(monkeypatch) -> None:
    store = memory.InMemoryStore()
    now = {"t": 1000.0}
    monkeypatch.setattr(memory.time, "monotonic", lambda: now["t"])
    assert store.set_if_absent("key", "value", ttl=30) is True
    now["t"] += 31
    assert store.get("key") is None
