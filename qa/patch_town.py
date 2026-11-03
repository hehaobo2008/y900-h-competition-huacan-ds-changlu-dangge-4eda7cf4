import re
p = 'tools/build_town.py'
s = open(p, encoding='utf-8').read()

old = '''def canal_water(P):
    pts = [(x, canal_cy(x)) for x in range(-138, 143, 2)]
    P.append(B.road_ribbon("Water_Canal", pts, 14.6, "#3a625a", water, z=-2.15,
                           crown=0.0, segments_width=6))
'''
new = '''def canal_water(P):
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
'''
assert old in s
s = s.replace(old, new)

start = s.index('def canal_walls(P):')
end = s.index('def arch_z(')
new_walls = '''def canal_walls(P):
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


'''
s = s[:start] + new_walls + s[end:]

start = s.index("def pavement(P):")
end = s.index("# ------------------------------------------------------------------ canal")
new_pav = '''def pavement(P):
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


'''
s = s[:start] + new_pav + s[end:]

s = s.replace("    canal_water(P)\n    canal_walls(P)",
              "    canal_water(P)\n    canal_walk(P)\n    canal_walls(P)")
s = s.replace('B.terrain("Terrain", 320, 300, 116, 108, terrain_h, terrain_col, matte,',
              'B.terrain("Terrain", 320, 300, 104, 98, terrain_h, terrain_col, matte,')
s = s.replace('sph(P, "brball", 0.14, (px, yy, 1.55), "#b3aa96", mx=stone, seg=10, rings=6)',
              'sph(P, "brball", 0.14, (px, yy, 1.55), "#b3aa96", mx=stone, seg=7, rings=4)')
s = s.replace('sph(P, "drumball", 0.17, (bx + sx * 1.32, yc + sy * 7.6, 1.24), "#aba28e",\n                mx=stone, seg=10, rings=6)',
              'sph(P, "drumball", 0.17, (bx + sx * 1.32, yc + sy * 7.6, 1.24), "#aba28e",\n                mx=stone, seg=7, rings=4)')
s = s.replace('''        if sides:
            for sx in (-1, 1):
                for k in range(2):
                    sy = -d / 4 + k * d * 0.42
                    side_win(P, sx * w / 2, sy, zb + 1.65, 1.15, 1.3, sx,
                             lit=1 if R.random() < 0.12 else 0, fcol="#a9a699")''',
'''        if sides:
            for sx in (-1, 1):
                sy = -d * 0.18
                side_win(P, sx * w / 2, sy, zb + 1.65, 1.15, 1.3, sx,
                         lit=1 if R.random() < 0.12 else 0, fcol="#a9a699")''')

open(p, 'w', encoding='utf-8').write(s)
print("patched")
