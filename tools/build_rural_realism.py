"""Rebuild the first island from its original layout with upgraded near-field parts.

Uses build_rural.py for layout and the untouched other-era assets. This file is
the production entry point for the revised first island.
"""
from pathlib import Path
import math
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy
import build_rural as R
import blib as B
import rural_craft as craft
from mathutils import Vector
from era_fixtures import village_sign
from model_craft import Batch
import random
from rural_materials import pbr, project_uv

ROOT = Path(B.ROOT)
dirt = pbr("Rural_Dirt_PBR", "dirt", normal_strength=.4)
plaster = pbr("Rural_Limewash_PBR", "white_plaster_rough_01", derived=True, normal_strength=.22)
wood = pbr("Rural_Timber_PBR", "fine_grained_wood", normal_strength=.25)
tile = pbr("Rural_Grey_Tile_PBR", "clay_roof_tiles", derived=True, normal_strength=.35)
ground = pbr("Rural_Ground_PBR", "dirt", derived=True, normal_strength=.2, vertex_color=True)
track = pbr("Rural_Compacted_Tracks", "dirt", diffuse_override="Diffuse_track.png", normal_strength=.2, alpha=True)

# Morning windows are reflecting / shaded openings, not luminous light sources.
for material, color in [(R.glass, "#746d59"), (R.paper, "#c9bfa4"), (R.lantern, "#9e4432")]:
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Emission Strength"].default_value = 0
    bsdf.inputs["Base Color"].default_value = (*B.srgb(color), 1)

old_box, old_roof, old_road = B.box, B.tile_roof, B.road_ribbon
old_tufts = B.tufts_mesh
old_terrain = B.terrain
old_tree = B.tree
old_house = R.house
old_join, old_save = B.join_materials, B.save_blend
old_ground_h = R.ground_h
leaf_sprays = craft.cutout("Branch_foliage","leaf_spray.png")
grain_heads = craft.cutout("Harvest_panicles","rice_panicles.png")

def ground_h(x, y):
    # A real depression below the water, blended into the surrounding terrain.
    base = old_ground_h(x,y)
    radius = math.sqrt(((x-48)/25)**2 + ((y-38)/16)**2)
    t = max(0,min(1,(radius-.86)/.28))
    t = t*t*(3-2*t)
    shore=-.28*(1-t)+base*t
    if 2<y<29:
        channel=48+1.6*math.sin((y-17)*.14)
        width=min(1,(y-2)/8)*2.65
        if width>.01:
            blend=max(0,min(1,(abs(x-channel)-width)/1.7))
            shore=min(shore,-.39+(base+.39)*blend*blend*(3-2*blend))
    return shore
R.ground_h = ground_h

def wall_piece(name, size, pos):
    ob = old_box(name, size, pos, material=plaster)
    project_uv(ob, scale=1.0, use_transform=True)
    return ob

def pierced_wall(name, size, loc, shop=False):
    """Build a solid wall with actual door and window apertures."""
    w, d, h = size
    bottom = loc[2] - h/2
    top = bottom + h
    holes = [(-.73,.73,bottom+.03,bottom+2.20)]
    if shop:
        holes += [(x-1.05,x+1.05,1.18,2.52) for x in (-2.3,2.3)]
    else:
        windows = [-w/2+1.55, w/2-1.55] if w >= 7 else [-w/2+1.35]
        holes += [(x-.72,x+.72,1.625,2.775) for x in windows]
        if h > 3.4:
            upz = h/2+1.5
            holes += [(x-.55,x+.55,upz-.45,upz+.45) for x in (-w/3,0,w/3)]
    xs = sorted(set([-w/2,w/2] + [max(-w/2,min(w/2,v)) for hole in holes for v in hole[:2]]))
    zs = sorted(set([bottom,top] + [max(bottom,min(top,v)) for hole in holes for v in hole[2:]]))
    out = []
    for x0,x1 in zip(xs,xs[1:]):
        for z0,z1 in zip(zs,zs[1:]):
            if x1-x0 < .01 or z1-z0 < .01:
                continue
            x,z = (x0+x1)/2,(z0+z1)/2
            if any(a < x < b and c < z < e for a,b,c,e in holes):
                continue
            out.append(wall_piece(name+"_facade", (x1-x0,.28,z1-z0), (x,-d/2+.14,z)))
    out.append(wall_piece(name+"_back", (w,.28,h), (0,d/2-.14,loc[2])))
    for side in (-1,1):
        out.append(wall_piece(name+"_side", (.28,d-.56,h), (side*(w/2-.14),0,loc[2])))
    return out

def box(name, size=(1,1,1), loc=(0,0,0), rot=(0,0,0), color="#ffffff",
        material=None, bevel=0.0, smooth=False, face_colors=None):
    if name in ("HWall", "ShopWall"):
        return pierced_wall(name, size, loc, shop=name == "ShopWall")
    if name == "HStain":
        return None
    if name in ("HDoor", "ShopDoor", "HWin_paper", "HWinUp", "ShopWin"):
        loc = (loc[0], loc[1]+.13, loc[2])
    ob = old_box(name, size, loc, rot, color, material, bevel, smooth, face_colors)
    if name in ("Annex", "YardWall"):
        ob.data.materials.clear()
        ob.data.materials.append(plaster)
        project_uv(ob, scale=1.0)
    elif name in ("HDoor", "ShopDoor", "HLintel", "HDoorFrame", "AnnexDoor"):
        ob.data.materials.clear()
        ob.data.materials.append(wood)
        project_uv(ob, scale=.6, grain_axis=max(range(3), key=lambda i: size[i]))
    return ob
B.box = box

def roof(name, cx, cy, z, width, depth, ridge_h=2.2, eave_h=.2,
         color="#4b4a45", material=None, curl=.55, nx=26, ny=40):
    curl = min(curl, .10)
    obs = old_roof(name, cx, cy, z, width, depth, ridge_h, eave_h,
                   color, material, curl, nx, ny)
    bpy.data.objects.remove(obs[0], do_unlink=True)
    # The tiled shell has real shallow waves and course lips; the timber
    # underside and fascia generated by the original builder remain visible.
    sx = max(8, int(width/.15))
    sy = max(8, int(depth/.10))
    verts, faces = [], []
    for j in range(sy+1):
        y = -depth/2 + depth*j/sy
        for i in range(sx+1):
            x = -width/2 + width*i/sx
            u = min(1, abs(x)/(width/2))
            v = min(1, abs(y)/(depth/2))
            wave = .025 * math.cos(math.tau*y/.18)
            course = .012 * max(0, 1 - (abs(x) % .28)/.045)
            height = z+eave_h+ridge_h*(1-u)**1.35+curl*u**3*v**5+wave+course
            verts.append((cx+x,cy+y,height))
    for j in range(sy):
        for i in range(sx):
            a = j*(sx+1)+i
            faces.append((a,a+1,a+sx+2,a+sx+1))
    ob = B._finish(name+"_tiled_shell", verts, faces, "#ffffff", tile, smooth=True)
    uv = ob.data.uv_layers.new(name="UVMap")
    for poly in ob.data.polygons:
        for li in poly.loop_indices:
            v = ob.data.vertices[ob.data.loops[li].vertex_index].co
            uv.data[li].uv = (v.y/1.0, v.x/1.0)
    obs[0] = ob
    # Fill the two open gables down to the wall plate. The rake boards,
    # purlins and rafter tails follow the tiled surface at both ends.
    framing=Batch()
    if name in ("HRoof","ShopRoof"):
        for end in (-1,1):
            gy=cy+end*(depth/2-.68)
            vs,fs=[],[]
            for j in range(29):
                xx=(width/2-.82)*(2*j/28-1)
                top=z+eave_h+ridge_h*(1-abs(xx)/(width/2))**1.35-.045
                vs.extend([(cx+xx,gy,z-.10),(cx+xx,gy,top)])
                if j: fs.append((2*j-2,2*j,2*j+1,2*j-1))
            gable=B._finish(name+"_lime_gable",vs,fs,"#ffffff",plaster)
            project_uv(gable,scale=1.1)
            obs.append(gable)
            for j in range(0,28,2):
                framing.rod(vs[j*2+1],vs[(j+2)*2+1],.060,"#70573c",7)
            for k in range(-3,4):
                xx=k*(width-.9)/8
                zz=z+eave_h+ridge_h*(1-abs(xx)/(width/2))**1.35-.085
                framing.rod((cx+xx,gy,zz),(cx+xx,cy+end*(depth/2+.05),zz),.073,"#725b42")
    for side in (-1,1):
        for j in range(max(4,int(depth/.30))):
            yy=cy-depth/2+.14+j*.30
            framing.rod((cx+side*(width/2-.72),yy,z+eave_h+.09),
                        (cx+side*(width/2-.04),yy,z+eave_h-.06),.045,"#805f3f",7)
    obs.append(framing.object(name+"_roof_carpentry",R.matte))
    return obs
B.tile_roof = roof

def terrain(*args, **kwargs):
    ob = old_terrain(*args, **kwargs)
    ob.data.materials.clear()
    ob.data.materials.append(ground)
    project_uv(ob, scale=2.0)
    return ob
B.terrain = terrain

def tree(name, base, *args, **kwargs):
    result = old_tree(name, base, *args, **kwargs)
    # The small tree by the shop is replaced by a separately editable
    # textured broadleaf tree; retain RNG consumption for the other objects.
    if name == "Tree" and abs(base[0]+6)<.01 and abs(base[1]+55)<.01:
        for obj in result:
            bpy.data.objects.remove(obj, do_unlink=True)
        return []
    for i,obj in enumerate(result):
        if "_leaf" not in obj.name:
            continue
        bounds=[obj.matrix_world @ Vector(v) for v in obj.bound_box]
        low = [min(p[k] for p in bounds) for k in range(3)]
        high = [max(p[k] for p in bounds) for k in range(3)]
        center = [(a+b)/2 for a,b in zip(low,high)]
        radii = [max(.2,(b-a)/2) for a,b in zip(low,high)]
        result[i]=craft.canopy(center,radii,int(base[0]*81+base[1]*18)+i,leaf_sprays)
        bpy.data.objects.remove(obj,do_unlink=True)
    return result
B.tree = tree

def hillside_pine(x,y,h=4,color="#405b41"):
    z=R.ground_h(x,y)
    limbs=Batch()
    limbs.rod((x,y,z),(x+.11,y,z+h*.97),h*.036,"#645541",7,.026)
    foliage=[]
    for j in range(4):
        a=j*2.40+x*.14+y*.08
        r=h*(.21-.036*j)
        px=x+math.cos(a)*r*.47
        py=y+math.sin(a)*r*.47
        pz=z+h*(.43+.14*j)
        limbs.rod((x,y,pz-h*.14),(px,py,pz),h*.021,"#6a5a46",6,.018)
        foliage.append(craft.canopy((px,py,pz),(r*1.16,r*.94,r*.84),int(x*71+y*37)+j,leaf_sprays))
    R.add([limbs.object("Ridge pine branches",R.matte),*foliage])
R.conifer=hillside_pine

old_sphere=B.sphere
def sphere(name,radius=1.0,loc=(0,0,0),scale=(1,1,1),**kwargs):
    if name in ("BanyanLeaf","Shrub"):
        return craft.canopy(loc,[radius*s for s in scale],int(loc[0]*108+loc[2]*33),leaf_sprays)
    return old_sphere(name,radius,loc,scale,**kwargs)
B.sphere=sphere

def house(x, y, rot, w, d, h, style="white", two=False, yard=False):
    old_house(x,y,rot,w,d,h,style,two,yard)
    # The front courtyard house is the first close-view architectural sample.
    if abs(x+24)>.01 or abs(y-2)>.01:
        return
    obs = []
    def timber(name, size, pos):
        ob = old_box(name,size,pos,material=wood,bevel=.006)
        project_uv(ob,scale=.6,grain_axis=max(range(3),key=lambda i:size[i]),use_transform=True)
        obs.append(ob)
    def stone(name,size,pos):
        obs.append(old_box(name,size,pos,color="#8e897b",material=R.stone,bevel=.012))
    def metal(name,radius,depth,pos,rotation=(math.pi/2,0,0)):
        obs.append(B.cylinder(name,radius,depth,pos,rot=rotation,segments=12,
                              color="#55514a",material=R.metal))
    # Recessed, individually jointed vertical door boards and transverse rails.
    for i in range(6):
        timber("Sample_door_board",(.228,.045,2.10),(-.575+i*.23,-d/2+.055,1.625))
    for z in (.83,1.75,2.48):
        timber("Sample_door_batten",(1.35,.035,.075),(0,-d/2+.018,z))
        for xbolt in (-.56,.56):
            metal("Sample_door_batten_pin",.018,.018,(xbolt,-d/2-.007,z))
    for sx in (-1,1):
        # Hinges attach the two door leaves to their jambs.
        for z in (.82,2.30):
            obs.append(old_box("Sample_hinge_strap",(.28,.035,.055),
                               (sx*.58,-d/2-.018,z),color="#5d574b",material=R.metal,bevel=.004))
            metal("Sample_hinge_pin",.025,.13,(sx*.72,-d/2-.022,z),(0,0,0))
        metal("Sample_door_handle_boss",.052,.022,(sx*.17,-d/2-.015,1.58))
        pts=[]
        for i in range(25):
            a=math.tau*i/24
            pts.append((sx*.17+.065*math.cos(a),-d/2-.045,1.50+.065*math.sin(a)))
        obs.append(B.tube("Sample_door_pull",pts,.012,"#655c4e",R.metal,cyclic=True))
    timber("Sample_door_threshold",(1.55,.20,.10),(0,-d/2+.02,.57))
    if two:
        upper_z=h/2+1.5
        for wx in (-w/3,0,w/3):
            for side in (-1,1):
                timber("Sample_upper_window_jamb",(.075,.12,.98),
                       (wx+side*.56,-d/2-.025,upper_z))
                timber("Sample_upper_window_rail",(1.18,.12,.075),
                       (wx,-d/2-.025,upper_z+side*.48))
            for dx in (-.19,.19):
                timber("Sample_upper_window_bar",(.035,.065,.84),
                       (wx+dx,-d/2-.06,upper_z))
            timber("Sample_upper_window_crossbar",(1.06,.065,.035),
                   (wx,-d/2-.06,upper_z))
    # Three courses bridge the 0.55 m plinth, each resting on the one below.
    for yy,top in [(-d/2-.20,.50),(-d/2-.55,.34),(-d/2-.90,.18)]:
        stone("Sample_entry_step",(2.05,.38,top),(0,yy,top/2))
    # Uneven-width foundation stones under the two front courtyard wall runs.
    for side in (-1,1):
        x0=side*(w/4+1.3)
        for j in range(5):
            px=x0-1.2+j*.60
            stone("Sample_courtyard_foundation",(.58,.32,.26),(px,-5,.13))
        timber("Sample_yard_gate_post",(.15,.20,1.35),(side*(w/4+1.3-1.5),-5, .675))
    # Drainage / pedestrian strip connects the threshold and courtyard opening.
    for j in range(7):
        yy=-d/2-.8-j*.32
        if yy < -5.2: break
        stone("Sample_courtyard_paver",(1.05,.28,.055),(0,yy,.035))
    B.apply_xform(obs,(x,y,R.ground_h(x,y)),rot)
    R.add(obs)
R.house = house

def road(name, pts, width, color="#5b554c", material=None, z=.02, crown=.04, segments_width=3):
    if name != "Road":
        # The shoulder and ruts are part of the sculpted road mesh below.
        return None
    verts, faces = [], []
    step_count = 20
    length_steps = 387
    for i in range(length_steps+1):
        y = -145 + 290*i/length_steps
        x0 = R.road_x(y)
        slope = (R.road_x(y+.1)-R.road_x(y-.1))/.2
        inv = 1/math.sqrt(1+slope*slope)
        half = 2.65 + .16*math.sin(y*.043) + .08*math.sin(y*.12)
        for k in range(step_count+1):
            lateral = (2*k/step_count-1)*half
            x, yy = x0+lateral*inv, y-lateral*slope*inv
            edge = abs(lateral)/half
            rut = sum(math.exp(-((lateral-s*.95)/.23)**2) for s in (-1,1))
            high = R.ground_h(x,yy) + .035 + .065*(1-edge*edge) - .040*rut
            high += .008*math.sin(y*.22+lateral)
            verts.append((x,yy,high))
    for i in range(length_steps):
        for k in range(step_count):
            a = i*(step_count+1)+k
            faces.append((a,a+1,a+step_count+2,a+step_count+1))
    ob = B._finish("Road_sculpted_tracks", verts, faces, "#ffffff", dirt, smooth=True)
    uv = ob.data.uv_layers.new(name="UVMap")
    for poly in ob.data.polygons:
        for li in poly.loop_indices:
            v = ob.data.vertices[ob.data.loops[li].vertex_index].co
            uv.data[li].uv = (v.x/2, v.y/2)
    overlays = []
    verge=Batch()
    rng=random.Random(108)
    for i in range(5000):
        y=rng.uniform(-144,144)
        side=rng.choice((-1,1))
        half=2.65+.16*math.sin(y*.043)+.08*math.sin(y*.12)
        x=R.road_x(y)+side*(half+rng.uniform(-.34,1.06))
        zz=R.ground_h(x,y)+.048
        if rng.random()<.24:
            rr=rng.uniform(.025,.115)
            verge.rod((x,y,zz-.02),(x+.01,y,zz+rr*.42),rr,rng.choice(["#8e805e","#9d8f70","#877656"]),5,rr*.53)
        else:
            for k in range(4):
                dx,dy=rng.uniform(-.12,.12),rng.uniform(-.12,.12)
                h=rng.uniform(.09,.30)
                verge.panel([(x-.015,y,zz),(x+.015,y+.012,zz),
                             (x+dx,y+dy,zz+h)],rng.choice(["#868555","#84865c","#a69d66","#737d4c"]))
    overlays.append(verge.object("Irregular earth and stubble at road edge",R.rough))
    for side in (-1,1):
        vs, fs = [], []
        for i in range(length_steps+1):
            y = -145+290*i/length_steps
            x0 = R.road_x(y)
            slope = (R.road_x(y+.1)-R.road_x(y-.1))/.2
            inv = 1/math.sqrt(1+slope*slope)
            half = 2.65 + .16*math.sin(y*.043) + .08*math.sin(y*.12)
            for edge_sign in (-1,1):
                lateral = side*.95 + edge_sign*(.27+.025*math.sin(y*.14+side))
                x, yy = x0+lateral*inv, y-lateral*slope*inv
                edge = abs(lateral)/half
                rut = sum(math.exp(-((lateral-s*.95)/.23)**2) for s in (-1,1))
                high = R.ground_h(x,yy)+.035+.065*(1-edge*edge)-.040*rut
                high += .008*math.sin(y*.22+lateral)+.006
                vs.append((x,yy,high))
        for i in range(length_steps):
            a = i*2
            fs.append((a,a+1,a+3,a+2))
        layer = B._finish("Wheel_track_overlay", vs, fs, "#ffffff", track, smooth=True)
        uv = layer.data.uv_layers.new(name="UVMap")
        for poly in layer.data.polygons:
            for li in poly.loop_indices:
                index = layer.data.loops[li].vertex_index
                uv.data[li].uv = (index%2, (-145+290*(index//2)/length_steps)/2)
        overlays.append(layer)
    return [ob, *overlays]
B.road_ribbon = road

B.rice_field = craft.grain_plot

def crop_bands(x,y,w,d,rot,colors,height,rows):
    obj=craft.grain_plot("Harvest rows",0,0,.055,w,d,height=.57,rng=R.rng)
    B.apply_xform([obj],(x,y,R.ground_h(x,y)),rot)
    R.add(obj)
R.crop_bands=crop_bands

old_shop=R.village_shop
def shop(x,y,rot):
    old_shop(x,y,rot)
    R.add(craft.sorting_table(-3.0,-46.1,R.ground_h(-3,-46.1)))
    R.add(village_sign())
    for fx,fy,w,d,a in [(12,-61,11,19,.09),(22,-65,7,16,.10),(-13,-72,11,14,-.12),(16,-11,13,18,.05)]:
        crop_bands(fx,fy,w,d,a,(),.65,0)
R.village_shop=shop

def tufts(name, pts, height=.5, color="#6e864b", material=None, rng=None):
    if name != "RoadGrass":
        return old_tufts(name, pts, height, color, material, rng)
    rng = rng or R.rng
    verts, faces, colors = [], [], []
    for px,py,pz in pts:
        for cluster in range(3):
            x, y = px+rng.uniform(-.55,.55), py+rng.uniform(-.55,.55)
            z = R.ground_h(x,y)+.025
            for blade in range(6):
                a = rng.uniform(0, math.tau)
                h = rng.uniform(.12,.43)
                w = rng.uniform(.009,.022)
                bend = rng.uniform(.03,.13)
                dx,dy = math.cos(a),math.sin(a)
                sx,sy = -dy*w,dx*w
                n = len(verts)
                verts.extend([(x-sx,y-sy,z),(x+sx,y+sy,z),
                              (x+dx*bend*.4+sx*.5,y+dy*bend*.4+sy*.5,z+h*.6),
                              (x+dx*bend*.4-sx*.5,y+dy*bend*.4-sy*.5,z+h*.6),
                              (x+dx*bend,y+dy*bend,z+h)])
                faces.extend([(n,n+1,n+2,n+3),(n+3,n+2,n+4)])
                col = B.srgb(rng.choice(["#6d804d","#84905b","#788851","#9a9b68"]))
                colors.extend([col,col])
    return B._finish("Road_verge_grass", verts, faces, None, material, face_colors=colors)
B.tufts_mesh = tufts

def pond():
    cx,cy,rx,ry = 48,38,25,16
    R.add_water(B.ellipse_plane("Water_Pond",cx,cy,.07,rx,ry,64,"#385f59",R.water))
    verts,faces = [],[]
    n = 80
    for i in range(n+1):
        a = math.tau*i/n
        wobble = 1+.018*math.sin(a*7)+.012*math.sin(a*13)
        for ring in (1.0,1.13):
            x = cx+rx*ring*wobble*math.cos(a)
            y = cy+ry*ring*wobble*math.sin(a)
            z = .074 if ring == 1.0 else ground_h(x,y)+.02
            verts.append((x,y,z))
    for i in range(n):
        k=i*2
        faces.append((k,k+1,k+3,k+2))
    bank = B._finish("Pond_natural_bank",verts,faces,"#ffffff",dirt,smooth=True)
    project_uv(bank,scale=2)
    R.add(bank)
    irrigation=[]
    for j in range(30):
        yy=3+j*.70
        x=48+1.6*math.sin((yy-17)*.14)
        width=min(1,(yy-2)/8)*2.87
        irrigation.extend([(x-width,yy,.066),(x+width,yy,.066)])
    channel=B._finish("Water_Field_Inlet",irrigation,[(i,i+1,i+3,i+2) for i in range(0,len(irrigation)-2,2)],"#38776d",R.water)
    R.add_water(channel)
    # A small double-ended punt with individual plank courses, breast hook and seats.
    punt=Batch()
    x,y=39.0,26.4
    stations=[(-2.45,.075,.42),(-1.75,.61,.36),(-.65,.86,.31),(.65,.85,.32),(1.73,.58,.37),(2.45,.06,.46)]
    for side in (-1,1):
        for a,b in zip(stations,stations[1:]):
            for j,c in enumerate(("#574535","#7e6044","#996e45")):
                def point(row,f):
                    dx,w,gunwale=row
                    return (x+dx,y+side*w*(.61+.39*f),.03+(gunwale-.03)*f)
                punt.panel([point(a,j/3),point(b,j/3),point(b,(j+1)/3),point(a,(j+1)/3)],c)
            punt.rod(point(a,1),point(b,1),.043,"#ac8254")
    for a,b in zip(stations,stations[1:]):
        punt.panel([(x+a[0],y-a[1]*.65,.116),(x+b[0],y-b[1]*.65,.116),(x+b[0],y+b[1]*.65,.116),(x+a[0],y+a[1]*.65,.116)],"#61523d")
    for dx,ww in ((-1.20,1.28),(.32,1.58),(1.41,1.12)): punt.box((x+dx,y,.29),(.26,ww,.10),"#a98453")
    punt.rod((x-1.80,y-.35,.30),(x+1.84,y+.35,.54),.041,"#aa8756")
    for j in range(7):
        punt.box((x-2.4,22.8+j*.30,.24),(1.4,.28,.12),("#91734f","#a28157","#7d664b")[j%3])
    for dx in (-.55,.55):
        for yy in (22.7,24.6): punt.rod((x-2.4+dx,yy,-.36),(x-2.4+dx,yy,.46),.074,"#77644a")
    punt.pipe([(x-2.38,y,.41),(x-2.57,y-.8,.21),(x-2.96,24.6,.42)],.027,"#97845c",6)
    R.add(punt.object("Moored rice-field punt and landing",R.matte))
    # Reeds cluster on the sheltered shore; open water remains visible.
    rng = R.rng
    for i in range(85):
        a = rng.uniform(.05,math.pi*1.9)
        if math.cos(a) < -.35 and rng.random() < .75:
            continue
        rr = rng.uniform(1.00,1.10)
        x,y = cx+rx*rr*math.cos(a),cy+ry*rr*math.sin(a)
        z = max(.07,ground_h(x,y))+.01
        h = rng.uniform(.35,1.15)
        for j in range(3):
            dx,dy = rng.uniform(-.05,.05),rng.uniform(-.05,.05)
            R.add(B.beam("Pond_reed",(x,y,z),(x+dx,y+dy,z+h),.015,.015,"#7d8655",R.rough))
R.pond = pond

def join_and_save(prefix, objs, skip_prefixes=("Water", "FX_")):
    if prefix == "Rural":
        # Save before material batching, keeping the source parts editable.
        bpy.ops.file.pack_all()
        old_save(str(ROOT / "assets" / "zones" / "rural.blend"))
    return old_join(prefix, objs, skip_prefixes)

def skip_second_save(path):
    print("Editable source already saved before runtime batching:", path)

B.join_materials = join_and_save
B.save_blend = skip_second_save
R.main()
