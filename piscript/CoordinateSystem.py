import numpy as np
from piscript.PSMatrix import transform as _pstransform, concat, lconcat

import math


class CoordinateSystem:
    def transform(self, *args):
        return _pstransform(self.tm, *args)

    def rtransform(self, V):
        return _pstransform(self.tm[:4] + [0, 0], V)

    def inversetm(self):
        m = np.array(self.tm[:4]).reshape(2, 2)
        inv = np.linalg.inv(m)
        tx, ty = -self.tm[4], -self.tm[5]
        return [inv[0, 0], inv[0, 1], inv[1, 0], inv[1, 1],
                inv[0, 0] * tx + inv[0, 1] * ty,
                inv[1, 0] * tx + inv[1, 1] * ty]

    def itransform(self, P):
        return _pstransform(self.inversetm(), P[0], P[1])

    def atransform(self, b):
        self.tm[:] = concat(self.tm, b)

    def ltransform(self, b):
        self.tm[:4] = lconcat(self.tm, b)

    def translate(self, *args):
        if len(args) == 1:
            x, y = args[0]
        else:
            x, y = args
        t = self.tm
        t[4] += x * t[0] + y * t[2]
        t[5] += x * t[1] + y * t[3]

    def scale(self, *args):
        if len(args) == 1:
            a = b = float(args[0])
        else:
            a, b = float(args[0]), float(args[1])
        t = self.tm
        t[0] *= a; t[1] *= a; t[2] *= b; t[3] *= b

    def rotate(self, A):
        c, s = math.cos(A), math.sin(A)
        t = self.tm
        t[0], t[2] = t[0] * c + t[2] * s, -t[0] * s + t[2] * c
        t[1], t[3] = t[1] * c + t[3] * s, -t[1] * s + t[3] * c
