"""Three-dimensional rendering regressions."""

from types import SimpleNamespace

import numpy as np
import pytest

from piscript.PiScript3d import PiScript3d, SmoothConvexSurface


class FakeSurfaceFace:
    p = ((0, 0, 0), (1, 0, 0), (0, 1, 0))

    def is_visible(self, eye):
        return True

    def shade_factor(self, angle):
        return 1


class FakeSurfaceDevice:
    def __init__(self):
        self.batch_sizes = []

    def get_eye(self):
        return (0, 0, 1, 0)

    def get_light(self):
        return (0, 0, 1, 0)

    def transform2d(self, position):
        return (position[0], position[1])

    def shfill(self, data):
        self.batch_sizes.append(len(data))


def test_smooth_surface_uses_all_batches_and_default_color():
    surface = SmoothConvexSurface([FakeSurfaceFace()] * 1030)
    device = FakeSurfaceDevice()
    surface.paint(device)
    assert device.batch_sizes == [1024, 6]
    assert surface.color == [1, 1, 1]


def test_closepath3d_does_not_apply_matrix_twice():
    renderer = PiScript3d.__new__(PiScript3d)
    renderer.lm = np.array([1., 2., 3., 1.])
    renderer.gstack3d = [[[2, 0, 0, 0], [0, 2, 0, 0],
                          [0, 0, 2, 0], [0, 0, 0, 1]]]
    renderer.closepath = lambda: None
    renderer.closepath3d()
    assert np.allclose(renderer.cpt, renderer.lm)
    assert np.allclose(renderer.cpt, [1, 2, 3, 1])


def test_closepath3d_without_moveto_raises():
    renderer = PiScript3d.__new__(PiScript3d)
    renderer.lm = None
    with pytest.raises(ValueError, match="subpath"):
        renderer.closepath3d()
