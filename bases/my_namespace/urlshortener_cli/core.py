"""CLI shell for the URL shortener.

The second consumer of the shortener component (next to the HTTP base),
proving the functional core is shell-agnostic: here the store comes from
the keyvaluestore factory ($KV_BACKEND), same wiring as the API service.

Called without arguments, the CLI opens an interactive shell that keeps
one store alive across commands. That makes the in-memory backend usable
for demos: shortened URLs stay resolvable until the session ends.
"""

import argparse
import shlex
import sys
from collections.abc import Callable

from my_namespace import shortener
from my_namespace.keyvaluestore import create_store
from my_namespace.keyvaluestore.interface import KeyValueStore

DEFAULT_BASE_URL = "http://localhost:8000"

SHELL_HINTS = """commands:
  shorten <url> [--base-url URL]   shorten a URL, prints the short URL
  resolve <code>                   print the original URL
  help                             show these commands
  quit / Ctrl-D                    leave the shell"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="urlshortener",
        description="Shorten URLs and resolve short codes using the configured key-value backend.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    shorten = subparsers.add_parser("shorten", help="Shorten a URL, prints the short URL")
    shorten.add_argument("url", help="The URL to shorten")
    shorten.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"Public base URL of the shortener (default: {DEFAULT_BASE_URL})",
    )

    resolve = subparsers.add_parser("resolve", help="Resolve a short code, prints the original URL")
    resolve.add_argument("code", help="The short code to resolve")

    return parser


def _dispatch(args: argparse.Namespace, store: KeyValueStore) -> int:
    """Run one parsed command; returns the exit code for one-shot mode."""
    if args.command == "shorten":
        try:
            result = shortener.shorten(store, args.url)
        except (shortener.InvalidUrlError, shortener.CodeCollisionError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        base_url = args.base_url.rstrip("/")
        print(f"{base_url}/{result.code}")
        return 0

    url = shortener.resolve(store, args.code)
    if url is None:
        print(f"error: unknown code: {args.code}", file=sys.stderr)
        return 1
    print(url)
    return 0


def run_shell(store: KeyValueStore, input_fn: Callable[[str], str] = input) -> int:
    """Interactive mode: parse a line per iteration against the same store."""
    print(f"urlshortener shell — backend: {type(store).__name__}")
    print(SHELL_HINTS)
    while True:
        try:
            line = input_fn("" if not sys.stdin.isatty() else "urlshortener> ").strip()
        except EOFError:
            print()
            return 0
        except KeyboardInterrupt:
            print("\nbye")
            return 130
        if not line:
            continue
        first = line.split()[0].lower()
        if first in ("quit", "exit", "q"):
            return 0
        if first in ("help", "?"):
            print(SHELL_HINTS)
            continue
        try:
            # parse only this line; argparse prints usage errors itself
            args = build_parser().parse_args(shlex.split(line))
        except SystemExit:
            continue
        # one-shot exit codes don't end the session; errors are already printed
        _dispatch(args, store)


def main(
    argv: list[str] | None = None,
    store: KeyValueStore | None = None,
    input_fn: Callable[[str], str] = input,
) -> int:
    """Run the CLI. Returns the process exit code.

    ``store`` (and ``input_fn``) are injectable so tests run against an
    InMemoryStore without touching env vars or stdin; the keyvaluestore
    factory ($KV_BACKEND) is the composition root otherwise. No arguments
    means: open the interactive shell.
    """
    args_list = sys.argv[1:] if argv is None else list(argv)
    store = store if store is not None else create_store()
    if not args_list:
        return run_shell(store, input_fn=input_fn)
    return _dispatch(build_parser().parse_args(args_list), store)
