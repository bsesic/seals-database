"""Reversible short-id codec (Crockford base32)."""

import uuid

import pytest

from core.shortid import decode, encode
from core.uuids import uuid7


def test_round_trip_uuid7():
    for _ in range(200):
        value = uuid7()
        assert decode(encode(value)) == value


def test_round_trip_edge_values():
    for value in (uuid.UUID(int=0), uuid.UUID(int=(1 << 128) - 1)):
        assert decode(encode(value)) == value


def test_encoding_length_and_charset():
    s = encode(uuid7())
    assert len(s) == 26
    assert set(s) <= set("0123456789abcdefghjkmnpqrstvwxyz")


def test_decode_is_case_insensitive():
    value = uuid7()
    s = encode(value)
    assert decode(s.upper()) == value


def test_decode_crockford_aliases():
    # i/l -> 1, o -> 0; hyphens ignored.
    assert decode("0") == decode("o")
    assert decode("1") == decode("i") == decode("l")
    base = encode(uuid7())
    assert decode(base) == decode(base[:4] + "-" + base[4:])


def test_decode_rejects_invalid_characters():
    with pytest.raises(ValueError):
        decode("not valid u!")  # 'u' is excluded, '!' invalid


def test_decode_rejects_out_of_range():
    with pytest.raises(ValueError):
        decode("z" * 27)  # 27 chars overflows 128 bits
