"""Vector math utilities."""

import math
from itertools import product

import numpy as np


def clone(v):
    return list(v)


def minus(u):
    return [-x for x in u]


def mul(u, v):
    """Dot product or scalar multiplication."""
    if isinstance(v, (list, tuple, np.ndarray)):
        return sum(x * y for x, y in zip(u, v))
    return [x * v for x in u]


def div(u, c):
    return [x / c for x in u]


def x(u, v):
    """Cross product for 3D vectors."""
    return [
        u[1] * v[2] - u[2] * v[1],
        u[2] * v[0] - u[0] * v[2],
        u[0] * v[1] - u[1] * v[0],
    ]


def cross(u, v):
    """Cross product for 3D vectors."""
    return x(u, v)


def angle_between(u, v):
    ru = length(u)
    rv = length(v)
    return math.acos(mul(u, v) / (ru * rv))


def arg(u):
    """Angle of a 2D vector."""
    return math.atan2(u[1], u[0])


def perp(v):
    """Perpendicular 2D vector."""
    return [-v[1], v[0]]


def rotated(u, a, axis=None):
    """Rotate vector u by angle a (in radians).

    With 2 args: rotate 2D vector.
    With 3 args: rotate 3D vector u by angle a around axis.
    """
    if axis is None:
        c = math.cos(a)
        s = math.sin(a)
        return [c * u[0] - s * u[1], s * u[0] + c * u[1]]
    r = length(axis)
    n = [axis[0] / r, axis[1] / r, axis[2] / r]
    d = mul(u, n)
    u0 = [n[0] * d, n[1] * d, n[2] * d]
    u1 = [u[0] - u0[0], u[1] - u0[1], u[2] - u0[2]]
    u2 = x(n, u1)
    c = math.cos(a)
    s = math.sin(a)
    return [u0i + c * u1i + s * u2i for u0i, u1i, u2i in zip(u0, u1, u2)]


def reflected(f, u, v):
    """Reflect v across the line with normal f, direction u."""
    r = f[0] * u[0] + f[1] * u[1]
    c = 2 * (f[0] * v[0] + f[1] * v[1] + f[2]) / float(r)
    return (v[0] - c * u[0], v[1] - c * u[1])


def length(u):
    """Euclidean length of a vector."""
    m = max(abs(x) for x in u)
    if m == 0:
        return 0
    return m * math.sqrt(sum((x / m) ** 2 for x in u))


def evaluate(ell, P):
    return ell[0] * P[0] + ell[1] * P[1] + ell[2]


def line_through(P, Q):
    A = -(Q[1] - P[1])
    B = Q[0] - P[0]
    C = -A * P[0] - B * P[1]
    r = length((A, B))
    return [A / r, B / r, C / r]


def intersection(ell, m):
    det = ell[0] * m[1] - m[0] * ell[1]
    return [
        (-m[1] * ell[2] + ell[1] * m[2]) / det,
        (m[0] * ell[2] - ell[0] * m[2]) / det,
    ]


def linethrough(P, Q):
    v = [Q[0] - P[0], Q[1] - P[1]]
    r = length(v)
    A = -v[1] / r
    B = v[0] / r
    C = A * P[0] + B * P[1]
    return [A, B, -C]


def string(u):
    return "[" + ", ".join(str(x) for x in u) + "]"



def rotate(u, A):
    """Rotate 2D vector in-place."""
    c = math.cos(A)
    s = math.sin(A)
    x = c * u[0] - s * u[1]
    y = s * u[0] + c * u[1]
    u[0] = x
    u[1] = y


def interpolated(p, q, t):
    s = 1 - t
    return [s * pi + t * qi for pi, qi in zip(p, q)]


def isarray(a):
    """Check if a is a sequence type (list, tuple, or numpy array)."""
    return isinstance(a, (list, tuple, np.ndarray))


def parse_color(*args):
    """Parse color arguments into an (r, g, b) tuple.

    parse_color()           -> None
    parse_color(gray)       -> (gray, gray, gray)
    parse_color([r, g, b])  -> (r, g, b)
    parse_color(r, g, b)    -> (r, g, b)
    """
    if not args:
        return None
    if len(args) == 1:
        a = args[0]
        if isinstance(a, (list, tuple, np.ndarray)):
            return tuple(a[:3])
        return (a, a, a)
    return (args[0], args[1], args[2])


def distance(P, Q):
    return length([qi - pi for pi, qi in zip(P, Q)])


class _VectorBase(np.ndarray):
    """Base class for all vector types.

    Do not use this class directly to create vector instances;
    use Vector, Vec2, Vec3, etc. instead.
    """

    dim = 0  # 0 means dynamic dimension; Vec2..Vec5 override this

    def __new__(cls, *args):
        if len(args) == 1:
            x = args[0]
            try:
                vals = np.asarray(x, dtype=float)
            except (TypeError, ValueError):
                raise TypeError(
                    f"Cannot create {cls.__name__} from {type(x).__name__}"
                ) from None
            if vals.ndim == 0:
                dim = cls.dim or 1
                vals = np.full(dim, float(x))
        else:
            vals = np.asarray(args, dtype=float)

        if cls.dim and len(vals) != cls.dim:
            raise ValueError(
                f"{cls.__name__} requires exactly {cls.dim} elements,"
                f" got {len(vals)}"
            )
        return vals.view(cls)

    def __array_ufunc__(self, ufunc, method, *inputs, **kwargs):
        args = [
            i.view(np.ndarray) if isinstance(i, _VectorBase) else i
            for i in inputs
        ]
        result = getattr(ufunc, method)(*args, **kwargs)
        if isinstance(result, np.ndarray) and result.ndim == 1:
            out_type = type(self)
            if out_type.dim and len(result) != out_type.dim:
                out_type = Vector
            return result.view(out_type)
        return result

    def __array_finalize__(self, obj):
        if obj is None:
            return

    def __complex__(self):
        if len(self) < 2:
            raise ValueError(
                f"need at least 2 elements for complex(), got {len(self)}"
            )
        return complex(self[0], self[1])

    def __repr__(self):
        data = ', '.join(str(x) for x in self)
        return f"{type(self).__name__}({data})"

    def __str__(self):
        return self.__repr__()

    def length(self):
        """Return the Euclidean length (magnitude) of the vector."""
        return float(np.linalg.norm(self))

    def normalized(self):
        """Return a unit vector in the same direction."""
        m = np.max(np.abs(self))
        if m == 0:
            return self.copy()
        scaled = self / m
        return scaled / np.sqrt(np.dot(scaled, scaled))

    def perp(self):
        """Return a perpendicular 2D vector."""
        if len(self) != 2:
            raise ValueError("perp() requires a 2D vector")
        return type(self)([-self[1], self[0]])

    def arg(self):
        """Angle of a 2D vector in radians."""
        return math.atan2(self[1], self[0])


class Vector(_VectorBase):
    """General-purpose n-dimensional vector.

    Usage:
        Vector([1, 2, 3])   -- from a sequence
        Vector(1, 2, 3)     -- from varargs
    """
    pass


# ---- Fixed-dimension swizzlable vectors ----

_VEC_REGISTRY = {}


def _add_swizzles(cls):
    """Add swizzle properties to a fixed-dimension vector class."""
    key_set = "xyzw"
    valid_keys = key_set[:cls.dim]

    # Single-character accessors: v.x, v.y, v.z, v.w
    for idx, ch in enumerate(valid_keys):
        def make_prop(i):
            def getter(self):
                return self[i]
            def setter(self, val):
                self[i] = val
            return property(getter, setter)
        setattr(cls, ch, make_prop(idx))

    # Multi-character swizzle patterns (2-4 chars): v.xy, v.xyz, etc.
    for k in range(2, 5):
        for pattern in product(valid_keys, repeat=k):
            prop_name = ''.join(pattern)
            indices = [valid_keys.index(ch) for ch in pattern]
            target_dim = len(pattern)

            def make_swizzle_prop(idxs, td):
                def getter(self):
                    target_cls = _VEC_REGISTRY.get(td, Vector)
                    return self[idxs].view(target_cls)
                def setter(self, val):
                    self[idxs] = val
                return property(getter, setter)

            setattr(cls, prop_name, make_swizzle_prop(indices, target_dim))


# Create Vec2-Vec5 classes
for _d in range(2, 6):
    _VEC_REGISTRY[_d] = type(f'Vec{_d}', (Vector,), {'dim': _d})

# Add swizzles (all target classes already registered)
for _d in range(2, 6):
    _add_swizzles(_VEC_REGISTRY[_d])

Vec2 = _VEC_REGISTRY[2]
Vec3 = _VEC_REGISTRY[3]
Vec4 = _VEC_REGISTRY[4]
Vec5 = _VEC_REGISTRY[5]
