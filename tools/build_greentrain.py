"""The green passenger train (green-skinned train), original procedural model.
Forward +Y, origin at rail centre, Z up. Export as a single animated train."""
from __future__ import annotations
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
import blib as B  # noqa: E402

B.reset(1993)
rng = random.Random(1993)
ALL = []
green = B.vmat("TrainGreen", 0.78)
green2 = B.vmat("TrainGreen2", 0.82)
yellow = B.vmat("TrainYellow", 0.7)
roof = B.vmat("TrainRoof", 0.85)
under = B.vmat("TrainUnder", 0.9)
metal = B.vmat("TrainMetal", 0.4, 0.55)
glass = B.mat("TrainGlass", "#13232a", rough=0.18, metal=0.3)
warm = B.mat("TrainWarm", "#ffc684", rough=0.5, emission="#ffbf7a", emis_strength=1.8)
cool = B.mat("TrainCool", "#cfe9ff", rough=0.5, emission="#cfe9ff", emis_strength=1.1)
head = B.mat("TrainHead", "#fff2c8", emission="#fff0c0", emis_strength=4.5)
tail = B.mat("TrainTail", "#ff3a2c", emission="#ff3020", emis_strength=3.0)


def add(o):
    if isinstance(o, (list, tuple)):
        for q in o:
            add(q)
    else:
        ALL.append(o)


def rounded_section(w, h, top_round, bottom_round, z0, n=18):
    """Return a closed loop of (x,z) around a train body section."""
    x0, x1 = -w / 2, w / 2
    zb, zt = z0, z0 + h
    pts = []
    # bottom edge
    for i in range(4):
        pts.append((x0 + (x1 - x0) * i / 3, zb + (bottom_round if i in (0, 3) else 0)))
    # right side up to roof
    pts.append((x1, zb + bottom_round + (h - top_round - bottom_round) * .5))
    # roof arc
    for i in range(7):
        a = math.pi * i / 6
        pts.append((w / 2 * math.cos(a) * .98, zt - top_round + top_round * math.sin(a)))
    # left side down
    pts.append((x0, zb + bottom_round + (h - top_round - bottom_round) * .5))
    return pts


def carriage(cy, length=24.0, is_loco=False):
    # body loft
    secs = []
    n = 9 if is_loco else 7
    if is_loco:
        # front cab at +Y, taper at the front lower
        profiles = [
            (-length / 2, 1.00, 0.96), (-length / 2 + 2, 1.00, 1.0),
            (-2, 1.0, 1.0), (4, 1.0, 1.0), (7.0, .98, .96), (8.8, .94, .86), (9.5, .82, .70),
        ]
        for (y, sx, sz) in profiles:
            pts = rounded_section(3.1 * sx, 3.0 * sz, .42, .22, .95, 16)
            secs.append(((0, cy + y, 0), pts))
    else:
        for i in range(n):
            y = -length / 2 + length * i / (n - 1)
            pts = rounded_section(3.1, 3.0, .4, .2, .95, 16)
            secs.append(((0, cy + y, 0), pts))
    body = B.loft("TrainBody", secs, color="#35664e", material=green, smooth=True)
    add(body)
    # yellow waist stripe both sides
    for sx in (-1.56, 1.56):
        add(B.box("Stripe", (.05, length - 1.2, .16), (sx, cy, 1.45), color="#d6b24a", material=yellow))
    # windows
    n_win = 8 if not is_loco else 3
    for side in (-1, 1):
        for i in range(n_win):
            yy = cy - length / 2 + 3.0 + i * (length - 6.0) / max(1, n_win - 1)
            zz = 2.65
            ww = 1.45
            mat = warm if (i + side) % 3 else cool
            x = side * 1.565
            add(B.quad("TrainWindow", [(x, yy - ww/2, zz), (x, yy + ww/2, zz),
                                       (x, yy + ww/2, zz + 1.05), (x, yy - ww/2, zz + 1.05)], "#ffd9a0", mat))
            # frame
            add(B.box("WinFrame", (.06, ww + .12, .08), (side * 1.59, yy, zz + 1.1), color="#213c31", material=green2))
            add(B.box("WinFrame", (.06, ww + .12, .08), (side * 1.59, yy, zz - .05), color="#213c31", material=green2))
    # doors at both ends (except loco front)
    for dy in (-length / 2 + 1.8, length / 2 - 1.8):
        if is_loco and dy > 0:
            continue
        add(B.box("TrainDoor", (.08, 1.6, 2.45), (1.57, cy + dy, 2.2), color="#2a5744", material=green2, bevel=.02))
        add(B.box("DoorGlass", (.05, 1.1, .8), (1.625, cy + dy, 2.65), color="#ffd9a0", material=warm))
        add(B.box("DoorStep", (1.1, .35, .16), (1.05, cy + dy, .55), color="#3b3b35", material=metal))
    # roof ribs / AC
    for i in range(5):
        add(B.box("RoofRib", (2.4, .10, .06), (0, cy - length / 2 + 2 + i * (length - 4) / 4, 3.95),
                  color="#4b4d49", material=roof))
    add(B.box("RoofAC", (1.8, 2.8, .35), (0, cy - 2, 4.02), color="#5b5e58", material=roof, bevel=.05))
    add(B.box("RoofVent", (.9, 1.2, .22), (0, cy + 4, 4.0), color="#4a4d48", material=metal))
    # underframe / bogies
    add(B.box("Underframe", (2.4, length - 1.4, .35), (0, cy, .75), color="#262724", material=under))
    for by in (-length / 2 + 4.0, length / 2 - 4.0):
        add(B.box("Bogie", (2.2, 3.2, .55), (0, cy + by, .48), color="#292a27", material=under, bevel=.04))
        for wy in (-1.0, 1.0):
            for wx in (-.78, .78):
                add(B.cylinder("Wheel", .44, .26, (wx, cy + by + wy, .44), rot=(0, math.pi / 2, 0),
                               segments=14, color="#141513", material=metal))
            add(B.cylinder("Axle", .11, 2.3, (0, cy + by + wy, .44), rot=(0, math.pi / 2, 0),
                           segments=8, color="#3a3a35", material=metal))
        for yy in (-1.2, 1.2):
            add(B.box("Spring", (.32, .35, .45), (-1.1, cy + by + yy, .78), color="#4a4a42", material=metal))
    # couplers / buffers
    for dy in (-length / 2, length / 2):
        add(B.cylinder("Coupler", .12, 1.1, (0, cy + dy + (0.5 if dy > 0 else -0.5), .58),
                       rot=(math.pi / 2, 0, 0), segments=8, color="#3a3a35", material=metal))
        for sx in (-.75, .75):
            add(B.cylinder("Buffer", .13, .22, (sx, cy + dy, .72), rot=(math.pi / 2, 0, 0),
                           segments=8, color="#4a4a42", material=metal))
    return body


def locomotive(cy, length=20.0):
    # cab + long hood, green with yellow front stripe
    add(B.box("LocoFrame", (2.7, length, .45), (0, cy, .75), color="#262724", material=under))
    # main hood
    add(B.box("Hood", (2.5, length * .62, 2.35), (0, cy - 1.5, 2.1), color="#35664e", material=green, bevel=.12))
    add(B.box("HoodTop", (2.42, length * .62 - .4, .28), (0, cy - 1.5, 3.35), color="#2d5642", material=green2))
    # cab at front
    add(B.box("Cab", (2.85, 4.4, 2.65), (0, cy + 6.8, 2.25), color="#35664e", material=green, bevel=.12))
    add(B.box("CabRoof", (3.0, 4.8, .22), (0, cy + 6.8, 3.62), color="#2d5642", material=green2))
    # front face / windshield
    add(B.quad("Windshield", [(-1.05, cy + 9.02, 2.15), (1.05, cy + 9.02, 2.15),
                              (1.05, cy + 9.02, 3.25), (-1.05, cy + 9.02, 3.25)], "#13232a", glass))
    add(B.box("WindFrame", (2.3, .1, .12), (0, cy + 9.05, 3.3), color="#203b30", material=green2))
    # front yellow warning band
    add(B.box("FrontStripe", (2.6, .08, .28), (0, cy + 9.04, 1.35), color="#d6b24a", material=yellow))
    for sx in (-.88, .88):
        add(B.cylinder("Headlight", .17, .14, (sx, cy + 9.12, 1.6), rot=(math.pi / 2, 0, 0),
                       segments=10, color="#fff2c8", material=head))
    # side cab windows
    for sx in (-1.44, 1.44):
        add(B.quad("CabWindow", [(sx, cy + 5.6, 2.35), (sx, cy + 8.2, 2.35),
                                 (sx, cy + 8.2, 3.2), (sx, cy + 5.6, 3.2)], "#ffd9a0", warm))
    # hood grilles
    for i in range(6):
        add(B.box("Grille", (2.54, .16, .75), (0, cy - 7.8 + i * 1.7, 2.5), color="#284a3a", material=green2))
    # side stripe
    for sx in (-1.46, 1.46):
        add(B.box("LocoStripe", (.05, length - 4, .18), (sx, cy - 1.3, 1.45), color="#d6b24a", material=yellow))
    # roof exhaust, horn, antenna
    add(B.box("Exhaust", (.7, 1.1, .35), (0, cy - 5, 3.55), color="#3c3e39", material=metal))
    add(B.cylinder("Horn", .18, .5, (0, cy + 7.5, 3.8), rot=(0, math.pi/2, 0), segments=8, color="#8a8a7d", material=metal))
    add(B.box("RoofFan", (1.6, 1.4, .16), (0, cy + 2.0, 3.52), color="#4a4d48", material=metal))
    # handrails
    for sx in (-1.5, 1.5):
        add(B.tube("Handrail", [(sx, cy + 9.0, 1.2), (sx, cy + 9.0, 3.3)], .025, "#c8c0a8", metal, segments=4))
    # bogies
    for by in (-length/2 + 3.5, length/2 - 3.5):
        add(B.box("Bogie", (2.2, 3.3, .55), (0, cy + by, .48), color="#292a27", material=under, bevel=.04))
        for wy in (-1.0, 1.0):
            for wx in (-.78, .78):
                add(B.cylinder("Wheel", .46, .26, (wx, cy + by + wy, .46), rot=(0, math.pi/2, 0),
                               segments=14, color="#141513", material=metal))
    # cab steps
    for sx in (-1.2, 1.2):
        add(B.box("CabStep", (1.0, .4, .1), (sx, cy + 8.8, .55), color="#3b3b35", material=metal))
    # tail lights at the rear
    for sx in (-.8, .8):
        add(B.cylinder("Tail", .1, .1, (sx, cy - 9.0, 1.5), rot=(math.pi/2, 0, 0), segments=8,
                       color="#ff3a2c", material=tail))


def main():
    # four carriages + loco at the front, line centred at origin
    # loco from y=38..58, carriages behind
    locomotive(42.5)
    for i in range(4):
        carriage(20 - i * 25.0)
    # a pantograph on carriage 2
    cy = 20 - 25.0
    for sx in (-.8, .8):
        add(B.cylinder("Insulator", .12, .28, (sx, cy + 2, 4.1), segments=8, color="#8c7a5a", material=metal))
    add(B.tube("PantoArm", [(-.65, cy + 2, 4.2), (0, cy + 1.2, 5.3), (.65, cy + 2, 4.2)],
               .035, "#3a3a35", metal, segments=4))
    add(B.tube("PantoBar", [(-.9, cy + 1.4, 5.3), (.9, cy + 1.4, 5.3)], .035, "#3a3a35", metal, segments=4))
    add(B.box("Drawbar",(.34,.92,.22),(0,32.42,.82),color="#474842",material=metal))
    joined = B.join_materials("GreenTrain", ALL, skip_prefixes=())
    from era_fixtures import install
    joined.extend(install("green_train"))
    root = B.empty("GreenTrainRoot", (0, 0, 0))
    for ob in joined:
        ob.parent = root
        ob.matrix_parent_inverse = root.matrix_world.inverted()
    B.save_blend(os.path.join(B.ROOT, "assets", "vehicles", "green_train.blend"))
    B.export_glb(os.path.join(B.ROOT, "assets", "vehicles", "green_train.glb"))
    print("GREEN TRAIN EXPORTED", os.path.getsize(os.path.join(B.ROOT, "assets", "vehicles", "green_train.glb")))


if __name__ == "__main__":
    main()
