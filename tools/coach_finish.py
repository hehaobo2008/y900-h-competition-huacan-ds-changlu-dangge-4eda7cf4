"""Paint and glazing for the supplied CRH consist, in its native Blender frame."""
import math
import bpy
import numpy as np
import blib as B
from model_craft import Batch


def restore_bonnet(heads):
    head=next(o for o in heads if len(o.data.polygons)>10000)
    mesh=head.data
    old=next(m for m in mesh.materials if m.name.startswith("CRH baked"))
    pearl=next(i for i,m in enumerate(mesh.materials) if "silver_white" in m.name)
    paint=next(n.image for n in old.node_tree.nodes if n.type=="TEX_IMAGE" and n.image.colorspace_settings.name=="sRGB")
    w,h=paint.size[:]
    pixels=np.empty(w*h*4,dtype=np.float32)
    paint.pixels.foreach_get(pixels)
    pixels=pixels.reshape(h,w,4)
    uv=mesh.uv_layers.active.data
    regions={}
    candidates=[]
    for p in mesh.polygons:
        x,y,z=p.center
        if p.material_index==pearl or y<20.4 or z<1.32 or z>2.60 or p.normal.z<-.35:continue
        u,v=uv[p.loop_start].uv
        rgb=pixels[min(h-1,int(v*h))%h,min(w-1,int(u*w))%w,:3]
        tile=(math.floor(x/.19),math.floor(y/.19),math.floor(z/.19))
        regions.setdefault(tile,[]).append(float(rgb.mean()))
        if max(rgb)<.14:candidates.append((p,tile))
    fixed=0
    for p,(x,y,z) in candidates:
        samples=[v for a,b,c in [(0,0,0),(-1,0,0),(1,0,0),(0,-1,0),(0,1,0)] for v in regions.get((x+a,y+b,z+c),[])]
        if len(samples)>=8 and np.quantile(samples,.30)>.44:
            p.material_index=pearl
            fixed+=1
    print("CRH isolated dark bonnet triangles recoated:",fixed)
    # The supplied markings are flat quads inside the curved upper body. Conform the
    # original artwork to the actual outer skin, including its lower edge.
    from mathutils.bvhtree import BVHTree
    tree=BVHTree.FromObject(head,bpy.context.evaluated_depsgraph_get())
    for mark in heads:
        if not any("wordmark" in m.name for m in mark.data.materials):continue
        original=mark.data
        points=[v.co.copy() for v in original.vertices]
        side=1 if points[0].x>0 else -1
        y0,y1=min(v.y for v in points),max(v.y for v in points)
        z0,z1=min(v.z for v in points),max(v.z for v in points)
        corners={}
        for loop in original.loops:
            p=points[loop.vertex_index]
            corners[(round((p.y-y0)/(y1-y0)),round((p.z-z0)/(z1-z0)))]=np.array(original.uv_layers.active.data[loop.index].uv)
        verts,faces,uvs=[],[],[]
        nx,nz=24,8
        for j in range(nz+1):
            v=j/nz
            for i in range(nx+1):
                u=i/nx;y=y0+(y1-y0)*u;z=z0+(z1-z0)*v
                hit,normal,_,_=tree.ray_cast((side*3,y,z),(-side,0,0),3.)
                verts.append((hit.x+side*.017 if hit else points[0].x+side*.06,y,z))
                uvs.append((1-v)*((1-u)*corners[(0,0)]+u*corners[(1,0)])+v*((1-u)*corners[(0,1)]+u*corners[(1,1)]))
                if i<nx and j<nz:
                    n=j*(nx+1)+i
                    face=[n,n+1,n+nx+2,n+nx+1]
                    faces.append(face if side>0 else list(reversed(face)))
        overlay=bpy.data.meshes.new("Cab lettering follows shell")
        overlay.from_pydata(verts,[],faces);overlay.materials.append(original.materials[0])
        layer=overlay.uv_layers.new(name="UVMap")
        for loop in overlay.loops:layer.data[loop.index].uv=uvs[loop.vertex_index]
        overlay.update();mark.data=overlay
        if not original.users:
            bpy.data.meshes.remove(original)


def finish_coach(cars):
    car=next(o for o in cars if any("aluminium_atlas" in m.name for m in o.data.materials))
    mesh=car.data
    shell=B.mat("CRH pearl enamel","#e3e6e5",rough=.38,metal=.21)
    mesh.materials.append(shell)
    for p in mesh.polygons:
        name=mesh.materials[p.material_index].name
        if ("aluminium_atlas" in name or "dark_tinted_glazing" in name) and abs(p.normal.x)>.62:
            p.material_index=len(mesh.materials)-1
    paint,frame,glass=Batch(),Batch(),Batch()
    start,end=.45,21.51
    def window(batch,side,cy,z,w,h,r,x,color):
        shape=[]
        for ay,az,angle in ((w/2-r,h/2-r,0),(-w/2+r,h/2-r,90),(-w/2+r,-h/2+r,180),(w/2-r,-h/2+r,270)):
            for j in range(5):
                a=math.radians(angle+22.5*j)
                shape.append((side*x,cy+ay+r*math.cos(a),z+az+r*math.sin(a)))
        batch.panel(shape if side>0 else list(reversed(shape)),color)
    for side in (-1,1):
        # Native coach skin is 1.690 m at the waist, tapering to 1.63 at the skirt.
        for z1,z2,x1,x2,tone in [(1.99,2.15,1.696,1.696,"#315987"),(1.37,1.424,1.680,1.696,"#bcab80")]:
            pts=[(side*x1,start,z1),(side*x1,end,z1),(side*x2,end,z2),(side*x2,start,z2)]
            paint.panel(pts if side>0 else list(reversed(pts)),tone)
        for k in range(10):
            cy=3.20+k*1.73
            window(frame,side,cy,2.865,1.45,.90,.13,1.697,"#38454c")
            window(glass,side,cy,2.865,1.36,.80,.12,1.704,"#374b56" if k%4 else "#425865")
        for cy in (1.50,20.48):
            for dy in (-.53,.53):
                frame.box((side*1.695,cy+dy,2.46),(.018,.023,1.95),"#75818a")
            frame.box((side*1.694,cy,3.43),(.018,1.08,.034),"#74838c")
            window(frame,side,cy,2.88,.52,.84,.13,1.70,"#46535a")
            window(glass,side,cy,2.88,.44,.74,.10,1.707,"#354c59")
            frame.box((side*1.70,cy+.38,2.49),(.028,.052,.18),"#687983")
    cars.extend([paint.object("Coach waist and skirt paint",B.vmat("CRH durable livery",.44,.12)),
                 frame.object("Flush doors and window seals",B.vmat("CRH coach frames",.54,.16)),
                 glass.object("Individual tinted saloon windows",B.vmat("CRH coach windows",.25,.26))])

