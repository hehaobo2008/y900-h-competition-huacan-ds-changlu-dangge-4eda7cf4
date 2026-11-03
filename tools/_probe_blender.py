import bpy
print("BLENDER", bpy.app.version_string)
props = bpy.ops.export_scene.gltf.get_rna_type().properties
for p in props:
    if any(k in p.identifier for k in ["color","vertex","draco","image","material","yup","apply","format","selection","camera","light","extras"]):
        print(p.identifier, getattr(p,"default",None))
print("has gltf addon", "io_scene_gltf2" in bpy.context.preferences.addons)
