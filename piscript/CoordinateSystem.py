"""Affine coordinate system using PostScript's [a, b, c, d, tx, ty] order."""

import math

from piscript.PSMatrix import concat, lconcat, rtransform, transform


class CoordinateSystem:
    def transform(self, *args):
        return transform(self.tm, *args)

    def rtransform(self, *args):
        return rtransform(self.tm, *args)

    def inversetm(self):
        a, b, c, d, tx, ty = self.tm
        det = a * d - b * c
        if det == 0:
            raise ValueError("cannot invert a singular affine transform")
        return [
            d / det, -b / det, -c / det, a / det,
            (c * ty - d * tx) / det,
            (b * tx - a * ty) / det,
        ]

    def itransform(self, *args):
        return transform(self.inversetm(), *args)

    def atransform(self, matrix):
        self.tm[:] = concat(self.tm, matrix)

    def ltransform(self, matrix):
        self.tm[:4] = lconcat(self.tm, matrix)

    def translate(self, *args):
        if len(args) == 1:
            x, y = args[0]
        elif len(args) == 2:
            x, y = args
        else:
            raise TypeError("translate expects a point or x, y")
        a, b, c, d, tx, ty = self.tm
        self.tm[4] = tx + a * x + c * y
        self.tm[5] = ty + b * x + d * y

    def scale(self, *args):
        if len(args) == 1:
            sx = sy = float(args[0])
        elif len(args) == 2:
            sx, sy = map(float, args)
        else:
            raise TypeError("scale expects one or two scale factors")
        self.tm[0] *= sx
        self.tm[1] *= sx
        self.tm[2] *= sy
        self.tm[3] *= sy

    def rotate(self, angle):
        sine, cosine = math.sin(angle), math.cos(angle)
        a, b, c, d = self.tm[:4]
        self.tm[:4] = [
            a * cosine + c * sine,
            b * cosine + d * sine,
            c * cosine - a * sine,
            d * cosine - b * sine,
        ]
