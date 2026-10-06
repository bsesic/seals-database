"""UUIDv7 generation (RFC 9562).

UUIDv7 is time-ordered: the first 48 bits are a Unix millisecond timestamp,
so keys sort by creation time. That gives us index-friendly primary keys and
stable, externally-safe identifiers to back public resource IRIs, without the
index fragmentation of random UUIDv4. The Python standard library has no
``uuid.uuid7`` on this runtime, so we assemble one here.
"""

import os
import time
import uuid


def uuid7() -> uuid.UUID:
    """Return a new version-7 UUID (time-ordered)."""
    unix_ts_ms = int(time.time() * 1000) & ((1 << 48) - 1)
    rand_a = int.from_bytes(os.urandom(2), "big") & 0x0FFF  # 12 bits
    rand_b = int.from_bytes(os.urandom(8), "big") & ((1 << 62) - 1)  # 62 bits

    value = unix_ts_ms << 80          # 48-bit timestamp
    value |= 0x7 << 76                # version 7
    value |= rand_a << 64             # 12 random bits
    value |= 0b10 << 62              # RFC 4122 variant
    value |= rand_b                   # 62 random bits
    return uuid.UUID(int=value)
