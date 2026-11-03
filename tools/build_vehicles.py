"""Original vehicles for 《山河织路》. First: the rural two-wheeled rickshaw.
All geometry is authored here; no downloaded models."""
from __future__ import annotations
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
import blib as B  # noqa: E402

B.reset(1983)
W = B.vmat("V_Wood", 0.82)
W2 = B.vmat("V_WoodDark", 0.86)
M = B.vmat("V_Metal", 0.38, 0.62)
C = B.vmat("V_Cloth", 0.92)
R = B.vmat("V_Red", 0.8)
S = B.vmat("V_Straw", 0.95)
P = B.vmat("V_Paint", 0.55)


def wheel(side):
    x = side * 0.92
    parts = []
    rim_pts = []
    for i in range(25):
        a = math.tau * i / 24
        rim_pts.append((0, math.cos(a) * 0.62, math.sin(a) * 0.62))
    parts.append(B.tube(f"Rim_{side}", rim_pts, .045, "#4b4740", M, segments=5, cyclic=True))
    for i in range(12):
        a = math.tau * i / 12
        p1 = (0, math.cos(a) * 0.1, math.sin(a) * 0.1)
        p2 = (0, math.cos(a) * 0.58, math.sin(a) * 0.58)
        parts.append(B.beam(f"Spoke_{side}_{i}", p1, p2, .028, .028, "#7a5736" if i % 2 else "#8b6744", W))
    parts.append(B.cylinder(f"Hub_{side}", .13, .22, (0, 0, 0), rot=(0, math.pi / 2, 0),
                            segments=12, color="#6b4a30", material=W, bevel=.02))
    parts.append(B.cylinder(f"HubIron_{side}", .07, .24, (0, 0, 0), rot=(0, math.pi / 2, 0),
                            segments=10, color="#4b4740", material=M))
    ob = B.join_group(f"Wheel_{'L' if side < 0 else 'R'}", parts)
    ob.location = (x, 0, 0.64)
    return ob


def rickshaw():
    body = []
    # chassis: two long timbers and crossbars
    for sx in (-0.62, 0.62):
        body.append(B.box("Chassis", (.14, 3.0, .13), (sx, 0.15, .62), color="#6f4f31", material=W, bevel=.02))
    for yy in (-0.75, 0.1, 0.95):
        body.append(B.box("Cross", (1.5, .12, .12), (0, yy, .62), color="#7a5738", material=W, bevel=.015))
    # bed planks
    for i in range(7):
        body.append(B.box("Bed", (1.28, .235, .055), (0, -0.72 + i * .25, .74),
                          color="#8a6240" if i % 2 else "#7b5638", material=W, bevel=.008))
    # side rails
    for sx in (-0.72, 0.72):
        body.append(B.box("Rail", (.07, 1.65, .16), (sx, -0.05, .95), color="#6e4d30", material=W, bevel=.012))
        body.append(B.box("RailPost", (.08, .08, .42), (sx, -0.82, .84), color="#6e4d30", material=W))
        body.append(B.box("RailPost", (.08, .08, .42), (sx, 0.7, .84), color="#6e4d30", material=W))
    # handles (pulling shafts) forward
    for sx in (-0.6, 0.6):
        body.append(B.beam("Handle", (sx, 1.15, .66), (sx, 2.55, .9), .075, .09, "#7a5737", W))
        body.append(B.cylinder("Grip", .085, .42, (sx, 2.36, .87), rot=(0.18, 0, 0), segments=8,
                               color="#4b3423", material=W2))
    # front support leg
    for sx in (-0.6, 0.6):
        body.append(B.beam("Leg", (sx, 1.3, .6), (sx, 1.45, .08), .055, .06, "#6e4d30", W))
    # canopy posts
    for sx in (-1.0, 1.0):
        for yy in (-0.62, 0.72):
            body.append(B.cylinder("CanopyPost", .048, 1.35, (sx, yy, 1.52), segments=8,
                                   color="#6b4a2f", material=W))
    # canopy top: cloth shell, ribs along y, arched in x
    secs = []
    for iy in range(7):
        y = -0.8 + iy * 0.28
        pts = []
        for ix in range(9):
            x = -1.08 + ix * 0.27
            z = 2.18 + 0.18 * math.cos((x / 1.08) * math.pi / 2) - 0.04 * abs(iy - 3)
            pts.append((x, y, z))
        secs.append(pts)
    verts, faces = [], []
    for pts in secs:
        for p in pts:
            verts.append(p)
    for iy in range(len(secs) - 1):
        for ix in range(8):
            a = iy * 9 + ix
            faces.append((a, a + 1, a + 10, a + 9))
    cloth = B._finish("CanopyCloth", verts, faces, "#8c9a7c", C, smooth=True)
    body.append(cloth)
    # scalloped fringe
    for side in (-1, 1):
        for iy in range(6):
            y = -0.72 + iy * .28
            x = side * 1.09
            body.append(B.quad("Fringe", [(x, y, 2.18), (x, y + .12, 2.18),
                                          (x, y + .06, 1.94), (x, y - .02, 2.0)], "#a7b193", C))
    # bamboo ribs across canopy
    for iy in range(7):
        y = -0.8 + iy * 0.28
        pts = []
        for ix in range(9):
            x = -1.08 + ix * 0.27
            z = 2.20 + 0.18 * math.cos((x / 1.08) * math.pi / 2) - 0.04 * abs(iy - 3)
            pts.append((x, y, z + .015))
        body.append(B.tube("CanopyRib", pts, .022, "#5a432d", W2, segments=5))
    # back panel
    body.append(B.quad("BackPanel", [(-1.04, .84, 1.02), (1.04, .84, 1.02), (1.04, .84, 2.16), (-1.04, .84, 2.16)],
                       "#7f8d70", C))
    # seat cushion and back
    body.append(B.box("Seat", (1.45, .78, .18), (0, .0, 1.0), color="#9a4c3b", material=R, bevel=.04))
    body.append(B.box("SeatBack", (1.45, .16, .55), (0, .38, 1.28), color="#8f4638", material=R, bevel=.03))
    body.append(B.box("SeatBase", (1.4, .8, .12), (0, 0, .86), color="#6c4b31", material=W))
    # straw hat on the seat
    body.append(B.lathe("StrawHat", [(0.32, 0), (0.36, .02), (0.2, .14), (0.02, .2)],
                        loc=(0.35, -0.05, 1.12), segments=16, color="#c6a766", material=S))
    # basket on the back
    body.append(B.lathe("Basket", [(0.35, 0), (0.4, .08), (0.43, .45), (0.36, .55)],
                        loc=(-0.35, -0.55, .8), segments=12, color="#b7955d", material=S))
    body.append(B.tube("BasketHandle", [(-0.6, -0.55, 1.33), (-0.35, -0.55, 1.5), (-0.1, -0.55, 1.33)],
                       .025, "#8a6a3e", S, segments=5))
    # red bundle / cloth
    body.append(B.sphere("Bundle", .3, (0.1, -0.5, 1.1), scale=(1.2, .9, .7), color="#a5372b", material=R,
                         segments=10, rings=6))
    body.append(B.box("Tassel", (.06, .06, .35), (0.62, 2.2, .98), color="#a5372b", material=R))
    # rope coil on side
    rope = []
    for i in range(25):
        a = math.tau * i / 24
        rope.append((0.76, -0.2 + .18 * math.cos(a), 1.0 + .18 * math.sin(a)))
    body.append(B.tube("Rope", rope, .018, "#b49a6a", S, segments=4, cyclic=True))
    # join body by material
    joined = B.join_materials("Rickshaw", body, skip_prefixes=())
    wl = wheel(-1)
    wr = wheel(1)
    root = B.empty("RickshawRoot", (0, 0, 0))
    for ob in joined + [wl, wr]:
        ob.parent = root
        ob.matrix_parent_inverse = root.matrix_world.inverted()
    B.save_blend(os.path.join(B.ROOT, "assets", "vehicles", "rickshaw.blend"))
    B.export_glb(os.path.join(B.ROOT, "assets", "vehicles", "rickshaw.glb"))


if __name__ == "__main__":
    rickshaw()
    print("RICKSHAW EXPORTED", os.path.getsize(os.path.join(B.ROOT, "assets", "vehicles", "rickshaw.glb")))
