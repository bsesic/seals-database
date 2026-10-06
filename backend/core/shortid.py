"""Reversible short ids for UUIDs (Crockford base32).

A record's primary key is a UUIDv7 (see ``core.uuids``). For public resource
IRIs we want something shorter and friendlier than the 36-char canonical form,
but still *reversible* — the id in the IRI must decode straight back to the
UUID so the resource resolves without a lookup table (5-star Linked Open Data).

Crockford base32 is used: case-insensitive, URL-safe, and it omits the easily
confused letters I, L, O and U. A 128-bit UUID encodes to 26 characters.
"""

import uuid

# Crockford base32 alphabet (no I, L, O, U).
_ALPHABET = "0123456789abcdefghjkmnpqrstvwxyz"
_DECODE = {c: i for i, c in enumerate(_ALPHABET)}
# Crockford decode aliases for visually similar characters.
_DECODE.update({"i": 1, "l": 1, "o": 0})

_LENGTH = 26  # ceil(128 / 5)


def encode(value: uuid.UUID) -> str:
    """Encode a UUID as a 26-character Crockford base32 string."""
    n = value.int
    chars = []
    for _ in range(_LENGTH):
        n, rem = divmod(n, 32)
        chars.append(_ALPHABET[rem])
    return "".join(reversed(chars))


def decode(text: str) -> uuid.UUID:
    """Decode a Crockford base32 short id back to a UUID.

    Case-insensitive; hyphens are ignored. Raises ``ValueError`` on an invalid
    character or an out-of-range value.
    """
    n = 0
    for ch in text.strip().lower():
        if ch == "-":
            continue
        try:
            n = n * 32 + _DECODE[ch]
        except KeyError:
            raise ValueError(f"invalid short id character: {ch!r}")
    if n >= 1 << 128:
        raise ValueError("short id out of range")
    return uuid.UUID(int=n)
