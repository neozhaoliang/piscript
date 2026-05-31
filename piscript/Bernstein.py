"""Bernstein polynomial utilities."""

import numpy as np


def choose(n, k):
    """Binomial coefficient."""
    if k < 0 or k > n:
        return 0
    if k == 0 or k == n:
        return 1
    k = min(k, n - k)
    c = 1
    for i in range(k):
        c = c * (n - i) // (i + 1)
    return c


def bernstein(y, t):
    """Evaluate a degree-n Bernstein polynomial defined by control points y at t.

    bernstein([y0, y1, ..., yn], t) computes sum_i y_i * B_{i,n}(t).
    """
    n = len(y) - 1
    if not isinstance(y[0], (list, tuple, np.ndarray)):
        # Scalar control points
        total = 0.0
        for i, yi in enumerate(y):
            total += yi * choose(n, i) * (t ** i) * ((1 - t) ** (n - i))
        return total
    # Vector control points
    result = [0.0] * len(y[0])
    for i, p in enumerate(y):
        b = choose(n, i) * (t ** i) * ((1 - t) ** (n - i))
        for j, pj in enumerate(p):
            result[j] += b * pj
    return result


def bernstein_basis(i, n, t):
    """Evaluate the i-th Bernstein basis polynomial of degree n at t."""
    return choose(n, i) * (t ** i) * ((1 - t) ** (n - i))


def interpolate(points, t_or_y, t=None):
    """Interpolate control points using Bernstein polynomials.

    interpolate(points, t)       -- single list of points at t
    interpolate(xs, ys, t)       -- evaluate 2D x, y separately
    """
    if t is not None:
        xs, ys, t_val = points, t_or_y, t
        return [bernstein(xs, t_val), bernstein(ys, t_val)]
    return bernstein(points, t_or_y)
