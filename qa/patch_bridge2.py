p = 'tools/build_town.py'
s = open(p, encoding='utf-8').read()

# cleaner coursing on arch faces
old = '''    # coursing above the ring
    for i in range(9):
        yy = yc - span / 2 + span * (i + 0.5) / 9
        zz = z_top - 0.28 - (i % 2) * 0.16
        boxp(P, "facecourse", (thick + 0.03, span / 9.0 * 0.92, 0.035), (x, yy, zz),
             "#736c5e", stone)'''
new = '''    # horizontal coursing above the arch (only where the face is solid)
    for k in range(3):
        zz = z_top - 0.28 - k * 0.46
        if crown + 0.12 < zz < z_top - 0.06:
            boxp(P, "facecourse", (thick + 0.02, span * 0.94, 0.032), (x, yc, zz),
                 "#736c5e", stone)'''
assert old in s
s = s.replace(old, new)
s = s.replace('''        arch_face(P, bx + sx * (width / 2 - 0.03), yc, 9.4, yc - 7.3, yc + 7.3,
                  -3.3, 1.74, -1.05, -2.9, 0.14, col="#8a8372", ring_col="#a29884")''','''        arch_face(P, bx + sx * (width / 2 - 0.02), yc, 9.4, yc - 7.3, yc + 7.3,
                  -3.3, 1.74, -1.05, -2.9, 0.24, col="#8a8372", ring_col="#a29884")''')

# willow: lower, fuller, more weeping
start = s.index('def willow(')
end = s.index('def bench(')
new_willow = '''def willow(P, x, y, z, h=6.4, name="willow"):
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


'''
s = s[:start] + new_willow + s[end:]
# five willows instead of six
s = s.replace("for i, (xx, sd) in enumerate(((-56, 1), (-44, -1), (-22, 1), (18, -1),\n                                  (36, 1), (58, -1))):",
              "for i, (xx, sd) in enumerate(((-56, 1), (-44, -1), (-22, 1), (18, -1),\n                                  (36, 1))):")
open(p, 'w', encoding='utf-8').write(s)
print('bridge courses + willow v2')
