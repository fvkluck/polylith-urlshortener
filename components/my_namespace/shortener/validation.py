"""URL validation for the shortener component. Pure, no I/O."""

from urllib.parse import urlparse

MAX_URL_LENGTH = 2048
ALLOWED_SCHEMES = ("http", "https")


class InvalidUrlError(ValueError):
    """Raised when a URL cannot be shortened."""

    def __init__(self, url: str, reason: str) -> None:
        self.url = url
        self.reason = reason
        super().__init__(f"Invalid URL ({reason}): {url!r}")


def validate_url(url: str) -> str:
    """Return the trimmed URL if valid, otherwise raise InvalidUrlError."""
    url = url.strip()
    if not url:
        raise InvalidUrlError(url, "URL is empty")
    if len(url) > MAX_URL_LENGTH:
        raise InvalidUrlError(url, f"URL is longer than {MAX_URL_LENGTH} characters")
    parsed = urlparse(url)
    if parsed.scheme not in ALLOWED_SCHEMES:
        raise InvalidUrlError(url, f"scheme must be one of {ALLOWED_SCHEMES}")
    if not parsed.netloc:
        raise InvalidUrlError(url, "host is missing")
    return url
