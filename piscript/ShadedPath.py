
from piscript.VectorUtils import *
import piscript.VectorUtils as VectorUtils
import math

class ShadedPath:

    # wd = width in points
    # c0, c1 = main, boundary colors
    def __init__(self, ps, wd):
        self.ps = ps
        self.wd = wd
        self.path = []
        self.closed = False

    # coords are rendered immediately into default
    def moveto(self, P, dP = None):
        if dP:
            P = Vector(self.ps.image(P))
            dP = Vector(self.ps.rimage(dP)).normalized()
            self.path.append([P, dP])
        else:
            P = Vector(self.ps.image(P))
            self.path.append([P, None])

    def lineto(self, P, dP = None):
        if dP:
            P = Vector(self.ps.image(P))
            dP = Vector(self.ps.rimage(dP)).normalized()
            self.path.append([P, dP])
        else:
            P = Vector(self.ps.image(P))
            self.path.append([P, None])

    def close(self):
        self.closed = True

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
        # build the separate shfill segments
        # for each, use shfill + clipping
        pi = math.pi
        ps = self.ps
        ps.gsave()
        ps.revert()
        p = self.path
        # set the displacements dP
        if self.closed:
            Q = p[0][0]
            R = p[1][0]
            v = R-Q
            P = p[-1][0]
            u = Q-P
            p[0][1] = self.midvector(u, v)

            Q = p[-1][0]
            R = p[0][0]
            v = R-Q
            P = p[-2][0]
            u = Q-P
            p[-1][1] = self.midvector(u, v)

        else:
            # deal separately with ends
            dQ = p[0][1] # is None or a unit vector
            Q = p[0][0]
            R = p[1][0]
            v = (R-Q).perp().normalized()
            if dQ:
                # scale to wd
                d = dQ*v
                p[0][1] = (self.wd/d)*dQ
            else: # use perp
                p[0][1] = self.wd*v.normalized()
            dQ = p[-1][1] # is None or a unit vector
            P = p[-2][0]
            Q = p[-1][0]
            v = (Q-P).perp().normalized()
            if dQ:
                # scale to wd
                d = dQ*v
                p[-1][1] = (self.wd/d)*dQ
            else: # use perp
                p[-1][1] = self.wd*v

        # then fix interior
        for i in range(1, len(p)-1):
            Q = p[i][0]
            R = p[i+1][0]
            v = R-Q
            P = p[i-1][0]
            u = Q-P
            p[i][1] = self.midvector(u, v)

        if self.closed: n = 0
        else: n = 1
        for i in range(n, len(p)):
            P = p[i-1][0]
            Q = p[i][0]
            dP = p[i-1][1]
            dQ = p[i][1]
            P0 = P + dP
            Q0 = Q + dQ
            u = (Q-P).perp().normalized()
            u *= self.wd
            # u = gradient along which the gradient is set
            ps.gsave()
            ps.newpath()
            ps.moveto(P)
            ps.lineto(P0)
            ps.lineto(Q0)
            ps.lineto(Q)
            ps.closepath()
            ps.clip()
            # assemble data: x0 y0 x1 y1 = Coords + colors
            data = [
                P[0], P[1], P[0]+u[0], P[1]+u[1], 
                C0[0], C0[1], C0[2], 
                C1[0], C1[1], C1[2],
            ]
            # debugging:
            """ ps.newpath()
            ps.moveto(P)
            ps.lineto(P0)
            ps.lineto(Q0)
            ps.lineto(Q)
            ps.closepath()
            ps.stroke(C0) """
            # end debugging
            ps.shstroke(data)
            ps.grestore()
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

    # -------------------------------------------------------------------

    def midvector(self, u, v):
        a = math.pi+u.arg()
        b = v.arg()
        c = a-b
        if c < 0: c += 2*math.pi
        elif c >= 2*math.pi: c -= 2*math.pi
        c /= 2
        V = Vector([math.cos(b+c), math.sin(b+c)])
        w = u.perp().normalized()
        d = V*w
        V = V*(self.wd/d)
        return V

    # --------------------------------------------------------------------
        

