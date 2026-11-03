"""第三幕 · 长街黄昏 / 1990s county town island + boxy 1990s sedan.
Original procedural geometry; the only external image is the project's own sign atlas.
Run:  blender -b --factory-startup --python tools/build_town.py -- town
      blender -b --factory-startup --python tools/build_town.py -- car
"""
from __future__ import annotations

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
import blib as B  # noqa: E402

SEED = 1994
ALL = []          # every static object of the town
WATER = []        # Water_* meshes kept separate
R = random.Random(SEED)

# ------------------------------------------------------------------ materials
B.reset(SEED)

matte = B.vmat("Matte", 0.86)
rough = B.vmat("Rough", 0.95)
stone = B.vmat("Stone", 0.90)
metal = B.vmat("Metal", 0.45, 0.45)
glass_dark = B.vmat("GlassDark", 0.22, 0.25)
water = B.mat("Water", "#38635c", rough=0.14, metal=0.2, alpha=1.0)
signs = B.mat("Signs", texture=os.path.join(B.ASSETS, "signs_atlas.png"), rough=0.75)
win_warm = B.mat("WinWarm", "#e2b276", rough=0.5, emission="#ffb765", emis_strength=1.5)
win_pale = B.mat("WinPale", "#d9d3b8", rough=0.5, emission="#ffe3b5", emis_strength=1.1)
shop_glow = B.mat("ShopGlow", "#e7c48c", rough=0.6, emission="#ffc884", emis_strength=1.15)
bulb = B.mat("Bulb", "#ffe2ae", rough=0.3, emission="#ffd9a0", emis_strength=2.4)
lantern_m = B.mat("Lantern", "#b5352b", rough=0.55, emission="#ff5f3a", emis_strength=1.5)
neon_tube = B.mat("NeonTube", "#d8e6da", rough=0.4, emission="#e6f4ea", emis_strength=2.0)
red_cloth = B.vmat("RedCloth", 0.92)

# ------------------------------------------------------------------ palette
C = {
    "wall_a": "#d9cfba", "wall_b": "#cdc2a8", "wall_c": "#c0b49a",
    "wall_d": "#b6b0a2", "wall_e": "#a9a79c", "wall_f": "#b9896f",
    "wall_g": "#9b5a46", "wall_h": "#b9c1b4", "wall_i": "#c8b58f",
    "band": "#9b8d7a", "band2": "#7e7466", "dark": "#3b3230",
    "trim": "#e0d5bf", "wood": "#6a4a31", "wood2": "#4e3724",
    "green": "#4f6a44", "olive": "#6b7647", "leaf": "#4f6642",
    "asphalt": "#6d6a62", "walk": "#a09987", "curb": "#b3ab9b",
    "stone": "#8c8575", "stone2": "#9d9585",
    "glass": "#3d5558", "glass2": "#5d7476",
    "red": "#a83a2d", "cream": "#d8c9a8", "blue": "#3f5a6a",
}


# ------------------------------------------------------------------ utilities
def add(objs):
    if objs is None:
        return
    if isinstance(objs, (list, tuple)):
        for o in objs:
            add(o)
    else:
        ALL.append(objs)


def vc(hexcol, amt=0.035):
    return B.vary(B.srgb(hexcol), amt)


def boxp(P, name, size, loc, color, mx=None, bevel=0.0, rot=(0, 0, 0)):
    P.append(B.box(name, size, loc, rot, color=color, material=mx or matte, bevel=bevel))


def cylp(P, name, r, depth, loc, color, mx=None, rot=(0, 0, 0), seg=12,
         r2=None, bevel=0.0, smooth=True):
    P.append(B.cylinder(name, r, depth, loc, rot, segments=seg, color=color,
                        material=mx or matte, radius2=r2, bevel=bevel, smooth=smooth))


def beamp(P, name, p1, p2, width=0.08, height=0.08, color="#777060", mx=None):
    o = B.beam(name, p1, p2, width, height, color=color, material=mx or matte)
    if o:
        P.append(o)


def quadp(P, name, corners, color, mx=None):
    P.append(B.quad(name, corners, color, mx or matte))


def sph(P, name, r, loc, color, scale=(1, 1, 1), mx=None, seg=10, rings=6):
    P.append(B.sphere(name, r, loc, scale=scale, color=color, material=mx or matte,
                      segments=seg, rings=rings))


def emit_strip(P, name, x, y, z, length, color="#ffeecc", axis="x", r=0.03):
    if axis == "x":
        cylp(P, name, r, length, (x, y, z), color, bulb, rot=(0, math.pi / 2, 0), seg=6)
    else:
        cylp(P, name, r, length, (x, y, z), color, bulb, rot=(math.pi / 2, 0, 0), seg=6)


# ------------------------------------------------------------------ street geometry
def road_x(y):
    return 4.6 * math.sin((y + 150.0) / 64.0) + 1.3 * math.sin((y + 30.0) / 23.0)


def road_dx(y):
    return (4.6 / 64.0) * math.cos((y + 150.0) / 64.0) + (1.3 / 23.0) * math.cos((y + 30.0) / 23.0)


def street_frame(y):
    t = road_dx(y)
    L = math.hypot(t, 1.0)
    return t / L, 1.0 / L


def frame_at(y, side, front, depth):
    """world centre + z-rotation for a building whose facade faces the street."""
    tx, ty = street_frame(y)
    nx, ny = ty, -tx
    off = front + depth * 0.5
    cx = road_x(y) + side * nx * off
    cy = y + side * ny * off
    rot = math.atan2(-side * ty, -side * tx)
    return cx, cy, rot


def offset_pts(off, y0=-152.0, y1=152.0, step=2.0):
    pts = []
    n = int((y1 - y0) / step)
    for i in range(n + 1):
        y = y0 + i * step
        tx, ty = street_frame(y)
        nx, ny = ty, -tx
        pts.append((road_x(y) + nx * off, y + ny * off))
    return pts


CANAL_Y = -14.0


def canal_cy(x):
    return CANAL_Y + 1.1 * math.sin(x / 38.0) + 0.5 * math.sin(x / 13.0 + 0.7)


def canal_slope(x):
    return 1.1 / 38.0 * math.cos(x / 38.0) + 0.5 / 13.0 * math.cos(x / 13.0 + 0.7)


def sstep(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def _hash(ix, iy, seed=0):
    v = math.sin(ix * 127.1 + iy * 311.7 + seed * 74.7) * 43758.5453
    return v - math.floor(v)


def vnoise(x, y, seed=0):
    ix, iy = math.floor(x), math.floor(y)
    fx, fy = sstep(0, 1, x - ix), sstep(0, 1, y - iy)
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
        amp *= 0.5
    return total / norm


HILLS = [
    (-118, 62, 42, 9.0), (-132, -62, 34, 6.4), (112, 104, 42, 8.0),
    (122, -96, 34, 5.5), (-30, 138, 46, 7.0), (48, -138, 50, 5.2),
]


def terrain_h(x, y):
    h = 0.10 * math.sin(x * 0.13) + 0.07 * math.sin(y * 0.17 + 1.2) + 0.05 * math.sin((x + y) * 0.09)
    for (hx, hy, r, hh) in HILLS:
        d = math.hypot((x - hx) / r, (y - hy) / (r * 0.8))
        h += hh * max(0.0, 1.0 - d * d) ** 2
    # keep the town floor calm
    dstreet = abs(x - road_x(y))
    flat = sstep(34, 16, dstreet)
    h *= (1.0 - flat * 0.75)
    # canal trench
    dc = abs(y - canal_cy(x))
    if dc < 8.2:
        h = min(h, -3.25)
    elif dc < 9.2:
        h = min(h, -3.25 + (dc - 8.2) / 1.0 * 3.3)
    # island rim stays level so it meets the slab nicely
    rim = min(160.0 - abs(x), 150.0 - abs(y))
    if rim < 10.0:
        h *= sstep(2.0, 10.0, rim)
    return h


def terrain_col(x, y, z):
    n = fbm(x * 0.06, y * 0.06, 3, 3)
    n2 = fbm(x * 0.31, y * 0.31, 8, 2)
    base = B.mix(B.srgb("#8c8a72"), B.srgb("#7b7f64"), n * 0.8)
    ds = abs(x - road_x(y))
    base = B.mix(base, B.srgb("#98917f"), sstep(22, 7, ds) * 0.5)
    # canal banks moss
    dc = abs(y - canal_cy(x))
    if dc < 12.0:
        base = B.mix(base, B.srgb("#6f7655"), sstep(12.0, 8.6, dc) * 0.65)
    # patchwork of fields outside the built blocks
    for (fx, fy, frx, fry, fcol) in (
            (-96, -46, 15, 10, "#94944f"), (80, -62, 13, 10, "#8f944f"),
            (-88, 96, 14, 9, "#9a945c"), (52, 128, 13, 8, "#7d8a4d"),
            (-70, -18, 12, 8, "#9a935a"), (58, 22, 16, 10, "#878f58"),
            (-24, 120, 12, 9, "#8d8a55"), (102, 70, 12, 10, "#8f8a5a")):
        d = ((x - fx) / frx) ** 2 + ((y - fy) / fry) ** 2
        if d < 1.4:
            base = B.mix(base, B.srgb(fcol), sstep(1.4, 0.5, d) * 0.55)
    # hills olive
    h = z
    if h > 1.5:
        base = B.mix(base, B.srgb("#727a52"), min(1.0, (h - 1.5) / 5.0) * 0.8)
    base = tuple(max(0.0, min(1.0, c * (0.9 + 0.22 * n2))) for c in base)
    return base


# ------------------------------------------------------------------ simple parts
def pavement(P):
    pts = offset_pts(0.0)
    P.append(B.road_ribbon("Road", pts, 9.0, C["asphalt"], rough, z=0.03, crown=0.05,
                           segments_width=6))
    for off in (-4.15, 4.15):
        P.append(B.road_ribbon("Gutter", offset_pts(off), 0.7, "#6d6a60", rough,
                               z=0.045, crown=0.0, segments_width=2))
    for side in (-1, 1):
        P.append(B.road_ribbon("Walk", offset_pts(side * 5.82), 2.5, C["walk"], rough,
                               z=0.145, crown=0.0, segments_width=2))
        curbside(P, side)
        quarters(P, side)
    yy = -144.0
    while yy < 146:
        if abs(yy - CANAL_Y) > 13:
            tx, ty = street_frame(yy)
            ang = math.atan2(ty, tx)
            boxp(P, "dash", (0.13, 2.4, 0.012), (road_x(yy), yy, 0.088),
                 "#c9c1a9", rough, rot=(0, 0, ang))
        yy += 6.4
    for yc in (-57.0, 24.0, 101.0):
        tx, ty = street_frame(yc)
        ang = math.atan2(ty, tx)
        for k in range(5):
            yy = yc + (k - 2) * 0.92
            xx = road_x(yy)
            boxp(P, "zebra", (8.5, 0.44, 0.012), (xx, yy, 0.09), vc("#c8c0a8", 0.05),
                 rough, rot=(0, 0, ang))
    for (mx, my) in ((road_x(12) + 1.6, 12), (road_x(-72) - 1.2, -72), (road_x(76) + 2.0, 76),
                     (road_x(-36) + 0.5, -36)):
        cylp(P, "manhole", 0.36, 0.045, (mx, my, 0.085), "#4a4844", metal, seg=16)
        cylp(P, "manring", 0.37, 0.018, (mx, my, 0.102), "#6f6a5e", metal, seg=16)
        boxp(P, "manbar", (0.5, 0.05, 0.012), (mx, my, 0.11), "#6f6a5e", metal)
        boxp(P, "manbar", (0.05, 0.5, 0.012), (mx, my, 0.11), "#6f6a5e", metal)
    for yy in (-110, -80, -40, 30, 66, 120):
        for side in (-1, 1):
            tx, ty = street_frame(yy)
            nx, ny = ty, -tx
            xx = road_x(yy) + side * nx * 4.0
            cyy = yy + side * ny * 4.0
            boxp(P, "grate", (0.55, 0.34, 0.02), (xx, cyy, 0.078), "#3f3d38", metal,
                 rot=(0, 0, math.atan2(ty, tx)))
            for k in range(5):
                boxp(P, "grateslat", (0.5, 0.032, 0.012),
                     (xx + (k - 2) * 0.09 * nx, cyy + (k - 2) * 0.09 * ny, 0.09),
                     "#6d675b", metal, rot=(0, 0, math.atan2(ty, tx)))


def curbside(P, side):
    samples = []
    yy = -152.0
    while yy <= 152.0:
        tx, ty = street_frame(yy)
        nx, ny = ty, -tx
        ox = road_x(yy) + nx * side * 4.58
        oy = yy + ny * side * 4.58
        samples.append((ox, oy, nx, ny))
        yy += 3.15
    verts, faces, fc = [], [], []
    for (ox, oy, nx, ny) in samples:
        for (o, zz) in ((-0.14, 0.03), (-0.14, 0.20), (0.16, 0.20)):
            verts.append((ox + nx * o, oy + ny * o, zz))
    for i in range(len(samples) - 1):
        a = i * 3
        b = (i + 1) * 3
        if side < 0:
            faces.append((a, b, b + 1, a + 1))
        else:
            faces.append((a, a + 1, b + 1, b))
        fc.append(vc("#b4ac9b", 0.04))
        faces.append((a + 1, b + 1, b + 2, a + 2))
        fc.append(vc("#9e9684", 0.04))
    P.append(B._finish("curb", verts, faces, None, rough, smooth=False, face_colors=fc))


def quarters(P, side):
    for i in range(60):
        yy = -146 + i * 4.9
        if abs(yy - CANAL_Y) < 11.5:
            continue
        tx, ty = street_frame(yy)
        nx, ny = ty, -tx
        cx = road_x(yy) + side * nx * 5.8
        cy = yy + side * ny * 5.8
        dx, dy = nx * 1.2, ny * 1.2
        tx2, ty2 = tx * 0.03, ty * 0.03
        corners = [(cx - dx - tx2, cy - dy - ty2, 0.152), (cx + dx - tx2, cy + dy - ty2, 0.152),
                   (cx + dx + tx2, cy + dy + ty2, 0.152), (cx - dx + tx2, cy - dy + ty2, 0.152)]
        P.append(B.quad("wjoint", corners, "#87806f", rough))


# ------------------------------------------------------------------ canal
def canal_water(P):
    xs = list(range(-138, 143, 2))
    verts, faces, fc = [], [], []
    for x in xs:
        cy = canal_cy(x)
        sl = canal_slope(x)
        L = math.hypot(1.0, sl)
        nx, ny = -sl / L, 1.0 / L
        for o in (-7.45, 7.45):
            verts.append((x + nx * o, cy + ny * o, -2.15))
    for i in range(len(xs) - 1):
        a = i * 2
        b = a + 2
        faces.append((a, b, b + 1, a + 1))
        fc.append(vc("#3a625a", 0.03))
    P.append(B._finish("Water_Canal", verts, faces, None, water, smooth=False,
                       face_colors=fc))


def canal_walk(P):
    for side in (-1, 1):
        pts = []
        for x in range(-136, 140, 4):
            cy = canal_cy(x)
            sl = canal_slope(x)
            L = math.hypot(1.0, sl)
            nx, ny = -sl / L, 1.0 / L
            pts.append((x + nx * side * 10.8, cy + ny * side * 10.8, 0.135))
        verts, faces, fc = [], [], []
        for (cx, cy, cz) in pts:
            sl = canal_slope(cx)
            L = math.hypot(1.0, sl)
            nx, ny = -sl / L, 1.0 / L
            for o in (-2.6, 2.6):
                verts.append((cx + nx * o, cy + ny * o, cz))
        for i in range(len(pts) - 1):
            a = i * 2
            b = a + 2
            faces.append((a, a + 1, b + 1, b))
            fc.append(vc("#98917f", 0.03))
        P.append(B._finish("canalwalk", verts, faces, None, rough, smooth=False,
                           face_colors=fc))


def canal_walls(P):
    zrows = [-3.30, -2.28, -1.42, -0.58, 0.10]
    band_cols = ["#4f5a46", "#6d6a58", "#857e6c", "#948b78"]
    for side in (-1, 1):
        xs = list(range(-138, 142, 3))
        verts, faces, fc = [], [], []
        for x in xs:
            cy = canal_cy(x)
            sl = canal_slope(x)
            L = math.hypot(1.0, sl)
            nx, ny = -sl / L, 1.0 / L
            for zz in zrows:
                verts.append((x + nx * side * 7.02, cy + ny * side * 7.02, zz))
        nb = len(zrows) - 1
        for i in range(len(xs) - 1):
            for r in range(nb):
                a = i * len(zrows) + r
                b = (i + 1) * len(zrows) + r
                if side > 0:
                    faces.append((a, b, b + 1, a + 1))
                else:
                    faces.append((a, a + 1, b + 1, b))
                fc.append(vc(band_cols[r], 0.055))
        P.append(B._finish("quayface", verts, faces, None, stone, smooth=False,
                           face_colors=fc))
        verts, faces, fc = [], [], []
        for x in xs:
            cy = canal_cy(x)
            sl = canal_slope(x)
            L = math.hypot(1.0, sl)
            nx, ny = -sl / L, 1.0 / L
            for (o, zz) in ((side * 6.88, 0.23), (side * 8.18, 0.23),
                            (side * 6.88, 0.11)):
                verts.append((x + nx * o, cy + ny * o, zz))
        for i in range(len(xs) - 1):
            a = i * 3
            b = (i + 1) * 3
            faces.append((a, a + 1, b + 1, b))
            fc.append(vc("#a49b87", 0.03))
            faces.append((a, a + 2, b + 2, b))
            fc.append(vc("#8d8573", 0.04))
        P.append(B._finish("quaycap", verts, faces, None, stone, smooth=False,
                           face_colors=fc))
        for xi in range(-132, 140, 12):
            cy = canal_cy(xi)
            sl = canal_slope(xi)
            L = math.hypot(1.0, sl)
            nx, ny = -sl / L, 1.0 / L
            boxp(P, "quayjoint", (0.05, 0.02, 2.5),
                 (xi + nx * side * 7.0, cy + ny * side * 7.0, -1.6), "#6c6658", stone,
                 rot=(0, 0, math.atan2(sl, 1.0)))
    for x in (-64, -50, -42, -34, -18, 16, 28, 38, 52, 66):
        for side in (-1, 1):
            cy = canal_cy(x)
            sl = canal_slope(x)
            L = math.hypot(1.0, sl)
            nx, ny = -sl / L, 1.0 / L
            off = side * 8.0
            bx, by = x + nx * off, cy + ny * off
            cylp(P, "bollard", 0.13, 0.52, (bx, by, 0.42), "#585346", stone,
                 seg=10, r2=0.11)
            cylp(P, "bollardcap", 0.16, 0.08, (bx, by, 0.70), "#6c6657", stone, seg=10)
    for (sx, sside, flip) in ((-7.0, 1, 1), (13.0, -1, -1)):
        cy = canal_cy(sx)
        off = 7.25 * sside
        for k in range(6):
            boxp(P, "canalstep", (2.0, 0.55, 0.22),
                 (sx, cy + off + flip * (0.25 + k * 0.5), 0.16 - k * 0.30),
                 vc(C["stone"], 0.05), stone, bevel=0.015)
        for zz in (0.55, 0.3):
            cylp(P, "steprail", 0.035, 1.3, (sx - 0.9, cy + off + flip * 1.7, zz),
                 "#5b5548", metal, rot=(math.pi / 2, 0, 0), seg=6)


def arch_z(y, yc, span, crown, spring):
    h = max(0.001, crown - spring)
    rad = (span * span / (8.0 * h)) + h * 0.5
    zc = crown - rad
    dy = max(-span * 0.499, min(span * 0.499, y - yc))
    return zc + math.sqrt(max(0.0, rad * rad - dy * dy))


def arch_face(P, x, yc, span, y0, y1, z_base, z_top, crown, spring, thick,
              col="#8b8474", ring_col="#a29884"):
    """stone bridge face in the YZ plane at x, with a segmental arch opening."""
    # piers
    boxp(P, "pierL", (thick, yc - span / 2 - y0, z_top - z_base),
         (x, (y0 + yc - span / 2) / 2, (z_base + z_top) / 2), col, stone, bevel=0.01)
    boxp(P, "pierR", (thick, y1 - (yc + span / 2), z_top - z_base),
         (x, (yc + span / 2 + y1) / 2, (z_base + z_top) / 2), col, stone, bevel=0.01)
    # comb above the arch
    n = 26
    for i in range(n):
        a = yc - span / 2 + span * i / n
        b = yc - span / 2 + span * (i + 1) / n
        zz = max(arch_z(a, yc, span, crown, spring), arch_z(b, yc, span, crown, spring))
        boxp(P, "spandrel", (thick, (b - a) + 0.015, max(0.05, z_top - zz)),
             (x, (a + b) / 2, (zz + z_top) * 0.5), vc(col, 0.04), stone)
    # voussoir ring on both faces
    for fx in (x + thick * 0.5 + 0.02, x - thick * 0.5 - 0.02):
        for i in range(18):
            y = yc - span / 2 + span * (i + 0.5) / 18
            zz = arch_z(y, yc, span, crown, spring)
            dz = arch_z(y + 0.12, yc, span, crown, spring) - zz
            ang = math.atan2(dz, 0.12)
            boxp(P, "ring", (0.09, span / 18.0 * 1.05, 0.34), (fx, y, zz),
                 vc(ring_col, 0.05), stone, rot=(ang, 0, 0))
    # horizontal coursing above the arch (only where the face is solid)
    for k in range(3):
        zz = z_top - 0.28 - k * 0.46
        if crown + 0.12 < zz < z_top - 0.06:
            boxp(P, "facecourse", (thick + 0.02, span * 0.94, 0.032), (x, yc, zz),
                 "#736c5e", stone)


def street_bridge(P):
    x0 = road_x(CANAL_Y)
    yc = canal_cy(x0)
    z_deck = 0.02
    # arch faces
    for side in (-1, 1):
        arch_face(P, x0 + side * 7.15, yc, 13.4, yc - 8.2, yc + 8.2, -3.3, -0.06,
                  -0.62, -3.0, 0.72)
    # stone parapets, both sidewalks
    for side in (-1, 1):
        px = x0 + side * 6.95
        boxp(P, "brplinth", (0.46, 16.8, 0.26), (px, yc, 0.28), "#8e8777", stone, bevel=0.01)
        boxp(P, "brpanel", (0.34, 16.6, 0.62), (px, yc, 0.72), vc("#99917f", 0.03), stone)
        boxp(P, "brcap", (0.55, 16.9, 0.16), (px, yc, 1.10), "#ada491", stone, bevel=0.02)
        for k in range(5):
            yy = yc - 6.8 + k * 3.4
            boxp(P, "brpost", (0.58, 0.58, 1.34), (px, yy, 0.70), "#a59c89", stone,
                 bevel=0.02)
            boxp(P, "brpostcap", (0.7, 0.7, 0.14), (px, yy, 1.42), "#b3aa96", stone,
                 bevel=0.02)
            sph(P, "brball", 0.14, (px, yy, 1.55), "#b3aa96", mx=stone, seg=7, rings=4)
        for k in range(4):
            yy = yc - 5.1 + k * 3.4
            boxp(P, "brpanelrecess", (0.02, 2.0, 0.3), (px - side * 0.17, yy, 0.76),
                 "#847c6c", stone)
    # deck underside band
    boxp(P, "brdeckband", (14.6, 17.2, 0.2), (x0, yc, -0.16), "#7c7566", stone)


def footbridge(P):
    bx = -30.0
    yc = canal_cy(bx)
    width = 3.2
    y0, y1 = yc - 9.0, yc + 9.0

    def deck_z(yy):
        t = max(0.0, min(1.0, (yy - y0) / (y1 - y0)))
        return 0.12 + 1.9 * (math.sin(math.pi * t) ** 0.9)

    n = 22
    seg = (y1 - y0) / n
    for i in range(n):
        ya = y0 + i * seg
        yb = ya + seg
        ym = (ya + yb) / 2
        top = max(deck_z(ya), deck_z(yb))
        inner = abs(ym - yc) < 7.3
        bot = top - 0.3 if inner else 0.1
        boxp(P, "fb_deck", (width, seg + 0.02, top - bot), (bx, ym, (top + bot) / 2),
             vc("#968f7e", 0.035), stone, bevel=0.012)
        # solid stone parapets following the stepped deck
        for sx in (-1, 1):
            px = bx + sx * (width / 2 - 0.1)
            boxp(P, "fb_par", (0.2, seg + 0.03, 0.8), (px, ym, top + 0.42),
                 vc("#9d9583", 0.03), stone)
            boxp(P, "fb_cop", (0.3, seg + 0.05, 0.1), (px, ym, top + 0.85),
                 "#b0a58e", stone)
            if i % 3 == 1:
                boxp(P, "fb_panel", (0.02, seg * 0.55, 0.34), (px - sx * 0.11, ym,
                     top + 0.43), "#827a69", stone)
    # arch faces below the central span
    for sx in (-1, 1):
        arch_face(P, bx + sx * (width / 2 - 0.02), yc, 9.4, yc - 7.3, yc + 7.3,
                  -3.3, 1.74, -1.05, -2.9, 0.24, col="#8a8372", ring_col="#a29884")
    # drum stones and ball caps at the four ends
    for sx in (-1, 1):
        for sy in (-1, 1):
            yy = yc + sy * (9.0 + 0.1)
            top = 0.12
            boxp(P, "fb_drum", (0.44, 0.44, 1.1), (bx + sx * 1.49, yy, top + 0.55),
                 "#a09886", stone, bevel=0.02)
            sph(P, "fb_ball", 0.16, (bx + sx * 1.49, yy, top + 1.16), "#aba28e",
                mx=stone, seg=7, rings=4)
    # approach paving
    for sy in (-1, 1):
        boxp(P, "fb_approach", (3.5, 2.2, 0.1), (bx, yc + sy * 9.8, 0.05),
             "#8f8878", stone)


def headwall(P, x, flip):
    yc = canal_cy(x)
    boxp(P, "headwall", (2.2, 24.0, 4.1), (x, yc, -0.9), vc("#847d6d", 0.03), stone,
         bevel=0.02)
    boxp(P, "headcap", (2.7, 24.4, 0.18), (x, yc, 1.16), "#a49b87", stone, bevel=0.02)
    # culvert mouth
    boxp(P, "culvert", (0.4, 8.0, 2.0), (x - flip * 1.15, yc, -2.2), "#2c3431", matte)
    for k in range(3):
        boxp(P, "culvertbar", (0.08, 0.12, 1.9), (x - flip * 1.32, yc - 2.4 + k * 2.4, -2.2),
             "#4b4a41", metal)
    # rubble / bank shrubs
    for k in range(6):
        yy = yc - 10 + k * 4.0
        sph(P, "bankrock", R.uniform(0.35, 0.7), (x - flip * 2.4, yy, 0.2),
            vc("#7e7867", 0.05), scale=(1.2, 1.0, 0.55), mx=stone, seg=7, rings=5)


# ------------------------------------------------------------------ building bits
def frame_ring(P, cx, cz, w, h, fy, t=0.075, dep=0.1, color="#b9b7ac",
               name="fr", mat=None):
    x0, x1 = cx - w / 2, cx + w / 2
    z0, z1 = cz - h / 2, cz + h / 2
    ix0, ix1 = x0 + t, x1 - t
    iz0, iz1 = z0 + t, z1 - t
    verts = [(x0, fy, z0), (x1, fy, z0), (x1, fy, z1), (x0, fy, z1),
             (ix0, fy, iz0), (ix1, fy, iz0), (ix1, fy, iz1), (ix0, fy, iz1),
             (ix0, fy + dep, iz0), (ix1, fy + dep, iz0), (ix1, fy + dep, iz1),
             (ix0, fy + dep, iz1)]
    faces = [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7),
             (4, 5, 9, 8), (5, 6, 10, 9), (6, 7, 11, 10), (7, 4, 8, 11)]
    fc = [vc(color, 0.02) for _ in range(8)]
    P.append(B._finish(name, verts, faces, None, mat or metal, smooth=False,
                       face_colors=fc))


def win(P, cx, cz, w, h, fy, lit=0, bars=False, blind=None, fcol="#b9b7ac",
        name="win", awning=None):
    """upright street window; the frame is a single ring mesh (cheap + deep)."""
    t = 0.072
    frame_ring(P, cx, cz, w, h, fy - 0.055, t=t, dep=0.115, color=fcol,
               name=name + "_fr")
    gm = win_warm if lit == 1 else (win_pale if lit == 2 else glass_dark)
    gc = "#ffffff" if lit else C["glass"]
    gw = w - 2 * t - 0.025
    gh = h - 2 * t - 0.025
    quadp(P, name + "_g", [(cx - gw / 2, fy - 0.015, cz - gh / 2),
                           (cx + gw / 2, fy - 0.015, cz - gh / 2),
                           (cx + gw / 2, fy - 0.015, cz + gh / 2),
                           (cx - gw / 2, fy - 0.015, cz + gh / 2)], gc, gm)
    if not lit and R.random() < 0.45:
        quadp(P, name + "_refl", [(cx - gw * 0.34, fy - 0.02, cz - gh * 0.44),
                                  (cx - gw * 0.18, fy - 0.02, cz - gh * 0.44),
                                  (cx - gw * 0.18, fy - 0.02, cz + gh * 0.44),
                                  (cx - gw * 0.34, fy - 0.02, cz + gh * 0.44)],
              "#6a8384", glass_dark)
    if blind:
        quadp(P, name + "_blind", [(cx - gw / 2, fy - 0.03, cz + gh / 2 - gh * 0.26),
                                   (cx + gw / 2, fy - 0.03, cz + gh / 2 - gh * 0.26),
                                   (cx + gw / 2, fy - 0.03, cz + gh / 2),
                                   (cx - gw / 2, fy - 0.03, cz + gh / 2)],
              blind, matte)
    # centre mullions
    boxp(P, name + "_m", (0.04, 0.035, gh), (cx, fy - 0.045, cz), fcol, metal)
    boxp(P, name + "_mh", (gw, 0.035, 0.032), (cx, fy - 0.045, cz), fcol, metal)
    boxp(P, name + "_sill", (w + 0.24, 0.24, 0.085), (cx, fy - 0.08, cz - h / 2 - 0.055),
         "#c0b8a6", stone, bevel=0.01)
    if bars:
        n = max(3, int(w / 0.26))
        for i in range(n):
            bx = cx - gw * 0.44 + gw * 0.88 * i / max(1, n - 1)
            boxp(P, name + "_bar", (0.022, 0.022, gh * 0.96), (bx, fy - 0.14, cz),
                 "#5b574e", metal)
        for dz in (-h * 0.30, h * 0.30):
            boxp(P, name + "_barb", (gw * 0.94, 0.022, 0.022), (cx, fy - 0.14, cz + dz),
                 "#5b574e", metal)


def side_win(P, x, cy, cz, w, h, side, lit=0, fcol="#b2afa3", name="sw"):
    s = 1 if side > 0 else -1
    t = 0.07
    y0, y1 = cy - w / 2, cy + w / 2
    z0, z1 = cz - h / 2, cz + h / 2
    iy0, iy1 = y0 + t, y1 - t
    iz0, iz1 = z0 + t, z1 - t
    xf = x + s * 0.065
    xb = x + s * 0.005
    verts = []
    for xx in (xf, xb):
        verts += [(xx, y0, z0), (xx, y1, z0), (xx, y1, z1), (xx, y0, z1),
                  (xx, iy0, iz0), (xx, iy1, iz0), (xx, iy1, iz1), (xx, iy0, iz1)]
    faces = []
    for k in (0, 4):
        faces += [(k + 0, k + 1, k + 5, k + 4), (k + 1, k + 2, k + 6, k + 5),
                  (k + 2, k + 3, k + 7, k + 6), (k + 3, k + 0, k + 4, k + 7),
                  (k + 4, k + 5, k + 9, k + 8), (k + 5, k + 6, k + 10, k + 9),
                  (k + 6, k + 7, k + 11, k + 10), (k + 7, k + 4, k + 8, k + 11)]
    fc = [vc(fcol, 0.02) for _ in faces]
    P.append(B._finish(name + "_fr", verts, faces, None, metal, smooth=False,
                       face_colors=fc))
    gm = win_warm if lit == 1 else glass_dark
    quadp(P, name + "_g", [(x + s * 0.02, iy0, iz0), (x + s * 0.02, iy1, iz0),
                           (x + s * 0.02, iy1, iz1), (x + s * 0.02, iy0, iz1)],
          C["glass"], gm)
    boxp(P, name + "_sill", (0.22, w + 0.22, 0.075), (x + s * 0.08, cy, z0 - 0.05),
         "#b8b09e", stone)


def back_win(P, cy, cz, w, h, fy, name="bw", lit=0):
    """cheap service-side window seen from above."""
    boxp(P, name + "_r", (w + 0.1, 0.1, h + 0.1), (cy, fy - 0.02, cz), "#2f3739", matte)
    gm = win_warm if lit else glass_dark
    quadp(P, name + "_g", [(cy - w / 2, fy + 0.04, cz - h / 2),
                           (cy + w / 2, fy + 0.04, cz - h / 2),
                           (cy + w / 2, fy + 0.04, cz + h / 2),
                           (cy - w / 2, fy + 0.04, cz + h / 2)], C["glass"], gm)
    boxp(P, name + "_f", (w + 0.16, 0.06, 0.07), (cy, fy - 0.02, cz + h / 2),
         "#b0a893", metal)
    boxp(P, name + "_sill", (w + 0.2, 0.2, 0.07), (cy, fy - 0.03, cz - h / 2 - 0.05),
         "#a89f8a", stone)


def ac_unit(P, cx, cz, fy, side=1, name="ac"):
    boxp(P, name, (0.76, 0.3, 0.52), (cx, fy - 0.21, cz), "#cfc8b4", matte, bevel=0.02)
    boxp(P, name + "_gril", (0.6, 0.02, 0.4), (cx - 0.06, fy - 0.37, cz), "#8e8b7e", metal)
    for k in range(4):
        boxp(P, name + "_slat", (0.6, 0.02, 0.025), (cx - 0.06, fy - 0.385, cz - 0.16 + k * 0.1),
             "#767366", metal)
    cylp(P, name + "_fan", 0.16, 0.03, (cx + 0.2, fy - 0.38, cz), "#9a988b", metal,
         rot=(math.pi / 2, 0, 0), seg=12)
    cylp(P, name + "_hub", 0.035, 0.05, (cx + 0.2, fy - 0.40, cz), "#5f5c52", metal,
         rot=(math.pi / 2, 0, 0), seg=8)
    for k in range(4):
        a = math.pi * k / 2 + 0.5
        beamp(P, name + "_spoke",
              (cx + 0.2, fy - 0.405, cz),
              (cx + 0.2 + 0.13 * math.cos(a), fy - 0.405, cz + 0.13 * math.sin(a)),
              0.018, 0.018, "#6c695e", metal)
    # brackets and drip pipe
    for sx in (-0.3, 0.3):
        beamp(P, name + "_br", (cx + sx, fy - 0.02, cz - 0.3), (cx + sx, fy - 0.42, cz - 0.3),
              0.035, 0.035, "#5c584d", metal)
    boxp(P, name + "_drip", (0.04, 0.04, 0.5), (cx + 0.28, fy - 0.3, cz - 0.55), "#7d7a6c", metal)


def balcony(P, cx, cz, fy, w=2.7, dep=1.05, laundry=False, rail="#7c7a6e", name="bal"):
    # slab
    boxp(P, name + "_s", (w, dep, 0.14), (cx, fy - dep / 2, cz), "#b7b0a0", stone, bevel=0.015)
    for sx in (-1, 1):
        beamp(P, name + "_brk", (cx + sx * (w / 2 - 0.25), fy, cz - 0.55),
              (cx + sx * (w / 2 - 0.25), fy - dep + 0.1, cz - 0.06), 0.07, 0.1, "#8a8374")
    # rails
    boxp(P, name + "_r1", (w, 0.06, 0.07), (cx, fy - dep + 0.04, cz + 1.0), rail, metal)
    boxp(P, name + "_r2", (w, 0.05, 0.05), (cx, fy - dep + 0.04, cz + 0.28), rail, metal)
    n = max(6, int(w / 0.17))
    for i in range(n):
        bx = cx - w / 2 + 0.06 + (w - 0.12) * i / max(1, n - 1)
        boxp(P, name + "_bar", (0.028, 0.028, 0.78), (bx, fy - dep + 0.04, cz + 0.62), rail, metal)
    for sx in (-1, 1):
        boxp(P, name + "_side", (0.05, dep, 0.05),
             (cx + sx * (w / 2 - 0.04), fy - dep / 2, cz + 1.0), rail, metal)
        for k in range(4):
            boxp(P, name + "_sbar", (0.026, 0.026, 0.78),
                 (cx + sx * (w / 2 - 0.04), fy - 0.2 - k * (dep - 0.4) / 3, cz + 0.62),
                 rail, metal)
    # laundry pole
    if laundry:
        boxp(P, name + "_pole", (w * 0.86, 0.035, 0.035),
             (cx, fy - dep + 0.16, cz + 1.55), "#8a7350", matte)
        for sx in (-1, 1):
            beamp(P, name + "_polebr", (cx + sx * w * 0.4, fy - dep + 0.2, cz + 1.0),
                  (cx + sx * w * 0.4, fy - dep + 0.2, cz + 1.55), 0.025, 0.025, "#6f5c3f")
        cols = ["#c7bda2", "#a85244", "#6f8490", "#d4c8ab", "#8a9a72"]
        for k in range(3):
            cw = w * 0.2
            bx = cx - w * 0.3 + k * w * 0.28
            quadp(P, name + "_cloth",
                  [(bx, fy - dep + 0.17, cz + 1.54), (bx + cw, fy - dep + 0.17, cz + 1.54),
                   (bx + cw + 0.03, fy - dep + 0.19, cz + 0.55),
                   (bx - 0.01, fy - dep + 0.19, cz + 0.62)],
                  cols[k % len(cols)], rough)
    # potted plant
    if R.random() < 0.45:
        px = cx + w * 0.36
        cylp(P, name + "_pot", 0.14, 0.24, (px, fy - dep + 0.2, cz + 0.2), "#9b5f45",
             matte, seg=8, r2=0.17)
        sph(P, name + "_plant", 0.2, (px, fy - dep + 0.2, cz + 0.46), "#4d6a42",
            scale=(1, 1, 0.8), mx=matte, seg=7, rings=5)


def shutter(P, cx, bw, fy, gh, name="sh", closed=True, color="#8d958f"):
    opw = bw - 0.18
    oh = gh - 0.88
    z0 = 0.50
    # side guides
    for sx in (-1, 1):
        boxp(P, name + "_guide", (0.09, 0.16, oh + 0.25),
             (cx + sx * (opw / 2 + 0.03), fy + 0.06, z0 + oh / 2), "#6c6a60", metal)
    # rolled housing
    boxp(P, name + "_box", (opw + 0.26, 0.34, 0.34), (cx, fy + 0.12, z0 + oh + 0.16),
         "#70746e", metal, bevel=0.02)
    cylp(P, name + "_roll", 0.15, opw + 0.1, (cx, fy + 0.12, z0 + oh + 0.16),
         "#7f857f", metal, rot=(0, math.pi / 2, 0), seg=10)
    if closed:
        n = 10
        sh_h = oh - 0.22
        boxp(P, name + "_panel", (opw, 0.05, sh_h), (cx, fy + 0.09, z0 + sh_h / 2),
             color, metal)
        for k in range(n):
            zz = z0 + 0.12 + sh_h * k / n
            boxp(P, name + "_slat", (opw - 0.03, 0.035, 0.055),
                 (cx, fy + 0.055, zz), vc("#777d77", 0.05), metal)
        boxp(P, name + "_handle", (0.22, 0.06, 0.05), (cx, fy + 0.02, z0 + 0.45),
             "#565349", metal)
        # a faded notice
        if R.random() < 0.5:
            boxp(P, name + "_note", (0.4, 0.012, 0.3), (cx + opw * 0.2, fy + 0.015, z0 + 1.4),
                 "#d2c7ab", matte)
    else:
        # half open: a short skirt + dark opening above
        boxp(P, name + "_panel", (opw, 0.05, 0.7), (cx, fy + 0.09, z0 + 0.35),
             color, metal)
        for k in range(5):
            boxp(P, name + "_slat", (opw - 0.03, 0.035, 0.055),
                 (cx, fy + 0.055, z0 + 0.12 + k * 0.15), vc("#777d77", 0.05), metal)
        boxp(P, name + "_dark", (opw, 0.05, oh - 0.9), (cx, fy + 0.1, z0 + 0.9 + (oh - 0.9) / 2),
             "#3a3a33", matte)


def shop_open(P, cx, bw, fy, gh, name="op", warm=0, shelves=True, counter=True):
    opw = bw - 0.2
    oh = gh - 0.88
    z0 = 0.46
    # interior shell
    dep = 2.0
    boxp(P, name + "_fl", (opw, dep, 0.05), (cx, fy + dep / 2, z0 - 0.04), "#7f796b", rough)
    boxp(P, name + "_back", (opw, 0.06, oh), (cx, fy + dep, z0 + oh / 2), "#8a7b63", matte)
    # shelf against the back
    if shelves:
        boxp(P, name + "_shelf", (opw - 0.25, 0.34, oh * 0.8),
             (cx, fy + dep - 0.22, z0 + oh * 0.38), "#6b4d34", matte)
        for k in range(2):
            zz = z0 + 0.65 + k * (oh - 1.2) / 1.8
            boxp(P, name + "_shb", (opw - 0.3, 0.36, 0.04), (cx, fy + dep - 0.22, zz),
                 "#8a6744", matte)
            ng = 4
            for g in range(ng):
                gx = cx - opw * 0.36 + (opw * 0.72) * g / max(1, ng - 1)
                gc = ["#a94b38", "#c8b06a", "#5b7d86", "#b7b092", "#7c8f5e"][(k * 3 + g) % 5]
                boxp(P, name + "_good", (0.15, 0.18, 0.24),
                     (gx, fy + dep - 0.38, zz + 0.14), gc, matte)
    if counter:
        boxp(P, name + "_ct", (opw - 0.35, 0.6, 0.9),
             (cx, fy + 0.95, z0 + 0.45), "#78604a", matte, bevel=0.02)
        boxp(P, name + "_ctop", (opw - 0.3, 0.7, 0.06),
             (cx, fy + 0.95, z0 + 0.93), "#a79b80", matte)
    # light
    boxp(P, name + "_cord", (0.02, 0.02, 0.55), (cx, fy + dep * 0.5, z0 + oh - 0.28),
         "#4b463c", metal)
    sph(P, name + "_bulb", 0.09, (cx, fy + dep * 0.5, z0 + oh - 0.62), "#ffdfa8",
        mx=bulb if warm else shop_glow, seg=8, rings=5)
    # threshold step
    boxp(P, name + "_step", (opw + 0.3, 0.44, 0.2), (cx, fy - 0.1, 0.2), "#a29a87",
         stone, bevel=0.01)


def shop_glass(P, cx, bw, fy, gh, name="gl", door=True, fcol="#b7b3a4"):
    opw = bw - 0.18
    oh = gh - 0.92
    z0 = 0.5
    # frame grid
    boxp(P, name + "_back", (opw + 0.1, 0.2, oh + 0.1), (cx, fy + 0.12, z0 + oh / 2),
         "#3b4243", matte)
    nm = 3 if opw > 2.0 else 2
    for k in range(1, nm):
        boxp(P, name + "_mull", (0.07, 0.12, oh), (cx - opw / 2 + opw * k / nm,
             fy + 0.01, z0 + oh / 2), fcol, metal)
    boxp(P, name + "_rail", (opw, 0.12, 0.07), (cx, fy + 0.01, z0 + oh * 0.52), fcol, metal)
    boxp(P, name + "_litel", (opw + 0.16, 0.12, 0.08), (cx, fy - 0.02, z0 + oh + 0.06),
         fcol, metal)
    boxp(P, name + "_sill", (opw + 0.2, 0.3, 0.12), (cx, fy - 0.05, z0 - 0.04),
         "#b0a792", stone, bevel=0.01)
    # glass panes
    for k in range(nm):
        gw = opw / nm - 0.08
        gx = cx - opw / 2 + opw * (k + 0.5) / nm
        boxp(P, name + "_g", (gw, 0.02, oh - 0.14), (gx, fy + 0.015, z0 + oh / 2),
             C["glass"], glass_dark)
        boxp(P, name + "_refl", (gw * 0.28, 0.012, oh * 0.8),
             (gx - gw * 0.2, fy - 0.005, z0 + oh / 2), "#78908f", glass_dark)
    if door:
        dx = cx + opw * 0.22
        boxp(P, name + "_door", (0.98, 0.1, oh - 0.2), (dx, fy - 0.02, z0 + (oh - 0.2) / 2),
             "#4b5b58", glass_dark)
        boxp(P, name + "_dframe", (1.08, 0.11, 0.07), (dx, fy - 0.03, z0 + oh - 0.16),
             fcol, metal)
        boxp(P, name + "_dhandle", (0.05, 0.06, 0.3), (dx - 0.34, fy - 0.09, z0 + 1.0),
             "#8c8a7c", metal)


def shop_door(P, cx, bw, fy, gh, name="dr", col="#513524"):
    dw = min(1.3, bw - 0.4)
    dh = min(2.3, gh - 1.1)
    z0 = 0.5
    boxp(P, name + "_frame", (dw + 0.3, 0.16, dh + 0.18), (cx, fy + 0.02, z0 + dh / 2),
         "#4c3b2b", matte)
    boxp(P, name + "_door", (dw, 0.09, dh - 0.06), (cx, fy - 0.06, z0 + dh / 2), col, matte)
    for sx in (-1, 1):
        boxp(P, name + "_panel", (dw * 0.32, 0.02, dh * 0.5),
             (cx + sx * dw * 0.2, fy - 0.11, z0 + dh * 0.4), "#3c2a1d", matte)
    boxp(P, name + "_knob", (0.06, 0.08, 0.06), (cx + dw * 0.3, fy - 0.12, z0 + 1.1),
         "#b7a06a", metal)
    # transom
    boxp(P, name + "_trans", (dw, 0.04, 0.34), (cx, fy - 0.04, z0 + dh + 0.24),
         C["glass"], glass_dark)


def shop_grille(P, cx, bw, fy, gh, name="gr"):
    opw = bw - 0.2
    oh = gh - 0.9
    z0 = 0.5
    boxp(P, name + "_dark", (opw, 0.1, oh), (cx, fy + 0.1, z0 + oh / 2), "#33352f", matte)
    n = max(6, int(opw / 0.18))
    for i in range(n):
        gx = cx - opw / 2 + 0.05 + (opw - 0.1) * i / max(1, n - 1)
        boxp(P, name + "_bar", (0.026, 0.03, oh), (gx, fy - 0.02, z0 + oh / 2), "#5b5a50", metal)
    for k in range(3):
        boxp(P, name + "_h", (opw, 0.03, 0.03), (cx, fy - 0.03, z0 + oh * (0.25 + k * 0.25)),
             "#5b5a50", metal)
    boxp(P, name + "_top", (opw + 0.2, 0.18, 0.2), (cx, fy + 0.02, z0 + oh + 0.08),
         "#6e6758", metal)


def blank_sign(P, fy, z, w, h, board="#5a3226", mark=("#c9a96a", "#e0d3b2")):
    boxp(P, "bsign_b", (w + 0.28, 0.14, h + 0.26), (0, fy - 0.19, z), board, matte)
    boxp(P, "bsign_f1", (w + 0.1, 0.05, 0.07), (0, fy - 0.27, z + h / 2 + 0.05),
         mark[0], matte)
    boxp(P, "bsign_f2", (w + 0.1, 0.05, 0.07), (0, fy - 0.27, z - h / 2 - 0.05),
         mark[0], matte)
    cylp(P, "bsign_disc", h * 0.30, 0.03, (-w * 0.33, fy - 0.29, z), mark[1], matte,
         rot=(math.pi / 2, 0, 0), seg=14)
    for k in range(2):
        boxp(P, "bsign_bar", (w * 0.34, 0.03, h * 0.1),
             (w * 0.1, fy - 0.29, z + (k - 0.5) * h * 0.26), mark[1], matte)


def street_sign(P, key, fy, z, w, h, board="#3c2a22", frame="#c7b58c", glow=True):
    boxp(P, "sign_b", (w + 0.3, 0.16, h + 0.28), (0, fy - 0.2, z), board, matte, bevel=0.01)
    P.append(B.sign_quad("sign_q", key, (0, fy - 0.29, z), 0.0, w, h, signs))
    for (dx, dz, sx, sz) in ((0, h / 2 + 0.09, w + 0.3, 0.08), (0, -h / 2 - 0.09, w + 0.3, 0.08),
                             (-w / 2 - 0.09, 0, 0.08, h + 0.2), (w / 2 + 0.09, 0, 0.08, h + 0.2)):
        boxp(P, "sign_frame", (sx, 0.2, sz), (dx, fy - 0.21, z + dz), frame, metal)
    for sx in (-1, 1):
        beamp(P, "sign_brk", (sx * (w / 2 - 0.3), fy - 0.02, z + h / 2 + 0.16),
              (sx * (w / 2 - 0.3), fy - 0.34, z + h / 2 + 0.16), 0.05, 0.06, "#5a564a")
    if glow:
        boxp(P, "sign_light", (w * 0.9, 0.08, 0.045), (0, fy - 0.32, z - h / 2 - 0.17),
             "#ffe7b8", neon_tube)


def awning(P, cx, bw, fy, z, depth=1.45, cols=("#a44434", "#d8cbb0"), name="awn",
           valance=0.22):
    n = 8
    ang = 0.19
    cw = (bw - 0.25) / n
    for k in range(n):
        boxp(P, name + "_stripe", (cw + 0.005, depth, 0.045),
             (cx - (bw - 0.25) / 2 + cw * (k + 0.5),
              fy - math.cos(ang) * depth * 0.5, z - math.sin(ang) * depth * 0.5),
             cols[k % 2], matte, rot=(ang, 0, 0))
    # valance
    for k in range(n):
        boxp(P, name + "_val", (cw + 0.005, 0.03, valance),
             (cx - (bw - 0.25) / 2 + cw * (k + 0.5), fy - math.cos(ang) * depth,
              z - math.sin(ang) * depth - valance / 2 + 0.02),
             cols[k % 2], matte)
    boxp(P, name + "_rail", (bw - 0.2, 0.05, 0.05),
         (cx, fy - math.cos(ang) * depth, z - math.sin(ang) * depth + 0.01),
         "#6b6658", metal)
    for sx in (-1, 1):
        beamp(P, name + "_arm", (cx + sx * (bw / 2 - 0.35), fy - 0.01, z - 0.62),
              (cx + sx * (bw / 2 - 0.35), fy - math.cos(ang) * depth + 0.05,
               z - math.sin(ang) * depth),
              0.045, 0.045, "#5b5749", metal)


def roof_tank(P, cx, cy, z, r=0.82, name="tank"):
    for sx in (-1, 1):
        for sy in (-1, 1):
            boxp(P, name + "_leg", (0.12, 0.12, 1.15),
                 (cx + sx * r * 0.62, cy + sy * r * 0.62, z + 0.57), "#7a7465", metal)
    boxp(P, name + "_plat", (r * 1.7, r * 1.7, 0.1), (cx, cy, z + 1.16), "#8d8474", metal)
    cylp(P, name + "_body", r, 1.25, (cx, cy, z + 1.82), "#cfc8b3", metal,
         seg=12, r2=r * 0.96)
    for zz in (z + 1.48, z + 2.28):
        cylp(P, name + "_band", r * 1.01, 0.035, (cx, cy, zz), "#8a8474", metal, seg=12)
    cylp(P, name + "_lid", r * 0.86, 0.3, (cx, cy, z + 2.5), "#b8b19d", metal,
         seg=12, r2=0.08)
    cylp(P, name + "_pipe", 0.06, z + 1.1, (cx + r * 0.55, cy, (z + 1.1) / 2 + 0.35),
         "#77715f", metal, seg=6)


def antenna(P, cx, cy, z, name="ant"):
    cylp(P, name + "_mast", 0.035, 3.2, (cx, cy, z + 1.6), "#5a564a", metal, seg=6)
    boxp(P, name + "_boom", (0.03, 0.03, 0.9), (cx, cy + 0.7, z + 2.6),
         "#5a564a", metal, rot=(math.pi / 2, 0, 0))
    for k in range(3):
        ln = 0.9 - k * 0.2
        boxp(P, name + "_el", (ln, 0.025, 0.025), (cx, cy + 0.4 + k * 0.32, z + 2.6),
             "#6b6658", metal)


def bulkhead(P, cx, cy, z, name="bulk", col="#c8c0ad"):
    boxp(P, name + "_b", (2.3, 2.1, 2.1), (cx, cy, z + 1.05), col, matte, bevel=0.02)
    boxp(P, name + "_roof", (2.6, 2.4, 0.12), (cx, cy, z + 2.16), "#8b8372", stone, bevel=0.01)
    boxp(P, name + "_door", (0.85, 0.06, 1.8), (cx, cy - 1.08, z + 0.95), "#5b4c3a", matte)
    boxp(P, name + "_vent", (0.3, 0.3, 0.7), (cx + 0.7, cy + 0.6, z + 2.3), "#6d6758", metal)


def rooftop_laundry(P, cx, cy, z, w=3.4, name="rl"):
    for sx in (-1, 1):
        boxp(P, name + "_post", (0.06, 0.06, 1.4), (cx + sx * w / 2, cy, z + 0.7),
             "#6d5b3e", matte)
    boxp(P, name + "_line", (w, 0.02, 0.02), (cx, cy, z + 1.35), "#4b463c", metal)
    cols = ["#c6bda3", "#a85244", "#6d8490", "#d9cdb1", "#8c9c75"]
    for k in range(4):
        bx = cx - w * 0.36 + k * w * 0.22
        quadp(P, name + "_cl", [(bx, cy, z + 1.34), (bx + w * 0.16, cy, z + 1.34),
                                (bx + w * 0.16 + 0.02, cy + 0.02, z + 0.55),
                                (bx, cy + 0.02, z + 0.62)], cols[k % 5], rough)


def parapet(P, w, d, z, h=0.82, col="#b3a88f"):
    for (bx, by, sx, sy) in ((0, -d / 2 + 0.12, w + 0.1, 0.24), (0, d / 2 - 0.12, w + 0.1, 0.24),
                             (-w / 2 + 0.12, 0, 0.24, d - 0.2), (w / 2 - 0.12, 0, 0.24, d - 0.2)):
        boxp(P, "parapet", (sx, sy, h), (bx, by, z + h / 2), col, matte)
        boxp(P, "paracop", (sx + 0.08, sy + 0.08, 0.09), (bx, by, z + h + 0.04), "#a99f8a", stone)
    # little pier blocks
    for sx in (-1, 1):
        for sy in (-1, 1):
            boxp(P, "parapier", (0.32, 0.32, h + 0.18), (sx * (w / 2 - 0.1), sy * (d / 2 - 0.1),
                 z + (h + 0.18) / 2), col, matte)


def tile_facade(P, w, z0, z1, fy, color_a="#d7d3c4", color_b="#c5c1b2"):
    cols = max(6, int(w / 0.75))
    rows = max(6, int((z1 - z0) / 0.55))
    verts, faces, fc = [], [], []
    gap = 0.012
    for iy in range(rows):
        for ix in range(cols):
            x0 = -w / 2 + w * ix / cols + gap
            x1 = -w / 2 + w * (ix + 1) / cols - gap
            zz0 = z0 + (z1 - z0) * iy / rows + gap
            zz1 = z0 + (z1 - z0) * (iy + 1) / rows - gap
            b = len(verts)
            verts += [(x0, fy - 0.012, zz0), (x1, fy - 0.012, zz0),
                      (x1, fy - 0.012, zz1), (x0, fy - 0.012, zz1)]
            faces.append((b, b + 1, b + 2, b + 3))
            c = B.mix(B.srgb(color_a), B.srgb(color_b), 0.5 if (ix + iy) % 2 else 0.0)
            fc.append(B.vary(c, 0.035))
    P.append(B._finish("tilefacade", verts, faces, None, matte, smooth=False, face_colors=fc))


def drainpipe(P, x, fy, z0, z1, name="dp"):
    cylp(P, name, 0.055, z1 - z0, (x, fy - 0.12, (z0 + z1) / 2), "#7c7666", metal, seg=8)
    for k in range(4):
        zz = z0 + (z1 - z0) * (0.15 + k * 0.22)
        boxp(P, name + "_br", (0.16, 0.05, 0.03), (x, fy - 0.04, zz), "#5f5b4d", metal)
    boxp(P, name + "_shoe", (0.14, 0.34, 0.14), (x, fy - 0.26, z0 + 0.12), "#6c6658", metal,
         rot=(0.6, 0, 0))


def window_laundry(P, cx, fy, z, w=2.1, name="wl"):
    boxp(P, name + "_pole", (w, 0.035, 0.035), (cx, fy - 0.52, z), "#8a7350", matte)
    for sx in (-1, 1):
        beamp(P, name + "_brk", (cx + sx * w * 0.42, fy - 0.02, z),
              (cx + sx * w * 0.42, fy - 0.55, z), 0.025, 0.025, "#6f5c3f")
    cols = ["#c7bda2", "#a85244", "#6f8490", "#d4c8ab"]
    for k in range(3):
        bx = cx - w * 0.34 + k * w * 0.3
        quadp(P, name + "_cl",
              [(bx, fy - 0.53, z), (bx + w * 0.2, fy - 0.53, z),
               (bx + w * 0.21, fy - 0.55, z - 0.72),
               (bx - 0.01, fy - 0.55, z - 0.62)],
              cols[k % 4], rough)


def roof_solar(P, cx, cy, z, rot=0.0, name="solar"):
    b = []
    ang = 0.58
    boxp(b, name + "_panel", (1.9, 1.5, 0.05), (0, 0, 0.55), "#5c5a50", metal,
         rot=(ang, 0, 0))
    for k in range(9):
        yy = -0.7 + k * 0.17
        zz = 0.42 + (yy + 0.7) * 0.64
        cylp(b, name + "_tube", 0.048, 1.92, (0, yy, zz), "#7d999a", glass_dark,
             rot=(0, math.pi / 2, 0), seg=8)
    cylp(b, name + "_tank", 0.28, 1.9, (0, 0.68, 1.28), "#c9c2ad", metal,
         rot=(0, math.pi / 2, 0), seg=12)
    for sx in (-1, 1):
        boxp(b, name + "_leg", (0.06, 0.06, 0.95), (sx * 0.8, 0.45, 0.48), "#6d6757", metal)
        boxp(b, name + "_leg", (0.06, 0.06, 0.45), (sx * 0.8, -0.55, 0.22), "#6d6757", metal)
    cylp(b, name + "_pipe", 0.035, 1.1, (0.7, 0.6, 0.62), "#8a8474", metal,
         rot=(0.2, 0, 0), seg=6)
    B.apply_xform(b, (cx, cy, z), rot)
    P.extend(b)


def shophouse(y, side, w, d, floors, wall, *, sign=None, sign_w=4.2, sign_h=1.3,
              board="#432b23", shop=("open", "shutter"), bays=None,
              awning_bays=(1,), awn_cols=("#9d4032", "#d7c9ad"),
              balconies=(), roof="flat", setback=0.0, ac=True, tank=None,
              antenna_roof=None, bulk=True, sides=True, style="plaster",
              laundry=False, lit_bias=0.3, extra=None, name="shop", gh=4.2, fh=3.15,
              shop_lit=True):
    P = []
    fy = -d / 2.0
    H = gh + (floors - 1) * fh
    n = bays or (3 if w >= 10.5 else 2)
    inner = w - 0.9
    bw = inner / n
    centers = [-w / 2 + 0.45 + bw * (i + 0.5) for i in range(n)]

    # base and body
    boxp(P, name + "_base", (w + 0.18, d + 0.18, 0.42), (0, 0, 0.21), "#98917f",
         stone, bevel=0.02)
    boxp(P, name + "_body", (w, d, H - gh), (0, 0, (gh + H) / 2), vc(wall, 0.02),
         matte, bevel=0.025)
    # stained base band (thin cladding panels, never a solid block)
    boxp(P, name + "_stainf", (w + 0.02, 0.02, 0.5), (0, fy - 0.012, 0.7), "#a69c86", matte)
    for sx in (-1, 1):
        boxp(P, name + "_stains", (0.02, d, 0.5), (sx * (w / 2 + 0.005), 0, 0.7),
             "#a69c86", matte)
    # ground floor structure: side walls, back wall, front piers, lintel
    boxp(P, name + "_back", (w, 0.42, gh - 0.4), (0, d / 2 - 0.21, (gh + 0.4) / 2),
         vc(wall, 0.02), matte)
    for sx in (-1, 1):
        boxp(P, name + "_sidew", (0.42, d, gh - 0.4), (sx * (w / 2 - 0.21), 0,
             (gh + 0.4) / 2), vc(wall, 0.02), matte)
    # end piers and dividers
    boxp(P, name + "_pier", (0.5, 0.5, gh - 0.4), (-w / 2 + 0.25, fy + 0.25, (gh + 0.4) / 2),
         vc(wall, 0.02), matte, bevel=0.01)
    boxp(P, name + "_pier", (0.5, 0.5, gh - 0.4), (w / 2 - 0.25, fy + 0.25, (gh + 0.4) / 2),
         vc(wall, 0.02), matte, bevel=0.01)
    for i in range(1, n):
        px = -w / 2 + 0.45 + bw * i
        boxp(P, name + "_pier", (0.3, 0.46, gh - 0.4), (px, fy + 0.23, (gh + 0.4) / 2),
             vc(wall, 0.02), matte, bevel=0.01)
    boxp(P, name + "_lintel", (w, 0.6, 0.5), (0, fy + 0.3, gh - 0.25), vc(wall, 0.02),
         matte)
    boxp(P, name + "_beamface", (w, 0.06, 0.42), (0, fy - 0.0, gh - 0.25), "#8d8270", matte)

    # shop bays
    for i in range(n):
        cx = centers[i]
        typ = shop[i % len(shop)]
        if typ == "open":
            shop_open(P, cx, bw, fy, gh, name + f"_op{i}", warm=1 if shop_lit else 0,
                      shelves=True)
        elif typ == "shutter":
            shutter(P, cx, bw, fy, gh, name + f"_sh{i}", closed=R.random() < 0.72)
        elif typ == "glass":
            shop_glass(P, cx, bw, fy, gh, name + f"_gl{i}", door=True)
        elif typ == "door":
            shop_door(P, cx, bw, fy, gh, name + f"_dr{i}")
        elif typ == "grille":
            shop_grille(P, cx, bw, fy, gh, name + f"_gr{i}")
        else:
            shop_open(P, cx, bw, fy, gh, name + f"_op{i}")
        if R.random() < 0.55:
            fc = awn_cols[0] if i in awning_bays else ["#6d3a2e", "#33463e", "#3e4c54"][i % 3]
            boxp(P, name + "_shopframeL", (0.13, 0.1, gh - 1.1),
                 (cx - bw / 2 + 0.18, fy - 0.02, (gh - 1.1) / 2 + 0.5), fc, matte)
            boxp(P, name + "_shopframeR", (0.13, 0.1, gh - 1.1),
                 (cx + bw / 2 - 0.18, fy - 0.02, (gh - 1.1) / 2 + 0.5), fc, matte)
            boxp(P, name + "_shopframeT", (bw - 0.24, 0.1, 0.14),
                 (cx, fy - 0.02, gh - 0.72), fc, matte)
        if i in awning_bays:
            awning(P, cx, bw, fy, 3.28, depth=1.5, cols=awn_cols, name=name + f"_aw{i}")

    # upper facade
    for sx in (-1, 1):
        boxp(P, name + "_corner", (0.28, d + 0.06, H - gh - 0.1),
             (sx * (w / 2 - 0.08), 0, (gh + H) / 2), vc(wall, 0.012), matte)
    for f in range(floors):
        zz = gh + f * fh
        boxp(P, name + "_band", (w + 0.13, 0.19, 0.16), (0, fy - 0.015, zz),
             "#8f816c", matte)
        for sx in (-1, 1):
            boxp(P, name + "_sband", (0.19, d + 0.13, 0.16), (sx * w / 2, 0, zz),
                 "#8f816c", matte)
    # top cornice
    boxp(P, name + "_cornice", (w + 0.22, d + 0.22, 0.16), (0, 0, H - 0.06),
         "#938772", matte)

    if style == "tile":
        tile_facade(P, w, gh + 0.35, H - 0.2, fy)
    elif style == "brick":
        for k in range(max(2, int((H - gh) / 0.7))):
            boxp(P, "mortar", (w * 0.98, 0.02, 0.018),
                 (0, fy - 0.02, gh + 0.4 + k * 0.7), "#d2c5ad", matte)
    elif style == "cement":
        for k in range(3):
            boxp(P, "streak", (0.5, 0.012, R.uniform(0.8, 2.2)),
                 (-w / 2 + 1.0 + k * w * 0.3, fy - 0.03, gh + 1.6), "#8e8574", matte)

    # upper windows / balconies
    wins = []
    win_w = min(1.5, bw * 0.62)
    for f in range(1, floors):
        zb = gh + (f - 1) * fh
        for i in range(n):
            cx = centers[i]
            if (f, i) in balconies:
                # balcony door
                boxp(P, "bdoor_r", (1.2, 0.14, 2.2), (cx, fy + 0.06, zb + 1.12), "#2f3739", matte)
                boxp(P, "bdoor_g", (1.0, 0.04, 2.05), (cx, fy - 0.02, zb + 1.10),
                     C["glass"], win_warm if R.random() < 0.35 else glass_dark)
                boxp(P, "bdoor_f", (1.1, 0.07, 0.06), (cx, fy - 0.06, zb + 2.12),
                     "#b7b3a5", metal)
                boxp(P, "bdoor_m", (0.04, 0.05, 2.0), (cx, fy - 0.07, zb + 1.1),
                     "#b7b3a5", metal)
                balcony(P, cx, zb + 0.02, fy, w=min(2.7, bw - 0.35), dep=1.02,
                        laundry=laundry, name=f"{name}_bal{f}{i}")
            else:
                lit = 1 if R.random() < lit_bias * 0.6 else (2 if R.random() < 0.18 else 0)
                bars = R.random() < 0.28
                blind = ["#d3c8ad", "#b3a68a", "#a8503f"][R.randrange(3)] if R.random() < 0.25 else None
                win(P, cx, zb + 1.70, win_w, 1.38, fy, lit=lit, bars=bars, blind=blind,
                    name=f"{name}_w{f}{i}")
            # AC units on the facade
            if ac and R.random() < 0.34 and i < n - 1:
                ac_unit(P, cx + win_w * 0.75, zb + 1.18, fy, name=f"{name}_ac{f}{i}")
                boxp(P, name + "_acstain", (0.5, 0.012, R.uniform(0.6, 1.5)),
                     (cx + win_w * 0.75, fy - 0.03, zb + 0.45), "#8d8472", matte)
        # side windows (visible from the aerial)
        if sides:
            sx = -1 if (f + (1 if side > 0 else 0)) % 2 else 1
            side_win(P, sx * w / 2, -d * 0.18, zb + 1.65, 1.15, 1.3, sx,
                     lit=1 if R.random() < 0.1 else 0, fcol="#a9a699",
                     name=f"{name}_sw{f}")
            bx = -w * 0.22 if f % 2 else w * 0.22
            back_win(P, bx, zb + 1.65, 0.98, 1.12, d / 2,
                     name=f"{name}_bw{f}", lit=1 if R.random() < 0.06 else 0)

    # rear service door, small canopy and drainpipe
    rd = d / 2
    boxp(P, name + "_bdoor", (1.0, 0.12, 2.05), (w * 0.3, rd + 0.02, 1.42), "#54402e", matte)
    boxp(P, name + "_bdcan", (1.4, 0.5, 0.08), (w * 0.3, rd + 0.25, 2.55), "#6b6252", metal,
         rot=(0.16, 0, 0))
    drainpipe(P, -w / 2 + 0.28, rd, 0.4, H - 0.2, name=name + "_bpipe")

    # a muted accent pilaster / band adds colour between the signs
    acc = ["#8a4a3a", "#3e5a58", "#7c8a6a", "#4a5b6c"][R.randrange(4)]
    if R.random() < 0.55:
        boxp(P, name + "_accent", (0.55, 0.03, H - gh - 0.7),
             (w / 2 - 0.45, fy - 0.02, (gh + H) / 2 - 0.3), acc, matte)
    boxp(P, name + "_bandline", (w + 0.06, 0.07, 0.12), (0, fy - 0.02, gh - 0.62),
         "#7b6a54", matte)

    # sign
    if sign:
        street_sign(P, sign, fy, gh + 0.18, sign_w, sign_h, board=board)
    else:
        blank_sign(P, fy, gh + 0.18, min(5.0, w * 0.55), 1.2,
                   board=["#4d3128", "#32463e", "#2f3c4c", "#6b3a2c"][R.randrange(4)])

    if R.random() < 0.16:
        rbx = centers[R.randrange(n)]
        boxp(P, name + "_redcloth", (0.7, 0.035, 1.75), (rbx, fy - 0.06, gh + 1.0),
             "#a83a2d", red_cloth)
        boxp(P, name + "_redclothcap", (0.78, 0.06, 0.08), (rbx, fy - 0.07, gh + 1.9),
             "#e0d0aa", matte)
    if R.random() < 0.38:
        projecting_sign(P, w / 2 - 0.5, fy, gh + 0.5,
                        ["#8a4a3a", "#3e5a58", "#4a5b6c"][R.randrange(3)],
                        name + "_proj")
    if R.random() < 0.42:
        poster(P, -w / 2 + 0.5, 2.05, 0.4, 0.6, fy - 0.035,
               style=R.randrange(4), name=name + "_notice")
    if laundry and not balconies:
        window_laundry(P, centers[0], fy, gh + 0.75, w=min(2.3, bw - 0.2),
                       name=name + "_laundry")

    # conductive pipe + meter box
    boxp(P, "conduit", (0.05, 0.05, H - 1.0), (w / 2 - 0.45, fy - 0.07, (H + 1.0) / 2),
         "#7a7464", metal)
    boxp(P, "meter", (0.34, 0.16, 0.44), (w / 2 - 0.45, fy - 0.14, 2.7), "#b7b09c", metal)

    # roof
    if roof == "tile":
        ro = B.tile_roof(name + "_roof", 0, 0, H, d + 1.5, w + 1.6,
                         ridge_h=max(1.5, min(2.4, w * 0.16)), eave_h=0.16,
                         color=["#57544d", "#6a5f52", "#50524c", "#6d5a4b"][
                             abs(int(y * 5 + w)) % 4], material=matte, curl=0.32,
                         nx=16, ny=int(max(14, w * 2.2)))
        B.apply_xform(ro, (0, 0, 0), math.pi / 2)
        P.extend(ro)
        # gable walls on the sides
        for sx in (-1, 1):
            verts = [(sx * (w / 2 + 0.02), -d / 2, H - 0.05),
                     (sx * (w / 2 + 0.02), d / 2, H - 0.05),
                     (sx * (w / 2 + 0.02), 0, H + max(1.5, min(2.4, w * 0.16)) + 0.12)]
            P.append(B._finish("gable", verts, [(0, 1, 2)], vc(wall, 0.02), matte,
                               face_colors=None))
            boxp(P, "gabletrim", (0.12, d + 0.1, 0.12), (sx * (w / 2 + 0.02), 0, H + 0.1),
                 "#6b5f4c", matte)
        boxp(P, "eaveboard", (w + 1.4, 0.14, 0.16), (0, fy - 0.55, H - 0.02), "#5a5143", matte)
        # small water tank on a rear flat
        if tank:
            roof_tank(P, -w * 0.22, d * 0.22, H + 0.3, 0.56, name="tank")
    else:
        parapet(P, w, d, H)
        # roof surface panel
        rcol = ["#8e8778", "#9b8a72", "#7c8277", "#a0947e", "#8b7064", "#94a095"][
            (abs(int(y * 7 + w * 3)) + floors) % 6]
        boxp(P, "roofdeck", (w - 0.35, d - 0.35, 0.08), (0, 0, H + 0.02), rcol, rough)
        if tank is None:
            tank = floors >= 3 and R.random() < 0.45
        if tank:
            roof_tank(P, -w * 0.24, d * 0.2, H + 0.1, 0.66 if w < 10 else 0.8,
                      name="tank")
        if bulk and R.random() < 0.6:
            bulkhead(P, w * 0.22, d * 0.24, H + 0.1, name="bulk", col=vc(wall, 0.02))
        if antenna_roof is None:
            antenna_roof = R.random() < 0.38
        if antenna_roof:
            antenna(P, w * 0.3, -d * 0.15, H + 0.1, name="ant")
        if laundry:
            rooftop_laundry(P, 0, -d * 0.18, H + 0.15, w=w * 0.65, name="rlaundry")
        if R.random() < 0.08:
            roof_solar(P, -w * 0.16, d * 0.12, H + 0.1, rot=0.0, name="rsolar")
        if R.random() < 0.12:
            # pigeon coop
            boxp(P, "coop", (0.9, 0.6, 0.7), (w * 0.3, d * 0.26, H + 0.45), "#8a7150",
                 matte, bevel=0.01)
            for g in range(5):
                boxp(P, "coopbar", (0.02, 0.02, 0.55), (w * 0.3 - 0.35 + g * 0.17,
                     d * 0.26 - 0.32, H + 0.45), "#5b4a33", metal)

    if extra:
        extra(P, {"w": w, "d": d, "fy": fy, "gh": gh, "H": H, "n": n, "bw": bw,
                  "centers": centers, "name": name})
    if os.environ.get("BSIZE"):
        tt = 0
        for o in P:
            o.data.calc_loop_triangles()
            tt += len(o.data.loop_triangles)
        print("BSIZE", name, w, d, floors, n, tt)
    cx, cy, rot = frame_at(y, side, 7.2 + setback, d)
    B.apply_xform(P, (cx, cy, 0), rot)
    if len(P) > 60:
        add(B.join_materials(name, P, skip_prefixes=()))
    else:
        add(P)
    return {"cx": cx, "cy": cy, "rot": rot, "fy": fy, "w": w, "d": d, "H": H}


# ------------------------------------------------------------------ signs / posters
def lantern(P, x, y, z, name="lantern", r=0.22):
    sph(P, name + "_body", r, (x, y, z), "#c03a2c", scale=(1, 1, 0.86), mx=lantern_m,
        seg=10, rings=6)
    cylp(P, name + "_top", r * 0.55, 0.06, (x, y, z + r * 0.86), "#c9a35a", metal, seg=8)
    cylp(P, name + "_bot", r * 0.55, 0.06, (x, y, z - r * 0.85), "#c9a35a", metal, seg=8)
    boxp(P, name + "_tassel", (0.025, 0.025, 0.26), (x, y, z - r - 0.16), "#a8382b", matte)
    cylp(P, name + "_cord", 0.008, 0.42, (x, y, z + r + 0.24), "#4b4034", metal, seg=4)


def poster(P, cx, cz, w, h, y, style=0, name="poster"):
    boxp(P, name + "_b", (w + 0.1, 0.04, h + 0.1), (cx, y + 0.01, cz), "#3d3630", matte)
    P.append(B.quad(name + "_bg", [(cx - w / 2, y - 0.025, cz - h / 2),
                                   (cx + w / 2, y - 0.025, cz - h / 2),
                                   (cx + w / 2, y - 0.025, cz + h / 2),
                                   (cx - w / 2, y - 0.025, cz + h / 2)],
                    ["#d8c8a8", "#7d9a98", "#b45a44", "#c9b06a"][style % 4], matte))
    if style % 4 == 0:
        cylp(P, name + "_sun", h * 0.2, 0.012, (cx - w * 0.12, y - 0.04, cz + h * 0.12),
             "#c5573f", matte, rot=(math.pi / 2, 0, 0), seg=14)
        quadp(P, name + "_hill", [(cx - w / 2, y - 0.042, cz - h * 0.28),
                                  (cx + w / 2, y - 0.042, cz - h * 0.28),
                                  (cx + w * 0.1, y - 0.042, cz - h * 0.02),
                                  (cx - w * 0.35, y - 0.042, cz - h * 0.12)], "#5e6b4b", matte)
        boxp(P, name + "_bar", (w * 0.86, 0.01, h * 0.06), (cx, y - 0.045, cz - h * 0.38),
             "#3f3b32", matte)
    elif style % 4 == 1:
        boxp(P, name + "_band", (w * 0.3, 0.012, h * 0.92), (cx - w * 0.18, y - 0.04, cz),
             "#dfd6bb", matte)
        cylp(P, name + "_ring", h * 0.3, 0.012, (cx + w * 0.16, y - 0.04, cz + h * 0.06),
             "#b8483a", matte, rot=(math.pi / 2, 0, 0), seg=16)
        boxp(P, name + "_foot", (w * 0.9, 0.012, h * 0.1), (cx, y - 0.042, cz - h * 0.4),
             "#3c4540", matte)
    elif style % 4 == 2:
        boxp(P, name + "_band", (w * 0.9, 0.012, h * 0.18), (cx, y - 0.04, cz - h * 0.24),
             "#d9c9a7", matte)
        cylp(P, name + "_sun", h * 0.22, 0.012, (cx, y - 0.04, cz + h * 0.16),
             "#d9b25e", matte, rot=(math.pi / 2, 0, 0), seg=14)
        boxp(P, name + "_v", (w * 0.07, 0.012, h * 0.8), (cx + w * 0.3, y - 0.04, cz),
             "#3b3730", matte)
    else:
        quadp(P, name + "_hill", [(cx - w / 2, y - 0.04, cz - h * 0.42),
                                  (cx + w / 2, y - 0.04, cz - h * 0.42),
                                  (cx + w * 0.2, y - 0.04, cz + h * 0.06),
                                  (cx - w * 0.1, y - 0.04, cz + h * 0.02)], "#44656e", matte)
        boxp(P, name + "_sun", (w * 0.16, 0.012, h * 0.16), (cx + w * 0.2, y - 0.045, cz + h * 0.2),
             "#d9c9a7", matte)
        boxp(P, name + "_bar", (w * 0.9, 0.01, h * 0.05), (cx, y - 0.045, cz + h * 0.4),
             "#3f3b32", matte)
    for (dx, dz, sx, sz) in ((0, h / 2 + 0.03, w + 0.14, 0.06), (0, -h / 2 - 0.03, w + 0.14, 0.06),
                             (-w / 2 - 0.03, 0, 0.06, h), (w / 2 + 0.03, 0, 0.06, h)):
        boxp(P, name + "_fr", (sx, 0.05, sz), (cx + dx, y - 0.035, cz + dz), "#6f6653", metal)


def cross_banner(y, z=6.4, span=15.0, drop=0.0, name="banner"):
    P = []
    tx, ty = street_frame(y)
    nx, ny = ty, -tx
    cx = road_x(y)
    verts, faces, fc = [], [], []
    seg = 14
    for i in range(seg + 1):
        t = i / seg
        xx = cx + (t - 0.5) * span * nx
        yy = y + (t - 0.5) * span * ny
        sag = 0.55 * math.sin(math.pi * t) ** 1.2
        wave = 0.06 * math.sin(t * math.pi * 3)
        verts.append((xx, yy, z - sag + wave))
        verts.append((xx, yy, z - sag - 1.12 + wave * 0.6))
    for i in range(seg):
        a = i * 2
        faces.append((a, a + 2, a + 3, a + 1))
        fc.append(vc("#a83a2d", 0.035))
    P.append(B._finish(name, verts, faces, None, red_cloth, smooth=False, face_colors=fc))
    # cream border lines
    for off, hh in ((0.0, 0.07), (-1.12, 0.07)):
        v2, f2, c2 = [], [], []
        for i in range(seg + 1):
            t = i / seg
            xx = cx + (t - 0.5) * span * nx
            yy = y + (t - 0.5) * span * ny
            sag = 0.55 * math.sin(math.pi * t) ** 1.2
            wave = 0.06 * math.sin(t * math.pi * 3)
            v2.append((xx, yy - 0.015, z - sag + wave + off + hh * 0.5))
            v2.append((xx, yy - 0.015, z - sag + wave + off - hh * 0.5))
        for i in range(seg):
            a = i * 2
            f2.append((a, a + 2, a + 3, a + 1))
            c2.append(B.srgb("#e0d0aa"))
        P.append(B._finish(name + "_edge", v2, f2, None, matte, smooth=False, face_colors=c2))
    # ropes at both ends, up to roof height
    for s in (-1, 1):
        ex = cx + s * 0.5 * span * nx
        ey = y + s * 0.5 * span * ny
        t = math.tau
        beamp(P, name + "_rope", (ex, ey, z + 0.1), (ex, ey, z + 1.5), 0.022, 0.022,
              "#4b4034", metal)
    B.apply_xform(P, (0, 0, 0), 0)
    add(P)


# ------------------------------------------------------------------ landmark extras
def fandian_extra(P, c):
    w, d, fy, gh = c["w"], c["d"], c["fy"], c["gh"]
    for sx in (-1, 1):
        lantern(P, sx * 2.35, fy - 0.72, 3.0, name="fd_lantern")
        boxp(P, "fd_lantern_br", (0.06, 0.5, 0.06), (sx * 2.35, fy - 0.35, 3.55),
             "#5a4a36", metal)
    # standing menu board
    boxp(P, "fd_menu_fr", (0.9, 0.1, 1.25), (3.55, fy - 1.55, 0.66), "#6a4a32", matte,
         rot=(-0.12, 0, 0.05))
    boxp(P, "fd_menu_fc", (0.78, 0.03, 1.1), (3.55, fy - 1.62, 0.68), "#d6c8aa", matte,
         rot=(-0.12, 0, 0.05))
    for k in range(5):
        boxp(P, "fd_menu_row", (0.5, 0.012, 0.045), (3.48, fy - 1.65, 1.02 - k * 0.17),
             ["#8e3f31", "#4b5a45", "#6a5a3c"][k % 3], matte, rot=(-0.12, 0, 0.05))
    # stacked crates + stool by the door
    for k in range(2):
        boxp(P, "fd_crate", (0.55, 0.4, 0.3), (-3.95, fy - 0.62, 0.55 + k * 0.31),
             "#8a6544", matte, bevel=0.01)
        boxp(P, "fd_crate_strip", (0.5, 0.02, 0.06), (-3.95, fy - 0.83, 0.6 + k * 0.31),
             "#6c4c32", matte)
    cylp(P, "fd_stool", 0.17, 0.05, (-2.9, fy - 1.05, 0.62), "#8a6444", matte, seg=8)
    for k in range(3):
        a = math.tau * k / 3
        beamp(P, "fd_stoolleg", (-2.9 + 0.11 * math.cos(a), fy - 1.05 + 0.11 * math.sin(a), 0.15),
              (-2.9 + 0.13 * math.cos(a), fy - 1.05 + 0.13 * math.sin(a), 0.6), 0.03, 0.03,
              "#6b4e34", matte)


def lifa_extra(P, c):
    w, d, fy, gh = c["w"], c["d"], c["fy"], c["gh"]
    # barber pole
    bx = w / 2 - 0.75
    cylp(P, "barber_rod", 0.025, 0.5, (bx, fy - 0.55, 3.55), "#7c7464", metal, seg=6)
    cylp(P, "barber_body", 0.12, 1.15, (bx, fy - 0.55, 2.6), "#e3dcc9", matte, seg=12)
    for k in range(6):
        col = "#b23a30" if k % 2 == 0 else "#3f607a"
        cylp(P, "barber_band", 0.125, 0.09, (bx, fy - 0.55, 2.12 + k * 0.19), col, matte,
             seg=12)
    cylp(P, "barber_cap", 0.14, 0.1, (bx, fy - 0.55, 3.22), "#c9b98f", metal, seg=12)
    cylp(P, "barber_cap2", 0.14, 0.1, (bx, fy - 0.55, 1.99), "#c9b98f", metal, seg=12)
    boxp(P, "barber_bracket", (0.06, 0.34, 0.06), (bx, fy - 0.2, 3.3), "#5c574a", metal)
    # window lettering board (abstract stripes) + towel rail
    boxp(P, "lifa_board", (1.5, 0.06, 0.7), (-2.35, fy - 0.24, 2.45), "#e0d6bf", matte)
    for k in range(3):
        boxp(P, "lifa_stripe", (0.25, 0.02, 0.5), (-2.85 + k * 0.45, fy - 0.28, 2.45),
             ["#b23a30", "#3f607a", "#b23a30"][k], matte)
    # doorway bench
    boxp(P, "lifa_bench", (1.6, 0.42, 0.12), (-3.0, fy - 0.75, 0.55), "#7b5c3d", matte)
    for sx in (-1, 1):
        boxp(P, "lifa_benchleg", (0.12, 0.36, 0.42), (-3.0 + sx * 0.6, fy - 0.75, 0.3),
             "#5f4732", matte)


def zhaoxiang_extra(P, c):
    w, d, fy, gh = c["w"], c["d"], c["fy"], c["gh"]
    # large display photo frames on the facade (abstract landscapes, no people)
    for k, (px, style) in enumerate(((-2.9, 0), (2.9, 1), (0.0, 3))):
        poster(P, px, 2.55, 1.45, 1.75, fy - 0.08, style=style, name=f"zx_photo{k}")
    # camera on a wooden tripod by the door
    cx = 3.55
    for k in range(3):
        a = math.tau * k / 3 + 0.4
        beamp(P, "cam_leg", (cx + 0.28 * math.cos(a), fy - 1.05 + 0.28 * math.sin(a), 0.05),
              (cx, fy - 1.05, 1.15), 0.035, 0.035, "#6d4c31", matte)
    boxp(P, "cam_body", (0.62, 0.42, 0.5), (cx, fy - 1.05, 1.3), "#4a3b2d", matte, bevel=0.02)
    cylp(P, "cam_lens", 0.15, 0.3, (cx - 0.15, fy - 1.32, 1.32), "#2e2b26", metal,
         rot=(math.pi / 2, 0, 0), seg=12)
    cylp(P, "cam_glass", 0.09, 0.04, (cx - 0.15, fy - 1.48, 1.32), "#6e8c8c", glass_dark,
         rot=(math.pi / 2, 0, 0), seg=10)
    boxp(P, "cam_bellows", (0.3, 0.22, 0.32), (cx + 0.1, fy - 1.04, 1.3), "#342820", matte)
    boxp(P, "cam_plate", (0.04, 0.04, 0.3), (cx + 0.3, fy - 0.96, 1.55), "#6b5a40", metal)
    # shutter-board stand
    boxp(P, "zx_stand", (0.7, 0.1, 1.1), (-3.7, fy - 1.5, 0.62), "#5f4933", matte,
         rot=(-0.1, 0, 0))
    poster(P, -3.7, 0.75, 0.55, 0.7, fy - 1.56, style=2, name="zx_stand_poster")


def shudian_extra(P, c):
    w, d, fy, gh = c["w"], c["d"], c["fy"], c["gh"]
    # magazine rack on the walk
    boxp(P, "sd_rack", (1.9, 0.55, 0.95), (-3.2, fy - 1.3, 0.62), "#6b523a", matte)
    for k in range(3):
        boxp(P, "sd_rack_shelf", (1.8, 0.5, 0.03), (-3.2, fy - 1.35, 0.72 + k * 0.3),
             "#8b6a47", matte)
        for g in range(4):
            boxp(P, "sd_mag", (0.36, 0.03, 0.2), (-3.95 + g * 0.42, fy - 1.42,
                0.82 + k * 0.3), ["#b34b39", "#d0bd8e", "#4e6d78", "#7e8f5c"][(g + k) % 4],
                 matte)
    # books stacked by the door
    for k in range(3):
        boxp(P, "sd_bookstack", (0.42, 0.28, 0.16), (3.6, fy - 0.55, 0.55 + k * 0.17),
             ["#8f3f32", "#c7b184", "#4b6570"][k], matte)
    # small reading bench
    boxp(P, "sd_bench", (1.7, 0.4, 0.12), (3.4, fy - 1.35, 0.58), "#7e5d3e", matte)
    for sx in (-1, 1):
        boxp(P, "sd_benchleg", (0.12, 0.34, 0.4), (3.4 + sx * 0.65, fy - 1.35, 0.3),
             "#604731", matte)


def gongxiaoshe_extra(P, c):
    w, d, fy, gh = c["w"], c["d"], c["fy"], c["gh"]
    # grain sacks
    for k in range(5):
        px = -4.4 + (k % 3) * 0.75
        py = fy - 0.7 - (k // 3) * 0.65
        sph(P, "gx_sack", 0.3, (px, py, 0.62), "#bcae86", scale=(1, 0.8, 1.25),
            mx=rough, seg=9, rings=6)
        cylp(P, "gx_sacktie", 0.08, 0.12, (px, py, 0.95), "#8d7c5c", rough, seg=6)
    # bamboo baskets
    for k in range(3):
        px = 3.7 + k * 0.55
        py = fy - 0.7
        lathe_basket(P, px, py, 0.0, 0.30, 0.36)
    # crates
    for k in range(2):
        boxp(P, "gx_crate", (0.7, 0.5, 0.4), (2.4, fy - 0.9, 0.55 + k * 0.41),
             "#8a6544", matte)
        for s in range(3):
            boxp(P, "gx_slat", (0.66, 0.02, 0.05), (2.4, fy - 1.16, 0.42 + k * 0.41 + s * 0.12),
                 "#6c4c32", matte)
    # beam scale
    boxp(P, "gx_scale_base", (0.45, 0.45, 0.12), (-1.7, fy - 1.2, 0.5), "#5d594b", metal)
    cylp(P, "gx_scale_post", 0.035, 1.05, (-1.7, fy - 1.2, 1.05), "#7d7662", metal, seg=6)
    boxp(P, "gx_scale_beam", (1.4, 0.05, 0.05), (-1.7, fy - 1.2, 1.55), "#8c8268", metal)
    cylp(P, "gx_scale_pan", 0.26, 0.05, (-2.25, fy - 1.2, 1.18), "#7d7662", metal, seg=12)
    for k in range(3):
        beamp(P, "gx_scale_chain", (-2.25 + 0.18 * math.cos(k * 2), fy - 1.2, 1.5),
              (-2.25, fy - 1.2, 1.2), 0.008, 0.008, "#5d5749", metal)
    # rope coil
    pts = [(2.9 + 0.16 * math.cos(a), fy - 1.55 + 0.16 * math.sin(a), 0.5)
           for a in [math.tau * i / 16 for i in range(16)]]
    P.append(B.tube("gx_rope", pts, 0.025, "#b49a6a", rough, segments=4, cyclic=True))


def lathe_basket(P, x, y, z, r=0.3, h=0.4, name="basket"):
    P.append(B.lathe(name, [(r * 0.72, z + 0.02), (r * 0.9, z + h * 0.25),
                            (r, z + h * 0.72), (r * 0.94, z + h)],
                     loc=(x, y, 0), segments=12, color="#b6915c", material=matte))
    P.append(B.tube(name + "_rim", [(x + r * 0.94 * math.cos(a), y + r * 0.94 * math.sin(a), z + h)
                                    for a in [math.tau * i / 16 for i in range(16)]],
                    0.022, "#8a6a3e", matte, segments=4, cyclic=True))


def baihuo_extra(P, c):
    w, d, fy, gh = c["w"], c["d"], c["fy"], c["gh"]
    # wide entrance awning
    awning(P, 0, 11.2, fy, 3.35, depth=1.9, cols=("#9c3f31", "#ddcfb3"), name="bh_awn")
    # tall display lightboxes either side of the central door
    for sx in (-1, 1):
        boxp(P, "bh_showcase", (2.4, 0.34, 2.3), (sx * 5.35, fy - 0.36, 1.72), "#6e6150",
             matte, bevel=0.02)
        boxp(P, "bh_showglass", (2.15, 0.04, 2.05), (sx * 5.35, fy - 0.56, 1.72),
             C["glass"], glass_dark)
        poster(P, sx * 5.35, 1.85, 1.1, 1.6, fy - 0.59, style=(0 if sx < 0 else 1),
               name=f"bh_post{sx}")
    # secondary wall sign high on the facade
    boxp(P, "bh_highboard", (5.4, 0.2, 2.2), (0, fy - 0.16, c["H"] - 1.7), "#3e2a22", matte)
    P.append(B.sign_quad("bh_highsign", "baihuo", (0, fy - 0.29, c["H"] - 1.7), 0.0, 4.9, 1.75,
                         signs))
    for (dx, dz, sx, sz) in ((0, 1.0, 5.6, 0.08), (0, -1.0, 5.6, 0.08),
                             (-2.78, 0, 0.08, 2.05), (2.78, 0, 0.08, 2.05)):
        boxp(P, "bh_highframe", (sx, 0.24, sz), (dx, fy - 0.19, c["H"] - 1.7 + dz),
             "#c4b38c", metal)
    boxp(P, "bh_lightstrip", (4.6, 0.08, 0.06), (0, fy - 0.24, c["H"] - 2.82), "#ffe6b4",
         neon_tube)
    # interior: clothes rail / counters visible from the door
    for sx in (-1, 1):
        rail = c["centers"][0] if sx < 0 else c["centers"][2]
        beamp(P, "bh_rail", (rail - 1.0, fy + 0.7, 2.35), (rail + 1.0, fy + 0.7, 2.35),
              0.04, 0.04, "#a8a69a", metal)
        for k in range(4):
            col = ["#9c4a3c", "#c7bb96", "#4e6d75", "#8a8f62"][k % 4]
            boxp(P, "bh_cloth", (0.36, 0.12, 1.0), (rail - 0.72 + k * 0.48, fy + 0.7, 1.78),
                 col, rough)
        cylp(P, "bh_bulb", 0.09, 0.14, (rail, fy + 1.1, 3.2), "#ffe0a6", bulb, seg=8)
    # red ribbon across the entrance
    pts = []
    for i in range(9):
        t = i / 8
        xx = -4.6 + 9.2 * t
        pts.append((xx, fy - 0.78, 3.12 - 0.12 * math.sin(math.pi * t)))
    verts, faces, fc = [], [], []
    for (x, y, z) in pts:
        verts.append((x, y, z))
        verts.append((x, y, z - 0.55))
    for i in range(8):
        a = i * 2
        faces.append((a, a + 2, a + 3, a + 1))
        fc.append(vc("#a83a2d", 0.03))
    P.append(B._finish("bh_ribbon", verts, faces, None, red_cloth, smooth=False,
                       face_colors=fc))
    # potted plants at the door
    for sx in (-1, 1):
        cylp(P, "bh_pot", 0.32, 0.55, (sx * 1.9, fy - 0.9, 0.72), "#a05f45", matte,
             seg=10, r2=0.4)
        sph(P, "bh_plant", 0.48, (sx * 1.9, fy - 0.9, 1.25), "#4d6a42", scale=(1, 1, 0.9),
            mx=matte, seg=8, rings=5)


def lushe_extra(P, c):
    w, d, fy, gh = c["w"], c["d"], c["fy"], c["gh"]
    # projecting sign, readable along the street
    P.append(B.sign_quad("ls_proj", "lushe", (-w / 2 + 0.42, fy - 0.98, 6.9),
                         math.pi / 2, 2.4, 1.2, signs))
    boxp(P, "ls_projboard", (0.16, 2.6, 1.4), (-w / 2 + 0.42, fy - 0.98, 6.9), "#3e2a22",
         matte)
    for zz in (6.1, 7.7):
        beamp(P, "ls_projbr", (-w / 2 + 0.3, fy - 0.05, zz), (-w / 2 + 0.42, fy - 1.9, zz),
              0.04, 0.04, "#55503f", metal)
    # entrance lanterns + mat
    for sx in (-1, 1):
        lantern(P, sx * 1.5, fy - 0.55, 3.05, name="ls_lantern")
    boxp(P, "ls_mat", (2.2, 1.2, 0.03), (0, fy - 0.8, 0.47), "#8a3a2f", rough)
    # reception shelves visible through the open bay
    boxp(P, "ls_keyboard", (1.5, 0.08, 1.0), (-2.56, fy + 1.85, 2.2), "#5b4a36", matte)
    for r in range(4):
        for g in range(5):
            boxp(P, "ls_key", (0.1, 0.03, 0.14), (-3.2 + g * 0.22, fy + 1.78, 2.0 - r * 0.2),
                 "#d3c394", metal)
    # luggage trolley by the door
    boxp(P, "ls_trolley", (0.6, 1.0, 0.1), (3.4, fy - 0.9, 0.5), "#6d5a40", matte)
    for sx in (-1, 1):
        cylp(P, "ls_trolleywheel", 0.12, 0.05, (3.4 + sx * 0.28, fy - 1.32, 0.25),
             "#3f3b33", metal, rot=(0, math.pi / 2, 0), seg=10)
    boxp(P, "ls_luggage", (0.55, 0.4, 0.5), (3.4, fy - 0.95, 0.9), "#8a5a43", matte,
         bevel=0.03)


def cinema_build(y=69.0):
    w, d = 20.0, 16.0
    cx, cy, rot = frame_at(y, 1, 7.2 + 9.0, d)
    P = []
    fy = -d / 2.0
    H = 10.8
    # forecourt
    boxp(P, "cin_plaza", (21.0, 9.4, 0.16), (0, fy - 4.7, 0.08), "#948c7b", rough)
    for k in range(3):
        boxp(P, "cin_plazaline", (0.9, 9.2, 0.012), (-7.4 + k * 7.4, fy - 4.7, 0.165),
             "#87806e", rough)
    # hall volume (recessed 0.9)
    boxp(P, "cin_body", (w, d, H), (0, 0.9, H / 2), vc("#cdc0a6", 0.015), matte,
         bevel=0.03)
    boxp(P, "cin_roofdeck", (w - 0.6, d - 0.6, 0.1), (0, 0.9, H + 0.03), "#8b8472", rough)
    parapet(P, w, d, H)
    # side facade panels + upper centre panel
    for sx in (-1, 1):
        boxp(P, "cin_facade", (6.4, 0.6, H), (sx * 6.8, fy + 0.1, H / 2),
             vc("#d5c9b0", 0.012), matte, bevel=0.02)
        boxp(P, "cin_pilaster", (0.4, 0.75, H), (sx * 9.75, fy + 0.06, H / 2), "#b3a488",
             stone, bevel=0.02)
        boxp(P, "cin_pilaster2", (0.28, 0.72, 4.4), (sx * 3.75, fy + 0.06, 2.2), "#b3a488",
             stone, bevel=0.02)
    boxp(P, "cin_upper", (7.4, 0.6, H - 4.7), (0, fy + 0.1, 4.7 + (H - 4.7) / 2),
         vc("#d5c9b0", 0.012), matte, bevel=0.02)
    boxp(P, "cin_fascia", (w + 0.1, 0.1, 0.55), (0, fy - 0.2, 5.0), "#a2967e", stone)
    boxp(P, "cin_fascia2", (w + 0.1, 0.1, 0.35), (0, fy - 0.2, 9.5), "#a2967e", stone)
    # entrance recess: warm lobby wall + four doors
    boxp(P, "cin_lobby", (7.2, 0.12, 4.5), (0, fy + 0.78, 2.35), "#d9b47c", shop_glow)
    for k in range(5):
        boxp(P, "cin_doorframe", (0.16, 0.18, 4.2), (-3.4 + k * 1.7, fy + 0.62, 2.2),
             "#4c4236", metal)
    for k in range(4):
        boxp(P, "cin_door", (1.5, 0.1, 3.9), (-2.55 + k * 1.7, fy + 0.52, 2.15),
             "#3a4a48", glass_dark)
        boxp(P, "cin_doorbar", (0.05, 0.06, 1.1), (-2.55 + k * 1.7, fy + 0.45, 2.2),
             "#a8a49a", metal)
    # entrance steps
    for k in range(3):
        boxp(P, "cin_step", (8.0 - k * 0.5, 0.55, 0.16), (0, fy - 0.1 - k * 0.5, 0.24 + k * 0.12),
             "#a8a08d", stone, bevel=0.01)
    # canopy
    boxp(P, "cin_canopy", (10.6, 4.5, 0.26), (0, fy - 2.15, 4.85), "#c4b597", stone,
         bevel=0.02)
    boxp(P, "cin_canfascia", (10.6, 0.22, 0.95), (0, fy - 4.42, 5.12), "#3e332b", matte)
    boxp(P, "cin_cantop", (10.7, 4.6, 0.08), (0, fy - 2.15, 5.0), "#b2a58c", stone)
    for sx in (-1, 1):
        boxp(P, "cin_cancol", (0.22, 0.22, 4.7), (sx * 5.0, fy - 4.2, 2.42), "#8e8572",
             stone)
    P.append(B.sign_quad("cin_sign", "dianying", (0, fy - 4.56, 5.12), 0.0, 5.6, 1.86, signs))
    boxp(P, "cin_signframe", (6.2, 0.14, 2.18), (0, fy - 4.48, 5.12), "#2f2721", matte)
    for k in range(11):
        sph(P, "cin_bulb", 0.065, (-4.6 + k * 0.92, fy - 4.45, 4.55), "#ffe8bb", mx=bulb,
            seg=8, rings=5)
    for k in range(7):
        sph(P, "cin_bulb2", 0.06, (-3.6 + k * 1.2, fy - 3.5, 4.66), "#ffe8bb", mx=bulb,
            seg=8, rings=5)
    # circular high window
    cylp(P, "cin_oframe", 1.15, 0.16, (0, fy - 0.24, 8.0), "#b7a98e", stone,
         rot=(math.pi / 2, 0, 0), seg=20)
    cylp(P, "cin_oglass", 0.94, 0.2, (0, fy - 0.3, 8.0), "#31474b", glass_dark,
         rot=(math.pi / 2, 0, 0), seg=20)
    for k in range(4):
        a = math.pi * k / 4
        boxp(P, "cin_omull", (1.85, 0.03, 0.06), (0, fy - 0.42, 8.0), "#8c8874", metal,
             rot=(0, 0, a))
    # upper windows on the side sections
    for sx in (-1, 1):
        for k in range(2):
            win(P, sx * (5.2 + k * 2.9), 7.8, 1.3, 2.4, fy - 0.18, lit=0,
                fcol="#b0a692", name=f"cin_up{sx}{k}")
    # vertical red banner (blank), swallow tail
    boxp(P, "cin_banner", (1.35, 0.07, 6.6), (-8.5, fy - 0.33, 6.6), "#a83a2d", red_cloth)
    for sx in (-1, 1):
        boxp(P, "cin_banner_edge", (0.06, 0.05, 6.6), (-8.5 + sx * 0.66, fy - 0.37, 6.6),
             "#ddcda8", matte)
    quadp(P, "cin_tail1", [(-9.15, fy - 0.37, 3.3), (-8.5, fy - 0.37, 3.3),
                           (-8.5, fy - 0.37, 2.85)], "#a83a2d", red_cloth)
    quadp(P, "cin_tail2", [(-8.5, fy - 0.37, 3.3), (-7.85, fy - 0.37, 3.3),
                           (-8.5, fy - 0.37, 2.85)], "#a83a2d", red_cloth)
    # poster wall + posters
    boxp(P, "cin_postwall", (5.8, 0.18, 2.95), (8.3, fy - 3.7, 1.55), "#c9b99a", matte,
         bevel=0.02)
    for k in range(3):
        poster(P, 6.1 + k * 2.2, 1.55, 1.9, 2.3, fy - 3.82, style=k, name=f"cin_post{k}")
    for sx in (-1, 1):
        boxp(P, "cin_postleg", (0.14, 0.14, 1.55), (8.3 + sx * 2.7, fy - 3.7, 0.78),
             "#6f6653", metal)
    # posters on facade sections
    poster(P, -6.8, 2.2, 1.7, 2.3, fy - 0.36, style=1, name="cin_fp1")
    poster(P, 6.8, 2.2, 1.7, 2.3, fy - 0.36, style=2, name="cin_fp2")
    # ticket booth
    boxp(P, "tk_base", (2.5, 2.3, 2.45), (-8.3, fy - 2.6, 1.22), "#cfc3a8", matte,
         bevel=0.02)
    boxp(P, "tk_window", (1.4, 0.12, 1.0), (-8.3, fy - 3.78, 1.85), "#3c4a46", glass_dark)
    boxp(P, "tk_frame", (1.55, 0.14, 0.08), (-8.3, fy - 3.8, 2.42), "#6a5c46", metal)
    boxp(P, "tk_counter", (1.7, 0.35, 0.1), (-8.3, fy - 3.92, 1.3), "#9a8b70", stone)
    boxp(P, "tk_roof", (2.9, 2.7, 0.14), (-8.3, fy - 2.6, 2.55), "#7c7058", stone)
    boxp(P, "tk_board", (1.6, 0.06, 0.55), (-8.3, fy - 3.8, 3.02), "#d6c8aa", matte)
    boxp(P, "tk_boardstripe", (1.2, 0.02, 0.08), (-8.3, fy - 3.84, 3.02), "#a83a2d", matte)
    # bikes + planters + bollards
    for k in range(3):
        bicycle(P, 2.0 + k * 1.3, fy - 6.6, 0.1, "#3f5a55" if k % 2 else "#7a4a3c",
                name=f"cin_bike{k}")
    for sx in (-1, 1):
        boxp(P, "cin_planter", (1.1, 0.8, 0.5), (sx * 3.4, fy - 7.4, 0.35), "#9c8d72",
             stone, bevel=0.02)
        sph(P, "cin_shrub", 0.55, (sx * 3.4, fy - 7.4, 0.95), "#4d6a42", scale=(1, 0.8, 0.9),
            mx=matte, seg=8, rings=5)
    for k in range(5):
        cylp(P, "cin_bollard", 0.1, 0.55, (-8.0 + k * 4.0, fy - 8.6, 0.38), "#7f7765",
             stone, seg=8)
    lantern(P, -2.4, fy - 0.55, 2.8, name="cin_lantern")
    lantern(P, 2.4, fy - 0.55, 2.8, name="cin_lantern2")
    # small ticket / queue rail
    for k in range(3):
        cylp(P, "cin_rail", 0.035, 0.9, (-9.8, fy - 5.4 + k * 1.0, 0.5), "#6f6a5a",
             metal, seg=6)
    P.append(B.tube("cin_railbar", [(-9.8, fy - 5.4, 0.9), (-9.8, fy - 3.4, 0.9)], 0.03,
                    "#6f6a5a", metal, segments=4))
    B.apply_xform(P, (cx, cy, 0), rot)
    add(B.join_materials("cinema", P, skip_prefixes=()))


def coach(P, px, py, ang, name="bus"):
    """static intercity coach, local +Y is the nose."""
    L, Wd = 8.7, 2.45
    body = []
    boxp(body, name + "_lower", (Wd, L, 1.9), (0, 0, 1.32), "#ded5bd", matte, bevel=0.06)
    boxp(body, name + "_roof", (Wd * 0.98, L * 0.97, 0.5), (0, 0, 2.45), "#d5ccb3", matte,
         bevel=0.1)
    boxp(body, name + "_skirt", (Wd + 0.04, L + 0.02, 0.5), (0, 0, 0.55), "#7b7264", matte,
         bevel=0.03)
    # window band
    for sx in (-1, 1):
        boxp(body, name + "_win", (0.03, L * 0.84, 0.92), (sx * (Wd / 2 + 0.005), -0.2, 2.0),
             C["glass"], glass_dark)
        for k in range(9):
            boxp(body, name + "_mull", (0.04, 0.07, 0.95),
                 (sx * (Wd / 2 + 0.02), -3.6 + k * 0.9, 2.0), "#c9c1ab", metal)
        boxp(body, name + "_stripe", (0.02, L * 0.94, 0.16), (sx * (Wd / 2 + 0.02), 0, 1.18),
             "#a43a2f", matte)
        boxp(body, name + "_stripe2", (0.02, L * 0.94, 0.05), (sx * (Wd / 2 + 0.02), 0, 1.38),
             "#c9b98f", matte)
    # windshield / rear glass
    boxp(body, name + "_front", (Wd * 0.88, 0.06, 1.05), (0, L / 2 + 0.01, 2.02),
         C["glass"], glass_dark)
    boxp(body, name + "_frontframe", (Wd * 0.94, 0.1, 0.09), (0, L / 2 + 0.02, 2.57),
         "#c9c1ab", metal)
    boxp(body, name + "_rear", (Wd * 0.84, 0.05, 0.9), (0, -L / 2 - 0.01, 2.0),
         C["glass"], glass_dark)
    # destination board
    boxp(body, name + "_dest", (1.5, 0.06, 0.34), (0, L / 2 + 0.05, 2.72), "#33342e", matte)
    boxp(body, name + "_destface", (1.36, 0.03, 0.2), (0, L / 2 + 0.09, 2.72), "#d9cba7",
         matte)
    # door on the right side near the front
    boxp(body, name + "_door", (0.06, 1.15, 1.95), (Wd / 2 + 0.03, 2.5, 1.3), C["glass"],
         glass_dark)
    boxp(body, name + "_doorframe", (0.08, 0.07, 2.0), (Wd / 2 + 0.05, 1.92, 1.3),
         "#cbc3ad", metal)
    boxp(body, name + "_doorframe", (0.08, 0.07, 2.0), (Wd / 2 + 0.05, 3.08, 1.3),
         "#cbc3ad", metal)
    # bumpers, lights, plate
    boxp(body, name + "_bump", (Wd + 0.1, 0.24, 0.3), (0, L / 2 + 0.08, 0.62), "#6b675c",
         metal, bevel=0.03)
    boxp(body, name + "_bump2", (Wd + 0.1, 0.24, 0.3), (0, -L / 2 - 0.08, 0.62), "#6b675c",
         metal, bevel=0.03)
    for sx in (-1, 1):
        boxp(body, name + "_head", (0.4, 0.06, 0.3), (sx * 0.82, L / 2 + 0.13, 0.98),
             "#e7dcbc", matte)
        boxp(body, name + "_tail", (0.3, 0.06, 0.36), (sx * 0.86, -L / 2 - 0.13, 0.98),
             "#a3342b", matte)
        cylp(body, name + "_mirror", 0.045, 0.5, (sx * (Wd / 2 + 0.2), L / 2 - 0.25, 2.2),
             "#4d4a41", metal, rot=(0.2, 0, sx * 0.5), seg=6)
    boxp(body, name + "_plate", (0.55, 0.04, 0.18), (0, -L / 2 - 0.14, 0.62), "#d8d2bd",
         matte)
    # wheels
    for yy in (2.75, -2.55):
        for sx in (-1, 1):
            wheel_simple(body, sx * (Wd / 2 - 0.08), yy, 0.48, 0.28,
                         name + f"_wheel{yy}{sx}")
    # roof racks + vents
    boxp(body, name + "_vent", (0.5, 0.5, 0.14), (0, 1.8, 2.74), "#b9b19d", metal)
    boxp(body, name + "_vent", (0.5, 0.5, 0.14), (0, -2.0, 2.74), "#b9b19d", metal)
    for k in range(2):
        boxp(body, name + "_rack", (1.7, 0.06, 0.06), (0, 1.2 - k * 2.4, 2.78),
             "#6d685a", metal)
    B.apply_xform(body, (px, py, 0), ang)
    add(body)


def wheel_simple(P, x, y, r, width, name="wheel"):
    P.append(B.lathe(name + "_tire",
                     [(r * 0.62, -width / 2), (r * 0.94, -width / 2), (r, 0),
                      (r * 0.94, width / 2), (r * 0.62, width / 2)],
                     loc=(x, y, r), rot=(0, math.pi / 2, 0), segments=14,
                     color="#3b3934", material=matte))
    cylp(P, name + "_rim", r * 0.58, width * 0.5, (x, y, r), "#8d897b", metal,
         rot=(0, math.pi / 2, 0), seg=12)
    cylp(P, name + "_hub", r * 0.26, width * 0.56, (x, y, r), "#b9b19c", metal,
         rot=(0, math.pi / 2, 0), seg=10)


def bus_station(y=110.0):
    w, d = 14.0, 11.0
    cx, cy, rot = frame_at(y, 1, 7.2 + 6.0, d)
    P = []
    fy = -d / 2.0
    H = 8.8
    # forecourt
    boxp(P, "st_plaza", (18.0, 6.4, 0.15), (0, fy - 3.2, 0.075), "#918a78", rough)
    for k in range(4):
        boxp(P, "st_line", (0.09, 5.8, 0.012), (-6.0 + k * 4.0, fy - 3.2, 0.157),
             "#7d7664", rough)
    # hall
    boxp(P, "st_body", (w, d, H), (0, 0, H / 2), vc("#d3c7ad", 0.015), matte, bevel=0.03)
    boxp(P, "st_stain", (w + 0.02, 0.02, 0.6), (0, fy - 0.01, 0.75), "#a89a80", matte)
    for f in range(1, 2):
        boxp(P, "st_band", (w + 0.1, 0.18, 0.16), (0, fy - 0.02, 4.4), "#8e816a", matte)
    boxp(P, "st_stripe", (w + 0.04, 0.04, 1.05), (0, fy - 0.02, 4.75), "#c3b596", matte)
    # ground: ticket windows + central door
    for k in range(3):
        wx = -4.6 + k * 2.4
        boxp(P, "st_ticket", (1.8, 0.16, 1.55), (wx, fy - 0.08, 2.15), "#3d4b47", matte)
        boxp(P, "st_ticketglass", (1.55, 0.03, 1.25), (wx, fy - 0.18, 2.18), "#6f8a80",
             glass_dark)
        for b in range(5):
            boxp(P, "st_ticketbar", (0.03, 0.03, 1.25), (wx - 0.6 + b * 0.3, fy - 0.21, 2.18),
                 "#6b6655", metal)
        boxp(P, "st_ticketsill", (2.0, 0.36, 0.1), (wx, fy - 0.25, 1.42), "#a79a80", stone)
        boxp(P, "st_ticketboard", (1.7, 0.05, 0.3), (wx, fy - 0.23, 3.15), "#d6c9ac", matte)
        boxp(P, "st_ticketstrip", (1.3, 0.02, 0.07), (wx, fy - 0.27, 3.15), "#a43a2f", matte)
    # door between the ticket windows
    boxp(P, "st_door", (2.4, 0.12, 2.55), (0.1, fy - 0.12, 1.42), "#4a5551", glass_dark)
    boxp(P, "st_doorframe", (2.6, 0.16, 0.1), (0.1, fy - 0.16, 2.7), "#b9b09a", metal)
    boxp(P, "st_doorhandle", (0.05, 0.08, 0.7), (0.55, fy - 0.22, 1.5), "#a9a28f", metal)
    boxp(P, "st_doorstep", (3.2, 0.8, 0.18), (0.1, fy - 0.45, 0.2), "#a29a87", stone)
    # canopy
    boxp(P, "st_canopy", (9.0, 3.3, 0.24), (0, fy - 1.55, 4.55), "#b9ad93", stone,
         bevel=0.02)
    boxp(P, "st_canfascia", (9.0, 0.16, 0.78), (0, fy - 3.18, 4.7), "#3c332b", matte)
    P.append(B.sign_quad("st_sign", "bashi", (0, fy - 3.29, 4.72), 0.0, 3.9, 1.4, signs))
    boxp(P, "st_signboard", (4.3, 0.1, 1.65), (0, fy - 3.24, 4.72), "#2f2821", matte)
    for sx in (-1, 1):
        cylp(P, "st_column", 0.11, 4.3, (sx * 4.1, fy - 3.0, 2.28), "#8d8571", stone, seg=10)
    # upstairs windows
    for k in range(4):
        win(P, -4.8 + k * 3.2, 6.55, 1.4, 1.35, fy - 0.05, lit=(1 if k == 1 else 0),
            fcol="#b1a894", name=f"st_up{k}")
    # high name sign
    boxp(P, "st_high", (4.4, 0.14, 1.55), (0, fy - 0.12, H - 1.2), "#3c2c24", matte)
    P.append(B.sign_quad("st_high_sign", "bashi", (0, fy - 0.21, H - 1.2), 0.0, 4.0, 1.4,
                         signs))
    boxp(P, "st_highframe", (4.6, 0.1, 0.08), (0, fy - 0.2, H - 0.4), "#c9b891", metal)
    # timetable
    boxp(P, "st_timetable", (2.9, 0.1, 1.7), (4.6, fy - 0.13, 2.05), "#5d5140", matte)
    boxp(P, "st_tt_face", (2.7, 0.03, 1.5), (4.6, fy - 0.19, 2.05), "#d5c7a8", matte)
    for r in range(5):
        for g in range(4):
            boxp(P, "st_tt_cell", (0.52, 0.01, 0.1), (3.55 + g * 0.66, fy - 0.21, 1.55 + r * 0.24),
                 "#8e7f5e", matte)
    boxp(P, "st_tt_head", (2.7, 0.02, 0.14), (4.6, fy - 0.2, 2.72), "#a43a2f", matte)
    # benches + luggage
    for k in range(2):
        bx = -2.6 + k * 3.6
        boxp(P, "st_bench", (2.2, 0.45, 0.12), (bx, fy - 1.4, 0.62), "#7b5c3d", matte)
        for sx in (-1, 1):
            boxp(P, "st_benchleg", (0.12, 0.4, 0.45), (bx + sx * 0.85, fy - 1.4, 0.34),
                 "#5f4732", matte)
    for k in range(3):
        boxp(P, "st_bag", (0.55, 0.4, 0.45), (3.4 + (k % 2) * 0.6, fy - 1.9 - (k // 2) * 0.5,
             0.55), ["#8a5a43", "#4f5f63", "#b09a72"][k], matte, bevel=0.02)
    sph(P, "st_sack", 0.32, (-5.3, fy - 1.9, 0.5), "#b9a97e", scale=(1, 0.8, 1.1),
        mx=rough, seg=8, rings=5)
    # roof equipment
    roof_tank(P, -w * 0.25, d * 0.22, H + 0.1, 0.66, name="st_tank")
    boxp(P, "st_vent", (1.0, 0.8, 0.8), (w * 0.22, d * 0.2, H + 0.5), "#c2b8a1", metal,
         bevel=0.02)
    P.append(B.tube("st_ventpipe", [(w * 0.22, d * 0.2, H + 0.9), (w * 0.22, d * 0.2, H + 1.6),
                                     (w * 0.2, d * 0.2, H + 1.9)], 0.09, "#6f6858", metal,
                    segments=6))
    B.apply_xform(P, (cx, cy, 0), rot)
    add(B.join_materials("station", P, skip_prefixes=()))
    # coach in the forecourt
    tx, ty = street_frame(103.0)
    nx, ny = ty, -tx
    busx = road_x(103.0) + nx * 10.2
    busy = 103.0 + ny * 10.2
    coach(ALL, busx, busy, math.atan2(-tx, ty) + 0.16)
    # stop pole on the walk
    sx = road_x(104.5) + nx * 6.3
    sy = 104.5 + ny * 6.3
    boxp(ALL, "stop_pole", (0.09, 0.09, 3.2), (sx, sy, 1.6), "#6c6655", metal)
    P2 = []
    boxp(P2, "stop_board", (1.5, 0.08, 0.6), (0, 0, 0), "#2f3a42", metal)
    P2.append(B.sign_quad("stop_sign", "bashi", (0, -0.05, 0), 0.0, 1.35, 0.5, signs))
    B.apply_xform(P2, (sx, sy - 0.35, 2.6), math.atan2(-tx, ty))
    add(P2)
    boxp(ALL, "stop_bench", (1.5, 0.4, 0.12), (sx + 0.9, sy - 0.2, 0.55), "#7b5c3d", matte)


# ------------------------------------------------------------------ street furniture
def bicycle(P, x, y, rot, col="#3f5a55", name="bike"):
    b = []
    rx = 0.56
    for sx in (-rx, rx):
        pts = []
        for i in range(19):
            a = math.tau * i / 18
            pts.append((sx + 0.34 * math.cos(a), 0, 0.37 + 0.34 * math.sin(a)))
        b.append(B.tube(name + "_rim", pts, 0.024, "#3c3a35", metal, segments=4, cyclic=True))
        for i in range(8):
            a = math.tau * i / 8 + 0.2
            beamp(b, name + "_sp", (sx, 0, 0.37),
                  (sx + 0.31 * math.cos(a), 0, 0.37 + 0.31 * math.sin(a)),
                  0.008, 0.008, "#8a8579", metal)
        cylp(b, name + "_hub", 0.045, 0.11, (sx, 0, 0.37), "#8d897b", metal,
             rot=(math.pi / 2, 0, 0), seg=8)
    beamp(b, name + "_f1", (-rx, 0, 0.37), (-0.14, 0, 0.78), 0.03, 0.03, col, matte)
    beamp(b, name + "_f2", (-0.14, 0, 0.78), (0.32, 0, 0.8), 0.03, 0.03, col, matte)
    beamp(b, name + "_f3", (0.32, 0, 0.8), (rx, 0, 0.37), 0.03, 0.03, col, matte)
    beamp(b, name + "_f4", (-0.14, 0, 0.78), (-0.06, 0, 0.37), 0.028, 0.028, col, matte)
    beamp(b, name + "_f5", (-0.06, 0, 0.37), (0.32, 0, 0.8), 0.028, 0.028, col, matte)
    beamp(b, name + "_fork", (rx, 0, 0.37), (0.44, 0, 0.85), 0.025, 0.025, "#8a8579", metal)
    boxp(b, name + "_seat", (0.3, 0.13, 0.06), (-0.18, 0, 0.88), "#3d2b20", matte)
    beamp(b, name + "_seatpost", (-0.18, 0, 0.62), (-0.18, 0, 0.85), 0.022, 0.022,
          "#8a8579", metal)
    # handlebar
    boxp(b, name + "_bar", (0.04, 0.5, 0.04), (0.44, 0, 0.9), "#6f6b5e", metal)
    for sy in (-1, 1):
        cylp(b, name + "_grip", 0.035, 0.1, (0.44, sy * 0.22, 0.9), "#3b342a", matte,
             rot=(math.pi / 2, 0, 0), seg=6)
    # fenders
    for sx in (-rx, rx):
        pts = []
        for i in range(7):
            a = math.pi * 0.15 + math.pi * 0.8 * i / 6
            pts.append((sx + 0.37 * math.cos(a), 0, 0.37 + 0.37 * math.sin(a)))
        b.append(B.tube(name + "_fender", pts, 0.026, col, matte, segments=4))
    # rear rack + basket
    boxp(b, name + "_rack", (0.44, 0.24, 0.03), (-0.58, 0, 0.77), "#7d7869", metal)
    boxp(b, name + "_basket", (0.3, 0.26, 0.22), (0.52, 0, 0.96), "#9a7b4f", matte)
    for k in range(3):
        boxp(b, name + "_basketslat", (0.3, 0.02, 0.02), (0.52, -0.12 + k * 0.12, 1.04),
             "#7c5f3b", matte)
    # chain guard + crank
    cylp(b, name + "_crank", 0.1, 0.04, (-0.06, 0.06, 0.4), "#6d6758", metal,
         rot=(math.pi / 2, 0, 0), seg=10)
    boxp(b, name + "_chain", (0.36, 0.02, 0.05), (-0.15, 0.04, 0.45), "#5d5749", metal)
    beamp(b, name + "_kick", (-0.45, 0.0, 0.36), (-0.5, 0.12, 0.03), 0.018, 0.018,
          "#5f5b4e", metal)
    B.apply_xform(b, (x, y, 0.02), rot)
    add(b)


def tricycle(P, x, y, rot, name="tri"):
    b = []
    # three wheels: single front, two rear
    for (wx, wy) in ((1.15, 0.0), (-0.85, -0.55), (-0.85, 0.55)):
        wheel_simple(b, wx, wy, 0.33, 0.1, name + f"_w{wx}{wy}")
    beamp(b, name + "_frame1", (1.15, 0, 0.33), (-0.2, 0, 0.62), 0.045, 0.045,
          "#4d5c50", metal)
    beamp(b, name + "_frame2", (-0.2, 0, 0.62), (-0.85, -0.4, 0.33), 0.04, 0.04,
          "#4d5c50", metal)
    beamp(b, name + "_frame3", (-0.2, 0, 0.62), (-0.85, 0.4, 0.33), 0.04, 0.04,
          "#4d5c50", metal)
    # cargo bed
    boxp(b, name + "_bed", (1.5, 1.25, 0.1), (-0.4, 0, 0.72), "#7c5a3c", matte, bevel=0.01)
    for k in range(5):
        boxp(b, name + "_plank", (1.42, 1.2, 0.03), (-0.4, 0, 0.79 - k * 0.02),
             "#8a6544", matte)
    for sy in (-1, 1):
        boxp(b, name + "_rail", (1.5, 0.05, 0.42), (-0.4, sy * 0.6, 0.98), "#6d4f34", matte)
    boxp(b, name + "_tail", (0.05, 1.2, 0.42), (-1.15, 0, 0.98), "#6d4f34", matte)
    # front fork/handlebar + saddle
    beamp(b, name + "_fork", (1.15, 0, 0.33), (1.0, 0, 0.88), 0.04, 0.04, "#8a8579", metal)
    boxp(b, name + "_bar", (0.05, 0.62, 0.04), (1.0, 0, 0.9), "#6f6b5e", metal)
    boxp(b, name + "_seat", (0.28, 0.3, 0.07), (-0.05, 0, 0.82), "#3b2a20", matte)
    # crates on the bed
    for k in range(2):
        boxp(b, name + "_crate", (0.55, 0.5, 0.35), (-0.65 + k * 0.55, -0.05, 0.95),
             "#96704b", matte, bevel=0.01)
    B.apply_xform(b, (x, y, 0.02), rot)
    add(b)


def street_lamp(P, y, side, name="lamp"):
    tx, ty = street_frame(y)
    nx, ny = ty, -tx
    x = road_x(y) + side * nx * 5.5
    yy = y + side * ny * 5.5
    cylp(P, name + "_base", 0.19, 0.35, (x, yy, 0.3), "#77705f", stone, seg=10)
    cylp(P, name + "_pole", 0.09, 6.1, (x, yy, 3.35), "#5c5a50", metal, seg=8, r2=0.065)
    # arm toward the road
    ax = -side * nx
    ay = -side * ny
    p0 = (x, yy, 6.3)
    p1 = (x + ax * 1.1, yy + ay * 1.1, 6.62)
    p2 = (x + ax * 2.0, yy + ay * 2.0, 6.55)
    beamp(P, name + "_arm1", p0, p1, 0.06, 0.06, "#565349", metal)
    beamp(P, name + "_arm2", p1, p2, 0.055, 0.055, "#565349", metal)
    cylp(P, name + "_head", 0.28, 0.16, (p2[0], p2[1], 6.42), "#6c675a", metal, seg=12)
    cylp(P, name + "_glow", 0.24, 0.05, (p2[0], p2[1], 6.32), "#ffe8b8", bulb, seg=12)
    sph(P, name + "_bulb", 0.1, (p2[0], p2[1], 6.36), "#fff0c8", mx=bulb, seg=8, rings=5)
    cylp(P, name + "_cap", 0.3, 0.08, (p2[0], p2[1], 6.52), "#565349", metal, seg=12)
    boxp(P, name + "_banner", (0.5, 0.02, 0.7), (x + ax * 0.1, yy + ay * 0.1, 4.9),
         "#a83a2d" if side > 0 else "#3e5a62", red_cloth if side > 0 else rough,
         rot=(0, 0, math.atan2(ty, tx)))


def power_pole(P, y, name="pole", trans=False):
    tx, ty = street_frame(y)
    nx, ny = ty, -tx
    x = road_x(y) + nx * 6.55
    yy = y + ny * 6.55
    cylp(P, name + "_p", 0.15, 8.6, (x, yy, 4.3), "#7e7868", stone, seg=8, r2=0.1)
    boxp(P, name + "_arm", (2.3, 0.1, 0.11), (x, yy, 7.9), "#5e5748", matte,
         rot=(0, 0, math.atan2(ty, tx)))
    boxp(P, name + "_arm2", (1.7, 0.08, 0.09), (x, yy, 7.25), "#5e5748", matte,
         rot=(0, 0, math.atan2(ty, tx)))
    for k in (-1, 0, 1):
        cylp(P, name + "_ins", 0.055, 0.2, (x + nx * k * 0.85, yy + ny * k * 0.85, 8.02),
             "#d4ccb4", matte, seg=6)
    for k in (-0.5, 0.5):
        cylp(P, name + "_ins2", 0.05, 0.18, (x + nx * k * 0.7, yy + ny * k * 0.7, 7.36),
             "#c8c0a8", matte, seg=6)
    if trans:
        cylp(P, name + "_trans", 0.32, 0.85, (x - nx * 0.5, yy - ny * 0.5, 6.1),
             "#8e9584", metal, seg=12)
        for zz in (5.8, 6.4):
            cylp(P, name + "_transband", 0.33, 0.05, (x - nx * 0.5, yy - ny * 0.5, zz),
                 "#6d7464", metal, seg=12)
        boxp(P, name + "_transbr", (0.5, 0.1, 0.1), (x - nx * 0.3, yy - ny * 0.3, 6.9),
             "#5e5748", metal)
    # number plate
    boxp(P, name + "_plate", (0.22, 0.03, 0.34), (x, yy - 0.16, 3.4), "#d6c8a8", matte,
         rot=(0, 0, math.atan2(ty, tx)))
    return (x, yy)


def wire(P, pts, color="#37332c", name="wire"):
    P.append(B.tube(name, pts, 0.016, color, matte, segments=4))


def street_tree(P, y, side, h=4.6, name="stree"):
    tx, ty = street_frame(y)
    nx, ny = ty, -tx
    x = road_x(y) + side * nx * 6.05
    yy = y + side * ny * 6.05
    boxp(P, name + "_pit", (1.3, 1.3, 0.06), (x, yy, 0.15), "#4e4538", rough)
    for sx in (-1, 1):
        boxp(P, name + "_edge", (1.4, 0.08, 0.12), (x, yy + sx * 0.66, 0.2), "#8a8270", stone)
        boxp(P, name + "_edge", (0.08, 1.4, 0.12), (x + sx * 0.66, yy, 0.2), "#8a8270", stone)
    paper_tree(P, name, x, yy, 0.12, h, h * 0.52, "#4d6a44", "#5b4935")


def willow(P, x, y, z, h=6.4, name="willow"):
    trunk = [(x, y, z), (x + 0.12, y + 0.04, z + h * 0.28),
             (x - 0.06, y, z + h * 0.5)]
    P.append(B.tube(name + "_trunk", trunk, 0.24, "#5e4a34", matte, segments=6))
    for k in range(4):
        a = math.tau * k / 4 + 0.55
        p1 = (x + math.cos(a) * 1.0, y + math.sin(a) * 1.0, z + h * 0.62)
        p2 = (x + math.cos(a) * 2.0, y + math.sin(a) * 2.0, z + h * 0.44)
        P.append(B.tube(name + f"_br{k}", [(x, y, z + h * 0.45), p1, p2], 0.09,
                        "#5e4a34", matte, segments=5))
    # soft weeping crown
    for k in range(6):
        a = math.tau * k / 6 + 0.3
        rr = 0.8 + (k % 3) * 0.4
        cx = x + math.cos(a) * rr
        cy = y + math.sin(a) * rr
        cz = z + h * (0.66 + 0.055 * (k % 3))
        sph(P, name + "_crown", 1.0, (cx, cy, cz), ["#6f8048", "#7c8b52", "#87965a"][k % 3],
            scale=(1.15, 1.15, 0.82), mx=matte, seg=7, rings=5)
    for k in range(3):
        a = math.tau * k / 3 + 0.9
        cx = x + math.cos(a) * 1.35
        cy = y + math.sin(a) * 1.35
        sph(P, name + "_drape", 0.62, (cx, cy, z + h * 0.44), "#7a894f",
            scale=(0.9, 0.9, 1.9), mx=matte, seg=6, rings=4)
    # hanging leaf curtain
    for k in range(14):
        a = math.tau * k / 14 + 0.2
        rr = 1.3 + 0.85 * (k % 3) / 2.0
        sx = x + math.cos(a) * rr
        sy = y + math.sin(a) * rr
        top = z + h * (0.8 - 0.04 * (k % 2))
        pts = [(sx, sy, top),
               (sx + math.cos(a) * 0.35, sy + math.sin(a) * 0.35, top - h * 0.14),
               (sx + math.cos(a) * 0.6, sy + math.sin(a) * 0.6, z + h * 0.36),
               (sx + math.cos(a) * 0.72, sy + math.sin(a) * 0.72, z + h * 0.07)]
        P.append(B.tube(name + f"_str{k}", pts, 0.017, "#6b6b45", matte, segments=4))
        tx, ty = -math.sin(a), math.cos(a)
        for j in range(4):
            t = 0.10 + j * 0.21
            lz = top - h * (0.1 + 0.72 * t)
            lx = sx + math.cos(a) * (0.15 + 0.58 * t)
            ly = sy + math.sin(a) * (0.15 + 0.58 * t)
            w = 0.26 + 0.05 * (k % 2)
            hh = 0.62 + 0.1 * ((k + j) % 3)
            col = "#7f8f52" if (k + j) % 2 else "#8f9b5c"
            quadp(P, name + f"_leaf{k}{j}",
                  [(lx - tx * w / 2, ly - ty * w / 2, lz),
                   (lx + tx * w / 2, ly + ty * w / 2, lz + 0.03),
                   (lx + tx * w * 0.35, ly + ty * w * 0.35, lz - hh),
                   (lx - tx * w * 0.25, ly - ty * w * 0.25, lz - hh * 0.92)],
                  col, matte)


def bench(P, x, y, rot, name="bench"):
    b = []
    for k in range(3):
        boxp(b, name + "_slat", (1.9, 0.13, 0.045), (0, -0.15 + k * 0.15, 0.52), "#8a6844",
             matte)
    boxp(b, name + "_back", (1.9, 0.05, 0.42), (0, 0.24, 0.78), "#8a6844", matte)
    for sx in (-1, 1):
        boxp(b, name + "_leg", (0.09, 0.5, 0.5), (sx * 0.78, 0.0, 0.27), "#5c5a50", metal)
        boxp(b, name + "_arm", (0.08, 0.5, 0.08), (sx * 0.78, 0.0, 0.63), "#5c5a50", metal)
    B.apply_xform(b, (x, y, 0.05), rot)
    add(b)


def mailbox(P, x, y, rot):
    b = []
    boxp(b, "mb_post", (0.16, 0.16, 1.05), (0, 0, 0.52), "#5e5a4c", metal)
    boxp(b, "mb_body", (0.52, 0.42, 0.72), (0, 0, 1.15), "#3f5f4a", matte, bevel=0.03)
    boxp(b, "mb_roof", (0.6, 0.5, 0.1), (0, 0, 1.54), "#334e3d", matte)
    boxp(b, "mb_slot", (0.36, 0.03, 0.07), (0, -0.22, 1.32), "#2b2d27", matte)
    boxp(b, "mb_hood", (0.42, 0.08, 0.05), (0, -0.24, 1.38), "#334e3d", metal)
    cylp(b, "mb_badge", 0.11, 0.02, (0, -0.25, 1.05), "#c9c0a4", metal,
         rot=(math.pi / 2, 0, 0), seg=10)
    B.apply_xform(b, (x, y, 0.05), rot)
    add(b)


def hydrant(P, x, y, rot=0.0):
    b = []
    cylp(b, "hy_base", 0.2, 0.12, (0, 0, 0.1), "#8f3a2d", metal, seg=10)
    cylp(b, "hy_body", 0.15, 0.72, (0, 0, 0.5), "#b23a2c", metal, seg=10)
    cylp(b, "hy_cap", 0.17, 0.1, (0, 0, 0.9), "#8f3a2d", metal, seg=10)
    sph(b, "hy_top", 0.1, (0, 0, 0.98), "#8f3a2d", mx=metal, seg=8, rings=5)
    for sx in (-1, 1):
        cylp(b, "hy_out", 0.07, 0.16, (sx * 0.17, 0, 0.64), "#8f3a2d", metal,
             rot=(0, math.pi / 2, 0), seg=8)
        cylp(b, "hy_capout", 0.085, 0.04, (sx * 0.26, 0, 0.64), "#c7a56e", metal,
             rot=(0, math.pi / 2, 0), seg=8)
    B.apply_xform(b, (x, y, 0.05), rot)
    add(b)


def trash_bin(P, x, y):
    cylp(P, "bin", 0.28, 0.72, (x, y, 0.42), "#6c7469", metal, seg=10, r2=0.31)
    cylp(P, "bin_lid", 0.32, 0.08, (x, y, 0.82), "#596158", metal, seg=10)
    cylp(P, "bin_mouth", 0.13, 0.04, (x, y, 0.87), "#33372f", matte, seg=8)


def public_tap(P, x, y, rot):
    b = []
    boxp(b, "tap_base", (1.4, 0.8, 0.4), (0, 0, 0.2), "#9a9280", stone, bevel=0.02)
    boxp(b, "tap_basin", (1.1, 0.56, 0.12), (0, 0, 0.45), "#7d8a84", stone)
    cylp(b, "tap_pipe", 0.035, 0.75, (0, 0.28, 0.82), "#7d7a6a", metal, seg=6)
    beamp(b, "tap_spout", (0, 0.28, 1.18), (0, 0.05, 1.14), 0.03, 0.03, "#8d897a", metal)
    boxp(b, "tap_handle", (0.16, 0.04, 0.04), (0, 0.28, 1.25), "#b23a2c", matte)
    B.apply_xform(b, (x, y, 0.05), rot)
    add(b)


def stall(P, x, y, rot, kind="veg", name="stall"):
    b = []
    # frame
    for sx in (-1, 1):
        for sy in (-1, 1):
            boxp(b, name + "_post", (0.055, 0.055, 2.25), (sx * 1.25, sy * 0.85, 1.14),
                 "#6e5b42", matte)
    boxp(b, name + "_railf", (2.55, 0.05, 0.05), (0, -0.85, 2.22), "#6e5b42", matte)
    boxp(b, name + "_railb", (2.55, 0.05, 0.05), (0, 0.85, 2.22), "#6e5b42", matte)
    # canopy: striped cloth sloping to the front
    n = 6
    for k in range(n):
        boxp(b, name + "_can", (2.7 / n + 0.005, 2.0, 0.035),
             (-1.35 + 2.7 * (k + 0.5) / n, 0, 2.42 + 0.08),
             ["#c7b58e", "#a44434"][k % 2], matte, rot=(0.12, 0, 0))
    for k in range(n):
        boxp(b, name + "_val", (2.7 / n + 0.005, 0.03, 0.24),
             (-1.35 + 2.7 * (k + 0.5) / n, -1.02, 2.26),
             ["#c7b58e", "#a44434"][k % 2], matte)
    # table
    boxp(b, name + "_table", (2.35, 1.15, 0.08), (0, -0.1, 0.86), "#96714d", matte,
         bevel=0.01)
    for sx in (-1, 1):
        for sy in (-1, 1):
            boxp(b, name + "_tleg", (0.06, 0.06, 0.82), (sx * 1.02, sy * 0.48, 0.43),
                 "#6f583d", matte)
    boxp(b, name + "_cloth", (2.3, 0.03, 0.62), (0, -0.68, 0.55), "#7d8d7a", rough)
    if kind == "veg":
        for k in range(3):
            lathe_basket(b, -0.7 + k * 0.68, -0.25, 0.88, 0.26, 0.2,
                         name=name + f"_basket{k}")
            for j in range(5):
                sph(b, name + "_veg", 0.11, (-0.7 + k * 0.68 + (j % 2) * 0.09, -0.28 + (j // 2) * 0.08,
                    1.06 + (j % 3) * 0.03), ["#6f8a4c", "#8a9a58", "#b06a44"][(k + j) % 3],
                    scale=(1, 1, 0.8), mx=matte, seg=7, rings=4)
        boxp(b, name + "_crate", (0.6, 0.42, 0.3), (0.85, 0.3, 0.98), "#8a6544", matte)
        for j in range(3):
            boxp(b, name + "_slat", (0.56, 0.02, 0.04), (0.85, 0.08, 0.9 + j * 0.1),
                 "#6c4c32", matte)
        # hanging bulb
        boxp(b, name + "_cord", (0.02, 0.02, 0.5), (0.7, 0.15, 2.2), "#4b463c", metal)
        sph(b, name + "_bulb", 0.075, (0.7, 0.15, 1.95), "#ffdfa8", mx=bulb, seg=7, rings=4)
    elif kind == "food":
        # steamer stack + pot + bowls
        for k in range(3):
            cylp(b, name + "_steam", 0.36, 0.17, (-0.5, -0.1, 1.02 + k * 0.18),
                 "#c5b18a", matte, seg=14)
            cylp(b, name + "_steamrim", 0.37, 0.03, (-0.5, -0.1, 1.09 + k * 0.18),
                 "#8f7d5d", metal, seg=14)
        cylp(b, name + "_pot", 0.3, 0.4, (0.55, -0.1, 1.1), "#4b4a44", metal, seg=12)
        for k in range(3):
            cylp(b, name + "_bowl", 0.1, 0.08, (0.55 + (k - 1) * 0.22, -0.5, 0.96),
                 "#e0d7bd", matte, seg=8)
        boxp(b, name + "_stove", (0.66, 0.5, 0.3), (0.55, -0.1, 0.92), "#7c7364", metal)
    else:
        for k in range(4):
            boxp(b, name + "_box", (0.36, 0.3, 0.24), (-0.8 + k * 0.5, -0.2, 1.02 + (k % 2) * 0.26),
                 ["#a04a39", "#c9b57e", "#4f6b72", "#8a8a5e"][k], matte)
        boxp(b, name + "_rack", (2.2, 0.5, 0.04), (0, 0.4, 1.18), "#7c6a4a", matte)
    for k in range(2):
        cylp(b, name + "_stool", 0.16, 0.05, (-1.55 + k * 0.4, -1.2, 0.5), "#8a6444",
             matte, seg=8)
        for j in range(3):
            a = math.tau * j / 3
            beamp(b, name + "_stoolleg", (-1.55 + k * 0.4 + 0.1 * math.cos(a),
                  -1.2 + 0.1 * math.sin(a), 0.15), (-1.55 + k * 0.4 + 0.12 * math.cos(a),
                  -1.2 + 0.12 * math.sin(a), 0.5), 0.025, 0.025, "#6b4e34", matte)
    B.apply_xform(b, (x, y, 0.02), rot)
    add(b)


def canal_boat(P, x, y, rot, name="boat"):
    b = []
    ztop, zmid, zbot = -1.55, -1.78, -2.45
    xs = [-3.1, -2.7, -1.8, 0.0, 1.8, 2.7, 3.1]
    ws = [0.06, 0.52, 0.82, 0.90, 0.82, 0.52, 0.06]
    verts, faces, fc = [], [], []
    for xx, ww in zip(xs, ws):
        verts += [(xx, -ww, ztop), (xx, -ww * 0.86, zmid), (xx, 0, zbot),
                  (xx, ww * 0.86, zmid), (xx, ww, ztop)]
    for i in range(len(xs) - 1):
        a = i * 5
        bb = (i + 1) * 5
        for k in range(4):
            faces.append((a + k, bb + k, bb + k + 1, a + k + 1))
            fc.append(vc("#6d5238", 0.06))
    faces.append((4, 3, 2, 1, 0))
    fc.append(vc("#6d5238", 0.04))
    a = (len(xs) - 1) * 5
    faces.append((a, a + 1, a + 2, a + 3, a + 4))
    fc.append(vc("#6d5238", 0.04))
    b.append(B._finish("boat_hull", verts, faces, None, matte, smooth=False,
                       face_colors=fc))
    # gunwale rails
    for sy in (-1, 1):
        pts = [(xx, sy * ww * 0.98, ztop + 0.02) for xx, ww in zip(xs[1:-1], ws[1:-1])]
        b.append(B.tube("boat_rail", pts, 0.045, "#8a6b46", matte, segments=4))
    # floor and ribs
    boxp(b, "boat_floor", (5.2, 1.35, 0.06), (0, 0, -1.95), "#7b5c3d", matte)
    for k in range(6):
        bx = -2.4 + k * 0.95
        boxp(b, "boat_rib", (0.08, 1.62, 0.12), (bx, 0, -1.88), "#5d452f", matte)
    # stern cabin
    boxp(b, "boat_cabin", (1.55, 1.28, 1.25), (-1.45, 0, -1.30), "#c6b48f", matte,
         bevel=0.02)
    boxp(b, "boat_cabroof", (1.85, 1.55, 0.09), (-1.45, 0, -0.64), "#7b6a50", metal)
    for sy in (-1, 1):
        boxp(b, "boat_cabwin", (1.0, 0.03, 0.42), (-1.55, sy * 0.655, -1.18), "#3a4a46",
             glass_dark)
    boxp(b, "boat_cabdoor", (0.45, 0.03, 0.95), (-0.68, -0.66, -1.40), "#5b4632", matte)
    cylp(b, "boat_chimney", 0.06, 0.55, (-1.95, 0.35, -0.35), "#4f4b41", metal, seg=6)
    # cargo: tarp + crates
    boxp(b, "boat_cargo", (1.6, 1.25, 0.5), (0.65, 0, -1.65), "#5e7c86", rough)
    for k in range(3):
        boxp(b, "boat_crate", (0.55, 0.5, 0.35), (1.8 + (k % 2) * 0.62, -0.2 + (k // 2) * 0.5,
             -1.55), "#8a6544", matte)
    # oars + pole + fenders
    beamp(b, "boat_oar", (0.2, -1.1, -1.35), (2.4, -1.5, -1.2), 0.035, 0.035, "#8a6b46", matte)
    cylp(b, "boat_pole", 0.03, 3.6, (0.9, 0.9, -1.7), "#a58a54", matte,
         rot=(0, math.pi / 2, 0), seg=6)
    for k in range(3):
        cylp(b, "boat_fender", 0.16, 0.41, (0.3 + k * 1.6, 0.95, -1.75), "#3b3934",
             matte, rot=(math.pi / 2, 0, 0), seg=10)
    lantern(b, -0.2, -0.85, -0.78, name="boat_lantern", r=0.15)
    B.apply_xform(b, (x, y, 0), rot)
    add(b)


def solar_heater(P, cx, cy, z, rot=0.0, name="solar"):
    b = []
    ang = 0.62
    # tilted collector with glass tubes
    boxp(b, name + "_back", (1.9, 1.55, 0.06), (0, 0, 0.55), "#8a8372", metal,
         rot=(ang, 0, 0))
    for k in range(9):
        cylp(b, name + "_tube", 0.055, 1.9, (-0.8 + k * 0.2, -0.38, 0.72), "#7d9a9d",
             glass_dark, rot=(0, math.pi / 2, ang), seg=8)
    boxp(b, name + "_frame", (2.0, 0.06, 0.08), (0, -0.75, 1.16), "#6d6757", metal)
    cylp(b, name + "_tank", 0.3, 1.9, (0, 0.62, 1.18), "#c9c2ad", metal,
         rot=(0, math.pi / 2, 0), seg=12)
    for sx in (-1, 1):
        boxp(b, name + "_leg", (0.07, 0.07, 0.95), (sx * 0.8, 0.5, 0.48), "#6d6757", metal)
    cylp(b, name + "_pipe", 0.04, 1.4, (0.75, 0.62, 0.55), "#8a8474", metal, seg=6)
    B.apply_xform(b, (cx, cy, z), rot)
    add(b)


def projecting_sign(P, x, fy, z, col="#a83a2d", name="psign"):
    b = []
    boxp(b, name + "_b", (0.07, 1.15, 0.72), (x, fy - 0.62, z), col, matte)
    for sy in (-1, 1):
        boxp(b, name + "_edge", (0.09, 0.05, 0.78), (x, fy - 0.62 + sy * 0.56, z),
             "#e0d2b2", matte)
        cylp(b, name + "_disc", 0.2, 0.02, (x + 0.045, fy - 0.62, z), "#e0d2b2", matte,
             rot=(0, math.pi / 2, 0), seg=12)
        boxp(b, name + "_stripe", (0.02, 0.8, 0.09), (x + 0.05, fy - 0.62, z - 0.22),
             "#e0d2b2", matte)
    boxp(b, name + "_brk", (0.06, 0.5, 0.06), (x, fy - 0.2, z + 0.3), "#55503f", metal)
    P.append(B.join_group(name, b))


def phone_booth(P, x, y, rot):
    b = []
    boxp(b, "pb_base", (1.0, 1.0, 0.12), (0, 0, 0.06), "#7f7b6c", stone)
    for sx in (-1, 1):
        for sy in (-1, 1):
            boxp(b, "pb_post", (0.08, 0.08, 2.3), (sx * 0.42, sy * 0.42, 1.2), "#3f5a62",
                 metal)
    for sx in (-1, 1):
        boxp(b, "pb_glass", (0.03, 0.78, 2.0), (sx * 0.43, 0, 1.25), "#6d8888", glass_dark)
    for sy in (-1, 1):
        boxp(b, "pb_glass", (0.78, 0.03, 2.0), (0, sy * 0.43, 1.25), "#6d8888", glass_dark)
        boxp(b, "pb_frame", (0.95, 0.06, 0.08), (0, sy * 0.43, 2.28), "#3f5a62", metal)
    boxp(b, "pb_roof", (1.15, 1.15, 0.12), (0, 0, 2.42), "#3f5a62", metal)
    boxp(b, "pb_phone", (0.24, 0.16, 0.42), (0.1, -0.36, 1.35), "#4d4a3f", matte)
    boxp(b, "pb_handset", (0.06, 0.22, 0.08), (-0.03, -0.46, 1.42), "#2f2c26", matte)
    boxp(b, "pb_shelf", (0.55, 0.2, 0.05), (0.05, -0.3, 1.05), "#6c6658", metal)
    B.apply_xform(b, (x, y, 0.08), rot)
    add(b)


def handcart(P, x, y, rot):
    b = []
    boxp(b, "hc_bed", (1.2, 1.8, 0.09), (0, 0, 0.62), "#8a6744", matte)
    for sy in (-1, 1):
        boxp(b, "hc_rail", (0.05, 1.8, 0.35), (sy * 0.58, 0, 0.8), "#6d4f34", matte)
    for sy in (-1, 1):
        cylp(b, "hc_wheel", 0.27, 0.07, (0, sy * 0.62, 0.28), "#3c3a34", matte,
             rot=(math.pi / 2, 0, 0), seg=14)
    for sy in (-1, 1):
        beamp(b, "hc_handle", (0.5, sy * 0.45, 0.65), (1.35, sy * 0.45, 0.55), 0.04, 0.04,
              "#6d4f34", matte)
    for k in range(2):
        boxp(b, "hc_box", (0.5, 0.45, 0.35), (-0.2 + k * 0.45, 0.3, 0.85), "#9a7450",
             matte)
    B.apply_xform(b, (x, y, 0.05), rot)
    add(b)


def kiosk_binggun(P, x, y, rot):
    b = []
    boxp(b, "bg_base", (2.0, 1.6, 0.25), (0, 0, 0.12), "#8f8876", stone)
    boxp(b, "bg_body", (1.9, 1.5, 2.25), (0, 0, 1.35), "#ccd3c8", matte, bevel=0.02)
    boxp(b, "bg_roof", (2.3, 1.9, 0.13), (0, 0, 2.53), "#6f7d74", metal, bevel=0.02)
    # hatch + rolled shutter
    boxp(b, "bg_hatch", (1.25, 0.1, 0.85), (0, -0.76, 1.85), "#3d4a44", matte)
    boxp(b, "bg_sill", (1.5, 0.34, 0.1), (0, -0.86, 1.32), "#b3a98f", stone)
    cylp(b, "bg_roll", 0.12, 1.35, (0, -0.8, 2.28), "#7f887e", metal,
         rot=(0, math.pi / 2, 0), seg=8)
    P.append(B.sign_quad("bg_sign", "binggun", (0, -0.8, 2.82), 0.0, 1.65, 0.59, signs))
    boxp(b, "bg_signboard", (1.8, 0.1, 0.72), (0, -0.74, 2.82), "#3b2c24", matte)
    # ice box
    boxp(b, "bg_ice", (1.15, 0.72, 0.68), (0, -1.65, 0.4), "#e0ddd0", matte, bevel=0.03)
    boxp(b, "bg_icelid", (1.18, 0.75, 0.09), (0, -1.65, 0.78), "#c9c4b3", matte)
    for k in range(3):
        boxp(b, "bg_icestripe", (0.2, 0.02, 0.3), (-0.3 + k * 0.3, -2.02, 0.42),
             "#a83a2d", matte)
    # awning
    for k in range(4):
        boxp(b, "bg_aw", (0.5, 1.0, 0.03), (-0.75 + k * 0.5, -1.2, 2.3), 
             ["#a44434", "#d8cbb0"][k % 2], matte, rot=(0.22, 0, 0))
    B.apply_xform(b, (x, y, 0.08), rot)
    add(b)


def kiosk_xiubiao(P, x, y, rot):
    b = []
    boxp(b, "xb_base", (1.35, 1.0, 0.3), (0, 0, 0.15), "#8f8876", stone)
    boxp(b, "xb_body", (1.25, 0.9, 1.9), (0, 0, 1.25), "#7d6a52", matte, bevel=0.02)
    boxp(b, "xb_case", (1.1, 0.5, 0.4), (0, -0.45, 1.55), "#4a5a56", glass_dark, bevel=0.02)
    boxp(b, "xb_casef", (1.18, 0.52, 0.06), (0, -0.45, 1.78), "#c9b98f", metal)
    cylp(b, "xb_clock", 0.13, 0.02, (-0.3, -0.7, 1.6), "#e0d8c2", matte,
         rot=(math.pi / 2, 0, 0), seg=12)
    boxp(b, "xb_stool", (0.35, 0.3, 0.06), (0, -0.95, 0.5), "#8a6444", matte)
    P.append(B.sign_quad("xb_sign", "xiubiao", (0, -0.47, 2.4), 0.0, 1.7, 0.54, signs))
    boxp(b, "xb_signboard", (1.85, 0.08, 0.62), (0, -0.42, 2.4), "#3b2c24", matte)
    boxp(b, "xb_roof", (1.65, 1.25, 0.1), (0, 0, 2.4), "#6c6453", metal)
    B.apply_xform(b, (x, y, 0.06), rot)
    add(b)


# ------------------------------------------------------------------ background
def paper_tree(P, name, x, y, z, h=5.0, spread=2.2, leaf="#4c6a43",
               trunk="#5b4935"):
    P.append(B.cylinder(name + "_trunk", 0.13, h * 0.6, (x + 0.05, y, z + h * 0.3),
                        segments=6, color=trunk, material=matte, radius2=0.08))
    for b in range(3):
        a = math.tau * b / 3 + 0.5
        beamp(P, name + f"_br{b}", (x, y, z + h * 0.5),
              (x + math.cos(a) * spread * 0.55, y + math.sin(a) * spread * 0.55,
               z + h * 0.72), 0.055, 0.055, trunk, matte)
    for c in range(5):
        a = math.tau * c / 5 + R.uniform(-0.3, 0.3)
        rr = spread * R.uniform(0.25, 0.62)
        cx = x + math.cos(a) * rr
        cy = y + math.sin(a) * rr
        cz = z + h * R.uniform(0.66, 0.94)
        rx = spread * R.uniform(0.4, 0.62)
        rz = rx * R.uniform(0.55, 0.8)
        verts, faces = [], []
        for r in range(3):
            t = r / 2.0
            rad = rx * math.sin((0.18 + 0.72 * t) * math.pi)
            zz = cz - rz + 2 * rz * t
            for si in range(7):
                aa = math.tau * si / 7
                verts.append((cx + rad * math.cos(aa), cy + rad * math.sin(aa), zz))
        for r in range(2):
            for si in range(7):
                s2 = (si + 1) % 7
                faces.append((r * 7 + si, r * 7 + s2, (r + 1) * 7 + s2,
                              (r + 1) * 7 + si))
        P.append(B._finish(name + f"_leaf{c}", verts, faces, vc(leaf, 0.08), matte,
                           smooth=False))


def back_house(x, y, rot, w=7.0, d=6.0, floors=2, wall="#c4b79c", name="bh",
               courtyard=True):
    b = []
    h = 3.0 * floors
    boxp(b, name + "_base", (w + 0.3, d + 0.3, 0.3), (0, 0, 0.15), "#8d8573", stone)
    boxp(b, name + "_wall", (w, d, h), (0, 0, h / 2 + 0.25), wall, matte, bevel=0.02)
    boxp(b, name + "_band", (w + 0.08, d + 0.08, 0.12), (0, 0, 3.05), "#8d7f68", matte)
    for f in range(floors):
        for k in range(2):
            wx = -w * 0.24 + k * w * 0.48
            boxp(b, name + "_win", (1.05, 0.06, 1.1), (wx, -d / 2 - 0.03, 1.75 + f * 3.0),
                 C["glass"], glass_dark)
            boxp(b, name + "_wf", (1.2, 0.09, 0.07), (wx, -d / 2 - 0.05, 2.34 + f * 3.0),
                 "#6d5c42", matte)
            boxp(b, name + "_wf", (1.2, 0.09, 0.07), (wx, -d / 2 - 0.05, 1.16 + f * 3.0),
                 "#6d5c42", matte)
    boxp(b, name + "_door", (1.1, 0.1, 2.1), (0, -d / 2 - 0.04, 1.3), "#533a28", matte)
    boxp(b, name + "_doorf", (1.35, 0.14, 0.12), (0, -d / 2 - 0.05, 2.38), "#6b563d", matte)
    ro = B.tile_roof(name + "_roof", 0, 0, 0, d + 1.4, w + 1.4,
                     ridge_h=1.5, eave_h=0.14, color="#57544d", material=matte,
                     curl=0.3, nx=8, ny=11)
    B.apply_xform(ro, (0, 0, h + 0.25), math.pi / 2)
    b.extend(ro)
    boxp(b, name + "_chim", (0.5, 0.5, 1.3), (w * 0.28, d * 0.2, h + 1.1), "#968d78", matte)
    if courtyard:
        for sx in (-1, 1):
            boxp(b, name + "_cwall", (0.18, 2.4, 1.0), (sx * (w / 2 + 0.9), -d / 2 - 1.3, 0.5),
                 "#bdb298", matte)
        boxp(b, name + "_cgat", (w + 0.2, 0.16, 1.1), (0, -d / 2 - 2.6, 0.55), "#bdb298", matte)
        boxp(b, name + "_cgate", (2.0, 0.2, 1.9), (0, -d / 2 - 2.62, 0.95), "#584634", matte)
    B.apply_xform(b, (x, y, 0.02), rot)
    add(b)


def factory(x, y, rot):
    b = []
    w, d, h = 22.0, 11.0, 5.4
    boxp(b, "fac_wall", (w, d, h), (0, 0, h / 2 + 0.1), "#a8a090", matte, bevel=0.03)
    boxp(b, "fac_plinth", (w + 0.2, d + 0.2, 0.5), (0, 0, 0.25), "#8a8270", stone)
    boxp(b, "fac_band", (w + 0.05, d + 0.05, 0.35), (0, 0, h + 0.1), "#887f6d", matte)
    for k in range(6):
        boxp(b, "fac_win", (1.6, 0.06, 1.2), (-w * 0.38 + k * 2.9, -d / 2 - 0.04, 3.3),
             "#415353", glass_dark)
        boxp(b, "fac_winf", (1.75, 0.05, 0.08), (-w * 0.38 + k * 2.9, -d / 2 - 0.06, 3.95),
             "#6a5c46", metal)
    boxp(b, "fac_bigdoor", (4.2, 0.12, 3.6), (w * 0.25, -d / 2 - 0.05, 1.9), "#6c7568",
         metal)
    for k in range(4):
        boxp(b, "fac_doorslat", (4.0, 0.03, 0.05), (w * 0.25, -d / 2 - 0.12, 0.5 + k * 0.85),
             "#565e52", metal)
    # roof monitor
    boxp(b, "fac_mon", (w * 0.7, 1.4, 1.2), (0, 0.5, h + 0.7), "#9a9180", metal)
    for k in range(5):
        boxp(b, "fac_skyl", (2.0, 0.06, 0.5), (-w * 0.28 + k * 3.1, -0.25, h + 0.8),
             "#566a6b", glass_dark)
    # chimney
    cylp(b, "fac_chim", 1.05, 17.0, (-w * 0.36, d * 0.25, 8.5), "#9a6a55", rough,
         seg=14, r2=0.72)
    for k in range(4):
        cylp(b, "fac_chimband", 1.02 - k * 0.06, 0.14, (-w * 0.36, d * 0.25, 3.0 + k * 4.0),
             "#b88a72", rough, seg=14)
    cylp(b, "fac_chimlip", 0.85, 0.22, (-w * 0.36, d * 0.25, 17.0), "#c7b09a", stone,
         seg=14)
    # stacks of crates outside
    for k in range(5):
        boxp(b, "fac_crate", (0.8, 0.6, 0.5), (w * 0.36 - (k % 3) * 0.9, -d / 2 - 1.2,
             0.35 + (k // 3) * 0.5), "#8a6a48", matte)
    B.apply_xform(b, (x, y, 0.02), rot)
    add(b)


def water_tower(P, x, y, name="wtower"):
    b = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            beamp(b, name + "_leg", (x + sx * 2.4, y + sy * 2.4, 0.1),
                  (x + sx * 1.3, y + sy * 1.3, 8.6), 0.35, 0.35, "#8f8776", stone)
    for zz in (3.2, 5.9, 8.2):
        for k in range(2):
            boxp(b, name + "_brace", (6.0 - zz * 0.5, 0.12, 0.12),
                 (x, y - 2.0 + k * 4.0, zz), "#7f7767", stone, bevel=0.01)
            boxp(b, name + "_brace", (0.12, 6.0 - zz * 0.5, 0.12),
                 (x - 2.0 + k * 4.0, y, zz), "#7f7767", stone, bevel=0.01)
    cylp(b, name + "_tank", 2.6, 3.0, (x, y, 10.4), "#c6bea9", metal, seg=18)
    for zz in (9.3, 10.4, 11.5):
        cylp(b, name + "_band", 2.63, 0.08, (x, y, zz), "#8a8372", metal, seg=18)
    cylp(b, name + "_lid", 2.55, 1.1, (x, y, 12.45), "#b8b09b", metal, seg=18, r2=0.3)
    cylp(b, name + "_pipe", 0.13, 9.2, (x + 1.4, y, 4.8), "#77705f", metal, seg=8)
    boxp(b, name + "_platform", (3.2, 3.2, 0.14), (x, y, 8.9), "#8d8473", metal)
    for k in range(8):
        boxp(b, name + "_rung", (0.04, 0.4, 0.04), (x - 2.7, y, 9.2 + k * 0.4), "#6b6555",
             metal)
    add(b)


def field_plot(x, y, w, d, rot, col1="#7f9850", col2="#8fa95c", name="field"):
    z = max(0.05, terrain_h(x, y) + 0.04)
    b = []
    for (bx, by, bw, bd) in ((0, -d / 2, w + 0.6, 0.35), (0, d / 2, w + 0.6, 0.35),
                              (-w / 2, 0, 0.35, d + 0.6), (w / 2, 0, 0.35, d + 0.6)):
        b.append(B.box(name + "_bund", (bw, bd, 0.28), (bx, by, 0.14), color="#6f6845",
                       material=rough, bevel=0.02))
    b.append(B.rice_field(name + "_crop", 0, 0, 0.07, w - 1.2, d - 1.2, 0,
                          spacing=1.05, height=0.42, colors=(col1, col2), material=matte,
                          rng=R, blade_width=0.03, blades=4))
    B.apply_xform(b, (x, y, z), rot)
    add(b)


def conifer(x, y, h=5.0, color="#3c5438"):
    z = max(0.0, terrain_h(x, y))
    b = [B.cylinder("conif_trunk", 0.09, h * 0.4, (x, y, z + h * 0.2), segments=5,
                    color="#4f3f2e", material=matte)]
    for (rr, zz, hh) in ((0.36, 0.36, 0.5), (0.28, 0.58, 0.42), (0.18, 0.78, 0.34)):
        b.append(B.cylinder("conif_needle", h * rr, h * hh, (x, y, z + h * zz),
                            segments=7, color=color, material=matte, radius2=0.02))
    add(b)


def broadleaf(x, y, h=5.2):
    z = max(0.0, terrain_h(x, y))
    add(B.tree("btree", (x, y, z), h, h * 0.46, "#4c6a43", "#5b4935", matte, matte, R))


# ------------------------------------------------------------------ layout helpers
def prop_pos(y, side, off):
    tx, ty = street_frame(y)
    nx, ny = ty, -tx
    return (road_x(y) + side * nx * off, y + side * ny * off,
            math.atan2(-side * ty, -side * tx))


def xf(cx, cy, rot, lx, ly):
    c = math.cos(rot)
    s = math.sin(rot)
    return (cx + c * lx - s * ly, cy + s * lx + c * ly)


def alley(y, side, width=2.4):
    tx, ty = street_frame(y)
    nx, ny = ty, -tx
    c0 = (road_x(y) + side * nx * 7.05, y + side * ny * 7.05)
    c1 = (road_x(y) + side * nx * 31.0, y + side * ny * 31.0)
    P = []
    for (zz, col) in ((0.09, "#8a8372"), (0.095, "#756f5f")):
        w = width if zz < 0.09 else 0.16
        corners = [(c0[0] + tx * w / 2, c0[1] + ty * w / 2, zz),
                   (c0[0] - tx * w / 2, c0[1] - ty * w / 2, zz),
                   (c1[0] - tx * w / 2, c1[1] - ty * w / 2, zz),
                   (c1[0] + tx * w / 2, c1[1] + ty * w / 2, zz)]
        P.append(B.quad("alley", corners, col, rough))
    # service clutter in the alley
    for k in range(2):
        x, yy = c0[0] + nx * side * (2.0 + k * 1.4), c0[1] + ny * side * (2.0 + k * 1.4)
        boxp(P, "alleycrate", (0.55, 0.5, 0.42), (x, yy, 0.28), "#7f5f40", matte)
    P.append(B.tube("alleywire", [(c0[0], c0[1], 4.2), (c1[0], c1[1], 4.4)],
                    0.012, "#3a352d", matte, segments=4))
    add(P)


def parking_bay(yc, side=1):
    tx, ty = street_frame(yc)
    nx, ny = ty, -tx
    P = []
    for (o, ln) in ((2.15, 5.6), (4.35, 5.6)):
        x = road_x(yc) + side * nx * o
        yy = yc + side * ny * o
        boxp(P, "bayline", (0.1, ln, 0.012), (x, yy, 0.098), "#cfc7ae", rough,
             rot=(0, 0, math.atan2(ty, tx)))
    for off in (-2.8, 2.8):
        x = road_x(yc) + side * nx * 3.25 + tx * off
        yy = yc + side * ny * 3.25 + ty * off
        boxp(P, "bayline", (2.2, 0.1, 0.012), (x, yy, 0.098), "#cfc7ae", rough,
             rot=(0, 0, math.atan2(ty, tx)))
    add(P)


# ------------------------------------------------------------------ the town
def build_shop_row():
    # ---------------- south, west side
    shophouse(-115, -1, 8.5, 9, 2, C["wall_a"], shop=("open", "door"), name="sw2",
              roof="tile", awning_bays=(0,), awn_cols=("#7c4a3a", "#d8cbb0"),
              board="#3b4d42")
    shophouse(-101, -1, 11, 11, 3, C["wall_a"], shop=("glass", "open", "shutter"),
              name="sw3", style="tile", tank=True, awning_bays=(1,),
              balconies=((2, 1),))
    shophouse(-86, -1, 10, 10, 3, C["wall_b"], sign="fandian", sign_w=4.4, sign_h=1.55,
              shop=("open", "door", "open"), awning_bays=(0, 2), name="fandian",
              balconies=((1, 0),), laundry=True, board="#4a241d",
              awn_cols=("#9d3f31", "#d8c7a8"), extra=fandian_extra)
    shophouse(-71, -1, 7.5, 8.5, 2, C["wall_h"], sign="lifa", sign_w=3.6, sign_h=1.2,
              shop=("glass", "door"), roof="tile", awning_bays=(0,), name="lifa",
              awn_cols=("#55707c", "#d7d1bd"), board="#2f3f46", extra=lifa_extra,
              tank=False, antenna_roof=False)
    shophouse(-60, -1, 9, 10, 2, C["wall_i"], sign="zhaoxiang", sign_w=3.7, sign_h=1.32,
              shop=("glass", "door"), name="zhaoxiang", awning_bays=(0,),
              awn_cols=("#7b8a6e", "#ddcfb2"), board="#3b2b24", extra=zhaoxiang_extra)
    shophouse(-46, -1, 12, 11, 2, C["wall_d"], sign="gongxiaoshe", sign_w=5.0, sign_h=1.7,
              shop=("open", "open", "shutter"), name="gongxiaoshe", awning_bays=(0, 1),
              awn_cols=("#5d7059", "#d6c8a9"), board="#3a2d23",
              extra=gongxiaoshe_extra, tank=True)

    # ---------------- south, east side
    shophouse(-120, 1, 10, 10, 3, C["wall_e"], shop=("open", "glass", "shutter"),
              name="se2", style="cement", tank=True, awning_bays=(0,),
              awn_cols=("#8a4a3a", "#d4c6aa"), balconies=((2, 0),), laundry=True)
    shophouse(-105, 1, 8, 9, 2, C["wall_a"], shop=("open", "shutter"), name="se3",
              roof="tile", awning_bays=(0,), awn_cols=("#6b7a63", "#d6cab0"))
    shophouse(-90, 1, 12, 11, 3, C["wall_g"], shop=("shutter", "open", "door"), name="se4",
              style="brick", balconies=((2, 1),), tank=True, awning_bays=(1,),
              awn_cols=("#7d4738", "#d5c6a8"))
    shophouse(-74, 1, 9, 10, 2, C["wall_c"], shop=("glass", "open"), name="se5",
              awning_bays=(1,), awn_cols=("#5c7078", "#d7d0ba"), board="#334640",
              balconies=((1, 0),))
    shophouse(-50, 1, 10, 11, 3, C["wall_b"], sign="shudian", sign_w=4.2, sign_h=1.47,
              shop=("open", "glass", "open"), name="shudian", tank=True,
              awning_bays=(0,), awn_cols=("#5d7059", "#d8ccae"), board="#33463c",
              extra=shudian_extra)
    shophouse(-36, 1, 7, 8, 2, C["wall_h"], shop=("shutter", "glass"), name="se7",
              roof="tile", awning_bays=(1,))

    # ---------------- north, west side
    shophouse(8, -1, 10, 10, 3, C["wall_c"], shop=("open", "shutter", "glass"), name="nw1",
              tank=True, awning_bays=(0,), awn_cols=("#7c4a3a", "#d7c9ad"),
              balconies=((2, 0),), laundry=True)
    shophouse(21, -1, 9, 10, 4, C["wall_i"], sign="lushe", sign_w=3.2, sign_h=1.6,
              shop=("open", "door"), name="lushe", board="#45261f", tank=True,
              balconies=((1, 0), (1, 1), (2, 0), (2, 1), (3, 0), (3, 1)),
              laundry=True, extra=lushe_extra)
    shophouse(35, -1, 8, 9, 2, C["wall_a"], shop=("open", "shutter"), name="nw2",
              roof="tile", awning_bays=(1,), awn_cols=("#6a7a68", "#d5c9ae"))
    shophouse(49, -1, 11, 11, 3, C["wall_f"], shop=("glass", "open", "shutter"), name="nw3",
              style="brick", tank=True, awning_bays=(1,))
    shophouse(64, -1, 9, 10, 2, C["wall_c"], shop=("open", "door"), name="nw4",
              roof="tile", awning_bays=(0,), awn_cols=("#7c4a3a", "#d8cbb0"))
    shophouse(79, -1, 12, 11, 3, C["wall_a"], shop=("open", "glass", "open"), name="nw5",
              style="tile", tank=True, awning_bays=(0, 2), balconies=((2, 1),),
              laundry=True)
    shophouse(112, -1, 10, 10, 3, C["wall_b"], shop=("open", "shutter", "door"), name="nw7",
              balconies=((2, 1),), tank=True, awning_bays=(0,))

    # ---------------- north, east side
    shophouse(7, 1, 11, 10, 2, C["wall_c"], shop=("glass", "open", "shutter"), name="ne1",
              awning_bays=(1,), awn_cols=("#8a4a3a", "#d4c6aa"))
    shophouse(23, 1, 16, 12, 4, C["wall_a"], sign="baihuo", sign_w=5.2, sign_h=1.86,
              shop=("open", "open", "open"), name="baihuo", style="tile", tank=True,
              board="#3a2620", awning_bays=(), extra=baihuo_extra, bays=3)
    shophouse(38, 1, 9, 10, 3, C["wall_h"], shop=("shutter", "open", "glass"), name="ne3",
              style="cement", tank=True, awning_bays=(1,), balconies=((2, 1),),
              laundry=True)
    shophouse(90, 1, 9, 10, 3, C["wall_c"], shop=("glass", "open", "shutter"), name="ne5",
              tank=True, awning_bays=(1,), awn_cols=("#7c4a3a", "#d7c9ad"),
              balconies=((1, 1),), laundry=True)

    # landmark buildings that need their own massing
    cinema_build(69)
    bus_station(110)

    # alleys between buildings
    for (yy, sd) in ((-110.5, -1), (-93.5, -1), (-65.8, -1), (-54.0, -1),
                     (-127.8, 1), (-105.0, 1), (-82.2, 1), (-62.0, 1), (-42.2, 1),
                     (14.8, -1), (41.2, -1), (57.0, -1), (87.9, -1),
                     (13.7, 1), (32.2, 1), (45.0, 1), (98.7, 1), (120.2, 1)):
        alley(yy, sd)


def build_street_furniture():
    P = []
    # street lamps + emissive heads
    lamps = (-118, -92, -66, -40, 16, 42, 66, 94, 122)
    for i, yy in enumerate(lamps):
        street_lamp(P, yy, 1 if i % 2 == 0 else -1, name=f"lamp{i}")
    # power poles down the east side
    pole_ys = (-128, -100, -68, -36, 4, 40, 76, 112)
    pole_pts = []
    for i, yy in enumerate(pole_ys):
        pole_pts.append(power_pole(P, yy, name=f"pp{i}", trans=(i == 2 or i == 5)))
    # wires: three runs with sag
    for i in range(len(pole_pts) - 1):
        x0, y0 = pole_pts[i]
        x1, y1 = pole_pts[i + 1]
        for lev in (0, 1, 2):
            pts = []
            for k in range(9):
                t = k / 8
                xx = x0 + (x1 - x0) * t
                yy = y0 + (y1 - y0) * t
                zz = 7.95 + lev * 0.06 - 1.0 * math.sin(math.pi * t)
                if lev == 1:
                    zz += 0.38
                pts.append((xx + 0.02 * lev, yy, zz))
            wire(P, pts, name="wire")
    # service drops to the east buildings
    tx, ty = street_frame(4)
    nx, ny = ty, -tx
    for yy in (-100, -36, 40, 76):
        x0 = road_x(yy) + nx * 6.4
        y0 = yy + ny * 6.4
        x1 = road_x(yy) + nx * 7.6
        y1 = yy + ny * 7.6
        wire(P, [(x0, y0, 7.4), ((x0 + x1) / 2, (y0 + y1) / 2, 6.6), (x1, y1, 6.1)],
             name="dropwire")
    # cross-street cables with small red pennants
    for yy in (-100, 60):
        x0 = road_x(yy) + nx * 6.4
        y0 = yy + ny * 6.4
        x1 = road_x(yy) - nx * 5.8
        y1 = yy - ny * 5.8
        pts = []
        for k in range(9):
            t = k / 8
            pts.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t,
                        6.9 - 1.1 * math.sin(math.pi * t)))
        wire(P, pts, name="crosswire")
        for k in range(3):
            t = 0.28 + k * 0.22
            px = x0 + (x1 - x0) * t
            py = y0 + (y1 - y0) * t
            pz = 6.9 - 1.1 * math.sin(math.pi * t)
            boxp(P, "pennant", (0.16, 0.02, 0.34), (px, py, pz - 0.2), "#a83a2d", red_cloth,
                 rot=(0, 0, R.uniform(-0.2, 0.2)))
    # benches, postbox, hydrant, bins, tap
    bench(P, *prop_pos(-25.0, -1, 8.6)[:2], rot=prop_pos(-25.0, -1, 8.6)[2] + math.pi,
          name="bench0")
    bench(P, *prop_pos(31.0, 1, 5.9)[:2], rot=prop_pos(31.0, 1, 5.9)[2], name="bench1")
    bench(P, *prop_pos(104.0, 1, 5.9)[:2], rot=prop_pos(104.0, 1, 5.9)[2], name="bench2")
    mailbox(P, *prop_pos(-52.5, 1, 5.95)[:2], rot=prop_pos(-52.5, 1, 5.95)[2])
    hydrant(P, *prop_pos(12.5, 1, 5.95)[:2], rot=prop_pos(12.5, 1, 5.95)[2])
    for yy, sd in ((-114, -1), (28, 1), (86, -1)):
        x, y, rr = prop_pos(yy, sd, 6.3)
        trash_bin(P, x, y)
    x, y, rr = prop_pos(-27.0, 1, 7.6)
    public_tap(P, x, y, rr)
    # parking bay by the department store + hotspot marker
    parking_bay(36.0, 1)
    # two sun-faded banners across the street
    add(cross_banner(-54.0, z=6.15, span=14.5))
    add(cross_banner(82.0, z=6.35, span=14.5, name="banner2"))
    # small layers of wall notices near the bookshop / barber
    for (yy, sd, xo) in ((-54.5, 1, 6.9), (-69.0, -1, 6.95), (44.5, -1, 6.9)):
        tx, ty = street_frame(yy)
        nx, ny = ty, -tx
        x = road_x(yy) + sd * nx * xo
        y2 = yy + sd * ny * xo
        for k in range(3):
            boxp(P, "notice", (0.36, 0.012, 0.5), (x + ty * (k - 1) * 0.42, y2 - tx * (k - 1) * 0.42,
                 1.8 + (k % 2) * 0.1), ["#d6c8a8", "#a8b8ae", "#c28a6c"][k], matte,
                 rot=(0, 0, math.atan2(ty, tx)))
    add(P)


def build_market():
    P = []
    # south promenade: three vegetable stalls + one hot-food stall
    for i, yy in enumerate((-31.0, -28.4, -25.8, -23.2)):
        x, y, rot = prop_pos(yy, -1, 6.05)
        stall(P, x, y, rot, kind=("food" if i == 0 else "veg"), name=f"stall{i}")
    # north promenade, by the bridge
    for i, yy in enumerate((-2.6, 2.9)):
        x, y, rot = prop_pos(yy, -1, 6.05)
        stall(P, x, y, rot, kind=("goods" if i == 2 else "veg"), name=f"nstall{i}")
    # ice-cream kiosk on the east bank
    x, y, rot = prop_pos(-2.0, 1, 5.9)
    kiosk_binggun(P, x, y, rot)
    # watch-repair booth near the department store
    x, y, rot = prop_pos(14.5, 1, 6.1)
    kiosk_xiubiao(P, x, y, rot)
    # moored wooden cargo boat on the canal
    bx = 21.0
    canal_boat(None, bx, canal_cy(bx) + 4.9, math.atan2(canal_slope(bx), 1.0))
    # phone booth and handcart by the night market
    x, y, rot = prop_pos(-6.0, -1, 8.4)
    phone_booth(P, x, y, rot)
    x, y, rot = prop_pos(-24.4, -1, 7.2)
    handcart(P, x, y, rot + 0.35)

    # cargo tricycle + baskets around the market
    x, y, rot = prop_pos(-27.0, -1, 4.7)
    tricycle(P, x, y, rot)
    for i in range(3):
        x, y, rot = prop_pos(-21.0 + i * 0.8, -1, 8.3)
        lathe_basket(P, x, y, 0.2, 0.32, 0.36, name=f"market_basket{i}")
    add(P)


def build_vehicles_street():
    # parked bicycles along the shops
    for i, (yy, sd) in enumerate(((-58.5, 1), (-33.0, 1), (16.5, 1), (88.0, -1), (119.0, 1))):
        x, y, rot = prop_pos(yy, sd, 5.55)
        bicycle(ALL, x, y, rot + math.pi / 2 * sd, col=["#3f5a55", "#7a4a3c", "#4d5560"][i % 3],
                name=f"streetbike{i}")
    # a couple of delivery bikes leaned near the food stalls
    x, y, rot = prop_pos(-23.6, -1, 4.9)
    bicycle(ALL, x, y, rot + 1.25, col="#5f5c4e", name="marketbike")


def build_background():
    # back lanes behind both shop rows
    P = []
    for sd in (-1, 1):
        pts = []
        for yy in range(-146, 147, 4):
            tx, ty = street_frame(yy)
            nx, ny = ty, -tx
            pts.append((road_x(yy) + sd * nx * 29.5, yy + sd * ny * 29.5))
        P.append(B.road_ribbon("backlane", pts, 4.0, "#898273", rough, z=0.06, crown=0.02,
                               segments_width=2))
    add(P)
    # low courtyard houses behind the shops
    house_specs = [
        (-132, 1, 0.06), (-105, 1, -0.03), (-72, 1, 0.04), (-46, 1, 0.0),
        (62, 1, -0.02), (96, 1, 0.03), (126, 1, -0.04),
        (-120, -1, 0.03), (-78, -1, 0.05), (-46, -1, 0.0),
        (42, -1, 0.03), (120, -1, -0.01),
    ]
    for i, (yy, sd, dr) in enumerate(house_specs):
        x, y, rot = prop_pos(yy, sd, 36.0)
        back_house(x, y, rot + dr, w=7.0 + (i % 3), d=6.2, floors=2 if i % 4 else 1,
                   wall=["#c8bca2", "#d0c5ad", "#bdb59e", "#c3b393"][i % 4],
                   name=f"bh{i}", courtyard=(i % 3 != 0))
    # factory / water tower / sheds
    factory(64.0, -102.0, 0.08)
    factory(-72.0, 118.0, -1.52)
    wt = []
    water_tower(wt, -60.0, 62.0)
    add(wt)
    # fields
    field_plot(-94.0, -47.0, 26.0, 15.0, 0.03, name="field0")
    field_plot(80.0, -62.0, 22.0, 14.0, -0.04, name="field1")
    field_plot(-88.0, 96.0, 24.0, 14.0, 0.04, name="field2")
    field_plot(52.0, 128.0, 22.0, 13.0, -0.02, name="field3")
    field_plot(62.0, 6.0, 22.0, 12.0, 0.04, name="field4", col1="#8b9a52", col2="#9aa85e")
    # a couple of village ends and orchards
    for i, (xx, yy) in enumerate(((-128, 24), (-118, 86), (122, 26), (126, 84))):
        x, y, rot = prop_pos(yy, 1 if xx > 0 else -1, abs(xx - road_x(yy)) - 4)
        back_house(x, y, rot + R.uniform(-0.1, 0.1), w=6.5, d=5.6, floors=2,
                   wall=["#c8bca2", "#bdb59e"][i % 2], name=f"edgehouse{i}", courtyard=False)


def build_nature():
    P = []
    # street trees in gaps
    for i, (yy, sd) in enumerate(((-122, -1), (-98, 1), (-84, 1), (-36, -1),
                                  (12, 1), (37, -1), (84, -1))):
        street_tree(P, yy, sd, h=4.2 + (i % 3) * 0.5, name=f"stree{i}")
    # willows along the canal
    for i, (xx, sd) in enumerate(((-56, 1), (-44, -1), (-22, 1), (18, -1),
                                  (36, 1))):
        cy = canal_cy(xx)
        sl = canal_slope(xx)
        L = math.hypot(1.0, sl)
        nx, ny = -sl / L, 1.0 / L
        x = xx + nx * sd * 8.9
        y = cy + ny * sd * 8.9
        willow(P, x, y, 0.12, h=5.6 + (i % 3) * 0.6, name=f"willow{i}")
    # background trees
    for i, (xx, yy, hh) in enumerate(((-146, 30, 6.5), (-142, -80, 6.0), (-132, 118, 7.0),
                                      (-108, -120, 6.0), (-96, 12, 5.5), (-80, -86, 6.2),
                                      (-66, 92, 6.0), (-40, 136, 6.5), (-18, -132, 6.0),
                                      (36, 140, 6.4), (54, -124, 6.0), (96, 62, 6.2),
                                      (104, -26, 6.0), (140, 40, 6.4))):
        z = terrain_h(xx, yy)
        if z < 0:
            continue
        paper_tree(P, f"bg_tree{i}", xx, yy, z, hh, hh * 0.52, "#4a6741", "#5b4935")
    # conifers on the hill mounds
    for i, (xx, yy) in enumerate(((-120, 66), (-112, 56), (-126, 54), (-30, 136),
                                  (-24, 140), (110, 106), (118, 98), (102, 108),
                                  (124, -96), (132, -88))):
        conifer(xx, yy, 3.6 + (i % 3) * 1.1, "#3c5438" if i % 2 else "#44603c")
    # shrubs and weeds
    for i in range(26):
        xx = R.uniform(-150, 150)
        yy = R.uniform(-140, 140)
        if abs(xx - road_x(yy)) < 9.0 or abs(yy - canal_cy(xx)) < 12.0:
            continue
        if abs(xx) < 22 and abs(yy) < 140:
            continue
        sph(P, "shrub", R.uniform(0.3, 0.6), (xx, yy, terrain_h(xx, yy) + 0.2),
            ["#557348", "#47653e", "#647a4b"][i % 3], scale=(1.2, 1, 0.7), mx=matte,
            seg=7, rings=4)
    # grass tufts along the quay and back lanes
    pts = []
    for i in range(80):
        xx = R.uniform(-132, 136)
        yy = canal_cy(xx) + R.choice([-1, 1]) * R.uniform(8.4, 9.8)
        if abs(xx - road_x(canal_cy(xx))) < 10:
            continue
        pts.append((xx, yy, 0.2))
    add(B.tufts_mesh("quaygrass", pts, height=0.36, color="#6e7f4c", material=matte, rng=R))
    add(P)


def build_fx():
    # hotspot beside the parked car bay
    x, y, rot = prop_pos(36.0, 1, 3.2)
    B.empty("FX_Hotspot", (x, y, 1.35))
    B.empty("FX_CarSpot", (x, y, 0.02))
    # food-stall steam
    x, y, rot = prop_pos(-28.4, -1, 6.05)
    B.empty("FX_Smoke_1", (x, y, 3.2))
    # restaurant kitchen vent
    cx, cy, rot = frame_at(-86, -1, 7.2, 10)
    vx, vy = xf(cx, cy, rot, 3.2, 2.6)
    B.empty("FX_Smoke_2", (vx, vy, 9.4))
    for i, yy in enumerate((-118, -66, 16, 66, 122)):
        x, y, rot = prop_pos(yy, 1 if i % 2 == 0 else -1, 5.0)
        B.empty(f"FX_Light_{i+1}", (x, y, 6.2))


def build_town():
    build_ground()
    build_street()
    build_shop_row()
    build_street_furniture()
    build_market()
    build_vehicles_street()
    build_background()
    build_nature()
    build_fx()


def smooth_mesh(o):
    if o and o.type == "MESH":
        for p in o.data.polygons:
            p.use_smooth = True
    return o


def build_ground():
    add(B.ground_slab("Base", 320, 300, 9, top=-3.8,
                      colors=("#6f5b42", "#7e674a", "#8a7658", "#5a4a39", "#4b3e31")))
    pts = B.terrain("Terrain", 320, 300, 80, 76, terrain_h, terrain_col, matte,
                    z0=0.0, smooth=True)
    add(pts)


def build_street():
    P = []
    pavement(P)
    canal_water(P)
    canal_walk(P)
    canal_walls(P)
    street_bridge(P)
    footbridge(P)
    headwall(P, -138, 1)
    headwall(P, 141, -1)
    add(P)


def main():
    build_town()
    if os.environ.get("TOWN_STATS"):
        groups = {}
        for o in ALL:
            if not o or not o.data:
                continue
            o.data.calc_loop_triangles()
            key = o.name.split("_")[0].split(".")[0]
            groups[key] = groups.get(key, 0) + len(o.data.loop_triangles)
        for k, v in sorted(groups.items(), key=lambda kv: -kv[1])[:30]:
            print("STAT", k, v)
    print("PREJOIN objects", len(ALL))
    chunks = []
    for i in range(0, len(ALL), 160):
        chunks.extend(B.join_materials("Chunk", ALL[i:i + 160]))
        print("PREJOIN", i, len(chunks))
    print("PREJOIN done", len(chunks))
    B.join_materials("Town", chunks)
    tris = 0
    verts = 0
    for ob in bpy.context.scene.objects:
        if ob.type == "MESH":
            me = ob.data
            me.calc_loop_triangles()
            tris += len(me.loop_triangles)
            verts += len(me.vertices)
    print("TOWN STATS tris=%d verts=%d objs=%d" % (tris, verts, len(bpy.context.scene.objects)))
    B.save_blend(os.path.join(B.ROOT, "assets", "zones", "town.blend"))
    B.export_glb(os.path.join(B.ROOT, "assets", "zones", "town.glb"))
    print("TOWN EXPORTED", os.path.getsize(os.path.join(B.ROOT, "assets", "zones", "town.glb")))


# ------------------------------------------------------------------ the 1990s sedan
def build_car():
    B.reset(1996)
    paint = B.vmat("CarPaint", 0.42, 0.08)
    chrome = B.vmat("CarChrome", 0.24, 0.55)
    rubber = B.vmat("CarRubber", 0.92)
    glassm = B.mat("CarGlass", "#2c4247", rough=0.14, metal=0.25, alpha=1.0)
    trim = B.mat("CarTrim", "#211f1b", rough=0.62)
    interior = B.vmat("CarInterior", 0.88)
    lensw = B.mat("CarLampW", "#efe5c8", rough=0.18, emission="#ffe9bd", emis_strength=0.55)
    lensr = B.mat("CarLampR", "#8f1f1a", rough=0.22, emission="#ff3a2a", emis_strength=0.85)
    plate_m = B.mat("CarPlate", "#ded8c5", rough=0.75)
    wine = "#762b34"
    cream = "#cbbb9c"
    blk = "#26241f"
    tan = "#a58d6b"
    G = {"Paint": [], "Chrome": [], "Glass": [], "Trim": [], "LightW": [],
         "LightR": [], "Plate": [], "Interior": [], "Under": []}

    def bx(g, size, loc, color, mx, bevel=0.0, rot=(0, 0, 0), name="p"):
        G[g].append(B.box(name, size, loc, rot, color=color, material=mx, bevel=bevel))

    def cy(g, r, depth, loc, color, mx, rot=(0, 0, 0), seg=16, r2=None, name="c",
           smooth=True, bevel=0.0):
        G[g].append(B.cylinder(name, r, depth, loc, rot, segments=seg, color=color,
                               material=mx, radius2=r2, smooth=smooth, bevel=bevel))

    def beam(g, p1, p2, w=0.02, color="#cfc9b7", mx=None, name="b"):
        G[g].append(B.beam(name, p1, p2, w, w, color=color, material=mx or chrome))

    def quad(g, corners, color, mx, name="q"):
        G[g].append(B.quad(name, corners, color, mx))

    # ------------------------------------------------ lower body
    stations = [
        (-2.06, 0.710, 0.400, 0.830),
        (-1.99, 0.790, 0.350, 0.870),
        (-1.74, 0.842, 0.300, 0.905),
        (-1.20, 0.850, 0.285, 0.920),
        (0.00, 0.850, 0.285, 0.925),
        (1.00, 0.850, 0.285, 0.925),
        (1.66, 0.838, 0.305, 0.905),
        (1.94, 0.790, 0.340, 0.875),
        (2.06, 0.700, 0.400, 0.830),
    ]
    secs = []
    for (yy, ww, z0, z1) in stations:
        pts = [(-ww * 0.86, z0), (ww * 0.86, z0), (ww, z0 + 0.19), (ww, z1 - 0.07),
               (ww * 0.955, z1), (-ww * 0.955, z1), (-ww, z1 - 0.07), (-ww, z0 + 0.19)]
        secs.append(((0, yy, 0), [(a, b) for a, b in pts]))
    G["Paint"].append(B.loft("lowerbody", secs, color=wine, material=paint, smooth=False))

    # hood, trunk, cowl and shut lines
    bx("Paint", (1.34, 1.14, 0.032), (0, 1.47, 0.932), wine, paint, bevel=0.015)
    bx("Paint", (0.028, 1.06, 0.012), (-0.33, 1.47, 0.949), wine, paint)
    bx("Paint", (0.028, 1.06, 0.012), (0.33, 1.47, 0.949), wine, paint)
    bx("Paint", (1.30, 0.64, 0.03), (0, -1.73, 0.918), wine, paint, bevel=0.015)
    bx("Trim", (1.46, 0.014, 0.009), (0, 1.07, 0.935), blk, trim)
    bx("Trim", (1.36, 0.014, 0.009), (0, -1.64, 0.924), blk, trim)
    bx("Trim", (0.012, 0.92, 0.009), (-0.64, 1.47, 0.936), blk, trim)
    bx("Trim", (0.012, 0.92, 0.009), (0.64, 1.47, 0.936), blk, trim)
    bx("Trim", (1.22, 0.17, 0.028), (0, 0.94, 0.944), blk, trim)
    for k in range(9):
        bx("Trim", (0.09, 0.012, 0.03), (-0.5 + k * 0.125, 0.93, 0.952), "#4a453a", trim)
    for sx in (-1, 1):
        bx("Trim", (0.52, 0.017, 0.014), (sx * 0.28, 1.02, 0.955), blk, trim,
           rot=(0, 0, sx * 0.2))
        bx("Trim", (0.02, 0.1, 0.006), (sx * 0.52, 1.0, 0.958), blk, trim)
    # rocker, side mouldings
    for sx in (-1, 1):
        bx("Trim", (0.014, 2.7, 0.11), (sx * 0.842, 0, 0.335), blk, trim)
        bx("Chrome", (0.016, 2.35, 0.03), (sx * 0.850, 0, 0.60), "#bdb6a2", chrome)
        bx("Trim", (0.018, 2.30, 0.014), (sx * 0.853, 0, 0.58), blk, trim)


    cy("Chrome", 0.055, 0.018, (0.848, -1.50, 0.75), "#b9b2a0", chrome,
       rot=(0, math.pi / 2, 0), seg=10)

    # ------------------------------------------------ greenhouse
    cab = [
        (-1.46, 0.760, 0.945),
        (-1.34, 0.770, 1.065),
        (-1.04, 0.746, 1.365),
        (-0.80, 0.726, 1.452),
        (-0.05, 0.720, 1.462),
        (0.30, 0.722, 1.462),
        (0.56, 0.734, 1.430),
        (0.80, 0.756, 1.150),
        (0.94, 0.775, 0.960),
    ]
    csecs = []
    for (yy, ww, ztop) in cab:
        pts = [(-ww, 0.90), (ww, 0.90), (ww, ztop - 0.055), (ww * 0.86, ztop),
               (-ww * 0.86, ztop), (-ww, ztop - 0.055)]
        csecs.append(((0, yy, 0), [(a, b) for a, b in pts]))
    G["Paint"].append(B.loft("cabin", csecs, color=wine, material=paint, smooth=False))
    # vinyl roof panel
    quad("Paint", [(-0.60, -0.82, 1.4645), (0.60, -0.82, 1.4645),
                   (0.60, 0.30, 1.4645), (-0.60, 0.30, 1.4645)], cream, paint, "roofvinyl")
    bx("Chrome", (0.018, 1.16, 0.018), (-0.605, -0.26, 1.462), "#c9c2ae", chrome)
    bx("Chrome", (0.018, 1.16, 0.018), (0.605, -0.26, 1.462), "#c9c2ae", chrome)
    bx("Chrome", (1.22, 0.02, 0.018), (0, 0.31, 1.462), "#c9c2ae", chrome)
    bx("Chrome", (1.22, 0.02, 0.018), (0, -0.83, 1.462), "#c9c2ae", chrome)
    # drip rails
    for sx in (-1, 1):
        bx("Chrome", (0.014, 1.5, 0.014), (sx * 0.665, -0.28, 1.448), "#a9a28f", chrome)

    # ------------------------------------------------ glazing
    ws = [(-0.625, 0.905, 1.005), (0.625, 0.905, 1.005),
          (0.530, 0.365, 1.435), (-0.530, 0.365, 1.435)]
    ws = [(x, y + 0.012, z + 0.008) for (x, y, z) in ws]
    quad("Glass", ws, "#a9c1bd", glassm, "windshield")
    quad("Trim", [(x, y - 0.02, z) for (x, y, z) in ws], "#1b2627", trim, "ws_back")
    for i in range(4):
        beam("Chrome", ws[i], ws[(i + 1) % 4], 0.024, "#bcb5a2", chrome, "ws_trim")
    for sx in (-1, 1):
        beam("Trim", (sx * 0.64, 0.910, 1.0), (sx * 0.535, 0.36, 1.435), 0.030, blk, trim)
    rw = [(-0.580, -1.415, 1.020), (0.580, -1.415, 1.020),
          (0.500, -0.900, 1.400), (-0.500, -0.900, 1.400)]
    rw = [(x, y - 0.012, z + 0.008) for (x, y, z) in rw]
    quad("Glass", rw, "#9fb4b1", glassm, "rearglass")
    quad("Trim", [(x, y + 0.02, z) for (x, y, z) in rw], "#1b2627", trim, "rw_back")
    for i in range(4):
        beam("Chrome", rw[i], rw[(i + 1) % 4], 0.022, "#bcb5a2", chrome, "rw_trim")
    # side windows, both sides
    for sx in (-1, 1):
        xb = sx * 0.742
        xt = sx * 0.700
        wins = [
            [(xb, 0.880, 1.008), (xb, -0.020, 1.008), (xt, 0.025, 1.432),
             (xt, 0.380, 1.432)],
            [(xb, -0.075, 1.008), (xb, -0.820, 1.008), (xt, -0.765, 1.432),
             (xt, -0.030, 1.432)],
            [(xb, -0.875, 1.012), (xb, -1.090, 1.018), (xt, -1.145, 1.315),
             (xt, -0.830, 1.422)],
        ]
        for j, corners in enumerate(wins):
            quad("Glass", corners, "#a3b8b4", glassm, f"sideglass{sx}{j}")
            quad("Trim", [(x - sx * 0.012, y, z) for (x, y, z) in corners],
                 "#1b2627", trim, f"sideback{sx}{j}")
            for i in range(4):
                beam("Chrome", corners[i], corners[(i + 1) % 4], 0.016, "#b9b2a0", chrome,
                     "sw_trim")
        bx("Trim", (0.018, 0.075, 0.43), (sx * 0.735, -0.055, 1.20), blk, trim)
        beam("Trim", (sx * 0.742, 0.890, 1.005), (sx * 0.700, 0.385, 1.430), 0.026, blk, trim)
        beam("Trim", (sx * 0.742, -0.865, 1.010), (sx * 0.700, -1.150, 1.315), 0.028, blk, trim)
        bx("Chrome", (0.018, 2.64, 0.024), (sx * 0.768, -0.22, 0.955), "#c6bfab", chrome)

    # ------------------------------------------------ doors
    for sx in (-1, 1):
        for yy in (0.0, -0.90):
            bx("Trim", (0.012, 0.014, 0.56), (sx * 0.853, yy, 0.615), blk, trim)
        for yy in (0.10, -0.78):
            bx("Chrome", (0.035, 0.17, 0.045), (sx * 0.858, yy, 0.835), "#c2bba7", chrome,
               bevel=0.006)
            bx("Trim", (0.02, 0.19, 0.017), (sx * 0.862, yy, 0.812), blk, trim)
        cy("Chrome", 0.017, 0.018, (sx * 0.858, 0.06, 0.885), "#cfc8b4", chrome,
           rot=(0, math.pi / 2, 0), seg=8)
        bx("LightW", (0.017, 0.1, 0.045), (sx * 0.856, 1.5, 0.68), "#e0b25e", lensw)
        # hinges hinted inside door shut
        for yy in (0.0, -0.90):
            bx("Trim", (0.008, 0.05, 0.06), (sx * 0.852, yy, 0.5), "#3a362e", trim)

    # ------------------------------------------------ front end
    bx("Paint", (1.72, 0.16, 0.20), (0, 2.10, 0.50), wine, paint, bevel=0.02)
    bx("Chrome", (1.74, 0.1, 0.055), (0, 2.14, 0.59), "#c8c1ad", chrome)
    bx("Trim", (1.64, 0.02, 0.035), (0, 2.195, 0.49), blk, trim)
    for sx in (-1, 1):
        bx("Paint", (0.14, 0.34, 0.2), (sx * 0.83, 1.96, 0.50), wine, paint,
           bevel=0.02, rot=(0, 0, sx * 0.28))
        bx("Chrome", (0.055, 0.055, 0.21), (sx * 0.44, 2.185, 0.53), "#c8c1ad", chrome,
           bevel=0.01)
        bx("LightW", (0.17, 0.018, 0.055), (sx * 0.6, 2.195, 0.6), "#d99a4a", lensw)
    # grille
    bx("Trim", (1.06, 0.05, 0.25), (0, 2.075, 0.735), blk, trim)
    for k in range(6):
        bx("Chrome", (0.98, 0.018, 0.018), (0, 2.105, 0.635 + k * 0.043), "#b8b19d", chrome)
    for k in range(9):
        bx("Chrome", (0.014, 0.016, 0.22), (-0.44 + k * 0.11, 2.107, 0.735), "#8f8a7a", chrome)
    bx("Chrome", (1.0, 0.03, 0.022), (0, 2.106, 0.855), "#c6bfab", chrome)
    for sx in (-1, 1):
        bx("Chrome", (0.032, 0.032, 0.21), (sx * 0.515, 2.106, 0.735), "#c6bfab", chrome)
    cy("Chrome", 0.048, 0.02, (0, 2.109, 0.735), "#cfc8b4", chrome,
       rot=(math.pi / 2, 0, 0), seg=14)
    cy("Paint", 0.03, 0.022, (0, 2.112, 0.735), wine, paint,
       rot=(math.pi / 2, 0, 0), seg=12)
    # headlights
    for sx in (-1, 1):
        bx("Chrome", (0.36, 0.03, 0.2), (sx * 0.61, 2.075, 0.815), "#c6bfab", chrome,
           bevel=0.008)
        bx("LightW", (0.30, 0.022, 0.15), (sx * 0.61, 2.09, 0.815), "#f0e8cc", lensw)
        bx("Chrome", (0.30, 0.026, 0.012), (sx * 0.61, 2.095, 0.815), "#9f9a89", chrome)
        cy("LightW", 0.045, 0.02, (sx * 0.69, 2.095, 0.815), "#e7ddc0", lensw,
           rot=(math.pi / 2, 0, 0), seg=10)
    # front plate
    bx("Trim", (0.52, 0.03, 0.18), (0, 2.207, 0.72), blk, trim)
    bx("Plate", (0.46, 0.012, 0.14), (0, 2.222, 0.72), "#e2dcc8", plate_m)
    for sx in (-0.17, 0.17):
        cy("Trim", 0.011, 0.008, (sx, 2.23, 0.72), blk, trim,
           rot=(math.pi / 2, 0, 0), seg=6)
    bx("Trim", (1.2, 0.06, 0.09), (0, 2.10, 0.335), blk, trim)
    # hood hinges / jets
    for sx in (-1, 1):
        bx("Trim", (0.09, 0.05, 0.012), (sx * 0.45, 1.08, 0.947), "#3a362e", trim)
        cy("Chrome", 0.012, 0.03, (sx * 0.4, 0.95, 0.955), "#9a9585", chrome,
           rot=(math.pi / 2, 0, 0), seg=6)

    # ------------------------------------------------ rear end
    bx("Paint", (1.71, 0.16, 0.20), (0, -2.10, 0.50), wine, paint, bevel=0.02)
    bx("Chrome", (1.74, 0.1, 0.055), (0, -2.14, 0.59), "#c8c1ad", chrome)
    bx("Trim", (1.63, 0.02, 0.035), (0, -2.195, 0.49), blk, trim)
    for sx in (-1, 1):
        bx("Paint", (0.14, 0.34, 0.2), (sx * 0.83, -1.96, 0.50), wine, paint,
           bevel=0.02, rot=(0, 0, -sx * 0.28))
        bx("Chrome", (0.46, 0.03, 0.19), (sx * 0.56, -2.075, 0.80), "#c6bfab", chrome,
           bevel=0.008)
        bx("LightR", (0.4, 0.024, 0.14), (sx * 0.56, -2.09, 0.80), "#b02a1f", lensr)
        bx("LightW", (0.11, 0.026, 0.14), (sx * 0.73, -2.09, 0.80), "#e6dcc0", lensw)
        for k in range(3):
            bx("Trim", (0.34, 0.025, 0.011), (sx * 0.56, -2.094, 0.748 + k * 0.034), blk, trim)
    bx("Chrome", (1.3, 0.022, 0.025), (0, -2.085, 0.9), "#c0b9a5", chrome)
    bx("Trim", (0.52, 0.03, 0.18), (0, -2.207, 0.72), blk, trim)
    bx("Plate", (0.46, 0.012, 0.14), (0, -2.222, 0.72), "#e2dcc8", plate_m)
    for sx in (-0.17, 0.17):
        cy("Trim", 0.011, 0.008, (sx, -2.23, 0.72), blk, trim,
           rot=(math.pi / 2, 0, 0), seg=6)
    cy("Chrome", 0.016, 0.02, (0, -2.085, 0.74), "#cfc8b4", chrome,
       rot=(math.pi / 2, 0, 0), seg=6)
    cy("Chrome", 0.06, 0.018, (0, -2.083, 0.885), "#cfc8b4", chrome,
       rot=(math.pi / 2, 0, 0), seg=10)
    # license lamps
    for sx in (-1, 1):
        bx("LightW", (0.08, 0.02, 0.03), (sx * 0.2, -2.195, 0.8), "#e6dcc0", lensw)
    # exhaust
    cy("Under", 0.035, 0.55, (-0.38, -1.95, 0.24), "#6b6659", rubber,
       rot=(math.pi / 2, 0, 0), seg=8)
    cy("Chrome", 0.045, 0.13, (-0.38, -2.21, 0.24), "#9c9585", chrome,
       rot=(math.pi / 2, 0, 0), seg=8)
    # rear valance + mud flaps + reflectors + bumper bolts
    bx("Trim", (1.3, 0.08, 0.12), (0, -2.09, 0.33), blk, trim)
    for sx in (-1, 1):
        bx("LightR", (0.1, 0.02, 0.05), (sx * 0.74, -2.15, 0.62), "#a3342b", lensr)
        cy("Chrome", 0.018, 0.012, (sx * 0.6, -2.20, 0.5), "#cfc8b4", chrome,
           rot=(math.pi / 2, 0, 0), seg=6)
    for sx in (-1, 1):
        bx("Trim", (0.18, 0.02, 0.16), (sx * 0.78, -1.68, 0.2), blk, trim)

    # mirrors, antenna
    for sx in (-1, 1):
        beam("Trim", (sx * 0.79, 0.86, 1.005), (sx * 0.885, 0.80, 1.03), 0.035, blk, trim)
        bx("Chrome", (0.05, 0.15, 0.1), (sx * 0.9, 0.79, 1.04), "#c2bba7", chrome,
           bevel=0.012)
        bx("Glass", (0.02, 0.12, 0.075), (sx * 0.888, 0.725, 1.04), "#899d9a", glassm)
    cy("Chrome", 0.018, 0.07, (0.66, 1.30, 0.945), "#8e897a", chrome, seg=8)
    beam("Trim", (0.66, 1.30, 0.95), (0.68, 1.09, 1.49), 0.009, "#4a463c", chrome)

    # ------------------------------------------------ interior
    bx("Trim", (1.48, 3.1, 0.03), (0, 0.05, 0.35), "#4a4238", trim)
    bx("Interior", (1.42, 0.4, 0.24), (0, 0.60, 0.84), "#5b4c3c", interior, bevel=0.02)
    bx("Interior", (0.55, 0.2, 0.12), (-0.32, 0.47, 0.945), "#4e4033", interior,
       bevel=0.015)
    for sx in (-0.47, -0.32, -0.17):
        cy("Trim", 0.032, 0.012, (sx, 0.39, 0.951), "#2e2c26", trim,
           rot=(math.pi / 2, 0, 0), seg=8)
    bx("Trim", (0.34, 0.06, 0.1), (0.25, 0.58, 0.87), "#38342c", trim)
    for k in range(3):
        bx("Trim", (0.05, 0.012, 0.03), (0.16 + k * 0.08, 0.548, 0.87), "#80796a", trim)
    # seats with piping + headrests
    for sx in (-1, 1):
        cx = sx * 0.37
        bx("Interior", (0.5, 0.56, 0.15), (cx, 0.02, 0.585), tan, interior, bevel=0.03)
        bx("Interior", (0.48, 0.16, 0.56), (cx, -0.17, 0.86), tan, interior,
           bevel=0.03, rot=(-0.13, 0, 0))
        bx("Interior", (0.27, 0.13, 0.22), (cx, -0.22, 1.25), tan, interior,
           bevel=0.025)
        bx("Interior", (0.05, 0.4, 0.2), (cx + sx * 0.26, -0.06, 0.72), "#8f7a5b", interior)
        beam("Interior", (cx - 0.2, 0.28, 0.64), (cx + 0.2, 0.28, 0.64), 0.012, "#7e6a4e",
             interior)
        beam("Interior", (cx, -0.1, 0.62), (cx, -0.3, 1.12), 0.012, "#8c7859", interior)
    # rear bench, parcel shelf, speakers
    bx("Interior", (1.3, 0.55, 0.15), (0, -0.96, 0.58), tan, interior, bevel=0.03)
    bx("Interior", (1.3, 0.15, 0.48), (0, -1.18, 0.84), tan, interior, bevel=0.03,
       rot=(-0.12, 0, 0))
    for sx in (-0.38, 0.38):
        bx("Interior", (0.3, 0.12, 0.14), (sx, -1.29, 0.98), tan, interior, bevel=0.02)
    bx("Interior", (1.26, 0.3, 0.04), (0, -1.50, 0.9), "#4a4034", trim)
    for sx in (-0.4, 0.4):
        cy("Trim", 0.08, 0.015, (sx, -1.63, 0.925), "#33312a", trim,
           rot=(math.pi / 2, 0, 0), seg=10)
    # console, gear lever, handbrake
    bx("Interior", (0.22, 0.55, 0.22), (0, 0.18, 0.52), "#4c4034", interior, bevel=0.02)
    beam("Trim", (0.0, 0.23, 0.55), (0.02, 0.28, 0.73), 0.02, "#2f2b24", trim)
    G["Trim"].append(B.sphere("gearknob", 0.045, (0.02, 0.28, 0.75), color="#2f2b24",
                              material=trim, segments=8, rings=5))
    beam("Trim", (0.18, 0.35, 0.52), (0.2, 0.05, 0.64), 0.022, "#2f2b24", trim)
    for sx in (-1, 1):
        bx("Interior", (0.02, 2.0, 0.5), (sx * 0.79, 0.0, 0.62), tan, interior)
        bx("Interior", (0.12, 0.46, 0.1), (sx * 0.73, 0.2, 0.67), "#8d7759", interior)
        bx("Chrome", (0.03, 0.12, 0.03), (sx * 0.765, 0.2, 0.76), "#bdb6a2", chrome)
        bx("Interior", (0.18, 0.03, 0.025), (sx * 0.56, -0.26, 1.375), "#9c8768", interior)
    # steering wheel
    steer = []
    for i in range(21):
        a = math.tau * i / 20
        steer.append((-0.34 + 0.17 * math.cos(a), 0.35 + 0.05 * math.sin(a),
                      0.94 + 0.155 * math.sin(a)))
    G["Trim"].append(B.tube("steerwheel", steer, 0.018, "#2f2b24", trim, segments=5,
                            cyclic=True))
    beam("Trim", (-0.34, 0.33, 0.94), (-0.34, 0.42, 0.80), 0.028, "#3a352c", trim)
    for a in (0.2, 2.3, 4.4):
        beam("Trim", (-0.34, 0.40, 0.94),
             (-0.34 + 0.16 * math.cos(a), 0.40, 0.94 + 0.14 * math.sin(a)), 0.012,
             "#413b30", trim)
    # seat belts + buckles
    for sx in (-1, 1):
        beam("Interior", (sx * 0.68, 0.02, 1.36), (sx * 0.2, 0.22, 0.78), 0.035,
             "#b3a789", interior)
        bx("Chrome", (0.06, 0.03, 0.07), (sx * 0.2, 0.24, 0.74), "#b9b19d", chrome)
    for sx in (-0.45, -0.2, 0.1, 0.35):
        bx("Trim", (0.1, 0.03, 0.06), (sx, 0.392, 0.9), "#2c2a24", trim)
    for k in range(3):
        bx("Chrome", (0.07, 0.02, 0.02), (-0.1 + k * 0.1, 0.393, 0.82), "#8f8978", chrome)
    for sx in (-1, 1):
        cy("Chrome", 0.03, 0.03, (sx * 0.765, 0.18, 0.73), "#a9a28f", chrome,
           rot=(0, math.pi / 2, 0), seg=8)
        bx("Chrome", (0.04, 0.12, 0.035), (sx * 0.77, 0.12, 0.74), "#b3ab97", chrome,
           rot=(0, 0, sx * 0.4))
        bx("Chrome", (0.035, 0.13, 0.03), (sx * 0.77, -0.42, 0.76), "#b3ab97", chrome)
    for k in range(4):
        bx("Trim", (0.92, 0.012, 0.008), (0, -1.09 - k * 0.055, 1.18 - k * 0.02),
           "#25231f", trim, rot=(0.6, 0, 0))
    quad("Trim", [(-0.6, 0.43, 1.39), (0.6, 0.43, 1.39), (0.58, 0.395, 1.428),
                  (-0.58, 0.395, 1.428)], "#253b3d", glassm, "tintband")
    # rear view mirror, visors, dome light, headliner
    bx("Trim", (0.24, 0.04, 0.08), (0, 0.52, 1.34), "#2d2a24", trim)
    bx("Glass", (0.2, 0.02, 0.06), (0, 0.505, 1.34), "#8fa4a1", glassm)
    for sx in (-1, 1):
        bx("Interior", (0.36, 0.2, 0.025), (sx * 0.34, 0.45, 1.42), "#9c8768", interior)
    cy("LightW", 0.04, 0.02, (0, -0.35, 1.43), "#f0e3bc", lensw,
       rot=(math.pi / 2, 0, 0), seg=8)
    bx("Interior", (1.16, 1.7, 0.02), (0, -0.35, 1.40), "#c3b493", interior)
    # pedals
    for sx, yy in ((-0.48, 0.82), (-0.3, 0.83), (-0.12, 0.85)):
        bx("Trim", (0.08, 0.1, 0.02), (sx, yy, 0.46), "#33302a", trim, rot=(0.5, 0, 0))

    # ------------------------------------------------ underbody
    bx("Under", (1.5, 3.4, 0.1), (0, 0, 0.26), "#3b3933", rubber)
    cy("Under", 0.035, 1.7, (-0.35, 0.15, 0.21), "#6a6558", rubber,
       rot=(math.pi / 2, 0, 0), seg=6)
    bx("Under", (0.55, 0.4, 0.2), (-0.35, -1.0, 0.22), "#575349", rubber, bevel=0.02)
    cy("Under", 0.035, 0.5, (-0.35, -1.9, 0.205), "#5e594d", rubber,
       rot=(math.pi / 2, 0, 0), seg=6)
    for yy in (-1.32, 1.32):
        cy("Under", 0.045, 1.5, (0, yy, 0.30), "#4d4940", rubber,
           rot=(0, math.pi / 2, 0), seg=8)
    bx("Under", (1.0, 0.55, 0.2), (0, -1.45, 0.36), "#4a463d", rubber)
    for sx in (-1, 1):
        for yy in (-1.32, 1.32):
            beam("Under", (sx * 0.62, yy, 0.3), (sx * 0.8, yy + 0.35, 0.45), 0.035,
                 "#5a5549", rubber)
            beam("Under", (sx * 0.62, yy, 0.3), (sx * 0.8, yy - 0.35, 0.45), 0.032,
                 "#5a5549", rubber)
    # driveshaft + coil springs + shocks
    cy("Under", 0.03, 1.4, (0, 0.3, 0.22), "#5b564a", rubber,
       rot=(math.pi / 2, 0, 0), seg=6)
    for sx in (-1, 1):
        for yy in (-1.25, 1.3):
            pts = []
            for k in range(15):
                a = math.tau * k / 6
                pts.append((sx * 0.6 + 0.11 * math.cos(a),
                            yy + 0.11 * math.sin(a),
                            0.28 + 0.028 * k))
            G["Under"].append(B.tube("coil", pts, 0.018, "#6b6658", rubber, segments=4))
            cy("Under", 0.035, 0.24, (sx * 0.66, yy + 0.16, 0.5), "#5d584c", rubber,
               rot=(0.25, 0, 0), seg=6)
    cy("Under", 0.018, 1.3, (0, -1.15, 0.22), "#777164", chrome,
       rot=(0, math.pi / 2, 0), seg=6)
    G["Under"].append(B.tube("brakeline", [(-0.55, 1.25, 0.2), (-0.62, 0.1, 0.18),
                                          (-0.6, -1.1, 0.2), (-0.3, -1.3, 0.24)],
                            0.012, "#6b6659", rubber, segments=4))

    # ------------------------------------------------ wheel arches
    def arch(sx, yc, r_in, r_out, color, mx, xoff, n=14, name="arch", g="Paint"):
        verts, faces = [], []
        for i in range(n + 1):
            a = math.pi * i / n
            verts.append((sx * xoff, yc + r_out * math.cos(a), 0.30 + r_out * math.sin(a)))
            verts.append((sx * xoff, yc + r_in * math.cos(a), 0.30 + r_in * math.sin(a)))
        for i in range(n):
            a = i * 2
            faces.append((a, a + 1, a + 3, a + 2))
        G[g].append(B._finish(name, verts, faces, color, mx, smooth=False))

    for sx in (-1, 1):
        for yy in (-1.32, 1.32):
            # dark well behind the tyre
            verts, faces = [], []
            verts.append((sx * 0.848, yy, 0.30))
            for i in range(15):
                a = math.pi * i / 14
                verts.append((sx * 0.848, yy + 0.345 * math.cos(a),
                              0.30 + 0.345 * math.sin(a)))
            for i in range(14):
                faces.append((0, i + 1, i + 2))
            G["Trim"].append(B._finish("well", verts, faces, "#1f1d1a", trim,
                                       smooth=False))
            arch(sx, yy, 0.348, 0.395, wine, paint, 0.855, n=16, name="archlip")
            arch(sx, yy, 0.395, 0.402, "#3a3630", trim, 0.856, n=16, name="archseam", g="Trim")

    # ------------------------------------------------ wheels
    wheel_objs = []

    def make_wheel(sx, yy, label):
        W = []
        tire = B.lathe("tire",
                       [(0.175, -0.100), (0.240, -0.112), (0.285, -0.090),
                        (0.300, -0.040), (0.303, 0.000), (0.300, 0.040),
                        (0.285, 0.090), (0.240, 0.112), (0.175, 0.100)],
                       loc=(sx * 0.735, yy, 0.303), rot=(0, math.pi / 2, 0),
                       segments=28, color="#33312c", material=rubber, smooth=True)
        W.append(tire)
        # tread blocks
        for k in range(36):
            a = math.tau * k / 36
            W.append(B.box(f"tread{k}", (0.20, 0.016, 0.055),
                           (sx * 0.735, yy + 0.296 * math.cos(a), 0.303 + 0.296 * math.sin(a)),
                           (a, 0, 0), color="#2c2a26", material=rubber))
        rim = B.cylinder("rim", 0.188, 0.15, (sx * 0.735, yy, 0.303), (0, math.pi / 2, 0),
                         segments=24, color="#8e8a7c", material=chrome, smooth=True)
        W.append(rim)
        lip = []
        for k in range(25):
            a = math.tau * k / 24
            lip.append((sx * 0.812, yy + 0.18 * math.cos(a), 0.303 + 0.18 * math.sin(a)))
        W.append(B.tube("rimlip", lip, 0.012, "#c3bca8", chrome, segments=4, cyclic=True))
        hub = B.lathe("hubcap",
                      [(0.03, 0.0), (0.075, 0.008), (0.112, 0.03), (0.128, 0.055),
                       (0.120, 0.072)],
                      loc=(sx * 0.812, yy, 0.303), rot=(0, sx * math.pi / 2, 0),
                      segments=24, color="#cfc8b4", material=chrome, smooth=True)
        W.append(hub)
        for k in range(5):
            a = math.tau * k / 5 + 0.3
            W.append(B.box("hubspoke", (0.014, 0.028, 0.1),
                           (sx * 0.828, yy + 0.07 * math.cos(a), 0.303 + 0.07 * math.sin(a)),
                           (a - math.pi / 2, 0, 0), color="#a9a38e", material=chrome))
            W.append(B.cylinder("lug", 0.016, 0.02,
                                (sx * 0.833, yy + 0.099 * math.cos(a), 0.303 + 0.099 * math.sin(a)),
                                (0, sx * math.pi / 2, 0), segments=6,
                                color="#b5ae9a", material=chrome, smooth=True))
        W.append(B.cylinder("badge", 0.032, 0.01, (sx * 0.834, yy, 0.303),
                            (0, sx * math.pi / 2, 0), segments=12, color="#7a2a31",
                            material=chrome, smooth=True))
        W.append(B.cylinder("disc", 0.15, 0.025, (sx * 0.695, yy, 0.303),
                            (0, math.pi / 2, 0), segments=16, color="#6b6659",
                            material=chrome, smooth=True))
        for k, off in enumerate((-0.05, 0.0, 0.05)):
            ring = []
            for j in range(29):
                a = math.tau * j / 28
                ring.append((sx * 0.735 + off, yy + 0.298 * math.cos(a),
                             0.303 + 0.298 * math.sin(a)))
            W.append(B.tube("treadgroove", ring, 0.009, "#211f1c", rubber,
                            segments=4, cyclic=True))
        sw = []
        for j in range(25):
            a = math.tau * j / 24
            sw.append((sx * 0.842, yy + 0.23 * math.cos(a), 0.303 + 0.23 * math.sin(a)))
        W.append(B.tube("sidewall", sw, 0.006, "#cbc4ae", rubber, segments=4, cyclic=True))
        # top mud shield inside the arch
        guard = []
        for i in range(7):
            a = math.pi * i / 6
            guard.append((sx * 0.80, yy + 0.33 * math.cos(a), 0.303 + 0.33 * math.sin(a)))
        W.append(B.tube("wheelguard", guard, 0.02, "#2b2924", rubber, segments=4))
        final = B.join_group(f"Wheel_{label}", W)
        wheel_objs.append(final)

    make_wheel(-1, 1.32, "FL")
    make_wheel(1, 1.32, "FR")
    make_wheel(-1, -1.32, "RL")
    make_wheel(1, -1.32, "RR")

    # ------------------------------------------------ join/export
    body_objs = []
    for key, lst in G.items():
        if lst:
            body_objs.append(B.join_group("Car_" + key, lst))
    root = B.empty("Car", (0, 0, 0))
    for ob in body_objs + wheel_objs:
        ob.parent = root
        ob.matrix_parent_inverse = root.matrix_world.inverted()
    tris = 0
    mn = [9, 9, 9]
    mx = [-9, -9, -9]
    for ob in bpy.context.scene.objects:
        if ob.type == "MESH":
            me = ob.data
            me.calc_loop_triangles()
            tris += len(me.loop_triangles)
            for v in me.vertices:
                w = ob.matrix_world @ v.co
                for i in range(3):
                    mn[i] = min(mn[i], w[i])
                    mx[i] = max(mx[i], w[i])
    print("CAR STATS tris=%d objs=%d bbox=%s..%s" % (tris, len(bpy.context.scene.objects),
                                                    [round(v, 3) for v in mn],
                                                    [round(v, 3) for v in mx]))
    B.save_blend(os.path.join(B.ROOT, "assets", "vehicles", "car.blend"))
    B.export_glb(os.path.join(B.ROOT, "assets", "vehicles", "car.glb"),
                 objects=[root] + body_objs + wheel_objs)
    print("CAR EXPORTED", os.path.getsize(os.path.join(B.ROOT, "assets", "vehicles", "car.glb")))


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["town"]
    if args and args[0] == "car":
        build_car()
    else:
        main()
