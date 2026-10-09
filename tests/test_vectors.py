import math

import numpy as np
import pytest

from piscript.VectorUtils import Vec2, Vec3, Vec5, Vector, angle_between, length


def test_angle_and_norm():
    assert angle_between([1, 0], [-1, 0]) == pytest.approx(math.pi)
    assert length([]) == 0
    assert length([3, 4]) == 5
    with pytest.raises(ValueError):
        angle_between([0, 0], [1, 0])


def test_vector_ufuncs_and_inplace_update():
    value = Vec2(1, 2)
    value += Vec2(3, 4)
    assert isinstance(value, Vec2)
    assert value.tolist() == [4, 6]
    assert isinstance(np.sin(value), Vec2)
    assert np.add.reduce(value) == 10
    assert isinstance(Vec2(3, 4) + Vec2(1, 1), Vec2)


def test_vector_swizzles_and_dimensions():
    value = Vec5(1, 2, 3, 4, 5)
    assert value.v == 5
    assert value.xy.tolist() == [1, 2]
    value.yx = [8, 7]
    assert value.tolist() == [7, 8, 3, 4, 5]
    with pytest.raises(ValueError):
        Vec3([1, 2])
    with pytest.raises(ValueError):
        Vector([[1, 2], [3, 4]])
