def build_car():
    B.reset(1996)
    paint = B.vmat("CarPaint", 0.34, 0.28)
    chrome = B.vmat("CarChrome", 0.13, 0.95)
    rubber = B.vmat("CarRubber", 0.92)
    glassm = B.mat("CarGlass", "#25393d", rough=0.06, metal=0.25, alpha=0.45)
    trim = B.mat("CarTrim", "#211f1b", rough=0.62)
    interior = B.vmat("CarInterior", 0.88)
    lensw = B.mat("CarLampW", "#efe5c8", rough=0.18, emission="#ffe9bd", emis_strength=0.55)
    lensr = B.mat("CarLampR", "#8f1f1a", rough=0.22, emission="#ff3a2a", emis_strength=0.85)
    plate_m = B.mat("CarPlate", "#ded8c5", rough=0.75)
    wine = "#6b2831"
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

    # ------------------------------------------------ lower body
    stations = [
        (-2.06, 0.710, 0.400, 0.830),
        (-1.99, 0.790, 0.350, 0.870),
        (-1.74, 0.842, 0.300, 0.905),
        (-1.20, 0.850, 0.285, 0.920),
        (0.00, 0.850, 0.285, 0.925),
        (1.00, 0.850, 0.285, 0.925),
        (1.66, 0.838, 0.305, 0.905),
        (1.94, 0.790, 0.340, 0.875),
        (2.06, 0.700, 0.400, 0.830),
    ]
    secs = []
    for (yy, ww, z0, z1) in stations:
        pts = [(-ww * 0.86, z0), (ww * 0.86, z0), (ww, z0 + 0.19), (ww, z1 - 0.07),
               (ww * 0.955, z1), (-ww * 0.955, z1), (-ww, z1 - 0.07), (-ww, z0 + 0.19)]
        secs.append(((0, yy, 0), [(a, b) for a, b in pts]))
    G["Paint"].append(B.loft("lowerbody", secs, color=wine, material=paint, smooth=False))

    # hood, trunk, cowl and shut lines
    bx("Paint", (1.34, 1.14, 0.032), (0, 1.47, 0.932), wine, paint, bevel=0.015)
    bx("Paint", (0.028, 1.06, 0.012), (-0.33, 1.47, 0.949), wine, paint)
    bx("Paint", (0.028, 1.06, 0.012), (0.33, 1.47, 0.949), wine, paint)
    bx("Paint", (1.30, 0.64, 0.03), (0, -1.73, 0.918), wine, paint, bevel=0.015)
    bx("Trim", (1.46, 0.014, 0.009), (0, 1.07, 0.935), blk, trim)
    bx("Trim", (1.36, 0.014, 0.009), (0, -1.64, 0.924), blk, trim)
    bx("Trim", (0.012, 0.92, 0.009), (-0.64, 1.47, 0.936), blk, trim)
    bx("Trim", (0.012, 0.92, 0.009), (0.64, 1.47, 0.936), blk, trim)
    bx("Trim", (1.22, 0.17, 0.028), (0, 0.94, 0.944), blk, trim)
    for k in range(9):
        bx("Trim", (0.09, 0.012, 0.03), (-0.5 + k * 0.125, 0.93, 0.952), "#4a453a", trim)
    for sx in (-1, 1):
        bx("Trim", (0.52, 0.017, 0.014), (sx * 0.28, 1.02, 0.955), blk, trim,
           rot=(0, 0, sx * 0.2))
        bx("Trim", (0.02, 0.1, 0.006), (sx * 0.52, 1.0, 0.958), blk, trim)
    # rocker, side mouldings
    for sx in (-1, 1):
        bx("Trim", (0.014, 2.7, 0.11), (sx * 0.842, 0, 0.335), blk, trim)
        bx("Chrome", (0.016, 2.35, 0.03), (sx * 0.850, 0, 0.60), "#bdb6a2", chrome)
        bx("Trim", (0.018, 2.30, 0.014), (sx * 0.853, 0, 0.58), blk, trim)


    cy("Chrome", 0.055, 0.018, (0.848, -1.50, 0.75), "#b9b2a0", chrome,
       rot=(0, math.pi / 2, 0), seg=10)

    # ------------------------------------------------ greenhouse
    cab = [
        (-1.46, 0.760, 0.945),
        (-1.34, 0.770, 1.065),
        (-1.04, 0.746, 1.365),
        (-0.80, 0.726, 1.452),
        (-0.05, 0.720, 1.462),
        (0.30, 0.722, 1.462),
        (0.56, 0.734, 1.430),
        (0.80, 0.756, 1.150),
        (0.94, 0.775, 0.960),
    ]
    csecs = []
    for (yy, ww, ztop) in cab:
        pts = [(-ww, 0.90), (ww, 0.90), (ww, ztop - 0.055), (ww * 0.86, ztop),
               (-ww * 0.86, ztop), (-ww, ztop - 0.055)]
        csecs.append(((0, yy, 0), [(a, b) for a, b in pts]))
    G["Paint"].append(B.loft("cabin", csecs, color=wine, material=paint, smooth=False))
    # vinyl roof panel
    quad("Paint", [(-0.60, -0.82, 1.4645), (0.60, -0.82, 1.4645),
                   (0.60, 0.30, 1.4645), (-0.60, 0.30, 1.4645)], cream, paint, "roofvinyl")
    bx("Chrome", (0.018, 1.16, 0.018), (-0.605, -0.26, 1.462), "#c9c2ae", chrome)
    bx("Chrome", (0.018, 1.16, 0.018), (0.605, -0.26, 1.462), "#c9c2ae", chrome)
    bx("Chrome", (1.22, 0.02, 0.018), (0, 0.31, 1.462), "#c9c2ae", chrome)
    bx("Chrome", (1.22, 0.02, 0.018), (0, -0.83, 1.462), "#c9c2ae", chrome)
    # drip rails
    for sx in (-1, 1):
        bx("Chrome", (0.014, 1.5, 0.014), (sx * 0.665, -0.28, 1.448), "#a9a28f", chrome)

    # ------------------------------------------------ glazing
    ws = [(-0.625, 0.905, 1.005), (0.625, 0.905, 1.005),
          (0.530, 0.365, 1.435), (-0.530, 0.365, 1.435)]
    ws = [(x, y + 0.012, z + 0.008) for (x, y, z) in ws]
    quad("Glass", ws, "#a9c1bd", glassm, "windshield")
    for i in range(4):
        beam("Chrome", ws[i], ws[(i + 1) % 4], 0.024, "#bcb5a2", chrome, "ws_trim")
    for sx in (-1, 1):
        beam("Trim", (sx * 0.64, 0.910, 1.0), (sx * 0.535, 0.36, 1.435), 0.030, blk, trim)
    rw = [(-0.580, -1.415, 1.020), (0.580, -1.415, 1.020),
          (0.500, -0.900, 1.400), (-0.500, -0.900, 1.400)]
    rw = [(x, y - 0.012, z + 0.008) for (x, y, z) in rw]
    quad("Glass", rw, "#9fb4b1", glassm, "rearglass")
    for i in range(4):
        beam("Chrome", rw[i], rw[(i + 1) % 4], 0.022, "#bcb5a2", chrome, "rw_trim")
    for sx in (-1, 1):
        bx("Trim", (0.02, 0.5, 0.5), (sx * 0.735, -1.28, 1.24), blk, trim)
    # side windows, both sides
    for sx in (-1, 1):
        xb = sx * 0.742
        xt = sx * 0.700
        wins = [
            [(xb, 0.880, 1.008), (xb, -0.020, 1.008), (xt, 0.025, 1.432),
             (xt, 0.380, 1.432)],
            [(xb, -0.075, 1.008), (xb, -0.820, 1.008), (xt, -0.765, 1.432),
             (xt, -0.030, 1.432)],
            [(xb, -0.875, 1.012), (xb, -1.090, 1.018), (xt, -1.145, 1.315),
             (xt, -0.830, 1.422)],
        ]
        for j, corners in enumerate(wins):
            quad("Glass", corners, "#a3b8b4", glassm, f"sideglass{sx}{j}")
            for i in range(4):
                beam("Chrome", corners[i], corners[(i + 1) % 4], 0.016, "#b9b2a0", chrome,
                     "sw_trim")
        bx("Trim", (0.018, 0.075, 0.43), (sx * 0.735, -0.055, 1.20), blk, trim)
        beam("Trim", (sx * 0.742, 0.890, 1.005), (sx * 0.700, 0.385, 1.430), 0.026, blk, trim)
        beam("Trim", (sx * 0.742, -0.865, 1.010), (sx * 0.700, -1.150, 1.315), 0.028, blk, trim)
        bx("Chrome", (0.018, 2.64, 0.024), (sx * 0.768, -0.22, 0.955), "#c6bfab", chrome)

    # ------------------------------------------------ doors
    for sx in (-1, 1):
        for yy in (0.0, -0.90):
            bx("Trim", (0.012, 0.014, 0.56), (sx * 0.853, yy, 0.615), blk, trim)
        for yy in (0.10, -0.78):
            bx("Chrome", (0.035, 0.17, 0.045), (sx * 0.858, yy, 0.835), "#c2bba7", chrome,
               bevel=0.006)
            bx("Trim", (0.02, 0.19, 0.017), (sx * 0.862, yy, 0.812), blk, trim)
        cy("Chrome", 0.017, 0.018, (sx * 0.858, 0.06, 0.885), "#cfc8b4", chrome,
           rot=(0, math.pi / 2, 0), seg=8)
        bx("LightW", (0.017, 0.1, 0.045), (sx * 0.856, 1.5, 0.68), "#e0b25e", lensw)
        # hinges hinted inside door shut
        for yy in (0.0, -0.90):
            bx("Trim", (0.008, 0.05, 0.06), (sx * 0.852, yy, 0.5), "#3a362e", trim)

    # ------------------------------------------------ front end
    bx("Paint", (1.72, 0.16, 0.20), (0, 2.10, 0.50), wine, paint, bevel=0.02)
    bx("Chrome", (1.74, 0.1, 0.055), (0, 2.14, 0.59), "#c8c1ad", chrome)
    bx("Trim", (1.64, 0.02, 0.035), (0, 2.195, 0.49), blk, trim)
    for sx in (-1, 1):
        bx("Paint", (0.14, 0.34, 0.2), (sx * 0.83, 1.96, 0.50), wine, paint,
           bevel=0.02, rot=(0, 0, sx * 0.28))
        bx("Chrome", (0.055, 0.055, 0.21), (sx * 0.44, 2.185, 0.53), "#c8c1ad", chrome,
           bevel=0.01)
        bx("LightW", (0.17, 0.018, 0.055), (sx * 0.6, 2.195, 0.6), "#d99a4a", lensw)
    # grille
    bx("Trim", (1.06, 0.05, 0.25), (0, 2.075, 0.735), blk, trim)
    for k in range(6):
        bx("Chrome", (0.98, 0.018, 0.018), (0, 2.105, 0.635 + k * 0.043), "#b8b19d", chrome)
    for k in range(9):
        bx("Chrome", (0.014, 0.016, 0.22), (-0.44 + k * 0.11, 2.107, 0.735), "#8f8a7a", chrome)
    bx("Chrome", (1.0, 0.03, 0.022), (0, 2.106, 0.855), "#c6bfab", chrome)
    for sx in (-1, 1):
        bx("Chrome", (0.032, 0.032, 0.21), (sx * 0.515, 2.106, 0.735), "#c6bfab", chrome)
    cy("Chrome", 0.048, 0.02, (0, 2.109, 0.735), "#cfc8b4", chrome,
       rot=(math.pi / 2, 0, 0), seg=14)
    cy("Paint", 0.03, 0.022, (0, 2.112, 0.735), wine, paint,
       rot=(math.pi / 2, 0, 0), seg=12)
    # headlights
    for sx in (-1, 1):
        bx("Chrome", (0.36, 0.03, 0.2), (sx * 0.61, 2.075, 0.815), "#c6bfab", chrome,
           bevel=0.008)
        bx("LightW", (0.30, 0.022, 0.15), (sx * 0.61, 2.09, 0.815), "#f0e8cc", lensw)
        bx("Chrome", (0.30, 0.026, 0.012), (sx * 0.61, 2.095, 0.815), "#9f9a89", chrome)
        cy("LightW", 0.045, 0.02, (sx * 0.69, 2.095, 0.815), "#e7ddc0", lensw,
           rot=(math.pi / 2, 0, 0), seg=10)
    # front plate
    bx("Trim", (0.52, 0.03, 0.18), (0, 2.207, 0.72), blk, trim)
    bx("Plate", (0.46, 0.012, 0.14), (0, 2.222, 0.72), "#e2dcc8", plate_m)
    for sx in (-0.17, 0.17):
        cy("Trim", 0.011, 0.008, (sx, 2.23, 0.72), blk, trim,
           rot=(math.pi / 2, 0, 0), seg=6)
    bx("Trim", (1.2, 0.06, 0.09), (0, 2.10, 0.335), blk, trim)
    # hood hinges / jets
    for sx in (-1, 1):
        bx("Trim", (0.09, 0.05, 0.012), (sx * 0.45, 1.08, 0.947), "#3a362e", trim)
        cy("Chrome", 0.012, 0.03, (sx * 0.4, 0.95, 0.955), "#9a9585", chrome,
           rot=(math.pi / 2, 0, 0), seg=6)

    # ------------------------------------------------ rear end
    bx("Paint", (1.71, 0.16, 0.20), (0, -2.10, 0.50), wine, paint, bevel=0.02)
    bx("Chrome", (1.74, 0.1, 0.055), (0, -2.14, 0.59), "#c8c1ad", chrome)
    bx("Trim", (1.63, 0.02, 0.035), (0, -2.195, 0.49), blk, trim)
    for sx in (-1, 1):
        bx("Paint", (0.14, 0.34, 0.2), (sx * 0.83, -1.96, 0.50), wine, paint,
           bevel=0.02, rot=(0, 0, -sx * 0.28))
        bx("Chrome", (0.46, 0.03, 0.19), (sx * 0.56, -2.075, 0.80), "#c6bfab", chrome,
           bevel=0.008)
        bx("LightR", (0.4, 0.024, 0.14), (sx * 0.56, -2.09, 0.80), "#b02a1f", lensr)
        bx("LightW", (0.11, 0.026, 0.14), (sx * 0.73, -2.09, 0.80), "#e6dcc0", lensw)
        for k in range(3):
            bx("Trim", (0.34, 0.025, 0.011), (sx * 0.56, -2.094, 0.748 + k * 0.034), blk, trim)
    bx("Chrome", (1.3, 0.022, 0.025), (0, -2.085, 0.9), "#c0b9a5", chrome)
    bx("Trim", (0.52, 0.03, 0.18), (0, -2.207, 0.72), blk, trim)
    bx("Plate", (0.46, 0.012, 0.14), (0, -2.222, 0.72), "#e2dcc8", plate_m)
    for sx in (-0.17, 0.17):
        cy("Trim", 0.011, 0.008, (sx, -2.23, 0.72), blk, trim,
           rot=(math.pi / 2, 0, 0), seg=6)
    cy("Chrome", 0.016, 0.02, (0, -2.085, 0.74), "#cfc8b4", chrome,
       rot=(math.pi / 2, 0, 0), seg=6)
    cy("Chrome", 0.06, 0.018, (0, -2.083, 0.885), "#cfc8b4", chrome,
       rot=(math.pi / 2, 0, 0), seg=10)
    # license lamps
    for sx in (-1, 1):
        bx("LightW", (0.08, 0.02, 0.03), (sx * 0.2, -2.195, 0.8), "#e6dcc0", lensw)
    # exhaust
    cy("Under", 0.035, 0.55, (-0.38, -1.95, 0.24), "#6b6659", rubber,
       rot=(math.pi / 2, 0, 0), seg=8)
    cy("Chrome", 0.045, 0.13, (-0.38, -2.21, 0.24), "#9c9585", chrome,
       rot=(math.pi / 2, 0, 0), seg=8)
    # rear valance + mud flaps
    bx("Trim", (1.3, 0.08, 0.12), (0, -2.09, 0.33), blk, trim)
    for sx in (-1, 1):
        bx("Trim", (0.24, 0.02, 0.26), (sx * 0.79, -1.75, 0.20), blk, trim)

    # mirrors, antenna
    for sx in (-1, 1):
        beam("Trim", (sx * 0.79, 0.86, 1.005), (sx * 0.885, 0.80, 1.03), 0.035, blk, trim)
        bx("Chrome", (0.05, 0.15, 0.1), (sx * 0.9, 0.79, 1.04), "#c2bba7", chrome,
           bevel=0.012)
        bx("Glass", (0.02, 0.12, 0.075), (sx * 0.888, 0.725, 1.04), "#899d9a", glassm)
    cy("Chrome", 0.018, 0.07, (0.66, 1.30, 0.945), "#8e897a", chrome, seg=8)
    beam("Trim", (0.66, 1.30, 0.95), (0.68, 1.09, 1.49), 0.009, "#4a463c", chrome)

    # ------------------------------------------------ interior
    bx("Trim", (1.48, 3.1, 0.03), (0, 0.05, 0.35), "#4a4238", trim)
    bx("Interior", (1.42, 0.4, 0.24), (0, 0.60, 0.84), "#5b4c3c", interior, bevel=0.02)
    bx("Interior", (0.55, 0.2, 0.12), (-0.32, 0.47, 0.945), "#4e4033", interior,
       bevel=0.015)
    for sx in (-0.47, -0.32, -0.17):
        cy("Trim", 0.032, 0.012, (sx, 0.39, 0.951), "#2e2c26", trim,
           rot=(math.pi / 2, 0, 0), seg=8)
    bx("Trim", (0.34, 0.06, 0.1), (0.25, 0.58, 0.87), "#38342c", trim)
    for k in range(3):
        bx("Trim", (0.05, 0.012, 0.03), (0.16 + k * 0.08, 0.548, 0.87), "#80796a", trim)
    # seats with piping + headrests
    for sx in (-1, 1):
        cx = sx * 0.37
        bx("Interior", (0.5, 0.56, 0.15), (cx, 0.02, 0.585), tan, interior, bevel=0.03)
        bx("Interior", (0.48, 0.16, 0.56), (cx, -0.17, 0.86), tan, interior,
           bevel=0.03, rot=(-0.13, 0, 0))
        bx("Interior", (0.27, 0.13, 0.22), (cx, -0.22, 1.25), tan, interior,
           bevel=0.025)
        bx("Interior", (0.05, 0.4, 0.2), (cx + sx * 0.26, -0.06, 0.72), "#8f7a5b", interior)
        beam("Interior", (cx - 0.2, 0.28, 0.64), (cx + 0.2, 0.28, 0.64), 0.012, "#7e6a4e",
             interior)
        beam("Interior", (cx, -0.1, 0.62), (cx, -0.3, 1.12), 0.012, "#8c7859", interior)
    # rear bench, parcel shelf, speakers
    bx("Interior", (1.3, 0.55, 0.15), (0, -1.0, 0.58), tan, interior, bevel=0.03)
    bx("Interior", (1.3, 0.15, 0.5), (0, -1.24, 0.85), tan, interior, bevel=0.03,
       rot=(-0.12, 0, 0))
    for sx in (-0.38, 0.38):
        bx("Interior", (0.3, 0.12, 0.2), (sx, -1.32, 1.18), tan, interior, bevel=0.02)
    bx("Interior", (1.28, 0.4, 0.04), (0, -1.62, 0.9), "#4a4034", trim)
    for sx in (-0.4, 0.4):
        cy("Trim", 0.08, 0.015, (sx, -1.63, 0.925), "#33312a", trim,
           rot=(math.pi / 2, 0, 0), seg=10)
    # console, gear lever, handbrake
    bx("Interior", (0.22, 0.55, 0.22), (0, 0.18, 0.52), "#4c4034", interior, bevel=0.02)
    beam("Trim", (0.0, 0.23, 0.55), (0.02, 0.28, 0.73), 0.02, "#2f2b24", trim)
    G["Trim"].append(B.sphere("gearknob", 0.045, (0.02, 0.28, 0.75), color="#2f2b24",
                              material=trim, segments=8, rings=5))
    beam("Trim", (0.18, 0.35, 0.52), (0.2, 0.05, 0.64), 0.022, "#2f2b24", trim)
    for sx in (-1, 1):
        bx("Interior", (0.02, 2.0, 0.5), (sx * 0.79, 0.0, 0.62), tan, interior)
        bx("Interior", (0.12, 0.46, 0.1), (sx * 0.73, 0.2, 0.67), "#8d7759", interior)
        bx("Chrome", (0.03, 0.12, 0.03), (sx * 0.765, 0.2, 0.76), "#bdb6a2", chrome)
        bx("Interior", (1.12, 0.02, 0.02), (sx * 0.3, -0.02, 1.39), "#9c8768", interior)
    # steering wheel
    steer = []
    for i in range(21):
        a = math.tau * i / 20
        steer.append((-0.34 + 0.17 * math.cos(a), 0.35 + 0.05 * math.sin(a),
                      0.94 + 0.155 * math.sin(a)))
    G["Trim"].append(B.tube("steerwheel", steer, 0.018, "#2f2b24", trim, segments=5,
                            cyclic=True))
    beam("Trim", (-0.34, 0.33, 0.94), (-0.34, 0.42, 0.80), 0.028, "#3a352c", trim)
    for a in (0.2, 2.3, 4.4):
        beam("Trim", (-0.34, 0.40, 0.94),
             (-0.34 + 0.16 * math.cos(a), 0.40, 0.94 + 0.14 * math.sin(a)), 0.012,
             "#413b30", trim)
    # rear view mirror, visors, dome light, headliner
    bx("Trim", (0.24, 0.04, 0.08), (0, 0.52, 1.34), "#2d2a24", trim)
    bx("Glass", (0.2, 0.02, 0.06), (0, 0.505, 1.34), "#8fa4a1", glassm)
    for sx in (-1, 1):
        bx("Interior", (0.36, 0.2, 0.025), (sx * 0.34, 0.45, 1.42), "#9c8768", interior)
    cy("LightW", 0.04, 0.02, (0, -0.35, 1.43), "#f0e3bc", lensw,
       rot=(math.pi / 2, 0, 0), seg=8)
    bx("Interior", (1.16, 1.7, 0.02), (0, -0.35, 1.40), "#c3b493", interior)
    # pedals
    for sx, yy in ((-0.48, 0.82), (-0.3, 0.83), (-0.12, 0.85)):
        bx("Trim", (0.08, 0.1, 0.02), (sx, yy, 0.46), "#33302a", trim, rot=(0.5, 0, 0))

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
            beam("Under", (sx * 0.62, yy, 0.3), (sx * 0.8, yy - 0.35, 0.45), 0.032,
                 "#5a5549", rubber)
    # driveshaft
    cy("Under", 0.03, 1.4, (0, 0.3, 0.22), "#5b564a", rubber,
       rot=(math.pi / 2, 0, 0), seg=6)

    # ------------------------------------------------ wheel arches
    def arch(sx, yc, r_in, r_out, color, mx, xoff, n=14, name="arch", g="Paint"):
        verts, faces = [], []
        for i in range(n + 1):
            a = math.pi * i / n
            verts.append((sx * xoff, yc + r_out * math.cos(a), 0.30 + r_out * math.sin(a)))
            verts.append((sx * xoff, yc + r_in * math.cos(a), 0.30 + r_in * math.sin(a)))
        for i in range(n):
            a = i * 2
            faces.append((a, a + 1, a + 3, a + 2))
        G[g].append(B._finish(name, verts, faces, color, mx, smooth=False))

    for sx in (-1, 1):
        for yy in (-1.32, 1.32):
            # dark well behind the tyre
            verts, faces = [], []
            verts.append((sx * 0.848, yy, 0.30))
            for i in range(15):
                a = math.pi * i / 14
                verts.append((sx * 0.848, yy + 0.345 * math.cos(a),
                              0.30 + 0.345 * math.sin(a)))
            for i in range(14):
                faces.append((0, i + 1, i + 2))
            G["Trim"].append(B._finish("well", verts, faces, "#1f1d1a", trim,
                                       smooth=False))
            arch(sx, yy, 0.348, 0.395, wine, paint, 0.855, n=16, name="archlip")
            arch(sx, yy, 0.395, 0.402, "#3a3630", trim, 0.856, n=16, name="archseam", g="Trim")

    # ------------------------------------------------ wheels
    wheel_objs = []

    def make_wheel(sx, yy, label):
        W = []
        tire = B.lathe("tire",
                       [(0.175, -0.100), (0.240, -0.112), (0.285, -0.090),
                        (0.300, -0.040), (0.303, 0.000), (0.300, 0.040),
                        (0.285, 0.090), (0.240, 0.112), (0.175, 0.100)],
                       loc=(sx * 0.735, yy, 0.303), rot=(0, math.pi / 2, 0),
                       segments=28, color="#33312c", material=rubber, smooth=True)
        W.append(tire)
        # tread blocks
        for k in range(36):
            a = math.tau * k / 36
            W.append(B.box(f"tread{k}", (0.20, 0.016, 0.055),
                           (sx * 0.735, yy + 0.296 * math.cos(a), 0.303 + 0.296 * math.sin(a)),
                           (a, 0, 0), color="#2c2a26", material=rubber))
        rim = B.cylinder("rim", 0.188, 0.15, (sx * 0.735, yy, 0.303), (0, math.pi / 2, 0),
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
                            material=chrome, smooth=True))
        # top mud shield inside the arch
        guard = []
        for i in range(7):
            a = math.pi * i / 6
            guard.append((sx * 0.80, yy + 0.33 * math.cos(a), 0.303 + 0.33 * math.sin(a)))
        W.append(B.tube("wheelguard", guard, 0.02, "#2b2924", rubber, segments=4))
        final = B.join_group(f"Wheel_{label}", W)
        wheel_objs.append(final)

    make_wheel(-1, 1.32, "FL")
    make_wheel(1, 1.32, "FR")
    make_wheel(-1, -1.32, "RL")
    make_wheel(1, -1.32, "RR")

    # ------------------------------------------------ join/export
    body_objs = []
    for key, lst in G.items():
        if lst:
            body_objs.append(B.join_group("Car_" + key, lst))
    root = B.empty("Car", (0, 0, 0))
    for ob in body_objs + wheel_objs:
        ob.parent = root
        ob.matrix_parent_inverse = root.matrix_world.inverted()
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


