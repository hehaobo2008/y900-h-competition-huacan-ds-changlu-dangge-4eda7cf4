"""Blender procedural modeling library for 《山河织路》.
All geometry, colors and procedural details are generated from this project's code.
Blender 4.2, Z-up, meters. Exports Y-up glTF.
"""
from __future__ import annotations

import bpy
import bmesh
import json
import math
import os
import random
from mathutils import Euler, Matrix, Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")

# ---------------------------------------------------------------- scene / color

def reset(seed=1):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.render.engine = "BLENDER_EEVEE_NEXT"
    random.seed(seed)


def srgb(hexstr: str):
    h = hexstr.lstrip("#")
    vals = [int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4)]
    def lin(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return tuple(lin(c) for c in vals)


def mix(a, b, t):
    return tuple(a[i] * (1 - t) + b[i] * t for i in range(3))


def vary(c, amount):
    return tuple(max(0.0, min(1.0, v * (1.0 + random.uniform(-amount, amount)))) for v in c)


# ---------------------------------------------------------------- materials

_MATS = {}


def mat(name, color="#cccccc", rough=0.82, metal=0.0, emission=None,
        emis_strength=0.0, alpha=1.0, texture=None, use_vcol=False,
        double_sided=True, uv_scale=1.0):
    key = (name, color, rough, metal, emission, emis_strength, alpha,
           texture, use_vcol, double_sided, uv_scale)
    if key in _MATS and _MATS[key].name in bpy.data.materials:
        return _MATS[key]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.use_backface_culling = not double_sided
    nt = m.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    bsdf.inputs["Base Color"].default_value = (*srgb(color), 1.0)
    bsdf.inputs["Alpha"].default_value = alpha
    if use_vcol:
        attr = nt.nodes.new("ShaderNodeVertexColor")
        attr.layer_name = "Col"
        attr.location = (-420, 200)
        nt.links.new(attr.outputs["Color"], bsdf.inputs["Base Color"])
    if texture:
        img = bpy.data.images.load(texture, check_existing=True)
        img.colorspace_settings.name = "sRGB"
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = img
        tex.interpolation = "Linear"
        tex.location = (-520, 340)
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        if emis_strength > 0:
            nt.links.new(tex.outputs["Color"], bsdf.inputs["Emission Color"])
            bsdf.inputs["Emission Strength"].default_value = emis_strength
    elif emission:
        bsdf.inputs["Emission Color"].default_value = (*srgb(emission), 1.0)
        bsdf.inputs["Emission Strength"].default_value = emis_strength
    if alpha < 1.0:
        m.surface_render_method = "DITHERED"
    _MATS[key] = m
    return m


def vmat(name="Matte", rough=0.86, metal=0.0):
    return mat(name, "#ffffff", rough=rough, metal=metal, use_vcol=True)


# ---------------------------------------------------------------- mesh helpers

def _col(c):
    if c is None:
        return None
    if isinstance(c, str):
        return srgb(c)
    return c


def _finalize(name, me, color, material, smooth=False, face_colors=None):
    color = _col(color)
    if face_colors is not None:
        face_colors = [_col(c) for c in face_colors]
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    if material:
        me.materials.append(material)
    ca = me.color_attributes.new("Col", "FLOAT_COLOR", "CORNER")
    for poly in me.polygons:
        c = face_colors[poly.index] if face_colors is not None else color
        if c is None:
            c = (1, 1, 1)
        for li in poly.loop_indices:
            ca.data[li].color = (*c, 1.0)
    for p in me.polygons:
        p.use_smooth = smooth
    return ob


def _finish(name, verts, faces, color, material, smooth=False, face_colors=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    return _finalize(name, me, color, material, smooth, face_colors)


def box(name, size=(1, 1, 1), loc=(0, 0, 0), rot=(0, 0, 0), color="#ffffff",
        material=None, bevel=0.0, smooth=False, face_colors=None):
    sx, sy, sz = (s * 0.5 for s in size)
    verts = [(-sx, -sy, -sz), (sx, -sy, -sz), (sx, sy, -sz), (-sx, sy, -sz),
             (-sx, -sy, sz), (sx, -sy, sz), (sx, sy, sz), (-sx, sy, sz)]
    faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
             (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    if bevel > 0:
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=bevel, segments=1,
                        affect="EDGES", clamp_overlap=True)
        bm.to_mesh(me)
        bm.free()
        me.update()
    ob = _finalize(name, me, color, material, smooth=smooth, face_colors=face_colors)
    ob.matrix_world = Matrix.Translation(loc) @ Euler(rot, "XYZ").to_matrix().to_4x4()
    return ob


def beam(name, p1, p2, width=0.1, height=0.1, color="#ffffff", material=None, bevel=0.0):
    p1, p2 = Vector(p1), Vector(p2)
    d = p2 - p1
    length = d.length
    if length < 1e-6:
        return None
    rot = d.to_track_quat("Z", "Y").to_euler()
    ob = box(name, (width, height, length), (p1 + p2) * 0.5, rot,
             color=color, material=material, bevel=bevel)
    return ob


def cylinder(name, radius=0.5, depth=1.0, loc=(0, 0, 0), rot=(0, 0, 0),
             segments=16, color="#ffffff", material=None, cap=True, smooth=True,
             radius2=None, bevel=0.0):
    r2 = radius if radius2 is None else radius2
    verts, faces = [], []
    for i in range(segments):
        a = 2 * math.pi * i / segments
        verts.append((radius * math.cos(a), radius * math.sin(a), -depth / 2))
    for i in range(segments):
        a = 2 * math.pi * i / segments
        verts.append((r2 * math.cos(a), r2 * math.sin(a), depth / 2))
    for i in range(segments):
        j = (i + 1) % segments
        faces.append((i, j, segments + j, segments + i))
    if cap:
        faces.append(tuple(range(segments - 1, -1, -1)))
        faces.append(tuple(range(segments, segments * 2)))
    n_side = len(faces) - (2 if cap else 0)
    fc = None
    if smooth:
        fc = None
    ob = _finish(name, verts, faces, color, material, smooth=False, face_colors=fc)
    for i, p in enumerate(ob.data.polygons):
        p.use_smooth = smooth and i < n_side
    ob.matrix_world = Matrix.Translation(loc) @ Euler(rot, "XYZ").to_matrix().to_4x4()
    if bevel > 0:
        m = ob.modifiers.new("bev", "BEVEL")
        m.width = bevel
        m.segments = 2
        bpy.context.view_layer.objects.active = ob
        bpy.ops.object.modifier_apply(modifier=m.name)
    return ob


def lathe(name, profile, loc=(0, 0, 0), rot=(0, 0, 0), segments=24,
          color="#ffffff", material=None, smooth=True):
    """profile: [(radius, z), ...] bottom to top."""
    verts, faces = [], []
    rings = []
    for (r, z) in profile:
        ring = []
        for i in range(segments):
            a = 2 * math.pi * i / segments
            ring.append(len(verts))
            verts.append((r * math.cos(a), r * math.sin(a), z))
        rings.append(ring)
    for k in range(len(rings) - 1):
        a, b = rings[k], rings[k + 1]
        for i in range(segments):
            j = (i + 1) % segments
            faces.append((a[i], a[j], b[j], b[i]))
    faces.append(tuple(reversed(rings[0])))
    faces.append(tuple(rings[-1]))
    ob = _finish(name, verts, faces, color, material, smooth=smooth)
    nside = segments * (len(rings) - 1)
    for i, p in enumerate(ob.data.polygons):
        p.use_smooth = smooth and i < nside
    ob.matrix_world = Matrix.Translation(loc) @ Euler(rot, "XYZ").to_matrix().to_4x4()
    return ob


def loft(name, sections, loc=(0, 0, 0), rot=(0, 0, 0), color="#ffffff",
         material=None, smooth=True, closed=True):
    """sections: list of (offset_vector, [(a,b), ...]) loops, same length."""
    verts, faces = [], []
    rings = []
    n = len(sections[0][1])
    for off, pts in sections:
        ring = []
        for (a, b) in pts:
            ring.append(len(verts))
            verts.append((off[0] + a, off[1], off[2] + b))
        rings.append(ring)
    for k in range(len(rings) - 1):
        A, B = rings[k], rings[k + 1]
        for i in range(n if closed else n - 1):
            j = (i + 1) % n
            faces.append((A[i], A[j], B[j], B[i]))
    faces.append(tuple(reversed(rings[0])))
    faces.append(tuple(rings[-1]))
    ob = _finish(name, verts, faces, color, material, smooth=smooth)
    for i, p in enumerate(ob.data.polygons):
        p.use_smooth = smooth
    ob.matrix_world = Matrix.Translation(loc) @ Euler(rot, "XYZ").to_matrix().to_4x4()
    return ob


def tube(name, points, radius=0.03, color="#ffffff", material=None,
         segments=6, cyclic=False):
    cu = bpy.data.curves.new(name + "_c", "CURVE")
    cu.dimensions = "3D"
    cu.resolution_u = 1
    cu.bevel_depth = radius
    cu.bevel_resolution = 0
    sp = cu.splines.new("POLY")
    sp.points.add(len(points) - 1)
    for p, pt in zip(sp.points, points):
        p.co = (*pt, 1.0)
    sp.use_cyclic_u = cyclic
    ob = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(ob)
    cu.materials.append(material)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.convert(target="MESH")
    ob = bpy.context.active_object
    ob.name = name
    # vertex color attribute required for join consistency
    me = ob.data
    ca = me.color_attributes.get("Col")
    if ca is None:
        ca = me.color_attributes.new("Col", "FLOAT_COLOR", "CORNER")
    for li in range(len(ca.data)):
        ca.data[li].color = (*_col(color), 1.0)
    return ob


def sphere(name, radius=1.0, loc=(0, 0, 0), scale=(1, 1, 1), color="#ffffff",
           material=None, segments=12, rings=8, smooth=True):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=rings, radius=radius)
    bm.verts.ensure_lookup_table()
    bm.verts.index_update()
    verts = [tuple(v.co) for v in bm.verts]
    faces = [tuple(v.index for v in f.verts) for f in bm.faces]
    bm.free()
    ob = _finish(name, verts, faces, color, material, smooth=smooth)
    ob.matrix_world = Matrix.Translation(loc) @ Matrix.Diagonal((*scale, 1.0))
    return ob


def ellipse_plane(name, cx, cy, z, rx, ry, segments=28, color="#35606a", material=None):
    verts = [(cx, cy, z)]
    for i in range(segments):
        a = math.tau * i / segments
        verts.append((cx + rx * math.cos(a), cy + ry * math.sin(a), z))
    faces = [(0, i + 1, (i + 1) % segments + 1) for i in range(segments)]
    return _finish(name, verts, faces, color, material, smooth=False)


def ring_wall(name, cx, cy, z, rx, ry, width=0.5, height=0.4, segments=24,
              color="#6f6656", material=None):
    verts, faces = [], []
    for i in range(segments):
        a = math.tau * i / segments
        for (rr, zz) in ((1.0, 0.0), (1.0 + width / max(rx, ry), 0.0),
                         (1.0 + width / max(rx, ry), height), (1.0, height)):
            verts.append((cx + rx * rr * math.cos(a), cy + ry * rr * math.sin(a), z + zz))
    for i in range(segments):
        j = (i + 1) % segments
        for k in range(4):
            k2 = (k + 1) % 4
            faces.append((i * 4 + k, j * 4 + k, j * 4 + k2, i * 4 + k2))
    return _finish(name, verts, faces, color, material, smooth=False)


def join_group(name, objs):
    objs = [o for o in objs if o is not None and o.name in bpy.data.objects]
    if not objs:
        return None
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    if len(objs) > 1:
        bpy.ops.object.join()
    ob = bpy.context.active_object
    ob.name = name
    return ob


def export_glb(path, objects=None, extras=False):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    if objects:
        for o in objects:
            if o and o.name in bpy.data.objects:
                o.select_set(True)
    else:
        for o in bpy.context.scene.objects:
            o.select_set(True)
    bpy.ops.export_scene.gltf(
        filepath=path,
        export_format="GLB",
        use_selection=objects is not None,
        export_yup=True,
        export_apply=True,
        export_materials="EXPORT",
        export_vertex_color="MATERIAL",
        export_all_vertex_colors=False,
        export_image_format="AUTO",
        export_cameras=False,
        export_lights=False,
        export_extras=extras,
        export_texcoords=True,
        export_normals=True,
        export_tangents=False,
    )


def empty(name, loc=(0, 0, 0), rot=(0, 0, 0), size=1.0):
    e = bpy.data.objects.new(name, None)
    e.empty_display_size = size
    e.location = loc
    e.rotation_euler = Euler(rot, "XYZ")
    bpy.context.scene.collection.objects.link(e)
    return e


def ground_slab(name, size_x=320, size_y=300, depth=9, top=0.0,
                colors=("#6d5840", "#7d6347", "#8b7052", "#5b4a38", "#4a3d30"), cap=True):
    """Museum-style cut earth base; visible in the void overview."""
    sx, sy = size_x / 2, size_y / 2
    layers = [0.0, -0.8, -2.8, -5.6, -depth]
    verts, faces, face_colors = [], [], []
    # top
    verts += [(-sx, -sy, top), (sx, -sy, top), (sx, sy, top), (-sx, sy, top)]
    if cap:
        faces.append((0, 1, 2, 3)); face_colors.append(srgb("#8a8064"))
    for k, z in enumerate(layers[1:]):
        verts += [(-sx, -sy, z), (sx, -sy, z), (sx, sy, z), (-sx, sy, z)]
    # side bands
    for k in range(len(layers) - 1):
        a = k * 4
        b = (k + 1) * 4
        c = srgb(colors[min(k, len(colors) - 1)])
        for i in range(4):
            j = (i + 1) % 4
            faces.append((a + i, b + i, b + j, a + j))
            face_colors.append(vary(c, 0.06))
    faces.append((4 + 12 + 3, 4 + 12 + 2, 4 + 12 + 1, 4 + 12 + 0))
    face_colors.append(srgb(colors[-1]))
    ob = _finish(name, verts, faces, None, vmat(), smooth=False,
                 face_colors=face_colors)
    return ob


# ---------------------------------------------------------------- terrain / road

def terrain(name, size_x, size_y, nx, ny, height_fn, color_fn, material,
            z0=0.0, smooth=True, section=None):
    verts, faces, face_colors = [], [], []
    for iy in range(ny + 1):
        for ix in range(nx + 1):
            x = -size_x / 2 + size_x * ix / nx
            y = -size_y / 2 + size_y * iy / ny
            verts.append((x, y, z0 + height_fn(x, y)))
    for iy in range(ny):
        for ix in range(nx):
            a = iy * (nx + 1) + ix
            b = a + 1
            c = a + nx + 2
            d = a + nx + 1
            faces.append((a, b, c, d))
            cx = -size_x / 2 + size_x * (ix + 0.5) / nx
            cy = -size_y / 2 + size_y * (iy + 0.5) / ny
            cz = z0 + (height_fn(cx, cy) + 0.01)
            face_colors.append(_col(color_fn(cx, cy, cz)))
    if section:
        # Trace the exact terrain vertices. Duplicate the rim so its outward
        # normals never pull down the lighting on the hillside above it.
        rim = (list(range(nx)) +
               [j*(nx+1)+nx for j in range(ny)] +
               [ny*(nx+1)+nx-i for i in range(nx)] +
               [(ny-j)*(nx+1) for j in range(ny)])
        first = len(verts)
        colours = [srgb(c) for c in section]
        if len(colours) != 5:
            raise ValueError("The terrain cross-section needs five strata colours")
        for index in rim:
            x,y,h = verts[index]
            fold = .042*math.sin(x*.048+y*.037)+.026*math.sin(y*.128-x*.085)
            for f in (0.,.27+fold,.53+fold,.78+fold*.65,.94+fold*.18,1.):
                verts.append((x,y,min(z0,h)+(h-min(z0,h))*f))
        for i,index in enumerate(rim):
            a,b = first+6*i,first+6*((i+1)%len(rim))
            x,y,_ = verts[index]
            tone = .22+.15*math.sin(x*.067+y*.085)
            for j,colour in enumerate(colours):
                faces.append((a+j,b+j,b+j+1,a+j+1))
                face_colors.append(mix(colour,colours[min(j+1,len(colours)-1)],tone))
    ob = _finish(name, verts, faces, None, material, smooth=smooth, face_colors=face_colors)
    return ob


def road_ribbon(name, pts, width, color="#5b554c", material=None,
                z=0.02, crown=0.04, segments_width=3):
    """pts: [(x,y), ...] centerline; builds a strip with slight crown."""
    verts, faces, face_colors = [], [], []
    rows = []
    for idx, (x, y) in enumerate(pts):
        if idx == 0:
            dx, dy = pts[1][0] - x, pts[1][1] - y
        elif idx == len(pts) - 1:
            dx, dy = x - pts[-2][0], y - pts[-2][1]
        else:
            dx, dy = pts[idx + 1][0] - pts[idx - 1][0], pts[idx + 1][1] - pts[idx - 1][1]
        L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L, dx / L
        row = []
        for k in range(segments_width + 1):
            t = k / segments_width
            off = (t - 0.5) * width
            h = z + crown * (1 - abs(t - 0.5) * 2)
            row.append(len(verts))
            verts.append((x + nx * off, y + ny * off, h))
        rows.append(row)
    for i in range(len(rows) - 1):
        for k in range(segments_width):
            faces.append((rows[i][k], rows[i][k + 1], rows[i + 1][k + 1], rows[i + 1][k]))
            face_colors.append(vary(srgb(color), 0.045))
    return _finish(name, verts, faces, None, material, smooth=False, face_colors=face_colors)


def road_line(name, pts, width, color, material=None, z=0.085, dash=0.0):
    if dash <= 0:
        return road_ribbon(name, pts, width, color, material, z=z, crown=0.0, segments_width=1)
    obs = []
    acc = 0.0
    run = []
    for i in range(1, len(pts)):
        p0, p1 = Vector(pts[i - 1]), Vector(pts[i])
        seg = (p1 - p0).length
        steps = max(1, int(seg / 0.8))
        for k in range(steps):
            t = k / steps
            p = p0.lerp(p1, t)
            acc += seg / steps
            if (acc % (dash * 2)) < dash:
                run.append((p.x, p.y))
                if len(run) >= 2:
                    pass
            else:
                if len(run) >= 2:
                    obs.append(road_ribbon(f"{name}_{i}_{k}", run, width, color, material, z=z, crown=0, segments_width=1))
                run = []
    if len(run) >= 2:
        obs.append(road_ribbon(name + "_end", run, width, color, material, z=z, crown=0, segments_width=1))
    return obs


# ---------------------------------------------------------------- vegetation

def tree(name, base, height=5.0, spread=2.2, leaf_color="#4c6b45", trunk_color="#5b4935",
         material_leaf=None, material_trunk=None, rng=None, style="round"):
    rng = rng or random
    x, y, z = base
    obs = []
    trunk_pts = []
    for i in range(5):
        t = i / 4
        bend = math.sin(t * 1.7 + rng.random() * 2) * 0.25
        trunk_pts.append((x + bend, y + math.sin(t * 2.1) * 0.15, z + t * height * 0.62))
    obs.append(tube(name + "_trunk", trunk_pts, 0.11 + height * 0.012, trunk_color, material_trunk, segments=6))
    # branches
    for b in range(3):
        t = 0.28 + b * 0.14
        bx, by, bz = x, y, z + t * height
        ang = rng.random() * math.tau
        ln = spread * (0.45 - b * 0.08)
        obs.append(tube(name + f"_br{b}", [(bx, by, bz),
                     (bx + math.cos(ang) * ln, by + math.sin(ang) * ln, bz + ln * 0.55)],
                     0.035 + height * 0.004, trunk_color, material_trunk, segments=5))
    # foliage clumps
    for c in range(5):
        ang = rng.random() * math.tau
        rad = spread * (0.15 + 0.5 * rng.random())
        cx = x + math.cos(ang) * rad
        cy = y + math.sin(ang) * rad
        cz = z + height * (0.6 + 0.32 * rng.random())
        rx = spread * (0.42 + 0.25 * rng.random())
        rz = rx * (0.6 + 0.2 * rng.random())
        segs = 7
        rings = 4
        verts, faces = [], []
        for r in range(rings):
            t = r / (rings - 1)
            rr = rx * math.sin(math.pi * t) * (0.9 + 0.1 * math.sin(c * 2 + r))
            zz = -rz + 2 * rz * t
            for s in range(segs):
                a = math.tau * s / segs
                verts.append((cx + rr * math.cos(a), cy + rr * math.sin(a), cz + zz + rng.uniform(-0.08, 0.08)))
        for r in range(rings - 1):
            for s in range(segs):
                s2 = (s + 1) % segs
                faces.append((r * segs + s, r * segs + s2, (r + 1) * segs + s2, (r + 1) * segs + s))
        obs.append(_finish(name + f"_leaf{c}", verts, faces, vary(srgb(leaf_color), 0.07), material_leaf, smooth=True))
    return obs


def grass_tuft(name, x, y, z, height=0.35, color="#5f7a48", material=None, rng=None):
    rng = rng or random
    verts, faces, cols = [], [], []
    for k in range(3):
        a = rng.random() * math.tau
        w = 0.06 + rng.random() * 0.05
        dx, dy = math.cos(a) * w, math.sin(a) * w
        h = height * (0.7 + rng.random() * 0.5)
        base = len(verts)
        verts += [(x - dx, y - dy, z), (x + dx, y + dy, z), (x + dy * 3 - dx * .2, y - dx * 3 - dy * .2, z + h)]
        faces.append((base, base + 1, base + 2))
        cols.append(vary(srgb(color), 0.12))
    return [_finish(name, verts, faces, None, material, smooth=False, face_colors=cols)]


def tufts_mesh(name, points, height=0.4, color="#5f7a48", material=None, rng=None):
    """points: [(x,y,z), ...] -> one mesh of 3-blade tufts."""
    rng = rng or random
    verts, faces, cols = [], [], []
    for (x, y, z) in points:
        for k in range(3):
            a = rng.random() * math.tau
            w = 0.055 + rng.random() * 0.05
            dx, dy = math.cos(a) * w, math.sin(a) * w
            h = height * (0.65 + rng.random() * 0.6)
            base = len(verts)
            verts += [(x - dx, y - dy, z), (x + dx, y + dy, z),
                      (x + dy * 3 - dx * .2, y - dx * 3 - dy * .2, z + h)]
            faces.append((base, base + 1, base + 2))
            cols.append(vary(srgb(color), 0.14))
    if not verts:
        return None
    return _finish(name, verts, faces, None, material, smooth=False, face_colors=cols)


def rice_field(name, x, y, z, w, d, rot=0.0, spacing=1.0, height=0.45,
               colors=("#7f9850", "#8fa95c"), material=None, rng=None,
               blade_width=0.06, blades=3):
    rng = rng or random
    verts, faces, cols = [], [], []
    nx, ny = max(1, int(w / spacing)), max(1, int(d / spacing))
    for ix in range(nx):
        for iy in range(ny):
            cx = -w / 2 + (ix + 0.5) * w / nx + rng.uniform(-.12, .12)
            cy = -d / 2 + (iy + 0.5) * d / ny + rng.uniform(-.12, .12)
            if rng.random() < 0.08:
                continue
            for k in range(blades):
                a = rng.random() * math.tau
                ww = blade_width * (0.7 + rng.random() * 0.7)
                dx, dy = math.cos(a) * ww, math.sin(a) * ww
                h = height * (0.7 + rng.random() * 0.55)
                base = len(verts)
                verts += [(cx - dx, cy - dy, 0), (cx + dx, cy + dy, 0),
                          (cx + dy * 3 - dx * .2, cy - dx * 3 - dy * .2, h)]
                faces.append((base, base + 1, base + 2))
                cols.append(vary(srgb(colors[k % 2]), 0.1))
    if not verts:
        return None
    ob = _finish(name, verts, faces, None, material, smooth=False, face_colors=cols)
    apply_xform([ob], (x, y, z), rot)
    return ob


# ---------------------------------------------------------------- roofs / facades

def tile_roof(name, cx, cy, z, width, depth, ridge_h=2.2, eave_h=0.2,
              color="#4b4a45", material=None, curl=0.55, nx=26, ny=40):
    """Traditional tiled roof, ridge along Y, slopes toward ±X, upturned corners."""
    verts, faces, fc = [], [], []
    def h(x, y):
        u = min(1.0, abs(x) / (width / 2))
        v = min(1.0, abs(y) / (depth / 2))
        base = eave_h + ridge_h * (1 - u) ** 1.35
        lift = curl * (u ** 3) * (v ** 5)
        corr = 0.022 * math.sin((y / depth) * math.pi * 38) * (1 - u * 0.3)
        return z + base + lift + corr
    for iy in range(ny + 1):
        for ix in range(nx + 1):
            x = -width / 2 + width * ix / nx
            y = -depth / 2 + depth * iy / ny
            verts.append((cx + x, cy + y, h(x, y)))
    for iy in range(ny):
        for ix in range(nx):
            a = iy * (nx + 1) + ix
            b = a + 1
            c = a + nx + 2
            d = a + nx + 1
            faces.append((a, b, c, d))
            base = srgb(color)
            if (iy // 2) % 2 == 0:
                base = tuple(min(1.0, q * 1.06) for q in base)
            else:
                base = tuple(q * 0.94 for q in base)
            fc.append(vary(base, 0.04))
    ob = _finish(name, verts, faces, None, material, smooth=False, face_colors=fc)
    obs = [ob]
    # ridge beam sits on the roof surface, with end ornaments
    obs.append(box(name + "_ridge", (0.42, depth + 0.7, 0.30), (cx, cy, z + ridge_h + eave_h + 0.02),
                   color="#4b4943", material=material, bevel=0.06))
    for s in (-1, 1):
        obs.append(box(name + f"_ridgeEnd{s}", (0.55, 0.35, 0.62),
                       (cx, cy + s * (depth / 2 + 0.28), z + ridge_h + eave_h + 0.14),
                       color="#4b4943", material=material, bevel=0.05))
        obs.append(cylinder(name + f"_ridgeCap{s}", 0.14, 0.5,
                            (cx, cy + s * (depth / 2 + 0.3), z + ridge_h + eave_h + 0.5),
                            rot=(math.pi / 2, 0, 0), segments=8, color="#3f3d39", material=material))
    # eave fascia + tile ends
    for side in (-1, 1):
        obs.append(box(name + f"_eave{side}", (0.09, depth + 0.4, 0.18),
                       (cx + side * width / 2, cy, z + eave_h + 0.02),
                       color="#3b3833", material=material, bevel=0.02))
        for iy in range(0, ny, 2):
            y = -depth / 2 + depth * iy / ny
            xx = side * width / 2
            obs.append(cylinder(name + f"_cap{side}_{iy}", 0.075, 0.1,
                                (cx + xx, cy + y, z + eave_h + 0.03 + curl * 0.02),
                                rot=(math.pi / 2, 0, 0), segments=6,
                                color="#57534c", material=material))
    return obs


def window_lattice(name, cx, cy, z, w, h, normal_axis="y", sign=-1,
                   frame_color="#4c3928", material=None, bars=4, paper_color=None,
                   paper_material=None):
    """A traditional window: frame, lattice bars, optional glowing paper."""
    obs = []
    rot = (0, 0, 0) if normal_axis == "y" else (0, 0, math.pi / 2)
    if paper_color:
        obs.append(box(name + "_paper", (w * 0.9, 0.015, h * 0.9),
                       (cx, cy + sign * 0.01, z), rot,
                       color=paper_color, material=paper_material, bevel=0))
    # frame
    t = 0.055
    for (dx, dz, sx, sz) in [(0, h / 2, w, t), (0, -h / 2, w, t),
                             (-w / 2, 0, t, h), (w / 2, 0, t, h)]:
        obs.append(box(name + "_fr", (sx, 0.06, sz), (cx + dx, cy + sign * 0.03, z + dz), rot,
                       color=frame_color, material=material, bevel=0.008))
    for i in range(1, bars):
        fx = -w / 2 + w * i / bars
        obs.append(box(name + "_b", (0.022, 0.035, h * 0.9), (cx + fx, cy + sign * 0.04, z), rot,
                       color=frame_color, material=material))
    for i in range(1, 2):
        fz = -h / 2 + h * i / 2
        obs.append(box(name + "_b", (w * 0.9, 0.035, 0.022), (cx, cy + sign * 0.04, z + fz), rot,
                       color=frame_color, material=material))
    return obs


# ---------------------------------------------------------------- signs

_SIGNS = None

def signs():
    global _SIGNS
    if _SIGNS is None:
        with open(os.path.join(ASSETS, "signs_atlas.json"), encoding="utf-8") as f:
            _SIGNS = json.load(f)
    return _SIGNS


def sign_quad(name, key, loc, rot_z=0.0, w=3.0, h=1.0, material=None,
              tilt=0.0, face_color=None):
    rect = signs()["rects"][key]
    x0, y0, x1, y1 = rect["uv"]
    verts = [(-w / 2, 0, -h / 2), (w / 2, 0, -h / 2), (w / 2, 0, h / 2), (-w / 2, 0, h / 2)]
    faces = [(0, 1, 2, 3)]
    ob = _finish(name, verts, faces, face_color or (1, 1, 1), material, smooth=False)
    me = ob.data
    uv = me.uv_layers.new(name="UVMap")
    uvs = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    for i in range(len(me.loops)):
        uv.data[i].uv = uvs[i]
    ob.matrix_world = Matrix.Translation(loc) @ Euler((tilt, 0, rot_z), "XYZ").to_matrix().to_4x4()
    return ob


# ---------------------------------------------------------------- export utilities

def quad(name, corners, color, material, uv=None):
    if len(corners) not in (3,4) or (uv is not None and len(uv)!=len(corners)):
        raise ValueError(f"{name}: expected a triangle or quadrilateral with one UV per corner")
    ob = _finish(name, corners, [tuple(range(len(corners)))], color, material, smooth=False)
    if uv:
        me = ob.data
        layer = me.uv_layers.new(name="UVMap")
        for i in range(len(corners)):
            layer.data[i].uv = uv[i]
    return ob


def _flatten(objs):
    out = []
    for o in objs:
        if isinstance(o, (list, tuple)):
            out.extend(_flatten(o))
        elif o is not None:
            out.append(o)
    return out


def apply_xform(objs, loc=(0, 0, 0), rot_z=0.0, scale=1.0):
    M = Matrix.Translation(loc) @ Matrix.Rotation(rot_z, 4, "Z") @ Matrix.Scale(scale, 4)
    flat = _flatten(objs)
    for o in flat:
        o.matrix_world = M @ o.matrix_world
    return flat


def join_materials(prefix, objs, skip_prefixes=("Water", "FX_")):
    groups = {}
    for ob in objs:
        if ob is None or ob.name in ("",):
            continue
        if ob.get('grove_instance') or any(ob.name.startswith(p) for p in skip_prefixes):
            continue
        if not ob.data or not hasattr(ob.data, "polygons"):
            continue
        key = ob.data.materials[0].name if ob.data.materials else "NoMat"
        groups.setdefault(key, []).append(ob)
    out = []
    for key, group in groups.items():
        out.append(join_group(f"{prefix}_{key}", group))
    return out


def collection(name):
    col = bpy.data.collections.get(name)
    if not col:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
    return col


def save_blend(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=path)
