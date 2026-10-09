"""Cubic Bézier approximation of arcs and circles."""

import math


def _parse_arc_args(args):
    if len(args) == 3:
        return 0, 0, *args
    if len(args) == 4:
        (x, y), radius, start, end = args
        return x, y, radius, start, end
    if len(args) == 5:
        return args
    raise TypeError("arc expects (r, a, b), (center, r, a, b) or (x, y, r, a, b)")


def _makesimplearc(ps, x, y, radius, start, end):
    """Append a Bézier segment spanning at most ninety degrees."""
    factor = (4 / 3) * math.tan((end - start) / 4)
    cs, ss = math.cos(start), math.sin(start)
    ce, se = math.cos(end), math.sin(end)
    p0 = (x + radius * cs, y + radius * ss)
    p3 = (x + radius * ce, y + radius * se)
    p1 = (p0[0] - factor * radius * ss,
          p0[1] + factor * radius * cs)
    p2 = (p3[0] + factor * radius * se,
          p3[1] - factor * radius * ce)
    ps.curveto(p1, p2, p3)


def _draw_arc(ps, x, y, radius, start, end, clockwise=False):
    if radius < 0:
        raise ValueError("arc radius must be non-negative")
    start *= ps.toRad
    end *= ps.toRad
    turn = 2 * math.pi
    if clockwise and end > start:
        end -= turn * math.ceil((end - start) / turn)
    elif not clockwise and end < start:
        end += turn * math.ceil((start - end) / turn)

    point = (x + radius * math.cos(start), y + radius * math.sin(start))
    if ps.currentpoint() is None:
        ps.moveto(point)
    else:
        ps.lineto(point)

    sweep = end - start
    segments = max(1, math.ceil(abs(sweep) / (math.pi / 2)))
    for index in range(segments):
        a = start + sweep * index / segments
        b = start + sweep * (index + 1) / segments
        if a != b and radius:
            _makesimplearc(ps, x, y, radius, a, b)


def arc(ps, *args):
    """Draw a counterclockwise arc in the current angular unit."""
    _draw_arc(ps, *_parse_arc_args(args))


def arcn(ps, *args):
    """Draw a clockwise arc in the current angular unit."""
    _draw_arc(ps, *_parse_arc_args(args), clockwise=True)


def circle(ps, *args):
    """Draw a circle in radians or degrees, respecting the selected mode."""
    if len(args) == 1:
        x, y, radius = 0, 0, args[0]
    elif len(args) == 2:
        (x, y), radius = args
    elif len(args) == 3:
        x, y, radius = args
    else:
        raise TypeError("circle expects (r), (center, r) or (x, y, r)")
    _draw_arc(ps, x, y, radius, 0, 2 * math.pi / ps.toRad)
    ps.closepath()
