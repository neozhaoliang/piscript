"""Regression tests for independent arrow configurations and DVI movement."""

from types import SimpleNamespace

from piscript.Arrows import (
    _get_dims,
    _unpack_arrow_args,
    arrow,
    setarrowdims,
)
from piscript.Canvas import Canvas
from piscript.DviReader import DviReader


def test_arrow_endpoints_and_canvas_local_dimensions():
    assert _unpack_arrow_args((1, 2, 3, 4)) == (1, 2, 3, 4)
    assert _unpack_arrow_args(((1, 2), (3, 4))) == (1, 2, 3, 4)
    first = Canvas()
    second = Canvas()
    setarrowdims(first, 2, 6)
    setarrowdims(second, 4, 12)
    assert _get_dims(first).sw == 2
    assert _get_dims(second).sw == 4
    first.newpath()
    arrow(first, 1, 2, 30, 40)
    assert first.cmd


def test_dvi_w0_reuses_scaled_value():
    reader = DviReader.__new__(DviReader)
    reader.scaleFactor = 3
    reader.w = 0
    reader.h = 0
    command = SimpleNamespace(b=10)
    reader.execW(command)
    assert reader.w == 30
    assert reader.h == 30
    reader.execW0(command)
    assert reader.h == 60
