"""Core numerical and drawing regressions; no TeX installation required."""

import math

import pytest

from piscript.Arc import arc, circle
from piscript.Canvas import Canvas, NoCurrentPoint
from piscript.Cmd import CLOSEPATH, CURVETO, MOVETO, Skip
from piscript.Graphics import Graphics, GraphicsState
from piscript.PSMatrix import concat, rtransform, transform


def commands(canvas):
    cursor = 0
    while cursor < len(canvas.cmd):
        opcode = canvas.cmd[cursor]
        yield opcode, canvas.cmd[cursor + 1:cursor + Skip[opcode]]
        cursor += Skip[opcode]


def test_affine_matrix_and_inverse():
    state = GraphicsState()
    state.translate(2, -3)
    state.rotate(math.pi / 3)
    matrix = state.tm
    point = (4, 5)
    transformed = transform(matrix, point)
    assert state.itransform(transformed) == pytest.approx(point)
    assert rtransform(matrix, point) == pytest.approx(
        [transformed[0] - matrix[4], transformed[1] - matrix[5]]
    )
    assert concat(matrix, state.inversetm()) == pytest.approx([1, 0, 0, 1, 0, 0])


def test_singular_inverse():
    with pytest.raises(ValueError, match="singular"):
        GraphicsState([1, 0, 0, 0, 0, 0]).inversetm()


def test_graphics_state_isolation():
    graphics = Graphics()
    graphics.setcolor([1, 0, 0])
    graphics.setdash([2, 3], 1)
    graphics.setlinejoin(2)
    graphics.setmiterlimit(5)
    graphics.gsave()
    graphics.setcolor([0, 0, 1])
    graphics.setdash([9], 0)
    graphics.grestore()
    assert graphics.currentcolor() == [1, 0, 0]
    assert graphics.currentdash() == [[2, 3], 1]
    assert graphics.currentlinejoin() == 2
    assert graphics.currentmiterlimit() == 5
    snapshot = graphics.cgs()
    snapshot.color[0] = 0
    snapshot.dash[0].append(99)
    assert graphics.currentcolor() == [1, 0, 0]
    assert graphics.currentdash() == [[2, 3], 1]


def test_linear_transform_does_not_mutate_argument():
    graphics = Graphics()
    matrix = [2, 0, 0, 3]
    graphics.ltransform(matrix)
    assert matrix == [2, 0, 0, 3]
    assert graphics.ctm() == [2, 0, 0, 3, 0, 0]
    graphics.ltransform([1, 0], [0, 1])


def test_relative_path_and_clone():
    canvas = Canvas()
    canvas.newpath()
    canvas.moveto(1, 2)
    canvas.rlineto(3, 4)
    assert canvas.currentpoint() == pytest.approx((4, 6))
    clone = canvas.clone()
    clone.m[0] = 3
    assert canvas.m[0] == 1
    canvas.newpath()
    with pytest.raises(NoCurrentPoint):
        canvas.lineto(2, 3)


def test_circle_in_both_angular_modes():
    for mode in (0, 1):
        canvas = Canvas()
        canvas.setmode(mode)
        canvas.newpath()
        circle(canvas, (2, 3), 5)
        operations = list(commands(canvas))
        assert sum(op == CURVETO for op, _ in operations) == 4
        assert sum(op == CLOSEPATH for op, _ in operations) == 1
        first = next(payload for op, payload in operations if op == MOVETO)
        assert first == pytest.approx([7, 3])
        curves = [payload for op, payload in operations if op == CURVETO]
        assert curves[-1][-2:] == pytest.approx([7, 3], abs=1e-10)


def test_arc_zero_radius_and_invalid_arguments():
    canvas = Canvas()
    canvas.newpath()
    arc(canvas, 0, 0, math.pi)
    assert sum(op == CURVETO for op, _ in commands(canvas)) == 0
    with pytest.raises(ValueError):
        arc(canvas, -1, 0, math.pi)
    with pytest.raises(TypeError):
        arc(canvas, 1, 2)
