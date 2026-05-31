import piscript.FindResource as FindResource
import piscript.DeviceFont as DeviceFont
import piscript.PSReadable as PSReadable
from piscript.Canvas import Canvas
from piscript.StringInsert import StringInsert
import piscript.FontMap as FontMap
from piscript.Type1 import Type1Font
from piscript.DviToDevice import DviDevice
from piscript.PSMatrix import transform as _transform
# from BuildChar import BuildChar

import re
import math    

"""
import logging
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
"""

""" A TexInsert has a collection of significant points:
    that specify its geometry: ll, lr, ul, ur, origin, and marks """

class TexInsert(Canvas):
    def __init__(self):
        Canvas.__init__(self)
        self.bbox = [ 0, 0, 1, 1 ]
        self.mark = []
        self.origin = None # [ 0, 0 ]
        self.insert = None
        self.pinned = False
        self.texstring = None
        # eventually gets also width, height, depth

    def center(self):
        c = self.currentcenter()
        self.translate(-c[0], -c[1])

    def currentcenter(self):
        m = self.m
        b = self.bbox
        x = 0.5*(b[0]+b[2])
        y = 0.5*(b[1]+b[3])
        return _transform(m, (x, y))

    def currentll(self):
        m = self.m
        return _transform(m, (self.origbbox[0], self.origbbox[1]))

    def currentul(self):
        m = self.m
        return _transform(m, (self.origbbox[0], self.origbbox[3]))

    def currentur(self):
        m = self.m
        return _transform(m, (self.origbbox[2], self.origbbox[3]))

    def currentlr(self):
        m = self.m
        return _transform(m, (self.origbbox[2], self.origbbox[1]))

    def currentorigin(self):
        m = self.m
        return _transform(m, self.origorigin)

    def currentbbox(self):
        return (self.currentll(), self.currentlr(), self.currentur(), self.currentul())
    
    def currentmark(self, i):
        m = self.m
        return _transform(m, self.origMark[i])

    def pin(self):
        self.pinned = True

    def unpin(self):
        self.pinned = False
    
    """
    # setorigin(center) sets the center at the current origin
    def setorigin(self, *args):
        if len(args) > 1:
            x = args[0]; y = args[1] 
        else:
            P = args[0]
            x = P[0]; y = P[1]
        self.translate(-x,-y)
    """

    """ A TexInsert is really a restricted Canvas
    you cannot draw into it,
    and rotate etc.move *it* around, not the coordinate frame. 
    Here is a rough list of the variables and commands implemented:

        dvifont.deviceFont = self.insert.fontTable.findFont( dvifont.fontName )
        self.insert.setfont( dvifont.fontName, fontSize )
        self.insert.moveto( x, y)
        self.insert.show( s )
        self.insert.newpath()
        self.insert.moveto(x,y)
        self.insert.rlineto( w ,0 )
        self.insert.rlineto( 0 ,h )
        self.insert.rlineto( -w ,0 )
        self.insert.closepath()
        self.insert.fill()        
        self.insert.setcolor(color)
        self.insert.grestore() 
        insert.glevel == 1:
        insert.translate([-O[0], -O[1]])
        insert.bbox = [ ll[0] - O[0], ll[1] - O[1], ur[0] - O[0], ur[1] - O[1] ]
        insert.width = ur[0] - ll[0]
        insert.height = ur[1] - O[1]
        insert.depth = O[1] - ll[1]
        insert.origin = (0, 0)
        for m in self.mark:
            insert.mark.append([m[0]-O[0], m[1]-O[1]])

    """

    # the next several methods are a bit weird
    # first part is static; second part applies to self instead of the Canvas
    # well, not exactly; first applies on *left* to prematrix Canvas.m
    # whereas ordinary transforms apply to *right* of graphics matrix

    # args = (V), (x, y)
    def translate(self, *args):
        C = self
        # multiply C's m on the left by the translation matrix
        if (len(args) == 1):
            V = args[0]
            x = V[0]
            y = V[1]
        else: # two arguments
            x = args[0]
            y = args[1]
        m = C.m
        C.m = (m[0], m[1], m[2], m[3], m[4] + x, m[5] + y)

    def center(self):
        self.translate(-self.width/2.0, -self.height/2.0)

    # args = (a), (a, O), (a, x, y) 
    def rotate(self, *args):
        C = self
        if len(args) == 1: # a
            x = 0; y = 0
            a = self.toRad*args[0]
        elif len(args) == 2: # [x,y], a
            x = args[0][0]
            y = args[0][1]
            a = self.toRad*args[1]
        else: # x, y, a
            # affine rotation around (x, y)
            x = args[0]
            y = args[1]
            a = self.toRad*args[2]
        c = math.cos(a)
        s = math.sin(a)
        # A = [ c, s, -s, c, x-c*x+s*y, y-s*x-c*y ]
        # print "A=", [ c, s, -s, c, x-c*x+s*y, y-s*x-c*y ]
        m = C.m
        """
            c  -s  x-c*x+s*y    m0 m2 m4
            s   c  y-s*x-c*y    m1 m3 m5
               0   0      1      0  0  1
        """
        x0 = c*m[0]-s*m[1]
        y0 = s*m[0]+c*m[1]
        # m[0] = x; m[1] = y
        x1 = c*m[2]-s*m[3]
        y1 = s*m[2]+c*m[3]
        # m[2] = x; m[3] = y
        x2 = c*m[4]-s*m[5]+(x-c*x+s*y)
        y2 = s*m[4]+c*m[5]+(y-s*x-c*y)
        # m[4] = x; m[5] = y
        C.m = (x0, y0, x1, y1, x2, y2)

    # (s), (s, t)
    def scale(self, *args):
        C = self
        if len(args) == 1:
            s = args[0]
            t = s
        else:
            s = args[0]
            t = args[1]
        m = C.m
        """
            s  0  0    m0 m2 m4
            0  t  0    m1 m3 m5
            0  0  1     0  0  1
        """
        C.m = (m[0]*s, m[1]*t, m[2]*s, m[3]*t, m[4]*s, m[5]*t)

    # args =(1) array of 6 numbers; (2) array of 2 vectors; or (3) of 3 vectors
    def atransform(self, *args):
        C = self
        if len(args) == 1: # a single array of 6 numbers
            a = args[0]
        elif len(args) == 2: # a0, a1
            a = [ args[0][0], args[0][1], args[1][0], args[1][1], 0, 0 ]
        else: # 3: a0 a1 a2
            a = [ args[0][0], args[0][1], args[1][0], args[1][1], args[2][0], args[2][1] ]
        m = C.m
        """
            a0 a2 a4  m0 m2 m4
            a1 a3 a5  m1 m3 m5
             0  0  1   0  0  1
        """
        x0 = a[0]*m[0]+a[2]*m[1]
        y0 = a[1]*m[0]+a[3]*m[1]
        # m[0] = x; m[1] = y
        x1 = a[0]*m[2]+a[2]*m[3]
        y1 = a[1]*m[2]+a[3]*m[3]
        # m[2] = x; m[3] = y
        x2 = a[0]*m[4]+a[2]*m[5]+a[4]
        y2 = a[1]*m[4]+a[3]*m[5]+a[5]
        # m[4] = x; m[5] = y
        C.m = (x0, y0, x1, y1, x2, y2)


# ==================================================================================
# ==================================================================================
# ==================================================================================


# turns a .dvi file into (a) Canvas(es) 
class PysCmdDevice(DviDevice):

    def __init__(self, pageHeight, color):
        DviDevice.__init__( self, prefersChars=False)
        self.pageHeight = pageHeight
        self.mark = []
        self.fontTable = DeviceFont.FontTable()
        self.currentFont = None
        self.pages = []
        self.colorstack = [ color ]

    def dviToPSCoords(self, h, v):
        return (self.spToA * h, self.pageHeight - self.spToA * v)

    def dviToPSDims(self, a, b):
        return (self.spToA * a, self.spToA * b)

    def Str(x):
        return("%3.4f" % x)
    Str=staticmethod(Str)

    def beginDocument( self, num, den, mag, dvr):
        # FIXME (DM 7/9/2009) What are num, den?  We never use them....
        self.num = num;
        self.den = den;
        self.mag = mag;
        self.spToA = (72/72.27)*self.mag/(1000.0*(1 << 16))

    def endDocument( self, dvr ):        
        pass

    # dvr is the actual DviReader
    def beginPage(self, dvr):
        self.insert = TexInsert()
        self.insert.gsave()

    def endPage(self, dvr):
        insert = self.insert
        if not insert.glevel == 1:
            logger.warning("glevel = %s!", insert.glevel)
        while insert.glevel > 0:
            insert.grestore()

        O = self.dviToPSCoords(dvr.origin[0], dvr.origin[1])
        insert.origorigin = (O[0], O[1])
        insert.translate([-O[0], -O[1]])

        ll = self.dviToPSCoords(dvr.minwd, dvr.maxht)
        ur = self.dviToPSCoords(dvr.maxwd, dvr.minht)
        insert.bbox = (ll[0] - O[0], ll[1] - O[1], ur[0] - O[0], ur[1] - O[1])
        insert.origbbox = (ll[0], ll[1], ur[0], ur[1])
        insert.width = ur[0] - ll[0]
        insert.height = ur[1] - O[1]
        insert.depth = O[1] - ll[1]

        insert.origin = (0, 0)
        insert.origin = (0, 0)
        insert.origmark = []
        for m in self.mark:
            insert.mark.append([m[0]-O[0], m[1]-O[1]])
            insert.origmark.append((m[0], m[1]))
        self.pages.append(insert)

    def startFont( self, dvifont, sf, dvr ):
        if(dvifont.deviceFont == None ):
            dvifont.deviceFont = self.insert.fontTable.findFont( dvifont.fontName )
        self.currentFont = dvifont.deviceFont

        fontSize = (dvr.mag/1000.0)
        fontSize *= (dvifont.scaledSize*1.0/(1 << 16))
        fontSize *= sf
        self.insert.setfont( dvifont.fontName, fontSize )

    # NEW: WAC
    # buf = StringInsert, with metric data built in
    def putString( self, S, dvr ):
        metrics = []
        for p in S.metrics:
            q = self.dviToPSCoords(p[0], p[1]) 
            metrics.append(q)
        S.metrics = metrics
        self.insert.moveto(metrics[0])
        buf = S.string
        s = ""
        for c in buf:
            s += chr(c)
        S.string = s
        self.insert.show(S)

    def putRule( self, h, v, a, b, dvr):
        (x,y) = self.dviToPSCoords( h, v)
        (w,h) = self.dviToPSDims( b, a )
        self.insert.newpath()
        self.insert.moveto(x,y)
        self.insert.rlineto( w ,0 )
        self.insert.rlineto( 0 ,h )
        self.insert.rlineto( -w ,0 )
        self.insert.closepath()
        self.insert.fill()        

    def doSpecial(self, s, dvr):
        # Parse TeX \special commands: color{r g b}, uncolor, mark
        args_start = s.find("{")
        args_start = args_start if args_start >= 0 else len(s)
        cmd = s[:args_start].strip()
        args = s[args_start:]

        if cmd in ("Color", "color"):
            m = re.search(r"([\d.]+)\s+([\d.]+)\s+([\d.]+)", args)
            if m:
                color = [float(m.group(1)), float(m.group(2)), float(m.group(3))]
                self.colorstack.append(color)
                self.insert.setcolor(color)
            else:
                logger.warning("Invalid arguments to color")
        elif cmd in ("unColor", "uncolor"):
            if len(self.colorstack) > 1:
                self.colorstack.pop()
                self.insert.setcolor(self.colorstack[-1])
            else:
                logger.warning("Unmatched uncolor!")
        elif cmd == "mark":
            loc = dvr.getCurrentPosition()
            self.mark.append([self.spToA * loc[0],
                               self.pageHeight - self.spToA * loc[1]])
        else:
            pass

    
