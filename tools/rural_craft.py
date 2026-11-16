"""Cut paper foliage, drooping rice ears and bamboo work at the village entrance."""
from pathlib import Path
import math
import random
import bpy
import blib as B
from model_craft import Batch


def cutout(name, filename):
    mat=B.mat(name,texture=str(Path(B.ASSETS)/"textures"/filename),rough=.91)
    nodes=mat.node_tree.nodes
    image=next(n for n in nodes if n.type=="TEX_IMAGE")
    mask=nodes.new("ShaderNodeMath")
    mask.operation="GREATER_THAN"
    mask.inputs[1].default_value=.36
    mat.node_tree.links.new(image.outputs["Alpha"],mask.inputs[0])
    mat.node_tree.links.new(mask.outputs[0],nodes.get("Principled BSDF").inputs["Alpha"])
    return mat


def cards(name, quads, mat):
    verts=[v for quad in quads for v in quad]
    mesh=bpy.data.meshes.new(name)
    mesh.from_pydata(verts,[],[(i,i+1,i+2,i+3) for i in range(0,len(verts),4)])
    mesh.update()
    obj=bpy.data.objects.new(name,mesh)
    bpy.context.scene.collection.objects.link(obj)
    mesh.materials.append(mat)
    uv=mesh.uv_layers.new(name="UVMap")
    uv.data.foreach_set('uv',[0,0,1,0,1,1,0,1]*len(quads))
    return obj


def canopy(center, radii, seed, mat):
    """Orient terminal sprays around each original branch endpoint."""
    rng=random.Random(seed)
    cx,cy,cz=center
    rx,ry,rz=radii
    quads=[]
    for j in range(27):
        a=j*2.39996+rng.uniform(-.20,.20)
        t=rng.uniform(-.76,.95)
        r=math.sqrt(1-t*t)
        x=cx+math.cos(a)*rx*r*.61
        y=cy+math.sin(a)*ry*r*.61
        z=cz+t*rz*.75
        w=rng.uniform(.65,1.08)*min(rx,ry)
        dx,dy=-math.sin(a)*w,math.cos(a)*w
        ox,oy=math.cos(a)*rx*.61,math.sin(a)*ry*.61
        rise=rz*rng.uniform(.64,1.1)
        quads.append([(x-dx*.72,y-dy*.72,z-rise*.65),(x+dx*.72,y+dy*.72,z-rise*.65),
                      (x+dx+ox,y+dy+oy,z+rise*.54),(x-dx+ox,y-dy+oy,z+rise*.54)])
    return cards("Branch tip sprays",quads,mat)


def grain_plot(name,x,y,z,w,d,rot=0,spacing=1,height=.65,**kwargs):
    rng=kwargs.get("rng") or random.Random(14)
    quads=[]
    # Each cutout represents a stand of individually drawn laden stalks.
    # Offset adjacent rows and vary their yaw to break the billboard grid.
    nx,ny=max(1,round(w/.96)),max(1,round(d/.95))
    for j in range(ny):
        for k in range(nx):
            px=x-w/2+(k+.5+(j%2)*.17+rng.uniform(-.14,.14))*w/nx
            py=y-d/2+(j+.5+rng.uniform(-.17,.17))*d/ny
            h=max(.61,height*1.6)*rng.uniform(.82,1.15)
            a=rng.uniform(-.48,.48)+math.pi*.43*(j%3)
            for angle in (a,a+1.52):
                dx,dy=.62*math.cos(angle),.62*math.sin(angle)
                quads.append([(px-dx,py-dy,z),(px+dx,py+dy,z),
                              (px+dx+.11,py+dy,z+h),(px-dx+.11,py-dy,z+h)])
    obj=cards(name+"_laden_panicles",quads,bpy.data.materials["Harvest_panicles"])
    obj.rotation_euler.z=rot
    return obj


def sorting_table(x,y,z):
    wood,canes,grain=Batch(),Batch(),Batch()
    wood.box((x,y,z+.72),(2.55,.97,.12),"#785a3c")
    for s in (-1,1):
        for t in (-1,1):
            wood.rod((x+s*1.11,y+t*.40,z),(x+s*.99,y+t*.33,z+.69),.054,"#765e43",6)
        wood.rod((x-1.02,y+s*.34,z+.26),(x+1.02,y+s*.34,z+.26),.04,"#7c6242",6)
    rng=random.Random(71)
    for cx,r in ((x-.61,.56),(x+.62,.49)):
        for row in range(5):
            rr=r*(.87+.03*row)
            ring=[(cx+rr*math.cos(a*math.tau/64),y+rr*math.sin(a*math.tau/64),z+.79+row*.033) for a in range(65)]
            canes.pipe(ring,.018,"#ac864c" if row%2 else "#c3a36a",5)
        for j in range(-10,11):
            yy=j*r*.080
            xx=math.sqrt((r*.87)**2-yy**2)
            canes.rod((cx-xx,y+yy,z+.79),(cx+xx,y+yy,z+.79),.014,"#bfa16f",4)
            canes.rod((cx+yy,y-xx,z+.797),(cx+yy,y+xx,z+.797),.015,"#ab895b",4)
        if cx<x:
            grain.rings([[(cx+rr*math.cos(j*math.tau/32),y+rr*math.sin(j*math.tau/32),z+zz)
                          for j in range(32)] for rr,zz in [(r*.84,.80),(r*.68,.86),(.02,.90)]],"#c5a15b")
            for j in range(145):
                a=rng.random()*math.tau
                rr=r*.81*math.sqrt(rng.random())
                gx,gy=cx+rr*math.cos(a),y+rr*math.sin(a)
                gz=z+.905-.095*rr/(r*.81)
                grain.rod((gx,gy,gz),(gx+.017,gy+.011,gz+.003),.005,rng.choice(["#d2ae63","#c49c54","#e0bd78"]),4)
    return [wood.object("Mortised sorting trestle",B.vmat("Harvest_timber",.86)),
            canes.object("Split bamboo sieves",B.vmat("Split_bamboo",.72)),
            grain.object("Threshed rice",B.vmat("Grain_husks",.88))]
