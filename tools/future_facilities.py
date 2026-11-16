"""Occupied facades, quay furniture and an operating nursery on the existing starport route."""
import json
import math
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
import blib as B
from model_craft import Batch

GRID=json.loads((Path(B.ROOT)/"src/future_ground.json").read_text())


def floor_at(x,y):
    u=max(0,min(79.99,(x+160)/4)); v=max(0,min(73.99,(-y+148)/4))
    i,j=int(u),int(v);u-=i;v-=j
    return (1-v)*((1-u)*GRID[j][i]+u*GRID[j][i+1])+v*((1-u)*GRID[j+1][i]+u*GRID[j+1][i+1])


def nursery(shell,metal,plants,glass,lamps):
    x,y=127,48; floor=floor_at(x,y)+.25; eave=floor+3.28
    def z(x1,y1,height):return (x1,y1,floor+height)
    shell.box((x,y,floor-.19),(8.7,13.7,.38),"#aab6a2")
    for hand in (-1,1):
        for sy in (-6.2,0,6.2):
            xx,yy=x+hand*3.69,y+sy; low=min(floor_at(xx,yy)-.24,floor-.39)
            shell.box((xx,yy,(low+floor)/2),(.58,.68,floor-low),"#87988d")
    for yy in (41.5,43.68,45.84,48,50.16,52.32,54.5):
        for side in (-1,1):
            metal.rod((x+side*4,yy,floor),(x+side*4,yy,eave),.087,"#668c88",8)
        points=[(x+4*math.cos(i*math.pi/16),yy,eave+2.54*math.sin(i*math.pi/16)) for i in range(17)]
        metal.pipe(points,.083,"#91b5ab",7)
    for side in (-1,1):
        xx=x+side*4
        shell.box((xx,y,floor+.30),(.20,13,.6),"#758f81")
        # A gutter and drain conduct rain from the roof into the storage cistern.
        metal.rod((xx,41.37,eave+.06),(xx,54.66,eave+.06),.13,"#789298",8)
        metal.pipe([(xx,54.56,eave),(xx+.25*side,54.68,eave-.34),(xx+.25*side,54.68,floor+.22)],.089,"#849b93")
        for k in range(6):
            low=41.52+k*13/6;high=low+13/6-.05
            glass.panel([(xx,low,floor+.63),(xx,high,floor+.63),(xx,high,eave-.06),(xx,low,eave-.06)],"#b7dcd2")
    for k in range(6):
        y0=41.55+k*13/6;y1=y0+13/6-.08
        for i in range(12):
            a,b=i*math.pi/12,(i+1)*math.pi/12
            def point(angle,yy,lift=0):return (x+4*math.cos(angle),yy,eave+2.54*math.sin(angle)+lift)
            open_vent=k%2==1 and i==5
            quad=[point(a,y0),point(a,y1),point(b,y1,.37 if open_vent else 0),point(b,y0,.37 if open_vent else 0)]
            glass.panel(quad,"#a9d2c7")
            if open_vent:
                metal.pipe(quad+[quad[0]],.044,"#8ea89d",6)
                metal.rod(point(b,y0),quad[3],.035,"#626f68",6)
    for yy in (41.5,54.5):
        for k in range(8):
            a=x-4+k;b=a+1
            peak=lambda xx:eave+2.54*math.sqrt(max(0,1-((xx-x)/4)**2))
            lower=floor+2.56 if yy<y and 3<=k<=4 else floor+.26
            glass.panel([(a,yy,lower),(b,yy,lower),(b,yy,peak(b)),(a,yy,peak(a))],"#b6dad0")
            metal.rod((a,yy,lower),(a,yy,peak(a)),.052,"#88a89e",6)
    for xx in (x-1,x+1):
        metal.rod((xx,41.46,floor),(xx,41.46,floor+2.56),.087,"#a89c79",7)
    metal.rod((x-1,41.46,floor+2.56),(x+1,41.46,floor+2.56),.087,"#a89c79",7)
    for side in (-1,1):
        bx=x+side*2.08
        for yy in (44.8,51.2):
            metal.rod(z(bx,yy,3.81),z(bx,yy,4.96),.035,"#73887e",6)
        shell.box(z(bx,48,3.78),(.42,6.8,.17),"#a89970")
        lamps.box(z(bx,48,3.65),(.32,6.58,.09),"#ffdc96")
        for yy in (43.2,48,52.8):
            for dx in (-.58,.58):metal.rod(z(bx+dx,yy,0),z(bx+dx,yy,.83),.068,"#768e85",6)
        shell.box(z(bx,48,.86),(1.72,10.6,.16),"#957759")
        metal.pipe([z(bx+.81,42.6,.96),z(bx+.81,52.9,.96),z(bx+.81,53.1,.34)],.069,"#636f63",7)
        for j in range(8):
            yy=43.57+j*1.25
            shell.box(z(bx,yy,1.01),(1.48,1.09,.17),"#626b53")
            for k in range(6):
                xx=bx+((k%3)-1)*.43;cy=yy+((k//3)-.5)*.50
                for leaf in range(4):
                    a=leaf*math.pi/2+j*.68+k;dx,dy=math.cos(a),math.sin(a)
                    plants.panel([z(xx,cy,1.10),z(xx+.13*dx-.09*dy,cy+.13*dy+.09*dx,1.23),
                                  z(xx+.27*dx,cy+.27*dy,1.40+.06*(j%3)),z(xx+.13*dx+.09*dy,cy+.13*dy-.09*dx,1.21)],
                                 ["#67916a","#86a464","#84ab81","#abc57e"][leaf])
    # Low terracotta potting pots sit beside the water manifold at the far end.
    for j in range(6):
        px=x-2.6+j*.69
        metal.rod(z(px,53.87,.12),z(px,53.87,.70),.21,"#a26e50",12,.29)
        metal.rod(z(px,53.87,.66),z(px,53.87,.77),.31,"#b27853",12)
    # Access steps and the two outdoor water cisterns.
    for k in range(3):
        shell.box((x,41.23-.37*k,floor-.11-.11*k),(2.5,.43,.23),"#9dada1")
    for yy in (46,49):
        floor2=floor_at(132.65,yy)
        metal.rod((132.65,yy,floor2),(132.65,yy,floor2+2.19),.74,"#a1b2a6",16)
        for h in (.28,1.69,2.12):
            metal.rod((132.65,yy,floor2+h),(132.65,yy,floor2+h+.075),.78,"#698b87",16)
    metal.pipe([(131,54.55,eave-.2),(132.65,54.55,eave-.2),(132.65,49,floor_at(132.65,49)+2.25)],.11,"#658781")


def quay(shell,metal):
    # Extend the existing waterfront pavilion toward the existing ferry berth.
    x,y=58,-43.5
    for j in range(18):
        yy=y-3.13-.37*j
        shell.box((x,yy,2.07),(3.35,.34,.20),"#a18d6f")
    for side in (-1,1):
        xx=x+1.54*side
        for yy in (-46.64,-49.6,-52.64):
            metal.rod((xx,yy,-.24),(xx,yy,3.15),.12,"#718781",8)
        metal.pipe([(xx,-46.64,3.1),(xx,-49.6,3.1),(xx,-52.64,3.1)],.07,"#aab4a6")
    for xx in (57.2,58.8):
        metal.rod((xx,-52.64,2.18),(xx,-52.64,2.67),.15,"#626f69",10)


def install():
    for o in list(bpy.context.scene.objects):
        if o.name.startswith("PortFit_"):bpy.data.objects.remove(o,do_unlink=True)
    shell,metal,plants,glass,lamps=Batch(),Batch(),Batch(),Batch(),Batch()
    nursery(shell,metal,plants,glass,lamps);quay(shell,metal)
    shell.object("PortFit_Ceramic and timber",B.vmat("Port architectural ceramic",.79))
    metal.object("PortFit_Shades, services and deck rails",B.vmat("Port maintenance metal",.53,.23))
    plants.object("PortFit_Planting and nursery seedlings",B.vmat("Port greenhouse crops",.88))
    glass.object("PortFit_Nursery glazing",B.mat("Port nursery glazing clear","#91bcae",rough=.29,alpha=.14))
    lamps.object("PortFit_Propagation lights",B.mat("Nursery propagation light","#f5d399",emission="#ffdc96",emis_strength=.85))


if __name__=="__main__":
    from pathlib import Path
    scene_file=Path(bpy.data.filepath)
    if scene_file.stem!="future":raise ValueError(scene_file)
    install();bpy.context.preferences.filepaths.save_version=0
    B.save_blend(str(scene_file));B.export_glb(str(scene_file.with_suffix(".glb")))
