"""PiScript3d — 3D rendering extension for PiScript."""

from piscript.PiScript import *
from piscript.VectorUtils import Vector
import piscript.VectorUtils as VU
import numpy as np
import copy
from piscript.Fstr import fstr

import piscript.Bezier as Bezier
import math

import logging
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
#  Argument helpers
# ---------------------------------------------------------------------------

def _unpack_xyz(args):
    """(x, y, z) or ([x, y, z]) → (x, y, z)."""
    if len(args) == 3:
        return args[0], args[1], args[2]
    return args[0][0], args[0][1], args[0][2]


def _is_2d(args):
    """True if args represent a 2D point, not 3D."""
    return len(args) == 2 or (len(args) == 1 and len(args[0]) == 2)


# ---------------------------------------------------------------------------
#  Face
# ---------------------------------------------------------------------------

class Face:
    def __init__(self, *args):
        if isinstance(args[0], Face):
            f = args[0]
            self.p = f.p
            self.fill = f.fill
            self.nf = f.nf
            self.shading = f.shading
            self.stroke = f.stroke
            return
        if len(args) == 1:
            self.p = args[0]
            self.fill = [1, 1, 1]
        else:
            self.p = args[0]
            self.fill = args[1]
        self.stroke = [0, 0, 0]
        self.nf = self.normalfunction(self.p)
        self.shading = PiScript3d.default_shading
        self.extras = list(args[2:])

    def setshading(self, y):    self.shading = y

    def shade_factor(self, s):
        return Bezier.bernstein(self.shading, (s + 1) / 2.0)

    def setnormal(self, nf):    self.f[1] = nf
    def setfill(self, c):       self.fill = c
    def setstroke(self, c):     self.stroke = c

    def reversed(self):
        f = Face(self)
        f.nf = [-f.nf[0], -f.nf[1], -f.nf[2], -f.nf[3]]
        return f

    def isvisible(self, e):
        return sum(e[i] * self.nf[i] for i in range(4)) >= 0

    def is_visible(self, e):
        return self.isvisible(e)

    def outline(self, ps, *args):
        c = args[0] if args else self.stroke
        p = self.p
        ps.newpath()
        ps.moveto3d(p[-1][0], p[-1][1], p[-1][2])
        for pt in p:
            ps.lineto3d(pt[0], pt[1], pt[2])
        ps.closepath3d()
        ps.stroke(c)

    def paint(self, ps, *args):
        c = args[0] if args else self.fill
        p = self.p
        ps.newpath()
        ps.moveto3d(p[-1][0], p[-1][1], p[-1][2])
        for pt in p:
            ps.lineto3d(pt[0], pt[1], pt[2])
        ps.closepath3d()
        L = ps.get_light(); nf = self.nf
        s = L[0] * nf[0] + L[1] * nf[1] + L[2] * nf[2]
        s = Bezier.bernstein(self.shading, (s + 1.0) / 2)
        ps.fill(s * c[0], s * c[1], s * c[2])

    def display(self):
        logger.debug(f"face: {self.p}, {self.nf}")

    @staticmethod
    def normalfunction(p):
        u, v, w = p[0], p[1], p[2]
        a = [v[0] - u[0], v[1] - u[1], v[2] - u[2]]
        b = [w[0] - v[0], w[1] - v[1], w[2] - v[2]]
        c = VU.x(a, b)
        r = math.hypot(c[0], c[1], c[2])
        c[0] /= r; c[1] /= r; c[2] /= r
        return [c[0], c[1], c[2], -(c[0] * u[0] + c[1] * u[1] + c[2] * u[2])]

    @staticmethod
    def reverse_array(p):
        return list(reversed(p))


# ---------------------------------------------------------------------------
#  Surfaces
# ---------------------------------------------------------------------------

class SmoothConvexSurface:
    def __init__(self, f):
        self.f = f

    def paint(self, ps):
        e = ps.get_eye()
        l = ps.get_light()
        C = self.color
        n = len(self.f)
        MAX = 1024
        while n > 0:
            N = min(MAX, n)
            n -= N
            data_source = []
            for i in range(N):
                F = self.f[i]
                if F.is_visible(e):
                    t = F.p
                    a, b, c = [list(pt) + [1] for pt in t[:3]]
                    T = []
                    for v in (a, b, c):
                        sh = F.shade_factor(VU.mul(l, v))
                        u = ps.transform2d(v)
                        T.append([(u[0], u[1]),
                                   (sh * C[0], sh * C[1], sh * C[2])])
                    data_source.append(T)
            ps.shfill(data_source)


class ConvexSurface:
    def __init__(self, *args):
        if len(args) == 1:
            self.faces = args[0]
        else:
            self.faces = [Face(x, args[1]) for x in args[0]]

    def reversed(self):
        return ConvexSurface([f.reversed() for f in self.faces])

    def paint(self, ps, *args):
        for f in self.faces:
            if f.is_visible(ps.get_eye()):
                f.paint(ps, *args)

    def outline(self, ps, *args):
        for f in self.faces:
            if f.is_visible(ps.get_eye()):
                f.outline(ps, *args)

    def setshading(self, y):
        for F in self.faces:
            F.setshading(y)

    def setfill(self, c):
        for F in self.faces:
            F.setfill(c)

    def setstroke(self, c):
        for F in self.faces:
            F.setstroke(c)


# ---------------------------------------------------------------------------
#  PiScript3d
# ---------------------------------------------------------------------------

class PiScript3d(PiScript):

    default_shading = [0.4, 0.6, 0.9, 1.0]

    def __init__(self, device, *args):
        PiScript.__init__(self, device, *args)
        self.gstack3d = [
            [[[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]],
             [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]],
             [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1]]]
        ]
        L = Vector([-0.5, 1, 0.5, 0])
        self.light = L.normalized()
        self.set_eye([0, 0, 1, 0])
        self.setlinecap(1)
        self.setlinejoin(1)
        self.lm = None

    # ------------------------------------------------------------------
    #  graphics state
    # ------------------------------------------------------------------

    def gsave3d(self):
        g = self.gstack3d[-1]
        self.gstack3d.append([copy.deepcopy(g[0]), copy.deepcopy(g[1]), g[2]])

    def grestore3d(self):
        self.gstack3d.pop(-1)

    def set_eye(self, e):
        self.eye = e
        self.gstack3d[-1][2] = [
            [e[2], 0, -e[0], 0],
            [0, e[2], -e[1], 0],
            [0, 0, -e[3], e[2]],
        ]

    def get_eye(self):
        t = self.gstack3d[-1][1]
        e = self.eye
        return Vector([sum(t[i][j] * e[j] for j in range(4)) for i in range(4)])

    def homogeneous2d(self, x):
        t = self.gstack3d[-1][2]
        return [sum(t[i][j] * x[j] for j in range(4)) for i in range(3)]

    def place3d(self, t, *args):
        P = self.projectto2d(*args)
        self.place(t, P)

    def projectto2d(self, *args):
        if len(args) == 1:
            x = list(args[0]) + [1]
        else:
            x = [args[0], args[1], args[2], 1]
        x = np.dot(self.gstack3d[-1][0], x)
        P = self.display(x)
        return [P[0], P[1]]

    def display(self, x):
        t = self.gstack3d[-1][2]
        y = [sum(t[i][j] * x[j] for j in range(4)) for i in range(3)]
        return [y[0] * 1.0 / y[2], y[1] * 1.0 / y[2]]

    # ------------------------------------------------------------------
    #  coordinate transforms
    # ------------------------------------------------------------------

    def scale3d(self, *args):
        x, y, z = _unpack_xyz(args)
        t = self.gstack3d[-1][0]
        T = self.gstack3d[-1][1]
        for i in range(4):
            t[i][0] *= x; t[i][1] *= y; t[i][2] *= z
        for j in range(4):
            T[0][j] /= x * 1.0; T[1][j] /= y * 1.0; T[2][j] /= z * 1.0

    def translate3d(self, *args):
        x, y, z = _unpack_xyz(args)
        t = self.gstack3d[-1][0]
        T = self.gstack3d[-1][1]
        for i in range(4):
            t[i][3] += x * t[i][0] + y * t[i][1] + z * t[i][2]
        for j in range(4):
            T[0][j] -= x * T[3][j]
            T[1][j] -= y * T[3][j]
            T[2][j] -= z * T[3][j]

    def gfxtransform3d(self, m):
        t = self.gstack3d[-1][0]
        T = self.gstack3d[-1][1]
        p = [[sum(t[i][j] * m[j][k] for j in range(3)) for k in range(3)]
             for i in range(4)]
        for i in range(4):
            for k in range(3):
                t[i][k] = p[i][k]
        M = np.linalg.inv(np.array(m))
        p = [[sum(M[j][i] * T[j][k] for j in range(3)) for k in range(4)]
             for i in range(3)]
        for i in range(3):
            T[i] = p[i]

    def rotate3d(self, a, A):
        r = self.rotationmatrix(a, A)
        t = self.gstack3d[-1][0]
        T = self.gstack3d[-1][1]
        p = [[sum(t[i][j] * r[j][k] for j in range(3)) for k in range(3)]
             for i in range(4)]
        for i in range(4):
            for k in range(3):
                t[i][k] = p[i][k]
        p = [[sum(r[j][i] * T[j][k] for j in range(3)) for k in range(4)]
             for i in range(3)]
        for i in range(3):
            T[i] = p[i]

    def project(self, F, P):
        fP = F[0] * P[0] + F[1] * P[1] + F[2] * P[2] + F[3] * P[3]
        Fm = [
            [-fP + F[0] * P[0],  F[1] * P[0],  F[2] * P[0],  F[3] * P[0]],
            [F[0] * P[1], -fP + F[1] * P[1], -F[2] * P[1],  F[3] * P[1]],
            [F[0] * P[2],  F[1] * P[2], -fP + F[2] * P[2],  F[3] * P[2]],
            [F[0] * P[3],  F[1] * P[3],  F[2] * P[3], -fP + F[3] * P[3]],
        ]
        t = self.gstack3d[-1][0]
        self.gstack3d[-1][1] = None
        p = [[sum(t[i][j] * Fm[j][k] for j in range(4)) for k in range(4)]
             for i in range(4)]
        for i in range(4):
            for k in range(4):
                t[i][k] = p[i][k]

    # ------------------------------------------------------------------
    #  3D drawing — unified absolute / relative
    # ------------------------------------------------------------------

    def transform3d(self, v):
        return np.dot(self.gstack3d[-1][0], v)

    def transform2d(self, v):
        v = np.dot(self.gstack3d[-1][0], v)
        return self.display(v)

    def _move3d(self, args, relative=False, cmd='moveto'):
        """Unified moveto3d / rmoveto3d / lineto3d / rlineto3d."""
        a, b, c = _unpack_xyz(args)
        if relative:
            dv = np.dot(self.gstack3d[-1][0], [a, b, c, 0])
            v = [self.cpt[0] + dv[0], self.cpt[1] + dv[1],
                 self.cpt[2] + dv[2], 1]
        else:
            v = np.dot(self.gstack3d[-1][0], [a, b, c, 1])
        self.cpt = v
        if cmd == 'moveto':
            self.lm = v
        V = self.display(v)
        getattr(PiScript, cmd)(self, V[0], V[1])

    def moveto3d(self, *args):
        self._move3d(args, relative=False, cmd='moveto')

    def rmoveto3d(self, *args):
        self._move3d(args, relative=True, cmd='moveto')

    def lineto3d(self, *args):
        self._move3d(args, relative=False, cmd='lineto')

    def rlineto3d(self, *args):
        self._move3d(args, relative=True, cmd='lineto')

    def curveto3d(self, P1, P2, P3):
        cpt = self.cpt
        p0 = self.homogeneous2d([cpt[0], cpt[1], cpt[2], 1])
        p1 = np.dot(self.gstack3d[-1][0], [P1[0], P1[1], P1[2], 1])
        p1h = self.homogeneous2d(p1)
        w = 1.0 * p0[2]
        c = p1h[2] / w - 1
        x1 = p1h[0] / w - c * (p0[0] / w)
        y1 = p1h[1] / w - c * (p0[1] / w)
        p2 = np.dot(self.gstack3d[-1][0], [P2[0], P2[1], P2[2], 1])
        p2h = self.homogeneous2d(p2)
        p3 = np.dot(self.gstack3d[-1][0], [P3[0], P3[1], P3[2], 1])
        self.cpt = p3
        p3h = self.homogeneous2d(p3)
        w = 1.0 * p3h[2]
        c = p2h[2] / w - 1
        x2 = p2h[0] / w - c * (p3h[0] / w)
        y2 = p2h[1] / w - c * (p3h[1] / w)
        self.curveto(x1, y1, x2, y2, p3h[0] / w, p3h[1] / w)

    def closepath3d(self):
        v = np.dot(self.gstack3d[-1][0], self.lm)
        self.cpt = v
        self.closepath()

    # ------------------------------------------------------------------
    #  X- variants  (2D/3D auto-dispatch via _Xmove3d)
    # ------------------------------------------------------------------

    def _Xmove3d(self, args, relative=False, cmd='moveto'):
        """Xmoveto / Xrmoveto / Xlineto / Xrlineto3d — 2D fallback + 3D."""
        if _is_2d(args):
            return getattr(PiScript, cmd)(self, *args)
        self._move3d(args, relative=relative, cmd=cmd)

    def Xmoveto(self, *args):
        self._Xmove3d(args, relative=False, cmd='moveto')

    def Xrmoveto(self, *args):
        self._Xmove3d(args, relative=True, cmd='moveto')

    def Xlineto(self, *args):
        self._Xmove3d(args, relative=False, cmd='lineto')

    def Xrlineto3d(self, *args):
        self._Xmove3d(args, relative=True, cmd='rlineto')

    def Xcurveto(self, *args):
        if len(args) == 2:
            return PiScript.lineto(self, *args)
        P1, P2, P3 = args
        self.curveto3d(P1, P2, P3)

    def Xclosepath(self):
        if self.lm:
            v = np.dot(self.gstack3d[-1][0], self.lm)
            self.cpt = v
        PiScript.closepath(self)

    def Xstroke(self, *args):
        self.lm = None
        PiScript.stroke(self, *args)

    def Xfill(self, *args):
        self.lm = None
        PiScript.fill(self, *args)

    # ------------------------------------------------------------------
    #  lighting
    # ------------------------------------------------------------------

    def set_light(self, L):
        self.light = Vector(L).normalized()

    def get_light(self):
        t = self.gstack3d[-1][1]
        e = self.light
        v = [sum(t[i][j] * e[j] for j in range(4)) for i in range(4)]
        r = math.hypot(v[0], v[1], v[2])
        v[0] /= r; v[1] /= r; v[2] /= r
        return v

    def rotated(self, u, a, A):
        r = VU.length(a) * 1.0
        n = [a[0] / r, a[1] / r, a[2] / r]
        d = VU.mul(u, n)
        u0 = [n[0] * d, n[1] * d, n[2] * d]
        u1 = [u[0] - u0[0], u[1] - u0[1], u[2] - u0[2]]
        u2 = VU.x(n, u1)
        A *= self.toRad
        c = math.cos(A); s = math.sin(A)
        return [u0[i] + c * u1[i] + s * u2[i] for i in range(3)]

    def rotationmatrix(self, axis, A):
        a = self.rotated([1, 0, 0], axis, A)
        b = self.rotated([0, 1, 0], axis, A)
        c = self.rotated([0, 0, 1], axis, A)
        return [[a[0], b[0], c[0]],
                [a[1], b[1], c[1]],
                [a[2], b[2], c[2]]]
