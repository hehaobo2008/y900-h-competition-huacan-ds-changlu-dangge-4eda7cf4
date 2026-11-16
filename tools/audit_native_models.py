"""Reopen the editable models with Blender and check every file-backed image."""
from pathlib import Path
import json
import bpy

root=Path(__file__).resolve().parents[1]
results=[]
for folder,names in [('zones',['rural','town','city','rail','future']),
                     ('vehicles',['rickshaw','car','green_train','hsr','harmony','rocket'])]:
    for name in names:
        file=root/'assets'/folder/(name+'.blend')
        bpy.ops.wm.open_mainfile(filepath=str(file))
        images=[im for im in bpy.data.images if im.source=='FILE' and im.filepath]
        missing=[im.name for im in images if not im.packed_file and not Path(bpy.path.abspath(im.filepath)).is_file()]
        results.append(dict(name=name,bytes=file.stat().st_size,objects=len(bpy.context.scene.objects),
                            meshes=sum(o.type=='MESH' for o in bpy.context.scene.objects),fileImages=len(images),
                            packedImages=sum(bool(im.packed_file) for im in images),missing=missing))
(root/'qa'/'edition'/'native-audit.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
if any(not r['meshes'] or r['missing'] for r in results):
    raise ValueError([r for r in results if not r['meshes'] or r['missing']])
print('NATIVE AUDIT',len(results),'files passed')
