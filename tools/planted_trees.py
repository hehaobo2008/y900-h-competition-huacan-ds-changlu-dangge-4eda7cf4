"""Linked CC0 trees. Height and crown diameter are specified in metres."""
import math
from pathlib import Path
import bpy
from mathutils import Matrix, Vector

ROOT=Path(__file__).resolve().parents[1]/"assets/vegetation/trees"
MODELS={
    "street":("CommonTree_1","CommonTree_2"), "avenue":("CommonTree_3","CommonTree_4"),
    "river":("CommonTree_5",), "pine":("Pine_2","Pine_3","Pine_4"),
    "silver":("TwistedTree_2","TwistedTree_4"), "copper":("TwistedTree_1","TwistedTree_5"),
}
library={}


def plant(family,x,y,z,height,diameter,name=None):
    seed=round(x*43.3+y*71.7+z*11)
    variants=MODELS[family]
    variant=variants[seed%len(variants)]
    cached=library.get(variant)
    if cached is None or bpy.data.meshes.get(cached[0]) is None:
        bpy.ops.import_scene.gltf(filepath=str(ROOT/(variant+".glb")))
        obj=next(o for o in bpy.context.selected_objects if o.type=="MESH")
        mesh=obj.data
        mesh.transform(obj.matrix_world)
        top=max(v.co.z for v in mesh.vertices)
        width=max(max(v.co[a] for v in mesh.vertices)-min(v.co[a] for v in mesh.vertices) for a in (0,1))
        library[variant]=(mesh.name,top,width)
        bpy.data.objects.remove(obj,do_unlink=True)
    mesh_name,top,width=library[variant]
    obj=bpy.data.objects.new(name or (family+" "+variant),bpy.data.meshes[mesh_name])
    obj["grove_instance"]=True
    bpy.context.scene.collection.objects.link(obj)
    scale=diameter/width
    # The source root collar is at zero. Buried roots stay below the surface.
    obj.matrix_world=(Matrix.Translation(Vector((x,y,z))) @ Matrix.Rotation(seed*2.39996%(2*math.pi),4,"Z")
                      @ Matrix.Diagonal(Vector((scale,scale,height/top,1))))
    return obj
