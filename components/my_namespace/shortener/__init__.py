"""Public surface of the shortener component.

Consumers (bases, other components) use these functions only; nothing here
knows about a concrete key-value backend.
"""

from my_namespace.shortener.codes import generate_code
from my_namespace.shortener.core import CodeCollisionError, ShortenedUrl, resolve, shorten
from my_namespace.shortener.validation import InvalidUrlError, validate_url

__all__ = [
    "CodeCollisionError",
    "InvalidUrlError",
    "ShortenedUrl",
    "generate_code",
    "resolve",
    "shorten",
    "validate_url",
]
