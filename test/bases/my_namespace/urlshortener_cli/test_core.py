"""CLI shell tests: run main() against an injected InMemoryStore.

No mocking needed: capsys captures output, the injected store replaces the
composition root.
"""

import pytest

from my_namespace.keyvaluestore.memory import InMemoryStore
from my_namespace.urlshortener_cli import main

URL = "https://example.com/some/long/path"


@pytest.fixture
def store() -> InMemoryStore:
    return InMemoryStore()


def test_shorten_prints_short_url_with_default_base(store: InMemoryStore, capsys) -> None:
    exit_code = main(["shorten", URL], store=store)
    out = capsys.readouterr().out.strip()
    assert exit_code == 0
    code = out.rsplit("/", 1)[1]
    assert out == f"http://localhost:8000/{code}"
    assert store.get(code) == URL


def test_shorten_respects_base_url_option(store: InMemoryStore, capsys) -> None:
    exit_code = main(["shorten", URL, "--base-url", "https://s.example.com/"], store=store)
    out = capsys.readouterr().out.strip()
    assert exit_code == 0
    assert out.startswith("https://s.example.com/")  # trailing slash is stripped
    assert len(out.rsplit("/", 1)[1]) == 7


def test_shorten_then_resolve_round_trips(store: InMemoryStore, capsys) -> None:
    main(["shorten", URL], store=store)
    code = capsys.readouterr().out.strip().rsplit("/", 1)[1]
    exit_code = main(["resolve", code], store=store)
    assert exit_code == 0
    assert capsys.readouterr().out.strip() == URL


def test_resolve_unknown_code_errors(store: InMemoryStore, capsys) -> None:
    exit_code = main(["resolve", "missing"], store=store)
    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert "unknown code" in captured.err


def test_shorten_invalid_url_errors(store: InMemoryStore, capsys) -> None:
    exit_code = main(["shorten", "ftp://example.com"], store=store)
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "scheme" in captured.err
    assert store._data == {}


def test_missing_command_is_usage_error(store: InMemoryStore) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main([], store=store)
    # argparse convention: 2 for usage errors
    assert exc_info.value.code == 2


def test_main_without_store_uses_kv_backend_default(monkeypatch) -> None:
    monkeypatch.delenv("KV_BACKEND", raising=False)
    # goes through the factory like the console script does
    assert main(["resolve", "whatever"]) == 1
