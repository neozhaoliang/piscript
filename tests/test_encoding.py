import pytest

from piscript.AsciiHex import asciihex_decode, asciihex_encode
from piscript.Bernstein import bernstein, choose, interpolate


def test_asciihex_roundtrip_and_terminator():
    encoded, size = asciihex_encode(b"\x00\x11\xff")
    assert size == 3
    assert asciihex_decode(encoded + ">ignored") == (b"\x00\x11\xff", 7)
    assert asciihex_decode(" A B C >more") == (bytes.fromhex("abc0"), 8)
    with pytest.raises(ValueError):
        asciihex_decode("QZ>")


def test_bernstein_endpoint_and_empty_points():
    assert choose(5, 2) == 10
    assert bernstein([4, 9, 16], 0) == 4
    assert bernstein([4, 9, 16], 1) == 16
    assert interpolate([0, 1], [1, 0], 0.5) == [0.5, 0.5]
    with pytest.raises(ValueError):
        bernstein([], 0.5)
