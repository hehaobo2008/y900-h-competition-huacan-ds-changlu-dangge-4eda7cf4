"""Measure the theatre's parked bicycles after both model-space transforms."""
import json,math,sys
from pathlib import Path
from mathutils import Vector
import bpy
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/"tools"))
import build_town as town

assembled=[]
def collect(name,objects,**options):
    assembled.extend(objects)
    return []
town.B.join_materials=collect
town.cinema_build()
bpy.context.view_layer.update()
rows=[]
for j in range(2):
    prefix=f"cin_bike{j}_rim"
    wheels=[o for o in assembled if o.name.startswith(prefix)]
    assert len(wheels)==2
    world=[o.matrix_world @ v.co for o in wheels for v in o.data.vertices]
    avg=sum(world,Vector())/len(world)
    street=town.road_x(avg.y)
    edge=min(v.x-town.road_x(v.y) for v in world)
    floor=min(v.z for v in world)
    assert edge>5.4 and abs(floor-.16)<.045,(edge,floor)
    rows.append(dict(center=[round(avg.x,3),round(avg.y,3)],distanceFromRoadAxis=round(edge,3),tireBottom=round(floor,3)))
separation=math.dist(rows[0]["center"],rows[1]["center"])
assert separation>1.15
(root/"qa"/"refinement"/"cinema.json").write_text(json.dumps(dict(bicycles=rows,centerSpacing=round(separation,3)),indent=2),"utf8")
print("Theatre parking",rows,round(separation,2))
