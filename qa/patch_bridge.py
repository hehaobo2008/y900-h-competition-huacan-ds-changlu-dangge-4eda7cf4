p = 'tools/build_town.py'
s = open(p, encoding='utf-8').read()

# ---------------- replace willow ----------------
start = s.index('def willow(')
end = s.index('def bench(')
new_willow = '''def willow(P, x, y, z, h=6.4, name="willow"):
    trunk = [(x, y, z), (x + 0.12, y + 0.04, z + h * 0.3),
             (x - 0.06, y, z + h * 0.52)]
    P.append(B.tube(name + "_trunk", trunk, 0.22, "#5e4a34", matte, segments=6))
    for k in range(4):
        a = math.tau * k / 4 + 0.55
        p1 = (x + math.cos(a) * 1.0, y + math.sin(a) * 1.0, z + h * 0.7)
        p2 = (x + math.cos(a) * 1.9, y + math.sin(a) * 1.9, z + h * 0.55)
        P.append(B.tube(name + f"_br{k}", [(x, y, z + h * 0.48), p1, p2], 0.09,
                        "#5e4a34", matte, segments=5))
    # crown clumps
    for k in range(5):
        a = math.tau * k / 5 + 0.3
        rr = 0.9 + (k % 3) * 0.35
        cx = x + math.cos(a) * rr
        cy = y + math.sin(a) * rr
        cz = z + h * (0.78 + 0.06 * (k % 3))
        sph(P, name + "_crown", 0.95, (cx, cy, cz), "#7c8b52",
            scale=(1.15, 1.15, 0.55), mx=matte, seg=7, rings=5)
    # hanging curtain
    for k in range(14):
        a = math.tau * k / 14 + 0.2
        rr = 1.25 + 0.8 * (k % 3) / 2.0
        sx = x + math.cos(a) * rr
        sy = y + math.sin(a) * rr
        top = z + h * (0.9 - 0.05 * (k % 2))
        pts = [(sx, sy, top),
               (sx + math.cos(a) * 0.35, sy + math.sin(a) * 0.35, top - h * 0.14),
               (sx + math.cos(a) * 0.62, sy + math.sin(a) * 0.62, z + h * 0.42),
               (sx + math.cos(a) * 0.78, sy + math.sin(a) * 0.78, z + h * 0.13)]
        P.append(B.tube(name + f"_str{k}", pts, 0.018, "#6b6b45", matte, segments=4))
        tx, ty = -math.sin(a), math.cos(a)
        for j in range(3):
            t = 0.22 + j * 0.28
            lz = top - h * (0.12 + 0.74 * t)
            lx = sx + math.cos(a) * (0.18 + 0.62 * t)
            ly = sy + math.sin(a) * (0.18 + 0.62 * t)
            w = 0.2 + 0.06 * (k % 2)
            hh = 0.5 + 0.12 * ((k + j) % 3)
            col = "#7f8f52" if (k + j) % 2 else "#8f9b5c"
            quadp(P, name + f"_leaf{k}{j}",
                  [(lx - tx * w / 2, ly - ty * w / 2, lz),
                   (lx + tx * w / 2, ly + ty * w / 2, lz + 0.04),
                   (lx + tx * w * 0.4, ly + ty * w * 0.4, lz - hh),
                   (lx - tx * w * 0.3, ly - ty * w * 0.3, lz - hh * 0.9)],
                  col, matte)


'''
s = s[:start] + new_willow + s[end:]

# ---------------- replace footbridge ----------------
start = s.index('def footbridge(')
end = s.index('def headwall(')
new_bridge = '''def footbridge(P):
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
        arch_face(P, bx + sx * (width / 2 - 0.03), yc, 9.4, yc - 7.3, yc + 7.3,
                  -3.3, 1.74, -1.05, -2.9, 0.14, col="#8a8372", ring_col="#a29884")
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


'''
s = s[:start] + new_bridge + s[end:]
open(p, 'w', encoding='utf-8').write(s)
print('willow + footbridge rewritten')
