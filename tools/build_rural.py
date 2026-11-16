"""第一幕 · 田埂晨 / 1980s village island.
Original procedural geometry; no external models or textures."""
from __future__ import annotations
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
import blib as B  # noqa: E402

SEED = 1983
B.reset(SEED)
rng = random.Random(SEED)
ALL = []
WATER = []

matte = B.vmat("Matte", 0.88)
rough = B.vmat("Rough", 0.95)
metal = B.vmat("Metal", 0.42, 0.5)
stone = B.vmat("Stone", 0.9)
water = B.mat("Water", "#2f5b62", rough=0.12, metal=0.25, alpha=0.92)
glass = B.mat("GlassWarm", "#e8b06a", rough=0.5, emission="#ffb765", emis_strength=1.5)
paper = B.mat("PaperWarm", "#e9c68d", rough=0.8, emission="#ffc27a", emis_strength=0.55)
lantern = B.mat("Lantern", "#b83a2c", rough=0.5, emission="#ff6a45", emis_strength=1.8)
signs = B.mat("Signs", texture=os.path.join(B.ASSETS, "signs_atlas.png"), rough=0.75)
neon = B.mat("SignsNeon", texture=os.path.join(B.ASSETS, "signs_atlas.png"), rough=0.5,
             emission="#ffffff", emis_strength=1.4)


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


def road_x(y):
    return 3.0 * math.sin((y + 145) / 52.0) + 1.2 * math.sin((y + 20) / 19.0)


def ground_h(x, y):
    xr = road_x(y)
    d = abs(x - xr)
    flat = max(0.0, 1.0 - d / 22.0)
    base = 0.18 * math.sin(x * 0.08) * math.cos(y * 0.07) + 0.09 * math.sin((x - y) * 0.17)
    hill = 0.0
    if x < -50:
        t = min(1.0, (-x - 50) / 85.0)
        hill = (t ** 1.65) * 15.0
    hill *= max(0.0, min(1.0, (y + 80) / 60.0)) * max(0.0, min(1.0, (120 - y) / 45.0))
    edge = 0.0
    if y > 105:
        edge = ((y - 105) / 45.0) ** 2 * 3.0
    if y < -115:
        edge = ((-y - 115) / 35.0) ** 2 * 2.0
    return (base + hill + edge) * (1 - flat) + 0.02 * flat


def _hash(ix, iy, seed=0):
    v = math.sin(ix * 127.1 + iy * 311.7 + seed * 74.7) * 43758.5453
    return v - math.floor(v)


def _smooth(t):
    return t * t * (3 - 2 * t)


def vnoise(x, y, seed=0):
    ix, iy = math.floor(x), math.floor(y)
    fx, fy = _smooth(x - ix), _smooth(y - iy)
    a = _hash(ix, iy, seed)
    b = _hash(ix + 1, iy, seed)
    c = _hash(ix, iy + 1, seed)
    d = _hash(ix + 1, iy + 1, seed)
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def fbm(x, y, seed=0, oct=3):
    total, amp, norm = 0.0, 1.0, 0.0
    for o in range(oct):
        total += vnoise(x * (2 ** o), y * (2 ** o), seed + o) * amp
        norm += amp
        amp *= 0.52
    return total / norm


def sstep(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


C = {
    "green": B.srgb("#6d8547"), "green2": B.srgb("#7e9452"), "dark": B.srgb("#586f3e"),
    "dry": B.srgb("#968f5c"), "wheat": B.srgb("#b3a257"), "rape": B.srgb("#b8b15e"),
    "veg": B.srgb("#5b7742"), "dirt": B.srgb("#8d7e5e"), "thresh": B.srgb("#a59775"),
    "rock": B.srgb("#7b7b64"), "hill": B.srgb("#778255"), "soil": B.srgb("#7d6d50"),
}

PATCHES = [
    (-20, -108, 30, 20, C["wheat"], 0.85), (28, -112, 34, 18, C["dry"], 0.7),
    (2, -82, 22, 12, C["rape"], 0.75), (-20, -78, 18, 10, C["veg"], 0.8),
    (-34, 14, 16, 12, C["veg"], 0.7), (-12, 12, 10, 9, C["veg"], 0.6),
    (-28, 3, 26, 26, C["dirt"], 0.48), (-32, -14, 14, 9, C["thresh"], 0.95),
    (60, -52, 30, 18, C["dry"], 0.45), (92, 45, 24, 16, C["dry"], 0.35),
    (-75, 50, 30, 40, C["hill"], 0.5), (-88, -40, 22, 30, C["hill"], 0.5),
    (18, -106, 12, 18, B.srgb("#8f8a4e"), 0.8), (-16, -97, 10, 16, B.srgb("#7f8b4b"), 0.8),
    (58, -62, 11, 8, B.srgb("#99934f"), 0.7), (-22, -58, 7, 9, B.srgb("#5f7743"), 0.7),
]


def ground_color(x, y, z):
    n = fbm(x * 0.045, y * 0.045, 3, 3)
    n2 = fbm(x * 0.22, y * 0.22, 7, 2)
    base = B.mix(C["green"], C["green2"], n * 0.75 + n2 * 0.25)
    for (cx, cy, rx, ry, col, strength) in PATCHES:
        d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
        if d < 1.6:
            t = sstep(1.35, 0.55, d) * strength
            base = B.mix(base, col, t)
    if x < -55:
        t = sstep(-55, -105, x) * 0.55
        base = B.mix(base, C["hill"], t)
        base = B.mix(base, C["rock"], max(0.0, sstep(-95, -140, x)) * 0.35 * n)
    d = abs(x - road_x(y))
    base = B.mix(base, C["soil"], sstep(7.2, 4.4, d) * 0.88)
    base = tuple(max(0, min(1, c * (0.9 + 0.18 * n2))) for c in base)
    return base


def stone_path(pts, width=1.4):
    obs = []
    for i in range(len(pts) - 1):
        x0, y0 = pts[i]
        x1, y1 = pts[i + 1]
        n = max(1, int(math.hypot(x1 - x0, y1 - y0) / 0.9))
        for k in range(n):
            t = (k + 0.5) / n
            x = x0 + (x1 - x0) * t
            y = y0 + (y1 - y0) * t
            if rng.random() < 0.8:
                obs.append(B.box(f"Stone_{i}_{k}", (width * rng.uniform(.7, 1.0), 0.7, 0.07),
                                 (x, y, ground_h(x, y) + 0.05), rot=(0, 0, rng.uniform(-.3, .3)),
                                 color="#918a78", material=stone, bevel=0.02))
    return obs


def house(x, y, rot, w, d, h, style="white", two=False, yard=False):
    objs = []
    z = ground_h(x, y)
    # stone plinth
    objs.append(B.box("HPlinth", (w + 0.5, d + 0.5, 0.55), (0, 0, 0.27),
                      color="#8b8170", material=stone, bevel=0.03))
    # walls
    wc = {"white": "#e6dfcf", "cream": "#e3d8bf", "brick": "#b67a5b"}.get(style, "#e6dfcf")
    objs.append(B.box("HWall", (w, d, h), (0, 0, h / 2 + 0.5), color=wc, material=matte, bevel=0.04))
    # lower stain band
    objs.append(B.box("HStain", (w + 0.02, d + 0.02, 0.55), (0, 0, 0.78),
                      color="#b0a58d", material=matte, bevel=0.01))
    # floor band for two storey
    if two:
        objs.append(B.box("HBand", (w + 0.08, d + 0.08, 0.18), (0, 0, h / 2 + 0.5),
                          color="#7e6a55", material=matte, bevel=0.01))
        for i in range(3):
            objs.append(B.box("HWinUp", (1.1, 0.06, 0.9), (-w / 3 + i * w / 3, -d / 2 - 0.04, h / 2 + 1.5),
                              color="#2b3b3e", material=glass, bevel=0.01))
    # roof
    rh = 1.9 if not two else 2.2
    objs.extend(B.tile_roof("HRoof", 0, 0, h + 0.5, w + 1.8, d + 1.5, rh, 0.18,
                            "#646158", matte, curl=0.38))
    objs.append(B.box("HRoofUnder", (w + 1.5, d + 1.2, 0.14), (0, 0, h + 0.34),
                      color="#3d3428", material=matte))
    # eave rafters
    for i in range(int(w / 0.85)):
        ox = -w / 2 + 0.4 + i * 0.85
        objs.append(B.box("HRafter", (0.075, 1.0, 0.11), (ox, -d / 2 - 0.45, h + 0.38),
                          color="#57422f", material=matte))
        objs.append(B.box("HRafter", (0.075, 1.0, 0.11), (ox, d / 2 + 0.45, h + 0.38),
                          color="#57422f", material=matte))
    # door + frame
    dw, dh = 1.45, 2.15
    objs.append(B.box("HDoor", (dw, 0.12, dh), (0, -d / 2 - 0.01, 0.55 + dh / 2),
                      color="#4a3021", material=matte, bevel=0.02))
    objs.append(B.box("HLintel", (dw + 0.4, 0.18, 0.16), (0, -d / 2 - 0.02, 0.55 + dh + 0.08),
                      color="#5b4634", material=matte))
    for sx in (-1, 1):
        objs.append(B.box("HDoorFrame", (0.13, 0.16, dh), (sx * (dw / 2 + 0.16), -d / 2 - 0.02, 0.55 + dh / 2),
                          color="#5b4634", material=matte))
    # couplets, fu
    objs.append(B.sign_quad("HFu", "fu", (0, -d / 2 - 0.09, 0.55 + dh - 0.48), 0, 0.62, 0.62, signs))
    objs.append(B.sign_quad("HLianA", "chunlian_a", (-dw / 2 - 0.52, -d / 2 - 0.08, 0.55 + dh / 2), 0, 0.3, 1.42, signs))
    objs.append(B.sign_quad("HLianB", "chunlian_b", (dw / 2 + 0.52, -d / 2 - 0.08, 0.55 + dh / 2), 0, 0.3, 1.42, signs))
    # windows
    positions = [-w / 2 + 1.55, w / 2 - 1.55] if w >= 7 else [-w / 2 + 1.35]
    for i, wx in enumerate(positions):
        objs.append(B.window_lattice("HWin", wx, -d / 2 - 0.03, 2.2, 1.45, 1.15,
                                     "y", -1, "#4c3928", matte, 4, "#e6c179", paper))
    # chimney
    objs.append(B.box("HChimney", (0.62, 0.62, 1.6), (w / 3, d / 3, h + 0.5 + rh * 0.55),
                      color="#a9a18d", material=matte, bevel=0.03))
    objs.append(B.box("HChimCap", (0.9, 0.9, 0.12), (w / 3, d / 3, h + 0.5 + rh * 0.55 + 0.82),
                      color="#6f6758", material=matte))
    # steps
    objs.append(B.box("HStep", (2.2, 0.6, 0.16), (0, -d / 2 - 0.35, 0.08),
                      color="#9e947e", material=stone, bevel=0.02))
    # side lean-to kitchen
    if style != "brick":
        ax = w / 2 + 1.6
        objs.append(B.box("Annex", (3.4, 3.2, 2.25), (ax, 0.2, 1.12), color="#c4b79e", material=matte, bevel=0.03))
        objs.append(B.box("AnnexRoof", (4.0, 3.8, 0.16), (ax, 0.2, 2.4), rot=(0.12, 0, 0),
                          color="#4f4c45", material=matte, bevel=0.02))
        objs.append(B.box("AnnexDoor", (1.0, 0.08, 1.8), (ax, -1.42, 1.05), color="#4a3021", material=matte))
    # courtyard wall with gate, optional
    if yard:
        for (wx, wy, ww, wd) in [(-(w / 2 + 2.6), -1.5, 0.18, 7.0), (w / 2 + 2.6, -1.5, 0.18, 7.0),
                                  (-w / 4 - 1.3, -5.0, 3.0, 0.18), (w / 4 + 1.3, -5.0, 3.0, 0.18)]:
            objs.append(B.box("YardWall", (ww, wd, 1.15), (wx, wy, 0.58), color="#d9d1bd", material=matte, bevel=0.02))
            objs.append(B.box("YardCap", (ww + 0.12, wd + 0.12, 0.12), (wx, wy, 1.19), color="#5a564e", material=matte))
    B.apply_xform(objs, (x, y, z), rot)
    add(objs)


def gate(cx, cy, rot):
    objs = []
    z = ground_h(cx, cy)
    for sx in (-1, 1):
        objs.append(B.box("GatePier", (1.0, 1.0, 4.2), (sx * 4.4, 0, 2.1), color="#8e8673", material=stone, bevel=0.05))
        objs.append(B.box("GateCap", (1.5, 1.4, 0.22), (sx * 4.4, 0, 4.28), color="#6b6455", material=stone, bevel=0.03))
    objs.append(B.box("GateBeam", (11.0, 0.55, 0.6), (0, 0, 4.7), color="#4c3829", material=matte, bevel=0.04))
    eave = B.tile_roof("GateEave", 0, 0, 4.78, 6.6, 15.2, 0.48, 0.10, "#6d6960", matte, curl=0.6, nx=12, ny=36)
    B.apply_xform(eave, (0, 0, 0), math.pi / 2)
    objs.extend(eave)
    roof = B.tile_roof("GateRoof", 0, 0, 5.38, 4.6, 12.6, 1.95, 0.16, "#6d6960", matte, curl=0.5, nx=16, ny=34)
    B.apply_xform(roof, (0, 0, 0), math.pi / 2)
    objs.extend(roof)
    from scene_lettering import porch_braces
    objs.extend(B.apply_xform(porch_braces(),(0,0,4.7)))
    B.apply_xform(objs, (cx, cy, z), rot)
    add(objs)


def big_tree(x, y, h=8.0):
    z = ground_h(x, y)
    objs = B.tree("Camphor", (0, 0, 0), h, 5.2, "#41603e", "#58432f", matte, matte, rng)
    # wind ribbons
    for i in range(7):
        a = rng.random() * math.tau
        rr = rng.uniform(1.0, 3.4)
        objs.append(B.box("Ribbon", (0.1, 0.02, rng.uniform(.5, 1.1)),
                          (math.cos(a) * rr, math.sin(a) * rr, h * rng.uniform(.55, .85)),
                          rot=(0, 0, rng.uniform(-.4, .4)), color="#a93127", material=matte))
    # stone shrine beneath
    objs.append(B.box("Shrine", (1.2, 0.9, 0.75), (0.8, 0.8, 0.38), color="#8d8574", material=stone, bevel=0.03))
    objs.append(B.box("ShrineTop", (1.4, 1.1, 0.12), (0.8, 0.8, 0.82), color="#5e584c", material=stone))
    B.apply_xform(objs, (x, y, z), 0)
    add(objs)


def paddy(x, y, w, d, rot, water_level=0.05, rows=3.0, color_water="#38615f"):
    z = ground_h(x, y)
    objs = []
    objs.append(B.quad("Water_Paddy", [(-w/2, -d/2, water_level), (w/2, -d/2, water_level),
                                       (w/2, d/2, water_level), (-w/2, d/2, water_level)],
                       color_water, water))
    # earth bunds
    for (bx, by, bw, bd) in [(0, -d/2, w+0.5, 0.35), (0, d/2, w+0.5, 0.35),
                              (-w/2, 0, 0.35, d+0.5), (w/2, 0, 0.35, d+0.5)]:
        objs.append(B.box("Bund", (bw, bd, 0.26), (bx, by, 0.13), color="#6f6845", material=rough, bevel=0.03))
    # one merged rice mesh per plot (fast, still thousands of blades)
    objs.append(B.rice_field("Rice", 0, 0, water_level + 0.02, w - 1.2, d - 1.2, 0,
                             spacing=max(0.7, rows * 0.48), height=0.4,
                             colors=("#7f9a4c", "#93ab5c"), material=matte, rng=rng,
                             blade_width=0.028, blades=4))
    B.apply_xform(objs, (x, y, z), rot)
    add([o for o in objs if not o.name.startswith("Water_")])
    add_water([o for o in objs if o.name.startswith("Water_")])


def terrace(x0, y0, y1, width, z, depth=10):
    objs = []
    # flat paddy
    objs.append(B.quad("Water_Terrace", [(-width/2, y0, 0.06), (width/2, y0, 0.06),
                                         (width/2, y1, 0.06), (-width/2, y1, 0.06)],
                       "#3d6460", water))
    # retaining stone wall along the downhill edge
    n = max(2, int((y1 - y0) / 2.0))
    for i in range(n):
        yy = y0 + (y1 - y0) * (i + 0.5) / n
        objs.append(B.box("TerraceWall", (0.8, (y1 - y0) / n + 0.1, 1.1),
                          (width/2 + 0.1, yy, -0.4), color="#7f7868", material=stone, bevel=0.04))
    # rice rows merged
    objs.append(B.rice_field("TRice", 0, (y0 + y1) / 2, 0.12, width - 2.0, (y1 - y0) - 2.0, 0,
                             spacing=1.15, height=0.38, colors=("#7f9850", "#8fa95c"),
                             material=matte, rng=rng, blade_width=0.03, blades=4))
    B.apply_xform(objs, (x0, 0, z), 0)
    add([o for o in objs if not o.name.startswith("Water_")])
    add_water([o for o in objs if o.name.startswith("Water_")])


def pond():
    cx, cy, rx, ry = 48, 38, 25, 16
    objs = []
    objs.append(B.ellipse_plane("Water_Pond", cx, cy, 0.07, rx, ry, 40, "#2f5b5e", water))
    objs.append(B.ring_wall("PondBank", cx, cy, -0.08, rx, ry, 0.8, 0.35, 40, "#837b66", stone))
    # rocks and reeds
    for i in range(24):
        a = rng.uniform(0, math.tau)
        px, py = cx + rx * math.cos(a) * rng.uniform(.96, 1.05), cy + ry * math.sin(a) * rng.uniform(.96, 1.05)
        objs.append(B.sphere("Rock", rng.uniform(.25, .7), (px, py, 0.18), scale=(1, .8, .55),
                             color="#77705e", material=stone, segments=7, rings=5))
    for i in range(70):
        a = rng.uniform(0, math.tau)
        px, py = cx + rx * math.cos(a) * rng.uniform(.9, 1.03), cy + ry * math.sin(a) * rng.uniform(.9, 1.03)
        h = rng.uniform(0.8, 2.0)
        objs.append(B.cylinder("Reed", 0.018, h, (px, py, h/2), segments=4, color="#7e7c4e", material=rough))
        objs.append(B.quad("ReedLeaf", [(px, py, h), (px+.16, py, h-.28), (px+.3, py, h-.5), (px+.16, py, h-.38)],
                           "#6e7b43", matte))
    # lotus
    for i in range(16):
        a = rng.uniform(0, math.tau)
        r = rng.uniform(0, .75)
        px, py = cx + rx * math.cos(a) * r, cy + ry * math.sin(a) * r
        objs.append(B.ellipse_plane("Lotus", px, py, 0.12, rng.uniform(.3, .6), rng.uniform(.25, .5), 12,
                                     "#4f7643", matte))
    # ducks
    for i in range(3):
        px, py = cx + 8 + i * 2.2, cy - 4 + rng.uniform(-2, 2)
        objs.append(B.sphere("DuckBody", .25, (px, py, .18), scale=(1.2, .7, .8), color="#ddd6c2", material=matte, segments=8, rings=6))
        objs.append(B.sphere("DuckHead", .12, (px + .22, py, .38), color="#ddd6c2", material=matte, segments=8, rings=6))
        objs.append(cone("DuckBeak", .05, .14, (px + .33, py, .37), rot=(0, math.pi/2, 0), color="#cc7b2f", material=matte, segments=6))
    B.apply_xform(objs, (0, 0, 0), 0)
    # water separately is already named Water_ and not joined; add all
    for o in objs:
        if o.name.startswith("Water_"):
            add_water(o)
        else:
            add(o)


def cone(name, r, depth, loc, rot=(0, 0, 0), color="#ffffff", material=None, segments=12):
    # small cone via cylinder with zero top radius
    return B.cylinder(name, r, depth, loc, rot, segments=segments, color=color, material=material,
                      cap=True, smooth=True, radius2=0.0)


def bridge(cx, cy, rot, span=8.0, width=2.0, rise=1.0):
    from model_craft import Batch
    masonry=Batch()
    masonry_colors=("#a39682","#938979","#b3a48d","#9f9380","#b6aa91")
    # Wedge stones run through the barrel. The open arch reveals the irrigation channel.
    for i in range(15):
        angles=[math.pi*i/15+.004,math.pi*(i+1)/15-.004]
        points=[]
        for yy in (-width/2,width/2):
            for rad,up,t in ((.69,0,angles[0]),(.69,0,angles[1]),(1,.17,angles[1]),(1,.17,angles[0])):
                points.append((span*.5*math.cos(t)*rad,yy,.02+(rise*.88+up)*math.sin(t)))
        masonry.part(points,[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],masonry_colors[i%5])
    for i in range(18):
        x=-span/2+(i+.5)*span/18
        foot=rise*math.sqrt(max(0,1-(x/(span/2))**2))
        masonry.box((x,0,foot+.08),(span/18+.015,width+.10,.18),masonry_colors[(i+2)%5])
        for side in (-1,1):
            masonry.box((x,side*(width/2-.015),foot+.27),(span/18+.015,.19,.35),masonry_colors[i%5])
    for x0 in (-span*.48,-span*.25,0,span*.25,span*.48):
        height=rise*math.sqrt(max(0,1-(x0/(span/2))**2))
        for side in (-1,1):
            yy=side*(width/2-.015)
            masonry.box((x0,yy,height+.53),(.24,.24,.70),"#a49681")
            masonry.box((x0,yy,height+.89),(.29,.29,.075),"#b8aa94")
    ob=masonry.object("Field bridge stone barrel and coping",stone)
    B.apply_xform([ob],(cx,cy,.05),rot)
    add(ob)


def well(x, y):
    z = ground_h(x, y)
    objs = []
    objs.append(B.cylinder("WellWall", 1.0, 1.0, (0, 0, 0.5), segments=16, color="#898171", material=stone))
    objs.append(B.cylinder("WellWater", 0.82, 0.1, (0, 0, 0.88), segments=16, color="#2f5359", material=water))
    for s in (-1, 1):
        objs.append(B.box("WellPost", (0.16, 0.16, 2.1), (s * .85, 0, 1.5), color="#54402d", material=matte))
    objs.append(B.box("WellRoof", (2.5, 1.4, 0.16), (0, 0, 2.55), color="#4c4841", material=matte))
    B.apply_xform(objs, (x, y, z), rng.uniform(-.2, .2))
    add(objs)


def haystack(x, y, r=1.2, h=2.2):
    z = ground_h(x, y)
    objs = []
    objs.append(B.lathe("Hay", [(r, .0), (r*.98, .15), (r*.85, h*.55), (r*.45, h*.9), (0.02, h)],
                        segments=14, color="#b79a58", material=rough))
    objs.append(B.cylinder("HayPole", .04, h + 1.2, (0, 0, (h + 1.2)/2), segments=5,
                           color="#6e5837", material=matte))
    B.apply_xform(objs, (x, y, z), rng.uniform(0, 3))
    add(objs)


def woodpile(x, y, rot=0):
    z = ground_h(x, y)
    objs = []
    for row in range(3):
        for i in range(5 - row):
            objs.append(B.cylinder("Log", .13, 1.6, (-.5 + i * .27 + row * .13, 0, .14 + row * .25),
                                   rot=(0, math.pi/2, 0), segments=6, color="#806343", material=matte))
    B.apply_xform(objs, (x, y, z), rot)
    add(objs)


def laundry(x, y, rot=0):
    z = ground_h(x, y)
    objs = []
    for s in (-1, 1):
        objs.append(B.cylinder("LaundryPole", .05, 3.4, (s * 2.2, 0, 1.7), segments=6, color="#6a553d", material=matte))
    objs.append(B.tube("LaundryLine", [(-2.2, 0, 3.2), (0, 0, 3.35), (2.2, 0, 3.2)], .015, "#3f3830", matte, segments=4))
    cols = ["#a94a3c", "#d9c7a0", "#4f6e78", "#b8874c", "#e0d8c4"]
    for i, c in enumerate(cols):
        vx = -1.7 + i * .85
        objs.append(B.quad("Cloth", [(vx, .02, 3.3), (vx + .55, .02, 3.3), (vx + .55, .04, 2.35), (vx, .04, 2.35)], c, matte))
    B.apply_xform(objs, (x, y, z), rot)
    add(objs)


def corn_string(x, y, z):
    objs = []
    for i in range(8):
        objs.append(B.cylinder("Corn", .055, .42, (x + rng.uniform(-.1, .1), y, z - i * .38),
                               rot=(0, math.pi/2, 0), segments=6, color="#d8a842", material=matte))
    objs.append(B.tube("CornRope", [(x, y, z + .2), (x, y, z - 3.2)], .01, "#6d5a3a", matte, segments=4))
    add(objs)


def bike(x, y, rot=0):
    z = ground_h(x, y)
    objs = []
    for sx in (-0.58, 0.58):
        pts = []
        for i in range(17):
            a = math.tau * i / 16
            pts.append((sx + .33 * math.cos(a), 0, .36 + .33 * math.sin(a)))
        objs.append(B.tube("BikeWheel", pts, .022, "#3c3a35", metal, segments=4, cyclic=True))
        for i in range(8):
            a = math.tau * i / 8
            objs.append(B.beam("Spoke", (sx, 0, .36), (sx + .3 * math.cos(a), 0, .36 + .3 * math.sin(a)),
                               .008, .008, "#8a8579", metal))
    objs.append(B.tube("BikeFrame", [(-.58, 0, .36), (-.1, 0, .78), (.3, 0, .82), (.58, 0, .36)], .03,
                       "#3f5e58", metal, segments=4))
    objs.append(B.tube("BikeFrame2", [(-.1, 0, .78), (-.05, 0, .36), (.3, 0, .82)], .028, "#3f5e58", metal, segments=4))
    objs.append(B.beam("Bicycle stand", (-.28, 0, .36), (-.43, .18, .006), .022,.022, "#64635a", metal))
    objs.append(B.box("BikeSeat", (.3, .12, .06), (-.12, 0, .9), color="#3d2b20", material=matte))
    objs.append(B.tube("BikeBar", [(.5, -.22, .92), (.5, .22, .92)], .018, "#8a8579", metal, segments=4))
    B.apply_xform(objs, (x, y, z), rot)
    add(objs)


def make_ridge(name, along, base_coord, length, heights, color_low, color_high, thickness=4.0):
    """A mountain silhouette wall along X (along='x') or Y."""
    n = len(heights) - 1
    verts, faces, fc = [], [], []
    for layer in (0, 1):
        off = layer * thickness
        for i, h in enumerate(heights):
            t = i / n
            if along == "x":
                x = -length/2 + length * t
                y = base_coord + off
            else:
                x = base_coord + off
                y = -length/2 + length * t
            verts.append((x, y, -0.2))
            verts.append((x, y, h))
    for layer in (0, 1):
        for i in range(n):
            a = layer * (2 * (n + 1)) + i * 2
            faces.append((a, a + 2, a + 3, a + 1))
            z = (heights[i] + heights[i + 1]) * .5
            fc.append(B.srgb(color_high if z > 10 else color_low))
    ob = B._finish(name, verts, faces, None, B.vmat("Mountain", .95), smooth=False, face_colors=fc)
    add(ob)


def mountain_band(name, axis, a0, a1, amp, seed):
    if axis == "y":
        nx, ny = 110, 12
        def at(ix, iy):
            x = -160 + 320 * ix / nx
            y = a0 + (a1 - a0) * iy / ny
            return x, y, x, iy / ny
    else:
        nx, ny = 12, 120
        def at(ix, iy):
            x = a0 + (a1 - a0) * ix / nx
            y = -150 + 300 * iy / ny
            return x, y, y, ix / nx
    verts, faces, fc = [], [], []
    heights = []
    prng = random.Random(seed * 991 + 7)
    peaks = []
    for k in range(7):
        center = -165 + 330*(k+.45)/7 + prng.uniform(-9,9)
        peaks.append((center, prng.uniform(20,38), prng.uniform(.30,.97)))
    for iy in range(ny + 1):
        for ix in range(nx + 1):
            x, y, along, t = at(ix, iy)
            ridge = .57 + .15*math.sin(along*.031+seed)
            flank = t/ridge if t < ridge else (1-t)/(1-ridge)
            profile = math.sin(math.pi*.5*max(0,flank))**1.65
            env = max(hh*math.exp(-((along-center)/width)**2) for center,width,hh in peaks)
            saddle = 1-.74*math.exp(-((along-36)/28)**2)
            folds = .87+.13*math.sin(along*.105+t*4)+.10*fbm(along*.08,t*4,seed,2)
            h = amp*profile*(.05+env)*saddle*folds
            verts.append((x, y, max(0.0, h)))
            heights.append(h)
    for iy in range(ny):
        for ix in range(nx):
            a = iy * (nx + 1) + ix
            b = a + 1
            c = a + nx + 2
            d = a + nx + 1
            faces.append((a, b, c, d))
            h = (heights[a] + heights[b] + heights[c] + heights[d]) / 4
            t = max(0.0, min(1.0, h / max(amp, .01)))
            col = B.mix(B.srgb("#718f70"), B.srgb("#a4b397"), t * .72)
            col = B.mix(B.srgb("#56765d"), col, .59 + .21*math.sin(ix*.13+iy*.24))
            fc.append(tuple(max(0, min(1, q * (0.97 + 0.06 * rng.random()))) for q in col))
    ob = B._finish(name, verts, faces, None, B.vmat("Mountain", 0.97), smooth=True, face_colors=fc)
    add(ob)


def conifer(x, y, h=4.0, color="#3c5838"):
    z = ground_h(x, y)
    objs = [B.cylinder("ConiferTrunk", .09, h * .65, (x, y, z + h * .32), segments=5,
                       color="#4f3f2e", material=matte)]
    for (r, zz, hh) in [(0.34, .50, .52), (0.28, .70, .42), (0.20, .88, .32)]:
        objs.append(B.cylinder("ConiferNeedle", h * r, h * hh, (x, y, z + h * zz),
                               segments=8, color=color, material=matte, radius2=0.02))
    add(objs)


def crop_bands(x, y, w, d, rot, colors=("#b9a45f", "#c8b46e"), height=.72, rows=12):
    """Stylised cut-paper crop rows: ridged soil + serrated vertical ribbons."""
    z = ground_h(x, y)
    objs = []
    row_w = w / rows
    for i in range(rows):
        px = -w / 2 + (i + .5) * row_w
        objs.append(B.box("CropRidge", (row_w * .72, d, .18), (px, 0, .09),
                          color="#7a6748", material=rough, bevel=.015))
        for layer in (-1, 1):
            # vertical ribbon with a serrated top, running along local Y
            verts, faces, fc = [], [], []
            segs = max(4, int(d / .55))
            for k in range(segs + 1):
                yy = -d / 2 + d * k / segs
                hh = height * (0.82 + 0.18 * math.sin(k * 1.7 + i * .8 + layer)) + rng.uniform(-.05, .05)
                verts.append((px + layer * row_w * .18, yy, .12))
                verts.append((px + layer * row_w * .18, yy, .12 + hh))
            for k in range(segs):
                a = k * 2
                faces.append((a, a + 2, a + 3, a + 1))
                fc.append(B.vary(B.srgb(colors[(i + k) % 2]), 0.06))
            objs.append(B._finish("CropRibbon", verts, faces, None, matte, smooth=False, face_colors=fc))
    B.apply_xform(objs, (x, y, z), rot)
    add(objs)


def crop_rows(x, y, w, d, rot, colors=("#b1a052", "#c0b262"), height=.8, spacing=.85):
    z = ground_h(x, y)
    ob = B.rice_field("Crop", 0, 0, 0.06, w, d, 0, spacing=spacing, height=height,
                      colors=colors, material=matte, rng=rng,
                      blade_width=0.018, blades=5)
    B.apply_xform([ob], (x, y, z), rot)
    add(ob)
    n = max(2, int(d / 3.2))
    for i in range(n):
        yy = -d / 2 + i * d / n
        f = B.box("Furrow", (w, .22, .05), (0, yy, .03), color="#736344", material=rough)
        B.apply_xform([f], (x, y, z), rot)
        add(f)


def banyan(x, y, h=9.6):
    z = ground_h(x, y)
    objs = []
    objs.append(B.lathe("BanyanTrunk", [(1.15, 0), (.95, .7), (.7, 2.2), (.5, 4.2), (.38, 6.0)],
                        segments=12, color="#5a4430", material=matte))
    for i in range(5):
        a = math.tau * i / 5 + .3
        rr = 1.0 + rng.random() * .8
        objs.append(B.tube("BanyanRoot", [(0, 0, 1.4), (math.cos(a) * rr, math.sin(a) * rr, .12)],
                           .22, "#58422f", matte, segments=5))
    clump_specs = []
    for i in range(13):
        a = math.tau * i / 13 + rng.uniform(-.2, .2)
        rr = rng.uniform(1.2, 4.8)
        cx, cy = math.cos(a) * rr, math.sin(a) * rr
        cz = h * rng.uniform(.62, .96)
        rx = rng.uniform(1.5, 2.7)
        clump_specs.append((cx, cy, cz, rx))
        objs.append(B.tube("BanyanBranch", [(0, 0, h * .52), (cx * .45, cy * .45, cz * .82), (cx, cy, cz)],
                           .10, "#5a4430", matte, segments=5))
    for i, (cx, cy, cz, rx) in enumerate(clump_specs):
        col = ["#3f5f3c", "#4b6d44", "#58794b", "#456540"][i % 4]
        objs.append(B.sphere("BanyanLeaf", rx, (cx, cy, cz), scale=(1, 1, rng.uniform(.55, .8)),
                             color=col, material=matte, segments=9, rings=6))
    for i in range(14):
        a = rng.uniform(0, math.tau)
        rr = rng.uniform(2.4, 4.8)
        cx, cy = math.cos(a) * rr, math.sin(a) * rr
        top = h * rng.uniform(.62, .82)
        objs.append(B.tube("AerialRoot", [(cx, cy, top), (cx + rng.uniform(-.2, .2), cy, top * .5),
                                          (cx + rng.uniform(-.3, .3), cy, .05)],
                           .035, "#63503a", matte, segments=4))
    for i in range(8):
        a = rng.random() * math.tau
        rr = rng.uniform(2.0, 4.2)
        objs.append(B.box("Ribbon", (.1, .02, rng.uniform(.6, 1.2)),
                          (math.cos(a) * rr, math.sin(a) * rr, h * rng.uniform(.55, .8)),
                          rot=(0, 0, rng.uniform(-.4, .4)), color="#a93127", material=matte))
    objs.append(B.box("Shrine", (1.2, .9, .8), (.9, .8, .4), color="#8d8574", material=stone, bevel=.03))
    objs.append(B.box("ShrineTop", (1.45, 1.1, .12), (.9, .8, .86), color="#5e584c", material=stone))
    for s in (-1, 1):
        objs.append(B.box("Bench", (2.6, .55, .16), (-1.7, s * 1.3, .48), color="#6b563e", material=matte))
        objs.append(B.box("BenchLeg", (.16, .45, .45), (-2.7, s * 1.3, .22), color="#5a4935", material=matte))
        objs.append(B.box("BenchLeg", (.16, .45, .45), (-.7, s * 1.3, .22), color="#5a4935", material=matte))
    B.apply_xform(objs, (x, y, z), 0)
    add(objs)


def fence_line(pts, height=0.8, color="#817056"):
    objs = []
    for i in range(len(pts) - 1):
        x0, y0 = pts[i]
        x1, y1 = pts[i + 1]
        L = math.hypot(x1 - x0, y1 - y0)
        n = max(1, int(L / 1.7))
        for k in range(n + 1):
            t = k / n
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            z = ground_h(x, y)
            objs.append(B.box("FencePost", (.1, .1, height), (x, y, z + height / 2), color=color, material=matte))
        for level in (.42, .9):
            objs.append(B.beam("FenceRail", (x0, y0, ground_h(x0, y0) + level), (x1, y1, ground_h(x1, y1) + level),
                               .07, .07, color, matte))
    add(objs)


def village_shop(x, y, rot):
    objs = []
    z = ground_h(x, y)
    objs.append(B.box("ShopPlinth", (8.4, 5.4, .45), (0, 0, .22), color="#8b8170", material=stone, bevel=.03))
    objs.append(B.box("ShopWall", (8, 5, 3.2), (0, 0, 2.05), color="#dcd2bc", material=matte, bevel=.04))
    objs.extend(B.tile_roof("ShopRoof", 0, 0, 3.6, 9.4, 6.5, 1.7, .16, "#615d54", matte, curl=.36))
    objs.append(B.box("ShopUnder", (9, 6.1, .12), (0, 0, 3.45), color="#3d3428", material=matte))
    for i, wx in enumerate((-2.3, 2.3)):
        objs.append(B.box("ShopWin", (2.1, .08, 1.35), (wx, -2.52, 1.85), color="#26383a", material=glass, bevel=.01))
        objs.append(B.box("ShopWinFrame", (2.3, .12, .1), (wx, -2.54, 2.55), color="#4c3928", material=matte))
        objs.append(B.box("ShopWinFrame", (2.3, .12, .1), (wx, -2.54, 1.15), color="#4c3928", material=matte))
    objs.append(B.box("ShopDoor", (1.3, .12, 2.2), (0, -2.53, 1.55), color="#4a3021", material=matte, bevel=.02))
    objs.append(B.box("ShopAwning", (8.2, 2.3, .12), (0, -3.5, 2.72), rot=(.16, 0, 0), color="#8b3a2f", material=matte))
    for sx in (-3.6, 0, 3.6):
        objs.append(B.box("AwningPost", (.1, .1, 2.5), (sx, -4.4, 1.25), color="#5a4632", material=matte))
    # The street-facing fascia and its dimensional lettering are fitted over this eave in the interactive set.
    for s in (-1, 1):
        objs.append(B.box("ShopBench", (3.0, .5, .15), (-4.3, s * 1.5, .5), color="#6b563e", material=matte))
        objs.append(B.box("ShopBenchLeg", (.14, .42, .48), (-5.5, s * 1.5, .25), color="#5a4935", material=matte))
        objs.append(B.box("ShopBenchLeg", (.14, .42, .48), (-3.1, s * 1.5, .25), color="#5a4935", material=matte))
    for i in range(3):
        objs.append(B.sphere("Sack", .32, (3.4 + (i % 2) * .5, -3.2 + (i // 2) * .5, .35),
                             scale=(1, .75, 1.1), color="#b8a578", material=rough, segments=8, rings=5))
    objs.append(B.box("NoticeBoard", (1.7, .1, 1.4), (-3.9, -3.1, 1.9), color="#6f5a40", material=matte))
    from scene_lettering import grain_notice
    objs.extend(B.apply_xform(grain_notice(),(-3.9,-3.1,1.9)))
    B.apply_xform(objs, (x, y, z), rot)
    add(objs)


def main():
    # island base + terrain
    add(B.ground_slab("Base", 320, 300, 9, colors=("#6f5b42", "#7e674a", "#8a7658", "#5a4a39"),cap=False))
    add(B.terrain("Terrain", 320, 300, 170, 156, ground_h, ground_color, matte, z0=0.0, smooth=True,
                  section=("#726c58","#89816a","#948d70","#878a6c","#83906e")))

    # entry paddies
    for i, (x, y, w, d, rot) in enumerate([
        (-52, -104, 26, 14, .06), (74, -108, 28, 14, -.05), (100, -88, 24, 16, .02),
        (-38, -78, 20, 12, .1),
    ]):
        paddy(x, y, w, d, rot)
    # foreground crop fields, visible from the starting point
    crop_bands(18, -106, 22, 34, .03, ("#a99a5c", "#bdaa6a"), .38, 12)
    crop_bands(-16, -97, 18, 30, -.02, ("#8c9752", "#a3aa60"), .34, 11)
    crop_bands(-22, -58, 12, 16, .04, ("#5f7e46", "#789254"), .3, 9)
    crop_bands(58, -62, 20, 14, .02, ("#a99a5c", "#bba86a"), .34, 10)
    # right paddies
    for i, (x, y, w, d, rot) in enumerate([
        (72, -30, 32, 18, .03), (104, -2, 28, 20, -.04), (72, 18, 28, 16, .06),
        (106, 38, 26, 18, -.02), (76, 68, 32, 16, .04), (44, 78, 22, 14, -.06),
    ]):
        paddy(x, y, w, d, rot)
    # road
    road_pts = [(road_x(y), y) for y in range(-145, 146, 2)]
    add(B.road_ribbon("Road", road_pts, 3.2, "#8b7b5d", rough, z=0.06, crown=0.05, segments_width=4))
    add(B.road_ribbon("RoadShoulder", road_pts, 4.3, "#998a6c", rough, z=0.035, crown=0.02, segments_width=2))
    add(B.road_ribbon("CenterGrass", road_pts, 0.5, "#6e7d4a", rough, z=0.075, crown=0.0, segments_width=1))
    # wheel ruts
    for off in (-0.82, 0.82):
        ruts = []
        for i in range(0, len(road_pts) - 1):
            x0, y0 = road_pts[i]; x1, y1 = road_pts[i+1]
            dx, dy = x1-x0, y1-y0; L = math.hypot(dx, dy) or 1
            nx, ny = -dy/L, dx/L
            ruts.append((x0 + nx*off, y0 + ny*off))
        add(B.road_ribbon("Rut", ruts, 0.17, "#6d604d", rough, z=0.095, crown=0.0, segments_width=1))
    # stone lanes
    add(stone_path([(-1, -32), (-6, -20), (-14, -12), (-20, 0)], 1.6))
    add(stone_path([(-20, 0), (-24, 12), (-30, 26), (-26, 40)], 1.4))
    add(stone_path([(0, -8), (-8, -7), (-16, -5)], 1.2))

    # village gate + tree
    gate(-1.5, -36, 0.04)
    banyan(13, -27, 9.6)
    village_shop(-7.8, -49, math.pi / 2)
    # fences framing the approach
    fence_line([(road_x(y) - 6.2, y) for y in range(-128, -112, 8)], .8)
    fence_line([(-29, -58), (-29, -48), (-15, -48)], .75)
    # a few weathered stones at the field edge
    for i in range(9):
        wy = -52 - i * 4.5
        wx = road_x(wy) + 6.8 + rng.uniform(-.4, .4)
        add(B.sphere("FieldStone", rng.uniform(.25, .55), (wx, wy, ground_h(wx, wy)+.18),
                     scale=(1.2, 1, .6), color="#8d8574", material=stone, segments=7, rings=5))
    B.empty("FX_Hotspot", (0.2, -12, 1.3))
    B.empty("FX_Smoke_1", (5.2, 12.8, 8.2))
    B.empty("FX_Smoke_2", (-12.0, 15.5, 7.0))
    B.empty("FX_Fireflies", (42, 34, 1.2))

    # houses
    house(-24, 2, 0.05, 9.5, 7.0, 3.6, "white", True, True)
    house(-40, 5, 0.16, 7.2, 6.0, 3.2, "cream", False, True)
    house(-14, 24, 0.95, 8.0, 6.2, 3.3, "white", False, False)
    house(-35, 26, -0.12, 6.4, 5.4, 3.0, "brick", False, True)
    house(-7, 43, 1.45, 7.4, 6.0, 3.2, "cream", False, False)
    house(-29, 47, 0.04, 10.0, 7.2, 5.9, "brick", True, False)
    house(-45, 49, 0.2, 6.8, 5.4, 3.1, "white", False, False)
    house(-16, 61, -1.5, 8.2, 6.0, 3.4, "white", False, False)
    house(-40, 70, 0.05, 7.0, 5.6, 3.2, "cream", False, False)

    # courtyards, props
    well(-19, 17)
    haystack(-36, -8, 1.4, 2.6)
    haystack(-41, -3, 1.0, 1.9)
    haystack(-28, 15, 1.2, 2.2)
    woodpile(-41.5, 20, 0.02)
    woodpile(-18.5, 12, 0.2)
    laundry(-30, 14, 0.04)
    laundry(-19, 51, 1.5)
    corn_string(-19.2, 1.0, 4.2)
    corn_string(-18.0, 1.1, 4.2)
    bike(-11, 14, 0.4)
    bike(-8.1, -38.4, 0.08)
    # threshing ground
    add(B.quad("Thresh", [(-40, -19, 0.08), (-24, -19, 0.08), (-24, -8, 0.08), (-40, -8, 0.08)], "#a29472", rough))
    for i in range(4):
        add(B.quad("GrainMat", [(-38 + i*3.8, -17.5, 0.1), (-35.6 + i*3.8, -17.5, 0.1),
                                (-35.6 + i*3.8, -12.0, 0.1), (-38 + i*3.8, -12.0, 0.1)],
                   "#c3a75c" if i % 2 else "#b99a51", rough))
    add(B.cylinder("StoneRoller", .28, 1.4, (-30, -15, .38), rot=(0, math.pi/2, 0), segments=14,
                   color="#8b8574", material=stone))

    # pond and bridge
    pond()
    bridge(48, 17, .03, 9, 2.2, 1.12)
    # reeds along a stream edge
    for i in range(30):
        x, y = 68 + rng.uniform(-2, 2), 50 + rng.uniform(-10, 10)
        add(B.grass_tuft("ReedGrass", x, y, 0.1, rng.uniform(.6, 1.2), "#8b8a55", rough, rng))

    # terraces on the left hill
    for k in range(6):
        x = -64 - k * 9.5
        y0 = -32 + k * 2
        y1 = 90 - k * 3
        terrace(x, y0, y1, 10.0, 0.9 + k * 1.35)
    # hill hut
    house(-118, 42, -0.12, 6.0, 5.0, 2.7, "cream", False, False)
    # bamboo
    for i in range(22):
        bx, by = -55 + rng.uniform(-4, 4), 6 + rng.uniform(-4, 4)
        h = rng.uniform(4, 7)
        add(B.cylinder("Bamboo", .035, h, (bx, by, h/2), segments=5, color="#6f8a4f", material=matte))
        for k in range(3):
            add(B.quad("BambooLeaf", [(bx, by, h - k*.8), (bx+.5, by+.2, h-k*.8-.35),
                                       (bx+.85, by+.45, h-k*.8-.5), (bx+.45, by+.15, h-k*.8-.3)],
                       "#5e7c43", matte))
    # scattered trees
    for (tx, ty, h) in [(75, 8, 6.5), (92, -16, 5.5), (62, -52, 6.0), (110, 20, 5.0),
                         (-52, -30, 5.5), (-58, 32, 6.0), (-6, -55, 5.0), (24, 75, 6.5),
                         (-52, 78, 5.5), (112, 60, 5.0), (5, 95, 5.5)]:
        add(B.tree("Tree", (tx, ty, ground_h(tx, ty)), h, h*.48, "#486843", "#5b4935", matte, matte, rng))
    # shrubs
    for i in range(80):
        sx, sy = rng.uniform(-130, 130), rng.uniform(-125, 125)
        if abs(sx - road_x(sy)) < 6 or (sx > 20 and sy > 5 and sy < 60):
            continue
        if abs(sx + 28) < 22 and -25 < sy < 70:
            continue
        add(B.sphere("Shrub", rng.uniform(.35, .8), (sx, sy, ground_h(sx, sy) + .25),
                     scale=(1.2, 1, .75), color="#557348" if i % 3 else "#47653e",
                     material=matte, segments=7, rings=5))
    # grass near road (one merged mesh)
    gpts = []
    for i in range(190):
        gy = -132 + i * 1.42
        gx = road_x(gy) + rng.choice([-1, 1]) * rng.uniform(2.7, 5.8)
        gpts.append((gx, gy, ground_h(gx, gy) + 0.02))
    add(B.tufts_mesh("RoadGrass", gpts, height=0.38, color="#6e864b", material=matte, rng=rng))
    # power line
    poles = []
    for i, py in enumerate([-100, -62, -25, 12, 50, 88, 122]):
        px = road_x(py) + 6.5
        pz = ground_h(px, py)
        poles.append((px, py, pz))
        add(B.cylinder("PowerPole", .12, 7.8, (px, py, pz + 3.9), segments=8, color="#5e584c", material=matte))
        add(B.box("CrossArm", (2.4, .12, .12), (px, py, pz + 7.35), color="#4d4639", material=matte))
        for s in (-1, 1):
            add(B.cylinder("Insulator", .07, .2, (px + s*.95, py, pz + 7.5), segments=6,
                           color="#b8b09c", material=matte))
    for i in range(len(poles) - 1):
        x0, y0, z0 = poles[i]; x1, y1, z1 = poles[i+1]
        for s in (-1, 1):
            pts = []
            for k in range(9):
                t = k / 8
                pts.append((x0 + (x1-x0)*t + s*.95, y0 + (y1-y0)*t,
                            z0 + (z1-z0)*t + 7.5 - 1.5 * math.sin(math.pi * t)))
            add(B.tube("Wire", pts, .018, "#2e2a25", matte, segments=4))
    # layered mountain bands, cut by the island edge
    mountain_band("MountainBack", "y", 110, 150, 31, 2)
    mountain_band("MountainLeft", "x", -158, -116, 26, 5)
    mountain_band("MountainRight", "x", 128, 158, 13, 8)
    # dark tree line at the foot of the mountains
    for i in range(40):
        tx = -152 + i * 7.7 + rng.uniform(-2.5, 2.5)
        ty = 104 + rng.uniform(-7, 4)
        conifer(tx, ty, rng.uniform(3.0, 7.0), "#385235" if i % 2 else "#405c3b")
    for i in range(16):
        tx = -150 + i * 19 + rng.uniform(-4, 4)
        ty = -142 + rng.uniform(-2, 2)
        conifer(tx, ty, rng.uniform(3.5, 6.5), "#3a5437")
    # a few more trees around the village
    for (tx, ty, h) in [(-47, -12, 6.4), (-8, 68, 6.8), (20, 50, 5.8), (-52, 88, 6.2), (86, 70, 6.8)]:
        add(B.tree("Tree", (tx, ty, ground_h(tx, ty)), h, h*.5, "#446440", "#5b4935", matte, matte, rng))
    # orchard on the empty right slope
    for row in range(5):
        for col in range(7):
            tx = 72 + col * 8.0 + rng.uniform(-.8, .8)
            ty = 6 + row * 7.5 + rng.uniform(-.8, .8)
            add(B.tree("Orchard", (tx, ty, ground_h(tx, ty)), rng.uniform(2.8, 4.0), 1.5,
                       "#4a6a40" if col % 2 else "#557646", "#5b4935", matte, matte, rng))
    # solitary farmstead by the pond
    house(82, 33, 0.15, 7.0, 5.6, 3.1, "cream", False, True)
    haystack(74, 45, 1.0, 1.9)

    # chickens in the threshing yard
    for i in range(7):
        px, py = -35 + rng.uniform(-3.5, 4.5), -16 + rng.uniform(-2.5, 3.0)
        pz = ground_h(px, py) + .2
        col = "#e0d6bf" if i % 3 else "#b98a5a"
        add(B.sphere("ChickenBody", .18, (px, py, pz), scale=(1.25, .8, .9), color=col, material=matte, segments=8, rings=5))
        add(B.sphere("ChickenHead", .085, (px + .18, py, pz + .16), color=col, material=matte, segments=8, rings=5))
        add(cone("ChickenBeak", .025, .09, (px + .27, py, pz + .16), rot=(0, math.pi/2, 0), color="#c98a2e", material=matte, segments=5))
        add(B.quad("ChickenTail", [(px - .16, py, pz + .12), (px - .34, py, pz + .27),
                                   (px - .27, py, pz + .02), (px - .16, py, pz + .02)], "#7a5f42", matte))
        if i == 0:
            add(B.sphere("Comb", .06, (px + .18, py, pz + .26), scale=(1.2, .6, .8), color="#b83228", material=matte, segments=6, rings=4))
    # puddles and stones on the road
    for i in range(7):
        py = -118 + i * 27 + rng.uniform(-4, 4)
        px = road_x(py) + rng.uniform(-1.1, 1.1)
        add_water(B.ellipse_plane("Water_Puddle", px, py, 0.105, rng.uniform(.4, 1.1), rng.uniform(.18, .38),
                                  12, "#5f6a60", water))
    for i, py in enumerate([-118, -72, 26]):
        px = road_x(py) + rng.choice([-1, 1]) * rng.uniform(1.4, 2.2)
        add(B.sphere("RoadStone", rng.uniform(.08, .2), (px, py, ground_h(px, py) + .07),
                     scale=(1.2, 1, .55), color="#8f8676", material=stone, segments=6, rings=4))
    # small wildflowers by the verge
    for i in range(70):
        py = -126 + i * 2.9
        px = road_x(py) + rng.choice([-1, 1]) * rng.uniform(2.2, 4.2)
        add(B.sphere("Flower", .045, (px, py, ground_h(px, py) + .28), color="#e0cf7a" if i % 3 else "#e6e0cc",
                     material=matte, segments=6, rings=4))
    # join by material
    B.join_materials("Rural", ALL)
    # export
    B.save_blend(os.path.join(B.ROOT, "assets", "zones", "rural.blend"))
    B.export_glb(os.path.join(B.ROOT, "assets", "zones", "rural.glb"))
    print("RURAL EXPORTED", os.path.getsize(os.path.join(B.ROOT, "assets", "zones", "rural.glb")))


if __name__ == "__main__":
    main()
