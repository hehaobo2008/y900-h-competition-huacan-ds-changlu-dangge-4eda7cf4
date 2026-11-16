"""Build an editable, two-wheel hand-pulled freight cart (metres, +Y forward).

The .blend retains individual parts; only the runtime GLB is joined by material.
Original photo references informed the construction, but are not embedded.
"""
from pathlib import Path
import math
import random
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy
import blib as B
from rural_materials import pbr, project_uv
from mathutils import Vector
from model_craft import Batch

ROOT = Path(B.ROOT)
B.reset(1983)
rng = random.Random(1983)
wood = pbr("Cart_Wood", "fine_grained_wood", normal_strength=0.32)
linen = pbr("Cart_Linen", "rough_linen", derived=True, normal_strength=0.3)
iron = B.mat("Cart_Iron", "#48423b", rough=0.72, metal=0.72)
rope = B.mat("Cart_Hemp", "#9f8962", rough=0.95)
glass = B.mat("Cart_Lantern_Glass", "#c5d2c5", rough=0.2, alpha=0.32)
brass = B.mat("Cart_Lantern_Metal", "#72634a", rough=0.6, metal=0.6)
parts = []

def add(obj, textured=False, axis=None, scale=.6):
    if obj is not None:
        if textured:
            project_uv(obj, scale=scale, grain_axis=axis, offset=rng.random() * 2)
        parts.append(obj)
    return obj

def timber(name, size, pos, bevel=.008):
    ob = B.box(name, size, pos, material=wood, bevel=bevel)
    return add(ob, True, max(range(3), key=lambda i: size[i]))

def beam(name, p1, p2, width, height):
    ob = B.beam(name, p1, p2, width, height, material=wood, bevel=.006)
    return add(ob, True, 2)

def tube(name, points, radius, mat=rope):
    return add(B.tube(name, points, radius, "#ffffff", mat))

def metal_cylinder(name, radius, length, pos, rot=(0, 0, 0), mat=iron, segments=24):
    return add(B.cylinder(name, radius, length, pos, rot=rot, segments=segments, material=mat))

def annulus(name, x, radius_inner, radius_outer, half_width, z, material, count=64):
    verts, faces = [], []
    for i in range(count):
        a = math.tau * i / count
        y, zz = math.cos(a), math.sin(a)
        verts.extend([(x-half_width,y*radius_inner,z+zz*radius_inner),
                      (x-half_width,y*radius_outer,z+zz*radius_outer),
                      (x+half_width,y*radius_inner,z+zz*radius_inner),
                      (x+half_width,y*radius_outer,z+zz*radius_outer)])
    for i in range(count):
        a, b = 4*i, 4*((i+1) % count)
        faces.extend([(a,b,b+1,a+1), (a+2,a+3,b+3,b+2),
                      (a+1,b+1,b+3,a+3), (a,a+2,b+2,b)])
    ob = B._finish(name, verts, faces, "#ffffff", material)
    if material == wood:
        # UV the circular grain along the wheel, with a seam at the bottom.
        uv = ob.data.uv_layers.new(name="UVMap")
        for poly in ob.data.polygons:
            for li in poly.loop_indices:
                v = ob.data.vertices[ob.data.loops[li].vertex_index].co
                ang = math.atan2(v.z-z, v.y)
                uv.data[li].uv = (v.x / .6, (ang + math.pi) * radius_outer / .6)
    return add(ob)

# Four load-bearing beams and plank bed; the axle passes below both long beams.
for sx in (-.52, .52):
    timber("Main_longitudinal_beam", (.13, 2.08, .15), (sx, -.03, .72), .012)
for yy in (-.87, -.12, .77):
    timber("Transverse_bed_support", (1.35, .13, .12), (0, yy, .8), .008)
for i in range(7):
    timber("Bed_plank_%02d" % i, (.177, 1.82, .055), (-.54+i*.18, -.05, .89), .004)
for sx in (-.67, .67):
    timber("Side_sill", (.08, 1.94, .10), (sx, -.04, .91), .006)
    for yy in (-.82, .72):
        timber("Side_stanchion", (.075, .075, .38), (sx, yy, 1.08), .006)
    timber("Side_rail", (.068, 1.7, .075), (sx, -.05, 1.23), .006)
    # Shafts are secured to the long beams, not floating above them.
    beam("Pulling_shaft", (sx*.78, .30, .74), (sx*.78, 2.65, .91), .078, .09)
    metal_cylinder("Grip_collar", .052, .07, (sx*.78, 2.38, .89), (math.pi/2, 0, 0))
    beam("Support_leg", (sx*.78, .85, .7), (sx*.78, 1.18, .045), .075, .075)
    metal_cylinder("Shaft_iron_pin", .038, .09, (sx*.78, .69, .80), (0, math.pi/2, 0))
timber("Rear_crossbar", (1.45, .10, .10), (0, -.98, .87), .008)
metal_cylinder("Continuous_steel_axle", .052, 2.17, (0, 0, .65), (0, math.pi/2, 0), segments=32)
for sx in (-.52, .52):
    # Two iron straps visibly clamp the axle to each longitudinal member.
    for yy in (-.10, .10):
        add(B.box("Axle_strap", (.17, .045, .032), (sx, yy, .63), material=iron, bevel=.004))
        metal_cylinder("Axle_strap_bolt", .018, .025, (sx, yy, .66))

# Wood felloes, metal tires, stout spokes and hubs.
for side in (-1, 1):
    x = side * .95
    annulus("Wood_felloe", x, .555, .624, .055, .65, wood)
    annulus("Iron_tire", x, .624, .648, .061, .65, iron)
    hub = B.cylinder("Wood_hub", .125, .27, (x, 0, .65), rot=(0, math.pi/2, 0),
                     segments=24, material=wood, bevel=.008)
    add(hub, True, 2)
    for face in (-1, 1):
        metal_cylinder("Hub_iron_collar", .13, .028, (x+face*.095, 0, .65), (0, math.pi/2, 0))
    metal_cylinder("Axle_end_washer", .085, .022, (x+side*.15, 0, .65), (0, math.pi/2, 0))
    metal_cylinder("Axle_end_pin", .038, .13, (x+side*.18, 0, .65), (0, math.pi/2, 0))
    for j in range(14):
        a = math.tau*j/14
        y0,z0 = .105*math.cos(a), .65+.105*math.sin(a)
        y1,z1 = .575*math.cos(a), .65+.575*math.sin(a)
        beam("Wheel_spoke_%02d" % j, (x,y0,z0), (x,y1,z1), .055, .045)
    for j in range(7):
        a = math.tau*j/7
        metal_cylinder("Felloe_rivet", .014, .018,
                       (x+side*.058,.592*math.cos(a),.65+.592*math.sin(a)),
                       (0, math.pi/2, 0), segments=10)

# Sewn grain sacks laid on their long sides. The cross sections compress at
# the bed, gather into a tied neck, then flare into an uneven open cuff.
def sack(name, center, scale, seed):
    cx,cy,cz=center
    sx,sy,sz=scale
    verts,faces=[],[]
    rows,sides=48,56
    for j in range(rows+1):
        t=j/rows
        if t<.15:
            fullness=.54+.46*math.sin(t/.15*math.pi/2)
        elif t<.72:
            fullness=1-.09*((t-.40)/.32)**2
        elif t<.88:
            u=(t-.72)/.16
            fullness=.90-.74*u*u*(3-2*u)
        else:
            fullness=.16+.30*((t-.88)/.12)**1.3
        for k in range(sides):
            a=math.tau*k/sides
            pleat=(.027+.15*max(0,(t-.64)/.36))*math.cos(11*a+1.6*t+seed)
            pleat+=.03*math.sin(4*a+5*t+seed)*math.cos(math.tau*t)
            co,si=math.cos(a),math.sin(a)
            x=sx*fullness*(1+pleat)*math.copysign(abs(co)**.79,co)
            z=sz*fullness*(1+pleat)*math.copysign(abs(si)**.80,si)
            z=max(-sz*.52,z)-sz*.10*t
            y=(t*2-1)*sy+.018*math.cos(7*a+seed)*(t**6)
            verts.append((cx+x,cy+y,cz+z))
    for j in range(rows):
        for k in range(sides):
            a=j*sides+k; b=j*sides+(k+1)%sides
            faces.append((a,a+sides,b+sides,b))
    faces.append(tuple(range(sides)))
    ob=B._finish(name,verts,faces,"#ffffff",linen,smooth=True)
    uv=ob.data.uv_layers.new(name="UVMap")
    for poly in ob.data.polygons:
        for li in poly.loop_indices:
            idx=ob.data.loops[li].vertex_index
            v=idx%sides
            if v==0 and idx-1 in poly.vertices: v=sides
            uv.data[li].uv=(v/sides*3.1,(idx//sides)/rows*2.0)
    parts.append(ob)
    cord_y=cy+sy*.76
    for turn in range(3):
        points=[(cx+(sx*.166+.004)*math.cos(a*math.tau/36),cord_y+turn*.009,
                 cz-sz*.088+(sz*.17+.007)*math.sin(a*math.tau/36)) for a in range(37)]
        tube("Gathered neck binding",points,.007)
    tube("Hemp tail",[(cx+.08,cord_y,cz),(cx+.11,cord_y+.02,cz-.025),
                       (cx+.14,cord_y+.07,cz-.09)],.006)
    return ob

lower = sack("Rice sack - loaded against bed", (0,-.11,1.045),(.59,.71,.29),1)
upper = sack("Rice sack - pleated mouth",(-.045,-.10,1.32),(.49,.52,.225),2)
bpy.context.view_layer.update()
def sack_top(x, y):
    hits = []
    for ob in (lower, upper):
        inverse = ob.matrix_world.inverted()
        origin = inverse @ Vector((x,y,3))
        direction = inverse.to_3x3() @ Vector((0,0,-1))
        hit, point, _, _ = ob.ray_cast(origin, direction)
        if hit:
            hits.append((ob.matrix_world @ point).z)
    return max(hits) if hits else .96
for yy in (-.39, .18):
    over = [(x, yy, sack_top(x,yy)+.016) for x in (-.62+i*.04 for i in range(32))]
    tube("Cargo_lashing", [(-.71,yy,.79),(-.69,yy,.96),*over,(.69,yy,.96),(.71,yy,.79)], .012)
    tube("Lashing_below_bed", [(-.71,yy,.79),(-.62,yy,.73),(.62,yy,.73),(.71,yy,.79)], .012)
    tube("Lashing_knot", [(.69,yy,1.01),(.75,yy-.055,1.03),(.78,yy,1.07),
         (.71,yy+.05,1.04),(.69,yy,1.01),(.76,yy-.05,.91)], .013)
# A tied sample sheaf rides beside the sacks. Individual awns, glumes and
# bowed culms keep the outline legible from the road camera.
straw=Batch()
for k in range(82):
    offset=rng.gauss(0,.046)
    root=(-.48+offset,-.08+rng.uniform(-.06,.07),1.27+rng.uniform(-.028,.028))
    tie=(-.44+offset*.43,-.55,1.42+rng.uniform(-.026,.026))
    tip=(-.45+offset+rng.uniform(-.15,.15),-1.02-rng.uniform(0,.27),1.56+rng.uniform(-.08,.10))
    col=rng.choice(["#bb964b","#cfaa59","#ad904a","#dab96c"])
    straw.pipe([root,tie,tip],.005,col,4)
    for j in range(6):
        f=(j+1)/6
        g=(tip[0]+offset*f,tip[1]-.12*f,tip[2]-.065*f*f)
        straw.rod((g[0]-.005,g[1]+.015,g[2]+.009),g,.009,col,5,.002)
parts.append(straw.object("Bound sheaf of seed rice",B.vmat("Cart_straw",.84)))
for j in range(4):
    tube("Sheaf binding", [(-.44+.068*math.cos(k*math.tau/30),-.53-j*.009,
                           1.42+.04*math.sin(k*math.tau/30)) for k in range(31)],.007)
# Unlit kerosene lantern hanging from the right rail.
lx, ly, lz = .82, .56, .94
metal_cylinder("Lantern_base", .095, .065, (lx,ly,lz-.13), mat=brass)
metal_cylinder("Lantern_burner", .07, .05, (lx,ly,lz-.075), mat=brass)
globe = B.lathe("Lantern_glass", [(.050,0),(.071,.04),(.075,.12),(.058,.18),(.039,.21)],
                loc=(lx,ly,lz-.06), segments=24, material=glass)
add(globe)
metal_cylinder("Lantern_cap", .08, .04, (lx,ly,lz+.16), mat=brass)
metal_cylinder("Lantern_chimney", .048, .07, (lx,ly,lz+.21), mat=brass)
for sx in (-1,1):
    tube("Lantern_guard", [(lx+sx*.075,ly,lz-.10),(lx+sx*.095,ly,lz+.015),
         (lx+sx*.075,ly,lz+.17)], .008, brass)
tube("Lantern_handle", [(lx-.065,ly,lz+.17),(lx-.085,ly,lz+.29),
     (lx,ly,lz+.35),(lx+.085,ly,lz+.29),(lx+.065,ly,lz+.17)], .008, brass)
tube("Lantern_hook", [(lx,ly,lz+.35),(.73,ly,1.33),(.67,ly,1.23)], .009, brass)

# Keep source parts editable and make their images portable.
root = B.empty("RickshawRoot", (0, 0, 0))
for obj in parts:
    obj.parent = root
bpy.ops.file.pack_all()
source = ROOT / "assets" / "vehicles" / "rickshaw.blend"
output = ROOT / "assets" / "vehicles" / "rickshaw.glb"
B.save_blend(str(source))
# Joining is performed only after saving the editable source.
B.join_materials("Rickshaw", parts, skip_prefixes=())
B.export_glb(str(output))
print("RICKSHAW_REALISM", len(parts), output.stat().st_size)
