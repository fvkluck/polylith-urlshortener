"""Pure validation tests."""

import pytest

from my_namespace.shortener.validation import InvalidUrlError, validate_url


@pytest.mark.parametrize(
    "url",
    [
        "http://example.com",
        "https://example.com/path?query=1#frag",
        "  https://example.com/with-whitespace  ",
    ],
)
def test_valid_urls_pass(url: str) -> None:
    assert validate_url(url) == url.strip()


@pytest.mark.parametrize(
    ("url", "reason"),
    [
        ("ftp://example.com", "scheme"),
        ("javascript:alert(1)", "scheme"),
        ("file:///etc/passwd", "scheme"),
        ("", "empty"),
        ("   ", "empty"),
        ("/relative/path", "scheme"),
        ("https://", "host"),
        ("http:///no-host", "host"),
    ],
)
def test_invalid_urls_raise(url: str, reason: str) -> None:
    with pytest.raises(InvalidUrlError, match=reason):
        validate_url(url)


def test_overlong_urls_are_rejected() -> None:
    url = "https://example.com/" + "a" * 3000
    with pytest.raises(InvalidUrlError, match="longer than"):
        validate_url(url)


def test_error_carries_original_url_and_reason() -> None:
    with pytest.raises(InvalidUrlError) as exc_info:
        validate_url("ftp://example.com")
    assert exc_info.value.url == "ftp://example.com"
    assert "scheme" in exc_info.value.reason
