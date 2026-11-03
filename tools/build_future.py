"""第五幕 · 星河港 / 2035+ future island and heavy-lift rocket.
Original procedural geometry; no downloaded models, textures or images.

Usage:
  blender -b --factory-startup --python tools/build_future.py -- --only rocket
  blender -b --factory-startup --python tools/build_future.py -- --only zone
  blender -b --factory-startup --python tools/build_future.py -- --only all
"""
from __future__ import annotations

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
import blib as B  # noqa: E402

SEED = 2035
ROOT = B.ROOT
ZONE_BLEND = os.path.join(ROOT, "assets", "zones", "future.blend")
ZONE_GLB = os.path.join(ROOT, "assets", "zones", "future.glb")
ROCKET_BLEND = os.path.join(ROOT, "assets", "vehicles", "rocket.blend")
ROCKET_GLB = os.path.join(ROOT, "assets", "vehicles", "rocket.glb")

# =====================================================================
#  shared helpers
# =====================================================================

def srgb(h):
    return B.srgb(h)


def sstep(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3.0 - 2.0 * t)


def clamp01(x):
    return max(0.0, min(1.0, x))


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


def fbm(x, y, seed=0, octaves=3):
    total, amp, norm = 0.0, 1.0, 0.0
    for o in range(octaves):
        total += vnoise(x * (2 ** o), y * (2 ** o), seed + o) * amp
        norm += amp
        amp *= 0.52
    return total / norm


def flat_ring(name, z, r_in, r_out, seg=40, cx=0.0, cy=0.0,
              color="#ffffff", material=None, rot=0.0):
    """A one-sided annulus lying in the XY plane."""
    verts, faces = [], []
    for i in range(seg):
        a = math.tau * i / seg
        verts.append((cx + r_in * math.cos(a), cy + r_in * math.sin(a), z))
    for i in range(seg):
        a = math.tau * i / seg
        verts.append((cx + r_out * math.cos(a), cy + r_out * math.sin(a), z))
    for i in range(seg):
        j = (i + 1) % seg
        faces.append((i, j, seg + j, seg + i))
    ob = B._finish(name, verts, faces, color, material, smooth=False)
    if rot:
        B.apply_xform([ob], (0, 0, 0), rot)
    return ob


def ring_poly(name, outer_loop, inner_loop, color, material, flip=False):
    """Closed ring between two equal-length 3D loops."""
    verts = list(outer_loop) + list(inner_loop)
    n = len(outer_loop)
    faces = []
    for i in range(n):
        j = (i + 1) % n
        if flip:
            faces.append((i, n + i, n + j, j))
        else:
            faces.append((i, j, n + j, n + i))
    return B._finish(name, verts, faces, color, material, smooth=False)


def loft_rings(name, rings, color, material, smooth=True, cap_bottom=True,
               cap_top=True, face_colors=None):
    """rings: list of equal-length lists of (x, y, z); rings bottom to top."""
    verts, faces = [], []
    idx = []
    for ring in rings:
        cur = []
        for p in ring:
            cur.append(len(verts))
            verts.append(p)
        idx.append(cur)
    n = len(rings[0])
    for k in range(len(idx) - 1):
        A, B_ = idx[k], idx[k + 1]
        for i in range(n):
            j = (i + 1) % n
            faces.append((A[i], A[j], B_[j], B_[i]))
    if cap_bottom:
        faces.append(tuple(reversed(idx[0])))
    if cap_top:
        faces.append(tuple(idx[-1]))
    ob = B._finish(name, verts, faces, color, material, smooth=smooth,
                   face_colors=face_colors)
    nside = n * (len(idx) - 1)
    for i, p in enumerate(ob.data.polygons):
        p.use_smooth = smooth and i < nside
    return ob


def ellipse_loop(cx, cy, z, rx, ry, n=24, rot=0.0, shape=0.0, wave=0.0, phase=0.0):
    """Elliptical loop. shape>0 gives a rounded-triangle / leaf plan."""
    pts = []
    for i in range(n):
        a = math.tau * i / n
        rr = 1.0 + shape * math.cos(3 * a + phase) + wave * math.sin(5 * a + phase)
        x = rx * rr * math.cos(a)
        y = ry * rr * math.sin(a)
        xr = x * math.cos(rot) - y * math.sin(rot)
        yr = x * math.sin(rot) + y * math.cos(rot)
        pts.append((cx + xr, cy + yr, z))
    return pts


def rounded_loop(cx, cy, z, w, d, r=2.0, n=8, rot=0.0):
    """Rounded rectangle loop, n points per corner arc."""
    pts = []
    hw, hd = w / 2 - r, d / 2 - r
    corners = [(hw, hd, 0), (-hw, hd, math.pi / 2), (-hw, -hd, math.pi),
               (hw, -hd, math.pi * 1.5)]
    for (ccx, ccy, base) in corners:
        for i in range(n):
            a = base + (math.pi / 2) * i / n
            pts.append((ccx + r * math.cos(a), ccy + r * math.sin(a), z))
    out = []
    for (x, y, _zz) in pts:
        xr = x * math.cos(rot) - y * math.sin(rot)
        yr = x * math.sin(rot) + y * math.cos(rot)
        out.append((cx + xr, cy + yr, z))
    return out


def sweep_profile(name, pts, profile, color, material, closed_path=False,
                  smooth=False, face_colors=None):
    """Extrude a closed 2D profile (lateral, vertical) along a 3D polyline."""
    verts, faces = [], []
    n = len(pts)
    m = len(profile)
    for i, (x, y, z) in enumerate(pts):
        if i == 0:
            dx, dy = pts[1][0] - x, pts[1][1] - y
        elif i == n - 1:
            dx, dy = x - pts[-2][0], y - pts[-2][1]
        else:
            dx, dy = pts[i + 1][0] - pts[i - 1][0], pts[i + 1][1] - pts[i - 1][1]
        L = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / L, dx / L
        for (u, v) in profile:
            verts.append((x + nx * u, y + ny * u, z + v))
    for k in range(n - 1):
        A = k * m
        B_ = (k + 1) * m
        for i in range(m):
            j = (i + 1) % m
            faces.append((A + i, A + j, B_ + j, B_ + i))
    if not closed_path:
        faces.append(tuple(reversed(range(m))))
        faces.append(tuple(range((n - 1) * m, n * m)))
    ob = B._finish(name, verts, faces, color, material, smooth=smooth,
                   face_colors=face_colors)
    return ob


def catmull(points, samples=6, closed=False):
    """Smooth polyline (2D or 3D tuples)."""
    p = [tuple(pt) for pt in points]
    if closed:
        p = [p[-1]] + p + [p[0], p[1]]
    else:
        p = [p[0]] + p + [p[-1]]
    out = []
    segs = len(p) - 3
    for i in range(segs):
        p0, p1, p2, p3 = p[i], p[i + 1], p[i + 2], p[i + 3]
        for k in range(samples):
            t = k / samples
            t2, t3 = t * t, t * t * t
            pt = []
            for d in range(len(p1)):
                v = 0.5 * ((2 * p1[d]) + (-p0[d] + p2[d]) * t +
                           (2 * p0[d] - 5 * p1[d] + 4 * p2[d] - p3[d]) * t2 +
                           (-p0[d] + 3 * p1[d] - 3 * p2[d] + p3[d]) * t3)
                pt.append(v)
            out.append(tuple(pt))
    out.append(tuple(p[-2]))
    if closed:
        out = out[:-1]
    return out


def path_z(points, z0, z1=None):
    """add z to 2D points, optionally lerping along length."""
    if z1 is None:
        return [(x, y, z0) for (x, y) in points]
    total = 0.0
    lens = [0.0]
    for i in range(1, len(points)):
        total += math.hypot(points[i][0] - points[i - 1][0], points[i][1] - points[i - 1][1])
        lens.append(total)
    out = []
    for (x, y), L in zip(points, lens):
        t = L / max(total, 1e-6)
        out.append((x, y, z0 + (z1 - z0) * t))
    return out


def box(name, size, loc, color, material, rot=(0, 0, 0), bevel=0.0):
    return B.box(name, size, loc, rot=rot, color=color, material=material, bevel=bevel)


def beam(name, p1, p2, w, h, color, material):
    return B.beam(name, p1, p2, w, h, color, material)


def disc_quad(name, center, normal_angle, w, h, color, material, zoff=0.0):
    """Vertical quad facing outward at angle on a cylinder (center is x,y,z)."""
    cx, cy, cz = center
    tx, ty = -math.sin(normal_angle), math.cos(normal_angle)
    hw, hh = w / 2, h / 2
    verts = [(cx - tx * hw, cy - ty * hw, cz - hh + zoff),
             (cx + tx * hw, cy + ty * hw, cz - hh + zoff),
             (cx + tx * hw, cy + ty * hw, cz + hh + zoff),
             (cx - tx * hw, cy - ty * hw, cz + hh + zoff)]
    return B._finish(name, verts, [(0, 1, 2, 3)], color, material, smooth=False)


# =====================================================================
#  ROCKET
# =====================================================================

RC = {
    "white": "#eeeade",
    "white2": "#e2ddcf",
    "cream": "#f5f1e6",
    "dark": "#3a3e43",
    "dark2": "#2b2e32",
    "grey": "#8a8c88",
    "titan": "#6f6a5f",
    "gold": "#b98a4c",
    "copper": "#9c6644",
    "nozzle": "#5a4b3b",
    "glow": "#8fe6ff",
    "warm": "#ffc27a",
}


def rocket_materials():
    return {
        "white": B.vmat("R_Shell", 0.58),
        "metal": B.vmat("R_Metal", 0.34, 0.55),
        "dark": B.vmat("R_Dark", 0.46, 0.3),
        "gold": B.vmat("R_Gold", 0.32, 0.8),
        "nozzle": B.vmat("R_Nozzle", 0.44, 0.65),
        "glow": B.mat("R_Glow", "#a7ecff", rough=0.5, emission="#7fe2ff", emis_strength=2.4),
        "warm": B.mat("R_Warm", "#ffd6a0", rough=0.5, emission="#ffb765", emis_strength=1.8),
    }


def nozzle(name, cx, cy, zexit, r_exit, r_throat, length, segs=24, M=None):
    obs = []
    prof = []
    rings = 13
    for i in range(rings):
        t = i / (rings - 1)
        r = r_exit + (r_throat - r_exit) * (t ** 1.65)
        r += 0.014 * math.sin(t * math.pi * 8.0) * (1 - t * 0.4)
        z = 0.13 + length * t
        prof.append((max(0.06, r), z))
    prof.insert(0, (r_exit * 0.62, 0.015))
    prof.insert(1, (r_exit + 0.045, 0.055))
    prof.insert(2, (r_exit * 0.99, 0.13))
    obs.append(B.lathe(name + "_bell", prof, loc=(cx, cy, zexit), segments=segs,
                       color=RC["nozzle"], material=M["nozzle"]))
    # dark throat disc to read as a hollow bell
    obs.append(B.cylinder(name + "_throat", r_exit * 0.78, 0.06,
                          (cx, cy, zexit + 0.09), segments=segs,
                          color="#211d19", material=M["dark"], smooth=False))
    # gimbal / injector head
    obs.append(B.cylinder(name + "_gimbal", r_throat * 1.25, 0.46,
                          (cx, cy, zexit + length + 0.1), segments=14,
                          color=RC["titan"], material=M["metal"]))
    for i in range(3):
        a = math.tau * i / 3 + 0.3
        obs.append(B.box(name + f"_act{i}", (0.09, 0.09, 0.55),
                         (cx + math.cos(a) * r_exit * 0.72, cy + math.sin(a) * r_exit * 0.72,
                          zexit + length * 0.45),
                         color="#4b463d", material=M["metal"]))
    return obs


def grid_fin(name, cx, cy, z, angle, base_r, width=1.6, height=2.2,
             depth=0.30, M=None, cells_x=4, cells_y=3):
    """Lattice fin; built local +X radial, then rotated/translated."""
    obs = []
    rad = base_r
    cxo = rad + depth * 0.5 + 0.12
    # frame
    obs.append(B.box(name + "_fT", (depth, width, 0.15), (cxo, 0, z + height / 2),
                     color="#716c60", material=M["metal"]))
    obs.append(B.box(name + "_fB", (depth, width, 0.15), (cxo, 0, z - height / 2),
                     color="#716c60", material=M["metal"]))
    obs.append(B.box(name + "_fL", (depth, 0.15, height), (cxo, width / 2, z),
                     color="#716c60", material=M["metal"]))
    obs.append(B.box(name + "_fR", (depth, 0.15, height), (cxo, -width / 2, z),
                     color="#716c60", material=M["metal"]))
    for i in range(1, cells_y + 1):
        yy = -width / 2 + width * i / (cells_y + 1)
        obs.append(B.box(name + f"_h{i}", (depth * 0.72, width, 0.055),
                         (cxo, yy, z), color="#807a6c", material=M["metal"]))
    for i in range(1, cells_x + 1):
        zz = -height / 2 + height * i / (cells_x + 1)
        obs.append(B.box(name + f"_v{i}", (depth * 0.72, 0.055, height),
                         (cxo, 0, z + zz), color="#807a6c", material=M["metal"]))
    # mount arm into the body
    obs.append(B.box(name + "_mount", (0.7, 0.44, 0.62), (rad + 0.26, 0, z),
                     color="#4c4941", material=M["metal"]))
    B.apply_xform(obs, (cx, cy, 0), angle)
    return obs


def rivet_ring(name, z, r, n, size, color, M, angle=0.0):
    obs = []
    for i in range(n):
        a = math.tau * i / n + angle
        obs.append(B.box(name + f"_{i}", (size, size * 0.8, size * 0.55),
                         (r * math.cos(a), r * math.sin(a), z),
                         rot=(0, 0, a), color=color, material=M["metal"]))
    return obs


def rocket():
    B.reset(SEED + 7)
    rng = random.Random(SEED + 7)
    M = rocket_materials()
    ALL = []

    def add(o):
        if isinstance(o, (list, tuple)):
            for q in o:
                add(q)
        elif o is not None:
            ALL.append(o)

    SEG = 64
    R = 2.6
    # ------------------------------------------------------------------ core
    # aft skirt / thrust structure
    add(B.lathe("CoreAft", [(2.68, 3.38), (2.66, 3.7), (2.62, 4.1),
                            (2.6, 4.55), (2.5, 4.7), (2.3, 4.78)],
                segments=SEG, color=RC["dark"], material=M["dark"]))
    add(flat_ring("CoreHeatShield", 3.46, 1.86, 2.64, SEG, color="#2f2a25", material=M["dark"]))
    for i in range(12):
        a = math.tau * i / 12
        add(B.box("CoreHeatRib", (1.0, 0.16, 0.18),
                  ((2.2) * math.cos(a), (2.2) * math.sin(a), 3.4),
                  rot=(0, 0, a), color="#494039", material=M["dark"]))
    for i in range(6):
        a = math.tau * i / 6 + 0.26
        add(B.cylinder("AftStrut", 0.12, 2.1,
                       (2.5 * math.cos(a), 2.5 * math.sin(a), 3.3), segments=8,
                       color="#6b6254", material=M["metal"]))

    # main tank: white with faint warm panel variation, 3 lathe bands
    tank_prof = [(2.6, 4.62), (2.63, 5.05), (2.6, 6.2), (2.6, 10.0),
                 (2.605, 14.0), (2.6, 18.0), (2.61, 22.0), (2.6, 26.0),
                 (2.6, 29.4), (2.58, 29.9), (2.5, 30.1)]
    add(B.lathe("CoreTank", tank_prof, segments=SEG, color=RC["white"], material=M["white"]))
    # vertical weld & panel seams
    for i in range(10):
        a = math.tau * i / 10 + 0.12
        add(B.cylinder("CoreSeam", 0.022, 25.0,
                       (2.615 * math.cos(a), 2.615 * math.sin(a), 17.3),
                       segments=6, color="#cfc9bb", material=M["white"]))
    add(flat_ring("CoreBand1", 10.02, 2.585, 2.622, SEG, color=RC["grey"], material=M["white"]))
    add(flat_ring("CoreBand2", 19.02, 2.585, 2.622, SEG, color=RC["grey"], material=M["white"]))
    add(flat_ring("CoreBand3", 27.02, 2.585, 2.622, SEG, color=RC["grey"], material=M["white"]))
    add(flat_ring("CoreGold", 30.05, 2.575, 2.615, SEG, color=RC["gold"], material=M["gold"]))
    add(flat_ring("CoreAurora", 23.55, 2.585, 2.618, SEG, color="#5f9297", material=M["white"]))
    add(flat_ring("CoreAurora2", 24.25, 2.585, 2.618, SEG, color="#5f9297", material=M["white"]))
    # pale service walkway strip on the shade side
    for i in range(7):
        add(B.box("CoreWalk", (0.42, 0.26, 0.16),
                  (2.60 * math.cos(2.35), 2.60 * math.sin(2.35), 7.0 + i * 3.2),
                  rot=(0, 0, 2.35), color="#9d998d", material=M["metal"]))
    # bolts around panel joints
    for z in (6.0, 14.0, 22.0, 28.8):
        add(rivet_ring("CoreBolt", z, 2.635, 44, 0.075, "#b8b2a2", M, angle=0.02))

    # raceway / conduits on +X side (faces the service tower)
    for k, (aa, rr, ww) in enumerate([(0.16, 0.11, 0.16), (0.30, 0.08, 0.11)]):
        add(B.box(f"CoreRaceway{k}", (ww, ww, 25.6),
                  (2.66 * math.cos(aa), 2.66 * math.sin(aa), 17.2),
                  rot=(0, 0, aa), color="#a8a295", material=M["white"]))
        for i in range(7):
            z = 6.0 + i * 3.9
            add(B.box(f"RaceClamp{k}_{i}", (ww + 0.14, ww + 0.13, 0.13),
                      (2.665 * math.cos(aa), 2.665 * math.sin(aa), z),
                      rot=(0, 0, aa), color="#6d6961", material=M["metal"]))
    # umbilical plates & sockets (tower side)
    for i, z in enumerate((8.4, 16.6, 24.6, 34.8)):
        add(B.box(f"UmbPlate{i}", (0.12, 1.24, 1.5),
                  (2.67, 0.0, z), color="#6c6a63", material=M["metal"]))
        add(B.box(f"UmbInner{i}", (0.16, 0.9, 1.1),
                  (2.72, 0.0, z), color="#3c3f41", material=M["dark"]))
        for j in range(3):
            add(B.cylinder(f"UmbPlug{i}_{j}", 0.09, 0.28, (2.82, -0.34 + j * 0.34, z),
                           rot=(0, math.pi / 2, 0), segments=8,
                           color=RC["gold"], material=M["gold"]))
    # interstage
    add(B.lathe("CoreInterstage", [(2.58, 30.0), (2.62, 30.2), (2.62, 33.3),
                                   (2.55, 33.55), (2.42, 33.65)],
                segments=SEG, color=RC["dark"], material=M["dark"]))
    for i in range(8):
        a = math.tau * i / 8
        add(B.box("InterRib", (0.19, 0.34, 3.0), (2.6 * math.cos(a), 2.6 * math.sin(a), 31.8),
                  rot=(0, 0, a), color="#55585a", material=M["metal"]))
    for i in range(4):
        a = math.tau * i / 4 + math.pi / 4
        add(nozzle("SepMotor", 2.36 * math.cos(a), 2.36 * math.sin(a), 33.35,
                   0.20, 0.11, 0.72, segs=12, M=M))
    # grid fins on interstage
    for i in range(4):
        a = math.tau * i / 4 + math.pi / 4
        add(grid_fin(f"CoreGridFin{i}", 0, 0, 32.0, a, 2.6, 1.75, 2.3, 0.3, M))
    # upper stage
    add(B.lathe("UpperStage", [(2.52, 33.55), (2.58, 33.9), (2.58, 36.4),
                               (2.57, 40.0), (2.56, 43.0), (2.52, 44.1)],
                segments=SEG, color=RC["white2"], material=M["white"]))
    add(flat_ring("UpperGold", 33.95, 2.545, 2.60, SEG, color=RC["gold"], material=M["gold"]))
    add(flat_ring("UpperCyan", 42.7, 2.50, 2.55, SEG, color="#6fb9c4", material=M["white"]))
    for i in range(4):
        a = math.tau * i / 4 + 0.39
        add(B.box("RCSPod", (0.5, 0.82, 0.7), (2.45 * math.cos(a), 2.45 * math.sin(a), 41.1),
                  rot=(0, 0, a), color="#c9c5b8", material=M["white"]))
        for j in range(2):
            add(B.cylinder("RCSJet", 0.07, 0.24,
                           (2.72 * math.cos(a) + (j - .5) * .3 * -math.sin(a),
                            2.72 * math.sin(a) + (j - .5) * .3 * math.cos(a), 41.45),
                           rot=(math.pi / 2, 0, a), segments=6,
                           color="#5d5950", material=M["metal"]))
    add(rivet_ring("UpperBolt", 36.5, 2.60, 40, 0.06, "#b8b2a2", M))
    # folded service / umbilical arms on tower side
    for i, (z, ln) in enumerate([(36.4, 1.35), (40.2, 1.15)]):
        add(B.box(f"FoldArm{i}", (ln, 0.34, 0.34), (2.62 + ln / 2, 0.9, z),
                  color="#d8d3c5", material=M["white"]))
        add(B.box(f"FoldArmHinge{i}", (0.3, 0.44, 0.44), (2.62, 0.9, z),
                  color="#6b6a62", material=M["metal"]))
        add(B.box(f"FoldArmTip{i}", (0.22, 0.5, 0.5), (2.62 + ln, 0.9, z),
                  color=RC["gold"], material=M["gold"]))
        add(B.cylinder(f"FoldCable{i}", 0.035, ln * 0.95,
                       (2.62 + ln / 2, 0.58, z - 0.2), rot=(0, math.pi / 2, 0),
                       segments=5, color="#3d3b37", material=M["dark"]))
    # fairing
    fair = [(2.52, 44.05), (2.61, 44.3), (2.63, 45.4), (2.6, 46.8),
            (2.50, 48.4), (2.34, 50.0), (2.13, 51.6), (1.86, 53.2),
            (1.54, 54.8), (1.17, 56.3), (0.78, 57.7), (0.4, 58.9),
            (0.14, 59.7), (0.035, 60.0)]
    add(B.lathe("Fairing", fair, segments=SEG, color=RC["cream"], material=M["white"]))
    add(flat_ring("FairSeam1", 46.75, 2.58, 2.615, SEG, color=RC["grey"], material=M["white"]))
    add(flat_ring("FairSeam2", 48.4, 2.475, 2.51, SEG, color=RC["grey"], material=M["white"]))
    add(flat_ring("FairBaseGold", 44.26, 2.555, 2.60, SEG, color=RC["gold"], material=M["gold"]))
    add(flat_ring("FairAurora", 53.25, 1.84, 1.89, SEG, color="#5f9297", material=M["white"]))
    add(flat_ring("FairGold2", 56.35, 1.14, 1.19, SEG, color=RC["gold"], material=M["gold"]))
    # longitudinal fairing seams
    for i in range(4):
        a = math.tau * i / 4 + math.pi / 4
        pts = []
        for (r, z) in fair[1:]:
            pts.append((r * 1.002 * math.cos(a), r * 1.002 * math.sin(a), z))
        add(B.tube("FairSeam", pts, 0.018, "#c9c3b4", M["white"], segments=4))
    # latches / separation fittings
    for i in range(8):
        a = math.tau * i / 8 + 0.1
        add(B.box("FairLatch", (0.18, 0.34, 0.5), (2.66 * math.cos(a), 2.66 * math.sin(a), 45.3),
                  rot=(0, 0, a), color="#6b6961", material=M["metal"]))
    # abstract mission badge (original, no agency marks)
    add(B.cylinder("Badge", 0.62, 0.06, (2.58, 2.06, 55.8), rot=(0, math.pi / 2, 0),
                   segments=24, color="#c7a361", material=M["gold"]))
    add(B.cylinder("BadgeIn", 0.48, 0.075, (2.60, 2.06, 55.8), rot=(0, math.pi / 2, 0),
                   segments=24, color="#244b54", material=M["dark"]))
    add(B.cylinder("BadgeSun", 0.16, 0.085, (2.615, 2.06, 55.8), rot=(0, math.pi / 2, 0),
                   segments=16, color=RC["glow"], material=M["glow"]))
    # access hatch
    add(B.box("FairHatch", (0.1, 0.82, 1.1), (2.42, -1.42, 52.1),
              rot=(0, 0, -0.17), color="#d8d2c4", material=M["white"]))
    add(B.box("FairHatchFr", (0.06, 0.96, 1.24), (2.46, -1.42, 52.1),
              rot=(0, 0, -0.17), color="#8b877d", material=M["metal"]))
    # fairing tip antenna
    add(B.cylinder("TipAnt", 0.035, 0.8, (0, 0, 60.35), segments=6,
                   color="#6d6961", material=M["metal"]))
    add(B.sphere("TipBall", 0.08, (0, 0, 60.78), color="#b4563f", material=M["warm"],
                 segments=8, rings=5))
    # small service lights along the core
    for i, z in enumerate((7.2, 18.8, 27.5, 39.2)):
        a = -0.7
        add(B.box("NavLight", (0.06, 0.18, 0.08), (2.66 * math.cos(a), 2.66 * math.sin(a), z),
                  color=RC["glow"], material=M["glow"]))

    # ------------------------------------------------------------------ boosters
    angles = (math.pi / 2, math.pi / 2 + math.tau / 3, math.pi / 2 + 2 * math.tau / 3)
    BOOST_R = 1.75
    CENTER_R = 4.25
    for bi, a in enumerate(angles):
        bx, by = CENTER_R * math.cos(a), CENTER_R * math.sin(a)
        add(B.lathe(f"BoosterAft{bi}", [(1.92, 2.62), (1.9, 2.86), (1.82, 3.35),
                                        (1.76, 4.2), (1.8, 4.45)],
                    loc=(bx, by, 0), segments=40, color=RC["dark"], material=M["dark"]))
        add(B.lathe(f"BoosterBody{bi}", [(1.77, 4.35), (1.78, 5.0), (1.75, 10.0),
                                         (1.75, 16.0), (1.76, 21.0), (1.75, 26.2),
                                         (1.72, 26.9)],
                    loc=(bx, by, 0), segments=40, color=RC["white"], material=M["white"]))
        # nose ogive
        nose = [(1.72, 26.8), (1.71, 27.6), (1.66, 28.7), (1.56, 29.8),
                (1.41, 30.9), (1.2, 31.9), (0.94, 32.9), (0.66, 33.8),
                (0.38, 34.5), (0.14, 35.0), (0.03, 35.2)]
        add(B.lathe(f"BoosterNose{bi}", nose, loc=(bx, by, 0), segments=40,
                    color=RC["cream"], material=M["white"]))
        add(flat_ring(f"BoostGold{bi}", 26.82, 1.72, 1.77, 40, bx, by,
                      color=RC["gold"], material=M["gold"]))
        add(flat_ring(f"BoostSeam{bi}", 9.0, 1.735, 1.78, 40, bx, by,
                      color=RC["grey"], material=M["white"]))
        add(flat_ring(f"BoostSeam2{bi}", 18.5, 1.735, 1.78, 40, bx, by,
                      color=RC["grey"], material=M["white"]))
        for z in (6.8, 15.2, 23.4):
            add(rivet_ring(f"BoostBolt{bi}", z, 1.785, 26, 0.06, "#b8b2a2", M, angle=a))
        # separation ring & attach struts
        add(flat_ring(f"BoostSep{bi}", 3.35, 1.79, 1.87, 40, bx, by,
                      color=RC["copper"], material=M["gold"]))
        for z in (5.2, 20.5):
            p1 = (2.56 * math.cos(a), 2.56 * math.sin(a), z)
            p2 = ((CENTER_R - 1.72) * math.cos(a), (CENTER_R - 1.72) * math.sin(a), z)
            add(B.beam(f"BoostStrut{bi}_{z}", p1, p2, 0.28, 0.34, "#5b5650", M["metal"]))
        p1 = (2.5 * math.cos(a) + 0.1 * math.sin(a), 2.5 * math.sin(a) - 0.1 * math.cos(a), 17.0)
        p2 = ((CENTER_R - 1.35) * math.cos(a), (CENTER_R - 1.35) * math.sin(a), 23.5)
        add(B.beam(f"BoostDiag{bi}", p1, p2, 0.18, 0.2, "#5b5650", M["metal"]))
        # forward / aft external attach arms
        p1 = ((2.7) * math.cos(a), (2.7) * math.sin(a), 27.4)
        p2 = ((CENTER_R + 1.35) * math.cos(a), (CENTER_R + 1.35) * math.sin(a), 31.2)
        add(B.beam(f"BoostArmF{bi}", p1, p2, 0.2, 0.22, "#cfcabd", M["white"]))
        p1 = ((2.7) * math.cos(a), (2.7) * math.sin(a), 5.4)
        p2 = ((CENTER_R + 1.4) * math.cos(a), (CENTER_R + 1.4) * math.sin(a), 7.8)
        add(B.beam(f"BoostArmA{bi}", p1, p2, 0.26, 0.28, "#55524b", M["metal"]))
        # booster raceway (outward face)
        add(B.box(f"BoostRace{bi}", (0.18, 0.13, 21.0),
                  (bx + 1.77 * math.cos(a), by + 1.77 * math.sin(a), 15.4),
                  rot=(0, 0, a), color="#aaa497", material=M["white"]))
        add(flat_ring(f"BoostAurora{bi}", 11.6, 1.735, 1.774, 40, bx, by,
                      color="#6b989b", material=M["white"]))
        add(flat_ring(f"BoostAurora2{bi}", 12.25, 1.735, 1.774, 40, bx, by,
                      color="#6b989b", material=M["white"]))
        for i in range(5):
            z = 6.5 + i * 4.2
            add(B.box(f"BoostClamp{bi}_{i}", (0.32, 0.26, 0.14),
                      ((CENTER_R + 1.78) * math.cos(a), (CENTER_R + 1.78) * math.sin(a), z),
                      rot=(0, 0, a), color="#6d6961", material=M["metal"]))
        # grid fin on each booster
        add(grid_fin(f"BoostFin{bi}", 0, 0, 23.6, a, CENTER_R + BOOST_R + 0.0, 1.4, 1.9, 0.26, M, 3, 2))
        # booster twin nozzles
        for s in (-1, 1):
            t = (math.cos(a + math.pi / 2), math.sin(a + math.pi / 2))
            nx = bx + t[0] * 0.72 * s
            ny = by + t[1] * 0.72 * s
            add(nozzle(f"BoostNoz{bi}_{s}", nx, ny, 0.0, 0.66, 0.28, 2.45, segs=20, M=M))
        # nose tip probe
        add(B.cylinder(f"BoostProbe{bi}", 0.035, 0.5,
                       (bx, by, 35.4), segments=5, color="#6d6961", material=M["metal"]))

    # ------------------------------------------------------------------ core engines
    for i in range(4):
        a = math.tau * i / 4 + math.pi / 4
        add(nozzle(f"CoreNoz{i}", 1.48 * math.cos(a), 1.48 * math.sin(a), 0.0,
                   0.84, 0.31, 2.9, segs=24, M=M))
    add(nozzle("CoreNozC", 0, 0, 0.0, 0.88, 0.32, 3.0, segs=24, M=M))

    # engine bay plumbing ring
    for i in range(10):
        a = math.tau * i / 10
        add(B.tube("BayPipe", [(1.2 * math.cos(a), 1.2 * math.sin(a), 2.5),
                               (2.35 * math.cos(a), 2.35 * math.sin(a), 3.5)],
                   0.035, "#8b8272", M["metal"], segments=4))

    # ------------------------------------------------------------------ finalize
    B.join_materials("Rocket", ALL, skip_prefixes=())
    # stats
    tris = vtx = 0
    for ob in bpy.context.scene.objects:
        if ob.type == "MESH":
            vtx += len(ob.data.vertices)
            tris += sum(len(p.vertices) - 2 for p in ob.data.polygons)
    print(f"ROCKET STATS tris={tris} verts={vtx} objs={len(bpy.context.scene.objects)}")
    B.save_blend(ROCKET_BLEND)
    B.export_glb(ROCKET_GLB)
    print("ROCKET EXPORTED", os.path.getsize(ROCKET_GLB))


# =====================================================================
#  ZONE
# =====================================================================

IX, IY = 160.0, 150.0
CITY_Z = 1.58
BAY = (80.0, -81.0, 53.0, 35.0)
PAD = (102.0, 80.0)
PAD_Z = 6.6
ROCKET_Z = 7.0
STREAM_RAW = [(-88, 46), (-86, 34), (-82, 22), (-78, 10), (-72, -4),
              (-64, -17), (-52, -28), (-36, -36), (-16, -41),
              (6, -44), (24, -50), (38, -57)]
STREAM = catmull(STREAM_RAW, 8)
STREAM_W = 5.4

# road centrelines (Blender XY)
ROAD_MAIN = catmull([(24, -42), (16, -32), (11, -20), (12, -6), (14, 8),
                     (18, 22), (26, 34), (40, 44), (55, 51), (68, 57),
                     (78, 62), (86, 67)], 10)
ROAD_CROSS = catmull([(-47, -15), (-30, -13), (-8, -12.5), (14, -12.6)], 8)
PROMENADE = catmull([(18, -43), (40, -45), (62, -44), (84, -45),
                     (106, -46), (126, -48)], 10)
HILL_LANE = catmull([(-49, 6), (-62, 12), (-74, 22), (-84, 34), (-95, 48),
                     (-102, 62), (-108, 76)], 8)

ALL = []
WATER = []
M = {}


def add(objs):
    if objs is None:
        return
    if isinstance(objs, (list, tuple)):
        for o in objs:
            add(o)
    else:
        ALL.append(objs)


def add_water(objs):
    if objs is None:
        return
    if isinstance(objs, (list, tuple)):
        for o in objs:
            add_water(o)
    else:
        WATER.append(objs)
        ALL.append(objs)


def dist2path(pts, x, y):
    best = 1e9
    bestt = 0.0
    total = 0.0
    lens = [0.0]
    for i in range(1, len(pts)):
        total += math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1])
        lens.append(total)
    for i in range(len(pts) - 1):
        ax, ay = pts[i]
        bx, by = pts[i + 1]
        vx, vy = bx - ax, by - ay
        L2 = vx * vx + vy * vy
        t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((x - ax) * vx + (y - ay) * vy) / L2))
        px, py = ax + vx * t, ay + vy * t
        d = math.hypot(x - px, y - py)
        if d < best:
            best = d
            bestt = (lens[i] + (lens[i + 1] - lens[i]) * t) / max(total, 1e-6)
    return best, bestt


def bay_mask(x, y):
    d = ((x - BAY[0]) / BAY[2]) ** 2 + ((y - BAY[1]) / BAY[3]) ** 2
    d += (fbm(x * 0.055, y * 0.055, 21, 2) - 0.5) * 0.32
    return sstep(1.05, 0.88, d)


def plateau_mask(x, y):
    dx = max(abs(x - 103) - 38.0, 0.0)
    dy = max(abs(y - 78) - 33.0, 0.0)
    d = math.hypot(dx, dy)
    return sstep(8.0, 0.0, d)


def ground_h(x, y):
    n = fbm(x * 0.045, y * 0.045, 41, 3)
    n2 = fbm(x * 0.13, y * 0.13, 42, 2)
    h = CITY_Z + (n - 0.5) * 0.22 + (n2 - 0.5) * 0.05
    # west mountain shoulder, terraced towards the top
    w = sstep(-88.0, -152.0, x)
    if w > 0.001:
        hill = (w ** 1.55) * (34.0 + 12.0 * fbm(y * 0.03, x * 0.02, 51, 2))
        step = round(hill / 2.6) * 2.6
        hill = hill * 0.45 + step * 0.55
        h += hill * (0.65 + 0.35 * sstep(120, 60, abs(y - 40)))
    # north ridge with an open saddle above the spaceport
    bk = sstep(106.0, 150.0, y)
    ridge = 0.0
    if bk > 0.001:
        ridge += (bk ** 1.35) * (38.0 + 13.0 * fbm(x * 0.028, 7.1, 52, 2))
    peaks = [(-136, 139, 22, 28), (-88, 146, 32, 25), (-34, 141, 27, 29),
             (24, 147, 34, 31), (86, 143, 22, 28), (140, 139, 19, 21),
             (-152, 74, 18, 26), (-151, 18, 22, 23), (-142, -45, 15, 26),
             (-118, -92, 8.0, 30), (-78, -120, 5.0, 28)]
    for (px, py, ph, pw) in peaks:
        ridge += ph * math.exp(-(((x - px) / pw) ** 2 + ((y - py) / (pw * 1.18)) ** 2))
    notch = 1.0 - 0.56 * math.exp(-(((x - 108.0) / 30.0) ** 2)) * sstep(108, 130, y)
    h += ridge * notch
    # east shoulder behind the port
    e = sstep(144.0, 160.0, x) * sstep(-10.0, 40.0, y)
    h += e * 14.0 * (0.7 + 0.5 * fbm(y * 0.05, 3.3, 53, 2))
    # bay basin
    bm = bay_mask(x, y)
    if bm > 0.001:
        h = h * (1 - bm) + (-3.6) * bm
    # launch plateau
    pm = plateau_mask(x, y)
    if pm > 0.001:
        h = h * (1 - pm) + 6.2 * pm
    # stream channel
    sd, st = dist2path(STREAM, x, y)
    if sd < 8.5:
        carve = (1.0 - sstep(2.6, 8.5, sd)) * 1.15
        h -= carve
    return h


def ground_color(x, y, z):
    n = fbm(x * 0.05, y * 0.05, 61, 3)
    n2 = fbm(x * 0.17, y * 0.17, 62, 2)
    col = B.mix(srgb("#78905f"), srgb("#8ba36f"), n * 0.65 + n2 * 0.35)
    # dry meadow patches
    if fbm(x * 0.022 + 3.3, y * 0.022, 63, 2) > 0.62:
        col = B.mix(col, srgb("#a8a97c"), 0.35)
    # city ground: light warm paving with green pockets
    city_m = sstep(-64, -54, x) * sstep(74, 64, x) * sstep(-48, -40, y) * sstep(66, 56, y)
    if city_m > 0.01:
        pave = B.mix(srgb("#b8b09d"), srgb("#c8bfa9"), n2)
        col = B.mix(col, pave, city_m * 0.72)
        if n2 > 0.64:
            col = B.mix(col, srgb("#7f9673"), city_m * 0.45)
    # waterfront sand / shingle
    sd = abs(((x - BAY[0]) / BAY[2]) ** 2 + ((y - BAY[1]) / BAY[3]) ** 2 - 1.0)
    if sd < 0.22:
        col = B.mix(col, srgb("#c6b790"), sstep(0.22, 0.02, sd) * 0.75)
    # bay bottom
    bm = bay_mask(x, y)
    if bm > 0.01:
        col = B.mix(col, srgb("#5f746a"), bm * 0.8)
    # launch plateau concrete
    pm = plateau_mask(x, y)
    if pm > 0.01:
        conc = B.mix(srgb("#adaa9e"), srgb("#bbb7aa"), n2 * 0.7)
        col = B.mix(col, conc, pm * 0.90)
    # hills / mountain rock with layered contour bands
    if z > 3.5:
        t = sstep(4.0, 24.0, z)
        col = B.mix(col, srgb("#667a5e"), t * 0.55)
        col = B.mix(col, srgb("#8b9284"), sstep(24, 40, z) * 0.55)
        col = B.mix(col, srgb("#aeb0a1"), sstep(38, 55, z) * 0.45)
        if z > 8:
            band2 = 0.025 if int(z / 2.4) % 2 == 0 else -0.025
            col = tuple(clamp01(c + band2) for c in col)
    # stream stone banks
    sdist, st = dist2path(STREAM, x, y)
    if sdist < 8.0:
        col = B.mix(col, srgb("#a3977f"), sstep(8.0, 5.0, sdist) * 0.55)
    # paper layer banding
    band = math.sin(z * 1.35 + x * 0.01) * 0.016
    col = tuple(clamp01(c + band) for c in col)
    return B.vary(col, 0.035)


# ---------------------------------------------------------------- geometry utils

def flat_path(name, pts, width, color, material, zoff=0.0, uv_note=None):
    verts, faces = [], []
    n = len(pts)
    for i, (x, y, z) in enumerate(pts):
        if i == 0:
            dx, dy = pts[1][0] - x, pts[1][1] - y
        elif i == n - 1:
            dx, dy = x - pts[-2][0], y - pts[-2][1]
        else:
            dx, dy = pts[i + 1][0] - pts[i - 1][0], pts[i + 1][1] - pts[i - 1][1]
        L = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / L, dx / L
        verts.append((x - nx * width / 2, y - ny * width / 2, z + zoff))
        verts.append((x + nx * width / 2, y + ny * width / 2, z + zoff))
    for i in range(n - 1):
        a = i * 2
        faces.append((a, a + 2, a + 3, a + 1))
    return B._finish(name, verts, faces, color, material, smooth=False)


def offset_path(pts, off):
    out = []
    n = len(pts)
    for i, (x, y, z) in enumerate(pts):
        if i == 0:
            dx, dy = pts[1][0] - x, pts[1][1] - y
        elif i == n - 1:
            dx, dy = x - pts[-2][0], y - pts[-2][1]
        else:
            dx, dy = pts[i + 1][0] - pts[i - 1][0], pts[i + 1][1] - pts[i - 1][1]
        L = math.hypot(dx, dy) or 1.0
        out.append((x - dy / L * off, y + dx / L * off, z))
    return out


def resample(pts, step):
    out = [pts[0]]
    acc = 0.0
    for i in range(1, len(pts)):
        p0, p1 = pts[i - 1], pts[i]
        seg = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
        while acc + seg >= step:
            t = (step - acc) / seg
            p = (p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t)
            out.append((p[0], p[1], p1[2]))
            p0 = (p[0], p[1], p1[2])
            seg = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
            acc = 0.0
        acc += seg
    if out[-1][0] != pts[-1][0] or out[-1][1] != pts[-1][1]:
        out.append(pts[-1])
    return out


def path_tangent(pts, i):
    a = pts[max(0, i - 1)]
    b = pts[min(len(pts) - 1, i + 1)]
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    return ang


def ring_band(name, cx, cy, z, r_in, r_out, h, color, material, seg=32, yscale=1.0):
    verts, faces = [], []
    for k in range(4):
        rr = (r_out, r_out, r_in, r_in)[k]
        zz = (z, z + h, z + h, z)[k]
        for i in range(seg):
            a = math.tau * i / seg
            verts.append((cx + rr * math.cos(a), cy + rr * math.sin(a) * yscale, zz))
    for i in range(seg):
        j = (i + 1) % seg
        faces.append((i, j, seg + j, seg + i))
        faces.append((2 * seg + i, 2 * seg + j, 3 * seg + j, 3 * seg + i))
        faces.append((i, 2 * seg + i, 2 * seg + j, j))
        faces.append((seg + i, seg + j, 3 * seg + j, 3 * seg + i))
    return B._finish(name, verts, faces, color, material, smooth=False)


def panel(name, cx, cy, z, w, h, rot, color, material, normal="y"):
    """vertical panel; normal y faces -Y when rot=0."""
    if normal == "y":
        verts = [(-w / 2, 0, -h / 2), (w / 2, 0, -h / 2), (w / 2, 0, h / 2), (-w / 2, 0, h / 2)]
    else:
        verts = [(0, -w / 2, -h / 2), (0, w / 2, -h / 2), (0, w / 2, h / 2), (0, -w / 2, h / 2)]
    ob = B._finish(name, verts, [(0, 1, 2, 3)], color, material, smooth=False)
    B.apply_xform([ob], (cx, cy, z), rot)
    return ob


def sign_panel(name, key, cx, cy, z, rot, w, h, glow=False, board=True):
    mat = M["signsGlow"] if glow else M["signs"]
    obs = []
    if board:
        bx = cx - math.sin(rot) * 0.14
        by = cy + math.cos(rot) * 0.14
        obs.append(B.box(name + "_bd", (w + 0.34, 0.22, h + 0.32),
                         (bx, by, z), rot=(0, 0, rot), color="#2a3036", material=M["metal"]))
        for sx in (-1, 1):
            obs.append(B.box(name + f"_edge{sx}", (w + 0.4, 0.26, 0.09),
                             (bx, by, z + sx * (h / 2 + 0.2)),
                             rot=(0, 0, rot), color="#c7a161", material=M["gold"]))
    obs.append(B.sign_quad(name + "_q", key, (cx, cy, z), rot, w, h, mat))
    return obs


def railing(name, pts, z, height=1.1, post_step=2.4, color="#d8d2c2", glow=True):
    obs = []
    pts = resample(pts, post_step)
    for i, (x, y, zz) in enumerate(pts):
        obs.append(B.box(name + "_p", (0.09, 0.09, height), (x, y, z + height / 2),
                         color=color, material=M["metal"]))
        if glow and i % 3 == 0:
            obs.append(B.box(name + "_l", (0.13, 0.13, 0.08), (x, y, z + height + 0.04),
                             color="#c8f6ff", material=M["cyan"]))
    for lvl in (height * 0.55, height):
        obs.append(B.tube(name + "_r", [(x, y, z + lvl) for (x, y, zz) in resample(pts, 6.0)],
                          0.035, color, M["metal"]))
    return obs


def bench(name, x, y, z, rot, color="#b58e60"):
    obs = []
    obs.append(B.box(name + "_seat", (2.4, 0.62, 0.12), (x, y, z + 0.46), rot=(0, 0, rot),
                     color=color, material=M["wood"], bevel=0.03))
    obs.append(B.box(name + "_back", (2.4, 0.12, 0.5), (x - math.sin(rot) * 0.3, y + math.cos(rot) * 0.3, z + 0.78),
                     rot=(0.16, 0, rot), color=color, material=M["wood"]))
    for s in (-1, 1):
        ox = math.cos(rot) * s * 0.92
        oy = math.sin(rot) * s * 0.92
        obs.append(B.box(name + "_lg", (0.1, 0.5, 0.44), (x + ox, y + oy, z + 0.22),
                         rot=(0, 0, rot), color="#8a8980", material=M["metal"]))
    return obs


def bollard(name, x, y, z):
    obs = [B.cylinder(name + "_b", 0.11, 1.0, (x, y, z + 0.5), segments=8,
                      color="#d9d4c4", material=M["metal"]),
           B.cylinder(name + "_l", 0.13, 0.12, (x, y, z + 1.0), segments=8,
                      color="#c8f6ff", material=M["cyan"])]
    return obs


def planter(name, x, y, z, w=2.4, d=1.2, h=0.55, rot=0.0, hedge="#5e7c52"):
    obs = [B.box(name + "_box", (w, d, h), (x, y, z + h / 2), rot=(0, 0, rot),
                 color="#d8d0bd", material=M["wood"], bevel=0.03)]
    # low hedge / grass tufts
    grng = random.Random(int(x * 31 + y * 17) & 0xffff)
    pts = []
    for i in range(max(2, int(w * d * 0.9))):
        px = x + grng.uniform(-w * 0.4, w * 0.4)
        py = y + grng.uniform(-d * 0.3, d * 0.3)
        pts.append((px, py, z + h + 0.02))
    if pts:
        obs.append(B.tufts_mesh(name + "_g", pts, height=0.45, color=hedge,
                                material=M["foliage"], rng=grng))
    return obs


def tree_future(name, x, y, z, h=7.0, r=2.2, col="#5f7f55", rng=None):
    rng = rng or random
    obs = []
    obs.append(B.cylinder(name + "_t", 0.13 + h * 0.008, h * 0.62, (x, y, z + h * 0.31),
                          segments=6, color="#b8ac93", material=M["wood"]))
    obs.append(B.cylinder(name + "_t2", 0.09, h * 0.35, (x, y, z + h * 0.55),
                          segments=5, color="#c8bda4", material=M["wood"]))
    for k in range(4):
        a = rng.uniform(0, math.tau)
        rr = rng.uniform(0.0, r * 0.55)
        cx = x + math.cos(a) * rr
        cy = y + math.sin(a) * rr
        cz = z + h * (0.62 + 0.11 * k) + rng.uniform(-0.2, 0.2)
        rx = r * rng.uniform(0.55, 0.9)
        obs.append(B.sphere(name + f"_c{k}", rx, (cx, cy, cz),
                            scale=(1.0, 0.9, rng.uniform(0.35, 0.55)),
                            color=B.vary(srgb(col), 0.06), material=M["foliage"],
                            segments=6, rings=3))
    return obs


def tree_pine(name, x, y, z, h=9.0, col="#4e6b4f", rng=None):
    obs = [B.cylinder(name + "_t", 0.16, h * 0.55, (x, y, z + h * 0.27), segments=6,
                      color="#8d7c63", material=M["wood"])]
    for k in range(3):
        base = z + h * (0.32 + k * 0.19)
        rr = h * (0.19 - k * 0.035)
        obs.append(B.cylinder(name + f"_c{k}", rr, h * 0.32, (x, y, base + h * 0.16),
                              segments=8, color=B.vary(srgb(col), 0.07),
                              material=M["foliage"], radius2=0.02))
    return obs


# ---------------------------------------------------------------- ground / water / roads

def ground_z(x, y):
    return ground_h(x, y)


def build_terrain():
    # island base slab
    add(B.ground_slab("Base", 320, 300, 9,
                      colors=("#6f5c45", "#7d674d", "#8a7357", "#5d4c3b")))
    add(B.terrain("Terrain", 320, 300, 112, 96, ground_h, ground_color,
                  M["matte"], z0=0.0, smooth=True))
    # perimeter skirt closes the paper cut between slab and terrain
    edges = []
    n = 80
    for i in range(n):
        t = i / n
        edges.append((-160 + 320 * t, -150))
    for i in range(n):
        t = i / n
        edges.append((160, -150 + 300 * t))
    for i in range(n):
        t = i / n
        edges.append((160 - 320 * t, 150))
    for i in range(n):
        t = i / n
        edges.append((-160, 150 - 300 * t))
    verts, faces, fc = [], [], []
    for (x, y) in edges:
        h = ground_h(x, y)
        base = len(verts)
        verts += [(x, y, 0.0), (x, y, h * 0.45), (x, y, h * 0.78), (x, y, h)]
        col = B.mix(srgb("#6e5f4b"), srgb("#8b7b62"), 0.4)
        col = B.mix(col, srgb("#7b8770"), 0.25)
        for k in range(3):
            faces.append((base + k, base + k + 1, base + k + 5, base + k + 4))
            fc.append(B.vary(col, 0.05))
    # last column wraps? keep open (corners overlapped by terrain)
    faces, fc = [], []
    ne = len(edges)
    for i in range(ne):
        a = i * 4
        b = ((i + 1) % ne) * 4
        for k in range(3):
            faces.append((a + k, b + k, b + k + 1, a + k + 1))
            fc.append(B.vary(B.mix(srgb("#6e5f4b"), srgb("#8b7b62"), 0.25 + k * 0.18), 0.05))
    B._finish("Perimeter", verts, faces, None, M["matte"], smooth=False, face_colors=fc)


def water_poly(name, cx, cy, z, rx, ry, n=64, wob=0.045):
    verts = [(cx, cy, z)]
    for i in range(n):
        a = math.tau * i / n
        rr = 1.0 + wob * math.sin(a * 5 + 0.7) + 0.025 * math.sin(a * 9 + 2.1)
        verts.append((cx + rx * rr * math.cos(a), cy + ry * rr * math.sin(a), z))
    faces = [(0, i + 1, (i + 1) % n + 1) for i in range(n)]
    return B._finish(name, verts, faces, "#3c6464", M["water"], smooth=False)


def build_water():
    # bay
    add_water(water_poly("Water_Bay", BAY[0], BAY[1], 0.52, BAY[2] * 1.04, BAY[3] * 1.04, 80, 0.09))
    # stream ribbon
    sp = [(x, y, 0.92) for (x, y) in STREAM]
    add_water(flat_path("Water_Stream", sp, STREAM_W, "#3c6464", M["water"]))
    # small weir at the mouth
    add(B.box("StreamWeir", (7.2, 0.8, 0.55), (36.5, -56.0, 0.65),
              rot=(0, 0, -0.7), color="#a89c87", material=M["matte"], bevel=0.03))
    # stream edging stones
    for side in (-1, 1):
        ep = offset_path([(x, y, 0.92) for (x, y) in STREAM], side * (STREAM_W / 2 + 0.5))
        for i in range(0, len(ep) - 1, 3):
            x, y, z = ep[i]
            x2, y2, z2 = ep[min(i + 3, len(ep) - 1)]
            ang = math.atan2(y2 - y, x2 - x)
            add(B.box("StreamEdge", (math.hypot(x2 - x, y2 - y) + 0.3, 1.15, 0.55),
                      ((x + x2) / 2, (y + y2) / 2, 1.18), rot=(0, 0, ang),
                      color=B.vary(srgb("#a89c86"), 0.06), material=M["matte"]))
    # spring pool at the head of the stream
    sx0, sy0 = STREAM_RAW[0][0], STREAM_RAW[0][1]
    add_water(water_poly("Water_Spring", sx0, sy0 + 2, 0.95, 7.2, 5.4, 40, 0.08))
    add(B.ring_wall("SpringRim", sx0, sy0 + 2, 0.65,
                  7.4, 5.6, 0.9, 0.45, 40, "#a89c86", M["matte"]))
    # plaza reflecting pool
    add_water(water_poly("Water_Plaza", 2.0, -9.0, 1.735, 9.0, 5.2, 48, 0.02))
    add(ring_band("PlazaPoolRim", 2.0, -9.0, 1.60, 9.1, 9.6, 0.28, "#d9d1be", M["matte"], 48))
    # community courtyard pond
    lz = ground_h(-104, 14) + 0.12
    add_water(water_poly("Water_Lingtan", -104.0, 14.0, lz, 5.4, 3.0, 36, 0.03))
    add(ring_band("LingtanRim", -104.0, 14.0, lz - 0.16, 5.5, 6.0, 0.2, "#c9c1ae", M["matte"], 36))
    # rain gardens (sunken, with pebbles)
    gardens = [(-34, -32, 7.0, 4.0), (24, 2, 6.0, 3.2), (-36, 34, 6.5, 3.4),
               (78, 32, 7.5, 4.0), (50, -34, 5.5, 3.0), (10, 62, 6.2, 3.4)]
    for gi, (gx, gy, grx, gry) in enumerate(gardens):
        add_water(water_poly(f"Water_Rain_{gi}", gx, gy, 1.46, grx * 0.62, gry * 0.55, 28, 0.06))
        add(B.ring_wall(f"RainRim{gi}", gx, gy, 1.32, grx, gry, 0.7, 0.28, 28,
                      "#a87f5e", M["matte"]))
        rng = random.Random(900 + gi)
        for i in range(16):
            a = rng.uniform(0, math.tau)
            rr = rng.uniform(0.5, 1.05)
            px = gx + grx * rr * math.cos(a)
            py = gy + gry * rr * math.sin(a)
            add(B.sphere(f"RainPeb{gi}_{i}", rng.uniform(0.18, 0.42),
                         (px, py, 1.55), scale=(1.2, 1.0, 0.55),
                         color=B.vary(srgb("#9d9483"), 0.08), material=M["matte"],
                         segments=6, rings=4))
        pts = []
        for i in range(26):
            a = rng.uniform(0, math.tau)
            rr = rng.uniform(0.65, 1.02)
            px = gx + grx * rr * math.cos(a)
            py = gy + gry * rr * math.sin(a)
            pts.append((px, py, 1.5))
        add(B.tufts_mesh(f"RainGrass{gi}", pts, height=0.75, color="#7f9361",
                         material=M["foliage"], rng=rng))
    # waterfront pools on a terrace
    add_water(water_poly("Water_Terrace", 118.0, -35.0, 2.12, 5.4, 2.8, 28, 0.04))
    add(ring_band("TerraceRim", 118.0, -35.0, 1.98, 5.5, 6.0, 0.22, "#d5ccb8", M["matte"], 28))



def bay_shore_details():
    obs = []
    rng = random.Random(414)
    # islet with pines
    ix, iy = 54.0, -103.0
    obs.append(B.lathe("IsletBase", [(7.4, 0.35), (7.2, 0.6), (6.2, 1.1), (4.2, 1.9),
                                     (1.2, 2.4), (0.1, 2.5)],
                       loc=(ix, iy, 0), segments=20, color="#c3b58e", material=M["matte"]))
    obs.append(flat_ring("IsletSand", 0.62, 4.3, 7.3, 20, ix, iy, "#cdbf98", M["matte"]))
    for i in range(3):
        a = math.tau * i / 3 + 0.4
        obs.extend(tree_pine(f"IsletPine{i}", ix + math.cos(a) * 2.0, iy + math.sin(a) * 1.6,
                             2.2, 5.2, "#4e6a4b"))
    for i in range(8):
        a = rng.uniform(0, math.tau)
        obs.append(B.sphere(f"IsletRock{i}", rng.uniform(0.35, 0.8),
                            (ix + 7.0 * math.cos(a), iy + 6.6 * math.sin(a), 0.52),
                            scale=(1.3, 1, 0.6), color="#8e8674", material=M["matte"],
                            segments=5, rings=4))
    # rocks along the west and south shores
    for i in range(22):
        a = rng.uniform(0.25, 4.9)
        rr = rng.uniform(1.01, 1.08)
        px = BAY[0] + BAY[2] * rr * math.cos(a)
        py = BAY[1] + BAY[3] * rr * math.sin(a)
        if py > -48:
            continue
        obs.append(B.sphere(f"ShoreRock{i}", rng.uniform(0.3, 0.9), (px, py, 0.6),
                            scale=(1.4, 0.9, 0.55), color=B.vary(srgb("#928976"), 0.07),
                            material=M["matte"], segments=5, rings=4))
    # reeds at the marsh edge near the stream mouth
    pts = []
    for i in range(70):
        px = rng.uniform(30, 48)
        py = rng.uniform(-70, -52)
        if ((px - BAY[0]) / BAY[2]) ** 2 + ((py - BAY[1]) / BAY[3]) ** 2 > 1.0:
            pts.append((px, py, 0.6))
    add(B.tufts_mesh("BayReeds", pts, height=1.0, color="#7a8b56", material=M["foliage"], rng=rng))
    # viewing deck over the water
    dx, dy = 112.0, -47.5
    obs.append(B.box("BayDeck", (15.0, 7.0, 0.35), (dx, dy, 2.0),
                     color="#b08a60", material=M["wood"], bevel=0.03))
    for s2 in (-1, 1):
        obs.append(B.tube("BayDeckRail", [(dx - 7.2, dy + s2 * 3.3, 3.2),
                                          (dx + 7.2, dy + s2 * 3.3, 3.2)],
                          0.05, "#d8d1c0", M["metal"], segments=4))
        for i in range(5):
            obs.append(B.cylinder("BayDeckPost", 0.05, 1.1,
                                  (dx - 6.5 + i * 3.2, dy + s2 * 3.3, 2.7), segments=5,
                                  color="#d8d1c0", material=M["metal"]))
    for i in range(4):
        obs.append(B.cylinder("BayDeckPile", 0.20, 1.9,
                              (dx - 5.0 + i * 3.4, dy + 2.4, 0.9), segments=6,
                              color="#7c6a52", material=M["wood"]))
    obs.append(bench("BayDeckBench", dx - 3.0, dy + 1.4, 2.2, 0.0))
    obs.extend(tree_future("BayDeckTree", dx + 4.0, dy + 0.8, 2.2, 4.6, 1.5, "#5d7b49"))
    # small moored sailing boat
    bx, by = 118.0, -88.0
    obs.append(B.lathe("SailHull", [(0.4, 0.1), (1.8, 0.5), (2.0, 0.9), (1.5, 1.3), (0.3, 1.5)],
                       loc=(bx, by, 0.6), rot=(0, 0, 0.8), segments=14,
                       color="#e9e3d5", material=M["white"]))
    obs.append(B.cylinder("SailMast", 0.05, 5.0, (bx, by, 3.8), segments=5,
                          color="#a8a294", material=M["metal"]))
    obs.append(B.quad("Sail", [(bx, by, 6.2), (bx + 2.6, by, 4.0), (bx + 2.4, by, 2.1)],
                      "#e6dfce", M["white"]))
    return obs

def build_roads():
    # main boulevard with ramp to the pad
    p = []
    for (x, y) in ROAD_MAIN:
        z = max(1.74, ground_h(x, y) + 0.16)
        p.append((x, y, z))
    prof = [(-5.0, 0.0), (5.0, 0.0), (5.0, -0.5), (-5.0, -0.5)]
    add(sweep_profile("RoadMain", p, prof, "#6a6a66", M["matte"]))
    # sidewalks
    for side in (-1, 1):
        sp = offset_path(p, side * 6.8)
        add(flat_path("WalkMain", sp, 3.4, "#b8b09c", M["matte"], zoff=0.13))
        add(B.tube("CurbMain", [(x, y, z + 0.14) for (x, y, z) in offset_path(p, side * 5.15)],
                   0.10, "#d7cfbb", M["matte"]))
    # red thread centre line
    add(flat_path("RedThread", p, 0.24, "#ff6c4e", M["red"], zoff=0.03))
    for side in (-1, 1):
        lp = offset_path(p, side * 2.0)
        add(flat_path("LaneLine", [(x, y, z + 0.028) for (x, y, z) in lp], 0.12,
                      "#d8d2bf", M["cyan"]))
    # cross street
    q = [(x, y, max(1.74, ground_h(x, y) + 0.16)) for (x, y) in ROAD_CROSS]
    add(sweep_profile("RoadCross", q, [(-4.4, 0), (4.4, 0), (4.4, -0.5), (-4.4, -0.5)],
                      "#6a6a66", M["matte"]))
    for side in (-1, 1):
        sp = offset_path(q, side * 6.0)
        add(flat_path("WalkCross", sp, 2.8, "#b8b09c", M["matte"], zoff=0.12))
    # waterfront promenade
    pp = [(x, y, 2.06) for (x, y) in PROMENADE]
    add(sweep_profile("Promenade", pp, [(-4.2, 0), (4.2, 0), (4.2, -0.6), (-4.2, -0.6)],
                      "#b08a60", M["wood"]))
    # plank joints
    for i in range(0, len(pp) - 1, 2):
        x, y, z = pp[i]
        ang = path_tangent(pp, i)
        add(B.box("Plank", (0.10, 8.2, 0.045), (x, y, z + 0.04), rot=(0, 0, ang + math.pi / 2),
                  color="#8e6d4b", material=M["wood"]))
    # promenade water-side railing, seating, lanterns
    add(railing("PromRail", offset_path(pp, -3.9), 2.06, 1.1, 2.6))
    for i in range(2, len(pp) - 2, 4):
        x, y, z = pp[i]
        ang = path_tangent(pp, i)
        add(bench("PromBench", x + math.sin(ang) * 1.8, y - math.cos(ang) * 1.8, 2.08, ang + math.pi))
        add(B.cylinder("PromLanternP", 0.09, 2.5, (x - math.sin(ang) * 2.7, y + math.cos(ang) * 2.7, 3.35),
                       segments=6, color="#b39267", material=M["wood"]))
        add(B.sphere("PromLantern", 0.27, (x - math.sin(ang) * 2.7, y + math.cos(ang) * 2.7, 4.7),
                     scale=(1, 1, 1.3), color="#ffe2b0", material=M["warm"], segments=8, rings=6))
    # pier
    pier = catmull([(92, -45), (96, -52), (97, -62), (99, -70)], 8)
    pier = [(x, y, 1.35) for (x, y) in pier]
    add(sweep_profile("Pier", pier, [(-1.6, 0), (1.6, 0), (1.6, -0.4), (-1.6, -0.4)],
                      "#c09a6c", M["wood"]))
    for i in range(2, len(pier) - 1, 3):
        x, y, z = pier[i]
        for s in (-1.5, 1.5):
            add(B.cylinder("PierPile", 0.22, 2.2, (x + s * 0.5, y, 0.5), segments=8,
                           color="#7c6a52", material=M["wood"]))
    for side in (-1, 1):
        add(railing("PierRail", offset_path(pier, side * 1.6), 1.35, 1.0, 3.0))
    # pier pavilion
    px0, py0 = 99.0, -70.0
    for s2 in (-1, 1):
        for syy in (-1, 1):
            add(B.cylinder("PierPavPost", 0.12, 3.4,
                           (px0 + s2 * 2.3, py0 + syy * 2.0, 3.1), segments=6,
                           color="#9a7752", material=M["wood"]))
    add(B.lathe("PierPavRoof", [(4.6, 4.75), (4.2, 5.0), (2.6, 5.5), (0.15, 5.95)],
                loc=(px0, py0, 0), segments=18, color="#5e5b52", material=M["matte"]))
    add(B.box("PierPavDeck", (7.0, 6.0, 0.3), (px0, py0, 1.5), color="#c09a6c",
              material=M["wood"]))
    add(bench("PierBench", px0, py0 + 1.0, 1.65, 0.0))
    # hillside lane: stepped ramp following the slope
    hlp = [(x, y, ground_h(x, y) + 0.14) for (x, y) in HILL_LANE]
    add(sweep_profile("HillLane", hlp, [(-1.7, 0), (1.7, 0), (1.7, -0.35), (-1.7, -0.35)],
                      "#b3a78f", M["matte"]))
    for i in range(0, len(HILL_LANE) - 1, 1):
        x, y = HILL_LANE[i]
        z = ground_h(x, y)
        nxt = HILL_LANE[min(i + 1, len(HILL_LANE) - 1)]
        add(B.box("HillStep", (2.9, 2.2, 0.14), (x, y, z + 0.18),
                  rot=(0, 0, math.atan2(nxt[1] - y, nxt[0] - x)),
                  color="#c1b59d", material=M["matte"]))
        if i % 3 == 0:
            for s in (-1, 1):
                add(B.box("HillLamp", (0.12, 0.12, 1.1), (x + s * 1.6, y, z + 0.6),
                          color="#d6cfbd", material=M["metal"]))
                add(B.box("HillLampL", (0.16, 0.16, 0.12), (x + s * 1.6, y, z + 1.15),
                          color="#ffe0b0", material=M["warm"]))
    # launch plateau service ring + hazard markings
    ring = []
    for i in range(48):
        a = math.tau * i / 48
        ring.append((PAD[0] + 30 * math.cos(a), PAD[1] + 30 * math.sin(a), 6.44))
    add(sweep_profile("PortRing", ring, [(-2.6, 0), (2.6, 0), (2.6, -0.3), (-2.6, -0.3)],
                      "#8d8d86", M["matte"]))
    for i in range(36):
        a = math.tau * i / 36
        add(B.box("PadHazard", (0.9, 3.0, 0.06),
                  (PAD[0] + 27.4 * math.cos(a), PAD[1] + 27.4 * math.sin(a), 6.49),
                  rot=(0, 0, a), color="#d8b552" if i % 2 else "#3c3b36",
                  material=M["matte"]))
    # service road to the tank farm and control bunker
    svc = catmull([(84, 68), (76, 74), (70, 82), (68, 92), (72, 100)], 8)
    svc = [(x, y, 6.44) for (x, y) in svc]
    add(sweep_profile("PortService", svc, [(-2.2, 0), (2.2, 0), (2.2, -0.3), (-2.2, -0.3)],
                      "#8a8a83", M["matte"]))
    add(flat_path("PortRed", [(x, y, 6.47) for (x, y) in catmull(
        [(86, 66), (80, 70), (76, 76), (74, 82)], 6)], 0.2, "#ff6c4e", M["red"]))


# ---------------------------------------------------------------- city towers

def ellipse_band(name, cx, cy, z, rx0, ry0, rx1, ry1, h, color, material, seg=20, rot=0.0):
    """Solid elliptical planter/hedge ring."""
    ob = ellipse_loop(cx, cy, z, rx0, ry0, seg, rot=rot)
    ot = ellipse_loop(cx, cy, z + h, rx0, ry0, seg, rot=rot)
    ib = ellipse_loop(cx, cy, z, rx1, ry1, seg, rot=rot)
    it = ellipse_loop(cx, cy, z + h, rx1, ry1, seg, rot=rot)
    a = [p for p in ob] + [p for p in ot] + [p for p in ib] + [p for p in it]
    n = seg
    faces = []
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))                    # outer
        faces.append((2 * n + j, 2 * n + i, 3 * n + i, 3 * n + j))  # inner
        faces.append((n + i, n + j, 3 * n + j, 3 * n + i))    # top
        faces.append((i, 2 * n + i, 2 * n + j, j))            # bottom
    return B._finish(name, a, faces, color, material, smooth=False)


def mini_tree(name, cx, cy, z, h=3.0, r=1.1, col="#5a7844"):
    obs = [B.cylinder(name + "_t", 0.075, h * 0.55, (cx, cy, z + h * 0.27), segments=5,
                      color="#b7a98e", material=M["wood"])]
    obs.append(B.sphere(name + "_c", r, (cx, cy, z + h * 0.72),
                        scale=(1.0, 0.95, 0.7), color=B.vary(srgb(col), 0.06),
                        material=M["foliage"], segments=7, rings=4))
    obs.append(B.sphere(name + "_c2", r * 0.62, (cx + r * 0.35, cy + r * 0.1, z + h * 0.85),
                        scale=(1.0, 1.0, 0.75), color=B.vary(srgb(col), 0.06),
                        material=M["foliage"], segments=6, rings=4))
    return obs


def quad_batch(name, items, color, material):
    """items: (cx,cy,z,r,angle,w,h) -> vertical outward quads on a cylinder."""
    verts, faces = [], []
    for (cx, cy, z, r, ang, w, h) in items:
        tx, ty = -math.sin(ang), math.cos(ang)
        bx, by = cx + r * math.cos(ang), cy + r * math.sin(ang)
        a = len(verts)
        verts += [(bx - tx * w / 2, by - ty * w / 2, z - h / 2),
                  (bx + tx * w / 2, by + ty * w / 2, z - h / 2),
                  (bx + tx * w / 2, by + ty * w / 2, z + h / 2),
                  (bx - tx * w / 2, by - ty * w / 2, z + h / 2)]
        faces.append((a, a + 1, a + 2, a + 3))
    return B._finish(name, verts, faces, color, material, smooth=False)


def tower_plinth(name, cx, cy, z0, R, H=1.4, color="#dcd5c4"):
    obs = []
    obs.append(B.cylinder(name + "_pl", R * 1.16, H, (cx, cy, z0 + H / 2), segments=28,
                          color=color, material=M["white"]))
    obs.append(flat_ring(name + "_g", z0 + H + 0.02, R * 0.98, R * 1.15, 28, cx, cy,
                         "#71875a", M["foliage"]))
    for i in range(4):
        a = math.tau * i / 4 + 0.4
        obs.append(B.box(name + "_door", (1.8, 0.4, 2.3),
                         (cx + R * 1.15 * math.cos(a), cy + R * 1.15 * math.sin(a), z0 + H + 1.0),
                         rot=(0, 0, a), color="#23434a", material=M["glass"]))
        obs.append(B.box(name + "_doorl", (2.0, 0.12, 0.1),
                         (cx + R * 1.17 * math.cos(a), cy + R * 1.17 * math.sin(a), z0 + H + 2.2),
                         rot=(0, 0, a), color="#c9ddda", material=M["cyan"]))
    # podium lobby ring: glazing, columns and a shallow canopy
    nseg = 14
    for i in range(nseg):
        a = math.tau * i / nseg
        if i % 4 == 1:
            continue
        obs.append(B.box(name + "_lob", (2.3, 0.10, 2.2),
                         (cx + R * 1.13 * math.cos(a), cy + R * 1.13 * math.sin(a), z0 + H + 1.1),
                         rot=(0, 0, a + math.pi / 2), color="#3a5b60", material=M["glass"]))
        obs.append(B.box(name + "_col", (0.18, 0.18, 3.1),
                         (cx + R * 1.17 * math.cos(a + math.pi / nseg),
                          cy + R * 1.17 * math.sin(a + math.pi / nseg), z0 + H + 1.55),
                         color="#d8d1c0", material=M["metal"]))
    obs.append(flat_ring(name + "_canopy", z0 + H + 3.25, R * 1.06, R * 1.28, 24, cx, cy,
                         "#eee8da", M["white"]))
    obs.append(flat_ring(name + "_canopyg", z0 + H + 3.30, R * 1.16, R * 1.28, 24, cx, cy,
                         "#66864b", M["foliage"]))
    for s2 in (-1, 1):
        obs.append(B.box(name + "_steps", (3.2, 1.2, 0.14),
                         (cx + s2 * R * 1.22, cy - R * 0.45, z0 + 0.07),
                         color="#c7bfae", material=M["matte"]))
    return obs


def tower_petal(name, cx, cy, z0, H, R, floors=14, phase=0.0, seg=24, moon=False):
    obs = []
    obs.extend(tower_plinth(name, cx, cy, z0, R, 1.3))
    ztop = z0 + H

    def core_r(z):
        t = clamp01((z - z0) / H)
        return R * 0.74 * (1.0 - 0.10 * t)

    cr = [core_r(z0 + 2.0), core_r(z0 + H * 0.45), core_r(z0 + H * 0.8), core_r(ztop)]
    rings = [ellipse_loop(cx, cy, z0 + 2.0, cr[0], cr[0] * 0.92, 32, rot=phase),
             ellipse_loop(cx, cy, z0 + H * 0.45, cr[1], cr[1] * 0.92, 32, rot=phase + 0.05),
             ellipse_loop(cx, cy, z0 + H * 0.8, cr[2], cr[2] * 0.92, 32, rot=phase + 0.08),
             ellipse_loop(cx, cy, ztop, cr[3], cr[3] * 0.92, 32, rot=phase + 0.1)]
    obs.append(loft_rings(name + "_core", rings, "#ece6d8", M["white"], smooth=True))
    for i in range(12):
        a = math.tau * i / 12 + phase
        p0 = (cx + (cr[0] + 0.04) * math.cos(a), cy + (cr[0] + 0.04) * math.sin(a) * 0.92, z0 + 2.2)
        p1 = (cx + (cr[2] + 0.04) * math.cos(a), cy + (cr[2] + 0.04) * math.sin(a) * 0.92, ztop - 0.4)
        if i % 3 == 0:
            obs.append(B.beam(f"{name}_mull{i}", p0, p1, 0.16, 0.24, "#b58a5c", M["wood"]))
        else:
            obs.append(B.beam(f"{name}_mull{i}", p0, p1, 0.12, 0.18, "#d6cfbf", M["white"]))
    # vertical glazed slots on the curved white drum
    for si in range(8):
        base_a = math.tau * si / 8 + 0.19 + phase
        verts, faces = [], []
        for k in range(9):
            zz = z0 + 2.4 + (ztop - z0 - 3.0) * k / 8
            rr = core_r(zz) * 1.004
            for da in (-0.062, 0.062):
                aa = base_a + da
                verts.append((cx + rr * math.cos(aa), cy + rr * 0.92 * math.sin(aa), zz))
        for k in range(8):
            a0 = k * 2
            faces.append((a0, a0 + 2, a0 + 3, a0 + 1))
        obs.append(B._finish(name + f"_vslot{si}", verts, faces, "#3f6064", M["glass"], smooth=False))
    fh = (H - 5.0) / floors
    win_cool, win_warm, win_dark = [], [], []
    rng = random.Random(sum(ord(c) for c in name) * 37 + 11)
    for i in range(floors):
        t = i / floors
        z = z0 + 3.2 + i * fh
        rr = R * (1.0 - 0.20 * t) * (1.0 + 0.025 * math.sin(i * 1.62 + phase))
        rot = phase + i * 0.032
        rings_f = [ellipse_loop(cx, cy, z, rr * 0.955, rr * 0.86, seg, rot=rot, shape=0.035),
                   ellipse_loop(cx, cy, z + 0.55, rr, rr * 0.90, seg, rot=rot, shape=0.035),
                   ellipse_loop(cx, cy, z + 1.42, rr, rr * 0.90, seg, rot=rot, shape=0.035),
                   ellipse_loop(cx, cy, z + 1.60, rr * 0.95, rr * 0.855, seg, rot=rot, shape=0.035)]
        wc = B.mix(srgb("#f0ebde"), srgb("#e4dece"), 0.5 + 0.5 * math.sin(i * 1.1))
        obs.append(loft_rings(f"{name}_plate{i}", rings_f, wc, M["white"], smooth=False))
        gcol = ["#6b8a4f", "#78965a", "#607f47", "#829e5e"][i % 4]
        obs.append(flat_ring(f"{name}_green{i}", z + 1.62, rr * 0.80, rr * 0.995, seg, cx, cy,
                             gcol, M["foliage"]))
        obs.append(ellipse_band(f"{name}_hedge{i}", cx, cy, z + 1.62,
                                rr * 0.998, rr * 0.898, rr * 0.935, rr * 0.842, 0.72,
                                "#6b8d50", M["foliage"], 14, rot))
        obs.append(flat_ring(f"{name}_soffit{i}", z - 0.02, rr * 0.80, rr * 0.995, 24, cx, cy,
                             "#b0855a", M["wood"]))
        if i % 2 == 0:
            for k in range(4):
                a = rng.uniform(0, math.tau)
                px = cx + rr * 0.93 * math.cos(a)
                py = cy + rr * 0.93 * math.sin(a) * 0.9
                obs.append(B.sphere(f"{name}_shrub{i}_{k}", rng.uniform(0.5, 0.8),
                                    (px, py, z + 1.86), scale=(1.2, 1.0, 0.6),
                                    color=B.vary(srgb(gcol), 0.08), material=M["foliage"],
                                    segments=5, rings=3))
        if i in (2, 6, 9):
            a = rng.uniform(0, math.tau)
            px = cx + rr * 0.90 * math.cos(a)
            py = cy + rr * 0.90 * math.sin(a) * 0.9
            obs.extend(mini_tree(f"{name}_tt{i}", px, py, z + 1.62,
                                 2.6 + rng.uniform(0, 0.8), 0.85, "#648548"))
        cz = z + 1.78
        gr = core_r(cz)
        obs.append(flat_ring(f"{name}_seam{i}", cz, gr + 0.01, gr + 0.075, 32, cx, cy,
                             "#9aecf2", M["cyan"]))
        obs.append(flat_ring(f"{name}_wbal{i}", z + 2.62, gr + 0.01, gr + 0.20, 24, cx, cy,
                             "#a9855c", M["wood"]))
        # regular punched-window ribbon around the drum
        for k in range(16):
            a = math.tau * k / 16 + phase + 0.08
            zz = z + (1.62 + fh) * 0.5
            item = (cx, cy, zz, core_r(zz) + 0.02, a, 1.35, 1.8)
            q = (k * 7 + i * 3) % 10
            if q < 2:
                win_cool.append(item)
            elif q < 4:
                win_warm.append(item)
            else:
                win_dark.append(item)
        for k in range(6):
            a = rng.uniform(0, math.tau)
            zz = z + rng.uniform(1.95, max(2.1, fh - 0.15))
            r = core_r(zz) + 0.025
            item = (cx, cy, zz, r, a, rng.uniform(1.2, 2.2), rng.uniform(1.2, 2.0))
            q = rng.random()
            if q < 0.30:
                win_cool.append(item)
            elif q < 0.60:
                win_warm.append(item)
            else:
                win_dark.append(item)
    if win_cool:
        obs.append(quad_batch(name + "_wc", win_cool, "#bdefff", M["cyan"]))
    if win_warm:
        obs.append(quad_batch(name + "_ww", win_warm, "#ffd6a0", M["warm"]))
    if win_dark:
        obs.append(quad_batch(name + "_wd", win_dark, "#1f3a41", M["glass"]))
    rtop = R * 0.80
    obs.append(B.lathe(name + "_crown", [(rtop * 1.02, ztop), (rtop * 0.99, ztop + 0.7),
                                         (rtop * 0.82, ztop + 1.7), (rtop * 0.45, ztop + 2.4),
                                         (rtop * 0.18, ztop + 2.9)],
                       loc=(cx, cy, 0), segments=28, color="#efeadd", material=M["white"]))
    obs.append(flat_ring(name + "_roofg", ztop + 2.55, rtop * 0.15, rtop * 0.62, 28, cx, cy,
                         "#78915d", M["foliage"]))
    for k in range(5):
        a = rng.uniform(0, math.tau)
        obs.append(B.sphere(name + f"_rf{k}", rng.uniform(0.5, 0.9),
                            (cx + rtop * 0.42 * math.cos(a), cy + rtop * 0.42 * math.sin(a), ztop + 2.8),
                            scale=(1.1, 1.0, 0.7), color=B.vary(srgb("#6e875a"), 0.08),
                            material=M["foliage"], segments=7, rings=4))
    mast_h = 9.0 if H < 70 else 13.0
    obs.append(B.cylinder(name + "_mast", 0.10, mast_h, (cx, cy, ztop + 3.0 + mast_h / 2),
                          segments=6, color="#d6cfbf", material=M["metal"]))
    obs.append(B.sphere(name + "_beacon", 0.26, (cx, cy, ztop + 3.2 + mast_h),
                        color="#ff9a72", material=M["red"], segments=8, rings=5))
    if moon:
        zc = ztop + 8.2
        R_moon = 6.4
        ang = math.radians(-128)
        pts = []
        for i in range(40):
            a = math.tau * i / 40
            lx, lz = R_moon * math.cos(a), R_moon * math.sin(a)
            pts.append((cx + lx * math.cos(ang), cy + lx * math.sin(ang), zc + lz))
        obs.append(B.tube(name + "_moon", pts, 0.30, "#f2ecdf", M["white"], segments=6, cyclic=True))
        pts2 = []
        for i in range(40):
            a = math.tau * i / 40
            lx, lz = (R_moon - 0.55) * math.cos(a), (R_moon - 0.55) * math.sin(a)
            pts2.append((cx + lx * math.cos(ang), cy + lx * math.sin(ang), zc + lz))
        obs.append(B.tube(name + "_moonglow", pts2, 0.06, "#bff7ff", M["cyan"], segments=4, cyclic=True))
        for s in (-1, 1):
            ox = math.cos(ang) * s * 4.2
            obs.append(B.beam(name + f"_moonleg{s}",
                              (cx + ox, cy, zc - R_moon + 0.4),
                              (cx + ox, cy, ztop + 2.4), 0.22, 0.3, "#e9e3d5", M["white"]))
    return obs


def tower_ribbon(name, cx, cy, z0, H, rx, ry, twist=0.5, floors=16, phase=0.0):
    obs = []
    obs.extend(tower_plinth(name, cx, cy, z0, max(rx, ry) * 0.82, 1.3))
    n = 28
    zs = [z0 + H * (k / 8) for k in range(9)]
    scales = [1.0 - 0.14 * (k / 8) + 0.030 * math.sin(k * 0.9 + phase) for k in range(9)]
    rings = []
    for k in range(9):
        t = k / 8
        rings.append(ellipse_loop(cx, cy, zs[k], rx * scales[k], ry * scales[k], n,
                                  rot=phase + twist * t, shape=0.055, wave=0.02))
    obs.append(loft_rings(name + "_shell", rings, "#eee9dc", M["white"], smooth=True))
    for k in range(floors):
        t = (k + 0.5) / floors
        z = z0 + 2.0 + t * (H - 3.0)
        sc = 1.0 - 0.14 * t + 0.030 * math.sin(3.3 * t + phase)
        r0 = ellipse_loop(cx, cy, z, rx * sc * 1.004, ry * sc * 1.004, n,
                          rot=phase + twist * t, shape=0.055, wave=0.02)
        r1 = ellipse_loop(cx, cy, z + 1.30, rx * sc * 1.006, ry * sc * 1.006, n,
                          rot=phase + twist * (t + 0.025), shape=0.055, wave=0.02)
        obs.append(loft_rings(f"{name}_glass{k}", [r0, r1], "#3f6064", M["glass"],
                              smooth=True, cap_bottom=False, cap_top=False))
        for mi in range(8):
            a = math.tau * mi / 8 + phase + twist * t
            px = cx + rx * sc * 1.006 * math.cos(a)
            py = cy + ry * sc * 1.006 * math.sin(a)
            obs.append(B.box(f"{name}_winm{k}_{mi}", (0.10, 0.16, 0.9),
                             (px, py, z + 0.45), rot=(0, 0, a),
                             color="#e4ddcc", material=M["white"]))
    for k in range(5):
        t = 0.16 + k * 0.16
        z = z0 + 2.0 + t * (H - 3.0)
        sc = 1.0 - 0.14 * t + 0.030 * math.sin(3.3 * t + phase)
        rot = phase + twist * t
        lo = ellipse_loop(cx, cy, z, rx * sc * 1.02, ry * sc * 1.02, n, rot=rot, shape=0.055, wave=0.02)
        hi = ellipse_loop(cx, cy, z + 0.55, rx * sc * 1.05, ry * sc * 1.05, n, rot=rot, shape=0.055, wave=0.02)
        obs.append(loft_rings(name + f"_band{k}", [lo, hi], "#ece7da", M["white"], smooth=False))
        g = ellipse_loop(cx, cy, z + 0.58, rx * sc * 1.06, ry * sc * 1.06, n,
                         rot=rot, shape=0.055, wave=0.02)
        gi = ellipse_loop(cx, cy, z + 0.58, rx * sc * 0.80, ry * sc * 0.80, n,
                          rot=rot, shape=0.055, wave=0.02)
        obs.append(ring_poly(name + f"_green{k}", g, gi, ["#6a894e", "#75925a"][k % 2], M["foliage"]))
        obs.append(ellipse_band(name + f"_hedge{k}", cx, cy, z + 0.58,
                                rx * sc * 1.05, ry * sc * 1.05, rx * sc * 0.95, ry * sc * 0.95,
                                0.65, "#6a8b4f", M["foliage"], 16, rot))

        rng = random.Random(int(1000 * t) + 3)
        for j in range(8):
            a = rng.uniform(0, math.tau)
            px = cx + rx * sc * 0.96 * math.cos(a)
            py = cy + ry * sc * 0.96 * math.sin(a)
            obs.append(B.sphere(name + f"_shr{k}_{j}", rng.uniform(0.45, 0.75),
                                (px, py, z + 0.9), scale=(1.15, 1.0, 0.65),
                                color=B.vary(srgb("#68884d"), 0.09), material=M["foliage"],
                                segments=7, rings=4))
        if k in (1, 3):
            for j in range(2):
                a = rng.uniform(0, math.tau)
                px = cx + rx * sc * 0.88 * math.cos(a)
                py = cy + ry * sc * 0.88 * math.sin(a)
                obs.extend(mini_tree(f"{name}_tt{k}_{j}", px, py, z + 0.6, 3.0, 0.95, "#52713c"))
    for si, base_a in enumerate((0.3, 1.35, 2.4, 3.45, 4.5, 5.55)):
        verts, faces = [], []
        for k in range(9):
            t = k / 8
            z = z0 + 2.0 + t * (H - 3.0)
            sc = 1.0 - 0.14 * t + 0.03 * math.sin(3.3 * t + phase)
            a = base_a + twist * t + phase
            for da in (-0.012, 0.012):
                aa = a + da
                verts.append((cx + rx * sc * 1.008 * math.cos(aa),
                              cy + ry * sc * 1.008 * math.sin(aa), z))
        for k in range(8):
            a0 = k * 2
            faces.append((a0, a0 + 2, a0 + 3, a0 + 1))
        obs.append(B._finish(name + f"_seam{si}", verts, faces, "#bff7ff", M["cyan"], smooth=False))
    # tall glazed slots
    for si in range(6):
        base_a = math.tau * si / 6 + 0.31
        verts, faces = [], []
        for k in range(9):
            t = k / 8
            z = z0 + 3.0 + t * (H - 5.0)
            sc = 1.0 - 0.14 * t + 0.03 * math.sin(3.3 * t + phase)
            a = base_a + twist * t + phase
            for da in (-0.075, 0.075):
                aa = a + da
                verts.append((cx + rx * sc * 1.008 * math.cos(aa),
                              cy + ry * sc * 1.008 * math.sin(aa), z))
        for k in range(8):
            a0 = k * 2
            faces.append((a0, a0 + 2, a0 + 3, a0 + 1))
        obs.append(B._finish(name + f"_vslot{si}", verts, faces, "#37575c", M["glass"], smooth=False))
    # warm timber fins following the twist
    for si, base_a in enumerate((0.95, 2.25, 3.75, 5.05)):
        verts, faces = [], []
        for k in range(9):
            t = k / 8
            z = z0 + 2.0 + t * (H - 3.0)
            sc = 1.0 - 0.14 * t + 0.03 * math.sin(3.3 * t + phase)
            a = base_a + twist * t + phase
            for da in (-0.030, 0.030):
                aa = a + da
                verts.append((cx + rx * sc * 1.006 * math.cos(aa),
                              cy + ry * sc * 1.006 * math.sin(aa), z))
        for k in range(8):
            a0 = k * 2
            faces.append((a0, a0 + 2, a0 + 3, a0 + 1))
        obs.append(B._finish(name + f"_wood{si}", verts, faces, "#b0855a", M["wood"], smooth=False))
    top_sc = 0.86
    obs.append(B.lathe(name + "_crown", [(max(rx, ry) * top_sc * 0.72, z0 + H),
                                         (max(rx, ry) * top_sc * 0.66, z0 + H + 1.2),
                                         (max(rx, ry) * top_sc * 0.40, z0 + H + 2.2),
                                         (max(rx, ry) * top_sc * 0.12, z0 + H + 2.8)],
                       loc=(cx, cy, 0), segments=28, color="#f0ebde", material=M["white"]))
    obs.append(flat_ring(name + "_roofg", z0 + H + 2.45, 0.8, max(rx, ry) * 0.44, 28, cx, cy,
                         "#76905c", M["foliage"]))
    obs.append(B.cylinder(name + "_mast", 0.09, 10.0, (cx, cy, z0 + H + 7.8), segments=6,
                          color="#d6cfbf", material=M["metal"]))
    obs.append(B.sphere(name + "_beacon", 0.24, (cx, cy, z0 + H + 12.9),
                        color="#ffa07a", material=M["red"], segments=8, rings=5))
    return obs


def tower_terrace(name, cx, cy, z0, w, d, H, steps=4, rot=0.0):
    obs = []
    obs.extend(tower_plinth(name, cx, cy, z0, max(w, d) * 0.55, 1.2))
    for k in range(steps):
        t0 = k / steps
        t1 = (k + 1) / steps
        z = z0 + 1.2 + t0 * (H - 1.2)
        z2 = z0 + 1.2 + t1 * (H - 1.2)
        ww = w * (1 - 0.16 * t0)
        dd = d * (1 - 0.16 * t0)
        lo = rounded_loop(cx, cy, z, ww, dd, min(2.0, min(ww, dd) * 0.18), 4, rot)
        hi = rounded_loop(cx, cy, z2, ww * 0.985, dd * 0.985, min(2.0, min(ww, dd) * 0.18), 4, rot)
        obs.append(loft_rings(name + f"_vol{k}", [lo, hi], "#ece7d9", M["white"], smooth=False))
        gw = ww * 0.92
        gd = dd * 0.92
        groof = rounded_loop(cx, cy, z2 + 0.06, gw, gd, min(1.8, min(gw, gd) * 0.16), 4, rot)
        verts = groof + [(cx, cy, z2 + 0.06)]
        faces = [(i, (i + 1) % len(groof), len(groof)) for i in range(len(groof))]
        obs.append(B._finish(name + f"_gr{k}", verts, faces, "#758d5b", M["foliage"], smooth=False))
        po = rounded_loop(cx, cy, z2, ww, dd, min(2.0, min(ww, dd) * 0.18), 4, rot)
        pi = rounded_loop(cx, cy, z2, ww * 0.94, dd * 0.94, min(1.8, min(ww, dd) * 0.16), 4, rot)
        obs.append(ring_poly(name + f"_par{k}", po, pi, "#f2ecdf", M["white"]))
        for i in range(10):
            lx = cx - ww * 0.40 + i * (ww * 0.8 / 9)
            obs.append(B.box(name + f"_lv{k}_{i}", (0.12, 0.16, (z2 - z) * 0.7),
                             (lx, cy - dd / 2 - 0.12, z + (z2 - z) * 0.46),
                             color="#b88d5f", material=M["wood"]))
        for i in range(6):
            lx = cx - ww * 0.34 + i * (ww * 0.68 / 5)
            mat = M["glass"] if i % 3 else M["warm"]
            col = "#3e5f63" if i % 3 else "#ffd7a3"
            obs.append(B.box(name + f"_win{k}_{i}", (0.9, 0.08, 1.5),
                             (lx, cy - dd / 2 - 0.04, z + (z2 - z) * 0.4),
                             color=col, material=mat))
        for i in range(7):
            lx = cx - ww * 0.42 + i * (ww * 0.84 / 6)
            obs.append(B.box(name + f"_pl{k}_{i}", (1.1, 1.0, 0.7),
                             (lx, cy - dd * 0.44, z2 + 0.35),
                             color="#587641", material=M["foliage"]))
            obs.append(B.box(name + f"_pl2{k}_{i}", (1.1, 1.0, 0.7),
                             (lx, cy + dd * 0.44, z2 + 0.35),
                             color="#5d7c45", material=M["foliage"]))
    for i in range(3):
        a = math.tau * i / 3 + 0.5
        obs.extend(tree_future(name + f"_rt{i}", cx + math.cos(a) * w * 0.22,
                               cy + math.sin(a) * d * 0.22, z0 + H + 0.1, 4.2, 1.5, "#5f7c53"))
    return obs

def side_band(name, pts, z0, z1, off, color, material):
    """Vertical ribbon following a path, offset sideways."""
    op = offset_path(pts, off)
    verts, faces = [], []
    for (x, y, z) in op:
        verts.append((x, y, z + z0))
        verts.append((x, y, z + z1))
    for i in range(len(op) - 1):
        a = i * 2
        faces.append((a, a + 1, a + 3, a + 2))
    return B._finish(name, verts, faces, color, material, smooth=False)


def community_center():
    obs = []
    z0 = ground_h(-104, 14)
    wings = [(-104, 6.0, 27.0, 8.2), (-104, 22.0, 27.0, 8.2), (-117.0, 14.0, 8.2, 22.0)]
    for wi, (wx, wy, ww, wd) in enumerate(wings):
        lo = rounded_loop(wx, wy, z0, ww, wd, 2.4, 4, 0.0)
        hi = rounded_loop(wx, wy, z0 + 6.0, ww, wd, 2.4, 4, 0.0)
        obs.append(loft_rings(f"CommWall{wi}", [lo, hi], "#eee8da", M["white"], smooth=False))
        roof = rounded_loop(wx, wy, z0 + 6.05, ww * 0.93, wd * 0.93, 2.2, 4, 0.0)
        verts = roof + [(wx, wy, z0 + 6.05)]
        faces = [(i, (i + 1) % len(roof), len(roof)) for i in range(len(roof))]
        obs.append(B._finish(f"CommRoof{wi}", verts, faces, "#78905c", M["foliage"], smooth=False))
        for i in range(6):
            if wi == 2:
                yy = wy - wd * 0.38 + i * (wd * 0.76 / 5)
                obs.append(B.box(f"CommWin{wi}_{i}", (0.1, 1.7, 2.6),
                                 (wx + ww / 2 + 0.04, yy, z0 + 3.1),
                                 color="#26454b", material=M["glass"]))
            else:
                xx = wx - ww * 0.38 + i * (ww * 0.76 / 5)
                yy = wy + (wd / 2 + 0.04) * (1 if wi == 0 else -1)
                obs.append(B.box(f"CommWin{wi}_{i}", (1.7, 0.1, 2.6), (xx, yy, z0 + 3.1),
                                 color="#26454b", material=M["glass"]))
        for i in range(int(ww / 1.5)):
            xx = wx - ww * 0.45 + i * 1.5
            obs.append(B.box(f"CommLv{wi}_{i}", (0.12, 0.2, 1.0),
                             (xx, wy - wd / 2 - 0.15, z0 + 5.15),
                             color="#b5895d", material=M["wood"]))
        for i in range(3):
            for j in range(2):
                obs.append(B.box(f"CommSolar{wi}_{i}_{j}", (1.7, 1.1, 0.08),
                                 (wx - ww * 0.25 + i * ww * 0.25, wy - wd * 0.2 + j * wd * 0.35,
                                  z0 + 6.4), rot=(0.32, 0, 0),
                                 color="#243f4a", material=M["panel"]))
    obs.append(B.box("CommDeck", (25, 12, 0.18), (-104, 14.0, z0 + 0.1),
                     color="#c1b49a", material=M["matte"]))
    for i in range(4):
        obs.append(bench("CommBench", -112 + i * 4.4, 17.4, z0 + 0.2, 0.0))
    for i in range(6):
        obs.extend(bollard("CommBoll", -113 + i * 4.6, 10.2, z0 + 0.2))
    # free-standing sign, facing the city
    obs.append(B.box("LingFrame", (0.5, 7.4, 4.8), (-90.0, 14.0, z0 + 2.6),
                     color="#3d3a34", material=M["metal"]))
    obs.extend(sign_panel("LingSign", "lingtan", -89.8, 14.0, z0 + 3.0, math.pi / 2,
                          5.8, 1.9, glow=False))
    obs.append(B.box("LingBoard", (2.0, 0.25, 3.2), (-92.0, 20.0, z0 + 1.9),
                     color="#c8f3f3", material=M["cyan"]))
    # community pavilion over the pond edge
    for s in (-1, 1):
        obs.append(B.cylinder("CommPost", 0.16, 4.2, (-104 + s * 4.0, 14.0, z0 + 2.1), segments=8,
                              color="#b78c5f", material=M["wood"]))
    obs.append(B.box("CommCanopy", (10.0, 4.8, 0.25), (-104, 14.0, z0 + 4.3),
                     rot=(0.06, 0, 0), color="#efe9db", material=M["white"], bevel=0.04))
    return obs


def skybridge(name, cx1, cy1, cx2, cy2, z, w=3.2, h=3.4, sag=1.1, pylon=False):
    obs = []
    pts = catmull([(cx1, cy1), ((cx1 + cx2) / 2, (cy1 + cy2) / 2), (cx2, cy2)], 10)
    pp = []
    for i, (x, y) in enumerate(pts):
        t = i / (len(pts) - 1)
        pp.append((x, y, z - sag * math.sin(math.pi * t)))
    prof = [(-w / 2, 0.0), (w / 2, 0.0), (w / 2, h * 0.72), (w * 0.30, h),
            (-w * 0.30, h), (-w / 2, h * 0.72)]
    obs.append(sweep_profile(name, pp, prof, "#eee9dc", M["white"], smooth=False))
    for side in (-1, 1):
        obs.append(side_band(name + "_gl", pp, 0.6, h - 0.75, side * (w / 2 + 0.02),
                             "#2a4b51", M["glass"]))
    for i in range(1, len(pp) - 1, 3):
        x, y, zz = pp[i]
        ang = path_tangent(pp, i)
        obs.append(B.box(name + "_rib", (0.22, w + 0.5, 0.22), (x, y, zz + h + 0.05),
                         rot=(0, 0, ang + math.pi / 2), color="#dcd5c4", material=M["white"]))
        obs.append(B.box(name + "_lg", (0.6, 0.18, 0.1), (x, y, zz - 0.06),
                         rot=(0, 0, ang + math.pi / 2), color="#bff7ff", material=M["cyan"]))
    obs.append(flat_path(name + "_roofg", [(x, y, z + h + 0.12) for (x, y, z) in pp],
                         1.5, "#6f8858", M["foliage"]))
    gp = [(x, y, z + h + 0.18) for (x, y, z) in pp[1:-1:2]]
    obs.append(B.tufts_mesh(name + "_roofgt", gp, height=0.5, color="#6f8858",
                            material=M["foliage"], rng=random.Random(int(z * 13) & 0xffff)))
    if pylon:
        mx, my = (cx1 + cx2) / 2, (cy1 + cy2) / 2
        gz = ground_h(mx, my)
        obs.append(B.cylinder(name + "_pyl", 0.85, max(1.0, z - sag - gz), (mx, my, (z - sag + gz) / 2),
                              segments=10, color="#e6dfd0", material=M["white"], radius2=0.6))
        obs.append(B.box(name + "_cap", (4.2, 1.2, 0.6), (mx, my, z - sag - 0.3),
                         color="#eee9dc", material=M["white"]))
        obs.append(flat_ring(name + "_plg", gz + 0.1, 1.2, 2.4, 12, mx, my, "#6f8858", M["foliage"]))
    return obs


def city_plaza():
    obs = []
    z = 1.70
    obs.append(B.cylinder("PlazaPave", 16.0, 0.30, (2, -9, z - 0.15), segments=56,
                          color="#c7bea9", material=M["matte"]))
    for r0, r1, cc in [(4.4, 4.7, "#b3a88f"), (10.2, 10.6, "#d8d0bb"),
                       (14.2, 14.7, "#b3a88f"), (6.6, 6.85, "#ff6c4e")]:
        mat = M["red"] if cc == "#ff6c4e" else M["matte"]
        obs.append(flat_ring("PlazaRing", z + 0.02, r0, r1, 56, 2, -9, cc, mat))
    for i in range(5):
        obs.append(B.box("PlazaStone", (1.2, 1.2, 0.18), (2 + 5.4 - i * 1.5, -9 + 0.8, z - 0.02),
                         rot=(0, 0, 0.4), color="#cfc6b1", material=M["matte"], bevel=0.04))
    scx, scy = -9.0, -13.0
    ang = math.radians(-40)
    for rr, rad, col, mat in [(7.2, 0.38, "#f0ebde", M["white"]),
                              (6.1, 0.16, "#bff7ff", M["cyan"]),
                              (4.4, 0.07, "#ff8a68", M["red"])]:
        pts = []
        for i in range(40):
            a = math.tau * i / 40
            lx, lz = rr * math.cos(a), rr * math.sin(a)
            pts.append((scx + lx * math.cos(ang), scy + lx * math.sin(ang), z + 7.0 + lz))
        obs.append(B.tube("MoonPortal", pts, rad, col, mat, segments=6, cyclic=True))
    for s in (-1, 1):
        obs.append(B.box("MoonFoot", (2.6, 1.2, 0.7), (scx + s * 4.6, scy - 0.5, z + 0.35),
                         color="#ddd6c5", material=M["white"], bevel=0.05))
    for i in range(8):
        a = math.tau * i / 8 + 0.2
        px, py = 2 + 12.8 * math.cos(a), -9 + 12.8 * math.sin(a) * 0.85
        if 8 < px < 22 and -22 < py < -4:
            continue
        obs.extend(bench("PlazaBench", px, py, z, a + math.pi))
    for i in range(10):
        a = math.tau * i / 10
        px, py = 2 + 14.9 * math.cos(a), -9 + 14.9 * math.sin(a) * 0.9
        if 8 < px < 22 and -22 < py < -4:
            continue
        obs.extend(bollard("PlazaBoll", px, py, z))
    for i in range(5):
        a = math.tau * i / 5 + 0.4
        px, py = 2 + 11.5 * math.cos(a), -9 + 11.5 * math.sin(a) * 0.9
        obs.extend(tree_future("PlazaTree", px, py, z, 6.2, 1.9, "#647f52"))
    obs.append(B.box("PlazaKiosk", (4.2, 2.4, 3.0), (-6.0, -2.5, z + 1.5),
                     rot=(0, 0, 0.2), color="#e4ded0", material=M["white"], bevel=0.12))
    obs.append(B.box("PlazaKioskG", (3.6, 0.1, 1.7), (-6.0, -3.72, z + 1.8), rot=(0, 0, 0.2),
                     color="#aef2f7", material=M["cyan"]))
    return obs


def city_gate():
    obs = []
    gx, gy = 18.5, -38.0
    z = 1.72
    for s in (-1, 1):
        px = gx + s * 11.0
        obs.append(B.cylinder("GatePylon", 1.0, 12.4, (px, gy, z + 6.2), segments=12,
                              color="#eee9dc", material=M["white"], radius2=0.6))
        obs.append(B.box("GateFin", (0.28, 2.3, 9.0), (px, gy, z + 6.0),
                         color="#b78c5f", material=M["wood"]))
        obs.append(B.box("GateGlow", (0.16, 0.16, 10.0), (px - s * 1.0, gy - 0.9, z + 6.0),
                         color="#bff7ff", material=M["cyan"]))
        obs.append(B.box("GateFoot", (2.8, 2.8, 0.8), (px, gy, z + 0.4),
                         color="#d8d0bd", material=M["matte"], bevel=0.08))
    obs.append(B.box("GateBeam", (23.5, 1.1, 1.3), (gx, gy, z + 11.5),
                     color="#eee9dc", material=M["white"], bevel=0.08))
    obs.append(sign_panel("CitySign", "xincheng", gx, gy - 0.62, z + 10.4, 0.0, 10.4, 3.25,
                          glow=False))
    obs.append(sign_panel("CitySignB", "xincheng", gx, gy + 0.62, z + 10.4, math.pi, 10.4, 3.25,
                          glow=False, board=False))
    for s in (-1, 1):
        obs.extend(sign_panel("ExitSign", "exit", gx + s * 6.5, gy - 1.2, z + 2.4, 0.0,
                              2.2, 0.9, glow=True))
    return obs

# ---------------------------------------------------------------- transit

LOOP_C = (-18.0, 12.0)
LOOP_RX, LOOP_RY, LOOP_Z = 70.0, 48.0, 13.8
TOWER_BASES = [(-50, 28, 12.5), (-16, 18, 9.5), (-14, 44, 9.0), (-72, 2, 10.0),
               (-60, 44, 8.5), (-42, -20, 8.5), (28, -10, 9.0), (-18, -25, 9.0),
               (34, 14, 7.5), (38, 28, 5.0), (-104, 34, 7.0), (-122, 52, 6.0),
               (-108, 78, 6.5), (-132, 16, 6.0), (16, 48, 8.0), (36, 74, 8.0)]


def loop_pt(theta):
    return (LOOP_C[0] + LOOP_RX * math.cos(theta),
            LOOP_C[1] + LOOP_RY * math.sin(theta), LOOP_Z)


def build_guideway(name, pts, zoff=0.0):
    p = [(x, y, z + zoff) for (x, y, z) in pts]
    prof = [(-1.95, 0.0), (1.95, 0.0), (1.95, -0.36), (1.55, -0.72),
            (-1.55, -0.72), (-1.95, -0.36)]
    add(sweep_profile(name + "Deck", p, prof, "#e9e4d7", M["white"]))
    for s in (-1, 1):
        lp = offset_path(p, s * 1.62)
        add(flat_path(name + "Glow", lp, 0.20, "#a8f4ff", M["cyan"], zoff=0.025))
        add(side_band(name + "Side", p, -0.30, -0.04, s * 1.965, "#3d5a5f", M["glass"]))
    # centre rail / maglev spine
    add(flat_path(name + "Spine", p, 0.5, "#d6cfd0", M["metal"], zoff=0.012))


def build_transit():
    # elevated loop
    n = 72
    loop = [loop_pt(math.tau * i / n) for i in range(n + 1)]
    build_guideway("MagLoop", loop)
    # pylons
    pylon_n = 22
    for i in range(pylon_n):
        th = math.tau * i / pylon_n + 0.12
        x, y, z = loop_pt(th)
        sd, st = dist2path(STREAM, x, y)
        near_stream = sd < 7.0
        near_road = dist2path(ROAD_MAIN, x, y)[0] < 5.0
        near_bay = bay_mask(x, y) > 0.12
        if near_stream or near_road or near_bay:
            continue
        gz = ground_z(x, y)
        h = z - 1.0 - gz
        add(B.cylinder("LoopPylon", 0.78, h, (x, y, gz + h / 2), segments=12,
                       color="#e7e0d1", material=M["white"], radius2=0.56))
        add(B.cylinder("LoopPylonBase", 1.35, 0.6, (x, y, gz + 0.3), segments=16,
                       color="#c8c0ae", material=M["matte"]))
        add(B.box("LoopPylonCap", (3.2, 2.2, 0.65), (x, y, z - 0.95),
                  rot=(0, 0, th + math.pi / 2), color="#eee9dc", material=M["white"], bevel=0.05))
        add(B.box("LoopPylonGlow", (3.26, 2.26, 0.08), (x, y, z - 0.6),
                  rot=(0, 0, th + math.pi / 2), color="#bff7ff", material=M["cyan"]))
        add(flat_ring("LoopPylonGr", gz + 0.04, 1.4, 3.0, 16, x, y, "#70885a", M["foliage"]))
    # branch to the spaceport
    br = catmull([(51.3, 18.7), (56.0, 24.0), (59.5, 30.0), (61.8, 37.0),
                  (63.0, 44.0), (63.6, 50.0)], 8)
    brz = path_z(br, LOOP_Z, 10.2)
    build_guideway("MagBranch", brz)
    for i in (2, 8, 14, 20, 26, 32, 38, len(br) - 2):
        x, y, z = brz[i]
        gz = ground_z(x, y)
        h = z - 1.0 - gz
        add(B.cylinder("BranchPylon", 0.72, h, (x, y, gz + h / 2), segments=10,
                       color="#e7e0d1", material=M["white"], radius2=0.52))
        add(B.box("BranchCap", (2.8, 2.0, 0.55), (x, y, z - 0.9),
                  rot=(0, 0, path_tangent(brz, i) + math.pi / 2),
                  color="#eee9dc", material=M["white"]))
        add(flat_ring("BranchGr", gz + 0.04, 1.2, 2.5, 12, x, y, "#70885a", M["foliage"]))
    # water-front station
    build_station()
    # spaceport terminal
    build_port_terminal(brz[-1])
    # maglev train
    build_train()


def rounded_yz(x, w, h, r, n=3, zc=0.0):
    pts = []
    hw, hh = w / 2 - r, h / 2 - r
    corners = [(hw, hh, 0), (-hw, hh, math.pi / 2), (-hw, -hh, math.pi), (hw, -hh, math.pi * 1.5)]
    for (cy, cz, base) in corners:
        for i in range(n + 1):
            a = base + (math.pi / 2) * i / n
            pts.append((x, cy + r * math.cos(a), zc + h / 2 + cz + r * math.sin(a)))
    return pts


def railcar(name, base, rot, z):
    """Rounded maglev car; local +X along the length."""
    obs = []
    secs = [(-4.15, 0.55), (-3.85, 0.88), (-3.35, 1.0), (-1.0, 1.0),
            (1.0, 1.0), (3.35, 1.0), (3.85, 0.88), (4.15, 0.55)]
    rings = []
    for (x, sc) in secs:
        rings.append(rounded_yz(x, 2.75 * sc, 2.85 * sc, 0.55 * sc, 3, zc=1.45))
    obs.append(loft_rings(name + "_body", rings, "#f1ecdf", M["white"], smooth=True))
    # dark window band and lit panes (both sides)
    for s in (-1, 1):
        obs.append(B.box(name + "_wband", (6.9, 0.05, 0.95), (0, s * 1.385, z + 2.15),
                         color="#233f46", material=M["glass"]))
        for i in range(5):
            obs.append(B.box(name + f"_win{i}", (0.95, 0.04, 0.68),
                             (-2.6 + i * 1.3, s * 1.415, z + 2.2),
                             color="#bff7ff" if i % 3 else "#ffd8a5",
                             material=M["cyan"] if i % 3 else M["warm"]))
        obs.append(B.box(name + "_door", (0.9, 0.06, 2.1), (2.2, s * 1.39, z + 1.55),
                         color="#2b474d", material=M["glass"]))
        obs.append(B.box(name + "_doorl", (0.95, 0.04, 0.07), (2.2, s * 1.42, z + 2.6),
                         color="#a8f4ff", material=M["cyan"]))
        obs.append(B.box(name + "_skirtglow", (7.2, 0.05, 0.08), (0, s * 1.36, z + 0.42),
                         color="#a8f4ff", material=M["cyan"]))
    # undercarriage, maglev skids
    obs.append(B.box(name + "_under", (7.4, 2.1, 0.34), (0, 0, z + 0.26),
                     color="#44494b", material=M["metal"]))
    for s in (-1, 1):
        obs.append(B.box(name + "_skid", (7.0, 0.5, 0.22), (0, s * 1.05, z + 0.12),
                         color="#303538", material=M["metal"]))
    # roof equipment
    obs.append(B.box(name + "_roofbox", (2.6, 1.2, 0.35), (0, 0, z + 2.98),
                     color="#dad4c5", material=M["white"], bevel=0.06))
    obs.append(B.box(name + "_ant", (0.5, 0.08, 1.0), (-3.0, 0, z + 2.95),
                     color="#6d6961", material=M["metal"]))
    # destination strip
    obs.append(B.box(name + "_dest", (1.7, 0.05, 0.24), (0, -1.43, z + 2.7),
                     color="#a8f4ff", material=M["cyan"]))
    B.apply_xform(obs, (base[0], base[1], z), rot)
    return obs


def build_train():
    # place five cars on the loop south-east arc
    for k in range(5):
        th = math.radians(-72 + k * 9.2)
        x = LOOP_C[0] + LOOP_RX * math.cos(th)
        y = LOOP_C[1] + LOOP_RY * math.sin(th)
        tx, ty = -LOOP_RX * math.sin(th), LOOP_RY * math.cos(th)
        rot = math.atan2(ty, tx)
        add(railcar(f"Train{k}", (x, y, 0), rot, LOOP_Z + 0.02))


def build_station():
    sx, sy = -8.0, -35.6
    z = LOOP_Z
    # side platforms
    for s in (-1, 1):
        add(B.box("StationDeck", (26, 3.6, 0.40), (sx, sy + s * 4.0, z + 0.05),
                  rot=(0, 0, 0), color="#efe9db", material=M["white"], bevel=0.03))
        add(B.box("StationEdgeGlow", (24, 0.12, 0.09), (sx, sy + s * 2.25, z + 0.27),
                  color="#bff7ff", material=M["cyan"]))
        for i in range(9):
            xx = sx - 11.5 + i * 2.9
            add(B.box("StationSeat", (1.6, 0.55, 0.2), (xx, sy + s * 4.9, z + 0.55),
                      color="#b58e60", material=M["wood"]))
    # canopy arc ribs
    rook_x = [sx - 10.5, sx - 5.2, sx, sx + 5.2, sx + 10.5]
    for xx in rook_x:
        pts = []
        for i in range(13):
            a = math.pi * i / 12
            pts.append((xx, sy + 5.2 * math.cos(a), z + 0.5 + 4.1 * math.sin(a)))
        add(B.tube("StationRib", pts, 0.13, "#f1ecdf", M["white"], segments=5))
    # canopy skin
    verts, faces = [], []
    ns = 13
    for xx in rook_x:
        for i in range(ns):
            a = math.pi * i / (ns - 1)
            verts.append((xx, sy + 5.25 * math.cos(a), z + 0.52 + 4.15 * math.sin(a)))
    for k in range(len(rook_x) - 1):
        for i in range(ns - 1):
            a = k * ns + i
            faces.append((a, a + 1, a + ns + 1, a + ns))
    add(B._finish("StationCanopy", verts, faces, "#f3eee1", M["white"], smooth=True))
    # canopy edge glows
    for s in (-1, 1):
        pts = []
        for xx in rook_x:
            pts.append((xx, sy + s * 5.25, z + 0.55))
        add(B.tube("StationEdgeL", pts, 0.055, "#bff7ff", M["cyan"], segments=4))
    # timber underside battens
    for xx in [sx - 9.4 + i * 2.35 for i in range(9)]:
        pts = []
        for i in range(9):
            a = math.pi * (i + 1) / 10
            pts.append((xx, sy + 5.0 * math.cos(a), z + 0.62 + 3.9 * math.sin(a)))
        add(B.tube("StationBatten", pts, 0.045, "#b78c5f", M["wood"], segments=4))
    # support columns
    for sxx in (-1, 1):
        for syy in (-1, 1):
            add(B.cylinder("StationCol", 0.20, 4.1,
                           (sx + sxx * 10.6, sy + syy * 4.7, z + 2.2), segments=8,
                           color="#d8d1c0", material=M["metal"]))
    # platform sign
    add(sign_panel("PlatformSign", "platform", sx, sy - 5.5, z + 2.8, 0.0, 2.8, 1.15,
                   glow=True))
    add(sign_panel("PlatformSign2", "platform", sx - 9.0, sy - 1.2, z + 3.3, 0.0, 2.2, 0.9,
                   glow=False))
    # glass access ramp down to the plaza
    ramp = [(2.0, -39.0, z + 0.45), (2.0, -33.0, z - 2.6), (2.0, -27.0, z - 6.2),
            (2.0, -20.2, 2.6)]
    add(sweep_profile("RampFloor", ramp, [(-1.7, 0), (1.7, 0), (1.7, -0.3), (-1.7, -0.3)],
                      "#eae4d6", M["white"]))
    for s in (-1, 1):
        add(side_band("RampGlass", ramp, 0.1, 2.55, s * 1.72, "#35555b", M["glass"]))
        add(flat_path("RampLight", offset_path(ramp, s * 1.55), 0.12, "#a8f4ff", M["cyan"],
                      zoff=2.62))
    add(flat_path("RampRoof", ramp, 4.1, "#f2ecdf", M["white"], zoff=2.7))
    for i in range(1, len(ramp) - 1):
        x, y, zz = ramp[i]
        add(B.box("RampRib", (4.3, 0.15, 0.16), (x, y, zz + 2.72),
                  color="#ddd6c6", material=M["white"]))
    add(sign_panel("ExitSignStation", "exit", 2.0, -20.6, 4.4, 0.0, 2.4, 1.0, glow=True))
    add(B.box("RampLobby", (7.0, 5.0, 0.4), (2.0, -19.6, 2.5), color="#ded7c8",
              material=M["matte"], bevel=0.05))
    # lift tower at the west end
    add(B.box("StationLift", (3.0, 3.0, 13.0), (sx - 14.5, sy + 2.6, z - 5.0),
              color="#dcd5c4", material=M["white"], bevel=0.08))
    add(B.box("StationLiftG", (3.1, 0.08, 9.0), (sx - 14.5, sy + 1.06, z - 3.0),
              color="#a8f4ff", material=M["cyan"]))
    add(B.box("StationLiftCap", (3.6, 3.6, 0.5), (sx - 14.5, sy + 2.6, z + 1.8),
              color="#e8e2d3", material=M["white"]))
    # ground-level entry pavilion
    add(B.cylinder("StationEntry", 4.2, 0.5, (2.0, -19.0, 2.0), segments=24,
                   color="#d8d0bd", material=M["matte"]))
    for i in range(6):
        a = math.tau * i / 6
        add(B.cylinder("EntryPost", 0.09, 2.8, (2.0 + 3.0 * math.cos(a), -19.0 + 3.0 * math.sin(a), 3.6),
                       segments=6, color="#c8bfae", material=M["metal"]))
        add(B.sphere("EntryL", 0.18, (2.0 + 3.0 * math.cos(a), -19.0 + 3.0 * math.sin(a), 5.05),
                     color="#ffe1b2", material=M["warm"], segments=6, rings=4))


def build_port_terminal(end):
    x, y, z = end
    add(B.box("PortTermDeck", (18, 8, 0.5), (x, y - 1.0, z + 0.15),
              color="#e9e3d4", material=M["white"], bevel=0.04))
    add(B.box("PortTermGlow", (16, 0.14, 0.1), (x, y - 4.9, z + 0.42),
              color="#bff7ff", material=M["cyan"]))
    for k in (-1, 1):
        for xx in (x - 5.0, x + 5.0):
            pts = []
            for i in range(11):
                a = math.pi * i / 10
                pts.append((xx + k * 0.0, y - 1.0 + 4.2 * math.cos(a), z + 3.2 + 2.5 * math.sin(a)))
            add(B.tube("PortTermRib", pts, 0.10, "#f1ecdf", M["white"], segments=5))
    add(sign_panel("PortTermSign", "platform", x, y - 5.4, z + 2.5, 0.0, 2.6, 1.05, glow=True))
    add(sign_panel("PortExitSign", "exit", x - 7.4, y - 3.0, z + 1.9, 0.0, 2.0, 0.85, glow=True))
    for i in range(10):
        add(B.box("PortStair", (4.0, 0.75, 0.22), (x + 7.0, y - 4.2 + i * 0.75, z - 0.5 - i * 0.32),
                  color="#c9c1af", material=M["matte"]))
    for s in (-1, 1):
        add(B.tube("PortStairRail", [(x + 7.0 + s * 1.8, y - 4.4 + i * 0.75, z + 0.4 - i * 0.32) for i in range(10)],
                   0.05, "#cfc8b7", M["metal"]))

# ---------------------------------------------------------------- landscape

def street_lamp(name, x, y, z, ang):
    obs = []
    obs.append(B.cylinder(name + "_p", 0.10, 8.0, (x, y, z + 4.0), segments=8,
                          color="#d8d1c0", material=M["metal"]))
    obs.append(B.box(name + "_arm", (3.4, 0.11, 0.11), (x, y, z + 8.0),
                     rot=(0, 0, ang + math.pi / 2), color="#d8d1c0", material=M["metal"]))
    for s in (-1, 1):
        ox = math.cos(ang) * 0 - math.sin(ang) * s * 1.55
        oy = math.sin(ang) * 0 + math.cos(ang) * s * 1.55
        obs.append(B.box(name + "_head", (0.95, 0.32, 0.14), (x + ox, y + oy, z + 7.82),
                         rot=(0, 0, ang + math.pi / 2), color="#eee8da", material=M["white"]))
        obs.append(B.box(name + "_lens", (0.82, 0.24, 0.05), (x + ox, y + oy, z + 7.72),
                         rot=(0, 0, ang + math.pi / 2), color="#ffe0b4", material=M["warm"]))
    obs.append(B.box(name + "_base", (0.5, 0.5, 0.35), (x, y, z + 0.17),
                     color="#b8b1a1", material=M["matte"]))
    return obs


def solar_panel(name, x, y, z, rot=0.0, tilt=0.42, w=2.0, d=3.0, leg_h=1.1):
    obs = []
    loc0 = (x, y, z)
    obs.append(B.box(name + "_panel", (w, d, 0.08), (x, y, z + leg_h + 0.5),
                     rot=(tilt, 0, rot), color="#263f4a", material=M["panel"]))
    for i in range(1, 4):
        obs.append(B.box(name + "_cell", (0.04, d * 0.9, 0.10), (x, y, z + leg_h + 0.5),
                         rot=(tilt, 0, rot), color="#3f6770", material=M["panel"]))
    for s in (-1, 1):
        ox = math.cos(rot) * 0 - math.sin(rot) * s * (w / 2 - 0.15)
        oy = math.sin(rot) * 0 + math.cos(rot) * s * (w / 2 - 0.15)
        obs.append(B.box(name + "_frame", (0.10, d, 0.12), (x + ox, y + oy, z + leg_h + 0.5),
                         rot=(tilt, 0, rot), color="#c9c2b2", material=M["metal"]))
        obs.append(B.cylinder(name + "_leg", 0.06, leg_h + 0.5,
                              (x + ox * 0.75, y + oy * 0.75, z + (leg_h + 0.5) / 2),
                              segments=5, color="#b8b1a1", material=M["metal"]))
    return obs


def wind_turbine(name, x, y, z, H=42.0, blade=20.0, phase=0.0):
    obs = []
    obs.append(B.lathe(name + "_tower", [(1.9, 0.0), (1.75, 1.2), (1.45, H * 0.35),
                                         (1.05, H * 0.68), (0.75, H * 0.95), (0.7, H)],
                       loc=(x, y, z), segments=14, color="#e9e3d5", material=M["white"]))
    for k in range(3):
        obs.append(flat_ring(name + f"_ring{k}", z + 1.5 + k * (H / 4.2), 1.4 - k * 0.22,
                             1.52 - k * 0.22, 14, x, y, "#c6bfaf", M["metal"]))
    obs.append(B.box(name + "_door", (0.85, 0.14, 1.7), (x, y - 1.45, z + 0.85),
                     color="#4b4d49", material=M["metal"]))
    # nacelle
    obs.append(B.box(name + "_nac", (2.2, 4.6, 2.1), (x, y, z + H + 0.9),
                     color="#eee9db", material=M["white"], bevel=0.25))
    obs.append(B.box(name + "_nacf", (1.5, 1.0, 1.4), (x, y - 2.3, z + H + 0.8),
                     color="#d9d2c2", material=M["white"]))
    obs.append(B.cylinder(name + "_hub", 0.62, 1.2, (x, y - 3.0, z + H + 1.0),
                          rot=(math.pi / 2, 0, 0), segments=12,
                          color="#d7d0c0", material=M["white"], radius2=0.4))
    # three blades in the XZ plane, rotating around -Y axis
    for bi in range(3):
        ph = phase + bi * math.tau / 3
        dvec = (math.cos(ph), 0.0, math.sin(ph))
        pvec = (-math.sin(ph), 0.0, math.cos(ph))
        rings = []
        for k in range(6):
            t = k / 5
            r = 0.8 + t * blade
            chord = (2.6 * (1 - t) ** 0.8 + 0.25)
            thick = (0.42 * (1 - t) + 0.05)
            cx = x + dvec[0] * r
            cz = z + H + 1.0 + dvec[2] * r
            cy = y - 3.0
            ringv = []
            for q in range(4):
                if q == 0:
                    ringv.append((cx + pvec[0] * chord / 2, cy - thick / 2, cz + pvec[2] * chord / 2))
                elif q == 1:
                    ringv.append((cx + pvec[0] * chord / 2, cy + thick / 2, cz + pvec[2] * chord / 2))
                elif q == 2:
                    ringv.append((cx - pvec[0] * chord / 2, cy + thick / 2, cz - pvec[2] * chord / 2))
                else:
                    ringv.append((cx - pvec[0] * chord / 2, cy - thick / 2, cz - pvec[2] * chord / 2))
            rings.append(ringv)
        obs.append(loft_rings(name + f"_blade{bi}", rings, "#eee9dc", M["white"], smooth=False))
        obs.append(B.sphere(name + f"_btip{bi}", 0.12,
                            (x + dvec[0] * (blade + 0.9), y - 3.0, z + H + 1.0 + dvec[2] * (blade + 0.9)),
                            color="#c9a25f", material=M["gold"], segments=6, rings=4))
    obs.append(B.sphere(name + "_beacon", 0.22, (x, y, z + H + 2.3),
                        color="#ff9470", material=M["red"], segments=8, rings=5))
    return obs


def terrace_garden(cx, cy, w, d, levels=3, rot=0.0, crop="#7f9558"):
    """Stepped planted terraces cut into the west hill."""
    obs = []
    base_z = ground_h(cx, cy)
    for k in range(levels):
        z = base_z + 0.2 + k * 0.95
        xx = cx + (k - 1) * w * 0.30
        lo = rounded_loop(xx, cy, z, w, d, 1.8, 3, rot)
        hi = rounded_loop(xx, cy, z + 0.7, w * 0.98, d * 0.98, 1.8, 3, rot)
        obs.append(loft_rings(f"TerrWall{k}", [lo, hi], "#a99a82", M["matte"], smooth=False))
        top = rounded_loop(xx, cy, z + 0.72, w * 0.94, d * 0.94, 1.6, 3, rot)
        verts = top + [(xx, cy, z + 0.72)]
        faces = [(i, (i + 1) % len(top), len(top)) for i in range(len(top))]
        obs.append(B._finish(f"TerrTop{k}", verts, faces, "#7c915c", M["foliage"], smooth=False))
        rng = random.Random(700 + k + int(cx))
        rows = []
        for iy in range(int(d * 0.7 / 1.3)):
            yy = cy - d * 0.35 + iy * 1.3
            rows.extend([(xx - w * 0.32 + ix * 0.9, yy, z + 0.8)
                         for ix in range(int(w * 0.64 / 0.9))])
        add(B.tufts_mesh(f"TerrCrop{k}", rows, height=0.55, color=crop,
                         material=M["foliage"], rng=rng))
        for i in range(5):
            a = rng.uniform(0, math.tau)
            obs.append(B.sphere(f"TerrShrub{k}_{i}", rng.uniform(0.3, 0.55),
                                (xx + math.cos(a) * w * 0.38, cy + math.sin(a) * d * 0.36, z + 0.75),
                                scale=(1.1, 1, 0.7), color=B.vary(srgb("#5f7a50"), 0.1),
                                material=M["foliage"], segments=6, rings=4))
    return obs


def hill_pavilion(x, y):
    z = ground_h(x, y)
    obs = []
    for sxx in (-1, 1):
        for syy in (-1, 1):
            obs.append(B.cylinder("PavPost", 0.16, 4.0,
                                  (x + sxx * 3.4, y + syy * 3.4, z + 2.0), segments=6,
                                  color="#8c6c4a", material=M["wood"]))
    obs.append(B.box("PavDeck", (9.0, 9.0, 0.35), (x, y, z + 0.18), color="#c0b49c",
                     material=M["matte"]))
    for k, (rr, hh, zz) in enumerate([(6.6, 1.5, 4.3), (4.9, 1.2, 5.55)]):
        obs.append(B.lathe("PavRoof", [(rr, z + zz), (rr * 0.94, z + zz + 0.22),
                                       (rr * 0.55, z + zz + 0.75), (rr * 0.1, z + zz + hh)],
                           loc=(x, y, 0), segments=18, color="#5e5b52", material=M["matte"]))
    obs.append(B.cylinder("PavFinial", 0.12, 1.8, (x, y, z + 7.4), segments=6,
                          color="#b78c5f", material=M["gold"]))
    obs.append(B.box("PavBench", (4.6, 0.55, 0.15), (x, y + 2.4, z + 0.65),
                     color="#8a6a49", material=M["wood"]))
    return obs


def build_greenery():
    # boulevard trees and lamps
    p = [(x, y, max(1.72, ground_h(x, y) + 0.16)) for (x, y) in ROAD_MAIN]
    for i in range(2, len(p) - 2, 3):
        x, y, z = p[i]
        if z > 3.4:
            continue
        ang = path_tangent(p, i)
        for s in (-1, 1):
            ox = -math.sin(ang) * s * 8.4
            oy = math.cos(ang) * s * 8.4
            add(tree_future(f"StreetTree{i}_{s}", x + ox, y + oy, z - 0.02, 6.4, 1.9,
                            "#617c51" if (i + s) % 2 else "#6e8557"))
        if i % 6 == 2:
            for s in (-1, 1):
                ox = -math.sin(ang) * s * 6.0
                oy = math.cos(ang) * s * 6.0
                add(street_lamp(f"StreetLamp{i}_{s}", x + ox, y + oy, z, ang))
    # cross street trees
    q = [(x, y, max(1.72, ground_h(x, y) + 0.16)) for (x, y) in ROAD_CROSS]
    for i in range(2, len(q) - 2, 4):
        x, y, z = q[i]
        ang = path_tangent(q, i)
        for s in (-1, 1):
            add(tree_future(f"CrossTree{i}_{s}", x - math.sin(ang) * s * 7.4,
                            y + math.cos(ang) * s * 7.4, z, 5.6, 1.7, "#647f52"))
    # waterfront trees (land side)
    pp = [(x, y, 2.06) for (x, y) in PROMENADE]
    for i in range(2, len(pp) - 2, 3):
        x, y, z = pp[i]
        add(tree_future(f"ShoreTree{i}", x + math.sin(path_tangent(pp, i)) * 4.5,
                        y - math.cos(path_tangent(pp, i)) * 4.5, z + 0.05, 7.0, 2.2,
                        "#688255"))
    # hillside forest
    rng = random.Random(333)
    for i in range(48):
        tx = rng.uniform(-152, -88)
        ty = rng.uniform(-48, 112)
        if tx > -98 and -12 < ty < 28:
            continue
        z = ground_h(tx, ty)
        if z < 2.0:
            continue
        if i % 3 == 0:
            add(tree_pine(f"HillPine{i}", tx, ty, z, rng.uniform(6, 10), "#4b674d"))
        else:
            add(tree_future(f"HillTree{i}", tx, ty, z, rng.uniform(4.5, 8.0),
                            rng.uniform(1.5, 2.3), "#5c7751"))
    # mountain ridge pines
    for i in range(30):
        tx = rng.uniform(-150, 150)
        ty = rng.uniform(112, 146)
        z = ground_h(tx, ty)
        add(tree_pine(f"RidgePine{i}", tx, ty, z, rng.uniform(4, 8), "#4a654b"))
    # launch campus + port green
    for i in range(9):
        a = rng.uniform(0, math.tau)
        px = 64 + math.cos(a) * 10
        py = 62 + math.sin(a) * 8
        if px > 72:
            continue
        add(tree_future(f"PortTree{i}", px, py, ground_h(px, py), 5.5, 1.8, "#668056"))
    # tower base shrubs
    for (tx, ty, rr) in TOWER_BASES:
        for k in range(5):
            a = math.tau * k / 5 + tx * 0.02
            px = tx + math.cos(a) * (rr * 0.95)
            py = ty + math.sin(a) * (rr * 0.95)
            z = ground_h(px, py) + 1.3
            add(B.sphere(f"BaseShrub{int(tx)}_{int(ty)}_{k}", rng.uniform(0.5, 0.9),
                         (px, py, z), scale=(1.2, 1.0, 0.7), color="#5f7a4f",
                         material=M["foliage"], segments=7, rings=4))
    # solar farm between city and port
    for row in range(5):
        for col in range(5):
            sx = 47.6 + col * 2.9
            sy = 60.0 + row * 3.4
            z = ground_h(sx, sy)
            add(solar_panel(f"SolarFarm{row}_{col}", sx, sy, z, rot=0.0, tilt=0.40,
                            w=2.2, d=3.0, leg_h=1.0))
    # solar pergolas on the waterfront
    for i, (px, py) in enumerate([(44, -41.5), (76, -42)]):
        z = 2.06
        add(B.box("PergolaDeck", (7.0, 4.4, 0.3), (px, py, z + 0.15),
                  color="#b08a60", material=M["wood"]))
        for sxx in (-1, 1):
            for syy in (-1, 1):
                add(B.cylinder("PergolaPost", 0.09, 3.0,
                               (px + sxx * 3.1, py + syy * 1.8, z + 1.65), segments=6,
                               color="#d8d1c0", material=M["metal"]))
        for sxx in (-1, 1):
            add(B.box("PergolaPanel", (3.2, 4.0, 0.08), (px + sxx * 1.55, py, z + 3.25),
                      rot=(0.32, 0, 0), color="#263f4a", material=M["panel"]))
        add(B.box("PergolaBeam", (7.2, 0.14, 0.14), (px, py - 1.9, z + 3.0),
                  color="#cec7b7", material=M["wood"]))
    # wind turbines on the ridge
    for i, (wx, wy, hh, ph) in enumerate([(-118, 133, 46, 0.2), (-52, 139, 42, 1.1),
                                          (22, 136, 44, 2.0), (-142, 118, 40, 0.6)]):
        wz = ground_h(wx, wy)
        add(wind_turbine(f"Wind{i}", wx, wy, wz, hh, 20.0, ph))
        add(B.box("WindPad", (8, 8, 0.5), (wx, wy, wz + 0.2), color="#c4bda9",
                  material=M["matte"]))
    # stepped tea terraces on the west hill
    add(terrace_garden(-96, 62, 22, 17, 3, 0.06, "#7d9556"))
    add(terrace_garden(-126, 36, 18, 15, 3, -0.08, "#86975a"))
    add(hill_pavilion(-121, 94))
    # small rain-garden signage pylons
    for i, (gx, gy) in enumerate([(-34, -32), (24, 2)]):
        add(B.box(f"GardenSign{i}", (0.22, 0.22, 2.0), (gx + 4.2, gy, 2.6),
                  color="#d8d1c0", material=M["metal"]))
        add(B.box(f"GardenSignG{i}", (1.2, 0.06, 0.5), (gx + 3.6, gy, 3.1),
                  rot=(0, 0, 0.2), color="#a8f4ff", material=M["cyan"]))

# ---------------------------------------------------------------- spaceport

def pad_slab(name, x0, x1, y0, y1, ztop, color="#aaa79b", thick=0.7):
    add(B.box(name, (x1 - x0, y1 - y0, thick), ((x0 + x1) / 2, (y0 + y1) / 2, ztop - thick / 2),
              color=color, material=M["matte"], bevel=0.04))


def service_arm(name, face, target, z, length=6.8, width=1.35, height=1.5):
    dx, dy = target[0] - face[0], target[1] - face[1]
    L = math.hypot(dx, dy) or 1
    ux, uy = dx / L, dy / L
    ang = math.atan2(uy, ux)
    mx, my = face[0] + ux * length / 2, face[1] + uy * length / 2
    obs = []
    obs.append(B.box(name + "_box", (length, width, height), (mx, my, z),
                     rot=(0, 0, ang), color="#efe9db", material=M["white"]))
    obs.append(B.box(name + "_dark", (length * 0.92, width * 1.01, height * 0.22),
                     (mx, my, z - height * 0.36), rot=(0, 0, ang),
                     color="#3e4648", material=M["dark"]))
    for s in (-1, 1):
        obs.append(B.beam(name + f"_lat{s}",
                          (face[0] + ux * 0.7, face[1] + uy * 0.7, z - height / 2),
                          (face[0] + ux * (length - 0.3), face[1] + uy * (length - 0.3),
                           z + height / 2), 0.12, 0.14, "#75736a", M["metal"]))
    obs.append(B.box(name + "_hinge", (1.0, width + 0.45, height + 0.4),
                     (face[0], face[1], z), rot=(0, 0, ang),
                     color="#d8d1c0", material=M["white"]))
    obs.append(B.box(name + "_tip", (0.5, width + 0.2, height + 0.24),
                     (face[0] + ux * (length - 0.2), face[1] + uy * (length - 0.2), z),
                     rot=(0, 0, ang), color="#b98a4c", material=M["gold"]))
    obs.append(B.box(name + "_light", (0.18, 0.24, 0.1),
                     (face[0] + ux * length * 0.75, face[1] + uy * length * 0.75,
                      z + height / 2 + 0.06), rot=(0, 0, ang),
                     color="#bff7ff", material=M["cyan"]))
    return obs


def build_launch_tower():
    cx, cy = 117.0, 88.0
    z0 = 6.6
    H = 80.0
    levels = 8
    lv = []
    for k in range(levels + 1):
        t = k / levels
        half = 3.6 - 1.1 * t
        lv.append((z0 + t * H, half))
    obs = []
    # corner posts + faces
    for k in range(levels):
        zA, hA = lv[k]
        zB, hB = lv[k + 1]
        for sx in (-1, 1):
            for sy in (-1, 1):
                obs.append(B.beam(f"TwrCol{k}_{sx}_{sy}",
                                  (cx + sx * hA, cy + sy * hA, zA),
                                  (cx + sx * hB, cy + sy * hB, zB),
                                  0.46, 0.46, "#e6dfd0", M["white"]))
        for side in range(4):
            if side == 0:
                pA = [(cx - hA, cy - hA, zA), (cx + hA, cy - hA, zA)]
                pB = [(cx - hB, cy - hB, zB), (cx + hB, cy - hB, zB)]
            elif side == 1:
                pA = [(cx + hA, cy - hA, zA), (cx + hA, cy + hA, zA)]
                pB = [(cx + hB, cy - hB, zB), (cx + hB, cy + hB, zB)]
            elif side == 2:
                pA = [(cx + hA, cy + hA, zA), (cx - hA, cy + hA, zA)]
                pB = [(cx + hB, cy + hB, zB), (cx - hB, cy + hB, zB)]
            else:
                pA = [(cx - hA, cy + hA, zA), (cx - hA, cy - hA, zA)]
                pB = [(cx - hB, cy + hB, zB), (cx - hB, cy - hB, zB)]
            obs.append(B.beam(f"TwrH{k}_{side}", pA[0], pA[1], 0.22, 0.24,
                              "#7d7a70", M["metal"]))
            obs.append(B.beam(f"TwrH2{k}_{side}", pB[0], pB[1], 0.2, 0.22,
                              "#7d7a70", M["metal"]))
            obs.append(B.beam(f"TwrD1{k}_{side}", pA[0], pB[1], 0.16, 0.16,
                              "#989487", M["metal"]))
            obs.append(B.beam(f"TwrD2{k}_{side}", pA[1], pB[0], 0.16, 0.16,
                              "#989487", M["metal"]))
    # platforms
    for k in (2, 4, 6):
        z, half = lv[k]
        add(B.box(f"TwrPlat{k}", (half * 2 + 1.2, half * 2 + 1.2, 0.20),
                  (cx, cy, z), color="#9a978c", material=M["metal"]))
        for side in range(4):
            if side in (0, 1, 2, 3):
                pass
        # simple railing
        for sx in (-1, 1):
            obs.append(B.box(f"TwrRail{k}_{sx}", (half * 2 + 1.1, 0.08, 0.08),
                             (cx, cy + sx * (half + 0.55), z + 1.0),
                             color="#d5cebe", material=M["metal"]))
            obs.append(B.box(f"TwrRail2{k}_{sx}", (0.08, half * 2 + 1.1, 0.08),
                             (cx + sx * (half + 0.55), cy, z + 1.0),
                             color="#d5cebe", material=M["metal"]))
            for j in range(4):
                obs.append(B.box(f"TwrPost{k}_{sx}_{j}", (0.07, 0.07, 1.0),
                                 (cx + sx * (half + 0.55), cy - half + j * (half * 0.66),
                                  z + 0.5), color="#d5cebe", material=M["metal"]))
    # elevator core, offset inside the frame
    add(B.box("TwrCore", (2.5, 2.5, H - 4.0), (cx + 0.9, cy + 1.0, z0 + (H - 4.0) / 2),
              color="#ece6d8", material=M["white"], bevel=0.06))
    add(B.box("TwrCoreG", (0.08, 1.2, H - 12.0), (cx - 0.38, cy + 1.0, z0 + (H - 12) / 2),
              color="#a8f4ff", material=M["cyan"]))
    add(B.box("TwrCoreCap", (3.1, 3.1, 0.8), (cx + 0.9, cy + 1.0, z0 + H - 3.2),
              color="#e3dccd", material=M["white"]))
    # service arms to the rocket
    for i, zz in enumerate((43.0, 57.0)):
        t = (zz - z0) / H
        half = 3.6 - 1.1 * t
        face = (cx - half, cy - half * 0.45)
        obs.extend(service_arm(f"TwrArm{i}", face, (PAD[0], PAD[1]), zz,
                               length=9.2, width=1.35, height=1.55))
    # crane at the top
    zt = z0 + H
    obs.append(B.box("TwrCap", (5.4, 5.4, 1.2), (cx, cy, zt + 0.4),
                     color="#eee8da", material=M["white"]))
    obs.append(B.box("TwrJib", (18.0, 4.0, 0.85), (cx - 7.0, cy, zt + 2.0),
                     rot=(0, 0, 0.0), color="#e8e2d3", material=M["white"], bevel=0.05))
    obs.append(B.box("TwrJibIn", (15.0, 0.5, 0.4), (cx - 6.5, cy, zt + 2.5),
                     color="#b78c5f", material=M["wood"]))
    obs.append(B.box("TwrCounter", (4.4, 4.6, 1.8), (cx + 8.2, cy, zt + 1.4),
                     color="#5b5d58", material=M["metal"]))
    for s in (-1, 1):
        obs.append(B.beam("TwrTie", (cx + 2.2, cy + s * 2.0, zt + 4.0),
                          (cx - 13.0, cy + s * 1.8, zt + 2.2), 0.14, 0.14,
                          "#8d8a80", M["metal"]))
    obs.append(B.box("TwrCab", (2.2, 2.0, 1.7), (cx - 2.5, cy - 2.3, zt + 3.0),
                     color="#f0ebdd", material=M["white"], bevel=0.08))
    obs.append(B.box("TwrCabG", (1.5, 0.06, 0.8), (cx - 2.5, cy - 3.32, zt + 3.15),
                     color="#bff7ff", material=M["cyan"]))
    # lightning mast on top
    obs.append(B.cylinder("TwrMast", 0.10, 12.0, (cx, cy, zt + 7.0), segments=6,
                          color="#cfc8b8", material=M["metal"]))
    obs.append(B.sphere("TwrBeacon", 0.28, (cx, cy, zt + 13.1),
                        color="#ff9570", material=M["red"], segments=8, rings=5))
    # tower name at a readable height
    add(sign_panel("TowerSign", "xinghe", cx - 1.5, cy - 3.15, 23.0, 0.0, 7.4, 2.3, glow=True))
    # pipe raceway up one leg
    for k in range(levels):
        zA, hA = lv[k]
        zB, hB = lv[k + 1]
        obs.append(B.beam(f"TwrPipe{k}", (cx + hA + 0.3, cy - hA + 0.5, zA),
                          (cx + hB + 0.3, cy - hB + 0.5, zB), 0.14, 0.14,
                          "#b1a996", M["metal"]))
    return obs


def build_launch_pad():
    obs = []
    # apron slabs around the flame trench
    pad_slab("PadWest", 76, 112, 54, 106, 6.6, "#a9a69a")
    pad_slab("PadNorth", 112, 130, 86, 106, 6.6, "#a9a69a")
    pad_slab("PadSouth", 112, 130, 54, 74, 6.6, "#a9a69a")
    pad_slab("PadApronExt", 76, 84, 46, 54, 6.6, "#9f9c90")
    # expansion joints
    for i in range(6):
        add(B.box("PadJoint", (36, 0.10, 0.03), (94, 58 + i * 9.0, 6.615),
                  color="#89877f", material=M["matte"]))
        add(B.box("PadJoint2", (0.10, 50, 0.03), (82 + i * 7.4, 80, 6.615),
                  color="#89877f", material=M["matte"]))
    # exhaust well + grating
    add(B.cylinder("ExhaustWell", 8.3, 0.10, (PAD[0], PAD[1], 6.63), segments=32,
                   color="#2d2e2c", material=M["dark"]))
    add(flat_ring("ExhaustRing", 6.64, 7.6, 8.4, 32, PAD[0], PAD[1],
                  "#5d5a52", M["metal"]))
    for i in range(14):
        a = math.tau * i / 14
        add(B.box("ExhaustBar", (0.22, 13.0, 0.10),
                  (PAD[0] + 3.9 * math.cos(a), PAD[1] + 3.9 * math.sin(a), 6.7),
                  rot=(0, 0, a), color="#6d6961", material=M["metal"]))
    # flame trench
    add(B.box("TrenchFloor", (34, 12, 0.35), (129, 80, 3.95), color="#3a3b38", material=M["matte"]))
    for s in (-1, 1):
        add(B.box("TrenchWall", (34, 0.9, 3.0), (129, 80 + s * 6.0, 5.3),
                  color="#82807a", material=M["matte"]))
        add(B.box("TrenchLip", (34, 1.3, 0.22), (129, 80 + s * 6.0, 6.62),
                  color="#b0ad9e", material=M["matte"]))
    for i in range(17):
        add(B.box("TrenchGrate", (0.12, 11.6, 0.10), (112.5 + i * 1.05, 80, 6.58),
                  color="#5b584f", material=M["metal"]))
    # sloped flame deflector at the east end
    verts = [(132, 74, 3.9), (132, 86, 3.9), (146, 86, 3.9), (146, 74, 3.9),
             (132, 74, 4.2), (132, 86, 4.2), (146, 86, 7.6), (146, 74, 7.6)]
    faces = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2),
             (2, 6, 7, 3), (3, 7, 4, 0)]
    obs.append(B._finish("FlameDeflector", verts, faces, "#4c4a42", M["matte"], smooth=False))
    for i in range(6):
        add(B.box("DeflectorStreak", (0.5, 11.4, 0.05), (134 + i * 2.0, 80, 4.3 + i * 0.48),
                  rot=(0, 0, 0), color="#7d7466", material=M["metal"]))
    # launch table / mount
    add(ring_band("LaunchTable", PAD[0], PAD[1], 9.85, 6.75, 8.8, 0.55,
                  "#e8e2d3", M["white"], 32))
    add(flat_ring("LaunchTableTop", 10.42, 6.8, 8.82, 32, PAD[0], PAD[1],
                  "#b98a4c", M["gold"]))
    add(flat_ring("LaunchTableRing", 9.86, 8.78, 9.16, 32, PAD[0], PAD[1],
                  "#b8f0f5", M["cyan"]))
    for i in range(8):
        a = math.tau * i / 8 + 0.2
        x = PAD[0] + 8.6 * math.cos(a)
        y = PAD[1] + 8.6 * math.sin(a)
        obs.append(B.beam(f"TableLeg{i}", (x, y, 6.62), (x * 0.985 + PAD[0] * 0.015,
                                                        y * 0.985 + PAD[1] * 0.015, 9.85),
                          0.55, 0.55, "#cfc8b8", M["metal"]))
        obs.append(B.beam(f"TableBrace{i}", (x, y, 6.7),
                          (PAD[0] + 7.6 * math.cos(a + 0.38), PAD[1] + 7.6 * math.sin(a + 0.38), 9.5),
                          0.22, 0.22, "#9b9688", M["metal"]))
    for i in range(4):
        a = math.tau * i / 4 + 0.35
        x = PAD[0] + 6.2 * math.cos(a)
        y = PAD[1] + 6.2 * math.sin(a)
        obs.append(B.box(f"HoldDown{i}", (1.4, 1.3, 0.9), (x, y, 10.55),
                         rot=(0, 0, a), color="#76736a", material=M["metal"]))
        obs.append(B.box(f"HoldJaw{i}", (1.0, 0.4, 0.55), (x, y, 10.85),
                         rot=(0, 0, a), color="#c7a15a", material=M["gold"]))
    # deluge pipes around the table
    ringp = [(PAD[0] + 11.5 * math.cos(a), PAD[1] + 11.5 * math.sin(a), 6.9)
             for a in [math.tau * i / 32 for i in range(33)]]
    add(B.tube("DelugeRing", ringp, 0.16, "#b9b2a1", M["metal"], segments=6))
    for i in range(8):
        a = math.tau * i / 8
        add(B.cylinder("DelugeNoz", 0.09, 1.3, (PAD[0] + 11.5 * math.cos(a),
                                                PAD[1] + 11.5 * math.sin(a), 7.6),
                       rot=(0.5, 0, a), segments=5, color="#8c8980", material=M["metal"]))
    # blast wall segments at the east end
    for i in range(7):
        yy = 68 + i * 4.0
        add(B.box("BlastWall", (0.9, 3.5, 6.4), (147.5, yy, 9.8), rot=(0, 0, 0.10),
                  color="#9a978b", material=M["matte"]))
        add(B.box("BlastCap", (1.2, 3.7, 0.25), (147.5, yy, 13.05), rot=(0, 0, 0.10),
                  color="#6f6c62", material=M["matte"]))
    # perimeter rail around apron (partial)
    add(railing("PadRail", [(80 + i * 12, 53.2, 6.6) for i in range(5)], 6.6, 1.05, 3.0))
    # painted apron disc, rings and guide markings
    add(B.cylinder("PadDisc", 25.6, 0.05, (PAD[0], PAD[1], 6.62), segments=56,
                   color="#bdbbae", material=M["matte"]))
    add(flat_ring("PadDiscRing", 6.66, 23.8, 25.2, 56, PAD[0], PAD[1],
                  "#84827a", M["matte"]))
    add(flat_ring("PadDiscRing2", 6.665, 13.2, 13.8, 48, PAD[0], PAD[1],
                  "#c7a161", M["gold"]))
    for i in range(12):
        a = math.tau * i / 12
        add(B.box("PadTick", (0.42, 8.5, 0.035),
                  (PAD[0] + 18.2 * math.cos(a), PAD[1] + 18.2 * math.sin(a), 6.665),
                  rot=(0, 0, a), color="#d7d2c2", material=M["matte"]))
    for i in range(16):
        a = math.tau * i / 16
        add(B.box("PadHaz", (1.1, 2.0, 0.04),
                  (PAD[0] + 14.6 * math.cos(a), PAD[1] + 14.6 * math.sin(a), 6.67),
                  rot=(0, 0, a), color="#d8b552" if i % 2 else "#3c3b36",
                  material=M["matte"]))
    for i in range(8):
        a = math.tau * i / 8 + 0.2
        px = PAD[0] + 23.0 * math.cos(a)
        py = PAD[1] + 23.0 * math.sin(a)
        add(B.cylinder("PadLightPole", 0.08, 3.4, (px, py, 8.3), segments=6,
                       color="#d8d1c0", material=M["metal"]))
        add(B.sphere("PadLightGlobe", 0.17, (px, py, 10.1),
                     color="#bff7ff", material=M["cyan"], segments=6, rings=4))
    # chevrons guiding the approach
    for i in range(4):
        add(B.box("PadChevron", (0.55, 3.2, 0.04), (86 + i * 1.4, 62 + i * 1.6, 6.67),
                  rot=(0, 0, -0.65), color="#e0dbcb", material=M["matte"]))
    # small autonomous service cart near the pad
    add(B.box("CartBody", (3.4, 1.9, 0.8), (88, 72, 7.25), rot=(0, 0, 0.5),
              color="#e8e1d2", material=M["white"], bevel=0.06))
    add(B.box("CartDeck", (2.4, 1.6, 0.1), (88, 72, 7.7), rot=(0, 0, 0.5),
              color="#6f8c8b", material=M["panel"]))
    for sx in (-1, 1):
        for sy in (-1, 1):
            add(B.cylinder("CartWheel", 0.36, 0.28,
                           (88 + sx * 1.2 * math.cos(0.5) - sy * 0.85 * math.sin(0.5),
                            72 + sx * 1.2 * math.sin(0.5) + sy * 0.85 * math.cos(0.5), 6.95),
                           rot=(0, math.pi / 2, 0.5), segments=10,
                           color="#3b3e3d", material=M["metal"]))
    return obs


def build_lightning_masts():
    obs = []
    tops = []
    for i, (mx, my, hgt) in enumerate([(129, 56, 46), (84, 108, 46), (129, 103, 46)]):
        z = 6.6
        obs.append(B.lathe(f"Mast{i}", [(1.0, 0.0), (0.9, 1.0), (0.5, hgt * 0.55),
                                        (0.22, hgt * 0.93), (0.10, hgt)],
                           loc=(mx, my, z), segments=12, color="#e7e0d2", material=M["white"]))
        obs.append(B.cylinder(f"MastBase{i}", 1.7, 0.7, (mx, my, z + 0.35), segments=12,
                              color="#b8b1a1", material=M["matte"]))
        obs.append(B.cylinder(f"MastSpike{i}", 0.03, 4.0, (mx, my, z + hgt + 2.0),
                              segments=5, color="#a8a49a", material=M["metal"]))
        obs.append(B.sphere(f"MastBeacon{i}", 0.22, (mx, my, z + hgt + 0.3),
                            color="#ff9470", material=M["red"], segments=8, rings=5))
        tops.append((mx, my, z + hgt))
    tower_top = (117.0, 88.0, 6.6 + 80.0 + 6.0)
    # catenary wires
    def wire(nm, a, b, sag=4.0):
        pts = []
        for i in range(13):
            t = i / 12
            pts.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t,
                        a[2] + (b[2] - a[2]) * t - sag * math.sin(math.pi * t)))
        obs.append(B.tube(nm, pts, 0.035, "#4c4a45", M["metal"], segments=4))
    for i in (0, 2):
        wire(f"MastWire{i}", tops[i], tower_top, 5.0)
    for i in range(3):
        wire(f"MastWireS{i}", tops[i], tops[(i + 1) % 3], 2.0)
    return obs


def build_tank_farm():
    obs = []
    # sphere tanks
    for i, (tx, ty) in enumerate([(70.0, 92.0), (72.0, 101.0)]):
        zc = 12.2
        obs.append(B.sphere(f"TankSphere{i}", 4.3, (tx, ty, zc), scale=(1, 1, 1),
                            color="#eae4d6", material=M["white"], segments=24, rings=14))
        obs.append(ring_band(f"TankBand{i}", tx, ty, zc - 0.4, 4.28, 4.46, 0.55,
                             "#b98a4c", M["gold"], 28))
        for k in range(6):
            a = math.tau * k / 6
            obs.append(B.beam(f"TankLeg{i}_{k}", (tx + 2.6 * math.cos(a), ty + 2.6 * math.sin(a), 6.6),
                              (tx + 3.5 * math.cos(a), ty + 3.5 * math.sin(a), 8.0),
                              0.28, 0.28, "#8c887e", M["metal"]))
        obs.append(B.cylinder(f"TankSkirt{i}", 3.0, 2.0, (tx, ty, 7.6), segments=20,
                              color="#d8d1c1", material=M["metal"]))
        obs.append(B.box(f"TankStair{i}", (0.9, 0.9, 5.0), (tx + 4.0, ty, 9.2),
                          color="#b8b1a1", material=M["metal"]))
    # horizontal tanks
    for i, (tx, ty) in enumerate([(69.0, 80.0), (69.0, 87.0)]):
        obs.append(B.lathe(f"TankCyl{i}", [(1.1, 0.0), (2.6, 0.6), (2.6, 6.4), (1.1, 7.0)],
                           loc=(tx - 3.5, ty, 8.1), rot=(0, math.pi / 2, 0),
                           segments=18, color="#eae4d6", material=M["white"]))
        for k in range(2):
            obs.append(B.box(f"TankSaddle{i}_{k}", (1.2, 4.4, 0.8),
                              (tx - 2.2 + k * 4.4, ty, 9.0),
                              color="#b8b1a1", material=M["metal"]))
        obs.append(B.cylinder(f"TankValve{i}", 0.3, 0.5, (tx - 3.6, ty, 10.9),
                              segments=8, color="#a99f8a", material=M["metal"]))
    # containment walls
    for (x0, x1, y0, y1) in [(64.0, 78.0, 86.0, 106.0), (63.0, 76.0, 74.0, 84.0)]:
        for dx in (0, 1):
            add(B.box("TankWall", (x1 - x0 if dx == 0 else 0.4, 0.4 if dx == 0 else y1 - y0, 1.1),
                      ((x0 + x1) / 2 if dx == 0 else (x0 if dx == 1 else x1),
                       (y0 if dx == 0 else (y0 + y1) / 2), 7.15),
                      color="#b5af9f", material=M["matte"]))
    # pipe rack to the pad
    rack = catmull([(74, 93), (78, 90), (80, 86), (80, 80)], 5)
    for i, (px, py) in enumerate(rack):
        obs.append(B.box("PipePost", (0.16, 0.16, 1.2), (px, py, 7.2),
                         color="#9a968b", material=M["metal"]))
    for k, (dy, col) in enumerate([(0.35, "#b8b1a1"), (0.0, "#b98a4c"), (-0.35, "#8c887e")]):
        pts = [(px, py + dy, 7.75) for (px, py) in rack]
        obs.append(B.tube(f"Pipe{k}", pts, 0.12, col, M["metal"], segments=6))
    # pumping station
    add(B.box("PumpHouse", (4.8, 3.4, 2.6), (57.0, 95.0, 7.9),
              color="#ddd6c6", material=M["white"], bevel=0.06))
    add(B.cylinder("PumpStack", 0.35, 2.2, (58.0, 96.0, 10.2), segments=8,
                   color="#a8a294", material=M["metal"]))
    return obs


def build_searchlights():
    obs = []
    for i, (lx, ly) in enumerate([(84, 63), (121, 63), (84, 98), (121, 98)]):
        z = 6.6
        obs.append(B.cylinder(f"SearchBase{i}", 1.1, 0.5, (lx, ly, z + 0.25), segments=10,
                              color="#b5af9f", material=M["matte"]))
        obs.append(B.cylinder(f"SearchMast{i}", 0.24, 15.0, (lx, ly, z + 8.0), segments=8,
                              color="#e6dfd0", material=M["white"]))
        obs.append(B.box(f"SearchCross{i}", (0.14, 5.4, 0.14), (lx, ly, z + 15.3),
                         color="#d0c9b9", material=M["metal"]))
        for k in (-1, 1):
            yy = ly + k * 2.1
            obs.append(B.cylinder(f"SearchLamp{i}_{k}", 0.55, 0.9, (lx, yy, z + 15.0),
                                  rot=(0, math.pi / 2, 0), segments=12,
                                  color="#d9d3c4", material=M["metal"]))
            obs.append(B.cylinder(f"SearchLens{i}_{k}", 0.46, 0.08,
                                  (lx - 0.5, yy, z + 15.0), rot=(0, math.pi / 2, 0),
                                  segments=12, color="#ffe4b8", material=M["warm"]))
        obs.append(B.sphere(f"SearchBeacon{i}", 0.18, (lx, ly, z + 15.8),
                            color="#ff9470", material=M["red"], segments=6, rings=4))
    return obs


def build_port_buildings():
    obs = []
    # control bunker
    x, y = 66.0, 70.0
    z = ground_h(x, y)
    lo = rounded_loop(x, y, z, 17.0, 10.0, 2.0, 4, 0.0)
    hi = rounded_loop(x, y, z + 5.6, 15.0, 8.5, 2.0, 4, 0.0)
    obs.append(loft_rings("ControlBldg", [lo, hi], "#e9e3d5", M["white"], smooth=False))
    roof = rounded_loop(x, y, z + 5.7, 13.6, 7.4, 1.8, 4, 0.0)
    verts = roof + [(x, y, z + 5.7)]
    faces = [(i, (i + 1) % len(roof), len(roof)) for i in range(len(roof))]
    obs.append(B._finish("ControlRoof", verts, faces, "#728b59", M["foliage"], smooth=False))
    obs.append(B.box("ControlG", (15.0, 0.09, 1.9), (x, y - 5.0, z + 3.4),
                     color="#29494f", material=M["glass"]))
    obs.append(B.box("ControlGlow", (15.2, 0.06, 0.10), (x, y - 5.06, z + 4.45),
                     color="#bff7ff", material=M["cyan"]))
    obs.append(B.cylinder("ControlDishBase", 0.25, 1.6, (x + 5.5, y + 2.0, z + 6.4),
                          segments=8, color="#b8b1a1", material=M["metal"]))
    obs.append(B.lathe("ControlDish", [(0.1, 0.0), (0.75, 0.15), (1.55, 0.8), (1.9, 1.35)],
                       loc=(x + 5.5, y + 2.0, z + 7.2), rot=(0.4, 0, 0.3), segments=16,
                       color="#eae4d6", material=M["white"]))
    obs.append(B.cylinder("ControlRadar", 0.14, 1.6, (x - 4.5, y + 2.5, z + 7.0),
                          segments=6, color="#a8a294", material=M["metal"]))
    obs.append(B.box("ControlRadarBar", (2.6, 0.12, 0.12), (x - 4.5, y + 2.5, z + 7.7),
                     rot=(0, 0, 0.5), color="#d3ccbb", material=M["metal"]))
    obs.extend(sign_panel("ControlSign", "xinghe", x, y - 5.15, z + 2.0, 0.0, 4.6, 1.5, glow=True))
    # a low annex
    obs.append(B.box("ControlAnnex", (7.0, 5.0, 3.2), (x - 9.0, y + 1.0, z + 1.6),
                     color="#ded7c8", material=M["white"], bevel=0.08))
    obs.append(B.box("ControlAnnexG", (6.0, 0.08, 1.0), (x - 9.0, y - 1.55, z + 2.0),
                     color="#28484e", material=M["glass"]))
    # port gateway with the spaceport sign
    gx, gy = 76.0, 58.0
    rot = -1.10
    zz = 6.62
    axis = (math.cos(rot), math.sin(rot))
    for s in (-1, 1):
        px = gx + axis[0] * s * 9.0
        py = gy + axis[1] * s * 9.0
        obs.append(B.cylinder("PortGatePylon", 1.0, 15.0, (px, py, zz + 7.5), segments=12,
                              color="#eee9dc", material=M["white"], radius2=0.55))
        obs.append(B.box("PortGateFin", (0.3, 2.0, 11.0), (px, py, zz + 6.6),
                         rot=(0, 0, rot), color="#b78c5f", material=M["wood"]))
        obs.append(B.box("PortGateGlow", (0.14, 0.14, 12.0),
                         (px + math.sin(rot) * 1.05, py - math.cos(rot) * 1.05, zz + 6.8),
                         color="#bff7ff", material=M["cyan"]))
        obs.append(B.box("PortGateFoot", (3.0, 3.0, 0.7), (px, py, zz + 0.35),
                         color="#cfc7b5", material=M["matte"], bevel=0.06))
    obs.append(B.box("PortGateBeam", (20.0, 1.2, 1.35), (gx, gy, zz + 14.4),
                     rot=(0, 0, rot), color="#eee9dc", material=M["white"], bevel=0.07))
    obs.extend(sign_panel("PortSign", "xinghe", gx + math.sin(rot) * 0.66,
                          gy - math.cos(rot) * 0.66, zz + 13.2, rot, 8.8, 2.75, glow=True))
    # gate plaza + orbit sculpture
    obs.append(B.cylinder("PortPlaza", 14.0, 0.32, (gx, gy, zz - 0.05), segments=40,
                          color="#bdb6a5", material=M["matte"]))
    for rr, rad, col, mat in [(4.6, 0.18, "#f0ebde", M["white"]),
                              (3.4, 0.10, "#bff7ff", M["cyan"])]:
        pts = []
        for i in range(32):
            a = math.tau * i / 32
            pts.append((gx + 6.5 + rr * math.cos(a) * 0.35, gy + rr * math.cos(a) * 0.0,
                        zz + 3.0 + rr * math.sin(a)))
        # stand the ring upright, facing the gate
        pts2 = []
        for i in range(32):
            a = math.tau * i / 32
            lx = rr * math.cos(a)
            lz = rr * math.sin(a)
            pts2.append((69.0 + lx * math.cos(0.3), 61.0 + lx * math.sin(0.3), zz + 3.2 + lz))
        obs.append(B.tube("OrbitRing", pts2, rad, col, mat, segments=5, cyclic=True))
    for s in (-1, 1):
        obs.append(B.box("OrbitFoot", (1.2, 2.8, 0.6), (69.0, 61.0 + s * 1.2, zz + 0.3),
                         color="#d6cebb", material=M["matte"]))
    # water tower for deluge
    wx, wy = 126.0, 109.0
    zw = ground_h(wx, wy)
    for k in range(4):
        a = math.tau * k / 4 + 0.3
        obs.append(B.cylinder("DelugeTowerLeg", 0.22, 10.5,
                              (wx + 2.2 * math.cos(a), wy + 2.2 * math.sin(a), zw + 5.25),
                              segments=7, color="#cfc8b8", material=M["metal"]))
    obs.append(B.lathe("DelugeTowerTank", [(1.0, 0.0), (3.2, 0.5), (3.2, 4.6), (1.2, 5.2)],
                       loc=(wx, wy, zw + 10.0), segments=18, color="#e9e3d5", material=M["white"]))
    obs.append(B.cylinder("DelugeTowerPipe", 0.18, 10.0, (wx - 2.4, wy, zw + 5.0), segments=6,
                          color="#a7a193", material=M["metal"]))
    return obs

# ---------------------------------------------------------------- city assembly

def low_lab():
    x, y = 26.0, 60.0
    z = ground_h(x, y)
    lo = rounded_loop(x, y, z, 20.0, 12.0, 2.6, 4, 0.0)
    hi = rounded_loop(x, y, z + 7.6, 18.2, 10.4, 2.4, 4, 0.0)
    obs = [loft_rings("LabWall", [lo, hi], "#eee9dc", M["white"], smooth=False)]
    roof = rounded_loop(x, y, z + 7.7, 17.0, 9.4, 2.2, 4, 0.0)
    verts = roof + [(x, y, z + 7.7)]
    faces = [(i, (i + 1) % len(roof), len(roof)) for i in range(len(roof))]
    obs.append(B._finish("LabRoof", verts, faces, "#71895a", M["foliage"], smooth=False))
    obs.append(B.box("LabGlass", (15.0, 0.08, 2.5), (x, y - 6.1, z + 3.4),
                      color="#27474d", material=M["glass"]))
    obs.append(B.box("LabGlow", (15.2, 0.06, 0.08), (x, y - 6.15, z + 4.7),
                      color="#bff7ff", material=M["cyan"]))
    for i in range(6):
        obs.append(B.box("LabLouvre", (0.14, 0.2, 3.4), (x - 7 + i * 2.8, y + 6.05, z + 4.6),
                          color="#b78c5f", material=M["wood"]))
    for i in range(4):
        for j in range(2):
            obs.append(B.box("LabSolar", (2.2, 1.5, 0.08),
                              (x - 5.4 + i * 3.6, y - 2.2 + j * 4.0, z + 8.0),
                              rot=(0.28, 0, 0), color="#263f4a", material=M["panel"]))
    for i in range(4):
        a = math.tau * i / 4 + 0.6
        obs.extend(tree_future(f"LabTree{i}", x + 9.5 * math.cos(a), y + 7.0 * math.sin(a),
                               z, 5.5, 1.7, "#617d52"))
    return obs


def city_details():
    obs = []
    # street lanterns along the central plaza paths
    for i in range(8):
        a = math.tau * i / 8
        px, py = 2 + 17.5 * math.cos(a), -9 + 16.5 * math.sin(a) * 0.9
        obs.append(B.cylinder("PathLanternP", 0.07, 3.4, (px, py, 3.4), segments=6,
                              color="#b39267", material=M["wood"]))
        obs.append(B.sphere("PathLantern", 0.24, (px, py, 5.0), scale=(1, 1, 1.35),
                            color="#ffe2b0", material=M["warm"], segments=8, rings=6))
    # waterfront pavilion
    px, py = 58.0, -43.5
    for sxx in (-1, 1):
        for syy in (-1, 1):
            obs.append(B.cylinder("PavWaterPost", 0.13, 3.2,
                                  (px + sxx * 2.6, py + syy * 2.2, 3.6), segments=6,
                                  color="#9a7752", material=M["wood"]))
    obs.append(B.lathe("PavWaterRoof", [(4.4, 5.2), (4.1, 5.45), (2.4, 5.9), (0.15, 6.4)],
                       loc=(px, py, 0), segments=16, color="#5e5b52", material=M["matte"]))
    obs.append(B.box("PavWaterDeck", (7.0, 6.0, 0.3), (px, py, 2.1),
                      color="#b08a60", material=M["wood"]))
    # wayfinding pylons in the plaza
    for i, (sx, sy) in enumerate([(14, -2), (-10, 2)]):
        obs.append(B.box(f"WayPylon{i}", (0.6, 0.3, 2.4), (sx, sy, 2.9),
                          color="#e4ddcf", material=M["white"], bevel=0.04))
        obs.append(B.box(f"WayGlow{i}", (0.44, 0.06, 1.5), (sx, sy - 0.18, 3.1),
                          color="#a8f4ff", material=M["cyan"]))
    # steps from the plaza down to the bay
    for i in range(4):
        obs.append(B.box("BayStep", (16, 1.0, 0.18), (22, -40.5 - i * 1.0, 1.9 - i * 0.18),
                          color="#c2b8a2", material=M["matte"]))
    # low planting mounds at the gate
    for s in (-1, 1):
        obs.append(B.sphere("GateMound", 3.2, (18.5 + s * 5.8, -42.4, 1.5),
                            scale=(1.4, 0.8, 0.5), color="#6b8657", material=M["foliage"],
                            segments=9, rings=6))
    return obs


def bay_details():
    obs = []
    # white solar ferry on the bay
    fx, fy = 70.0, -78.0
    obs.append(B.lathe("FerryHull", [(0.6, 0.0), (2.4, 0.4), (2.6, 0.8), (2.3, 1.2),
                                     (0.5, 1.5)], loc=(fx, fy, 0.55), rot=(0, 0, 0.5),
                       segments=16, color="#eee9dc", material=M["white"]))
    obs.append(B.box("FerryCabin", (5.8, 3.0, 1.9), (fx, fy, 2.55), rot=(0, 0, 0.5),
                      color="#e8e2d4", material=M["white"], bevel=0.16))
    obs.append(B.box("FerryGlass", (5.0, 3.06, 0.85), (fx, fy, 2.75), rot=(0, 0, 0.5),
                      color="#2b4b50", material=M["glass"]))
    obs.append(B.box("FerrySolar", (6.4, 3.4, 0.08), (fx, fy, 3.6), rot=(0.1, 0, 0.5),
                      color="#253f49", material=M["panel"]))
    obs.append(B.box("FerryGlow", (5.4, 0.05, 0.08), (fx, fy - 1.55, 2.2), rot=(0, 0, 0.5),
                      color="#a8f4ff", material=M["cyan"]))
    obs.append(B.cylinder("FerryMast", 0.05, 1.1, (fx - 2.0, fy, 3.9), segments=5,
                          color="#a8a294", material=M["metal"]))
    # floating solar island
    ix, iy = 101.0, -99.0
    obs.append(B.box("FloatDeck", (15.0, 10.0, 0.4), (ix, iy, 0.75),
                      color="#d8d1c0", material=M["white"], bevel=0.05))
    for i in range(4):
        for j in range(3):
            obs += solar_panel(f"FloatSolar{i}_{j}", ix - 5.2 + i * 3.4, iy - 3.2 + j * 3.2,
                               0.95, rot=0.1, tilt=0.3, w=2.0, d=2.4, leg_h=0.7)
    obs.append(B.cylinder("FloatBeacon", 0.18, 0.5, (ix + 6.6, iy + 4.2, 1.2), segments=6,
                          color="#ff9470", material=M["red"]))
    # stream footbridge near the community
    bx, by = -84.0, 22.0
    obs.append(B.box("StreamBridgeDeck", (12.0, 3.4, 0.3), (bx, by, 2.0),
                      color="#b08a60", material=M["wood"]))
    for s in (-1, 1):
        for i in range(7):
            xx = bx - 5 + i * 1.7
            obs.append(B.cylinder("StreamBridgeR", 0.04, 1.0,
                                  (xx, by + s * 1.65, 2.7), segments=5,
                                  color="#d8d1c0", material=M["metal"]))
        obs.append(B.tube("StreamBridgeRail", [(bx - 6, by + s * 1.65, 3.1),
                                               (bx, by + s * 1.65, 3.4),
                                               (bx + 6, by + s * 1.65, 3.1)],
                          0.05, "#d8d1c0", M["metal"], segments=4))
    for s in (-1, 1):
        obs.append(B.box("StreamBridgePier", (1.4, 4.0, 1.9), (bx + s * 4.3, by, 1.0),
                          color="#a89c86", material=M["matte"]))
    return obs



# ---------------------------------------------------------------- eco village

def eco_house(name, x, y, rot, z, roof_style=0):
    obs = []
    obs.append(B.box(name + "_pl", (17.0, 12.0, 0.36), (0, 0, 0.18),
                     color="#a89c86", material=M["matte"], bevel=0.03))
    obs.append(B.box(name + "_main", (9.4, 6.6, 5.2), (0.6, 0.4, 3.0),
                     color="#efe9db", material=M["white"], bevel=0.05))
    obs.append(B.box(name + "_wing", (5.2, 5.4, 4.0), (-6.4, -0.6, 2.4),
                     color="#e9e2d3", material=M["white"], bevel=0.05))
    for (cx0, cy0, ww, dd) in [(-8.2, 0, 0.22, 11.6), (8.2, 0, 0.22, 11.6),
                                (-4.2, -5.8, 4.2, 0.22), (4.6, -5.8, 6.8, 0.22),
                                (0, 5.8, 16.4, 0.22)]:
        obs.append(B.box(name + "_cw", (ww, dd, 1.25), (cx0, cy0, 0.8),
                         color="#e2dac8", material=M["white"], bevel=0.02))
        obs.append(B.box(name + "_cc", (ww + 0.1, dd + 0.1, 0.14), (cx0, cy0, 1.48),
                         color="#5f6d59", material=M["matte"]))
    for s in (-1, 1):
        obs.append(B.box(name + "_gp", (0.32, 0.32, 2.3), (s * 1.65 - 0.9, -5.8, 1.5),
                         color="#7b6146", material=M["wood"]))
    obs.append(B.box(name + "_gl", (4.0, 0.4, 0.25), (-0.9, -5.8, 2.7),
                     color="#5a4c3b", material=M["wood"]))
    for i in range(5):
        obs.append(B.box(name + "_lv", (0.10, 0.15, 3.0), (-1.6 + i * 1.25, -3.38, 2.4),
                         color="#ad8356", material=M["wood"]))
    for i in range(3):
        obs.append(B.box(name + "_win", (1.7, 0.08, 1.6), (-2.4 + i * 2.4, -2.94, 2.6),
                         color="#ffd8a4" if i == 1 else "#3e5f63",
                         material=M["warm"] if i == 1 else M["glass"]))
    obs.append(B.box(name + "_door", (1.2, 0.1, 2.0), (3.0, -2.95, 1.35),
                     color="#59452f", material=M["wood"]))
    if roof_style == 0:
        obs.extend(B.tile_roof(name + "_roof", 0.6, 0.4, 5.6, 11.4, 8.4, 1.45, 0.18,
                               "#878b7c", M["matte"], curl=0.32, nx=10, ny=14))
        obs.append(B.box(name + "_roof2", (6.6, 7.0, 0.16), (-6.4, -0.6, 4.35),
                         rot=(0.14, 0, 0), color="#7d8173", material=M["matte"]))
    else:
        obs.append(B.box(name + "_roof", (11.6, 8.6, 0.35), (0.6, 0.4, 5.75),
                         color="#6b8554", material=M["foliage"], bevel=0.05))
        for i in range(3):
            obs.append(B.box(name + "_sol", (1.8, 1.2, 0.08), (-1.4 + i * 2.2, 1.4, 6.1),
                             rot=(0.28, 0, 0), color="#263f4a", material=M["panel"]))
    obs.append(B.box(name + "_garden", (10.0, 5.0, 0.12), (0.4, -2.9, 0.42),
                     color="#7f935f", material=M["foliage"]))
    obs.append(B.cylinder(name + "_basin", 1.25, 0.3, (-3.2, -3.8, 0.55), segments=14,
                          color="#a99d86", material=M["matte"]))
    obs.append(B.sphere(name + "_basinw", 1.05, (-3.2, -3.8, 0.62), scale=(1, 1, 0.12),
                        color="#3e5f63", material=M["glass"], segments=14, rings=4))
    obs.extend(tree_future(name + "_tree", 3.8, -3.0, 0.5, 5.4, 1.9, "#557444"))
    for i in range(8):
        obs.append(B.sphere(name + f"_peb{i}", 0.18 + 0.05 * (i % 3),
                            (0.5 + i * 0.7, 3.0, 0.5), scale=(1.2, 1, 0.5),
                            color="#9d9483", material=M["matte"], segments=5, rings=4))
    B.apply_xform(obs, (x, y, z), rot)
    return obs


def eco_village():
    obs = []
    rng = random.Random(812)
    houses = [(-56, -66, 0.15, 0), (-76, -78, -0.22, 0), (-48, -91, 0.42, 1),
              (-88, -62, 0.08, 1), (-67, -102, -0.35, 0)]
    for i, (hx, hy, hr, style) in enumerate(houses):
        obs.extend(eco_house(f"EcoHouse{i}", hx, hy, hr, ground_h(hx, hy), style))
    hx, hy = -64.0, -55.0
    hz = ground_h(hx, hy)
    lo = rounded_loop(hx, hy, hz, 17.0, 8.0, 2.0, 4, 0.08)
    hi = rounded_loop(hx, hy, hz + 4.6, 15.6, 7.0, 1.8, 4, 0.08)
    obs.append(loft_rings("VillageHall", [lo, hi], "#eee8da", M["white"], smooth=False))
    obs.append(B.lathe("HallRoof", [(9.8, hz + 4.8), (9.4, hz + 5.2), (5.4, hz + 5.9),
                                    (0.3, hz + 6.5)], loc=(hx, hy, 0), segments=20,
                       color="#6d7d5c", material=M["matte"]))
    obs.append(B.box("HallGlass", (13.0, 0.08, 2.4), (hx, hy - 4.1, hz + 2.7),
                     color="#3e5f63", material=M["glass"]))
    for i in range(9):
        obs.append(B.box("HallFin", (0.12, 0.18, 4.0), (hx - 6.2 + i * 1.55, hy - 4.15, hz + 2.8),
                         color="#ad8356", material=M["wood"]))
    obs.append(B.box("HallDeck", (19.0, 10.0, 0.2), (hx, hy, hz + 0.1),
                     color="#b8ad96", material=M["matte"]))
    px, py = -68.0, -84.0
    pz = ground_h(px, py) + 0.15
    add_water(water_poly("Water_Village", px, py, pz + 0.05, 7.2, 4.4, 40, 0.06))
    add(B.ring_wall("VillageRim", px, py, pz - 0.5, 7.5, 4.7, 0.9, 0.55, 40,
                    "#a89c86", M["matte"]))
    for i in range(10):
        a = math.tau * i / 10
        obs.append(B.sphere(f"VillR{i}", 0.3 + 0.15 * (i % 3),
                            (px + 8.2 * math.cos(a), py + 5.2 * math.sin(a), pz + 0.2),
                            scale=(1.2, 1, 0.5), color="#9c9280", material=M["matte"],
                            segments=5, rings=4))
    path = catmull([(18, -40), (-6, -43), (-28, -47), (-42, -55), (-52, -62),
                    (-58, -70)], 8)
    pp = [(x, y, max(1.66, ground_h(x, y) + 0.12)) for (x, y) in path]
    obs.append(sweep_profile("VillagePath", pp, [(-1.5, 0), (1.5, 0), (1.5, -0.25), (-1.5, -0.25)],
                             "#b08a60", M["wood"]))
    bx, by = -2.0, -42.6
    obs.append(B.box("LaneBridgeDeck", (13.0, 3.2, 0.28), (bx, by, 1.95), rot=(0, 0, 0.14),
                     color="#b08a60", material=M["wood"]))
    for s in (-1, 1):
        obs.append(B.tube("LaneBridgeRail", [(bx - 6, by + s * 1.5, 2.9), (bx, by + s * 1.5, 3.15),
                                             (bx + 6, by + s * 1.5, 2.9)],
                          0.05, "#d8d1c0", M["metal"], segments=4))
        for i in range(5):
            obs.append(B.cylinder("LaneBridgePost", 0.04, 1.1,
                                  (bx - 5 + i * 2.5, by + s * 1.5, 2.55), segments=5,
                                  color="#d8d1c0", material=M["metal"]))
    for i in range(2, len(pp) - 2, 2):
        x, y, z = pp[i]
        add(B.sphere(f"VillLamp{i}", 0.22, (x + 1.8, y, z + 1.1), scale=(1, 1, 1.3),
                     color="#ffe2b0", material=M["warm"], segments=7, rings=5))
        add(B.cylinder(f"VillLampP{i}", 0.07, 1.1, (x + 1.8, y, z + 0.55), segments=5,
                       color="#8f6f4e", material=M["wood"]))
    for i, (fx, fy, fw, fd, fr) in enumerate([(-92, -94, 18, 11, 0.08),
                                              (-40, -83, 13, 9, -0.1),
                                              (-84, -110, 15, 9, 0.02)]):
        fz = ground_h(fx, fy) + 0.1
        obs.append(B.box(f"FieldBase{i}", (fw + 1.2, fd + 1.2, 0.35), (fx, fy, fz - 0.05),
                         rot=(0, 0, fr), color="#8f8468", material=M["matte"]))
        add(B.rice_field(f"VillageCrop{i}", fx, fy, fz + 0.18, fw, fd, fr,
                         spacing=1.05, height=0.5, colors=("#7f9552", "#8d9f5b"),
                         material=M["foliage"], rng=rng, blade_width=0.035, blades=3))
        for j in range(4):
            yy = fy - fd / 2 + fd * (j + 0.5) / 4
            obs.append(B.box(f"FieldBund{i}_{j}", (fw + 1.4, 0.3, 0.28), (fx, yy, fz + 0.12),
                             rot=(0, 0, fr), color="#9a8f74", material=M["matte"]))
    for i in range(16):
        tx = rng.uniform(-98, -36)
        ty = rng.uniform(-112, -52)
        if any(abs(tx - hx2) < 11 and abs(ty - hy2) < 9 for (hx2, hy2, _, _) in houses):
            continue
        if abs(tx - px) < 10 and abs(ty - py) < 7:
            continue
        obs.extend(tree_future(f"VillageTree{i}", tx, ty, ground_h(tx, ty),
                               rng.uniform(5.0, 8.0), rng.uniform(1.7, 2.5),
                               "#557343" if i % 2 else "#617e4a"))
    for i in range(9):
        wx = 8 - i * 7.5
        wy = -42 - i * 3.0
        obs.append(B.box("LaneWall", (6.0, 0.4, 0.7), (wx, wy, ground_h(wx, wy) + 0.4),
                         rot=(0, 0, -0.25), color="#a99d86", material=M["matte"]))
    return obs


def build_city():
    g = ground_h
    tower_petal("B1", -50, 28, max(1.55, g(-50, 28)), 98, 12.5, 16, phase=0.2, moon=True)
    tower_ribbon("B2a", -16, 18, max(1.55, g(-16, 18)), 70, 9.5, 7.5, twist=0.55, floors=16)
    tower_ribbon("B2b", -14, 44, max(1.55, g(-14, 44)), 62, 9.0, 7.0, twist=-0.4, floors=14,
                 phase=0.7)
    tower_petal("B3", -72, 2, max(1.55, g(-72, 2)), 82, 10.0, 14, phase=1.1)
    tower_terrace("B4", -60, 44, max(1.55, g(-60, 44)), 16.0, 14.0, 44, 4, 0.15)
    tower_petal("B6", -42, -20, max(1.55, g(-42, -20)), 58, 8.5, 11, phase=0.6)
    tower_petal("A1", 28, -10, max(1.55, g(28, -10)), 66, 9.0, 12, phase=1.4)
    tower_ribbon("A2", -18, -25, max(1.55, g(-18, -25)), 60, 9.0, 7.0, twist=-0.5, floors=14,
                 phase=1.7)
    tower_petal("A3a", 34, 14, max(1.55, g(34, 14)), 52, 7.5, 10, phase=0.9)
    tower_terrace("A3b", 38, 28, max(1.55, g(38, 28)), 9.0, 8.0, 36, 4, -0.25)
    tower_petal("B5", 20, 45, max(1.55, g(20, 45)), 54, 8.0, 11, phase=2.0)
    tower_terrace("C1", -104, 34, g(-104, 34) - 0.3, 14.0, 12.0, 28, 4, 0.4)
    tower_terrace("C2", -122, 52, g(-122, 52) - 0.3, 12.0, 10.0, 24, 4, -0.2)
    tower_petal("C3", -108, 78, g(-108, 78) - 0.3, 40, 6.5, 8, phase=0.3)
    tower_petal("C6", -132, 16, g(-132, 16) - 0.3, 34, 6.0, 7, phase=1.9)
    tower_ribbon("D1", 38, 78, max(1.55, g(38, 78)), 28, 8.5, 6.5, twist=0.8, floors=8,
                 phase=0.35)
    # sky bridges
    skybridge("BridgeB2a", -16, 18, -14, 44, 32, 3.2, 3.4, 1.1, False)
    skybridge("BridgeB2b", -16, 18, -14, 44, 46, 3.2, 3.4, 1.1, False)
    skybridge("BridgeB1", -50, 28, -16, 18, 48, 3.4, 3.6, 1.4, True)
    skybridge("BridgeA1", 28, -10, 34, 14, 30, 3.2, 3.4, 1.1, False)
    skybridge("BridgeA3", 34, 14, 38, 28, 22, 3.0, 3.2, 0.8, False)
    skybridge("BridgeB6", -42, -20, -16, 18, 30, 3.2, 3.4, 1.3, True)
    skybridge("BridgeB3", -72, 2, -50, 28, 56, 3.2, 3.4, 1.5, False)
    # plazas, community, lab, bayside furniture
    add(city_plaza())
    add(community_center())
    add(city_gate())
    add(low_lab())
    add(city_details())
    add(bay_details())
    add(bay_shore_details())
    add(eco_village())

# ---------------------------------------------------------------- zone assembly

def zone_materials():
    m = {}
    m["matte"] = B.vmat("F_Matte", 0.90)
    m["white"] = B.vmat("F_White", 0.72)
    m["metal"] = B.vmat("F_Metal", 0.38, 0.45)
    m["wood"] = B.vmat("F_Wood", 0.85)
    m["panel"] = B.vmat("F_Panel", 0.30, 0.35)
    m["foliage"] = B.vmat("F_Foliage", 0.95)
    m["glass"] = B.mat("F_Glass", "#4a6e72", rough=0.26, metal=0.2)
    m["cyan"] = B.mat("EmisCyan", "#a8f7ff", rough=0.5, emission="#7fe8ff", emis_strength=2.2)
    m["warm"] = B.mat("EmisWarm", "#ffd9a8", rough=0.5, emission="#ffbe78", emis_strength=1.8)
    m["red"] = B.mat("EmisRed", "#ff6d52", rough=0.5, emission="#ff4a34", emis_strength=2.4)
    m["gold"] = B.vmat("F_Gold", 0.32, 0.7)
    m["dark"] = B.vmat("F_Dark", 0.52, 0.2)
    m["signs"] = B.mat("Signs", texture=os.path.join(B.ASSETS, "signs_atlas.png"), rough=0.75)
    m["signsGlow"] = B.mat("SignsGlow", texture=os.path.join(B.ASSETS, "signs_atlas.png"),
                           rough=0.5, emission="#cfefff", emis_strength=0.8)
    m["water"] = B.mat("Water", "#315f63", rough=0.10, metal=0.2, alpha=0.95)
    return m


def build_fx():
    B.empty("FX_Hotspot", (94.0, 71.0, 10.5), size=2.0)
    B.empty("FX_Smoke_1", (102.0, 80.0, 7.2), size=3.0)
    B.empty("FX_Smoke_2", (105.0, 78.0, 7.2), size=2.4)
    B.empty("FX_Light_Pad_1", (84, 63, 22.0))
    B.empty("FX_Light_Pad_2", (121, 63, 22.0))
    B.empty("FX_Light_Pad_3", (84, 98, 22.0))
    B.empty("FX_Light_Pad_4", (121, 98, 22.0))
    B.empty("FX_Light_Tower", (117.0, 88.0, 96.0))
    B.empty("FX_Light_Station", (-8.0, -35.6, 18.8))
    B.empty("FX_RocketBase", (PAD[0], PAD[1], ROCKET_Z), size=2.0)


def zone():
    global ALL, WATER, M
    B.reset(SEED + 31)
    ALL = []
    WATER = []
    M = zone_materials()

    build_terrain()
    build_water()
    build_roads()
    build_city()
    build_greenery()
    build_transit()
    add(build_launch_pad())
    add(build_launch_tower())
    add(build_lightning_masts())
    add(build_tank_farm())
    add(build_searchlights())
    add(build_port_buildings())

    # red thread continuation across the pad to the launch table
    add(flat_path("PadRedThread", [(84, 63, 6.62), (90, 69, 6.62), (97, 76, 6.62),
                                   (101.5, 79.4, 6.62)], 0.26, "#ff6c4e", M["red"]))
    add(flat_ring("PadRedRing", 6.63, 10.1, 10.32, 40, PAD[0], PAD[1],
                  "#ff6c4e", M["red"]))
    # approach pylons / light line along the port road
    for i in range(7):
        px = 82 + i * 2.3
        py = 62 + i * 2.3
        add(B.cylinder("ApproachLamp", 0.07, 2.4, (px, py, 8.0), segments=6,
                       color="#d8d1c0", material=M["metal"]))
        add(B.sphere("ApproachLampL", 0.16, (px, py, 9.2),
                     color="#bff7ff", material=M["cyan"], segments=6, rings=4))
    # perimeter fence and service gate on the plateau south edge
    for i in range(10):
        fx = 68 + i * 7.0
        fy = 47.5 + 0.12 * i
        fz = ground_h(fx, fy)
        add(B.box("PortFence", (0.12, 0.12, 1.6), (fx, fy, fz + 0.8),
                  color="#d8d1c0", material=M["metal"]))
        add(B.box("PortFenceL", (0.16, 0.16, 0.1), (fx, fy, fz + 1.62),
                  color="#bff7ff", material=M["cyan"]))
    for i in range(9):
        fx = 68 + i * 7.0 + 3.5
        fy = 47.6 + 0.12 * i
        fz = ground_h(fx, fy)
        add(B.box("PortFenceRail", (7.0, 0.06, 0.06), (fx, fy, fz + 1.35),
                  rot=(0, 0, 0.02), color="#d8d1c0", material=M["metal"]))
    build_fx()

    # make sure every mesh in the scene is included (towers etc. add themselves)
    seen = set()
    for ob in ALL:
        if ob is not None:
            seen.add(ob.name)
    for ob in bpy.context.scene.objects:
        if ob.type == "MESH" and ob.name not in seen:
            ALL.append(ob)

    # join static geometry by material
    B.join_materials("Future", ALL)

    tris = vtx = 0
    for ob in bpy.context.scene.objects:
        if ob.type == "MESH":
            vtx += len(ob.data.vertices)
            tris += sum(len(p.vertices) - 2 for p in ob.data.polygons)
    print(f"FUTURE STATS tris={tris} verts={vtx} objs={len(bpy.context.scene.objects)}")
    for ob in bpy.context.scene.objects:
        if ob.type == "MESH":
            print("  MESH", ob.name, ob.data.materials[0].name if ob.data.materials else "-",
                  sum(len(p.vertices) - 2 for p in ob.data.polygons))
    B.save_blend(ZONE_BLEND)
    B.export_glb(ZONE_GLB)
    print("FUTURE EXPORTED", os.path.getsize(ZONE_GLB))


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    only = "all"
    for i, a in enumerate(args):
        if a == "--only" and i + 1 < len(args):
            only = args[i + 1]
    if only in ("rocket", "all"):
        rocket()
    if only in ("zone", "all"):
        zone()
