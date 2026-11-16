"""Small batch mesh builder for fabricated parts. Coordinates are Blender metres."""
import math
from mathutils import Vector
import blib as B


class Batch:
    def __init__(self):
        self.vertices, self.faces, self.colors, self.smooth = [], [], [], []

    def part(self, points, faces, color, smooth=False):
        offset = len(self.vertices)
        self.vertices.extend(points)
        for face in faces:
            self.faces.append(tuple(offset + i for i in face))
            self.colors.append(color)
            self.smooth.append(smooth)

    def panel(self, points, color):
        self.part(points, [range(len(points))], color)

    def rings(self, rings, color, smooth=True, caps=True):
        n = len(rings[0])
        faces = []
        for row in range(len(rings)-1):
            for j in range(n):
                a = row*n+j
                b = row*n+(j+1)%n
                faces.append((a,b,b+n,a+n))
        if caps:
            faces.extend([tuple(reversed(range(n))),tuple(range((len(rings)-1)*n,len(rings)*n))])
        self.part([p for ring in rings for p in ring], faces, color, smooth)

    def rod(self, start, end, radius, color, sides=8, end_radius=None):
        a,b = Vector(start),Vector(end)
        axis = (b-a).normalized()
        across = axis.cross(Vector((0,0,1)) if abs(axis.z)<.9 else Vector((0,1,0))).normalized()
        up = axis.cross(across)
        circle = [across*math.cos(math.tau*j/sides)+up*math.sin(math.tau*j/sides) for j in range(sides)]
        r2 = radius if end_radius is None else end_radius
        self.rings([[tuple(a+v*radius) for v in circle],[tuple(b+v*r2) for v in circle]],color,sides>5)

    def pipe(self, points, radius, color, sides=7):
        for a,b in zip(points,points[1:]):
            self.rod(a,b,radius,color,sides)

    def box(self, center, size, color, angle=0):
        x,y,z = center
        w,d,h = (s/2 for s in size)
        co,si = math.cos(angle),math.sin(angle)
        corners = [(x+dx*co-dy*si,y+dx*si+dy*co) for dx,dy in [(-w,-d),(w,-d),(w,d),(-w,d)]]
        self.rings([[(a,b,z-h) for a,b in corners],[(a,b,z+h) for a,b in corners]],color,False)

    def object(self, name, material):
        obj = B._finish(name,self.vertices,self.faces,None,material,face_colors=self.colors)
        obj.data.polygons.foreach_set('use_smooth',self.smooth)
        return obj
