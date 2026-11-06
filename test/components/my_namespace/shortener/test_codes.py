"""Pure logic tests for code generation."""

import random

import pytest

from my_namespace.shortener import codes


def test_code_has_requested_length() -> None:
    code = codes.generate_code(random.Random(1), length=11)
    assert len(code) == 11


def test_code_uses_base62_alphabet_only() -> None:
    code = codes.generate_code(random.Random(2), length=200)
    assert all(char in codes.BASE62_ALPHABET for char in code)


def test_seeded_rng_is_deterministic() -> None:
    first = codes.generate_code(random.Random(42))
    second = codes.generate_code(random.Random(42))
    assert first == second


def test_lengths_default_to_seven() -> None:
    assert codes.DEFAULT_CODE_LENGTH == 7


def test_random_codes_are_unique_in_bulk() -> None:
    rng = random.Random(3)
    codes_generated = {codes.generate_code(rng) for _ in range(1000)}
    assert len(codes_generated) == 1000


@pytest.mark.parametrize("bad_length", [0, -1])
def test_nonpositive_length_raises(bad_length: int) -> None:
    with pytest.raises(ValueError, match="positive"):
        codes.generate_code(random.Random(4), length=bad_length)
