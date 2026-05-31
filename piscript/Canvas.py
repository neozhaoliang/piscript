"""Canvas: stores drawing commands in a command array.

Coordinate changes are handled by the super-class Graphics.
Drawing commands are translated into default coordinates via the
current transformation matrix before being stored.

A Canvas can be placed or embedded in another Canvas.
StringInserts are strings with metric data.
"""

from piscript.Graphics import Graphics
from piscript.PSMatrix import concat as _mconcat, transform as _mtransform, rtransform as _mrtransform
from piscript.StringInsert import StringInsert
import piscript.Fstr as Fstr
import piscript.DeviceFont as DeviceFont
from piscript.DeviceFont import Font
from piscript.Cmd import *
import piscript.VectorUtils as VectorUtils

import logging

logger = logging.getLogger(__name__)


class NoCurrentPoint(Exception):
    def __str__(self):
        return "\n\n----- No current point!  You probably forgot to begin a path with 'moveto'.\n"


class Canvas(Graphics):
    """Drawing surface backed by a command array.

    Each drawing operation appends an opcode + arguments to self.cmd[].
    The opcodes are defined in Cmd.py (SETLINEWIDTH, MOVETO, FILL, etc.).
    """

    def __init__(self):
        Graphics.__init__(self)
        self.fontTable = DeviceFont.FontTable()
        self.cmd = []
        self.m = [1, 0, 0, 1, 0, 0]
        self.pinned = False
        self.comment("canvas init")
        self.setlinewidth(1)
        self.setlinecap(0)
        self.setlinejoin(0)
        self.setdash([], 0)
        self.setmiterlimit(10.0)

    # ------------------------------------------------------------------
    #  internal helpers
    # ------------------------------------------------------------------

    def _emit(self, op, *args):
        """Append opcode + arguments to the command array."""
        self.cmd.append(op)
        self.cmd.extend(args)

    @staticmethod
    def _unpack_point(args):
        """Normalize (x, y) or ([x, y]) -> [x, y]."""
        if len(args) > 1:
            return [args[0], args[1]]
        return list(args[0])

    # ------------------------------------------------------------------
    #  clone / setup
    # ------------------------------------------------------------------

    def clone(self):
        c = Canvas()
        c.comment(" --- clone --- ")
        c.fontTable = self.fontTable
        c.cmd = list(self.cmd)
        c.m = self.m
        c.setlinewidth(self.currentlinewidth())
        c.setlinecap(self.currentlinecap())
        c.setlinejoin(self.currentlinejoin())
        d = self.currentdash()
        c.setdash(d[0], d[1])
        return c

    def setmode(self, mode):
        pass  # kept for backward compatibility

    def ctm(self):
        return self.cgs().tm

    def importPS(self, filename):
        self._emit(IMPORTPS, filename, self.ctm())

    def importEPS(self, filename):
        self._emit(IMPORTEPS, filename, self.ctm())

    def gsave(self):
        Graphics.gsave(self)
        self.cmd.append(GSAVE)

    def grestore(self):
        Graphics.grestore(self)
        self.cmd.append(GRESTORE)

    # ------------------------------------------------------------------
    #  coordinate transforms
    # ------------------------------------------------------------------

    def image(self, p):
        """Apply current TM to point p."""
        return _mtransform(self.ctm(), p)

    def rimage(self, v):
        """Apply linear component of TM to vector v."""
        return _mrtransform(self.ctm(), v)

    # ------------------------------------------------------------------
    #  path construction  (NEWPATH / MOVETO / LINETO / CURVETO / CLOSEPATH)
    # ------------------------------------------------------------------

    def nocurrentpoint(self):
        raise NoCurrentPoint()

    def newpath(self):
        self.setcurrentpoint(None)
        self.cmd.append(NEWPATH)

    def moveto(self, *args):
        P = self._unpack_point(args)
        self.setlastmove(P)
        self.setcurrentpoint(P)
        Q = self.image(P)
        self._emit(MOVETO, Q[0], Q[1])

    def lineto(self, *args):
        if not self.currentpoint():
            self.nocurrentpoint()
        P = self._unpack_point(args)
        self.setlastmove(P)
        self.setcurrentpoint(P)
        Q = self.image(P)
        self._emit(LINETO, Q[0], Q[1])

    def curveto(self, *args):
        if not self.currentpoint():
            self.nocurrentpoint()
        if len(args) == 3:
            P1, P2, P3 = [self.image(p) for p in args]
            self.setcurrentpoint(args[2])
        else:
            P1 = self.image([args[0], args[1]])
            P2 = self.image([args[2], args[3]])
            P3 = self.image([args[4], args[5]])
            self.setcurrentpoint([args[4], args[5]])
        self._emit(CURVETO, P1[0], P1[1], P2[0], P2[1], P3[0], P3[1])

    def closepath(self):
        self.cmd.append(CLOSEPATH)

    # ------------------------------------------------------------------
    #  realizing  (FILL / STROKE / CFILL / CSTROKE / CLIP)
    # ------------------------------------------------------------------

    def fill(self, *args):
        self.setcurrentpoint(None)
        c = VectorUtils.parse_color(*args)
        if c is None:
            self.cmd.append(FILL)
        else:
            self._emit(CFILL, *c)

    def stroke(self, *args):
        self.setcurrentpoint(None)
        c = VectorUtils.parse_color(*args)
        if c is None:
            self.cmd.append(STROKE)
        else:
            self._emit(CSTROKE, *c)

    def clip(self):
        self.cmd.append(CLIP)

    # ------------------------------------------------------------------
    #  graphics state parameters
    # ------------------------------------------------------------------

    def setlinewidth(self, w):
        Graphics.setlinewidth(self, w)
        self._emit(SETLINEWIDTH, w)

    def setlinecap(self, n):
        Graphics.setlinecap(self, n)
        self._emit(SETLINECAP, n)

    def setmiterlimit(self, x):
        Graphics.setmiterlimit(self, x)
        self._emit(SETMITERLIMIT, x)

    def setlinejoin(self, n):
        Graphics.setlinejoin(self, n)
        self._emit(SETLINEJOIN, n)

    def setdash(self, a, off):
        Graphics.setdash(self, a, off)
        self._emit(SETDASH, a, off)

    def setcolor(self, *args):
        c = list(VectorUtils.parse_color(*args))
        Graphics.setcolor(self, c)
        self._emit(SETCOLOR, *c)

    def scalelinewidth(self, s):
        Graphics.scalelinewidth(self, s)
        self._emit(SCALELINEWIDTH, s)

    # ------------------------------------------------------------------
    #  images
    # ------------------------------------------------------------------

    def put_image(self, img, n, interpolate):
        self.gsave()
        self._emit(IMAGE, img, n, interpolate, self.ctm())
        self.grestore()

    # ------------------------------------------------------------------
    #  miscellaneous
    # ------------------------------------------------------------------

    def insert(self, s):
        self._emit(INSERT, s)

    def comment(self, s):
        self._emit(COMMENT, s)

    # ------------------------------------------------------------------
    #  text
    # ------------------------------------------------------------------

    def setfont(self, fontName, size):
        f = self.fontTable.findFont(fontName)
        self.setcurrentfont(Font(f, fontName, size))
        self._emit(SETFONT, f.uniqueName(), size)

    @staticmethod
    def updatecharlist(s, f):
        for c in s:
            f.useChar(c)

    def show(self, s):
        if isinstance(s, StringInsert):
            s = s.string
        if isinstance(s, str):
            s = [ord(c) for c in s]
        if Graphics.isarray(s):
            if not self.currentpoint():
                self.moveto(0, 0)
            f = self.currentfont().font
            self.updatecharlist(s, f)
            M = _mconcat(self.m, self.ctm())
            self._emit(SHOW, s, M)
        else:
            print("\n--- Invalid argument in show! ---\n")

    # ------------------------------------------------------------------
    #  embedding  (EMBED)
    # ------------------------------------------------------------------

    def place(self, canvas, *args):
        if canvas.pinned:
            return canvas.texstring
        if not args:
            P = (0, 0)
        elif len(args) == 1:
            P = args[0]
        elif len(args) == 2:
            P = (args[0], args[1])
        self.fontTable.merge(canvas.fontTable)
        v = self.cgs().transform(P)
        c = canvas.clone()
        c.m = _mconcat((1, 0, 0, 1, v[0], v[1]), c.m)
        self._emit(EMBED, c)

    def embed(self, canvas):
        self.fontTable.merge(canvas.fontTable)
        self.gsave()
        c = canvas.clone()
        c.m = _mconcat(self.ctm(), c.m)
        self._emit(EMBED, c)
        self.grestore()

    # ------------------------------------------------------------------
    #  shfill
    # ------------------------------------------------------------------

    def shfill(self, data):
        self.cmd.append(SHFILL)
        self.cmd.append(4)
        self.cmd.append([[[self.image(p[0]), p[1]] for p in t] for t in data])

    def shcoons(self, data):
        self._emit(SHFILL, 6, [x for t in data for x in t])

    def shstroke(self, data):
        self._emit(SHFILL, 2, data)

    # ------------------------------------------------------------------
    #  derivative shapes
    # ------------------------------------------------------------------

    def connectto(self, *args):
        if self.currentpoint():
            self.lineto(*args)
        else:
            self.moveto(*args)

    def rmoveto(self, *args):
        P = self.currentpoint()
        if not P:
            self.nocurrentpoint()
        V = self._unpack_point(args)
        self.setrcurrentpoint(V)
        self.moveto(P[0] + V[0], P[1] + V[1])

    def rlineto(self, *args):
        P = self.currentpoint()
        if not P:
            self.nocurrentpoint()
        V = self._unpack_point(args)
        self.setrcurrentpoint(V)
        self.lineto(P[0] + V[0], P[1] + V[1])

    def quadto(self, *args):
        P0 = self.currentpoint()
        if not P0:
            self.nocurrentpoint()
        if len(args) == 2:
            P1, P2 = args[0], args[1]
        else:
            P1 = [args[0], args[1]]
            P2 = [args[2], args[3]]
        s, t = 2.0 / 3, 1.0 / 3
        self.curveto(
            t * P0[0] + s * P1[0], t * P0[1] + s * P1[1],
            s * P1[0] + t * P2[0], s * P1[1] + t * P2[1],
            P2[0], P2[1],
        )

    # ------------------------------------------------------------------
    #  geometry
    # ------------------------------------------------------------------

    def boundedbox(self, *args):
        if len(args) == 1:
            llx, lly, urx, ury = args[0][0], args[0][1], args[0][2], args[0][3]
        elif len(args) == 2:
            llx, lly = args[0][0], args[0][1]
            urx, ury = args[1][0], args[1][1]
        else:
            llx, lly, urx, ury = args[0], args[1], args[2], args[3]
        self.moveto(llx, lly)
        self.lineto(urx, lly)
        self.lineto(urx, ury)
        self.lineto(llx, ury)
        self.closepath()

    def envelope(self, bbox, delta):
        dx1, dy1, dx2, dy2 = delta
        return [
            (bbox[0][0] + dx1, bbox[0][1] + dy1),
            (bbox[1][0] + dx2, bbox[1][1] + dy1),
            (bbox[2][0] + dx2, bbox[2][1] + dy2),
            (bbox[3][0] + dx1, bbox[3][1] + dy2),
        ]

    def setbbox(self, bbox):
        if isinstance(bbox[0], (list, tuple)):
            self.bbox = [bbox[0][0], bbox[0][1], bbox[2][0], bbox[2][1]]
        else:
            self.bbox = bbox

    # ------------------------------------------------------------------
    #  display
    # ------------------------------------------------------------------

    def __str__(self):
        s = "(" + ", ".join(Fstr.cstr(x) for x in self.m) + ", )\n"
        return s + to_string(self.cmd)
