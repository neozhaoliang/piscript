"""Arc and circle drawing utilities.

arc()  — counterclockwise arc
arcn() — clockwise arc
circle() — full circle
"""

import math


# ---- shared helpers ----------------------------------------------------------

def _parse_arc_args(args):
    """Parse arc arguments: (r,A,B), (P,r,A,B), or (x,y,r,A,B)."""
    if len(args) == 3:
        return 0, 0, args[0], args[1], args[2]
    elif len(args) == 4:
        return args[0][0], args[0][1], args[1], args[2], args[3]
    else:
        return args[0], args[1], args[2], args[3], args[4]


def _makesimplearc(ps, x, y, r, A, B):
    """Draw a cubic Bezier approximation of a circular arc from A to B."""
    dA = 0.5 * (B - A)
    dx = r * math.cos(dA)
    dy = r * math.sin(dA)
    c = 4 * (r - dx) / (3.0 * dy)
    dx0, dy0 = r * math.cos(A), r * math.sin(A)
    dx3, dy3 = r * math.cos(B), r * math.sin(B)
    P0 = [x + dx0, y + dy0]
    P3 = [x + dx3, y + dy3]
    P1 = [P0[0] - c * dy0, P0[1] + c * dx0]
    P2 = [P3[0] + c * dy3, P3[1] - c * dx3]
    ps.curveto(P1, P2, P3)


def _draw_arc(ps, x, y, r, A, B, clockwise):
    """Draw an arc from angle A to angle B, in the given direction.

    Splits the arc into <= 90-degree segments to keep Bezier approximation
    accurate for all radii.
    """
    A_rad = A * ps.toRad
    B_rad = B * ps.toRad
    quadrant = math.pi / 2

    # Normalize angle range so the sweep is in the correct direction
    if clockwise:
        while A_rad < B_rad:
            A_rad += 2 * math.pi
    else:
        while B_rad < A_rad:
            B_rad += 2 * math.pi

    # Move to start point (connect if there's a current point)
    start = [x + r * math.cos(A_rad), y + r * math.sin(A_rad)]
    if ps.currentpoint():
        ps.lineto(*start)
    else:
        ps.moveto(*start)

    # Draw quadrant-by-quadrant
    step = quadrant if not clockwise else -quadrant
    while abs(B_rad - A_rad) > quadrant:
        next_a = A_rad + step
        _makesimplearc(ps, x, y, r, A_rad, next_a)
        A_rad = next_a

    # Remaining segment (if any)
    if abs(A_rad - B_rad) > 0.000000001:
        _makesimplearc(ps, x, y, r, A_rad, B_rad)


# ---- public API --------------------------------------------------------------

def arc(ps, *args):
    """Draw a counterclockwise arc.

    arc(r, A, B)           — centered at origin
    arc((x, y), r, A, B)   — centered at (x, y)
    arc(x, y, r, A, B)     — centered at (x, y)
    """
    x, y, r, A, B = _parse_arc_args(args)
    _draw_arc(ps, x, y, r, A, B, clockwise=False)


def arcn(ps, *args):
    """Draw a clockwise arc. Same argument forms as arc()."""
    x, y, r, A, B = _parse_arc_args(args)
    _draw_arc(ps, x, y, r, A, B, clockwise=True)


def circle(ps, *args):
    """Draw a full circle.

    circle(r)              — centered at origin
    circle((x, y), r)      — centered at (x, y)
    circle(x, y, r)        — centered at (x, y)
    """
    if len(args) == 1:
        x, y, r = 0, 0, args[0]
    elif len(args) == 2:
        x, y, r = args[0][0], args[0][1], args[1]
    else:
        x, y, r = args[0], args[1], args[2]

    p2 = math.pi / 2
    _draw_arc(ps, x, y, r, 0, p2, clockwise=False)
    _draw_arc(ps, x, y, r, p2, math.pi, clockwise=False)
    _draw_arc(ps, x, y, r, math.pi, 3 * p2, clockwise=False)
    _draw_arc(ps, x, y, r, 3 * p2, 2 * math.pi, clockwise=False)
    ps.closepath()
