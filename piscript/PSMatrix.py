"""Affine transform utilities for PostScript six-component matrices."""


def _point(args):
    if len(args) == 1:
        return args[0]
    if len(args) == 2:
        return args
    raise TypeError("expected a point or two coordinates")


def transform(tm, *args):
    """Transform a point, including translation."""
    x, y = _point(args)
    return [tm[0] * x + tm[2] * y + tm[4], tm[1] * x + tm[3] * y + tm[5]]


def rtransform(tm, *args):
    """Transform a vector, ignoring translation."""
    x, y = _point(args)
    return [tm[0] * x + tm[2] * y, tm[1] * x + tm[3] * y]


def concat(a, b):
    """Compose transforms: apply b, then a."""
    return [
        a[0] * b[0] + a[2] * b[1],
        a[1] * b[0] + a[3] * b[1],
        a[0] * b[2] + a[2] * b[3],
        a[1] * b[2] + a[3] * b[3],
        a[0] * b[4] + a[2] * b[5] + a[4],
        a[1] * b[4] + a[3] * b[5] + a[5],
    ]


def lconcat(a, b):
    """Compose just the linear portions of transforms."""
    return concat([*a[:4], 0, 0], [*b[:4], 0, 0])[:4]
