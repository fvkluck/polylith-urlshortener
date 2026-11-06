"""CLI shell tests: shell and one-shot modes against an injected store.

No mocking needed: an injected InMemoryStore replaces the composition root
and a scripted input_fn replaces stdin.
"""

import pytest

from my_namespace.keyvaluestore.memory import InMemoryStore
from my_namespace.urlshortener_cli import main

URL = "https://example.com/some/long/path"


@pytest.fixture
def store() -> InMemoryStore:
    return InMemoryStore()


# --- one-shot mode (unchanged behaviour) ---


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


def test_unknown_command_is_usage_error(store: InMemoryStore) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["bogus"], store=store)
    # argparse convention: 2 for usage errors
    assert exc_info.value.code == 2


def test_main_without_store_uses_kv_backend_default(monkeypatch) -> None:
    monkeypatch.delenv("KV_BACKEND", raising=False)
    # goes through the factory like the console script does
    assert main(["resolve", "whatever"]) == 1


# --- interactive shell mode ---


def make_input(store: InMemoryStore, lines: list) -> object:
    """Input fn over scripted lines; each entry is a line or a callable
    that derives the next line from the store (e.g. an earlier code)."""
    it = iter(lines)

    def input_fn(_prompt: str) -> str:
        item = next(it)
        return item(store) if callable(item) else item

    return input_fn


def test_shell_round_trips_within_one_session(store: InMemoryStore, capsys) -> None:
    # second command derives the code from what shorten actually wrote
    commands = [
        f"shorten {URL}",
        lambda s: f"resolve {next(iter(s._data))}",
        "quit",
    ]
    exit_code = main([], store=store, input_fn=make_input(store, commands))
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "http://localhost:8000/" in out
    assert URL in out  # printed by resolve in the same session


def test_shell_persists_multiple_shortens_in_one_store(store: InMemoryStore, capsys) -> None:
    commands = [
        "shorten https://first.example.com",
        "shorten https://second.example.com",
        lambda s: f"resolve {sorted(s._data)[0]}",
        "quit",
    ]
    exit_code = main([], store=store, input_fn=make_input(store, commands))
    out = capsys.readouterr().out
    assert exit_code == 0
    assert len(store._data) == 2
    assert "https://first.example.com" in out or "https://second.example.com" in out


def test_shell_banner_names_the_backend(store: InMemoryStore, capsys) -> None:
    main([], store=store, input_fn=make_input(store, ["quit"]))
    out = capsys.readouterr().out
    assert "urlshortener shell — backend: InMemoryStore" in out
    assert "commands:" in out


def test_shell_quit_exits_zero(store: InMemoryStore) -> None:
    assert main([], store=store, input_fn=make_input(store, ["quit"])) == 0


def test_shell_eof_exits_zero(store: InMemoryStore, capsys) -> None:
    def eof_input(_prompt: str) -> str:
        raise EOFError

    assert main([], store=store, input_fn=eof_input) == 0
    assert "bye" not in capsys.readouterr().out


def test_shell_continues_after_usage_error(store: InMemoryStore, capsys) -> None:
    commands = ["bogus command", f"shorten {URL}", "quit"]
    exit_code = main([], store=store, input_fn=make_input(store, commands))
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "usage:" in captured.err  # argparse complained, but the shell survived
    assert captured.out.count("http://localhost:8000/") == 1  # and still shortened


def test_shell_error_command_prints_error_but_keeps_session(store: InMemoryStore, capsys) -> None:
    commands = ["resolve missing", "quit"]
    exit_code = main([], store=store, input_fn=make_input(store, commands))
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "unknown code" in captured.err


def test_shell_help_lists_commands(store: InMemoryStore, capsys) -> None:
    commands = ["help", "quit"]
    main([], store=store, input_fn=make_input(store, commands))
    out = capsys.readouterr().out
    assert "shorten <url>" in out
    assert "resolve <code>" in out
