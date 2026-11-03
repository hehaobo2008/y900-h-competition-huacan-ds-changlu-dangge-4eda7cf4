p = 'tools/build_town.py'
s = open(p, encoding='utf-8').read()

# stain band: only thin panels so shop interiors stay open
old = '''    # stained base band
    boxp(P, name + "_stain", (w + 0.02, d + 0.02, 0.55), (0, 0, 0.72), "#a69c86", matte)'''
new = '''    # stained base band (thin cladding panels, never a solid block)
    boxp(P, name + "_stainf", (w + 0.02, 0.02, 0.5), (0, fy - 0.012, 0.7), "#a69c86", matte)
    for sx in (-1, 1):
        boxp(P, name + "_stains", (0.02, d, 0.5), (sx * (w / 2 + 0.005), 0, 0.7),
             "#a69c86", matte)'''
assert old in s
s = s.replace(old, new)

# windows a touch higher
s = s.replace('win(P, cx, zb + 1.66, win_w, 1.38, fy, lit=lit, bars=bars, blind=blind,',
              'win(P, cx, zb + 1.70, win_w, 1.38, fy, lit=lit, bars=bars, blind=blind,')

# fewer goods per open shop
s = s.replace('''        for k in range(4):
            zz = z0 + 0.45 + k * (oh - 0.9) / 3.6
            boxp(P, name + "_shb", (opw - 0.3, 0.36, 0.04), (cx, fy + dep - 0.22, zz),
                 "#8a6744", matte)
            ng = 5
            for g in range(ng):
                gx = cx - opw * 0.38 + (opw * 0.76) * g / max(1, ng - 1)
                gc = ["#a94b38", "#c8b06a", "#5b7d86", "#b7b092", "#7c8f5e"][(k * 3 + g) % 5]
                boxp(P, name + "_good", (0.14, 0.16, 0.22),
                     (gx, fy + dep - 0.38, zz + 0.14), gc, matte)''',
'''        for k in range(3):
            zz = z0 + 0.55 + k * (oh - 1.15) / 2.4
            boxp(P, name + "_shb", (opw - 0.3, 0.36, 0.04), (cx, fy + dep - 0.22, zz),
                 "#8a6744", matte)
            ng = 4
            for g in range(ng):
                gx = cx - opw * 0.36 + (opw * 0.72) * g / max(1, ng - 1)
                gc = ["#a94b38", "#c8b06a", "#5b7d86", "#b7b092", "#7c8f5e"][(k * 3 + g) % 5]
                boxp(P, name + "_good", (0.15, 0.18, 0.24),
                     (gx, fy + dep - 0.38, zz + 0.14), gc, matte)''')

# simplify roof tank
start = s.index('def roof_tank(')
end = s.index('def antenna(')
new_tank = '''def roof_tank(P, cx, cy, z, r=0.82, name="tank"):
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
    for k in range(3):
        boxp(P, name + "_rung", (0.03, 0.24, 0.03), (cx - r - 0.05, cy, z + 1.4 + k * 0.32),
             "#6d6757", metal)


'''
s = s[:start] + new_tank + s[end:]

# simplify antenna
start = s.index('def antenna(')
end = s.index('def bulkhead(')
new_ant = '''def antenna(P, cx, cy, z, name="ant"):
    cylp(P, name + "_mast", 0.035, 3.2, (cx, cy, z + 1.6), "#5a564a", metal, seg=6)
    boxp(P, name + "_boom", (0.03, 0.03, 0.9), (cx, cy + 0.7, z + 2.6),
         "#5a564a", metal, rot=(math.pi / 2, 0, 0))
    for k in range(3):
        ln = 0.9 - k * 0.2
        boxp(P, name + "_el", (ln, 0.025, 0.025), (cx, cy + 0.4 + k * 0.32, z + 2.6),
             "#6b6658", metal)


'''
s = s[:start] + new_ant + s[end:]

# prefix sub-part names for accounting
s = s.replace('ac_unit(P, cx + win_w * 0.75, zb + 1.18, fy, name=f"ac{f}{i}")',
              'ac_unit(P, cx + win_w * 0.75, zb + 1.18, fy, name=f"{name}_ac{f}{i}")')
s = s.replace('win(P, cx, zb + 1.70, win_w, 1.38, fy, lit=lit, bars=bars, blind=blind,\n                    name=f"w{f}{i}")',
              'win(P, cx, zb + 1.70, win_w, 1.38, fy, lit=lit, bars=bars, blind=blind,\n                    name=f"{name}_w{f}{i}")')
s = s.replace('balcony(P, cx, zb + 0.02, fy, w=min(2.7, bw - 0.35), dep=1.02,\n                        laundry=laundry, name=f"bal{f}{i}")',
              'balcony(P, cx, zb + 0.02, fy, w=min(2.7, bw - 0.35), dep=1.02,\n                        laundry=laundry, name=f"{name}_bal{f}{i}")')

# side window prefix
s = s.replace('def side_win(P, x, cy, cz, w, h, side, lit=0, fcol="#b2afa3"):',
              'def side_win(P, x, cy, cz, w, h, side, lit=0, fcol="#b2afa3", name="sw"):')
for old_name in ['"sw_r"', '"sw_g"', '"sw_f"', '"sw_m"', '"sw_sill"']:
    s = s.replace(old_name, 'name + "_r"' if old_name == '"sw_r"' else
                  ('name + "_g"' if old_name == '"sw_g"' else
                   ('name + "_f"' if old_name == '"sw_f"' else
                    ('name + "_m"' if old_name == '"sw_m"' else 'name + "_sill"'))))
s = s.replace('''                side_win(P, sx * w / 2, sy, zb + 1.65, 1.15, 1.3, sx,
                         lit=1 if R.random() < 0.12 else 0, fcol="#a9a699")''',
'''                side_win(P, sx * w / 2, sy, zb + 1.65, 1.15, 1.3, sx,
                         lit=1 if R.random() < 0.12 else 0, fcol="#a9a699",
                         name=f"{name}_sw{f}{'L' if sx < 0 else 'R'}")''')

open(p, 'w', encoding='utf-8').write(s)
print('patched 2')
