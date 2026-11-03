"""第二幕 · 街市暮 / 1990s county town. Original procedural scene, rebuilt denser."""
from __future__ import annotations
import math, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
import blib as B  # noqa: E402

B.reset(1996)
rng = random.Random(1996)
ALL = []
matte = B.vmat("TownMatte", .9)
concrete = B.vmat("TownConcrete", .93)
brick = B.vmat("TownBrick", .9)
wood = B.vmat("TownWood", .85)
metal = B.vmat("TownMetal", .45, .5)
stone = B.vmat("TownStone", .92)
glass = B.mat("TownGlass", "#1a2628", rough=.18, metal=.2)
warm = B.mat("TownWarm", "#ffc17a", rough=.5, emission="#ffb56a", emis_strength=1.7)
pale = B.mat("TownPale", "#f5e6c8", rough=.5, emission="#f7e7c7", emis_strength=1.0)
signs = B.mat("TownSigns", texture=os.path.join(B.ASSETS, "signs_atlas.png"), rough=.5,
              emission="#ffffff", emis_strength=1.8)
neon = B.mat("TownNeon", "#ff6a8a", rough=.4, emission="#ff6a8a", emis_strength=3.2)
redm = B.mat("TownRed", "#a43a2c", rough=.7, emission="#b2402e", emis_strength=.25)
water = B.mat("Water", "#3a625c", rough=.12, metal=.2)


def add(o):
    if isinstance(o, (list, tuple)):
        for x in o: add(x)
    else: ALL.append(o)


def shop_house(x, y, rot, w, d, h, style, key, seed=1, balcony=True, tile=False):
    r = random.Random(seed)
    objs = []
    wc = ["#ded1b8", "#e8dcc4", "#b98a6b", "#d9d0bf", "#cfc3a7"][seed % 5]
    # shop / ground floor
    objs.append(B.box("TownPlinth", (w + .4, d + .4, .45), (0, 0, .22), color="#806f58", material=stone, bevel=.03))
    objs.append(B.box("TownBody", (w, d, h), (0, 0, h / 2 + .45), color=wc, material=matte, bevel=.04))
    # shopfront on local -Y
    for i in range(3):
        ox = -w/2 + .8 + i * (w - 1.6) / 2
        objs.append(B.box("ShopGlass", ((w - 2.6) / 2, .08, 2.0), (ox, -d/2 - .05, 1.65), color="#172528",
                          material=glass if i % 2 else warm, bevel=.01))
    objs.append(B.box("ShopDoor", (1.25, .1, 2.2), (w/2 - 1.0, -d/2 - .06, 1.7), color="#423025", material=wood))
    # awning
    objs.append(B.box("Awning", (w * .92, 2.0, .12), (0, -d/2 - .9, 3.2), rot=(.12, 0, 0),
                      color="#7f3a2f" if seed % 2 else "#33544a", material=matte, bevel=.02))
    # sign above the awning
    objs.append(B.sign_quad("ShopSign", key, (0, -d/2 - .10, h * .62 + 1.3), 0, min(7.2, w * .82), 1.55, signs))
    objs.append(B.box("SignBack", (min(7.4, w * .86), .12, 1.75), (0, -d/2 - .02, h * .62 + 1.3),
                      color="#3a2a21", material=wood))
    # neon tube under awning
    objs.append(B.box("Neon", (w * .7, .05, .06), (0, -d/2 - 1.7, 2.75), color="#ff6a8a", material=neon))
    # upper windows
    floors = max(1, int((h - 4.0) / 3.0))
    for f in range(floors):
        z = 5.5 + f * 3.0
        for k in range(3 if w >= 7 else 2):
            wx = -w/2 + w * (k + .5) / (3 if w >= 7 else 2)
            objs.append(B.box("WinDark", (1.35, .06, 1.35), (wx, -d/2 - .04, z), color="#24343a", material=glass))
            objs.append(B.box("WinFrame", (1.55, .1, .09), (wx, -d/2 - .05, z + .72), color="#4a3829", material=wood))
            objs.append(B.box("WinFrame", (1.55, .1, .09), (wx, -d/2 - .05, z - .72), color="#4a3829", material=wood))
            if r.random() < .35:
                objs.append(B.box("WinWarm", (1.2, .04, 1.15), (wx, -d/2 - .075, z), color="#ffd9a0", material=warm))
            if r.random() < .22:
                objs.append(B.box("AC", (.75, .42, .5), (wx + .9, -d/2 - .25, z - .55), color="#8a8a80", material=metal))
        # balcony
        if balcony:
            objs.append(B.box("Balcony", (w * .82, 1.0, .14), (0, -d/2 - .6, z - 1.55), color="#7a6b58", material=concrete, bevel=.02))
            for k in range(7):
                objs.append(B.box("Rail", (.055, .055, .62), (-w * .38 + k * w * .76 / 6, -d/2 - 1.05, z - 1.2),
                                  color="#4b4a44", material=metal))
            if r.random() < .4:
                objs.append(B.quad("Laundry", [(-1.3, -d/2 - 1.07, z - 1.0), (.2, -d/2 - 1.07, z - 1.0),
                                               (.2, -d/2 - 1.07, z - .1), (-1.3, -d/2 - 1.07, z - .1)],
                                   r.choice(["#a94a3c", "#d9c7a0", "#4f6e78", "#c2a75f"]), matte))
    # roof
    if tile:
        objs.extend(B.tile_roof("TownRoof", 0, 0, h + .45, w + 1.2, d + 1.2, 1.35, .14, "#5f5b52", matte, curl=.35))
    else:
        objs.append(B.box("Parapet", (w + .3, d + .3, .55), (0, 0, h + .75), color="#6b6256", material=concrete))
        add_tank = r.random() < .55
        if add_tank:
            objs.append(B.cylinder("Tank", .8, 1.5, (w * .25, d * .2, h + 1.6), segments=10, color="#7f817b", material=metal))
        objs.append(B.cylinder("Antenna", .06, 3.5, (-w * .28, d * .15, h + 2.2), segments=5, color="#4a4c4f", material=metal))
    # side AC and small windows
    for f in range(floors):
        z = 6.5 + f * 3.0
        objs.append(B.box("SideWin", (.06, 1.0, 1.0), (w/2 + .04, 0, z), color="#203238", material=glass))
    # roof water tank
    B.apply_xform(objs, (x, y, 0), rot)
    add(objs)


def street_lamp(x, y, side=1):
    add(B.cylinder("LampPole", .09, 7.5, (x, y, 3.75), segments=7, color="#3f4143", material=metal))
    add(B.box("LampArm", (1.8, .08, .08), (x + side * .9, y, 7.3), color="#3f4143", material=metal))
    add(B.box("LampHead", (.9, .25, .16), (x + side * 1.75, y, 7.2), color="#ffd9a0", material=warm))
    B.empty("FX_Light", (x + side * 1.75, y, 7.2))


def power_pole(x, y, h=8.5):
    add(B.cylinder("PowerPole", .10, h, (x, y, h/2), segments=7, color="#4e4a42", material=wood))
    add(B.box("CrossArm", (1.9, .1, .1), (x, y, h - .5), color="#4e4a42", material=wood))
    for s in (-1, 1):
        add(B.cylinder("Insulator", .05, .16, (x + s*.75, y, h - .35), segments=6, color="#b8b09c", material=matte))


def bus_station(x, y):
    add(B.box("StationFloor", (18, 6, .22), (x, y, .11), color="#6f6b60", material=stone))
    add(B.box("StationRoof", (16, 5, .18), (x, y, 3.2), color="#3b3d3e", material=metal))
    for sx in (-7.5, 7.5):
        add(B.cylinder("StationPost", .10, 3.2, (x + sx, y - 2, 1.6), segments=6, color="#4c4e50", material=metal))
    add(B.box("StationBack", (16, .12, 1.8), (x, y + 2.4, 1.1), color="#202a2a", material=glass))
    add(B.box("StationBench", (8, .6, .18), (x - 2, y + 1.6, .6), color="#5d4a35", material=wood))
    add(B.sign_quad("StationSign", "bashi", (x, y - 2.7, 2.8), 0, 5.0, 1.1, signs))


def bus(x, y, rot=0):
    objs = []
    objs.append(B.box("BusBody", (10.5, 2.5, 2.8), (0, 0, 1.6), color="#e4e0d2", material=concrete, bevel=.1))
    objs.append(B.box("BusBand", (10.3, 2.52, .9), (0, 0, 2.15), color="#1c2f35", material=glass))
    for k in range(5):
        objs.append(B.box("BusWin", (1.2, .04, .8), (-3.8 + k * 1.9, -1.27, 2.15), color="#ffd9a0", material=warm))
    objs.append(B.box("BusRoof", (10.5, 2.4, .12), (0, 0, 3.05), color="#d6d3c8", material=concrete))
    for sx in (-3.5, 3.5):
        for sy in (-1.1, 1.1):
            objs.append(B.cylinder("BusWheel", .42, .28, (sx, sy, .42), rot=(math.pi/2, 0, 0), segments=10, color="#171817", material=metal))
    B.apply_xform(objs, (x, y, .12), rot)
    add(objs)


def bicycle(x, y, rot=0):
    objs = []
    for sx in (-.55, .55):
        pts = [(sx + .3*math.cos(i*math.tau/16), 0, .32 + .3*math.sin(i*math.tau/16)) for i in range(17)]
        objs.append(B.tube("BikeWheel", pts, .02, "#3a3833", metal, segments=4, cyclic=True))
    objs.append(B.tube("BikeFrame", [(-.55, 0, .32), (-.1, 0, .72), (.35, 0, .75), (.55, 0, .32)], .025, "#3e5f58", metal, segments=4))
    objs.append(B.box("BikeSeat", (.28, .1, .05), (-.12, 0, .82), color="#3a2a20", material=wood))
    objs.append(B.tube("BikeBar", [(.45, -.2, .85), (.45, .2, .85)], .018, "#8a8579", metal, segments=4))
    B.apply_xform(objs, (x, y, .05), rot); add(objs)


def main():
    add(B.ground_slab("TownBase", 320, 300, 9, colors=("#64513d", "#725c45", "#806a50", "#534434")))
    add(B.terrain("TownTerrain", 320, 300, 64, 60, lambda x, y: .0,
                  lambda x, y, z: "#6f7750" if y < 55 else "#78714f", matte))
    # main street
    add(B.road_ribbon("TownRoad", [(0, y) for y in range(-150, 151, 2)], 8.2, "#4e4d47", matte, z=.06, crown=.02, segments_width=4))
    for sx in (-7.2, 7.2):
        add(B.road_ribbon("Sidewalk", [(sx, y) for y in range(-150, 151, 2)], 4.0, "#7f796a", stone, z=.16, segments_width=2))
    for x in (-2.7, 2.7):
        add(B.road_line("Lane", [(x, y) for y in range(-150, 151, 4)], .10, "#c8bfa2", matte, z=.09, dash=3.0))
    # canal at y=40
    add(B.quad("Water_Canal", [(-160, 32, .04), (160, 32, .04), (160, 48, .04), (-160, 48, .04)], "#3a625c", water))
    for yy in (32, 48):
        for x0 in range(-160, 160, 16):
            if abs(x0 + 8) < 14: continue
            add(B.box("CanalWall", (16, .7, 1.0), (x0 + 8, yy, .5), color="#746b5b", material=stone, bevel=.03))
            add(B.box("CanalCap", (16.3, .9, .14), (x0 + 8, yy, 1.06), color="#8d8572", material=stone))
    for sx in (-7.5, 7.5):
        add(B.box("BridgeRail", (.35, 16, 1.05), (sx, 40, .55), color="#8d8572", material=stone, bevel=.02))
        for yy in range(34, 48, 3):
            add(B.box("BridgePost", (.4, .3, 1.0), (sx, yy, 1.0), color="#9a927e", material=stone))
    for yy in (36, 44):
        add(B.cylinder("BridgePier", 1.4, 2.2, (0, yy, -1.0), segments=10, color="#5e574b", material=stone))
    # buildings both sides
    left = [(-100, "baihuo", 8.5, 7.0, 10.5, 0, True, False), (-84, "zhaoxiang", 7.0, 6.0, 9.0, 1, True, True),
            (-68, "lifa", 6.2, 5.4, 8.2, 2, False, False), (-52, "shudian", 7.4, 6.2, 9.6, 3, True, False),
            (-24, "fandian", 8.0, 6.6, 11.5, 4, True, False), (-8, "gongxiaoshe", 7.2, 6.0, 9.2, 5, True, True),
            (8, "dianying", 10.0, 7.5, 12.0, 6, True, False), (24, "binggun", 6.0, 5.2, 8.0, 7, False, False),
            (62, "lushe", 8.0, 6.6, 11.0, 9, True, False),
            (86, "changluli", 7.2, 6.0, 9.4, 10, True, False), (110, "yeshi", 8.0, 6.4, 10.2, 11, True, False)]
    right = [(-106, "gongxiaoshe", 7.4, 6.2, 9.4, 12, True, False), (-88, "bashi", 7.0, 5.8, 8.6, 13, True, True),
             (-70, "huoguo", 6.4, 5.4, 8.4, 14, True, False), (-56, "mian", 6.2, 5.2, 8.0, 15, False, False),
             (-18, "yaodian", 6.8, 5.6, 8.8, 16, True, False), (0, "bianli", 7.0, 5.8, 9.0, 17, True, True),
             (18, "shufang", 7.6, 6.2, 9.8, 18, True, False), (38, "chalou", 8.0, 6.6, 10.6, 19, True, True),
             (58, "dianying", 9.4, 7.2, 11.6, 20, True, False), (80, "lushe", 7.8, 6.4, 10.2, 21, True, False),
             (104, "baihuo", 8.2, 6.6, 10.0, 22, True, True)]
    for (yy, key, w, d, h, seed, bal, tile) in left:
        shop_house(-13, yy, math.pi / 2, w, d, h, "town", key, 100 + seed, bal, tile)
    for (yy, key, w, d, h, seed, bal, tile) in right:
        shop_house(13, yy, -math.pi / 2, w, d, h, "town", key, 200 + seed, bal, tile)
    # cinema marquee on the left big building (seed 6 at y=8): extra poster wall
    for i in range(3):
        add(B.quad("Poster", [(-9.12, 4.2 + i*2.2, 5.6), (-9.12, 5.6 + i*2.2, 5.6),
                              (-9.12, 5.6 + i*2.2, 7.8), (-9.12, 4.2 + i*2.2, 7.8)],
                   ["#c7b26e", "#a9c1b2", "#c79074"][i], matte))
    # bus station on the right near the south
    bus_station(13, -124)
    bus(23, -124, 0)
    # street props
    for i in range(10):
        yy = -135 + i * 26
        street_lamp(-8.5, yy, -1)
        street_lamp(8.5, yy + 12, 1)
    for i in range(9):
        yy = -128 + i * 28
        power_pole(9.8, yy)
    for i in range(4):
        bicycle(-6.2, -60 + i * 26, rng.uniform(-.2, .2))
    # big tree by the canal and small square
    add(B.tree("TownTree", (13, 52, .15), 7.5, 3.6, "#3f5f3f", "#55422f", matte, matte, rng))
    add(B.tree("TownTree", (-14, 58, .15), 6.5, 3.2, "#446342", "#55422f", matte, matte, rng))
    add(B.box("Square", (22, 12, .08), (0, 64, .03), color="#8b8474", material=stone))
    add(B.box("Bench", (2.4, .55, .14), (-4, 60, .55), color="#5d4a35", material=wood))
    add(B.box("Bench", (2.4, .55, .14), (4, 68, .55), color="#5d4a35", material=wood))
    # red banner across the street
    add(B.box("BannerPole", (.1, .1, 6.5), (-8.5, -30, 3.25), color="#4a4a44", material=metal))
    add(B.box("BannerPole", (.1, .1, 6.5), (8.5, -30, 3.25), color="#4a4a44", material=metal))
    add(B.quad("Banner", [(-8.2, -30, 4.4), (8.2, -30, 4.4), (8.2, -30, 5.6), (-8.2, -30, 5.6)], "#a83a2c", matte))
    # car hotspot
    B.empty("FX_Hotspot", (3.5, 18, 1.4))
    B.empty("FX_Smoke_1", (-8, -60, 4))
    B.empty("FX_Light", (0, 64, 3))
    B.join_materials("Town2", ALL)
    B.save_blend(os.path.join(B.ROOT, "assets", "zones", "town2.blend"))
    B.export_glb(os.path.join(B.ROOT, "assets", "zones", "town2.glb"))
    print("TOWN2 EXPORTED", os.path.getsize(os.path.join(B.ROOT, "assets", "zones", "town2.glb")))


if __name__ == "__main__":
    main()
