def build_car():
    B.reset(1996)
    paint = B.vmat("CarPaint", 0.30, 0.35)
    chrome = B.vmat("CarChrome", 0.13, 0.95)
    rubber = B.vmat("CarRubber", 0.92)
    glassm = B.mat("CarGlass", "#25393d", rough=0.06, metal=0.25, alpha=0.45)
    trim = B.mat("CarTrim", "#211f1b", rough=0.62)
    interior = B.vmat("CarInterior", 0.88)
    lensw = B.mat("CarLampW", "#efe5c8", rough=0.18, emission="#ffe9bd", emis_strength=0.55)
    lensr = B.mat("CarLampR", "#8f1f1a", rough=0.22, emission="#ff3a2a", emis_strength=0.85)
    plate_m = B.mat("CarPlate", "#ded8c5", rough=0.75)
    wine = "#5a1f27"
    cream = "#ded3b8"
    blk = "#26241f"
    tan = "#a58d6b"
    G = {"Paint": [], "Chrome": [], "Glass": [], "Trim": [], "LightW": [],
         "LightR": [], "Plate": [], "Interior": [], "Under": []}

    def bx(g, size, loc, color, mx, bevel=0.0, rot=(0, 0, 0), name="p"):
        G[g].append(B.box(name, size, loc, rot, color=color, material=mx, bevel=bevel))

    def cy(g, r, depth, loc, color, mx, rot=(0, 0, 0), seg=16, r2=None, name="c",
           smooth=True, bevel=0.0):
        G[g].append(B.cylinder(name, r, depth, loc, rot, segments=seg, color=color,
                               material=mx, radius2=r2, smooth=smooth, bevel=bevel))

    def beam(g, p1, p2, w=0.02, color="#cfc9b7", mx=None, name="b"):
        G[g].append(B.beam(name, p1, p2, w, w, color=color, material=mx or chrome))

    def quad(g, corners, color, mx, name="q"):
        G[g].append(B.quad(name, corners, color, mx))

    # ------------------------------------------------ lower body shell
    stations = [
        (-2.06, 0.71, 0.40, 0.83),
        (-1.99, 0.79, 0.35, 0.87),
        (-1.74, 0.842, 0.30, 0.905),
        (-1.20, 0.850, 0.285, 0.920),
        (0.00, 0.850, 0.285, 0.925),
        (1.00, 0.850, 0.285, 0.925),
        (1.66, 0.838, 0.305, 0.905),
        (1.94, 0.79, 0.34, 0.875),
        (2.06, 0.70, 0.40, 0.83),
    ]
    secs = []
    for (yy, ww, z0, z1) in stations:
        pts = [(-ww * 0.86, z0), (ww * 0.86, z0), (ww, z0 + 0.19), (ww, z1 - 0.07),
               (ww * 0.955, z1), (-ww * 0.955, z1), (-ww, z1 - 0.07), (-ww, z0 + 0.19)]
        secs.append(((0, yy, 0), [(a, b) for a, b in pts]))
    G["Paint"].append(B.loft("lowerbody", secs, color=wine, material=paint, smooth=False))

    # hood / trunk / cowl panels and shut lines
    bx("Paint", (1.32, 1.16, 0.032), (0, 1.46, 0.932), wine, paint, bevel=0.015)
    bx("Paint", (0.03, 1.1, 0.035), (-0.30, 1.46, 0.945), cream, paint)
    bx("Paint", (0.03, 1.1, 0.035), (0.30, 1.46, 0.945), cream, paint)
    bx("Paint", (1.28, 0.72, 0.03), (0, -1.74, 0.918), wine, paint, bevel=0.015)
    bx("Trim", (1.44, 0.014, 0.008), (0, 1.07, 0.934), blk, trim)
    bx("Trim", (1.34, 0.014, 0.008), (0, -1.52, 0.923), blk, trim)
    bx("Trim", (0.012, 0.95, 0.008), (-0.635, 1.46, 0.935), blk, trim)
    bx("Trim", (0.012, 0.95, 0.008), (0.635, 1.46, 0.935), blk, trim)
    # cowl vent + wipers
    bx("Trim", (1.24, 0.16, 0.03), (0, 1.12, 0.945), blk, trim)
    for sx in (-1, 1):
        bx("Trim", (0.52, 0.018, 0.014), (sx * 0.27, 1.15, 0.962), blk, trim,
           rot=(0, 0, sx * 0.22))
    # rocker strips and side mouldings
    for sx in (-1, 1):
        bx("Trim", (0.014, 2.7, 0.11), (sx * 0.842, 0, 0.335), blk, trim)
        bx("Chrome", (0.016, 2.35, 0.03), (sx * 0.850, 0, 0.60), "#bdb6a2", chrome)
        bx("Trim", (0.018, 2.30, 0.014), (sx * 0.853, 0, 0.58), blk, trim)

    # ------------------------------------------------ greenhouse shell
    cab = [
        (-1.80, 0.760, 0.935),
        (-1.60, 0.770, 1.02),
        (-1.30, 0.745, 1.32),
        (-1.02, 0.725, 1.455),
        (-0.30, 0.720, 1.468),
        (0.34, 0.720, 1.468),
        (0.62, 0.730, 1.455),
        (0.98, 0.752, 1.19),
        (1.16, 0.775, 1.00),
    ]
    csecs = []
    for (yy, ww, ztop) in cab:
        pts = [(-ww, 0.90), (ww, 0.90), (ww, ztop - 0.055), (ww * 0.86, ztop),
               (-ww * 0.86, ztop), (-ww, ztop - 0.055)]
        csecs.append(((0, yy, 0), [(a, b) for a, b in pts]))
    G["Paint"].append(B.loft("cabin", csecs, color=wine, material=paint, smooth=False))
    # vinyl roof cap
    bx("Paint", (1.30, 1.26, 0.03), (0, -0.10, 1.484), cream, paint, bevel=0.025)
    bx("Chrome", (0.02, 1.22, 0.02), (-0.655, -0.10, 1.458), "#c9c2ae", chrome)
    bx("Chrome", (0.02, 1.22, 0.02), (0.655, -0.10, 1.458), "#c9c2ae", chrome)
    bx("Chrome", (1.30, 0.025, 0.02), (0, 0.525, 1.460), "#c9c2ae", chrome)
    bx("Chrome", (1.30, 0.025, 0.02), (0, -0.725, 1.460), "#c9c2ae", chrome)

    # ------------------------------------------------ glazing
    ws = [(-0.625, 1.155, 1.005), (0.625, 1.155, 1.005),
          (0.535, 0.625, 1.438), (-0.535, 0.625, 1.438)]
    ws = [(x, y + 0.012, z + 0.010) for (x, y, z) in ws]
    quad("Glass", ws, "#a9c1bd", glassm, "windshield")
    for i in range(4):
        beam("Chrome", ws[i], ws[(i + 1) % 4], 0.022, "#bcb5a2", chrome, "ws_trim")
    rw = [(-0.585, -1.665, 1.015), (0.585, -1.665, 1.015),
          (0.492, -1.275, 1.428), (-0.492, -1.275, 1.428)]
    rw = [(x, y - 0.012, z + 0.008) for (x, y, z) in rw]
    quad("Glass", rw, "#9fb4b1", glassm, "rearglass")
    for i in range(4):
        beam("Chrome", rw[i], rw[(i + 1) % 4], 0.021, "#bcb5a2", chrome, "rw_trim")
    # side windows (front, rear, quarter) both sides
    for sx in (-1, 1):
        xb = sx * 0.741
        xt = sx * 0.700
        wins = [
            [(xb, 0.955, 1.008), (xb, 0.075, 1.008), (xt, 0.135, 1.415), (xt, 0.735, 1.405)],
            [(xb, -0.005, 1.008), (xb, -0.800, 1.008), (xt, -0.740, 1.418), (xt, 0.055, 1.418)],
            [(xb + sx * 0.002, -0.860, 1.012), (xb, -1.085, 1.015),
             (xt, -1.195, 1.385), (xt, -0.800, 1.414)],
        ]
        for j, corners in enumerate(wins):
            quad("Glass", corners, "#a3b8b4", glassm, f"sideglass{sx}{j}")
            for i in range(4):
                beam("Chrome", corners[i], corners[(i + 1) % 4], 0.017, "#b9b2a0", chrome,
                     "sw_trim")
        # B pillar
        bx("Trim", (0.018, 0.085, 0.44), (sx * 0.735, 0.045, 1.20), blk, trim)
        # A / C pillar rubbers
        beam("Trim", (sx * 0.742, 0.965, 1.005), (sx * 0.700, 0.745, 1.410), 0.026, blk, trim)
        beam("Trim", (sx * 0.742, -0.855, 1.01), (sx * 0.700, -1.20, 1.39), 0.028, blk, trim)
        # beltline chrome
        bx("Chrome", (0.018, 2.62, 0.024), (sx * 0.767, -0.22, 0.955), "#c6bfab", chrome)
    # ---------------------- doors, handles, seams
    for sx in (-1, 1):
        for yy in (0.02, -1.02):
            bx("Trim", (0.012, 0.014, 0.56), (sx * 0.853, yy, 0.615), blk, trim)
        for yy in (0.14, -0.84):
            bx("Chrome", (0.035, 0.17, 0.045), (sx * 0.858, yy, 0.835), "#c2bba7", chrome,
               bevel=0.006)
            bx("Trim", (0.02, 0.19, 0.018), (sx * 0.862, yy, 0.812), blk, trim)
        # door lock
        cy("Chrome", 0.018, 0.02, (sx * 0.858, 0.06, 0.885), "#cfc8b4", chrome,
           rot=(0, math.pi / 2, 0), seg=8)
        # side marker
        bx("LightW", (0.018, 0.1, 0.045), (sx * 0.856, 1.5, 0.68), "#e0b25e", lensw)

    # ------------------------------------------------ front end
    bx("Paint", (1.72, 0.16, 0.2), (0, 2.10, 0.50), wine, paint, bevel=0.02)
    bx("Chrome", (1.74, 0.1, 0.055), (0, 2.14, 0.59), "#c8c1ad", chrome)
    bx("Trim", (1.64, 0.02, 0.035), (0, 2.195, 0.49), blk, trim)
    for sx in (-1, 1):
        bx("Paint", (0.14, 0.34, 0.2), (sx * 0.83, 1.96, 0.50), wine, paint,
           bevel=0.02, rot=(0, 0, sx * 0.28))
        bx("Chrome", (0.06, 0.06, 0.20), (sx * 0.44, 2.185, 0.53), "#c8c1ad", chrome,
           bevel=0.01)
    # grille
    bx("Trim", (1.06, 0.05, 0.25), (0, 2.075, 0.735), blk, trim)
    for k in range(5):
        bx("Chrome", (0.98, 0.018, 0.02), (0, 2.105, 0.655 + k * 0.04), "#b8b19d", chrome)
    bx("Chrome", (0.98, 0.03, 0.02), (0, 2.106, 0.815), "#c6bfab", chrome)
    for sx in (-1, 1):
        bx("Chrome", (0.03, 0.03, 0.19), (sx * 0.52, 2.106, 0.735), "#c6bfab", chrome)
    cy("Chrome", 0.055, 0.02, (0, 2.108, 0.735), "#cfc8b4", chrome,
       rot=(math.pi / 2, 0, 0), seg=12)
    cy("Paint", 0.035, 0.024, (0, 2.11, 0.735), wine, paint,
       rot=(math.pi / 2, 0, 0), seg=12)
    # headlights + indicators
    for sx in (-1, 1):
        bx("Chrome", (0.36, 0.03, 0.2), (sx * 0.61, 2.075, 0.815), "#c6bfab", chrome,
           bevel=0.008)
        bx("LightW", (0.30, 0.022, 0.15), (sx * 0.61, 2.09, 0.815), "#f0e8cc", lensw)
        bx("Chrome", (0.30, 0.026, 0.012), (sx * 0.61, 2.095, 0.815), "#9f9a89", chrome)
        bx("LightW", (0.28, 0.02, 0.055), (sx * 0.61, 2.09, 0.675), "#d99a4a", lensw)
    # front plate
    bx("Trim", (0.52, 0.03, 0.18), (0, 2.207, 0.72), blk, trim)
    bx("Plate", (0.46, 0.012, 0.14), (0, 2.222, 0.72), "#e2dcc8", plate_m)
    for sx in (-0.17, 0.17):
        cy("Trim", 0.012, 0.008, (sx, 2.23, 0.72), blk, trim,
           rot=(math.pi / 2, 0, 0), seg=6)
    # air dam
    bx("Trim", (1.2, 0.06, 0.09), (0, 2.10, 0.335), blk, trim)

    # ------------------------------------------------ rear end
    bx("Paint", (1.71, 0.16, 0.2), (0, -2.10, 0.50), wine, paint, bevel=0.02)
    bx("Chrome", (1.74, 0.1, 0.055), (0, -2.14, 0.59), "#c8c1ad", chrome)
    bx("Trim", (1.63, 0.02, 0.035), (0, -2.195, 0.49), blk, trim)
    for sx in (-1, 1):
        bx("Paint", (0.14, 0.34, 0.2), (sx * 0.83, -1.96, 0.50), wine, paint,
           bevel=0.02, rot=(0, 0, -sx * 0.28))
    for sx in (-1, 1):
        bx("Chrome", (0.46, 0.03, 0.19), (sx * 0.56, -2.075, 0.80), "#c6bfab", chrome,
           bevel=0.008)
        bx("LightR", (0.4, 0.024, 0.14), (sx * 0.56, -2.09, 0.80), "#b02a1f", lensr)
        bx("LightW", (0.11, 0.026, 0.14), (sx * 0.73, -2.09, 0.80), "#e6dcc0", lensw)
        for k in range(3):
            bx("Trim", (0.34, 0.025, 0.012), (sx * 0.56, -2.094, 0.745 + k * 0.035), blk, trim)
    bx("Chrome", (1.3, 0.022, 0.025), (0, -2.085, 0.9), "#c0b9a5", chrome)
    # rear plate
    bx("Trim", (0.52, 0.03, 0.18), (0, -2.207, 0.72), blk, trim)
    bx("Plate", (0.46, 0.012, 0.14), (0, -2.222, 0.72), "#e2dcc8", plate_m)
    for sx in (-0.17, 0.17):
        cy("Trim", 0.012, 0.008, (sx, -2.23, 0.72), blk, trim,
           rot=(math.pi / 2, 0, 0), seg=6)
    # trunk keyhole + badge (blank)
    cy("Chrome", 0.016, 0.02, (0, -2.085, 0.74), "#cfc8b4", chrome,
       rot=(math.pi / 2, 0, 0), seg=6)
    cy("Chrome", 0.06, 0.018, (0, -2.083, 0.885), "#cfc8b4", chrome,
       rot=(math.pi / 2, 0, 0), seg=10)
    # exhaust
    cy("Under", 0.035, 0.55, (-0.38, -1.95, 0.24), "#6b6659", rubber,
       rot=(math.pi / 2, 0, 0), seg=8)
    cy("Under", 0.045, 0.12, (-0.38, -2.21, 0.24), "#4d4a42", rubber,
       rot=(math.pi / 2, 0, 0), seg=8)

    # mirrors
    for sx in (-1, 1):
        beam("Trim", (sx * 0.79, 0.87, 1.005), (sx * 0.885, 0.82, 1.03), 0.035, blk, trim)
        bx("Chrome", (0.05, 0.15, 0.1), (sx * 0.9, 0.80, 1.04), "#c2bba7", chrome,
           bevel=0.012)
        bx("Glass", (0.02, 0.12, 0.075), (sx * 0.888, 0.735, 1.04), "#899d9a", glassm)
    # antenna
    cy("Chrome", 0.018, 0.07, (0.66, 1.28, 0.945), "#8e897a", chrome, seg=8)
    beam("Trim", (0.66, 1.28, 0.95), (0.68, 1.07, 1.49), 0.009, "#4a463c", chrome)

    # ------------------------------------------------ interior
    bx("Trim", (1.48, 3.1, 0.03), (0, -0.15, 0.35), "#4a4238", trim)
    bx("Interior", (1.42, 0.42, 0.24), (0, 0.69, 0.84), "#5b4c3c", interior, bevel=0.02)
    bx("Interior", (0.55, 0.2, 0.12), (-0.32, 0.55, 0.945), "#4e4033", interior,
       bevel=0.015)
    for sx in (-0.45, -0.2):
        cy("Trim", 0.035, 0.012, (sx, 0.445, 0.951), "#2e2c26", trim,
           rot=(math.pi / 2, 0, 0), seg=8)
    # steering wheel
    wheel_pts = []
    for i in range(19):
        a = math.tau * i / 18
        wheel_pts.append((-0.34 + 0.17 * math.cos(a),
                          0.42 + 0.05 * math.sin(a),
                          0.94 + 0.16 * math.sin(a)))
    G["Trim"].append(B.tube("steerwheel", wheel_pts, 0.018, "#2f2b24", trim, segments=5,
                            cyclic=True))
    beam("Trim", (-0.34, 0.39, 0.94), (-0.34, 0.43, 0.82), 0.028, "#3a352c", trim)
    for a in (0.2, 2.4, 4.4):
        beam("Trim", (-0.34, 0.43, 0.94),
             (-0.34 + 0.16 * math.cos(a), 0.43, 0.94 + 0.15 * math.sin(a)), 0.012,
             "#413b30", trim)
    # seats
    for sx in (-1, 1):
        cx = sx * 0.37
        bx("Interior", (0.5, 0.56, 0.15), (cx, 0.10, 0.585), tan, interior, bevel=0.03)
        bx("Interior", (0.48, 0.16, 0.56), (cx, -0.10, 0.86), tan, interior,
           bevel=0.03, rot=(-0.13, 0, 0))
        bx("Interior", (0.27, 0.13, 0.22), (cx, -0.16, 1.25), tan, interior,
           bevel=0.025)
        bx("Interior", (0.05, 0.4, 0.2), (cx + sx * 0.26, -0.02, 0.72), "#8f7a5b", interior)
    # rear bench + parcel shelf
    bx("Interior", (1.3, 0.55, 0.15), (0, -0.98, 0.58), tan, interior, bevel=0.03)
    bx("Interior", (1.3, 0.15, 0.5), (0, -1.22, 0.85), tan, interior, bevel=0.03,
       rot=(-0.12, 0, 0))
    for sx in (-0.38, 0.38):
        bx("Interior", (0.3, 0.12, 0.2), (sx, -1.30, 1.18), tan, interior, bevel=0.02)
    bx("Interior", (1.28, 0.4, 0.04), (0, -1.7, 0.9), "#4a4034", trim)
    # console + gear lever
    bx("Interior", (0.22, 0.6, 0.22), (0, 0.25, 0.52), "#4c4034", interior, bevel=0.02)
    beam("Trim", (0.0, 0.3, 0.55), (0.02, 0.34, 0.73), 0.02, "#2f2b24", trim)
    G["Trim"].append(B.sphere("gearknob", 0.045, (0.02, 0.34, 0.75), color="#2f2b24",
                              material=trim, segments=8, rings=5))
    # door cards / armrests
    for sx in (-1, 1):
        bx("Interior", (0.02, 2.0, 0.5), (sx * 0.79, 0.02, 0.62), tan, interior)
        bx("Interior", (0.12, 0.5, 0.1), (sx * 0.73, 0.2, 0.67), "#8d7759", interior)
    # rear view mirror + visors + headliner strip
    bx("Trim", (0.24, 0.04, 0.08), (0, 0.62, 1.34), "#2d2a24", trim)
    bx("Glass", (0.2, 0.02, 0.06), (0, 0.605, 1.34), "#8fa4a1", glassm)
    for sx in (-1, 1):
        bx("Interior", (0.36, 0.2, 0.025), (sx * 0.34, 0.55, 1.42), "#9c8768", interior)
    # small dome lamp
    cy("LightW", 0.04, 0.02, (0, -0.35, 1.43), "#f0e3bc", lensw,
       rot=(math.pi / 2, 0, 0), seg=8)

    # ------------------------------------------------ underbody
    bx("Under", (1.5, 3.4, 0.1), (0, 0, 0.26), "#3b3933", rubber)
    cy("Under", 0.035, 1.7, (-0.35, 0.15, 0.21), "#6a6558", rubber,
       rot=(math.pi / 2, 0, 0), seg=6)
    bx("Under", (0.55, 0.4, 0.2), (-0.35, -1.0, 0.22), "#575349", rubber, bevel=0.02)
    cy("Under", 0.035, 0.5, (-0.35, -1.9, 0.205), "#5e594d", rubber,
       rot=(math.pi / 2, 0, 0), seg=6)
    for yy in (-1.32, 1.32):
        cy("Under", 0.045, 1.5, (0, yy, 0.30), "#4d4940", rubber,
           rot=(0, math.pi / 2, 0), seg=8)
    bx("Under", (1.0, 0.55, 0.2), (0, -1.45, 0.36), "#4a463d", rubber)
    for sx in (-1, 1):
        for yy in (-1.32, 1.32):
            beam("Under", (sx * 0.62, yy, 0.3), (sx * 0.8, yy + 0.35, 0.45), 0.035,
                 "#5a5549", rubber)
    # wheel wells
    for sx in (-1, 1):
        for yy in (-1.32, 1.32):
            bx("Trim", (0.03, 0.72, 0.56), (sx * 0.845, yy, 0.40), blk, trim)
            # mud flap behind rear wheels
    for sx in (-1, 1):
        bx("Trim", (0.24, 0.02, 0.28), (sx * 0.8, -1.72, 0.20), blk, trim)

    # ------------------------------------------------ wheels (separate objects)
    wheel_objs = []

    def make_wheel(sx, yy, label):
        W = {"Paint": [], "Chrome": [], "Trim": [], "Under": []}
        prof = [(0.175, -0.095), (0.245, -0.105), (0.288, -0.082), (0.300, -0.03),
                (0.300, 0.03), (0.288, 0.082), (0.245, 0.105), (0.175, 0.095)]
        tire = B.lathe("tire", prof, loc=(sx * 0.73, yy, 0.30), rot=(0, math.pi / 2, 0),
                       segments=24, color="#33312c", material=rubber, smooth=True)
        W["Paint"].append(tire)
        rim = B.cylinder("rim", 0.19, 0.145, (sx * 0.73, yy, 0.30), (0, math.pi / 2, 0),
                         segments=18, color="#a5a091", material=chrome, smooth=True)
        W["Chrome"].append(rim)
        hub = B.lathe("hubcap",
                      [(0.035, 0.0), (0.09, 0.008), (0.135, 0.035), (0.155, 0.062),
                       (0.145, 0.083)],
                      loc=(sx * 0.805, yy, 0.30), rot=(0, sx * math.pi / 2, 0),
                      segments=18, color="#cfc8b4", material=chrome, smooth=True)
        W["Chrome"].append(hub)
        for k in range(5):
            a = math.tau * k / 5 + 0.3
            lug = B.cylinder("lug", 0.018, 0.02,
                             (sx * 0.833, yy + 0.085 * math.cos(a), 0.30 + 0.085 * math.sin(a)),
                             (0, sx * math.pi / 2, 0), segments=6,
                             color="#b5ae9a", material=chrome, smooth=True)
            W["Chrome"].append(lug)
        disc = B.cylinder("disc", 0.15, 0.025, (sx * 0.695, yy, 0.30),
                          (0, math.pi / 2, 0), segments=14, color="#6b6659",
                          material=chrome, smooth=True)
        W["Under"].append(disc)
        # fender-lip chrome eyebrow
        pts = []
        for i in range(9):
            a = math.pi * 0.12 + math.pi * 0.76 * i / 8
            pts.append((sx * 0.858, yy + 0.40 * math.cos(a), 0.30 + 0.40 * math.sin(a)))
        W["Chrome"].append(B.tube("warch", pts, 0.012, "#8e8878", chrome, segments=4))
        objs = []
        for key, lst in W.items():
            if lst:
                objs.append(B.join_group(f"{label}_{key}", lst))
        final = B.join_group(f"Wheel_{label}", objs)
        wheel_objs.append(final)
        return final

    make_wheel(-1, 1.32, "FL")
    make_wheel(1, 1.32, "FR")
    make_wheel(-1, -1.32, "RL")
    make_wheel(1, -1.32, "RR")

    # ------------------------------------------------ join body by material
    body_objs = []
    for key, lst in G.items():
        if lst:
            body_objs.append(B.join_group("Car_" + key, lst))
    root = B.empty("Car", (0, 0, 0))
    for ob in body_objs + wheel_objs:
        ob.parent = root
        ob.matrix_parent_inverse = root.matrix_world.inverted()
    # report
    tris = 0
    mn = [9, 9, 9]
    mx = [-9, -9, -9]
    for ob in bpy.context.scene.objects:
        if ob.type == "MESH":
            me = ob.data
            me.calc_loop_triangles()
            tris += len(me.loop_triangles)
            for v in me.vertices:
                w = ob.matrix_world @ v.co
                for i in range(3):
                    mn[i] = min(mn[i], w[i])
                    mx[i] = max(mx[i], w[i])
    print("CAR STATS tris=%d objs=%d bbox=%s..%s" % (tris, len(bpy.context.scene.objects),
                                                    [round(v, 3) for v in mn],
                                                    [round(v, 3) for v in mx]))
    B.save_blend(os.path.join(B.ROOT, "assets", "vehicles", "car.blend"))
    B.export_glb(os.path.join(B.ROOT, "assets", "vehicles", "car.glb"),
                 objects=[root] + body_objs + wheel_objs)
    print("CAR EXPORTED", os.path.getsize(os.path.join(B.ROOT, "assets", "vehicles", "car.glb")))


