import os
import copy
from io import StringIO

"""
import logging
logging.basicConfig(level=logging.DEBUG)
"""

from piscript.knuth import knuth
from piscript.DviFont import *
import piscript.VirtualFont as VirtualFont
import subprocess

def Kstr(x):
    return("%7.2f" % x)

"""
.dvi file reading:
    a .dvi file is a string of bytes
    partitioned into commands
    each command is an array of bytes
    the initial one is the command index;
        near the beginning the total length of the command
        and maybe the number of bytes in various parts is specified

    While reading the file, the state is essentially specified by
        (a) the current font
        (b) an array [ h, v, w, x, y, z ]
        (c) a stack of such arrays
    but in fact I keep track of various other things, too.

    [h, v] is the current position
    [w, x, y, z] specify certain dimensions

    The coordinate system has origin at upper left, v-axis going down.
        This is because then it doesn't have to know what the page size is.
        The graphics rendering program might do this;
        for example DviEPS does, since its coordinate system is at lower left.
    Variables are of two kinds, although confounded in a .dvi file:
        integers and lengths.

        Units of length are sp units, but subject to magnification.
        There are 2^16 sp in a Knuth point, 72.27 Knuth points to an inch,
        which is also equals 72 Adobe points.  A length in Adobe points is obtained from that in sp
        by multiplying it by (mag/1000)*2^{-16}*(72/72.27).

        The design size of a font is specified in sp units.
        The width, height, depth of characters is specified
        as a fraction of font design size, scaled by 2^20.
        So a true character dimension in sp units is
        (font design size)*(character width).

    The command index is in the range [0, 256), so equals one byte
    The data following the index is of two basic types:
        (a) integers of 1-4 bytes
        (b) arrays of bytes, usually strings of characters
    Integers of 1-3 bytes are either signed or unsigned.
        Those of 4 are signed.  These can be either lengths or integers.

    Each command reads its data, but it does not know
        how to use it.  The state the commands change is
        managed by the DviReader, so each command just calls
        back to the Reader to execute.  The most basic DviReader
        just keeps track of where we are on a page,
        also current dimensions, and current fonts.
        It uses stacks to do this.  More advanced Readers such as DviEPS or DviJava
        know how to display the page - this depends on
        what kind of display we are dealing with.

        March 23, 2008: I now plant rules.
"""

# --- dvi command indices ---

SETRULE = 132
PUTRULE = 137
NOP = 138
BOP = 139
EOP = 140
PUSH = 141
POP = 142
FNT1 = 235
FNT2 = 236
FNT3 = 237
FNT4 = 238
XXX1 = 239
XXX2 = 240
XXX3 = 241
XXX4 = 242
FNTDEF1 = 243
FNTDEF2 = 244
FNTDEF3 = 245
FNTDEF4 = 246
PRE = 247
POST = 248
POSTPOST = 249

# ===========================================================================
#  DviCommand base
# ===========================================================================

class DviCommand:
    """Base for all DVI command classes.

    Subclasses may set:
        INDEX  -- fixed opcode (used when no index is passed to __init__)
        _NAME  -- display name (defaults to class name)

    execute() auto-dispatches to dvr.exec<ClassName>(self).
    """
    INDEX = None

    def __init__(self, dvr, i=None):
        self.dvr = dvr
        self.index = i if i is not None else self.INDEX
        self.length = 1

    def read(self, input):
        pass

    def execute(self):
        getattr(self.dvr, 'exec' + type(self).__name__)(self)

    def __str__(self):
        name = getattr(self, '_NAME', type(self).__name__)
        return f"[{self.index}] {name}"

    def readable(self, dvr):
        return str(self)


# ===========================================================================
#  Read-method factories
# ===========================================================================

def _uread(base, attr='c'):
    """Return a read() that slurps an unsigned int.  Byte count = index - base."""
    def read(self, input):
        m = self.index - base
        setattr(self, attr, knuth.getUnsigned(input, m))
        self.length = m + 1
    return read


def _sread(base, attr='b'):
    """Return a read() that slurps a signed int.  Byte count = index - base."""
    def read(self, input):
        m = self.index - base
        setattr(self, attr, knuth.getInt(input, m))
        self.length = m + 1
    return read


# ===========================================================================
#  Factory
# ===========================================================================

def _make_cmd(name, **ns):
    """Create a DviCommand subclass.  ns provides method/attr overrides."""
    return type(name, (DviCommand,), ns)


# ===========================================================================
#  A. Factory-generated simple commands
# ===========================================================================

# --- A1.  Fixed-index, no read, auto-execute (push/pop/eop) ---

Push = _make_cmd('Push', INDEX=PUSH)
Pop  = _make_cmd('Pop',  INDEX=POP)
Eop  = _make_cmd('Eop',  INDEX=EOP)

# --- A2.  W0 / X0 / Y0 / Z0 : no read, display dvr state, auto-execute ---

W0 = _make_cmd('W0', INDEX=147,
    __str__=lambda self: f"w0:{self.dvr.w}")

X0 = _make_cmd('X0', INDEX=152,
    __str__=lambda self: f"x0:{self.dvr.x}")

Y0 = _make_cmd('Y0', INDEX=161,
    __str__=lambda self: f"y0:{self.dvr.y}")

Z0 = _make_cmd('Z0', INDEX=166,
    __str__=lambda self: f"z0:{self.dvr.z}")

# --- A3.  Read one unsigned int, auto-execute ---

Set = _make_cmd('Set', _NAME='set', read=_uread(127, 'c'),
    __str__=lambda self: f"set {self.index - 127} {self.c}",
    getCharIndex=lambda self: self.c)

Put = _make_cmd('Put', _NAME='put', read=_uread(132, 'c'),
    __str__=lambda self: f"put {self.index - 132}")

Fnt = _make_cmd('Fnt', read=_uread(234, 'k'),
    __str__=lambda self: f"fnt {self.k}")

FntNum = _make_cmd('FntNum',
    __str__=lambda self: f"font num {self.index - 171}")

# --- A4.  Read one signed int, auto-execute ---

Right = _make_cmd('Right', read=_sread(142, 'b'),
    __str__=lambda self: f"right: {self.b}")

Down  = _make_cmd('Down',  read=_sread(156, 'a'),
    __str__=lambda self: f"down{self.index - 156}: {self.a}")

W     = _make_cmd('W',     read=_sread(147, 'b'),
    __str__=lambda self: f"w{self.index - 147}:{self.b}")

X     = _make_cmd('X',     read=_sread(152, 'b'),
    __str__=lambda self: f"x{self.index - 152}:{self.b}")

Y     = _make_cmd('Y',     read=_sread(161, 'a'),
    __str__=lambda self: f"y{self.index - 161}:{self.a}")

Z     = _make_cmd('Z',     read=_sread(166, 'a'),
    __str__=lambda self: f"z{self.index - 166}:{self.a}")


# ===========================================================================
#  B. Hand-written (complex read / custom execute / special display)
# ===========================================================================

class SetChar(DviCommand):
    """Indices 0-127: the index itself is the character code."""
    _NAME = "set char"

    def __str__(self):
        return f"set char {chr(self.index)}({self.index})"

    def getCharIndex(self):
        return self.index


class SetRule(DviCommand):
    """Index 132: a[4] b[4] — set rule, changes h."""
    INDEX = SETRULE
    _NAME = "set rule"

    def readable(self, dvr):
        return "set rule:" + Kstr(dvr.sptoadobe(self.a)) + " x " + Kstr(dvr.sptoadobe(self.b))

    def read(self, input):
        self.a = knuth.getInt(input, 4)
        self.b = knuth.getInt(input, 4)
        self.length = 9


class PutRule(DviCommand):
    """Index 137: a[4] b[4] — put rule, no position change."""
    INDEX = PUTRULE

    def __str__(self):
        return f"put rule:{self.a} x {self.b}"

    def read(self, input):
        self.a = knuth.getInt(input, 4)
        self.b = knuth.getInt(input, 4)
        self.length = 9


class Nop(DviCommand):
    """Index 138: does nothing."""
    INDEX = NOP

    def __str__(self):
        return "nop"

    def execute(self):
        return None


class Bop(DviCommand):
    """Index 139: begin page.  c[0..9][4] p[4]."""
    INDEX = BOP

    def read(self, input):
        self.c = [knuth.getInt(input, 4) for _ in range(10)]
        self.p = knuth.getInt(input, 4)
        self.length = 45

    def __str__(self):
        return "bop"


class XXX(DviCommand):
    """Indices 239-242: k[1..4] x[k] — specials."""

    def read(self, input):
        m = self.index - 238
        k = knuth.getUnsigned(input, m)
        self.x = knuth.getString(input, k)
        self.length = 1 + m + k

    def __str__(self):
        return "xxx "

    def execute(self):
        self.dvr.doSpecial(self.x)


class FntDef(DviCommand):
    """Indices 243-246: font definition."""

    def __str__(self):
        if self.directory:
            s = f"font def {self.k}: {os.path.join(self.directory, self.fontfile)}"
        else:
            s = f"font def {self.k}: {self.fontfile}"
        return s + f" {self.s}, {self.d}"

    def readable(self, dvr):
        if self.directory:
            s = f"font def {self.k}: {os.path.join(self.directory, self.fontfile)}"
        else:
            s = f"font def {self.k}: {self.fontfile}"
        return s + f" {Kstr(dvr.sptoadobe(self.s))}, {Kstr(dvr.sptoadobe(self.d))}"

    def read(self, input):
        m = self.index - 242
        self.k = knuth.getUnsigned(input, m)
        self.c = knuth.getUnsigned(input, 4)
        self.s = knuth.getUnsigned(input, 4)
        self.d = knuth.getUnsigned(input, 4)
        a = input.read(1)[0]
        ell = input.read(1)[0]
        self.directory = knuth.getString(input, a)
        self.fontfile = knuth.getString(input, ell)
        self.length = m + 15 + a + ell


class PreAmble(DviCommand):
    """Index 247: preamble."""
    INDEX = PRE

    def __str__(self):
        return f"preamble: {self.x}" if self.x else "preamble"

    def read(self, input):
        self.i = input.read(1)
        self.num = knuth.getUnsigned(input, 4)
        self.den = knuth.getUnsigned(input, 4)
        self.mag = knuth.getUnsigned(input, 4)
        k = input.read(1)[0]
        self.x = knuth.getString(input, k)
        self.length = 15 + k


class PostAmble(DviCommand):
    """Index 248: postamble."""
    INDEX = POST

    def __str__(self):
        return "postamble"

    def read(self, input):
        self.p = knuth.getInt(input, 4)
        self.num = knuth.getInt(input, 4)
        self.den = knuth.getInt(input, 4)
        self.mag = knuth.getInt(input, 4)
        self.ell = knuth.getInt(input, 4)
        self.u = knuth.getInt(input, 4)
        self.s = knuth.getUnsigned(input, 2)
        self.t = knuth.getUnsigned(input, 2)
        self.length = 29


class PostPostAmble(DviCommand):
    """Index 249: post-postamble."""
    INDEX = POSTPOST

    def __str__(self):
        return "postpostamble"

    def read(self, input):
        self.q = knuth.getInt(input, 4)
        self.i = knuth.getInt(input, 1)
        c = input.read(1)[0]
        f = 0
        while ((c + 256) & 255) == 223:
            f += 1
            b = input.read(1)
            if b:
                c = b[0]
            else:
                break
        self.length = 6 + f


class VIllegal(DviCommand):
    """Placeholder for illegal commands in virtual fonts."""

    def __init__(self, dvr, k):
        DviCommand.__init__(self, dvr, k)

    def __str__(self):
        return f"Illegal VFont command {self.index}"

    def read(self, input):
        logging.error(str(self))

    def execute(self):
        logging.error(str(self))


# ===========================================================================
#  C.  mkCommands  —  declarative table-driven construction
# ===========================================================================

# Each entry: (klass, start, end, has_index_arg)
#   start/end = range of indices [start, end); if None → singleton (no loop)
#   has_index_arg = True if the class __init__ takes (dvr, index)

_COMMAND_TABLE = [
    (SetChar,       0,   128, True),
    (Set,         128,   132, True),
    (SetRule,    None,  None, False),
    (Put,         133,   137, True),
    (PutRule,    None,  None, False),
    (Nop,        None,  None, False),
    (Bop,        None,  None, False),
    (Eop,        None,  None, False),
    (Push,       None,  None, False),
    (Pop,        None,  None, False),
    (Right,       143,   147, True),
    (W0,        None,  None, False),
    (W,          148,   152, True),
    (X0,        None,  None, False),
    (X,          153,   157, True),
    (Down,        157,   161, True),
    (Y0,        None,  None, False),
    (Y,          162,   166, True),
    (Z0,        None,  None, False),
    (Z,          167,   171, True),
    (FntNum,      171,   235, True),
    (Fnt,         235,   239, True),
    (XXX,         239,   243, True),
    (FntDef,      243,   247, True),
    (PreAmble,   None,  None, False),
    (PostAmble,  None,  None, False),
    (PostPostAmble, None, None, False),
]


def _build_commands(dvr, table):
    """Build the 250-element command dispatch array from a declarative table."""
    cmd = []
    for klass, start, end, has_index in table:
        if start is not None:
            for i in range(start, end):
                cmd.append(klass(dvr, i) if has_index else klass(dvr))
        else:
            cmd.append(klass(dvr))
    return cmd


# ===========================================================================
#  DviReader
# ===========================================================================


"""
    DviReader reads commands from the .dvi file
    and execute them. The basic DviReader just
    keeps track of the current state,
    without doing anything else.
    Extensions will display the file in various media.

    The most complicated structures it deals with are DviFonts.
"""

class DviReader:

    """
    The current state:

        * int h, v, w, x, y, z

        These are positions, measured in the units
        specified by num, den relative to sp.
        In particular, h and v are the current
        horizontal and vertical coordinates.

        * Stack dims

        Stores dimension arrays.  Used as a primnitive graphisc state
        in PostScript.  Here implemented as a list.  It is started all over
        at the beginning of each page.

        * DviFont currentFont
        * int currentPageNo

        In some versions, we need to access pages independently.

        * int num, den, mag
        Variables set once at the start of every file.

        * Stack fonts

        Used to assemble a list of all fonts.

        * Stack currentPage

        Used to assemble the current page. */

        * Hashtable fontTable

        Records fonts so far defined.  Implemented as a dictionary.

        A list of the fonts that haven't been located. */

        * InputStream input

        * DviCommand[] command
"""

    def __init__(self, file):
        self.input = open(file + ".dvi", "rb")
        self.mkCommands()
        self.fontTable = {}
        currentPageNo = -1
        self.descendingVirtualFonts = True
        self.scaleFactor = 1
        self.vFontStates = []
        self.currentFont = None
        self.h = 0
        self.v = 0
        self.w = 0
        self.x = 0
        self.y = 0
        self.z = 0
        self.minwdSet = False
        self.maxwdSet = False
        self.maxhtSet = False
        self.minhtSet = False
        self.maxlevelSet = False
        P = []
        c = self.getpre()
        self.mag = c.mag
        c = self.getpostpost()
        n = c.q
        P.append(n)
        c = self.getcommandat(c.q)
        n = c.p
        while not n == -1:
            P.append(n)
            c = self.getcommandat(n)
            n = c.p
        self.page = []
        for i in range(len(P)):
            self.page.append(P[i-1])
        self.input.close()
        self.input = open(file + ".dvi", "rb")

    def getpre(self):
        self.input.seek(0,0)
        c = self.getCommand()
        return(c)

    def getpostpost(self):
        k = 1
        while(True):
            self.input.seek(-k,2)
            s = self.input.read(1)[0]
            if not s == 223:
                break
            k += 1
        self.input.seek(-k-5,2)
        c = self.getCommand()
        return c

    def getcommandat(self,n):
        self.input.seek(n, 0)
        c = self.getCommand()
        return c


    def readpage(self, n):
        pass

    def mkCommands(self):
        command = _build_commands(self, _COMMAND_TABLE)

        # Virtual-font variant: ban Bop, Eop, FntDef, PreAmble, PostAmble, PostPostAmble
        vfont_command = list(command)
        vfont_command[BOP] = VIllegal(self, BOP)
        vfont_command[EOP] = VIllegal(self, EOP)
        for i in range(243, 248):
            vfont_command[i] = VIllegal(self, i)

        self.standard_command = command
        self.vfont_command = vfont_command
        self.command = self.standard_command

    def render(self):
        while (True):
            c = self.getCommand()
            c.execute()
            P = self.getCurrentPosition()
            print(c.readable(self))
            print("\t(" + Kstr(self.sptoadobe(P[0])) + ", " + Kstr(self.sptoadobe(P[1])) + ")")
            if (c.index == self.EOF()):
                break

    def getCommand(self):
        while( (len(self.vFontStates) > 0) and (self.input.pos>=self.input.len) ):
            self.popVFont()
        n = self.input.read(1)[0]
        self.command[n].read(self.input)
        return(self.command[n])

    def getCurrentPosition(self):
        return([self.h, self.v])

    def EOF(self):
        return(POST)

    def close(self):
        self.input.close()

    def sptoadobe(self, x):
        return(x*(72/72.27)*self.mag/(1000.0*(1 << 16)))

    def Str(x):
        return("%3.4f" % x)
    Str=staticmethod(Str)

    # adjust minimum width etc.
    def adjustbbox(self, c):
        loc = self.getCurrentPosition()
        w = self.currentFont.getCharWidth(c)
        h = self.currentFont.getCharHeight(c)
        d = self.currentFont.getCharDepth(c)
        ss = self.currentFont.scaledSize
        if not self.maxlevelSet:
            self.maxlevel = loc[1]
            self.maxlevelSet = True
        else:
            level = loc[1]
            if (level > self.maxlevel):
                self.maxlevel = level
        if not self.minwdSet:
            self.minwd = loc[0] - w*ss
            self.minwdSet = True
        else:
            wd = loc[0] - w*ss
            if (wd < self.minwd):
                self.minwd = wd
        if not self.maxwdSet:
            self.maxwd = loc[0]
            self.maxwdSet = True
        else:
            wd = loc[0]
            if (wd > self.maxwd):
                self.maxwd = wd
        if not self.minhtSet:
            self.minht = loc[1]-h*ss;
            self.minhtSet = True
        else:
            ht = loc[1]-h*ss
            if (ht < self.minht):
                self.minht = ht
        if not self.maxhtSet:
            self.maxht = loc[1]+d*ss
            self.maxhtSet = True
        else:
            ht = loc[1]+ss*d
            if (ht > self.maxht):
                self.maxht = ht

    def startFont( self, font ):
        self.currentFont = font
        if( not self.currentFont.isUsed ):
            self.currentFont.load()

    def pushVFont( self, cindex):
        vFont = self.currentFont.vChars
        self.dims.append([ self.h, self.v, self.w, self.x, self.y, self.z])
        self.vFontStates.append([ self.dims, self.currentFont, self.scaleFactor, self.fontTable, self.input ])
        self.w=0; self.x=0; self.y=0; self.z=0;
        self.fontTable = vFont.fontTable
        self.scaleFactor *= (self.currentFont.scaledSize*1.0/(1 << 20))
        self.currentFont = vFont.defaultFont
        if( self.currentFont != None ):
            self.startFont( self.currentFont );
        self.dims=[]
        self.input = StringIO(vFont.packets[cindex].dvi)
        self.command = self.vfont_command

    def popVFont( self ):
        self.input.close()
        [ self.dims, self.currentFont, self.scaleFactor, self.fontTable, self.input ] = self.vFontStates.pop()
        [ self.h, self.v, self.w, self.x, self.y, self.z ] = self.dims.pop()
        self.command = self.standard_command

    # --- execution methods ---

    def execSetChar(self, dvc):
        cw = self.currentFont.getCharWidth(dvc.index)
        ss = self.currentFont.scaledSize
        dh = cw*ss*self.scaleFactor
        self.h += dh
        if( self.currentFont.isVirtual and self.descendingVirtualFonts):
            self.pushVFont( dvc.index )
            self.h -= dh

    def execFntNum(self, dvc):
        self.startFont( self.fontTable.get("f" + str(dvc.index-171) ) )

    def execFnt(self, dvc):
        self.startFont( self.fontTable.get("f" + str(dvc.k)) )

    def execSetRule(self, dvc):
        self.h += dvc.b*self.scaleFactor

    def execPutRule(self, dvc):
        return None

    def execSet(self, dvc):
        cw = self.currentFont.getCharWidth(dvc.c)
        ss = self.currentFont.scaledSize
        dh = cw*ss*self.scaleFactor
        self.h += dh
        if( self.currentFont.isVirtual and self.descendingVirtualFonts):
            self.pushVFont( dvc.c )
            self.h -= dh

    def execPut(self, dvc):
        return None

    def execBop(self, dvc):
        self.h = 0
        self.v = 0
        self.w = 0
        self.x = 0
        self.y = 0
        self.z = 0
        self.dims = []
        self.currentFont = None
        self.currentPage = []

    def execFntDef(self, dvc):
        key = "f" + str(dvc.k)
        if (self.fontTable.get(key) == None):
            tf = DviFont(dvc.fontfile, dvc.s, dvc.d, dvc.k)
            self.fontTable[key] = tf

    def execEop(self, dvc):
        return None

    def execPush(self, dvc):
        V = [ self.h, self.v, self.w, self.x, self.y, self.z ]
        self.dims.append(V)

    def execPop(self, dvc):
        self.h, self.v, self.w, self.x, self.y, self.z = self.dims.pop()

    def execPreAmble(self, dvc):
        self.num = dvc.num
        self.den = dvc.den
        self.mag = dvc.mag
        self.ell = dvc.mag/1000.0

    def execXXX(self, dvc):
        s = dvc.x
        self.doSpecial(s)

    def execRight(self, dvc):
        self.h += dvc.b*self.scaleFactor

    def execDown(self, dvc):
        self.v += dvc.a*self.scaleFactor

    def execW0(self, dvc):
        self.h += self.w*self.scaleFactor

    def execW(self, dvc):
        self.w = dvc.b*self.scaleFactor
        self.h += self.w

    def execX0(self, dvc):
        self.h += self.x

    def execX(self, dvc):
        self.x = dvc.b*self.scaleFactor
        self.h += self.x

    def execY0(self, dvc):
        self.v += self.y

    def execY(self, dvc):
        self.y = dvc.a*self.scaleFactor
        self.v += self.y

    def execZ0(self, dvc):
        self.v += self.z

    def execZ(self, dvc):
        self.z = dvc.a*self.scaleFactor
        self.v += self.z

    def execPostAmble(self, dvc):
        return None

    def execPostPostAmble(self, dvc):
        return None

    # --------------------------------------------------------------

    def doSpecial(self, s):
        pass
