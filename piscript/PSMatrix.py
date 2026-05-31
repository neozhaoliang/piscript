"""Affine transform utilities for 2D matrices (6-element lists [a,b,c,d,tx,ty])."""


def transform(tm, *args):
    if len(args) == 2:
        x, y = args
    else:
        x, y = args[0]
    return [tm[0] * x + tm[2] * y + tm[4], tm[1] * x + tm[3] * y + tm[5]]


def rtransform(tm, *args):
    if len(args) == 2:
        x, y = args
    else:
        x, y = args[0]
    return [tm[0] * x + tm[2] * y, tm[1] * x + tm[3] * y]


def concat(a, b):
    return [
        a[0] * b[0] + a[2] * b[1],
        a[1] * b[0] + a[3] * b[1],
        a[0] * b[2] + a[2] * b[3],
        a[1] * b[2] + a[3] * b[3],
        a[0] * b[4] + a[2] * b[5] + a[4],
        a[1] * b[4] + a[3] * b[5] + a[5],
    ]


def lconcat(a, b):
    return [
        a[0] * b[0] + a[2] * b[1],
        a[1] * b[0] + a[3] * b[1],
        a[0] * b[2] + a[2] * b[3],
        a[1] * b[2] + a[3] * b[3],
    ]
