"""PiScript -- a programmable PostScript graphics library.

Usage::

    from piscript.PiModule import *
    init("output", 400, 300)
    beginpage()
    moveto(100, 100)
    lineto(200, 200)
    stroke()
    endpage()
    finish()
"""

__version__ = "0.1.0"

__all__ = [
    # Vector math
    "Vector", "Vec2", "Vec3", "Vec4", "Vec5",
    # Core classes
    "Canvas", "Graphics", "PiScript", "PiScript3d",
    # Module facades
    "PiModule",
]
