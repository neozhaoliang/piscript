"""Compatibility regressions for the legacy public API."""

from piscript import PiModule
from piscript.Canvas import Canvas
from piscript.PiScript3d import Face


def test_exported_functions_are_available():
    assert "moveto" in PiModule.__all__
    assert callable(PiModule.arc)
    assert callable(PiModule.ArcArrow)


def test_face_copy_does_not_share_geometry():
    face = Face([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
    duplicate = Face(face)
    duplicate.p[0][0] = 10
    assert face.p[0][0] == 0
    duplicate.setnormal([0, 0, -1, 0])
    assert duplicate.nf == [0, 0, -1, 0]
    assert face.nf != duplicate.nf


def test_canvas_mode_selector():
    canvas = Canvas()
    canvas.setmode(1)
    assert canvas.toRad > 0
    canvas.setmode(0)
    assert canvas.toRad == 1
