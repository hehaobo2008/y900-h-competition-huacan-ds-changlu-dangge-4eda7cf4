"""Fourth act · 山河速 / 2020s high-speed rail valley at dawn.
Original procedural bridge, valley, and 6-car EMU. Forward +Y for the train."""
from __future__ import annotations
import math, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
import blib as B  # noqa: E402

ROOT = B.ROOT

# ---------------------------------------------------------------- train
def build_train():
    B.reset(2021)
    rng = random.Random(2021)
    ALL = []
    white = B.vmat("HSRWhite", .38, .12)
    white2 = B.vmat("HSRWhite2", .5, .08)
    blue = B.vmat("HSRBlue", .45, .1)
    glass = B.mat("HSRGlass", "#0e1c24", rough=.1, metal=.35)
    warm = B.mat("HSRWarm", "#ffe0ad", rough=.4, emission="#ffd9a0", emis_strength=1.4)
    cool = B.mat("HSRCool", "#e6f2ff", rough=.4, emission="#dceeff", emis_strength=1.0)
    metal = B.vmat("HSRMetal", .35, .7)
    rubber = B.vmat("HSRRubber", .9)
    head = B.mat("HSRHead", "#fff8e0", emission="#fff0c0", emis_strength=4)
    tail = B.mat("HSRTail", "#ff3a2c", emission="#ff3020", emis_strength=2.2)

    def add(o):
        if isinstance(o, (list, tuple)):
            for x in o: add(x)
        else: ALL.append(o)

    def section(w, h, z0):
        pts = []
        # bottom
        for i in range(4):
            pts.append((-w/2 + w*i/3, z0))
        # right side
        pts.append((w/2, z0 + h*.35))
        # roof arc
        for i in range(7):
            a = math.pi * i / 6
            pts.append((w/2*.98*math.cos(a), z0 + h - h*.18 + h*.18*math.sin(a)))
        # left side
        pts.append((-w/2, z0 + h*.35))
        return pts

    def car(cy, length=25.0, nose=False):
        # loft
        n = 8
        secs = []
        for i in range(n):
            u = i / (n - 1)
            y = cy - length/2 + length*u
            sx, sz, zoff = 1.0, 1.0, 0.9
            if nose:
                # front car: taper at the +Y end
                v = (y - (cy + length/2 - 3.0)) / 6.0
                if v > 0:
                    t = min(1.0, v)
                    sx = 1.0 - .62 * (t ** 1.4)
                    sz = 1.0 - .5 * (t ** 1.8)
                    zoff = .9 - .16 * t
            pts = section(3.3 * sx, 3.1 * sz, zoff)
            secs.append(((0, y, 0), pts))
        add(B.loft("HSRBody", secs, color="#e9e7df", material=white, smooth=True))
        # window band and lit windows
        for sx in (-1.655, 1.655):
            add(B.box("HSRBand", (.035, length - 2.4, .72), (sx, cy, 2.55), color="#16262e", material=glass))
            nwin = 8 if not nose else 5
            for k in range(nwin):
                yy = cy - length/2 + 3.0 + k * (length - 6.0) / max(1, nwin - 1)
                add(B.box("HSRWin", (.045, 1.35, .55), (sx * 1.005, yy, 2.55),
                          color="#fff0c0" if (k + (1 if sx > 0 else 0)) % 3 else "#dceeff",
                          material=warm if (k + (1 if sx > 0 else 0)) % 3 else cool))
        # blue waist stripe and lower skirt
        for sx in (-1.67, 1.67):
            add(B.box("HSRStripe", (.04, length - 1.2, .16), (sx, cy, 1.55), color="#2b5d8e", material=blue))
            add(B.box("HSRSkirt", (.03, length - 1.2, .38), (sx, cy, .95), color="#c9c8c1", material=white2))
        # doors
        for dy in (-length/2 + 2.2, length/2 - 2.2):
            for sx in (-1.66, 1.66):
                add(B.box("HSRDoor", (.06, 1.15, 2.15), (sx, cy + dy, 1.85), color="#d8d6cd", material=white2))
                add(B.box("HSRDoorGlass", (.04, .8, .55), (sx * 1.02, cy + dy, 2.35), color="#1d3038", material=glass))
        # roof
        add(B.box("HSRRoof", (2.2, length - 2, .18), (0, cy, 4.02), color="#d9d7cd", material=white2))
        add(B.box("HSRAC", (1.5, 2.6, .35), (0, cy - 2, 4.15), color="#c7c5bc", material=metal))
        # bogies
        for by in (-length/2 + 3.6, length/2 - 3.6):
            add(B.box("HSRBogie", (2.3, 3.1, .5), (0, cy + by, .55), color="#2b2c2a", material=metal))
            for wy in (-1.0, 1.0):
                for wx in (-1.02, 1.02):
                    add(B.cylinder("HSRWheel", .43, .24, (wx, cy + by + wy, .43),
                                   rot=(0, math.pi/2, 0), segments=14, color="#151615", material=rubber))
        # nose / front
        if nose:
            fy = cy + length/2
            add(B.box("NoseTip", (2.05, 3.2, .8), (0, fy - .2, 1.35), color="#e9e7df", material=white, bevel=.35))
            add(B.quad("NoseGlass", [(-.78, fy + 1.25, 2.25), (.78, fy + 1.25, 2.25),
                                     (.66, fy + 1.7, 2.95), (-.66, fy + 1.7, 2.95)], "#14242c", glass))
            for sx in (-.62, .62):
                add(B.box("NoseLight", (.28, .07, .12), (sx, fy + 1.65, 1.55), color="#fff0c0", material=head))
            add(B.box("NoseStripe", (1.4, .06, .10), (0, fy + 1.69, 1.15), color="#2b5d8e", material=blue))
            add(B.box("FrontSkirt", (2.0, .6, .32), (0, fy + .4, .72), color="#bfbdb5", material=white2))
        else:
            add(B.cylinder("RearLight", .10, .1, (1.1, cy + length/2 + .01, 1.7), rot=(math.pi/2, 0, 0),
                           segments=8, color="#ff3a2c", material=tail))
            add(B.cylinder("RearLight", .10, .1, (-1.1, cy + length/2 + .01, 1.7), rot=(math.pi/2, 0, 0),
                           segments=8, color="#ff3a2c", material=tail))

    centers = [-62.5, -37.5, -12.5, 12.5, 37.5, 62.5]
    for i, cy in enumerate(centers):
        car(cy, 25.0, nose=(i == len(centers)-1))
    # pantograph on car 2
    cy = centers[1]
    for sx in (-.8, .8):
        add(B.cylinder("Insulator", .10, .24, (sx, cy + 2, 4.2), segments=8, color="#7e7561", material=metal))
    add(B.tube("PantoArm", [(-.7, cy + 2, 4.3), (0, cy + 1.0, 5.4), (.7, cy + 2, 4.3)],
               .03, "#2f2f2c", metal, segments=5))
    add(B.tube("PantoBar", [(-.9, cy + 1.3, 5.4), (.9, cy + 1.3, 5.4)], .03, "#2f2f2c", metal, segments=5))
    joined = B.join_materials("HSR", ALL)
    root = B.empty("HSRRoot", (0, 0, 0))
    for ob in joined:
        ob.parent = root
        ob.matrix_parent_inverse = root.matrix_world.inverted()
    B.save_blend(os.path.join(ROOT, "assets", "vehicles", "hsr.blend"))
    B.export_glb(os.path.join(ROOT, "assets", "vehicles", "hsr.glb"))
    print("HSR EXPORTED", os.path.getsize(os.path.join(ROOT, "assets", "vehicles", "hsr.glb")))


# ---------------------------------------------------------------- rail scene
def build_rail():
    B.reset(2021)
    rng = random.Random(2021)
    ALL = []
    matte = B.vmat("RailMatte", .9)
    rock = B.vmat("RailRock", .95)
    steel = B.vmat("RailSteel", .35, .7)
    concrete = B.vmat("RailConcrete", .92)
    snow = B.vmat("RailSnow", .8)
    water = B.mat("Water", "#2f5a60", rough=.1, metal=.2)
    signs = B.mat("RailSigns", texture=os.path.join(B.ASSETS, "signs_atlas.png"), rough=.5)
    lamp = B.mat("RailLamp", "#ffd9a0", emission="#ffd9a0", emis_strength=3)
    red = B.mat("RailRed", "#ff3a2c", emission="#ff3020", emis_strength=4)
    tree_m = B.vmat("RailTree", .95)

    def add(o):
        if isinstance(o, (list, tuple)):
            for x in o: add(x)
        else: ALL.append(o)

    def ground_h(x, y):
        ay = abs(y)
        if ay < 32:
            return 0.0
        bank = smoothstep(32, 64, ay) * 13
        ridge = (ridged(x, y) ** 1.25) * 56
        ridge *= smoothstep(55, 145, ay)
        side = smoothstep(92, 160, abs(x)) * 20
        return bank + ridge + side

    def ridged(x, y):
        v, amp, fx, fy = 0.0, 1.0, .017, .014
        for k in range(4):
            s = math.sin(x * fx + math.sin(y * fy * 1.7 + k * .9) * 1.35 + k * 2.3)
            t = math.sin(y * fy + math.sin(x * fx * 1.3 + k * .7) * 1.15 + k * 1.6)
            v += amp * (.5 + .5 * s * t)
            amp *= .55; fx *= 2.05; fy *= 2.05
        return v / 1.95

    def smoothstep(a, b, x):
        t = max(0.0, min(1.0, (x-a)/(b-a)))
        return t*t*(3-2*t)

    def fbm2(x, y):
        v = 0.0
        for k in range(4):
            xx, yy = x*(2**k), y*(2**k)
            v += (math.sin(xx*12.9898 + yy*78.233 + k*3.1) * 43758.5453 % 1.0) / (2**k)
        return max(0.0, min(1.0, v))

    add(B.ground_slab("RailBase", 320, 300, 9, colors=("#4a4032", "#5b4c3a", "#6b5a45", "#3d342a")))
    add(B.terrain("RailTerrain", 320, 300, 168, 156, ground_h,
                  lambda x, y, z: B.mix(B.srgb("#5a6642"), B.srgb("#7c7d60"), min(1, z/58)) if z > 1 else B.srgb("#4d5938"),
                  matte))
    # river
    add(B.quad("Water_River", [(-160, -32, .25), (160, -32, .25), (160, 32, .25), (-160, 32, .25)],
               "#2f5a60", water))
    for yy in (-32, 32):
        for x0 in range(-160, 160, 20):
            add(B.box("RiverBank", (20, 1.4, .6), (x0 + 10, yy, .3), color="#7e7562", material=rock, bevel=.04))
    # bridge
    Z = 32.0
    add(B.box("BridgeDeck", (13, 300, 1.3), (0, 0, Z), color="#7b7970", material=concrete, bevel=.05))
    add(B.box("BridgeBed", (9.5, 300, .18), (0, 0, Z + .72), color="#4a4a46", material=matte))
    for sx in (-6.2, 6.2):
        add(B.box("BridgeParapet", (.4, 300, 1.05), (sx, 0, Z + 1.0), color="#9a978c", material=concrete, bevel=.03))
        for yy in range(-150, 151, 6):
            add(B.box("BridgePost", (.5, .3, .9), (sx, yy, Z + 1.0), color="#a9a596", material=concrete))
    # rails, sleepers
    for sx in (-2.4, 2.4):
        for k in range(2):
            add(B.box("Track", (2.4, 290, .10), (sx, 0, Z + .88), color="#8b8a82", material=steel))
        for yy in range(-150, 151, 8):
            add(B.box("Sleeper", (3.2, .4, .1), (sx, yy, Z + .82), color="#5d5b53", material=concrete))
    # piers
    for yy in (0, -90, 90):
        add(B.box("BridgePier", (7, 3.2, Z - .5), (0, yy, (Z - .5)/2), color="#8d897b", material=concrete, bevel=.05))
    for yy in (-10, 10):
        add(B.cylinder("RiverPier", 2.2, Z, (0, yy, Z/2), segments=12, color="#7f7b6f", material=concrete))
    # A pylons
    for py in (-46, 46):
        base_z = ground_h(0, py)
        for sx in (-1, 1):
            add(B.beam("PylonLeg", (sx * 10, py, base_z), (sx * 2.2, py, 86), .85, 1.1, "#a19d90", concrete))
        add(B.box("PylonBeam", (22, 2.2, 1.2), (0, py, 52), color="#a19d90", material=concrete, bevel=.05))
        add(B.box("PylonBeam", (14, 1.8, 1.0), (0, py, 76), color="#aaa698", material=concrete, bevel=.05))
        add(B.box("PylonTop", (4.2, 4.2, 3.2), (0, py, 86), color="#b0ac9e", material=concrete, bevel=.05))
        for k in range(1, 8):
            ty = py + (k * 12 if py > 0 else -k * 12)
            for sx in (-1, 1):
                add(B.tube("Cable", [(sx * 3, py, 87), (sx * 6.0, ty, Z + 1.1)], .07, "#d3cfc1", steel, segments=4))
    # catenary
    for yy in range(-140, 141, 24):
        add(B.cylinder("CatPole", .12, 8, (5.8, yy, Z + 4), segments=6, color="#5b5b55", material=steel))
        add(B.box("CatArm", (5.4, .08, .08), (3.2, yy, Z + 7.8), color="#5b5b55", material=steel))
    for sx in (-2.4, 2.4):
        add(B.tube("CatWire", [(-2.4, -150, Z + 7.7), (-2.4, 150, Z + 7.7)], .018, "#4a4a45", steel, segments=4))
    # bridge name gantry
    for sx in (-8, 8):
        add(B.cylinder("GantryPole", .12, 5, (sx, 58, Z + 2.5), segments=6, color="#6f6c61", material=steel))
    add(B.box("GantryBeam", (17, .4, .4), (0, 58, Z + 5), color="#6f6c61", material=steel))
    add(B.sign_quad("BridgeName", "qiaoming", (0, 58.3, Z + 3.6), 0, 8, 2.0, signs))
    # village on the north bank
    for i, (vx, vy) in enumerate([(-52, -72), (-38, -80), (-66, -84), (54, -76)]):
        z = ground_h(vx, vy)
        add(B.box("VillageHouse", (6, 5, 3), (vx, vy, z + 1.5), color="#d8cbb0", material=matte, bevel=.05))
        add(B.tile_roof("VillageRoof", vx, vy, z + 3, 7.2, 6.0, 1.2, .12, "#5f5b52", matte, curl=.4))
    add(B.sign_quad("StationSign", "yunling", (-45, -68, ground_h(-45, -68) + 3.2), 0, 6, 1.5, signs))
    # trees on slopes
    for i in range(70):
        tx = rng.uniform(-150, 150)
        ty = rng.choice([-1, 1]) * rng.uniform(55, 135)
        z = ground_h(tx, ty)
        add(B.tree("RailTree", (tx, ty, z), rng.uniform(3.5, 7.5), rng.uniform(1.8, 3.2),
                   "#3d5b3f" if i % 3 else "#4a6a45", "#5b4935", tree_m, matte, rng))
    # wind turbines
    for (tx, ty) in [(-116, -118), (112, -110), (104, 112)]:
        z = ground_h(tx, ty)
        add(B.cylinder("TurbineTower", 1.0, 30, (tx, ty, z + 15), segments=10, color="#d6d6cc", material=concrete))
        add(B.sphere("TurbineNacelle", 1.2, (tx, ty, z + 30), scale=(2.2, 1, 1.1), color="#e4e3da", material=concrete,
                     segments=8, rings=5))
        for k in range(3):
            a = k * math.tau / 3
            add(B.beam("Blade", (tx, ty, z + 30), (tx + math.cos(a) * 13, ty, z + 30 + math.sin(a) * 13),
                       .45, .16, "#e8e6dc", concrete))
    # small boat
    add(B.lathe("Boat", [(.1, 0), (1.1, .25), (1.5, .7), (1.2, .9)], loc=(-36, 5, .35), segments=12,
                color="#5c4934", material=matte))
    add(B.box("BoatLight", (.2, .2, .2), (-35, 5, 1.4), color="#ffd9a0", material=lamp))
    # birds
    for i in range(12):
        bx, by = rng.uniform(-80, 80), rng.uniform(-100, 80)
        bz = rng.uniform(25, 55)
        add(B.box("Bird", (1.2, .06, .06), (bx, by, bz), rot=(0, 0, 0), color="#4b4a43", material=matte))
        add(B.box("Bird", (.7, .05, .05), (bx + .6, by, bz + .25), rot=(0, .4, 0), color="#4b4a43", material=matte))
    B.empty("FX_Hotspot", (0, 0, Z + 3))
    B.empty("FX_Smoke_1", (-45, -68, ground_h(-45, -68) + 4))
    B.join_materials("RailScene", ALL)
    B.save_blend(os.path.join(ROOT, "assets", "zones", "rail.blend"))
    B.export_glb(os.path.join(ROOT, "assets", "zones", "rail.glb"))
    print("RAIL EXPORTED", os.path.getsize(os.path.join(ROOT, "assets", "zones", "rail.glb")))


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if not args or "train" in args:
        build_train()
    if not args or "rail" in args:
        build_rail()
