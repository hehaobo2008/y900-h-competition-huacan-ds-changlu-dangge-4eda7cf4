p = 'tools/build_town.py'
s = open(p, encoding='utf-8').read()
s = s.replace('''        rim = B.cylinder("rim", 0.188, 0.15, (sx * 0.735, yy, 0.303), (0, math.pi / 2, 0),
                         segments=20, color="#a5a091", material=chrome, smooth=True)
        W.append(rim)
        hub = B.lathe("hubcap",
                      [(0.035, 0.0), (0.09, 0.008), (0.135, 0.035), (0.156, 0.062),
                       (0.147, 0.083)],
                      loc=(sx * 0.812, yy, 0.303), rot=(0, sx * math.pi / 2, 0),
                      segments=20, color="#cfc8b4", material=chrome, smooth=True)
        W.append(hub)
        # spokes + lugs
        for k in range(6):
            a = math.tau * k / 6 + 0.25
            W.append(B.box("hubspoke", (0.016, 0.03, 0.115),
                           (sx * 0.825, yy + 0.085 * math.cos(a), 0.303 + 0.085 * math.sin(a)),
                           (a - math.pi / 2, 0, 0), color="#b9b29e", material=chrome))
        for k in range(5):
            a = math.tau * k / 5 + 0.3
            W.append(B.cylinder("lug", 0.017, 0.02,
                                (sx * 0.835, yy + 0.128 * math.cos(a), 0.303 + 0.128 * math.sin(a)),
                                (0, sx * math.pi / 2, 0), segments=6,
                                color="#b5ae9a", material=chrome, smooth=True))
        W.append(B.cylinder("disc", 0.15, 0.025, (sx * 0.695, yy, 0.303),
                            (0, math.pi / 2, 0), segments=14, color="#6b6659",
                            material=chrome, smooth=True))''','''        rim = B.cylinder("rim", 0.188, 0.15, (sx * 0.735, yy, 0.303), (0, math.pi / 2, 0),
                         segments=24, color="#8e8a7c", material=chrome, smooth=True)
        W.append(rim)
        lip = []
        for k in range(25):
            a = math.tau * k / 24
            lip.append((sx * 0.812, yy + 0.18 * math.cos(a), 0.303 + 0.18 * math.sin(a)))
        W.append(B.tube("rimlip", lip, 0.012, "#c3bca8", chrome, segments=4, cyclic=True))
        hub = B.lathe("hubcap",
                      [(0.03, 0.0), (0.075, 0.008), (0.112, 0.03), (0.128, 0.055),
                       (0.120, 0.072)],
                      loc=(sx * 0.812, yy, 0.303), rot=(0, sx * math.pi / 2, 0),
                      segments=24, color="#cfc8b4", material=chrome, smooth=True)
        W.append(hub)
        for k in range(5):
            a = math.tau * k / 5 + 0.3
            W.append(B.box("hubspoke", (0.014, 0.028, 0.1),
                           (sx * 0.828, yy + 0.07 * math.cos(a), 0.303 + 0.07 * math.sin(a)),
                           (a - math.pi / 2, 0, 0), color="#a9a38e", material=chrome))
            W.append(B.cylinder("lug", 0.016, 0.02,
                                (sx * 0.833, yy + 0.099 * math.cos(a), 0.303 + 0.099 * math.sin(a)),
                                (0, sx * math.pi / 2, 0), segments=6,
                                color="#b5ae9a", material=chrome, smooth=True))
        W.append(B.cylinder("badge", 0.032, 0.01, (sx * 0.834, yy, 0.303),
                            (0, sx * math.pi / 2, 0), segments=12, color="#7a2a31",
                            material=chrome, smooth=True))
        W.append(B.cylinder("disc", 0.15, 0.025, (sx * 0.695, yy, 0.303),
                            (0, math.pi / 2, 0), segments=16, color="#6b6659",
                            material=chrome, smooth=True))
        for k, off in enumerate((-0.05, 0.0, 0.05)):
            ring = []
            for j in range(29):
                a = math.tau * j / 28
                ring.append((sx * 0.735 + off, yy + 0.298 * math.cos(a),
                             0.303 + 0.298 * math.sin(a)))
            W.append(B.tube("treadgroove", ring, 0.009, "#211f1c", rubber,
                            segments=4, cyclic=True))
        sw = []
        for j in range(25):
            a = math.tau * j / 24
            sw.append((sx * 0.842, yy + 0.23 * math.cos(a), 0.303 + 0.23 * math.sin(a)))
        W.append(B.tube("sidewall", sw, 0.006, "#cbc4ae", rubber, segments=4, cyclic=True))''')
s = s.replace('''    # rear view mirror, visors, dome light, headliner''','''    # seat belts + buckles
    for sx in (-1, 1):
        beam("Interior", (sx * 0.68, 0.02, 1.36), (sx * 0.2, 0.22, 0.78), 0.035,
             "#b3a789", interior)
        bx("Chrome", (0.06, 0.03, 0.07), (sx * 0.2, 0.24, 0.74), "#b9b19d", chrome)
    for sx in (-0.45, -0.2, 0.1, 0.35):
        bx("Trim", (0.1, 0.03, 0.06), (sx, 0.392, 0.9), "#2c2a24", trim)
    for k in range(3):
        bx("Chrome", (0.07, 0.02, 0.02), (-0.1 + k * 0.1, 0.393, 0.82), "#8f8978", chrome)
    for sx in (-1, 1):
        cy("Chrome", 0.03, 0.03, (sx * 0.765, 0.18, 0.73), "#a9a28f", chrome,
           rot=(0, math.pi / 2, 0), seg=8)
        bx("Chrome", (0.04, 0.12, 0.035), (sx * 0.77, 0.12, 0.74), "#b3ab97", chrome,
           rot=(0, 0, sx * 0.4))
        bx("Chrome", (0.035, 0.13, 0.03), (sx * 0.77, -0.42, 0.76), "#b3ab97", chrome)
    for k in range(4):
        bx("Trim", (0.92, 0.012, 0.008), (0, -1.09 - k * 0.055, 1.18 - k * 0.02),
           "#25231f", trim, rot=(0.6, 0, 0))
    quad("Trim", [(-0.6, 0.43, 1.39), (0.6, 0.43, 1.39), (0.58, 0.395, 1.428),
                  (-0.58, 0.395, 1.428)], "#253b3d", glassm, "tintband")
    # rear view mirror, visors, dome light, headliner''')
s = s.replace('''    # driveshaft
    cy("Under", 0.03, 1.4, (0, 0.3, 0.22), "#5b564a", rubber,
       rot=(math.pi / 2, 0, 0), seg=6)''','''    # driveshaft + coil springs + shocks
    cy("Under", 0.03, 1.4, (0, 0.3, 0.22), "#5b564a", rubber,
       rot=(math.pi / 2, 0, 0), seg=6)
    for sx in (-1, 1):
        for yy in (-1.25, 1.3):
            pts = []
            for k in range(15):
                a = math.tau * k / 6
                pts.append((sx * 0.6 + 0.11 * math.cos(a),
                            yy + 0.11 * math.sin(a),
                            0.28 + 0.028 * k))
            G["Under"].append(B.tube("coil", pts, 0.018, "#6b6658", rubber, segments=4))
            cy("Under", 0.035, 0.24, (sx * 0.66, yy + 0.16, 0.5), "#5d584c", rubber,
               rot=(0.25, 0, 0), seg=6)
    cy("Under", 0.018, 1.3, (0, -1.15, 0.22), "#777164", chrome,
       rot=(0, math.pi / 2, 0), seg=6)
    G["Under"].append(B.tube("brakeline", [(-0.55, 1.25, 0.2), (-0.62, 0.1, 0.18),
                                          (-0.6, -1.1, 0.2), (-0.3, -1.3, 0.24)],
                            0.012, "#6b6659", rubber, segments=4))''')
s = s.replace('''    # air dam
    bx("Trim", (1.2, 0.06, 0.09), (0, 2.10, 0.335), blk, trim)''','''    # air dam + bumper bolts
    bx("Trim", (1.2, 0.06, 0.09), (0, 2.10, 0.335), blk, trim)
    for sx in (-0.6, 0.6):
        cy("Chrome", 0.018, 0.012, (sx, 2.20, 0.5), "#cfc8b4", chrome,
           rot=(math.pi / 2, 0, 0), seg=6)
    cy("Chrome", 0.055, 0.016, (0, 1.98, 0.938), "#c9c2ae", chrome,
       rot=(math.pi / 2, 0, 0), seg=12)''')
s = s.replace('''    # rear valance + mud flaps
    bx("Trim", (1.3, 0.08, 0.12), (0, -2.09, 0.33), blk, trim)''','''    # rear valance + mud flaps + reflectors + bumper bolts
    bx("Trim", (1.3, 0.08, 0.12), (0, -2.09, 0.33), blk, trim)
    for sx in (-1, 1):
        bx("LightR", (0.1, 0.02, 0.05), (sx * 0.74, -2.15, 0.62), "#a3342b", lensr)
        cy("Chrome", 0.018, 0.012, (sx * 0.6, -2.20, 0.5), "#cfc8b4", chrome,
           rot=(math.pi / 2, 0, 0), seg=6)''')
open(p, 'w', encoding='utf-8').write(s)
print('car enriched')
