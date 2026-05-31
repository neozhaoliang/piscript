
from piscript.PiScript3d import *

import math
from piscript.Icosahedron import *
from piscript.Bezier import interpolate

"""
    Start with the icosahedron, subdivide its triangle faces into
    sub-faces and project onto the unit sphere, n times.  Add normal
    vectors to the vertices.  Apply shfill.
"""

class Sphere(SmoothConvexSurface):
    global ICV, ICI
    def __init__(self, color, n):
        self.color = color
        self.shading = PiScript3d.default_shading
        icv = []
        vc = len(ICV)
        for i in range(vc):
            icv.append(ICV[i])
        # icv = a list of actual 3D vertices
        # vc = current vertex count
        # T = list of triangles [a, b, c] where a etc = indices into ivc
        vdict = {}
        # t = list of vertex triples making up current triangles
        T = ICI
        newt = []
        for i in range(n):
            # scan through current triangle list and subdivide
            for t in T:
                # print "i = " + str(i)
                if t[0] < t[1]:
                    A = t[0]; B = t[1]
                else:
                    A = t[1]; B = t[0]
                k = Sphere.key(A, B)
                if k in vdict:
                    ia = vdict[k]
                    a = icv[ia]
                else:
                    a = interpolate(icv[A], icv[B], 0.5)
                    a = Sphere.project(a)
                    ia = vc
                    icv.append(a)
                    vc += 1
                    vdict[k] = ia

                if t[1] < t[2]:
                    A = t[1]; B = t[2]
                else:
                    A = t[2]; B = t[1]
                k = Sphere.key(A, B)
                if k in vdict:
                    ib = vdict[k]
                    b = icv[ib]
                else:
                    b = interpolate(icv[A], icv[B], 0.5)
                    b = Sphere.project(b)
                    ib = vc
                    icv.append(b)
                    vc += 1
                    vdict[k] = ib

                if t[2] < t[0]:
                    A = t[2]; B = t[0]
                else:
                    A = t[0]; B = t[2]
                k = Sphere.key(A, B)
                if k in vdict:
                    ic = vdict[k]
                    c = icv[ic]
                else:
                    c = interpolate(icv[A], icv[B], 0.5)
                    c = Sphere.project(c)
                    ic = vc
                    icv.append(c)
                    vc += 1
                    vdict[k] = ic
                """
                    0   c  2
                      a   b
                        1
                """
                # print "vertex count = " + str(vc)
                newt.append([t[0], ia, ic])
                newt.append([t[1], ib, ia])
                newt.append([t[2], ic, ib])
                newt.append([ia, ib, ic])
            T = newt
        # now the triangles and vertices are constructed in T, and icv
        # make faces out of the elements of T
        f = []
        for t in T:
            p = [ icv[t[0]], icv[t[1]], icv[t[2]] ]
            f.append(Face(p, color))     # an array of three vertex indices
        self.f = f

    def project(p):
        r = math.sqrt(p[0]*p[0]+p[1]*p[1]+p[2]*p[2])
        q = [ p[0]/r, p[1]/r, p[2]/r ]
        return(q)
    project = staticmethod(project)

    def key(i, j):
        return(str(i) + ":" + str(j))
    key = staticmethod(key)
                
