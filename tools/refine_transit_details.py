"""Targeted edits to the current, already-dressed scenes; preserve their other geometry."""
import bpy,bmesh,math,json,sys
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
import blib as B
ROOT=Path(B.ROOT)
REPORT=ROOT/'qa/transit/details.json'
REPORT.parent.mkdir(parents=True,exist_ok=True)
def components(obj):
    mesh=obj.data
    adjacency=[[] for _ in mesh.vertices]
    for e in mesh.edges:
        a,b=e.vertices;adjacency[a].append(b);adjacency[b].append(a)
    seen=set()
    for start in range(len(mesh.vertices)):
        if start in seen:continue
        todo=[start];seen.add(start);part=[]
        while todo:
            a=todo.pop();part.append(a)
            for b in adjacency[a]:
                if b not in seen:seen.add(b);todo.append(b)
        yield part,[obj.matrix_world@mesh.vertices[i].co for i in part]

def refine_bridge():
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'assets/zones/rail.blend'))
    changed=[]
    for obj in bpy.context.scene.objects:
        if obj.type!='MESH':continue
        material=obj.data.materials[0].name if obj.data.materials else ''
        if material not in ('RailSteel','Valley bridge enamel','Bridge ivory letters'):continue
        selected=[]
        for ids,points in components(obj):
            if all(-7.1<p.x<-6.08 and 8.7<p.y<21.3 and 30.2<p.z<32.8 for p in points):selected.extend(ids)
        if selected:
            delta=obj.matrix_world.inverted().to_3x3()@Vector((0,-15,0))
            for i in selected:obj.data.vertices[i].co+=delta
            obj.data.update();changed.append({'object':obj.name,'vertices':len(selected)})
    assert len(changed)==3,changed
    B.save_blend(str(ROOT/'assets/zones/rail.blend'))
    B.export_glb(str(ROOT/'assets/zones/rail.glb'))
    return changed

def remove_static_train():
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'assets/zones/future.blend'))
    cars=[];theta=math.radians(-72)
    for k in range(5):
        x=-18+70*math.cos(theta);y=12+48*math.sin(theta)
        tx=-70*math.sin(theta);ty=48*math.cos(theta);a=math.atan2(ty,tx)
        cars.append((x,y,math.cos(a),math.sin(a)))
        theta+=8.55/math.hypot(tx,ty)
    def inside(p,car):
        x,y,c,s=car;dx,dy=p.x-x,p.y-y
        return abs(dx*c+dy*s)<4.45 and abs(-dx*s+dy*c)<1.51 and 13.826<p.z<17.7
    removed=[]
    for obj in list(bpy.context.scene.objects):
        if obj.type!='MESH' or not obj.name.startswith('Future_'):continue
        selected=[];parts=0
        for ids,points in components(obj):
            if any(all(inside(p,car) for p in points) for car in cars):
                selected.extend(ids);parts+=1
        if selected:
            bm=bmesh.new();bm.from_mesh(obj.data);bm.verts.ensure_lookup_table()
            bmesh.ops.delete(bm,geom=[bm.verts[i] for i in selected],context='VERTS')
            bm.to_mesh(obj.data);bm.free();obj.data.update()
            removed.append({'object':obj.name,'vertices':len(selected),'parts':parts})
    assert sum(x['parts'] for x in removed)>=100,removed
    B.save_blend(str(ROOT/'assets/zones/future.blend'))
    B.export_glb(str(ROOT/'assets/zones/future.glb'))
    return removed
report={'bridge':refine_bridge(),'removedStaticMetro':remove_static_train()}
REPORT.write_text(json.dumps(report,indent=2),encoding='utf-8')
print('TARGETED SCENE EDITS',json.dumps(report))
