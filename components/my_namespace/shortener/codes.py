"""Short code generation for the shortener component.

Pure logic: randomness is injected (an ``random.Random`` instance) so tests
are deterministic and the composition root owns entropy.
"""

import random

BASE62_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"

# 62^7 ≈ 3.5 * 10^12 possible codes; overridable via generate_code(length=...)
DEFAULT_CODE_LENGTH = 7


def generate_code(rng: random.Random, length: int = DEFAULT_CODE_LENGTH) -> str:
    """Generate a random base62 code of exactly ``length`` characters."""
    if length <= 0:
        raise ValueError(f"length must be positive, got {length}")
    return "".join(rng.choice(BASE62_ALPHABET) for _ in range(length))
