"""Make legible, physically fitted Chinese lettering from the bundled OFL typefaces."""
import math
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

import blib as B


def letters(name, words, centre, width, height, material, angle=0, brush=False, relief=.009):
    face = "MaShanZheng-Regular.ttf" if brush else "ZCOOLQingKeHuangYou-Regular.ttf"
    font = bpy.data.fonts.load(str(Path(B.ASSETS) / "sources" / "lettering" / face), check_existing=True)
    curve = bpy.data.curves.new(name, "FONT")
    curve.font, curve.body, curve.space_character = font, words, 1.12
    curve.resolution_u = 6
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    mesh = bpy.data.meshes.new_from_object(obj.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.curves.remove(curve)
    lo = Vector(tuple(min(v.co[i] for v in mesh.vertices) for i in range(3)))
    hi = Vector(tuple(max(v.co[i] for v in mesh.vertices) for i in range(3)))
    scale = min(width/(hi.x-lo.x), height/(hi.y-lo.y))
    mesh.transform(Matrix.Scale(scale, 4) @ Matrix.Translation(-(lo+hi)*.5))
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    obj.matrix_world = Matrix.Translation(centre) @ Matrix.Rotation(angle, 4, 'Z') @ Matrix.Rotation(math.pi/2, 4, 'X')
    if relief:
        mod = obj.modifiers.new("Enamel depth", 'SOLIDIFY')
        mod.thickness, mod.offset = relief, -1
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
    return obj


def grain_notice():
    wood = B.mat("Weathered notice frame", "#675040", rough=.92)
    chalk = B.mat("Lime chalk", "#e4dcc2", rough=.99)
    board = [B.box("Weighing slate", (1.66,.055,1.32), (0,-.069,0),
                   color="#43524b", material=B.vmat("Weighing slate paint",.96))]
    for side in (-1,1):
        board.append(B.box("Notice frame", (.062,.12,1.45), (side*.85,-.066,0),material=wood))
        board.append(B.box("Notice rail", (1.74,.12,.065), (0,-.066,side*.68),material=wood))
    board.append(letters("Weighing announcement","收购过秤",(0,-.103,.20),1.42,.40,chalk,brush=True,relief=0))
    board.append(letters("Produce on scales","稻　谷",(0,-.103,-.30),.72,.24,chalk,brush=True,relief=0))
    return board


def porch_braces():
    wood=B.vmat("Entrance carpentry",.88)
    return [B.beam("Shelter knee brace",(side*4.4,0,-1.22),(side*3.18,0,-.26),
                   .19,.22,"#63513f",wood) for side in (-1,1)]

