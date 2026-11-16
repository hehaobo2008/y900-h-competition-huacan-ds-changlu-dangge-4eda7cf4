"""Verify tree sources and the four viewpoints along each native tunnel."""
import bpy,json
from pathlib import Path
from mathutils import Vector

root=Path(__file__).resolve().parents[1]
report={}
seen=set()
for chapter in ('town','city','rail','future'):
    bpy.ops.wm.open_mainfile(filepath=str(root/'assets/zones'/(chapter+'.blend')))
    trees=[obj for obj in bpy.context.scene.objects if obj.get('grove_instance')]
    models={t.data.name.split('.')[0] for t in trees}
    if not models or seen&models:raise ValueError((chapter,models,seen&models))
    seen|=models
    report[chapter]={'models':sorted(models),'trees':len(trees)}
    print('PLANTED',chapter,len(trees),sorted(models))
    if chapter=='future':
        for o in trees:
            if o.name.startswith(('LabTree','ShoreTree','BayDeckTree','PortTree','PlazaTree')):
                print('SPECIMEN',o.name,tuple(round(x,2) for x in o.matrix_world.translation))
    if chapter!='rail':continue
    scene=bpy.context.scene;dg=bpy.context.evaluated_depsgraph_get()
    def hit(start,ray,axis,expected):
        ok,at,normal,face,ob,mat=scene.ray_cast(dg,Vector(start),Vector(ray),distance=65)
        if not ok or abs(at[axis]-expected)>.65:
            raise AssertionError((start,ray,expected,tuple(at),ob))
        return round(at[axis],2)
    tunnels={}
    for s in (-1,1):
        tunnels[str(s)]={
            'trackClearToBack':[hit((x,s*104,35.4),(0,s,0),1,s*142) for x in (-2.4,2.4)],
            'sideLining':[hit((0,s*124,35.4),(h,0,0),0,h*6.9) for h in (-1,1)],
            'ceiling':hit((0,s*124,35.4),(0,0,1),2,43),
            'outsideWall':hit((2,s*158,35.4),(0,-s,0),1,150*s)}
    report[chapter]['portals']=tunnels
if len(seen)!=12:raise AssertionError(seen)
(root/'qa/scenery/planting.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
