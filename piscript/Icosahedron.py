
from piscript.PiScript3d import *

import math

A = math.pi/5
y = math.sqrt(5)/(1 + math.sqrt(5))
d = math.sqrt(2*y)
h = 0.5
g = math.sqrt(d*d - 1) + h

ICV = [
  [0, 0, 1],
  [1/g, 0, h/g ],
  [math.cos(2*A)/g, math.sin(2*A)/g, h/g],
  [math.cos(4*A)/g, math.sin(4*A)/g, h/g],
  [math.cos(6*A)/g, math.sin(6*A)/g, h/g],
  [math.cos(8*A)/g, math.sin(8*A)/g, h/g],
  [math.cos(9*A)/g, math.sin(9*A)/g, -h/g],
  [math.cos(7*A)/g, math.sin(7*A)/g, -h/g],
  [math.cos(5*A)/g, math.sin(5*A)/g, -h/g],
  [math.cos(3*A)/g, math.sin(2*A)/g, -h/g],
  [math.cos(1*A)/g, math.sin(1*A)/g, -h/g],
  [0, 0, -1]
] 

ICI = [
  [ 0, 1, 2 ],
  [ 0, 2, 3 ],
  [ 0, 3, 4 ],
  [ 0, 4, 5 ],
  [ 0, 5, 1 ],
  [ 2, 1, 10 ],
  [ 2, 10, 9 ],
  [ 3, 2, 9 ],
  [ 3, 9, 8 ],
  [ 4, 3, 8 ],
  [ 4, 8, 7 ],
  [ 5, 4, 7 ],
  [ 5, 7, 6 ],
  [ 1, 5, 6 ],
  [ 1, 6, 10 ],
  [ 6, 7, 11 ],
  [ 7, 8, 11 ],
  [ 8, 9, 11 ],
  [ 9, 10, 11 ],
  [ 10, 6, 11 ]
]

class Icosahedron(ConvexSurface):

    def __init__(self, c):
        global ICI, ICV
        p = [[ICV[v[0]], ICV[v[1]], ICV[v[2]]] for v in ICI]
        f = []
        for face in p:
            nf = Face.normalfunction(face)
            if nf[3] > 0:
                f.append(Face(Face.reverse_array(p[i]), c))
            else:
                f.append(Face(p[i], c))
        
        ConvexSurface.__init__(self, f)

        

