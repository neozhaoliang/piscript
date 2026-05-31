"""PiScript - generate PostScript graphics with TeX text rendering.

Quick usage (global singleton):
    from piscript.PiModule import *
    init(300, 200)
    beginpage()
    newpath()
    moveto(0, 0); lineto(100, 100)
    stroke()
    endpage()
    finish()

Multi-instance usage (no global state):
    ps = init("output_a", 300, 200)
    ps.beginpage()
    ...
    ps.finish()

Most functions auto-proxy to the global `ps` singleton via __getattr__.
Only functions with special logic, deprecated wrappers, or name mismatches
are defined explicitly.
"""

import math
import warnings

from piscript.Arc import arc as _arc, arcn as _arcn, circle as _circle
from piscript.Arrows import arrow as _arrow, setarrowdims as _setarrowdims
from piscript.Arrows import arcarrow as _arcarrow, arcnarrow as _arcnarrow
from piscript.Arrows import openarrow as _openarrow, texarrow as _texarrow
from piscript.Canvas import Canvas
from piscript.PSExec import PSExec
from piscript.PiScript import PiScript
from piscript.PiScript3d import *  # noqa: Face, ConvexSurface, etc.
from piscript.ShadedPath import ShadedPath  # noqa: re-export
from piscript.ShadedBand import ShadedBand  # noqa: re-export
from piscript.Sphere import Sphere  # noqa: re-export
from piscript.Type1 import Type1Font  # noqa: re-export
from piscript.VectorUtils import Vector  # noqa: re-export
from piscript.TexFontNameDict import *  # noqa: re-export
from piscript.TexAliasDict import *  # noqa: re-export

# ---------------------------------------------------------------------------
#  Math re-exports
# ---------------------------------------------------------------------------

atan = math.atan
pi = math.pi
cos = math.cos
sin = math.sin
exp = math.exp
sqrt = math.sqrt
log = math.log
tan = math.tan
atan2 = math.atan2
acos = math.acos
asin = math.asin

# ---------------------------------------------------------------------------
#  Singleton
# ---------------------------------------------------------------------------

class _Uninitialized:
    """Sentinel that raises a helpful error until init() is called."""
    def __getattr__(self, name):
        raise RuntimeError(
            "PiScript not initialized. Call init() or init3d() first."
        )
    def __call__(self, *args, **kwargs):
        raise RuntimeError(
            "PiScript not initialized. Call init() or init3d() first."
        )

ps = _Uninitialized()

# ---------------------------------------------------------------------------
#  Init
# ---------------------------------------------------------------------------

def init(*args):
    """init(w, h) | init(filename, w, h) | init(w, h, 'noclip')"""
    global ps
    ps = PiScript(PSExec(), *args)
    return ps


def init3d(*args):
    """Initialize 3D PiScript."""
    global ps
    ps = PiScript3d(PSExec(), *args)
    return ps

# ---------------------------------------------------------------------------
#  Special functions  (non-trivial logic, deprecated wrappers, factories,
#                       external-module calls, name mismatches)
# ---------------------------------------------------------------------------

# --- non-trivial logic ---

def width():        return ps.width
def height():       return ps.height
def currentwidth(): return ps.width
def currentheight(): return ps.height

def center():       ps.center()

def currentcenter():
    b = ps.currentbbox()
    return [(b[0][0] + b[2][0]) / 2.0, (b[0][1] + b[2][1]) / 2.0]

def zoom(x, c, s):
    translate(c)
    scale(s)
    translate(-x[0], -x[1])

def linethrough(P, Q):
    from piscript.VectorUtils import linethrough as _linethrough
    return _linethrough(P, Q)

def interpolation(p, q, t):
    from piscript.VectorUtils import interpolated
    return interpolated(p, q, t)

def fontlist():
    from piscript.TexAliasDict import aliasdict
    from piscript.TexFontNameDict import texfontname
    FL = [[k, aliasdict[k]] for k in aliasdict]
    FL.extend([k, texfontname[k]] for k in texfontname)
    return FL

def transform(m, v):
    from piscript.PSMatrix import transform as _mtransform
    return _mtransform(m, v)

# --- deprecated wrappers ---

def affine_reflect(f):
    """Deprecated: use reflect() instead."""
    warnings.warn("affine_reflect() is deprecated; use reflect()",
                  DeprecationWarning, stacklevel=2)
    ps.reflect(f)

def seteye(e):
    """Deprecated: use set_eye() instead."""
    warnings.warn("seteye() is deprecated; use set_eye()",
                  DeprecationWarning, stacklevel=2)
    ps.set_eye(e)

def geteye():
    """Deprecated: use get_eye() instead."""
    warnings.warn("geteye() is deprecated; use get_eye()",
                  DeprecationWarning, stacklevel=2)
    return ps.get_eye()

def setlight(L):
    """Deprecated: use set_light() instead."""
    warnings.warn("setlight() is deprecated; use set_light()",
                  DeprecationWarning, stacklevel=2)
    ps.set_light(L)

def getlight():
    """Deprecated: use get_light() instead."""
    warnings.warn("getlight() is deprecated; use get_light()",
                  DeprecationWarning, stacklevel=2)
    return ps.get_light()

def projection2d(*args):
    """Deprecated: use project_to_2d() instead."""
    warnings.warn("projection2d() is deprecated; use project_to_2d()",
                  DeprecationWarning, stacklevel=2)
    return ps.projectto2d(*args)

def smoothconvexsurface(f):
    """Deprecated: use smooth_convex_surface() instead."""
    warnings.warn("smoothconvexsurface() is deprecated; use smooth_convex_surface()",
                  DeprecationWarning, stacklevel=2)
    return smooth_convex_surface(f)

# --- functions that call external modules with ps as first arg ---

def arc(*args):             _arc(ps, *args)
def arcn(*args):            _arcn(ps, *args)
def circle(*args):          _circle(ps, *args)
def arrow(*args):           _arrow(ps, *args)
def openarrow(*args):       _openarrow(ps, *args)
def setarrowdims(*args):    _setarrowdims(ps, *args)
def texarrow(*args):        _texarrow(ps, *args)
def arcarrow(*args):        _arcarrow(ps, *args)
def arcnarrow(*args):       _arcnarrow(ps, *args)

def shadedpath(wd):         return ShadedPath(ps, wd)
def shadedband():           return ShadedBand(ps)

# --- functions that operate on non-ps objects (surfaces, faces) ---

def paint(s, *args):        s.paint(ps, *args)
def outline(s, *args):      s.outline(ps, *args)
def reverse(f):             return f.reversed()
def setshading(f, y):       f.setshading(y)
def set_shading(f, y):      f.setshading(y)

# --- factory functions ---

def canvas(*args):          return Canvas(*args)
def insert(*args):          return Canvas(*args)
def face(p, c=None):
    from piscript.PiScript3d import Face
    return Face(p, c) if c is not None else Face(p)

def sphere(c, n):
    return Sphere(c, n)

def font(fn):
    return Type1Font(fn)

def convexsurface(*args):
    from piscript.PiScript3d import ConvexSurface
    return ConvexSurface(*args)

def convex_surface(f):
    from piscript.PiScript3d import ConvexSurface
    return ConvexSurface(face(f))

def smooth_convex_surface(f):
    from piscript.PiScript3d import SmoothConvexSurface
    return SmoothConvexSurface(f)

# --- name mismatches / special call patterns ---

def image(img, n, interpolate=False):
    ps.put_image(img, n, interpolate)

def putPS(s):
    ps.insert(s)

def bbox(*args):
    ps.boundedbox(*args)

def ArcArrow(c, r, a, b):
    ps.arcarrow(c, r, a, b)

def ArcnArrow(c, r, a, b):
    ps.arcnarrow(c, r, a, b)

def current_point():
    return ps.currentpoint()

def epsboundingbox(fn):
    return PSExec.epsboundingbox(fn)

# --- TeX ---

from piscript.Tex import TexEnv  # noqa: re-export


def texinsert(texstring, save=None, pin=False):
    return ps.texinsert(texstring, save, pin)

# ---------------------------------------------------------------------------
#  Auto-proxy wrappers — generated at import time, deferred to ps at call time
# ---------------------------------------------------------------------------

# Names that need to map to a different method on ps
_ALIASES = {
    'flush': 'finish',
    'setgray': 'setcolor',
}

# Names that should be available as module-level functions, proxying to ps
_PROXY_NAMES = [
    # page-level
    'beginpage', 'endpage', 'minx', 'maxx', 'miny', 'maxy',
    'setbbox', 'currentbbox', 'currentlinewidth', 'currentlinecap',
    # graphics state
    'gsave', 'grestore', 'cgs', 'revert', 'lrevert',
    'scale', 'translate', 'rotate', 'ltransform', 'atransform', 'reflect',
    'scalelinewidth', 'setlinewidth', 'setcolor', 'setgray',
    'setlinecap', 'setmiterlimit', 'setlinejoin', 'setdash',
    'setdeg', 'setrad', 'todeg', 'torad',
    # path construction
    'newpath', 'moveto', 'connectto', 'lineto', 'quadto', 'curveto',
    'rmoveto', 'rlineto', 'currentpoint', 'closepath', 'boundedbox',
    # realizing
    'stroke', 'fill', 'clip', 'shfill',
    # text
    'setfont', 'show', 'stringinsert',
    # TeX
    'settexprefix', 'settexmacros', 'settexpostfix', 'settexcommand',
    'settexsave', 'settexenv', 'settexconfig',
    # embedding
    'place', 'embed', 'place3d', 'comment',
    # raw PS
    'importPS', 'importEPS', 'include',
    # 3D
    'gsave3d', 'grestore3d', 'set_eye', 'get_eye', 'set_light', 'get_light',
    'project_to_2d', 'scale3d', 'gfxtransform3d', 'rotate3d', 'translate3d', 'project',
    'moveto3d', 'rmoveto3d', 'lineto3d', 'rlineto3d', 'curveto3d', 'closepath3d',
    # misc
    'envelope', 'finish', 'flush',
]


def _make_proxy(name):
    """Create a wrapper that delegates to ps.<name> at call time."""
    target = _ALIASES.get(name, name)
    def wrapper(*args, **kwargs):
        return getattr(ps, target)(*args, **kwargs)
    wrapper.__name__ = name
    wrapper.__qualname__ = name
    return wrapper


# Inject proxy wrappers into the module namespace (so star import finds them)
for _n in _PROXY_NAMES:
    if _n not in globals():
        globals()[_n] = _make_proxy(_n)

# __all__ for star import — includes explicit names + proxies + re-exports
__all__ = sorted(
    {k for k in globals() if not k.startswith('_') and k not in ('math', 'warnings', 'ps')}
    | {'ShadedPath', 'ShadedBand', 'Sphere', 'Type1Font', 'Vector', 'Canvas',
       'TexEnv', 'PiScript', 'PiScript3d', 'Face', 'ConvexSurface', 'SmoothConvexSurface'}
)
