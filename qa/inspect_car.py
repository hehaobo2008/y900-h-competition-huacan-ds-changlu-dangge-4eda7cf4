import bpy
bpy.ops.wm.open_mainfile(filepath=r"H:\appdata\H\competition\huacan-ds\changlu-dangge\assets\vehicles\car.blend")
for ob in bpy.context.scene.objects:
    if ob.type=='MESH':
        xs=[(ob.matrix_world @ v.co) for v in ob.data.vertices]
        mn=[min(p[i] for p in xs) for i in range(3)]
        mx=[max(p[i] for p in xs) for i in range(3)]
        print(ob.name, [round(v,2) for v in mn], [round(v,2) for v in mx], len(ob.data.polygons))
