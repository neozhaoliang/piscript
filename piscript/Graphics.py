#!/usr/bin/python

from piscript.Fstr import fstr
from piscript.CoordinateSystem import CoordinateSystem
import piscript.VectorUtils as VectorUtils
import math
import numpy as np

import logging
logger = logging.getLogger(__name__)
"""

The graphics state holds

font
linecap (needs to be accessed by Arrows)
linewidth (allows relative dimensioning)
# reversion (reversion mode for Canvases)
coordinate matrices (inherited from CoordinateSystem)

current point
lastmove

There are other thinsg in the PostScript graphics state
that do not need to be accessed in PiScript.

many of these will return variables to be used by PiScript and Path
mode: radians = 0, degrees = 1 

also in new version, tm = array of 6 numbers 

vectors are columns """

class GraphicsState(CoordinateSystem):

    def __init__(self, *args):
        if not args:
            self.tm = [ 1.0, 0.0, 0.0, 1.0, 0.0, 0.0 ]
            self.currentpoint = None
            self.currentfont = None
            self.lastmove = None

            self.linewidth = 1
            self.linecap = 0

            self.color = [0,0,0]
            """
            self.miterlimit = 10.0
            self.linejoin = 0
            self.dash = [[], 0] """

        elif Graphics.isarray(args[0]):
            self.tm = args[0]
            self.currentpoint = None
            self.currentfont = None
            self.lastmove = None
            # self.reversion = True

            self.linewidth = 1
            self.linecap = 0

            self.color = [0,0,0]
            """
            self.miterlimit = 10.0
            self.linejoin = 0
            self.dash = [[], 0] """

        else: # args[0] = another GraphicsState, returns a new copy
            g = args[0]
            tm = g.tm
            self.tm = [ 
                tm[0], tm[1], tm[2], tm[3], tm[4], tm[5]
            ]
            self.currentfont = g.currentfont
            self.currentpoint = g.currentpoint
            self.lastmove = g.lastmove
            # self.reversion = g.reversion

            self.linewidth = g.linewidth
            self.linecap = g.linecap

            self.color = g.color
            """
            self.miterlimit = g.miterlimit
            self.linejoin = g.linejoin
            self.dash = g.dash """

    """ 
    WAC: Pushed these up to CoordinateSystem:
        def transform
        def itransform
        def rtransform
        def inversetm 
    """

    def __str__(self):
        tm = self.tm
        s = "["
        for i in range(6):
            s += " " + fstr(tm[i])
        s += " ] ("
        s += str(self.linewidth)
        s += ")"
        return(s)
        
# ===========================================================================


class Graphics:

    # mode 0 = radians, 1 = degrees
    def __init__(self):
        self.defaultgs = GraphicsState() # used for recovery in case of stack abuse
        self.gstack = [ self.defaultgs ]
        self.glevel = 0
        self.toDeg = 180.0/math.pi  #initial mode = radians
        self.toRad = 1.0
        self.mode = 0 # radians 

    # --- graphics state --------------------------------------------------

    def gsave(self):
        gs = self.gstack[self.glevel]
        C = GraphicsState(gs)
        self.gstack.append(C)
        self.glevel += 1
        
    def grestore(self):
        n = self.glevel
        if n > 0:
            self.gstack.pop()
            self.glevel -= 1
        else:
            print
            
            print("\t*** ERROR: There is an extra grestore! ***")
            print("\t*** Ignoring it ... ***")
            
            print

    # --- coordinate changes ----------------------------------------------------------

    # returns a new copy: no good for setting parameters
    def cgs(self):
        gs = self.gstack[self.glevel]
        return GraphicsState(gs)

    def ctm():
        gs = self.gstack[self.glevel]
        tm = gs.tm
        return [ tm[0], tm[1], tm[2], tm[3], tm[4], tm[5] ]

    def revert(self, linear_only=False):
        gs = self.cgs()
        t = gs.inversetm()
        if linear_only:
            t[4] = 0; t[5] = 0
        self.atransform(t)
        return gs

    def lrevert(self):
        return self.revert(linear_only=True)

    def translate(self, *args):    
        if (len(args) == 1):
            V = args[0]
        else:
            x = args[0]
            y = args[1]
            V = [x, y]
        gs = self.gstack[self.glevel]
        gs.translate(V)
        return V

    def scale(self, *args):
        if len(args) == 1:
            s = args[0]
            if s == "cm":
                s = 72/2.54
            if s == "in":
                s = 72.0
            if s == "mm":
                s = 72/25.4
            if s == "pt":
                s = 1.0
            t = s
        else:
            s = args[0]
            t = args[1]
        gs = self.gstack[self.glevel]
        gs.scale(s, t)
        return [ s, t ]
        
    # a or x, y, a
    def rotate(self, *args):
        gs = self.cgs()
        if len(args) == 1: # a
            # x = 0; y = 0
            a = args[0]
            A = a*self.toRad
            gs = self.gstack[self.glevel]
            gs.rotate(A)
            return [ a ]
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
        A = [ c, s, -s, c, x-c*x+s*y, y-s*x-c*y ]
        gs = self.gstack[self.glevel]
        gs.atransform(A)
        return A

    # f = [a, b, c]
    def reflect(self, *args):
        f = args[0]
        if len(args) > 1:
            v = args[1]
        else:
            v = (f[0], f[1])

        A = VectorUtils.reflected(f, v, (0,0))
        B = VectorUtils.reflected(f, v, (1,0))
        C = VectorUtils.reflected(f, v, (0,1))
        A = (B[0]-A[0], B[1]-A[1], C[0]-A[0], C[1]-A[1], A[0], A[1])
        gs = self.gstack[self.glevel]
        gs.atransform(A)
        return A

    def ltransform(self, *args):
        if len(args) == 1: # a single array of 4 numbers
            a = args[0]
            a.append(0)
            a.append(0)
        else: # len(args) == 2:
            a = [ a[0][0], a[0][1], a[1][0], a[1][1], 0, 0 ]
        gs = self.gstack[self.glevel]
        gs.ltransform(a)
        return a
    
    # args = (1) array of 6 numbers; (2) array of 2 vectors; (3) of 3 vectors
    def atransform(self, *args):
        if len(args) == 1: # a single array of 6 numbers
            a = args[0]
        elif len(args) == 2: # a0, a1
            a = [ args[0][0], args[0][1], args[1][0], args[1][1], 0, 0 ]
        else: # 3: a0 a1 a2
            a = [ args[0][0], args[0][1], args[1][0], args[1][1], args[2][0], args[2][1] ] 
        gs = self.gstack[self.glevel]
        gs.atransform(a)
        return a
        
    # ---------------------------------------------------------------------------

    # ---- current graphics state accessor ----

    def _gs(self):
        return self.gstack[self.glevel]

    # ---- line / color / dash parameters ----

    def scalelinewidth(self, c):
        self._gs().linewidth *= c

    def setcolor(self, c):
        self._gs().color = c

    def currentcolor(self):
        return self._gs().color

    def setlinewidth(self, c):
        self._gs().linewidth = c

    def currentlinewidth(self):
        return self._gs().linewidth

    def setlinecap(self, n):
        self._gs().linecap = n

    def currentlinecap(self):
        return self._gs().linecap

    def setlinejoin(self, n):
        self._gs().linejoin = n

    def currentlinejoin(self):
        return self._gs().linejoin

    def setdash(self, a, o):
        self._gs().dash = [a, o]

    def currentdash(self):
        return self._gs().dash

    def setmiterlimit(self, x):
        self._gs().miterlimit = x

    def currentmiterlimit(self):
        return self._gs().miterlimit

    def setcurrentfont(self, f):
        gs = self.gstack[self.glevel]
        gs.currentfont = f
        
    def currentfont(self):
        gs = self.gstack[self.glevel]
        return gs.currentfont

    def setdeg(self):
        self.mode = 1
        self.toDeg = 1
        self.toRad = math.pi/180.0

    def setrad(self):
        self.mode = 0
        self.toDeg = 180.0/math.pi
        self.toRad = 1
    
    # --- the current point is stored in default coords -------------------
    
    def setcurrentpoint(self, P):
        gs = self.gstack[self.glevel]
        if P is not None:
            P = gs.transform(P)
            gs.currentpoint = P
        else:
            gs.currentpoint = None

    # shifts the current point by V
    def setrcurrentpoint(self, V):
        gs = self.gstack[self.glevel]
        V = gs.rtransform(V)
        P = gs.currentpoint
        P[0] += V[0]
        P[1] += V[1]

    def lastmove(self):
        gs = self.gstack[self.glevel]
        P = gs.lastmove
        P = gs.itransform(P)
        return P
        
    def setlastmove(self, P):
        gs = self.gstack[self.glevel]
        P = gs.transform(P)
        gs.lastmove = P
    
    def currentpoint(self):
        gs = self.gstack[self.glevel]
        P = gs.currentpoint
        if P:
            return gs.itransform(P)
        return None

    def thereisacurrentpoint(self):
        return self.gstack[self.glevel].currentpoint is not None

    # --- static utilities -----------------------------------------

    def isarray(a):
        return isinstance(a, (list, tuple, np.ndarray))
    isarray = staticmethod(isarray)

# ===================================================================

