"""Export an edited rural.blend or rickshaw.blend without modifying the source.

Usage: blender -b assets/zones/rural.blend --python tools/export_rural_assets.py
"""
from pathlib import Path
import sys
import bpy
sys.path.insert(0, str(Path(__file__).resolve().parent))
import blib as B

source = Path(bpy.data.filepath)
if source.name not in ("rural.blend", "rickshaw.blend"):
    raise RuntimeError("Open rural.blend or rickshaw.blend before export")
meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
if source.name == "rural.blend":
    B.join_materials("Rural", meshes)
else:
    B.join_materials("Rickshaw", meshes, skip_prefixes=())
target = source.with_suffix(".glb")
B.export_glb(str(target))
print("EXPORTED_EDITABLE_SOURCE", target, target.stat().st_size)
