"""1990s boxy sedan, original procedural model. Forward +Y, origin on the ground."""
from __future__ import annotations
import math, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
import blib as B  # noqa: E402

B.reset(1994)
rng = random.Random(1994)
ALL = []
paint = B.vmat("CarPaint", .38, .18)
chrome = B.vmat("CarChrome", .16, .95)
rubber = B.vmat("CarRubber", .9)
glass = B.mat("CarGlass", "#16262c", rough=.12, metal=.3)
red = B.mat("CarRed", "#b22a22", rough=.5, emission="#b22a22", emis_strength=.5)
head = B.mat("CarHead", "#fff2c8", rough=.3, emission="#fff0c0", emis_strength=3)
tail = B.mat("CarTail", "#e03024", rough=.4, emission="#ff3020", emis_strength=2.2)
plate = B.mat("CarPlate", "#d8d4c4", rough=.6)
interior = B.vmat("CarInterior", .9)


def add(o):
    if isinstance(o, (list, tuple)):
        for x in o: add(x)
    else: ALL.append(o)


def main():
    # main body
    add(B.box("Body", (1.74, 4.35, .52), (0, 0, .66), color="#8e2c2a", material=paint, bevel=.14))
    # hood and trunk shoulders
    add(B.box("Hood", (1.66, 1.25, .16), (0, 1.47, .98), color="#8e2c2a", material=paint, bevel=.06))
    add(B.box("Trunk", (1.66, 1.0, .16), (0, -1.62, .98), color="#8e2c2a", material=paint, bevel=.06))
    # glass greenhouse with painted pillars
    add(B.box("Greenhouse", (1.50, 1.92, .44), (0, -.02, 1.30), color="#16262c", material=glass, bevel=.05))
    add(B.box("Belt", (1.58, 1.98, .17), (0, -.02, 1.06), color="#7f2625", material=paint, bevel=.04))
    add(B.box("Roof", (1.46, 1.74, .07), (0, -.02, 1.54), color="#7f2625", material=paint, bevel=.03))
    for sx in (-.755, .755):
        for yy in (-.94, -.02, .92):
            add(B.box("Pillar", (.06, .07, .46), (sx, yy, 1.30), color="#7f2625", material=paint))
        add(B.box("WinTrim", (.025, 1.92, .035), (sx, -.02, 1.505), color="#3a2a24", material=chrome))
        add(B.box("WinTrim", (.025, 1.92, .035), (sx, -.02, 1.095), color="#3a2a24", material=chrome))
        add(B.box("ChromeBelt", (.018, 2.1, .03), (sx * 1.055, 0, 1.06), color="#c9c6b8", material=chrome))
    # windshield and rear window are the greenhouse end faces
    add(B.quad("Windshield", [(-.70, .965, 1.10), (.70, .965, 1.10), (.70, .965, 1.50), (-.70, .965, 1.50)], "#16262c", glass))
    add(B.quad("RearGlass", [(-.70, -1.005, 1.10), (.70, -1.005, 1.10), (.70, -1.005, 1.50), (-.70, -1.005, 1.50)], "#16262c", glass))
    # door seams / handles
    for sx in (-.878, .878):
        for yy in (-.42, .7):
            add(B.box("DoorSeam", (.012, .025, .48), (sx, yy, .83), color="#4b1b1a", material=rubber))
        add(B.box("Handle", (.045, .22, .045), (sx, .05, 1.04), color="#c9c6b8", material=chrome))
        add(B.box("Mirror", (.16, .07, .15), (sx * 1.00, .62, 1.18), color="#7f2625", material=paint))
        add(B.box("MirrorGlass", (.12, .03, .1), (sx * 1.06, .62, 1.18), color="#182a30", material=glass))
    # chrome bumpers
    for yy in (2.18, -2.18):
        add(B.box("Bumper", (1.84, .12, .18), (0, yy, .58), color="#c9c6b8", material=chrome, bevel=.03))
    # grille
    add(B.box("Grille", (.92, .06, .24), (0, 2.20, .78), color="#24242a", material=rubber))
    for i in range(5):
        add(B.box("GrilleBar", (.82, .02, .025), (0, 2.235, .70 + i * .045), color="#b8b4a8", material=chrome))
    # square headlights / indicators / tail lights
    for sx in (-.62, .62):
        add(B.box("Headlight", (.30, .04, .17), (sx, 2.225, .82), color="#fff0c0", material=head))
        add(B.box("Indicator", (.12, .04, .08), (sx * .62, 2.225, .68), color="#ff9c3a", material=tail))
        add(B.box("Taillight", (.26, .04, .14), (sx, -2.225, .84), color="#ff3020", material=tail))
    add(B.box("PlateFront", (.46, .025, .14), (0, 2.24, .55), color="#d8d4c4", material=plate))
    add(B.box("PlateRear", (.46, .025, .14), (0, -2.24, .55), color="#d8d4c4", material=plate))
    # wipers / antenna / exhaust
    for sx in (-.38, .16):
        add(B.beam("Wiper", (sx, .92, 1.06), (sx + .3, .72, 1.20), .012, .012, "#1c1c1c", rubber))
    add(B.cylinder("Antenna", .004, .7, (-.7, -1.0, 1.7), segments=4, color="#1c1c1c", material=chrome))
    add(B.cylinder("Exhaust", .03, .3, (.5, -2.24, .35), rot=(math.pi/2, 0, 0), segments=8, color="#3a3a35", material=chrome))
    # wheels + hubs + arches
    for sx in (-.82, .82):
        for yy in (-1.38, 1.38):
            add(B.cylinder("Tyre", .32, .21, (sx, yy, .34), rot=(0, math.pi/2, 0), segments=18, color="#141414", material=rubber))
            add(B.cylinder("Hub", .19, .22, (sx * 1.02, yy, .34), rot=(0, math.pi/2, 0), segments=12, color="#b9b6aa", material=chrome))
            add(B.cylinder("HubCap", .06, .24, (sx * 1.03, yy, .34), rot=(0, math.pi/2, 0), segments=8, color="#7a776c", material=chrome))
            add(B.box("Arch", (.05, .74, .08), (sx * 1.02, yy, .65), color="#5b1c1b", material=paint))
    # interior hints through glass
    add(B.box("Seat", (.72, .5, .25), (-.35, -.05, 1.08), color="#3a2c26", material=interior))
    add(B.box("Seat", (.72, .5, .25), (.35, -.05, 1.08), color="#3a2c26", material=interior))
    add(B.box("Dash", (1.3, .25, .1), (0, .78, 1.08), color="#2c2420", material=interior))
    add(B.tube("Steer", [(.35, .62, 1.1), (.35, .48, 1.22)], .03, "#1c1c1c", interior, segments=5))
    # join
    joined = B.join_materials("Car", ALL)
    root = B.empty("CarRoot", (0, 0, 0))
    for ob in joined:
        ob.parent = root
        ob.matrix_parent_inverse = root.matrix_world.inverted()
    B.save_blend(os.path.join(B.ROOT, "assets", "vehicles", "car.blend"))
    B.export_glb(os.path.join(B.ROOT, "assets", "vehicles", "car.glb"))
    print("CAR EXPORTED", os.path.getsize(os.path.join(B.ROOT, "assets", "vehicles", "car.glb")))


if __name__ == "__main__":
    main()
