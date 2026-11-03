"""Pipeline validation asset: vertex colors, sign texture, emissive, empties."""
import os
import sys
import math

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
import blib as B  # noqa: E402

B.reset(7)
matte = B.vmat("Matte", 0.86)
metal = B.vmat("Metal", 0.4, 0.55)
glass = B.mat("Glass", "#3f5a68", rough=0.18, metal=0.15)
glow = B.mat("GlowWarm", "#ffb15a", rough=0.5, emission="#ffb15a", emis_strength=2.2)
signs = B.mat("Signs", texture=os.path.join(B.ASSETS, "signs_atlas.png"), rough=0.72)
neon = B.mat("SignsNeon", texture=os.path.join(B.ASSETS, "signs_atlas.png"), rough=0.5,
             emission="#ffffff", emis_strength=2.0)

B.ground_slab("Base", 80, 80, 7)
terrain = B.terrain("Terrain", 80, 80, 24, 24,
                    lambda x, y: 0.35 * math.sin(x * 0.11) * math.cos(y * 0.1) +
                    0.15 * math.sin((x + y) * 0.25),
                    lambda x, y, z: "#7b8a58" if (x + y) % 9 > 3 else "#8a9362",
                    matte)
road_pts = [(0, -34), (0.5, -22), (2, -10), (1.5, 2), (-1.5, 14), (-1, 26), (0, 34)]
road = B.road_ribbon("Road", road_pts, 4.2, "#6a6153", matte)
line = B.road_line("RoadLine", road_pts, 0.12, "#d8cba9", matte, z=0.09, dash=2.0)
for o in line:
    if o:
        pass

# House 1: white wall, tiled roof, lattice, couplets
B.box("HouseWall", (8, 6, 3.4), (0, 6, 1.7), color="#e6dfcf", material=matte, bevel=0.06)
B.box("HousePlinth", (8.5, 6.5, 0.5), (0, 6, 0.25), color="#8d8068", material=matte, bevel=0.04)
roof = B.tile_roof("HouseRoof", 0, 6, 3.4, 10.2, 7.6, 2.3, 0.18, "#4a4843", matte)
for o in roof:
    pass
B.box("Door", (1.5, 0.12, 2.25), (0, 2.94, 1.25), color="#4b3325", material=matte, bevel=0.03)
B.sign_quad("Fu", "fu", (0, 2.86, 2.2), 0, 0.72, 0.72, signs)
B.sign_quad("LianA", "chunlian_a", (-1.25, 2.9, 1.6), 0, 0.34, 1.5, signs)
B.sign_quad("LianB", "chunlian_b", (1.25, 2.9, 1.6), 0, 0.34, 1.5, signs)
B.window_lattice("Win1", -2.7, 2.94, 2.1, 1.5, 1.1, "y", -1, "#4c3928", matte, 4,
                  "#d9b877", glow)
B.window_lattice("Win2", 2.7, 2.94, 2.1, 1.5, 1.1, "y", -1, "#4c3928", matte, 4,
                  "#d9b877", glow)
B.box("Chimney", (0.6, 0.6, 1.6), (2.6, 8.4, 4.2), color="#b8b1a2", material=matte, bevel=0.03)

# Shop building
B.box("Shop", (10, 8, 7), (-12, 9, 3.5), color="#cbbfa9", material=matte, bevel=0.08)
B.box("ShopBase", (10.4, 8.3, 1.2), (-12, 9, 0.6), color="#7b6d5d", material=matte, bevel=0.03)
B.sign_quad("Baihuo", "baihuo", (-12, 4.9, 4.1), 0, 6.2, 1.6, signs)
# shopfront openings
for i in range(3):
    B.box("ShopGlass", (2.1, 0.1, 2.0), (-15 + i * 3, 4.94, 1.8), color="#2c3b40", material=glass, bevel=0.02)
B.box("Awning", (9.6, 2.0, 0.12), (-12, 5.0, 3.35), rot=(0.18, 0, 0), color="#8a3b31", material=matte, bevel=0.02)
for i in range(4):
    B.box("Balcony", (10.2, 0.8, 0.18), (-12, 5.1, 4.7 + i * 0.02), color="#b7aa95", material=matte, bevel=0.02)
    for j in range(9):
        B.box("Rail", (0.05, 0.05, 0.55), (-16.6 + j * 1.15, 5.1, 5.0), color="#5c574e", material=matte)

# Emissive windows on shop
for i in range(4):
    for j in range(2):
        B.box("WinGlow", (1.2, 0.08, 0.9), (-15.4 + j * 4.4, 4.94, 5.9 + i * 0.0),
              color="#ffb15a", material=glow)

# Tree + grass
B.tree("Tree", (-5.4, 0.5, 0.25), 5.2, 2.4, "#4d6a43", "#5b4935", matte, matte)
for i in range(20):
    B.grass_tuft(f"Grass{i}", -6 + (i * 2.7) % 14, -3 + (i * 3.3) % 10, 0.28, 0.4, "#5f7a48", matte)

# utility pole + wire
B.cylinder("Pole", 0.09, 7.5, (4.0, -4, 3.75), segments=8, color="#5b554b", material=matte)
B.tube("Wire", [(4.0, -4, 7.4), (4.0, 4, 7.1), (4.0, 14, 7.3)], 0.022, "#2e2b27", matte)
B.box("SignPost", (0.3, 0.05, 0.5), (4, -4, 7.0), color="#8a3b31", material=matte)

# emissive shop sign test
B.sign_quad("NeonTest", "neon_ye", (-12, 4.9, 2.0), 0, 2.0, 2.0, neon)

B.empty("FX_Hotspot", (0, 2.9, 1.2))
B.empty("FX_Smoke", (2.6, 8.4, 5.2))

B.save_blend(os.path.join(B.ROOT, "assets", "test_zone.blend"))
B.export_glb(os.path.join(B.ROOT, "assets", "test_zone.glb"))
print("TEST ASSET EXPORTED", os.path.getsize(os.path.join(B.ROOT, "assets", "test_zone.glb")))
