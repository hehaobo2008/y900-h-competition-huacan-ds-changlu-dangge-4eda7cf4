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

B.reset(2012)
rng = random.Random(2012)
ALL = []
WATER = []

# ---------------------------------------------------------------- materials
matte = B.vmat("CityMatte", 0.9)
concrete = B.vmat("CityConcrete", 0.94)
metal = B.vmat("CityMetal", 0.45, 0.55)
stone = B.vmat("CityStone", 0.92)
tree_m = B.vmat("CityTree", 0.95)
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
    if v < .10:
        return dark
    if v < .34:
        return cool
    if v < .47:
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


def tower(x, y, w, d, h, style="glass", seed=1, name="Tower", sign_key=None, billboard=None):
    r = random.Random(seed)
    podium_h = 7.5 if style != "res" else 5.5
    # podium
    add(B.box("Podium", (w + 4, d + 4, podium_h), (x, y, podium_h / 2), color="#4a4c4e",
              material=concrete, bevel=.06))
    add(B.box("PodiumCap", (w + 4.4, d + 4.4, .25), (x, y, podium_h + .1), color="#2c2e31", material=metal))
    # storefront glass on the avenue side
    side = "east" if x < 0 else "west"
    sx = x + (1 if x < 0 else -1) * ((w + 4) / 2 + .04)
    for i in range(max(2, int(d / 4.2))):
        yy = y - d / 2 + (i + .5) * d / max(2, int(d / 4.2))
        mat = [warm, cool, pale][r.randrange(3)]
        if side == "east":
            win_right(sx, yy, 1.5, d / max(2, int(d / 4.2)) * .62, 2.2, mat)
        else:
            win_left(sx, yy, 1.5, d / max(2, int(d / 4.2)) * .62, 2.2, mat)
    # awning
    ax = x + (1 if x < 0 else -1) * ((w + 4) / 2 + 1.2)
    add(B.box("Awning", (2.4, d * .82, .12), (ax, y, 4.1), color="#3a2728" if r.random() < .5 else "#243a3a",
              material=matte, bevel=.02))
    if sign_key:
        sign_on_side(x + (1 if x < 0 else -1) * ((w + 4) / 2 + .08), y, podium_h + 1.2, min(9, d * .65), 2.1, side, sign_key)
        add(B.box("SignFrame", (.16, min(9, d * .65) + .4, 2.5),
                  (x + (1 if x < 0 else -1) * ((w + 4) / 2 + .05), y, podium_h + 1.15),
                  color="#17181a", material=metal))
    # shaft sections
    sections = [(w, d, podium_h, h)]
    if style == "step" and h > 100:
        sections = [(w, d, podium_h, h * .62), (w * .8, d * .8, h * .62, h * .84), (w * .62, d * .62, h * .84, h)]
    for si, (sw, sd, z0, z1) in enumerate(sections):
        add(B.box("Shaft", (sw, sd, z1 - z0), (x, y, (z0 + z1) / 2),
                  color="#3d4045" if style != "res" else "#57524a", material=concrete, bevel=.05))
        n_floors = max(1, int((z1 - z0) / 3.4))
        n_bays = max(3, int(sd / 1.75))
        n_bays_x = max(3, int(sw / 1.75))
        # floor bands
        for f in range(1, n_floors):
            z = z0 + f * 3.4
            add(B.box("FloorBand", (sw + .24, sd + .24, .14), (x, y, z),
                      color="#2a2c30", material=metal))
        # vertical mullions on glass towers
        if style in ("glass", "step"):
            for side_i, axis in enumerate(("yn", "yp", "xn", "xp")):
                for k in range(1, n_bays + 1):
                    if axis in ("yn", "yp"):
                        xx = x - sd / 2 + k * sd / (n_bays + 1)
                        yy = y - sd / 2 - .05 if axis == "yn" else y + sd / 2 + .05
                        add(B.box("Mullion", (.08, .08, z1 - z0), (xx, yy, (z0 + z1) / 2),
                                  color="#5a6068", material=metal))
                    else:
                        yy = y - sw / 2 + k * sw / (n_bays_x + 1)
                        xx = x - sw / 2 - .05 if axis == "xn" else x + sw / 2 + .05
                        add(B.box("Mullion", (.08, .08, z1 - z0), (xx, yy, (z0 + z1) / 2),
                                  color="#5a6068", material=metal))
        # windows
        for f in range(1, n_floors):
            z = z0 + f * 3.4 + .8
            # front / back
            for side_kind in ("front", "back"):
                yy = y - sd / 2 - .06 if side_kind == "front" else y + sd / 2 + .06
                for k in range(n_bays_x):
                    ww = sw - 1.0
                    cx = x - ww / 2 + (k + .5) * ww / n_bays_x
                    if r.random() < .13:
                        continue
                    mat = pick_window(r)
                    if side_kind == "front":
                        win_front(cx, yy, z, min(1.8, ww / n_bays * .72), 1.75, mat)
                    else:
                        win_back(cx, yy, z, min(1.8, ww / n_bays * .72), 1.75, mat)
            # left / right
            for side_kind in ("left", "right"):
                xx = x - sw / 2 - .06 if side_kind == "left" else x + sw / 2 + .06
                for k in range(n_bays):
                    ww = sd - 1.0
                    cy = y - ww / 2 + (k + .5) * ww / n_bays
                    if r.random() < .13:
                        continue
                    mat = pick_window(r)
                    if side_kind == "left":
                        win_left(xx, cy, z, min(1.8, ww / n_bays_x * .72), 1.75, mat)
                    else:
                        win_right(xx, cy, z, min(1.8, ww / n_bays_x * .72), 1.75, mat)
        # balconies / AC on residential and grid towers
        if style in ("res", "grid"):
            for f in range(2, n_floors, 2):
                z = z0 + f * 3.4 + .3
                yy = y - sd / 2 - .55
                add(B.box("Balcony", (min(6.0, sw * .55), 1.1, .16), (x, yy, z),
                          color="#6a645b", material=concrete, bevel=.02))
                for k in range(6):
                    add(B.box("Rail", (.06, .06, .6), (x - min(6.0, sw * .55) / 2 + .3 + k * min(6.0, sw * .55) / 6, yy - .5, z + .3),
                              color="#3b3b39", material=metal))
                if r.random() < .35:
                    add(B.quad("Laundry", [(x - 1.2, yy - .56, z + .2), (x + .2, yy - .56, z + .2),
                                           (x + .2, yy - .56, z + 1.0), (x - 1.2, yy - .56, z + 1.0)],
                               r.choice(["#a94a3c", "#d9c7a0", "#4f6e78", "#c2a75f"]), matte))
        # AC units
        for k in range(max(2, int(h / 30))):
            cx = x + r.uniform(-sw / 2 + 1, sw / 2 - 1)
            z = z0 + r.uniform(2, max(3, z1 - z0 - 2))
            add(B.box("AC", (.9, .45, .55), (cx, y - sd / 2 - .3, z), color="#7a7a72", material=metal))
    # crown
    top_h = h
    add(B.box("Crown", (w + .5, d + .5, .6), (x, y, top_h + .1), color="#26282c", material=metal))
    if style in ("glass", "step"):
        for side_i in range(2):
            add(B.box("CrownNeon", (w * .9, .12, .16), (x, y - d / 2 - .06, top_h - 2 + side_i * 1.1),
                      color="#7fe8e0", material=neonCyan))
    # roof equipment
    add(B.box("Mech", (w * .42, d * .42, 3.0), (x, y + d * .05, top_h + 1.5), color="#34373b", material=concrete))
    add(B.cylinder("Tank", 1.4, 2.6, (x - w * .25, y + d * .2, top_h + 1.3), segments=10,
                   color="#6a6d70", material=metal))
    add(B.cylinder("Antenna", .10, r.uniform(4, 12), (x + w * .22, y - d * .15, top_h + 4),
                   segments=6, color="#6a6d70", material=metal))
    add(B.sphere("Beacon", .28, (x + w * .22, y - d * .15, top_h + 8.2), color="#ff3020", material=red, segments=8, rings=5))
    # billboard
    if billboard:
        bw, bh = 16, 6.5
        add(B.box("BBFrame", (bw + .8, .4, bh + .8), (x, y - d / 2 - .9, top_h + 8), color="#1a1c1f", material=metal))
        sign_on_side(x, y - d / 2 - 1.12, top_h + 8, bw, bh, "south", billboard)
        for k in range(3):
            add(B.box("BBPost", (.2, .2, 6), (x - bw * .35 + k * bw * .35, y - d / 2 - .9, top_h + 3),
                      color="#2a2c2f", material=metal))
        for k in range(4):
            add(B.box("BBLight", (.18, .18, .18), (x - bw * .4 + k * bw * .27, y - d / 2 - 1.3, top_h + 8 + bh / 2 + .5),
                      color="#ffd9a0", material=lamp))
    return


def tower_simple(x, y, w, d, h, seed=1, color="#3f4247"):
    """Cheap distant tower with a few lit windows."""
    r = random.Random(seed)
    add(B.box("DistantTower", (w, d, h), (x, y, h / 2), color=color, material=concrete, bevel=.03))
    for f in range(3, int(h / 4), 3):
        for k in range(3):
            if r.random() < .5:
                win_quad([(x - w * .3 + k * w * .2, y - d / 2 - .05, f),
                          (x - w * .22 + k * w * .2, y - d / 2 - .05, f),
                          (x - w * .22 + k * w * .2, y - d / 2 - .05, f + 1.2),
                          (x - w * .3 + k * w * .2, y - d / 2 - .05, f + 1.2)],
                         r.choice([warm, cool, pale]))


# ---------------------------------------------------------------- street furniture
def street_lamp(x, y, side=1, h=8.0):
    add(B.cylinder("LampPole", .10, h, (x, y, h / 2), segments=8, color="#2e3034", material=metal))
    add(B.box("LampArm", (2.2, .10, .10), (x + side * 1.1, y, h - .1), color="#2e3034", material=metal))
    add(B.box("LampHead", (.8, .28, .16), (x + side * 2.1, y, h - .2), color="#ffd9a0", material=lamp))
    B.empty("FX_Light", (x + side * 2.1, y, h - .2))


def street_tree(x, y, h=5.5):
    add(B.tree("CityTree", (x, y, .15), h, h * .48, "#2e4a39", "#4b3d2e", tree_m, matte, rng))
    add(B.box("TreePlanter", (2.0, 2.0, .45), (x, y, .22), color="#54514a", material=stone, bevel=.03))


def car(x, y, rot=0, color="#6b2e2e", scale=1.0, z=0.0):
    objs = []
    objs.append(B.box("CarBody", (4.2, 1.8, .62), (0, 0, .55), color=color, material=concrete, bevel=.12))
    objs.append(B.box("CarCabin", (2.3, 1.55, .62), (0, -.1, 1.05), color="#17262c", material=glass, bevel=.1))
    objs.append(B.box("CarRoof", (2.0, 1.5, .1), (0, -.1, 1.38), color=color, material=concrete, bevel=.02))
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
    for sy in (-2.3, 2.3):
        add(B.box("Rail", (320, .12, .12), (0, 5 + sy, z + .72), color="#8a8a86", material=metal))
        for k in range(-156, 157, 10):
            add(B.box("Sleeper", (1.2, .35, .08), (k, 5 + sy, z + .66), color="#6a665c", material=matte))
    for px in range(-150, 151, 25):
        add(B.cylinder("CatPole", .12, 8.5, (px, 5 + 3.7, z + 4.9), segments=6, color="#4a4c50", material=metal))
        add(B.box("CatArm", (0.1, 3.4, .1), (px, 5 + 2.0, z + 8.9), color="#4a4c50", material=metal))
    for sy in (-2.3, 2.3):
        add(B.tube("CatWire", [(-158, 5 + sy, z + 8.7), (158, 5 + sy, z + 8.7)], .018, "#3e3f42", metal, segments=4))
    # station
    add(B.box("StationPlatform", (70, 8.0, .5), (-78, 5, z + .2), color="#6d6a60", material=stone))
    add(B.box("StationRoof", (74, 9.0, .25), (-78, 5, z + 5.4), color="#2c3033", material=metal))
    for px in range(-112, -43, 8):
        add(B.box("StationCol", (.35, .35, 4.9), (px, 5, z + 2.9), color="#5d5d56", material=metal))
        add(B.box("StationLight", (1.0, .25, .12), (px, 5, z + 5.1), color="#ffd9a0", material=lamp))
    sign_on_side(-78, 5 - 4.2, z + 4.4, 8, 2.2, "south", "platform")
    # stairs from street
    for i in range(8):
        add(B.box("StationStep", (4.0, 1.0, .35), (-30, 5 - 5.8 + i * .9, z - i * .55), color="#55544e", material=stone))


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
        car(px, -85 + (3.5 if i % 2 else -3.5), math.pi / 2 if i % 2 else -math.pi / 2,
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



def street_neon_row():
    keys = ["yeshi", "chalou", "shufang", "yingyuan", "bianli", "changluli", "mian", "huoguo", "yaodian", "neon_ye"]
    for i, xx in enumerate((-34, -74, -108, 34, 74, 108)):
        side = "east" if xx < 0 else "west"
        key = keys[i % len(keys)]
        sx = xx + (1 if xx < 0 else -1) * 16
        sign_on_side(sx, -88 + i * 27, 5.6, 8.5, 2.2, side, key)
        add(B.box("NeonBar", (.12, .12, 7.2), (sx + (1 if xx < 0 else -1) * .1, -92 + i * 27, 5.2),
                  color="#ff4f8b" if i % 2 else "#53e0e0", material=neonPink if i % 2 else neonCyan))
    # overhead gantry
    for px in (-10, 10):
        add(B.cylinder("GantryPole", .18, 10, (px, 18, 5), segments=8, color="#3c3e42", material=metal))
    add(B.box("GantryBeam", (22, .4, .5), (0, 18, 10), color="#3c3e42", material=metal))
    sign_on_side(0, 18.3, 8.6, 13, 3.2, "south", "changluli")
    # giant led screen
    add(B.box("LEDFrame", (22, .5, 12), (-24, -30, 18), color="#17181a", material=metal))
    sign_on_side(-24, -29.7, 18, 20, 10, "south", "yeshi")
    # reflection strips
    for i, (px, py) in enumerate([(-9, -4), (9, -30), (-9, -56), (9, 12), (-9, 58), (9, 76)]):
        add(B.box("Reflect", (1.6, 12, .02), (px, py, .12),
                  color="#ff4f8b" if i % 2 else "#53e0e0", material=neonPink if i % 2 else neonCyan))

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
    add(B.ground_slab("CityBase", 320, 300, 9, colors=("#3c3a35", "#4a4740", "#565247", "#403e37")))
    add(B.terrain("CityTerrain", 320, 300, 64, 60, lambda x, y: 0.0,
                  lambda x, y, z: "#383a38" if abs(x) < 14 else ("#3d443c" if y > 90 else "#44443f"),
                  matte))
    # avenue
    add(B.road_ribbon("Avenue", [(0, y) for y in range(-150, 151, 2)], 18, "#2b2d2f", matte, z=.06, crown=.02, segments_width=4))
    for x in (-12.5, 12.5):
        add(B.road_ribbon("Sidewalk", [(x, y) for y in range(-150, 151, 2)], 5.5, "#4b4c49", stone, z=.16, crown=0, segments_width=2))
    for x in (-6, 0, 6):
        add(B.road_line("Lane", [(x, y) for y in range(-150, 151, 4)], .12, "#bdb69a", matte, z=.09, dash=3.0))
    # cross streets
    for cy in (-80, -20, 40):
        add(B.road_ribbon("CrossStreet", [(x, cy) for x in range(-160, 161, 2)], 10, "#2b2d2f", matte, z=.055, crown=.02, segments_width=3))
        for sx in (-13, 13):
            for k in range(9):
                add(B.box("Crosswalk", (.7, 5.5, .03), (sx - 4 + k * 1.0, cy, .10), color="#c6c0a6", material=matte))
    # zebra at y=95
    for k in range(12):
        add(B.box("Zebra", (1.0, 4.0, .03), (-8 + k * 1.45, 95, .10), color="#c6c0a6", material=matte))

    street_neon_row()
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
        billboard = key if h > 100 else None
        tower(x, y, w, d, h, style, seed, sign_key=key, billboard=billboard)
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
    for i in range(5):
        px = -30 + i * 13
        add(B.box("Stall", (6, 3.2, 2.6), (px, 10.5, 1.3), color="#5b3a2c", material=matte, bevel=.03))
        add(B.box("StallAwning", (6.8, 3.8, .12), (px, 10.5, 2.9), color="#8f3a2c" if i % 2 else "#35584d", material=matte))
        add(B.box("StallLight", (.6, .3, .16), (px, 8.7, 2.6), color="#ffd9a0", material=lamp))
    # plaza sculpture near river
    add(B.lathe("Sculpture", [(0.0, 0), (.8, 1.2), (1.6, 4.0), (.9, 7.0), (.2, 8.2)], loc=(-34, 88, 0),
                segments=14, color="#8f8a7c", material=stone))
    add(B.tube("SculptureRing", [(-34 + 3*math.cos(a), 88, 4 + 2.5*math.sin(a)) for a in [i*math.tau/24 for i in range(24)]],
               .12, "#ffc46b", neonWarm, segments=5, cyclic=True))
    # cars on avenue
    for i, (cx, cy) in enumerate([(5, 28), (-5, 12), (5, -8), (-5, 44), (5, 70)]):
        car(cx, cy, 0 if i % 2 else math.pi, ["#b8b2a2", "#3a4a52", "#7a2e2e", "#2e3a33"][i % 4])
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
    B.save_blend(os.path.join(B.ROOT, "assets", "zones", "city.blend"))
    B.export_glb(os.path.join(B.ROOT, "assets", "zones", "city.glb"))
    print("CITY EXPORTED", os.path.getsize(os.path.join(B.ROOT, "assets", "zones", "city.glb")))


if __name__ == "__main__":
    main()
