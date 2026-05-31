
from piscript.PiModule import *

# from piscript.PiScript3d import Face, ConvexSurface

class Cube(ConvexSurface):
    V = [
        Vector([-1,-1,-1]),
        Vector([-1, 1,-1]),
        Vector([ 1, 1,-1]),
        Vector([ 1,-1,-1]),
        Vector([-1,-1, 1]),
        Vector([-1, 1, 1]),
        Vector([ 1, 1, 1]),
        Vector([ 1,-1, 1]),
    ]
    # color, centre, side
    
    def __init__(self, *args):
        if len(args) == 1:
            color = args[0]
            s = 1
            ctr = (0,0,0)
        else:
            color = args[0]
            s = args[1]
            ctr = args[2]
        V = Cube.V
        v = [ s*x + ctr for x in V ]
        indices = [
            [4,7,6,5],
            [7,3,2,6],
            [3,0,1,2],
            [0,4,5,1],
            [5,6,2,1],
            [7,4,0,3],
        ]
        p = [[v[j] for j in idx] for idx in indices]
        F = [Face(x, color) for x in p]

        ConvexSurface.__init__(self, F)

