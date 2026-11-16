"""Fourth act · 山河速 / 2020s high-speed rail valley at dawn.
Original procedural bridge, valley, and 6-car EMU. Forward +Y for the train."""
from __future__ import annotations
import math, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
import blib as B  # noqa: E402

ROOT = B.ROOT

from model_craft import Batch
from rolling_stock import build_train
import rail_valley


# ---------------------------------------------------------------- rail scene
def build_rail():
    B.reset(2021)
    rng = random.Random(2021)
    ALL = []
    matte = B.vmat("RailMatte", .9)
    rock = B.vmat("RailRock", .95)
    steel = B.vmat("RailSteel", .35, .7)
    concrete = B.vmat("RailConcrete", .92)
    snow = B.vmat("RailSnow", .8)
    water = B.mat("Water", "#2f5a60", rough=.1, metal=.2)
    signs = B.mat("RailSigns", texture=os.path.join(B.ASSETS, "signs_atlas.png"), rough=.5)
    lamp = B.mat("RailLamp", "#ffd9a0", emission="#ffd9a0", emis_strength=3)
    red = B.mat("RailRed", "#ff3a2c", emission="#ff3020", emis_strength=4)

    def add(o):
        if isinstance(o, (list, tuple)):
            for x in o: add(x)
        else: ALL.append(o)

    def shore(x):
        return 7*math.sin(x*.026)+3*math.sin(x*.058+.4)

    def ground_h(x, y):
        ay = abs(y-shore(x))
        bank = smoothstep(32, 64, ay) * 13
        ridge = (ridged(x, y) ** 1.25) * 56
        ridge *= smoothstep(55, 145, ay)
        side = smoothstep(92, 160, abs(x)) * 20
        hill=(bank + ridge + side)*smoothstep(29,50,ay)
        # The track cuts through the high ground at both ends of the valley.
        cut=smoothstep(75,105,abs(y))*(1-smoothstep(7.4,19,abs(x)))
        return hill-cut*max(0,hill-30.4)

    def ridged(x, y):
        v, amp, fx, fy = 0.0, 1.0, .017, .014
        for k in range(4):
            s = math.sin(x * fx + math.sin(y * fy * 1.7 + k * .9) * 1.35 + k * 2.3)
            t = math.sin(y * fy + math.sin(x * fx * 1.3 + k * .7) * 1.15 + k * 1.6)
            v += amp * (.5 + .5 * s * t)
            amp *= .55; fx *= 2.05; fy *= 2.05
        return v / 1.95

    def smoothstep(a, b, x):
        t = max(0.0, min(1.0, (x-a)/(b-a)))
        return t*t*(3-2*t)

    def fbm2(x, y):
        v = 0.0
        for k in range(4):
            xx, yy = x*(2**k), y*(2**k)
            v += (math.sin(xx*12.9898 + yy*78.233 + k*3.1) * 43758.5453 % 1.0) / (2**k)
        return max(0.0, min(1.0, v))

    add(B.ground_slab("RailBase",320,300,9,colors=("#4a4032","#5b4c3a","#6b5a45","#3d342a"),cap=False))
    add(rail_valley.terrain(ground_h,B.vmat('Valley earth and grass',.96)))
    # river
    shore_verts = [(x,shore(x)+s*38,.25) for x in range(-160,161,4) for s in (-1,1)]
    add(B._finish("Water_River", shore_verts, [(i,i+2,i+3,i+1) for i in range(0,len(shore_verts)-2,2)],"#537c79",water))
    girders, bed = Batch(), Batch()
    rail_valley.bank_woodland(ground_h,shore)
    # bridge
    Z = 32.0
    add(B.box("BridgeDeck", (13, 273.6, 1.3), (0, 0, Z), color="#7b7970", material=concrete, bevel=.05))
    add(B.box("BridgeBed", (9.5, 273.6, .18), (0, 0, Z + .72), color="#4a4a46", material=matte))
    for sx in (-6.2, 6.2):
        add(B.box("BridgeParapet", (.4, 213.5, 1.05), (sx, 0, Z + 1.0), color="#9a978c", material=concrete, bevel=.03))
        for yy in range(-105, 106, 6):
            add(B.box("BridgePost", (.5, .3, .9), (sx, yy, Z + 1.0), color="#a9a596", material=concrete))
    # rails, sleepers
    for sx in (-2.4, 2.4):
        rail_head_width = .074
        for side in (-1,1):
            offset = side * (1.435 + rail_head_width) / 2
            girders.box((sx+offset,0,Z+.94),(rail_head_width,273.6,.115),"#9da7a5")
        for k in range(370):
            bed.box((sx,-136.55+k*.74,Z+.836),(2.65,.24,.075),"#898c81")
    for side in (-1,1):
        # A single closed, tapered box girder on each side. The bearing sits under its bottom flange.
        edge=side*4.6
        profile=[(-1.68,31.44),(1.68,31.44),(1.16,29.80),(-1.16,29.80)]
        girders.rings([[(edge+x,y,z) for x,z in profile] for y in (-136.7,136.7)],"#899897",False)
        girders.box((side*6.32,0,31.77),(.38,273.45,.45),"#a2aaa1")
    # The stays carry the river span. Only the two approaches need intermediate piers.
    for yy in (-99,99):
        foot=ground_h(0,yy)-.30
        bed.box((0,yy,foot+.68),(7.4,4.6,1.36),"#827f76")
        def octagon(ww,dd,z):
            return [(ww*math.cos(math.tau*j/8),yy+dd*math.sin(math.tau*j/8),z) for j in range(8)]
        bed.rings([octagon(2.4,1.9,foot+.90),octagon(1.88,1.42,27.6),
                   octagon(5.60,1.94,29.13),octagon(5.60,1.94,29.45)],"#97968a",False)
        for xx in (-4.6,4.6): girders.box((xx,yy,29.63),(1.35,1.48,.37),"#526167")
    boat=Batch()
    bx,by=-24.0,-9.4
    sections=[(-6,.12,1.13),(-4.7,1.33,.91),(-2.3,1.67,.83),(2,1.64,.82),(4.5,1.24,.97),(5.8,.12,1.18)]
    for a,b in zip(sections,sections[1:]):
        for side in (-1,1):
            def p(row,frac):
                dx,w,top=row
                return (bx+dx,by+side*w*(.76+.24*frac),.20+top*frac)
            for f,c in ((0,"#416e73"),(.40,"#3d5d64"),(.72,"#986a4d")):
                upper=.40 if f==0 else .72 if f==.4 else 1
                boat.panel([p(a,f),p(b,f),p(b,upper),p(a,upper)],c)
        boat.panel([(bx+a[0],by-a[1],.20+a[2]),(bx+b[0],by-b[1],.20+b[2]),
                    (bx+b[0],by+b[1],.20+b[2]),(bx+a[0],by+a[1],.20+a[2])],"#a08a63")
    boat.box((bx+.5,by,1.54),(4.1,2.37,1.06),"#c3b59b")
    for side in (-1,1):
        for k in range(3): boat.box((bx-.70+k*1.17,by+side*1.2,1.65),(.88,.05,.53),"#48636a")
    boat.box((bx+.45,by,2.15),(4.6,2.73,.13),"#7c5c44")
    boat.rod((bx+2.2,by,2.18),(bx+2.2,by,3.08),.047,"#6c6558")
    add(boat.object("River survey launch",concrete))
    # A pylons
    for py in (-46, 46):
        base_z = ground_h(0, py)
        for sx in (-1, 1):
            add(B.beam("PylonLeg", (sx*11.3,py,base_z),(sx*1.5,py,86),2.3,2.9,"#cccabe",concrete,bevel=.12))
            bed.box((sx*10.8,py,base_z+1.1),(5.2,6.8,2.2),"#989d8e")
        add(B.box("PylonBeam", (10.2,2.55,2.15),(0,py,62),color="#c6c7b9",material=concrete,bevel=.09))
        add(B.box("PylonTop",(4.8,3.0,2.6),(0,py,86),color="#bdc3b8",material=concrete,bevel=.12))
        for direction in (-1,1):
            outer = direction*py>0
            for k in range(1,9):
                ty = py+direction*k*((101-abs(py))/8 if outer else 5.15)
                h=68+k*2.05
                for sx in (-1,1):
                    x=sx*(11.3-9.8*(h-base_z)/(86-base_z))
                    a=(x,py+.8*direction,h)
                    b=(sx*6.05,ty,33.05)
                    girders.rod(b,a,.125,"#d8d4bf",8)
                    girders.rod(b,tuple(b[j]+.043*(a[j]-b[j]) for j in range(3)),.26,"#9c5845",10)
    # Each track has its own cantilever. Thin conductors have a separate material
    # so the renderer can cover fractional pixels without tracing an ink outline.
    wire=Batch()
    for side in (-1,1):
        track=side*2.4
        for k in range(11):
            y=-120+k*24
            girders.rod((side*5.65,y,Z+.67),(side*5.65,y,Z+8.0),.14,"#707c7b",10)
            girders.rod((side*5.65,y,Z+7.84),(track,y,Z+7.72),.10,"#889491",8)
            girders.rod((side*5.65,y,Z+6.38),(track+side*.54,y,Z+7.74),.079,"#83918c",8)
            if k==10: continue
            prev=(track,y,Z+7.75)
            for j in range(1,7):
                u=j/6
                pt=(track,y+24*u,Z+7.75-.40*math.sin(math.pi*u))
                wire.rod(prev,pt,.068,"#747f7d",8)
                if j in (2,4): wire.rod(pt,(track,pt[1],Z+6.98),.041,"#76817d",6)
                prev=pt
        wire.rod((track,-122,Z+6.98),(track,122,Z+6.98),.078,"#687977",10)
    add(wire.object("Contact and messenger wire",B.vmat("Overhead conductors",.90)))
    add(girders.object("Stay anchors and bridge girders", steel))
    add(bed.object("Track sleepers and pylon footings",concrete))
    from scene_lettering import letters
    for y in (-3.8,3.8):
        add(B.box("Bridge sign mounting shoe",(.55,.30,1.46),(-6.40,y,31.53),
                  color="#5f6c68",material=steel))
    add(B.box("Bridge enamel rim",(.18,12.4,2.30),(-6.71,0,31.47),color="#b4aba0",material=steel,bevel=.06))
    add(B.box("Bridge enamel face",(.075,12.06,2.04),(-6.83,0,31.47),material=B.mat("Valley bridge enamel","#284743",rough=.66)))
    add(letters("Bridge name in enamel","山河大桥",(-6.90,0,31.49),10.8,1.63,
                B.mat("Bridge ivory letters","#fff2d2",rough=.58),angle=-math.pi/2,brush=True,relief=.045))
    # village on the north bank
    for i, (vx, vy) in enumerate([(-52, -72), (-38, -80), (-66, -84), (54, -76)]):
        z = ground_h(vx, vy)
        add(B.box("VillageHouse", (6, 5, 3), (vx, vy, z + 1.5), color="#d8cbb0", material=matte, bevel=.05))
        add(B.tile_roof("VillageRoof", vx, vy, z + 3, 7.2, 6.0, 1.2, .12, "#5f5b52", matte, curl=.4))
    add(B.sign_quad("StationSign", "yunling", (-45, -68, ground_h(-45, -68) + 3.2), 0, 6, 1.5, signs))
    # wind turbines
    for (tx, ty) in [(-116, -118), (112, -110), (104, 112)]:
        z = ground_h(tx, ty)
        add(B.cylinder("TurbineTower", 1.0, 30, (tx, ty, z + 15), segments=10, color="#d6d6cc", material=concrete))
        add(B.sphere("TurbineNacelle", 1.2, (tx, ty, z + 30), scale=(2.2, 1, 1.1), color="#e4e3da", material=concrete,
                     segments=8, rings=5))
        for k in range(3):
            a = k * math.tau / 3
            add(B.beam("Blade", (tx, ty, z + 30), (tx + math.cos(a) * 13, ty, z + 30 + math.sin(a) * 13),
                       .45, .16, "#e8e6dc", concrete))
    B.empty("FX_Hotspot", (0, 0, Z + 3))
    B.empty("FX_Smoke_1", (-45, -68, ground_h(-45, -68) + 4))
    add(rail_valley.portals(ground_h,concrete,rock,steel))
    bpy.context.preferences.filepaths.save_version = 0
    B.join_materials("RailScene", ALL)
    bpy.ops.file.pack_all()
    B.save_blend(os.path.join(ROOT, "assets", "zones", "rail.blend"))
    B.export_glb(os.path.join(ROOT, "assets", "zones", "rail.glb"))
    print("RAIL EXPORTED", os.path.getsize(os.path.join(ROOT, "assets", "zones", "rail.glb")))


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if not args or "train" in args:
        build_train()
    if not args or "rail" in args:
        build_rail()
