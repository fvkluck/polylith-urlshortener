"""Enables ``python -m my_namespace.urlshortener_cli``."""

import sys

from my_namespace.urlshortener_cli.core import main

if __name__ == "__main__":
    sys.exit(main())
