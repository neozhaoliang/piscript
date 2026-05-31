"""Arrow drawing utilities for PiScript — ported from Python 2 original."""

from piscript.VectorUtils import Vector
from piscript.Arc import arc as _arc, arcn as _arcn

import math


class _Dims:
    """Container for arrow dimensions — replaces module-level globals."""
    sw = 1.0
    hw = 3.6
    A = 24 * math.pi / 180.0
    B = 60 * math.pi / 180.0


_d = _Dims()


# ---------------------------------------------------------------------------
#  Transformable mixin — eliminates duplicate translate/rotate in 5 classes
# ---------------------------------------------------------------------------

class _Transformable:
    """Mixin: provides translate() and rotate() by iterating self._points."""

    _points = ()

    def translate(self, p):
        for name in self._points:
            Arrow.Translate(getattr(self, name), p)

    def rotate(self, a):
        c = math.cos(a); s = math.sin(a)
        for name in self._points:
            Arrow.Rotate(getattr(self, name), c, s)


# ---------------------------------------------------------------------------
#  Arrow components
# ---------------------------------------------------------------------------

class PlainHead(_Transformable):
    _points = ('p0', 'p1', 'p2', 'p3', 'p4')

    def __init__(self):
        xA = 0.5 * _d.hw / math.tan(_d.A)
        xB = 0.5 * (_d.hw - _d.sw) / math.tan(_d.B)
        self.p0 = Vector([0, -0.5 * _d.sw])
        self.p1 = self.p0 + [-xB, -0.5 * (_d.hw - _d.sw)]
        self.p2 = self.p1 + [xA, 0.5 * _d.hw]
        self.p3 = self.p2 + [-xA, 0.5 * _d.hw]
        self.p4 = self.p3 + [xB, -0.5 * (_d.hw - _d.sw)]
        self.length = xA - xB

    def start(self):    return self.p0
    def stop(self):     return self.p4

    def beginpath(self, p):
        p.moveto(self.p0)

    def mkpath(self, p):
        p.lineto(self.p1)
        p.lineto(self.p2)
        p.lineto(self.p3)
        p.lineto(self.p4)


class StraightShaft(_Transformable):
    _points = ('p0', 'p1', 'p2', 'p3')

    def __init__(self, L):
        wd = 0.5 * _d.sw
        self.p0 = [0, -wd]
        self.p1 = [L, -wd]
        self.p2 = [L,  wd]
        self.p3 = [0,  wd]

    def mkbottompath(self, p):  p.lineto(self.p1)
    def mktoppath(self, p):     p.lineto(self.p3)


class ArcShaft(_Transformable):
    _points = ('p0', 'p1', 'p2', 'p3', 'ctr')

    def __init__(self, A, r):
        c = math.cos(A); s = math.sin(A)
        e = 0.5 * _d.sw
        self.p0 = Vector([r + e, 0])
        self.p3 = Vector([r - e, 0])
        self.p1 = Vector([(r + e) * c, (r + e) * s])
        self.p2 = Vector([(r - e) * c, (r - e) * s])
        self.A0 = 0
        self.A1 = A
        self.r = r
        self.ctr = Vector([0, 0])

    def rotate(self, a):
        super().rotate(a)
        self.A0 += a
        self.A1 += a

    def mkbottompath(self, p):
        _arc(p, self.ctr, self.r + 0.5 * _d.sw, self.A0, self.A1)

    def mktoppath(self, p):
        _arcn(p, self.ctr, self.r - 0.5 * _d.sw, self.A1, self.A0)

    def start(self):    return self.p0


class ArcnShaft(ArcShaft):
    def __init__(self, A, r):
        ArcShaft.__init__(self, A, r)
        self.p0, self.p2 = self.p2, self.p0
        self.p1, self.p3 = self.p3, self.p1

    def mkbottompath(self, p):
        _arcn(p, self.ctr, self.r - 0.5 * _d.sw, self.A1, self.A0)

    def mktoppath(self, p):
        _arc(p, self.ctr, self.r + 0.5 * _d.sw, self.A0, self.A1)

    def start(self):    return self.p0


class StubTail(_Transformable):
    _points = ('p0', 'p1')

    def __init__(self):
        self.p0 = Vector([0, 0.5 * _d.sw])
        self.p1 = Vector([0, -0.5 * _d.sw])

    def start(self):    return self.p0
    def stop(self):     return self.p1

    def mkpath(self, p):
        p0, p1 = self.p0, self.p1
        c = p.currentlinecap()
        if c == 0:
            p.lineto(p1)
        elif c == 1:
            ctr = (p0 + p1) * 0.5
            ang = math.atan2(p0[1] - p1[1], p0[0] - p1[0])
            p.arc(ctr[0], ctr[1], 0.5 * _d.sw, ang, ang + math.pi)
        else:
            v = (p0 - p1) * 0.5
            p.lineto(p0 + [-v[1], v[0]])
            p.lineto(p1 + [-v[1], v[0]])
            p.lineto(p1)


class TexHead(_Transformable):
    _points = ('P', 'Q')

    def __init__(self, A, B, R):
        self.A, self.B, self.R = A, B, R
        self.P = [0, -0.5 * _d.sw]
        self.Q = [0, 0.5 * _d.sw]
        self.axis = [1, 0]
        self.r = 0.84 * _d.sw
        self.rho = 0.8 * self.r
        c = math.cos(A)
        Ax = math.acos((R * c - _d.sw / 2) / (R + self.r / 2))
        self.length = (R + self.r / 2) * math.sin(Ax) - R * math.sin(A)

    def rotate(self, a):
        super().rotate(a)
        c = math.cos(a); s = math.sin(a)
        Arrow.Rotate(self.axis, c, s)

    def mkpath(self, ps):
        A = self.A; axis = self.axis; R = self.R
        O = [0.5 * (self.P[0] + self.Q[0]), 0.5 * (self.P[1] + self.Q[1])]
        s = math.sin(A); c = math.cos(A)
        al = math.atan2(axis[1], axis[0])
        e = [R * s * axis[0], R * s * axis[1]]
        f = [-R * c * axis[1], R * c * axis[0]]
        C = [O[0] + e[0] - f[0], O[1] + e[1] - f[1]]
        Ax = math.acos((R * c - _d.sw / 2) / (R + self.r / 2))
        T = math.pi / 2 + A + al + self.B
        _arc(ps, C, R + self.r / 2, math.pi / 2 + Ax + al, T)
        _arc(ps, C[0] + R * math.cos(T), C[1] + R * math.sin(T),
               self.r / 2, T, T + math.pi)
        _arcn(ps, C, R - self.r / 2, T, math.pi / 2 + A + al)
        dx = 0.5 * (self.r - self.rho) / s
        _arc(ps, O[0] + dx * axis[0], O[1] + dx * axis[1],
               self.rho / 2, -math.pi / 2 + al + A, math.pi / 2 + al - A)
        C = [O[0] + e[0] + f[0], O[1] + e[1] + f[1]]
        T = -math.pi / 2 - A - self.B + al
        _arcn(ps, C, R - self.r / 2, -math.pi / 2 - A + al, T)
        _arc(ps, C[0] + R * math.cos(T), C[1] + R * math.sin(T),
               self.r / 2, T - math.pi, T)
        _arc(ps, C, R + self.r / 2, T, -math.pi / 2 - Ax + al)

    def start(self):
        X = self.length; a = self.axis
        return [self.P[0] - X * a[0], self.P[1] - X * a[1]]

    def stop(self):
        X = self.length; a = self.axis
        return [self.Q[0] - X * a[0], self.Q[1] - X * a[1]]


class QuadShaft:
    def __init__(self, ell, P):
        wd = 0.5 * _d.sw
        k = (len(P) - 1) // 2
        bottom = []; top = []
        P0, P1 = P[0], P[1]
        P01 = [P1[0] - P0[0], P1[1] - P0[1]]
        d01 = math.hypot(P01[0], P01[1])
        u = [-P01[1] / d01, P01[0] / d01]
        self.p0 = [P0[0] - wd * u[0], P0[1] - wd * u[1]]
        self.p3 = [P0[0] + wd * u[0], P0[1] + wd * u[1]]
        bottom.append(self.p0); top.append(self.p3)
        for i in range(k - 1):
            P2 = P[2 * i + 2]
            P12 = [P2[0] - P1[0], P2[1] - P1[1]]
            d12 = math.hypot(P12[0], P12[1])
            v = [-P12[1] / d12, P12[0] / d12]
            dot = u[0] * v[0] + u[1] * v[1]
            det = dot * dot - 1
            a = (wd / det) * (dot - 1); b = a
            w = [a * u[0] + b * v[0], a * u[1] + b * v[1]]
            bottom.append([P1[0] - w[0], P1[1] - w[1]])
            top.append([P1[0] + w[0], P1[1] + w[1]])
            P0, P1 = P2, P[2 * i + 3]
            u = v
            bottom.append([P0[0] - wd * u[0], P0[1] - wd * u[1]])
            top.append([P0[0] + wd * u[0], P0[1] + wd * u[1]])
        P2 = P[-1]
        dx, dy = P2[0] - P1[0], P2[1] - P1[1]
        D = math.hypot(dx, dy)
        P01 = [P1[0] - P0[0], P1[1] - P0[1]]
        P12 = [dx, dy]
        b_proj = (P01[0] * dx + P01[1] * dy) / float(dx * dx + dy * dy)
        a_val = 1 - b_proj
        s = (ell / D) / (1 + math.sqrt(1 - a_val * ell / D))
        t = 1 - s
        P012 = [P12[0] - P01[0], P12[1] - P01[1]]
        Q1 = [s * P0[0] + t * P1[0], s * P0[1] + t * P1[1]]
        Q2 = [P2[0] - 2 * s * P12[0] + s * s * P012[0],
              P2[1] - 2 * s * P12[1] + s * s * P012[1]]
        V = [2 * (P01[0] + t * P012[0]), 2 * (P01[1] + t * P012[1])]
        Dv = math.hypot(V[0], V[1])
        v = [-V[1] / Dv, V[0] / Dv]
        dot = u[0] * v[0] + u[1] * v[1]
        det = dot * dot - 1
        a_val2 = (wd / det) * (dot - 1); b_val2 = a_val2
        w = [a_val2 * u[0] + b_val2 * v[0], a_val2 * u[1] + b_val2 * v[1]]
        p1b = [Q1[0] - w[0], Q1[1] - w[1]]
        q1 = [Q1[0] + w[0], Q1[1] + w[1]]
        bottom.append(p1b); top.append(q1)
        self.p1 = [Q2[0] - wd * v[0], Q2[1] - wd * v[1]]
        self.p2 = [Q2[0] + wd * v[0], Q2[1] + wd * v[1]]
        bottom.append(self.p1); top.append(self.p2)
        self.bottom = bottom
        self.top = []
        n = len(top)
        for i in range(n):
            self.top.append(top[n - 1 - i])

    def mkbottompath(self, ps):
        b = self.bottom
        i = 1
        while i < len(b):
            ps.quadto(b[i], b[i + 1])
            i += 2

    def mktoppath(self, ps):
        t = self.top
        i = 1
        while i < len(t):
            ps.quadto(t[i], t[i + 1])
            i += 2

    def rotate(self, a):
        c = math.cos(a); s = math.sin(a)
        for pt in self.bottom + self.top:
            Arrow.Rotate(pt, c, s)

    def translate(self, p):
        for pt in self.bottom + self.top:
            Arrow.Translate(pt, p)


# ---------------------------------------------------------------------------
#  Arrow (composite)
# ---------------------------------------------------------------------------

class Arrow:
    def __init__(self, head, shaft, tail):
        Arrow.attach(head, head.start(), head.stop(), shaft.p1, shaft.p2)
        if tail is not None:
            Arrow.attach(tail, tail.start(), tail.stop(), shaft.p3, shaft.p0)
        self.shaft = shaft
        self.head = head
        self.tail = tail

    def start(self):
        return self.shaft.p0

    def translate(self, p):
        self.shaft.translate(p)
        self.head.translate(p)
        if self.tail is not None:
            self.tail.translate(p)

    def rotate(self, a):
        self.shaft.rotate(a)
        if self.head is not None:
            self.head.rotate(a)
        if self.tail is not None:
            self.tail.rotate(a)

    def mkpath(self, p):
        p.moveto(self.shaft.p0)
        self.shaft.mkbottompath(p)
        self.head.mkpath(p)
        self.shaft.mktoppath(p)
        if self.tail is not None:
            self.tail.mkpath(p)
            p.closepath()

    @staticmethod
    def Rotate(pt, c, s):
        x, y = pt[0], pt[1]
        pt[0] = c * x - s * y
        pt[1] = s * x + c * y

    @staticmethod
    def Translate(pt, v):
        pt[0] += v[0]
        pt[1] += v[1]

    @staticmethod
    def attach(h, t0, t1, s0, s1):
        h.translate([-t0[0], -t0[1]])
        u = [s1[0] - s0[0], s1[1] - s0[1]]
        v = [t1[0] - t0[0], t1[1] - t0[1]]
        a = math.atan2(u[1], u[0])
        b = math.atan2(v[1], v[0])
        h.rotate(a - b)
        h.translate([s0[0], s0[1]])


# ---------------------------------------------------------------------------
#  Public API
# ---------------------------------------------------------------------------

def setarrowdims(ps, *args):
    if len(args) == 1:
        _d.sw = float(args[0])
        _d.hw = 3.6 * _d.sw
    elif len(args) == 2:
        _d.sw = float(args[0])
        _d.hw = float(args[1])
    else:
        _d.sw = float(args[0])
        _d.hw = float(args[1])
        _d.A = args[2] * ps.toRad
        _d.B = args[3] * ps.toRad


def _unpack_arrow_args(args):
    """Parse arrow(x0,y0,x1,y1) / arrow([x0,y0],[x1,y1]) / arrow([x1,y1])."""
    n = len(args)
    if n == 1:
        return 0, 0, args[0][0], args[0][1]
    a0, a1 = args[0], args[1]
    if hasattr(a0, '__iter__') and hasattr(a1, '__iter__'):
        return a0[0], a0[1], a1[0], a1[1]
    return 0, 0, a0, a1


def arrow(ps, *args):
    x0, y0, x1, y1 = _unpack_arrow_args(args)
    h = PlainHead()
    L = math.hypot(x1 - x0, y1 - y0)
    s = StraightShaft(L - h.length)
    t = StubTail()
    a = Arrow(h, s, t)
    C = math.atan2(y1 - y0, x1 - x0)
    a.rotate(C)
    a.translate([x0, y0])
    a.mkpath(ps)


def openarrow(ps, *args):
    n = len(args)
    if n == 1:
        x, y = args[0][0], args[0][1]
    else:
        x, y = args[0], args[1]
    h = PlainHead()
    L = math.hypot(x, y)
    s = StraightShaft(L - h.length)
    a = Arrow(h, s, None)
    C = math.atan2(y, x)
    a.rotate(C)
    a.mkpath(ps)


def _unpack_arc_args(args):
    """Parse (C, r, A, B) or (cx, cy, r, A, B)."""
    if len(args) == 4:
        return args[0], args[1], args[2], args[3]
    return (args[0], args[1]), args[2], args[3], args[4]


def arcarrow(ps, *args):
    C, r, A, B = _unpack_arc_args(args)
    while B < A:
        B += 2 * math.pi
    head = PlainHead()
    S = head.length / r
    tail = StubTail()
    dT = B - A
    s = math.sin(dT); c = math.cos(dT)
    T = math.atan2(s - S * c, c + S * s)
    shaft = ArcShaft(T, r)
    a = Arrow(head, shaft, tail)
    a.rotate(A)
    a.translate(C)
    a.mkpath(ps)


def arcnarrow(ps, *args):
    C, r, A, B = _unpack_arc_args(args)
    while A < B:
        A += 2 * math.pi
    head = PlainHead()
    S = head.length / r
    tail = StubTail()
    dT = A - B
    s = math.sin(dT); c = math.cos(dT)
    T = math.atan2(s - S * c, c + S * s)
    shaft = ArcnShaft(T, r)
    a = Arrow(head, shaft, tail)
    a.rotate(B + math.atan(S))
    a.translate(C)
    a.mkpath(ps)


def texarrow(ps, *args):
    x0, y0, x1, y1 = _unpack_arrow_args(args)
    ell = math.hypot(x1 - x0, y1 - y0)
    head = TexHead(math.pi / 16, math.pi / 2.4, 1 * _d.hw)
    shaft = StraightShaft(ell - head.length)
    tail = StubTail()
    a = Arrow(head, shaft, tail)
    a.rotate(math.atan2(y1 - y0, x1 - x0))
    a.translate([x0, y0])
    a.mkpath(ps)


def quadarrow(ps, *args):
    A = args[0] if len(args) == 1 else args
    head = PlainHead()
    ell = head.length
    shaft = QuadShaft(ell, A)
    tail = StubTail()
    a = Arrow(head, shaft, tail)
    a.mkpath(ps)


def arrowhead(ps, A):
    h = PlainHead()
    h.rotate(A)
    h.beginpath(ps)
    h.mkpath(ps)
