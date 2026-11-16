"""Assemble the supplied 轨上清风 rolling stock in the project's metre coordinate system."""
from pathlib import Path
import math
import sys

import bpy
import bmesh
from mathutils import Matrix

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets" / "sources" / "guishangqingfeng"
OUT = ROOT / "assets" / "vehicles"


def meshes(file, ratio):
    bpy.ops.import_scene.gltf(filepath=str(SOURCE / file))
    result = [o for o in bpy.context.selected_objects if o.type == 'MESH']
    for obj in result:
        transform = obj.matrix_world.copy()
        obj.parent = None
        obj.matrix_world = Matrix.Identity(4)
        obj.data.transform(transform)
        if ratio < 1 and len(obj.data.polygons) > 25000:
            mod = obj.modifiers.new("Web silhouette", 'DECIMATE')
            mod.ratio = ratio
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.modifier_apply(modifier=mod.name)
    return result


def duplicate(objects, y, turn=0):
    for obj in objects:
        duplicate = obj.copy()
        bpy.context.collection.objects.link(duplicate)
        duplicate.rotation_mode = 'XYZ'
        duplicate.location.y = y
        duplicate.rotation_euler.z = turn


def emu(cab, coach, count):
    heads = meshes(cab, 1. if cab.startswith("crh-") else .21)
    cars = meshes(coach, 1.)
    if cab.startswith("crh-"):
        sys.path.insert(0,str(ROOT / "tools"))
        from coach_finish import restore_bonnet,finish_coach
        restore_bonnet(heads)
        finish_coach(cars)
    length, gap = 22.010002, .20
    rear = (count * length + (count + 1) * gap) / 2
    duplicate(heads, -rear, math.pi)
    for obj in heads:
        obj.location.y = rear
    for i in range(1, count):
        duplicate(cars, -rear + gap + i * (gap + length))
    for obj in cars:
        obj.location.y = -rear + gap


def green(coaches=16):
    objects = meshes("green-mobile.glb", .32)
    for obj in objects:
        coach = obj.copy()
        coach.data = obj.data.copy()
        bpy.context.collection.objects.link(coach)
        bm = bmesh.new()
        bm.from_mesh(coach.data)
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.y > 12.45], context='VERTS')
        bm.to_mesh(coach.data)
        bm.free()
        length = 12.52
        # The source includes a locomotive and the first passenger coach.
        obj.location.y = (length * (coaches - 1) - 24.48) / 2
        coach.location.y = obj.location.y - length
        for i in range(2, coaches):
            duplicate([coach], obj.location.y - length * i)


if __name__ == '__main__':
    selection=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    for target in selection or ('green_train', 'hsr', 'harmony'):
        if target not in ('green_train','hsr','harmony'): raise ValueError(target)
        bpy.ops.wm.read_factory_settings(use_empty=True)
        if target == 'green_train':
            green()
        else:
            kind = 'cr400af' if target == 'hsr' else 'crh'
            emu(kind + '-mobile-v4.glb', kind + '-coach-mobile-v4.glb', 10)
        for obj in list(bpy.context.scene.objects):
            if obj.type != 'MESH':
                bpy.data.objects.remove(obj, do_unlink=True)
        bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.wm.save_as_mainfile(filepath=str(OUT / (target + '.blend')), compress=True)
        bpy.ops.export_scene.gltf(filepath=str(OUT / (target + '.glb')), export_format='GLB',
                                  export_yup=True, export_image_format='AUTO', export_cameras=False, export_lights=False)
    if selection: sys.exit(0)
    sys.path.insert(0, str(ROOT / 'tools'))
    from build_future import ground_h
    import json
    # A four-metre grid follows the original terrain, including the launch plateau and tidal basin.
    grid = [[round(ground_h(x, -z), 2) for x in range(-160, 161, 4)] for z in range(-148, 149, 4)]
    (ROOT / 'src' / 'future_ground.json').write_text(json.dumps(grid,separators=(',',':')),encoding='ascii')
