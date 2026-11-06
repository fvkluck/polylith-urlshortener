"""CLI shell for the URL shortener.

The second consumer of the shortener component (next to the HTTP base),
proving the functional core is shell-agnostic: here the store comes from
the keyvaluestore factory ($KV_BACKEND), same wiring as the API service.
"""

import argparse
import sys

from my_namespace import shortener
from my_namespace.keyvaluestore import create_store
from my_namespace.keyvaluestore.interface import KeyValueStore

DEFAULT_BASE_URL = "http://localhost:8000"


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


def main(argv: list[str] | None = None, store: KeyValueStore | None = None) -> int:
    """Run the CLI. Returns the process exit code.

    ``store`` is injectable so tests run against an InMemoryStore; the
    keyvaluestore factory ($KV_BACKEND) is the composition root otherwise.
    """
    args = build_parser().parse_args(argv)
    store = store if store is not None else create_store()

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
