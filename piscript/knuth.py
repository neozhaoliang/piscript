"""Read DVI binary data using struct -- Knuth's byte conventions.

Uses Python's built-in struct module instead of manual bit-shifting.
All integers in DVI files are big-endian.
"""

import struct

_FMT_SIGNED = {1: ">b", 2: ">h", 3: ">i", 4: ">i"}
_FMT_UNSIGNED = {1: ">B", 2: ">H", 3: ">I", 4: ">I"}
_PAD = {1: b"", 2: b"", 3: b"\x00", 4: b""}


def getInt(f, k):
    return struct.unpack(_FMT_SIGNED[k], _PAD[k] + f.read(k))[0]


def getUnsigned(f, k):
    return struct.unpack(_FMT_UNSIGNED[k], _PAD[k] + f.read(k))[0]


def getWord(f):
    return struct.unpack(">I", f.read(4))[0]


def getString(f, n):
    return f.read(n).decode("ascii")


# Backward-compatible namespace
class knuth:
    getInt = staticmethod(getInt)
    getUnsigned = staticmethod(getUnsigned)
    getWord = staticmethod(getWord)
    getString = staticmethod(getString)
