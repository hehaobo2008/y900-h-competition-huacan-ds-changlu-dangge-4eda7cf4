"""第三幕 · 城夜雨 / 2010s Chinese metropolis at night.
Original procedural city; no downloaded assets or brands."""
from __future__ import annotations
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
import blib as B  # noqa: E402
from model_craft import Batch

B.reset(2012)
rng = random.Random(2012)
ALL = []
WATER = []

# ---------------------------------------------------------------- materials
matte = B.vmat("CityMatte", 0.9)
concrete = B.vmat("CityConcrete", 0.94)
metal = B.vmat("CityMetal", 0.45, 0.55)
stone = B.vmat("CityStone", 0.92)
glass = B.mat("CityGlass", "#0d1a22", rough=0.16, metal=0.5, double_sided=True)
warm = B.mat("CityWarm", "#ffbe78", rough=0.5, emission="#ffb86a", emis_strength=1.55, double_sided=True)
cool = B.mat("CityCool", "#a9dcff", rough=0.4, emission="#a8d8ff", emis_strength=1.15, double_sided=True)
pale = B.mat("CityPale", "#e8f0e0", rough=0.5, emission="#eaf4e8", emis_strength=0.9, double_sided=True)
dark = B.mat("CityDark", "#0b1219", rough=0.35, metal=0.25, double_sided=True)
lamp = B.mat("CityLamp", "#ffd9a0", rough=0.4, emission="#ffd39a", emis_strength=4.0)
neonPink = B.mat("NeonPink", "#ff4f8b", rough=0.35, emission="#ff4f8b", emis_strength=4.0)
neonCyan = B.mat("NeonCyan", "#53e0e0", rough=0.35, emission="#53e0e0", emis_strength=3.6)
neonWarm = B.mat("NeonWarm", "#ffc46b", rough=0.4, emission="#ffc46b", emis_strength=3.8)
neonRed = B.mat("NeonRed", "#ff5548", rough=0.4, emission="#ff5548", emis_strength=3.6)
red = B.mat("RedLight", "#ff3b30", rough=0.4, emission="#ff2a20", emis_strength=5.0)
head = B.mat("Headlight", "#fff2c8", rough=0.3, emission="#fff0c0", emis_strength=5.0)
tail = B.mat("Taillight", "#ff4030", rough=0.4, emission="#ff3020", emis_strength=3.0)
water = B.mat("Water", "#142a32", rough=0.12, metal=0.3)
signs = B.mat("SignsNeon", texture=os.path.join(B.ASSETS, "signs_atlas.png"), rough=0.45,
              emission="#ffffff", emis_strength=2.4)
signsPlain = B.mat("Signs", texture=os.path.join(B.ASSETS, "signs_atlas.png"), rough=0.7)


def add(objs):
    if objs is None:
        return
    if isinstance(objs, (list, tuple)):
        for o in objs:
            add(o)
    else:
        ALL.append(objs)


def add_water(objs):
    if isinstance(objs, (list, tuple)):
        for o in objs:
            add_water(o)
    else:
        WATER.append(objs)
        ALL.append(objs)


# ---------------------------------------------------------------- batched windows
BATCH = {}


def win_quad(corners, material):
    b = BATCH.setdefault(material.name, [material, [], []])
    verts, faces = b[1], b[2]
    i = len(verts)
    verts.extend(corners)
    faces.append((i, i + 1, i + 2))
    faces.append((i, i + 2, i + 3))


def win_front(x, y, z, w, h, material):
    win_quad([(x - w / 2, y, z), (x + w / 2, y, z), (x + w / 2, y, z + h), (x - w / 2, y, z + h)], material)


def win_back(x, y, z, w, h, material):
    win_quad([(x + w / 2, y, z), (x - w / 2, y, z), (x - w / 2, y, z + h), (x + w / 2, y, z + h)], material)


def win_left(x, y, z, w, h, material):
    win_quad([(x, y + w / 2, z), (x, y - w / 2, z), (x, y - w / 2, z + h), (x, y + w / 2, z + h)], material)


def win_right(x, y, z, w, h, material):
    win_quad([(x, y - w / 2, z), (x, y + w / 2, z), (x, y + w / 2, z + h), (x, y - w / 2, z + h)], material)


def pick_window(r):
    v = r.random()
    if v < .52:
        return dark
    if v < .70:
        return cool
    if v < .78:
        return pale
    return warm


# ---------------------------------------------------------------- towers
SIGN_KEYS = ["baihuo", "zhaoxiang", "lifa", "shudian", "fandian", "gongxiaoshe", "dianying",
             "binggun", "xiubiao", "lushe", "bashi", "yeshi", "chalou", "shufang", "yingyuan",
             "bianli", "guidao", "changluli", "mian", "huoguo", "yaodian"]


def sign_on_side(x, y, z, w, h, side, key, mat=signs):
    if side == "east":
        ob = B.sign_quad("CitySign", key, (x, y, z), math.pi / 2, w, h, mat)
    elif side == "west":
        ob = B.sign_quad("CitySign", key, (x, y, z), -math.pi / 2, w, h, mat)
    elif side == "south":
        ob = B.sign_quad("CitySign", key, (x, y, z), 0, w, h, mat)
    else:
        ob = B.sign_quad("CitySign", key, (x, y, z), math.pi, w, h, mat)
    add(ob)


def tower(x,y,w,d,h,style="glass",seed=1,sign_key=None):
    from city_architecture import building
    add(building(x,y,w,d,h,style,seed))
    # Tenant fascias sit on the arcade, just above its glazing.
    if sign_key and seed in (1,2,4,5,9,10,12,14):
        side = 1 if x<0 else -1
        sign_on_side(x+side*(w/2+1.85),y,6.95,min(8.4,d*.51),1.18,
                     "east" if side>0 else "west", sign_key)

def tower_simple(x,y,w,d,h,seed=1):
    from city_architecture import building
    add(building(x,y,w,d,h,("step","glass","res")[seed%3],seed,far=True))


# ---------------------------------------------------------------- street furniture
def street_lamp(x, y, side=1, h=8.0):
    add(B.cylinder("LampPole", .10, h, (x, y, h / 2), segments=8, color="#2e3034", material=metal))
    add(B.box("LampArm", (2.2, .10, .10), (x + side * 1.1, y, h - .1), color="#2e3034", material=metal))
    add(B.box("LampHead", (.8, .28, .16), (x + side * 2.1, y, h - .2), color="#ffd9a0", material=lamp))
    B.empty("FX_Light", (x + side * 2.1, y, h - .2))


def street_tree(x, y, h=5.5):
    from planted_trees import plant
    add(plant('avenue',x,y,.44,h,h*.58))
    add(B.box("TreePlanter", (2.0, 2.0, .45), (x, y, .22), color="#54514a", material=stone, bevel=.03))


def car(x, y, rot=0, color="#6b2e2e", scale=1.0, z=0.0):
    objs = []
    def skin(name, sections, tint, material):
        verts, faces = [], []
        for px, half_w, lower, upper, crown in sections:
            verts.extend([(px,-half_w*.93,lower),(px,-half_w,upper),(px,-half_w*.74,crown),
                          (px,half_w*.74,crown),(px,half_w,upper),(px,half_w*.93,lower)])
        for k in range(len(sections)-1):
            for j in range(6):
                a=k*6+j; b=k*6+(j+1)%6
                faces.append((a,b,b+6,a+6))
        faces.extend([tuple(reversed(range(6))),tuple(range(len(verts)-6,len(verts)))])
        objs.append(B._finish(name,verts,faces,tint,material,smooth=False))
    skin("Pressed body",[(-2.1,.7,.37,.61,.72),(-1.81,.89,.29,.72,.86),(-.6,.92,.26,.75,.88),
                         (.88,.91,.27,.73,.83),(1.73,.83,.31,.61,.69),(2.12,.69,.37,.53,.57)],color,concrete)
    skin("Glazed cabin",[(-1.42,.75,.77,.81,.83),(-.67,.78,.82,1.18,1.42),
                         (.29,.74,.80,1.23,1.46),(1.04,.76,.78,.84,.87)],"#253d48",glass)
    objs.append(B.box("Painted roof",(.96,1.14,.064),(-.18,0,1.44),color=color,material=concrete,bevel=.03))
    for side in (-1,1):
        objs.append(B.tube("Window pillar",[(-.27,side*.78,.82),(-.31,side*.62,1.39)],.048,color,metal))
        objs.append(B.tube("Belt trim",[(-1.47,side*.83,.79),(.79,side*.82,.80)],.024,"#929c9d",metal))
        objs.append(B.box("Mirror",(.22,.19,.14),(.52,side*.94,1.02),color=color,material=metal,bevel=.04))
    for sx in (-1.3, 1.3):
        for sy in (-.78, .78):
            objs.append(B.cylinder("Wheel", .34, .22, (sx, sy, .34), rot=(math.pi / 2, 0, 0),
                                   segments=12, color="#15171a", material=metal))
    for sy in (-.55, .55):
        objs.append(B.box("Headlight", (.08, .28, .16), (2.12, sy, .62), color="#fff0c0", material=head))
        objs.append(B.box("Taillight", (.08, .26, .14), (-2.12, sy, .62), color="#ff3020", material=tail))
    B.apply_xform(objs, (x, y, z), rot)
    add(objs)


def bus(x, y, rot=0):
    objs = []
    objs.append(B.box("BusBody", (11.0, 2.5, 3.0), (0, 0, 1.7), color="#2f5c6a", material=concrete, bevel=.1))
    objs.append(B.box("BusBand", (10.8, 2.52, 1.0), (0, 0, 2.2), color="#182a33", material=glass))
    objs.append(B.box("BusRoof", (11, 2.45, .12), (0, 0, 3.2), color="#d8d5c8", material=concrete))
    for sy in (-1.27, 1.27):
        for k in range(5):
            objs.append(B.box("BusWindow", (1.3, .03, .8), (-3.6 + k * 1.8, sy, 2.15),
                              color="#ffd9a0", material=warm))
    for sx in (-3.8, 3.8):
        for sy in (-1.0, 1.0):
            objs.append(B.cylinder("BusWheel", .45, .26, (sx, sy, .45), rot=(math.pi / 2, 0, 0),
                                   segments=12, color="#15171a", material=metal))
    B.apply_xform(objs, (x, y, 0.1), rot)
    add(objs)


def subway_entrance(x, y):
    objs = []
    objs.append(B.box("SubwayBase", (6.0, 4.0, .25), (0, 0, .12), color="#4e514f", material=stone))
    for sx in (-1, 1):
        objs.append(B.box("SubwayRail", (.12, 4.0, 1.0), (sx * 2.8, 0, .7), color="#5a6064", material=metal))
    objs.append(B.quad("SubwayGlass", [(-2.7, -1.9, 1.2), (2.7, -1.9, 1.2), (2.7, -1.9, 3.0), (-2.7, -1.9, 3.0)],
                       "#203038", glass))
    for i in range(6):
        objs.append(B.box("Step", (3.2, .6, .18), (0, 1.5 - i * .55, -.1 - i * .16), color="#3d3f41", material=stone))
    objs.append(B.box("SubwayTop", (6.4, 4.4, .18), (0, 0, 3.1), color="#24272b", material=metal))
    B.apply_xform(objs, (x, y, 0.15), 0)
    add(objs)
    sign_on_side(x, y - 2.05, 2.0, 2.4, 1.0, "south", "exit")


def bench(x, y, rot=0):
    objs = []
    objs.append(B.box("BenchSeat", (2.2, .55, .12), (0, 0, .5), color="#5d4a35", material=matte))
    for sx in (-.8, .8):
        objs.append(B.box("BenchLeg", (.12, .5, .5), (sx, 0, .25), color="#3d3a34", material=metal))
    B.apply_xform(objs, (x, y, .1), rot)
    add(objs)


def trash(x, y):
    add(B.cylinder("Trash", .35, .9, (x, y, .55), segments=10, color="#3c4a42", material=metal))


# ---------------------------------------------------------------- viaduct / expressway
def viaduct():
    z = 13.0
    add(B.box("ViaDeck", (320, 9.0, 1.1), (0, 5, z), color="#4a4a46", material=concrete, bevel=.05))
    add(B.box("ViaRoad", (320, 7.2, .12), (0, 5, z + .6), color="#2b2c2e", material=matte))
    for side in (-1, 1):
        add(B.box("ViaParapet", (320, .3, .9), (0, 5 + side * 4.4, z + .95), color="#65645c", material=concrete))
    for px in range(-150, 151, 30):
        add(B.box("ViaPier", (2.2, 3.2, z - .3), (px, 5, (z - .3) / 2), color="#55544e", material=concrete, bevel=.04))
    # rails, sleepers, catenary
    rail_head_width = .074
    for side in (-1,1):
        offset = side * (1.435 + rail_head_width) / 2
        add(B.box("Rail", (320, rail_head_width, .12), (0, 5 + offset, z + .795), color="#8a8a86", material=metal))
    sleepers = Batch()
    for k in range(431):
        sleepers.box((-159.1+k*.74,5,z+.6975),(.24,2.62,.075),"#787670")
    add(sleepers.object("Cross-track concrete sleepers",matte))
    for px in range(-150, 151, 25):
        add(B.cylinder("CatPole", .12, 8.5, (px, 5 + 3.7, z + 4.9), segments=6, color="#4a4c50", material=metal))
        add(B.box("CatArm", (0.1, 3.4, .1), (px, 5 + 2.0, z + 8.9), color="#4a4c50", material=metal))
    for sy in (-2.3, 2.3):
        add(B.tube("CatWire", [(-158, 5 + sy, z + 8.7), (158, 5 + sy, z + 8.7)], .018, "#3e3f42", metal, segments=4))
    # The north platform joins a two-flight stair, on the west pedestrian side.
    deck_top = z+1.18
    add(B.box("StationPlatform",(96,6.4,.50),(-65,10.2,deck_top-.25),color="#858376",material=stone))
    add(B.box("StationRoof",(97,6.6,.25),(-63.5,10.2,z+5.4),color="#485867",material=metal))
    fixtures = Batch()
    for px in range(-110,-13,8):
        fixtures.box((px,10.7,z+3.25),(.30,.30,4.15),"#758789")
        fixtures.box((px,8.35,z+5.21),(1.65,.21,.11),"#ebc79b")
    fixtures.box((-65,7.66,deck_top+.014),(95.5,.31,.028),"#d5ab68")
    steps=40
    landing=.16+(deck_top-.16)/2
    rise=(deck_top-.16)/(steps*2)
    for level,(xx,direction) in enumerate(((-15.9,1),(-13.45,-1))):
        start_y=8.12 if direction==1 else 21.12
        for j in range(steps):
            yy=start_y+direction*(j+.5)*.325
            top=.16+(level*steps+j+1)*rise
            fixtures.box((xx,yy,top-.13),(2.24,.331,.26),"#8d908a")
            fixtures.box((xx,yy-direction*.142,top+.008),(2.15,.037,.016),"#c3b494")
        for sx in (-1,1):
            rail_x=xx+sx*1.09
            for j in range(0,steps+1,5):
                yy=start_y+direction*j*.325
                foot=.16+(level*steps+j)*rise
                fixtures.rod((rail_x,yy,foot-.05),(rail_x,yy,foot+1.02),.036,"#7e9290")
            for dz in (.48,1.02):
                fixtures.rod((rail_x,start_y,.16+level*steps*rise+dz),
                             (rail_x,start_y+direction*13,.16+(level+1)*steps*rise+dz),.045,"#b5bdad")
    fixtures.box((-15.27,7.53,deck_top-.15),(4.6,1.16,.30),"#88928c")
    fixtures.box((-14.67,22.02,landing-.15),(4.72,1.8,.30),"#88928c")
    add(fixtures.object("Platform tactile strip and switchback stairs",metal))


def expressway():
    z = 16.0
    add(B.box("ExpDeck", (320, 12, 1.2), (0, -85, z), color="#474a4d", material=concrete, bevel=.05))
    add(B.box("ExpRoad", (320, 10, .12), (0, -85, z + .68), color="#2c2d2f", material=matte))
    for side in (-1, 1):
        add(B.box("ExpRail", (320, .25, 1.0), (0, -85 + side * 5.8, z + 1.2), color="#6a6c6b", material=metal))
    for px in range(-150, 151, 36):
        add(B.box("ExpPier", (3.0, 4.0, z - .4), (px, -85, (z - .4) / 2), color="#54534e", material=concrete, bevel=.05))
    for px in range(-150, 151, 24):
        add(B.cylinder("ExpLamp", .10, 7, (px, -85 + 5.1, z + 4.2), segments=6, color="#3a3c3f", material=metal))
        add(B.box("ExpLampHead", (1.2, .25, .14), (px, -85 + 4.2, z + 7.7), color="#ffd9a0", material=lamp))
    # cars
    for i in range(7):
        px = -110 + i * 34
        car(px, -85 + (3.5 if i % 2 else -3.5), 0 if i % 2 else math.pi,
            ["#aeb7b6", "#2f3a40", "#6a2e2e", "#d4c6a2"][i % 4], 1.0, z + .75)
    # gantry sign
    add(B.box("Gantry", (26, .5, .5), (20, -85, z + 8), color="#3c3e42", material=metal))
    for px in (-8, 8):
        add(B.cylinder("GantryPole", .18, 8, (20 + px, -85, z + 4), segments=8, color="#3c3e42", material=metal))
    sign_on_side(20, -85 + 6.05, z + 8.2, 12, 3.0, "south", "guidao")


def construction():
    x, y = 92, -42
    # unfinished frame
    for f in range(15):
        z = f * 3.6 + 1.8
        add(B.box("ConcreteSlab", (24, 21, .35), (x, y, z), color="#6c6c66", material=concrete, bevel=.02))
        for sx in (-10, -3, 4, 10):
            for sy in (-8, 0, 8):
                add(B.cylinder("Column", .38, 3.4, (x + sx, y + sy, z + 1.7), segments=8,
                               color="#77756c", material=concrete))
    for f in (5, 6, 7, 10):
        add(B.box("SafetyNet", (24.2, 21.2, 3.4), (x, y, f * 3.6 + 1.8), color="#3f6b53", material=B.mat(
            "Net", "#3f6b53", rough=.95, alpha=.55, double_sided=True)))
    # scaffolding
    for sx in (-12, 12):
        for sy in (-10, 10):
            add(B.beam("Scaffold", (x + sx, y + sy, 0), (x + sx, y + sy, 52), .08, .08, "#7c7a70", metal))
    # crane
    cx, cy = 72, -28
    add(B.box("CraneBase", (5, 5, 1.2), (cx, cy, .6), color="#5a5a54", material=concrete))
    for k in range(22):
        add(B.beam("CraneMast", (cx - .9, cy - .9, k * 3.8), (cx + .9, cy - .9, k * 3.8 + 3.5), .06, .06, "#c8a23a", metal))
        add(B.beam("CraneMast", (cx + .9, cy - .9, k * 3.8), (cx + .9, cy + .9, k * 3.8 + 3.5), .06, .06, "#c8a23a", metal))
        add(B.beam("CraneMast", (cx + .9, cy + .9, k * 3.8), (cx - .9, cy + .9, k * 3.8 + 3.5), .06, .06, "#c8a23a", metal))
        add(B.beam("CraneMast", (cx - .9, cy + .9, k * 3.8), (cx - .9, cy - .9, k * 3.8 + 3.5), .06, .06, "#c8a23a", metal))
    top = 22 * 3.8
    add(B.box("CraneJib", (58, .5, .5), (cx + 26, cy, top + 1), color="#c8a23a", material=metal))
    add(B.box("CraneCounter", (14, .9, 1.0), (cx - 8, cy, top + 1.4), color="#5a5a54", material=concrete))
    for dx in (3, 12, 22, 32, 44):
        add(B.tube("CraneCable", [(cx + dx, cy, top + 1), (cx + dx, cy, top - 10 - dx * .4)], .015, "#3a3a37", metal))
    add(B.box("CraneHook", (1.0, .8, .6), (cx + 44, cy, top - 28), color="#c8a23a", material=metal))
    add(B.box("CraneCab", (3.2, 2.6, 2.4), (cx + 2, cy, top - 1.5), color="#2f3b42", material=glass))
    # site barriers / stacks
    for i in range(8):
        add(B.box("SiteBarrier", (2.4, .25, 1.1), (x - 14 + i * 4, y - 12, .55), color="#c8a23a", material=matte))
    for i in range(3):
        add(B.box("PipeStack", (8, 2.2, .8), (x + 8, y + 12 + i * 1.6, .5 + i * .8), color="#6d6252", material=metal))


def comm_tower():
    x, y = -118, 32
    h = 112
    for i in range(14):
        z0, z1 = i * 8, (i + 1) * 8
        for sx in (-1, 1):
            for sy in (-1, 1):
                add(B.beam("CommLeg", (x + sx * 1.5, y + sy * 1.5, z0), (x + sx * .7, y + sy * .7, z1),
                           .10, .10, "#7b7b72", metal))
        for level in (0, 4):
            zz = z0 + level
            for sy in (-1, 1):
                add(B.beam("CommBrace", (x - 1.3, y + sy * 1.3, zz), (x + 1.3, y + sy * 1.3, zz), .05, .05, "#7b7b72", metal))
            for sx in (-1, 1):
                add(B.beam("CommBrace", (x + sx * 1.3, y - 1.3, zz), (x + sx * 1.3, y + 1.3, zz), .05, .05, "#7b7b72", metal))
    add(B.box("CommPlatform", (5.2, 5.2, .5), (x, y, 72), color="#55554f", material=metal))
    add(B.box("CommRing", (7.0, 7.0, .5), (x, y, 86), color="#6a6a60", material=metal))
    add(B.cylinder("CommMast", .12, 26, (x, y, h + 13), segments=6, color="#7b7b72", material=metal))
    add(B.sphere("CommBeacon", .4, (x, y, h + 26), color="#ff3020", material=red, segments=8, rings=5))
    for side in (-1, 1):
        add(B.lathe("Dish", [(0.0, .0), (.7, .25), (1.2, .7), (1.1, 1.2)], loc=(x + side * 3, y, 72.5),
                    rot=(0, math.pi / 2, 0), segments=10, color="#b9bcb9", material=metal))





def river():
    add_water(B.quad("Water_River", [(-160, 50, .05), (160, 50, .05), (160, 80, .05), (-160, 80, .05)],
                     "#142a32", water))
    for yy in (50, 80):
        for x0 in range(-160, 160, 18):
            if abs(x0 + 9) < 14:
                continue
            add(B.box("Embankment", (18, .8, 1.3), (x0 + 9, yy, .65), color="#6b6a60", material=stone, bevel=.04))
            add(B.box("EmbankCap", (18.4, 1.0, .16), (x0 + 9, yy, 1.35), color="#858276", material=stone))
    # promenade trees and lamps
    for i in range(8):
        px = -140 + i * 36
        street_tree(px, 46.5, 5.2)
        street_tree(px + 14, 83.5, 5.2)
        street_lamp(px, 43.5, 1, 7.5)
    # bridge parapets and piers
    for side in (-1, 1):
        add(B.box("BridgeParapet", (.6, 34, 1.3), (side * 11, 65, .75), color="#77756a", material=stone, bevel=.04))
        add(B.box("BridgeRail", (.16, 34, .12), (side * 11, 65, 1.42), color="#9a9688", material=metal))
        for sy in range(52, 80, 4):
            add(B.box("BridgeBaluster", (.3, .3, .7), (side * 11, sy, 1.05), color="#8f8a7c", material=stone))
    for yy in (56, 74):
        add(B.cylinder("BridgePier", 2.0, 3.8, (0, yy, -1.8), segments=12, color="#5f5e56", material=stone))
    # neon arch over bridge
    add(B.tube("BridgeNeon", [(-11, 61, 4.2), (-5, 65, 7.2), (0, 65, 7.6), (5, 65, 7.2), (11, 61, 4.2)],
               .12, "#ff4f8b", neonPink, segments=6))
    add(B.tube("BridgeNeon2", [(-11, 69, 4.2), (-5, 65, 7.2), (0, 65, 7.6), (5, 65, 7.2), (11, 69, 4.2)],
               .12, "#53e0e0", neonCyan, segments=6))
    # small boat
    add(B.lathe("Boat", [(0.1, 0), (1.4, .3), (1.8, .8), (1.5, 1.0)], loc=(40, 64, .1), segments=12,
                color="#5b4a36", material=matte))
    add(B.box("BoatCabin", (2.4, 1.2, .9), (40, 64, 1.2), color="#d6c8a8", material=matte))
    add(B.box("BoatLight", (.2, .2, .2), (41.2, 64, 1.8), color="#ffd9a0", material=lamp))


# ---------------------------------------------------------------- main
def main():
    add(B.ground_slab("CityBase", 320, 300, 9, cap=False, colors=("#3c3a35", "#4a4740", "#565247", "#403e37")))
    add(B.terrain("CityTerrain", 320, 300, 64, 60, lambda x, y: 0.0,
                  lambda x, y, z: "#383a38" if abs(x) < 14 else ("#3d443c" if y > 90 else "#44443f"),
                  matte))
    # avenue
    wet = B.vmat("Rain darkened asphalt",.28,.13)
    add(B.road_ribbon("Avenue", [(0, y) for y in range(-150, 151, 2)], 18, "#35434b", wet, z=.075, crown=0, segments_width=4))
    for x in (-12.5, 12.5):
        for start, end in [(-150,-85),(-75,-25),(-15,35),(45,150)]:
            add(B.road_ribbon("Sidewalk", [(x,start),(x,end)], 5.5, "#4b4c49", stone, z=.18, crown=0, segments_width=2))
    for x in (-6, 0, 6):
        add(B.road_line("Lane", [(x, y) for y in range(-150, 151, 4)], .12, "#bdb69a", matte, z=.135, dash=3.0))
    # cross streets
    for cy in (-80, -20, 40):
        for start, end in [(-160,-9),(9,160)]:
            add(B.road_ribbon("CrossStreet", [(start,cy),(end,cy)], 10, "#2b2d2f", matte, z=.075, crown=0, segments_width=3))
        for sx in (-13, 13):
            for k in range(9):
                add(B.box("Crosswalk", (.7, 5.5, .03), (sx - 4 + k * 1.0, cy, .143), color="#c6c0a6", material=matte))
    # zebra at y=95
    for k in range(12):
        add(B.box("Zebra", (1.0, 4.0, .03), (-8 + k * 1.45, 95, .143), color="#c6c0a6", material=matte))

    from city_architecture import noodle_corner
    add(noodle_corner())
    river()
    viaduct()
    expressway()
    construction()
    comm_tower()

    # towers
    towers = [
        (-38, -55, 24, 22, 118, "glass", 1, "yeshi"), (-72, -32, 28, 24, 86, "grid", 2, "chalou"),
        (-40, -14, 22, 20, 152, "step", 3, "guidao"), (-96, 8, 30, 28, 66, "res", 4, "shudian"),
        (-38, 24, 22, 22, 108, "glass", 5, "yingyuan"), (-108, -52, 30, 28, 58, "res", 6, "bianli"),
        (-104, 32, 26, 24, 78, "grid", 7, "fandian"), (-66, 34, 22, 20, 92, "step", 8, "changluli"),
        (38, -62, 24, 22, 138, "glass", 9, "mian"), (72, -44, 30, 26, 96, "grid", 10, "huoguo"),
        (40, -18, 24, 22, 168, "step", 11, "changluli"), (84, 4, 28, 24, 78, "res", 12, "yaodian"),
        (38, 28, 24, 22, 122, "glass", 13, "yeshi"), (112, -18, 30, 28, 62, "res", 14, "bianli"),
        (108, 32, 26, 22, 76, "grid", 15, "chalou"), (68, 30, 22, 18, 96, "step", 16, "shufang"),
        (24, 104, 22, 18, 46, "res", 17, "binggun"), (56, 112, 24, 20, 58, "grid", 18, "lushe"),
        (-56, 112, 26, 20, 38, "res", 19, "xiubiao"), (-116, 104, 26, 22, 52, "res", 20, "zhaoxiang"),
        (24, -112, 22, 20, 42, "res", 21, "lifa"), (-34, -116, 26, 22, 56, "grid", 22, "dianying"),
        (120, 78, 24, 22, 44, "res", 23, "baihuo"), (-124, 76, 24, 22, 48, "res", 24, "gongxiaoshe"),
    ]
    for i, t in enumerate(towers):
        x, y, w, d, h, style, seed, key = t
        tower(x, y, w, d, h, style, seed, sign_key=key)
    # distant silhouettes north and south
    for i in range(9):
        tower_simple(-140 + i * 34, -135 + rng.uniform(-6, 6), rng.uniform(12, 20), rng.uniform(12, 20),
                     rng.uniform(35, 75), 30 + i)
        tower_simple(-140 + i * 34, 132 + rng.uniform(-4, 4), rng.uniform(10, 18), rng.uniform(10, 18),
                     rng.uniform(30, 60), 50 + i)

    # street details
    for i in range(11):
        py = -140 + i * 26
        street_tree(-15.8, py, rng.uniform(4.6, 6.4))
        street_tree(15.8, py, rng.uniform(4.6, 6.4))
        street_lamp(-14.5, py + 8, -1, 8.2)
        street_lamp(14.5, py + 20, 1, 8.2)
    subway_entrance(18, -36)
    # bus stop + bus
    add(B.box("BusShelter", (7, 2.4, .18), (16, 96, 3.0), color="#2c3033", material=metal))
    for sx in (12.8, 19.2):
        add(B.cylinder("BusPost", .10, 3.0, (sx, 96, 1.5), segments=6, color="#4a4c50", material=metal))
    add(B.box("BusGlass", (6.6, .1, 1.8), (16, 97.1, 1.7), color="#1c3038", material=glass))
    bench(16, 94.8)
    sign_on_side(16, 97.2, 3.3, 4.0, 1.2, "south", "bashi")
    bus(24, 96, 0)
    # river bridge lamps
    for sx in (-9, 9):
        for yy in (54, 64, 76):
            street_lamp(sx, yy, 0, 5.5)
    # food street under viaduct
    for i,px in enumerate((-39,-28,-16,17,30)):
        add(B.box("Stall rear", (5.9,.18,2.63), (px,12.0,1.32), color="#71513d", material=matte, bevel=.03))
        add(B.box("Stall counter", (5.8,.68,.95), (px,9.6,.48), color="#916647", material=matte, bevel=.03))
        for sx in (-2.84,2.84):
            add(B.cylinder("Canopy post",.065,2.87,(px+sx,9.02,1.44),color="#60726b",material=metal,segments=8))
        for shelf in (.96,1.76):
            add(B.box("Pantry shelf",(5.2,.4,.09),(px,11.65,shelf),color="#b08d65",material=matte))
            for k in range(7):
                add(B.cylinder("Pantry jars",.12,.27,(px-2.02+k*.66,11.48,shelf+.17),
                               color=["#b98760","#dfbe79","#668474"][k%3],material=matte,segments=9))
        add(B.box("StallAwning", (6.8, 3.8, .12), (px, 10.5, 2.9), color="#8f3a2c" if i % 2 else "#35584d", material=matte))
        add(B.box("StallLight", (.6, .3, .16), (px, 8.7, 2.6), color="#ffd9a0", material=lamp))
    # plaza sculpture near river
    add(B.lathe("Sculpture", [(0.0, 0), (.8, 1.2), (1.6, 4.0), (.9, 7.0), (.2, 8.2)], loc=(-34, 88, 0),
                segments=14, color="#8f8a7c", material=stone))
    add(B.tube("SculptureRing", [(-34 + 3*math.cos(a), 88, 4 + 2.5*math.sin(a)) for a in [i*math.tau/24 for i in range(24)]],
               .12, "#ffc46b", neonWarm, segments=5, cyclic=True))
    # cars on avenue
    for i, (cx, cy) in enumerate([(5, 28), (-5, 12), (5, -8), (-5, 44), (5, 70)]):
        car(cx, cy, math.pi/2 if i%2 else -math.pi/2, ["#b8b2a2", "#3a4a52", "#93524d", "#2e3a33"][i % 4])
    # FX
    B.empty("FX_Hotspot", (-78, 5 - 4.2, 15.6))
    B.empty("FX_Smoke_1", (10, 10.5, 3.4))
    B.empty("FX_TrainLight", (0, 5, 14))

    # create batched window meshes
    for name, (material, verts, faces) in BATCH.items():
        if verts:
            ob = B._finish("CityWindows_" + name, verts, faces, "#ffffff", material, smooth=False)
            ALL.append(ob)

    B.join_materials("City", ALL)
    from era_fixtures import install
    install("city")
    bpy.ops.file.pack_all()
    B.save_blend(os.path.join(B.ROOT, "assets", "zones", "city.blend"))
    B.export_glb(os.path.join(B.ROOT, "assets", "zones", "city.glb"))
    print("CITY EXPORTED", os.path.getsize(os.path.join(B.ROOT, "assets", "zones", "city.glb")))


if __name__ == "__main__":
    main()
