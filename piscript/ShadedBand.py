
from piscript.VectorUtils import *
import piscript.VectorUtils as VectorUtils
import math

import logging
logger = logging.getLogger(__name__)
class ShadedBand:

    def __init__(self, ps):
        self.ps = ps
        self.path = []
        self.closed = False

    # coordinates are rendered immediately to default
    def moveto(self, P, Q):
        P = Vector(self.ps.image(P))
        Q = Vector(self.ps.image(Q))
        self.path.append([P, Q])

    def lineto(self, P, Q):
        P = Vector(self.ps.image(P))
        Q = Vector(self.ps.image(Q))
        self.path.append([P, Q])

    def quadto(self, P1, Q1, P2, Q2):
        pass

    def curveto(self, P1, Q1, P2, Q2, P3, Q3):
        P1 = Vector(self.ps.image(P1))
        Q1 = Vector(self.ps.image(Q1))
        P2 = Vector(self.ps.image(P2))
        Q2 = Vector(self.ps.image(Q2))
        P3 = Vector(self.ps.image(P3))
        Q3 = Vector(self.ps.image(Q3))
        self.path.append([P1, Q1, P2, Q2, P3, Q3])

    def closepath(self, ):
        self.closed = True

    def onethird(P, Q):
        return([2*P[0]/3.0 + Q[0]/3.0, 2*P[1]/3.0 + Q[1]/3.0])
    onethird = staticmethod(onethird)

    def stroke(self, *args):
        if not args:
            C0 = self.ps.currentcolor()
            C1 = [1, 1, 1]
        elif len(args) == 1:
            C0 = list(VectorUtils.parse_color(args[0]))
            C1 = [1, 1, 1]
        else:
            C0 = list(VectorUtils.parse_color(args[0]))
            C1 = list(VectorUtils.parse_color(args[1]))
        logger.debug(f"colors = {C0}, {C1}")
        p = self.path
        ps = self.ps
        ps.gsave()
        ps.revert()
        if self.closed: n = 0
        else: n = 1
        for i in range(n, len(p)):
            P = p[i-1]
            Q = p[i]
            if len(Q) == 2:
                # shfill a quadrilateral
                # assemble data: x0 y0 x1 y1 = Coords + colors
                data = [
                    [[ P[0], C0 ],
                    [ Q[0], C0 ],
                    [ Q[1], C1 ]],
                    [[ Q[1], C1 ],
                    [ P[1], C1 ],
                    [ P[0], C0 ]],
                ]
                ps.shfill(data)
            elif len(Q) == 6:
                # shfill a curvy quadrilateral
                # assemble data: x0 y0 x1 y1 ... = Coords + colors
                data = [
                    P[0], self.onethird(P[0], P[1]), self.onethird(P[1], P[0]), 
                        P[1], Q[1], Q[3], Q[5], 
                            self.onethird(Q[5], Q[4]), self.onethird(Q[4], Q[5]), Q[4], Q[2], Q[0],
                                C0, C1, C1, C0 
                        ] 
                logger.debug(f"data = {data}")
                logger.debug(f"length = {len(data)}")
                ps.shcoons(data)
        ps.grestore()

    def fill(self, *args):
        C1 = list(VectorUtils.parse_color(*args)) if args else self.ps.currentcolor()
        ps = self.ps
        ps.gsave()
        ps.revert()
        p = self.path
        ps.moveto(p[0][0])
        for i in range(1, len(p)):
            ps.lineto(p[i][0])
        ps.fill(C1)
        ps.grestore()




