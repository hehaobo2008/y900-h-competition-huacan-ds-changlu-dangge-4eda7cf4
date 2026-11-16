"""Editable set pieces for the market, viaduct and launch complex."""
import math
from pathlib import Path
import sys
import random
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
import blib as B
from model_craft import Batch


def enamel_sign(name,center,width,height,angle,tile):
    x,y,z=center
    dx,dy=math.cos(angle)*width/2,math.sin(angle)*width/2
    u,v=(tile%2)/2,(1-tile//2)/2
    mat=B.mat("Letterpress enamel",texture=str(Path(B.ASSETS)/"textures"/"workshop_print.jpg"),rough=.5)
    return B.quad(name,[(x-dx,y-dy,z-height/2),(x+dx,y+dy,z-height/2),
                        (x+dx,y+dy,z+height/2),(x-dx,y-dy,z+height/2)],"#ffffff",mat,
                  [(u+.001,v+.001),(u+.499,v+.001),(u+.499,v+.499),(u+.001,v+.499)])


def village_sign():
    stand=Batch()
    for y in (-46.74,-45.48): stand.rod((-3.66,y,0),(-3.66,y,1.95),.042,"#6b553e",7)
    return [enamel_sign("Grain purchasing notice",(-3.605,-46.11,1.55),1.45,.725,math.pi*.5,0),
            stand.object("Grain station notice posts",B.vmat("Harvest_timber",.86))]


def newspaper_kiosk():
    frame,paper,awning=Batch(),Batch(),Batch()
    cx,cy=8.25,34.5
    def box(batch,x,y,z,w,d,h,color):
        batch.box((cx+x,cy+y,.17+z),(w,d,h),color)
    pine,green,cream="#415652","#365952","#c8bfa1"
    # Shuttered back and ends, recessed opening and a cantilevered counter.
    box(frame,0,0,.08,2.7,1.40,.16,pine)
    box(frame,0,0,.51,2.62,1.30,.82,green)
    box(frame,0,.60,1.55,2.64,.10,1.75,"#617369")
    for s in (-1,1):
        box(frame,s*1.28,0,1.43,.08,1.32,2.45,green)
        box(frame,s*1.26,-.62,1.65,.085,.085,1.30,cream)
    box(frame,0,-.64,1.03,2.88,.64,.12,"#b5a47e")
    for h in (1.34,1.69,2.04): box(frame,0,.34,h,2.48,.37,.055,"#a18d6c")
    for k in range(9):
        for j in range(3):
            x=-1.05+k*.26
            cover=["#b8b293","#a26b54","#587878","#c6a771","#d6c8a6"][(k*3+j)%5]
            box(paper,x,.15,1.46+j*.35,.225,.08,.25,cover)
            box(paper,x,.102,1.52+j*.35,.173,.013,.018,"#eee1bf")
            for t in range(3):
                box(paper,x,.102,1.45+j*.35-t*.019,.16-t*.025,.009,.007,"#615a4d")
    for k in range(5):
        for j in range(4):
            box(paper,-.89+k*.43,-.69,1.10+j*.015,.35,.40,.014,"#c7bba0" if j%2 else "#e0cfaa")
    for k in range(20):
        x=-1.47+k*.15; col="#6c8578" if k%2 else "#d3c9a8"
        awning.panel([(cx+x,cy-.5,2.82),(cx+x+.15,cy-.5,2.82),
                      (cx+x+.15,cy-1.14,2.62),(cx+x,cy-1.14,2.62)],col)
        awning.panel([(cx+x,cy-1.14,2.62),(cx+x+.15,cy-1.14,2.62),
                      (cx+x+.14,cy-1.14,2.50),(cx+x+.075,cy-1.14,2.47),(cx+x,cy-1.14,2.51)],col)
    box(frame,0,0,2.72,2.98,1.66,.11,pine)
    box(frame,0,-.37,3.04,2.40,.10,.70,green)
    plate=enamel_sign("Masthead facing the approach",(cx,cy-.431,3.22),2.37,.65,0,1)
    pieces=[frame.object("Street kiosk joinery",B.vmat("Kiosk paint",.58)),
            paper.object("Individual journals and folded papers",B.vmat("Newsprint",.95)),
            awning.object("Scalloped canvas blind",B.vmat("Kiosk canvas",.92)),plate]
    from mathutils import Matrix
    pivot=Matrix.Translation((cx,cy,0))
    transform=pivot @ Matrix.Rotation(-.98,4,"Z") @ pivot.inverted()
    for obj in pieces: obj.data.transform(transform)
    return pieces


def station_letters(words,name,cx,y,z,height,width,face,material):
    curve=bpy.data.curves.new(name,"FONT")
    if face: curve.font=bpy.data.fonts.load(str(Path(B.ASSETS)/"sources"/"lettering"/face),check_existing=True)
    curve.body=words
    curve.space_character=1.18 if face else 1.36
    curve.resolution_u=6
    curve.extrude=.026
    curve.bevel_depth=.004
    curve.bevel_resolution=1
    original=bpy.data.objects.new(name,curve)
    bpy.context.collection.objects.link(original)
    bpy.context.view_layer.update()
    geometry=bpy.data.meshes.new_from_object(original.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bpy.data.objects.remove(original,do_unlink=True)
    bpy.data.curves.remove(curve)
    points=[v.co.copy() for v in geometry.vertices]
    left,right=min(p.x for p in points),max(p.x for p in points)
    low,high=min(p.y for p in points),max(p.y for p in points)
    scale=min(height/(high-low),width/(right-left))
    for v,p in zip(geometry.vertices,points):
        v.co=(cx+(p.x-(left+right)/2)*scale,y-p.z*scale,z+(p.y-(low+high)/2)*scale)
    obj=bpy.data.objects.new(name,geometry)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    return obj


def viaduct():
    steel,paint,lamps=Batch(),Batch(),Batch()
    for edge in (.42,9.58):
        for x in range(-152,152,4):
            steel.box((x+2,edge,12.87),(3.94,.22,.68),"#4b6068")
            for dx,dz in ((.16,12.61),(.16,13.13),(3.84,12.61),(3.84,13.13)):
                steel.rod((x+dx,edge-.13,dz),(x+dx,edge+.13,dz),.055,"#89918a",8)
            steel.rod((x,edge,13.65),(x,edge,14.54),.046,"#667d80")
        steel.rod((-152,edge,14.54),(152,edge,14.54),.057,"#8b9b93")
    # An arcade of triangular diaphragms under the deck. Interior faces catch
    # station light and the roof stays below the passing train's silhouette.
    for x in range(-60,61,3):
        steel.pipe([(x,.7,12.62),(x,2.55,11.86),(x,7.45,11.86),(x,9.3,12.62)],.095,"#62777a")
        if x%6==0:
            lamps.box((x,.18,12.55),(1.38,.10,.075),"#f7c58f")
    for x in (-13.2,13.2):
        for y in (-38,-16,24):
            steel.box((x,y,.27),(.72,.68,.43),"#526566")
            steel.rod((x,y,.41),(x,y,5.1),.12,"#455653",10)
            steel.rod((x,y,4.92),(x*.79,y,4.92),.095,"#51605c")
            steel.box((x*.79,y,4.40),(.42,.39,1.28),"#2c393b")
            for j,col in enumerate(["#a54637","#ba9250","#4ba490"]):
                paint.rod((x*.79,y-.18,4.78-.33*j),(x*.79,y-.23,4.78-.33*j),.126,col,16)
    plate=enamel_sign("Viaduct station entrance",(-11.4,-3.20,3.30),3.20,1.60,0,2)
    for x in (-12.65,-10.15): steel.rod((x,-3.10,0),(x,-3.10,4.08),.081,"#526264")
    # Approach-side enamel fascia. The piers, hangers and passing train sit behind the face.
    cx,y,z=1.45,-.65,11.12
    steel.box((cx,y,z),(8.75,.28,1.88),"#c19f72")
    steel.box((cx,y-.12,z),(8.61,.16,1.74),"#25424a")
    for x in (cx-3.72,cx+3.72):
        steel.pipe([(x,-.47,z+.60),(x,-.47,12.68),(x,.50,12.83)],.105,"#827d6c")
        for zz in (z-.68,z+.68): steel.rod((x,-.86,zz),(x,-.89,zz),.058,"#c8b490")
    ivory=B.mat("Station enamel ivory","#f3dfb2",rough=.52,emission="#f3dca5",emis_strength=.62)
    lettering=[station_letters("长路里站","Changluli name",cx,-.91,z+.16,.89,6.2,"ZCOOLQingKeHuangYou-Regular.ttf",ivory),
               station_letters("CHANGLULI  STATION","Station romanization",cx,-.91,z-.52,.22,5.75,None,ivory)]
    return [steel.object("Riveted inspection walk and road signals",B.vmat("Bridge steelwork",.46,.38)),
            paint.object("Signal lenses",B.vmat("Signal glass",.20,.22)),
            lamps.object("Underslung station lamps",B.mat("Platform light","#f5d0a3",emission="#edb877",emis_strength=1.5)),plate,*lettering]


def propellant_gallery():
    steel,coat,light=Batch(),Batch(),Batch()
    # Service side of the launch table, with flanged supply lines, handwheels
    # and a grated walkway following the bend towards the tower.
    for j in range(3):
        x=112+j*.69
        points=[(x,55,6.75),(x,55,8.2+j*.2),(x,69,8.2+j*.2),
                (x-.32,69.6,8.2+j*.2),(x-2.7,72.1,8.2+j*.2),(x-2.7,75,8.2+j*.2)]
        steel.pipe(points,.18-j*.025,"#a3b6b2",14)
        for y in (58,62,66,68):
            z=8.2+j*.2
            steel.rod((x,y-.07,z),(x,y+.07,z),.25-j*.025,"#617577",16)
            for k in range(8):
                a=k*math.tau/8
                steel.rod((x+.205*math.cos(a),y-.09,z+.205*math.sin(a)),
                          (x+.205*math.cos(a),y+.09,z+.205*math.sin(a)),.023,"#bec0ac",6)
        z=8.2+j*.2
        steel.rod((x,59,z),(x,59,z+.56),.08,"#697775")
        loop=[(x+.31*math.cos(a*math.tau/24),59+.31*math.sin(a*math.tau/24),z+.57) for a in range(25)]
        coat.pipe(loop,.037,"#a84735")
        for a in (0,2.09,4.19):
            coat.rod((x,59,z+.57),(x+.30*math.cos(a),59+.30*math.sin(a),z+.57),.022,"#a84735")
    for k in range(94):
        steel.box((115.32,55+k*.17,7.98),(1.37,.065,.12),"#859596")
    for side in (-1,1):
        x=115.32+side*.69
        steel.box((x,62.9,7.83),(.14,16.1,.26),"#515f62")
        for y in (55,58.2,61.4,64.6,67.8,70.9):
            steel.rod((x,y,6.64),(x,y,9.10),.054,"#858f87")
        coat.rod((x,55,9.10),(x,70.9,9.10),.063,"#c9a363")
    for x in (111.2,115.5):
        steel.rod((x,55,6.60),(x,55,11.22),.088,"#667579")
    plate=enamel_sign("Launch service placard",(113.35,54.95,10.23),4.43,1.85,0,3)
    for k in range(8):
        z=12.2+10*k
        light.box((117,84.3,z),(4.9,.085,.16),"#ffd2a0")
    launch_woodland()
    return [steel.object("Cryogenic pipe flanges and grating",B.vmat("Service alloy",.36,.64)),
            coat.object("Valve handwheels and safety rails",B.vmat("Safety enamel",.54,.21)),
            light.object("Service tower deck lights",B.mat("Service deck lamps","#eac995",emission="#f4c285",emis_strength=1.5)),plate]


def launch_woodland():
    from build_future import ground_h,fbm,sstep
    # The authored terrain grid is preserved when the base scene is batched.
    # Give its shared vertices continuous pigment across cell boundaries.
    terrain=bpy.data.objects["Future_F_Matte"]
    mesh=terrain.data
    attr=mesh.color_attributes["Col"]
    grid={}
    for v in mesh.vertices:
        x,y,z=terrain.matrix_world @ v.co
        u=(x+160)*112/320; w=(y+150)*96/300
        if abs(u-round(u))>.00009 or abs(w-round(w))>.00009 or z<4: continue
        if abs(z-ground_h(x,y))>.03: continue
        n=fbm(x*.074,y*.074,124,3)
        wooded=B.mix(B.srgb("#304b4d"),B.srgb("#60726b"),n)
        stone=B.mix(B.srgb("#516266"),B.srgb("#75817a"),n)
        grid[v.index]=B.mix(wooded,stone,sstep(22,54,z))
    for loop in mesh.loops:
        if loop.vertex_index in grid:
            attr.data[loop.index].color=(*grid[loop.vertex_index],1)
    from planted_trees import plant
    for obj in list(bpy.context.scene.objects):
        if obj.get('grove_instance') and obj.name.startswith('Starport windbreak'):
            bpy.data.objects.remove(obj,do_unlink=True)
    rng=random.Random(2035)
    planted=[]
    for i in range(740):
        x,y=rng.uniform(-153,155),rng.uniform(-143,147)
        if y<108 and x>-114: continue
        z=ground_h(x,y)
        if z<9 or fbm(x*.054,y*.054,76,2)<.42: continue
        if any((x-a)**2+(y-b)**2<46 for a,b in planted): continue
        planted.append((x,y))
        h=rng.uniform(5.4,9.3)
        plant("silver",x,y,z-.1,h,h*.82,"Starport windbreak")


def fairing_marks():
    decals=Batch()
    def wrap(a0,a1,z0,z1,col,r=2.637):
        for i in range(32):
            aa=a0+(a1-a0)*i/32
            bb=a0+(a1-a0)*(i+1)/32
            decals.panel([(r*math.cos(a),r*math.sin(a),z) for a,z in [(aa,z0),(bb,z0),(bb,z1),(aa,z1)]],col)
    for z,thick in ((7.1,.23),(24.0,.12),(24.42,.36),(28.2,.12)): wrap(0,math.tau,z,z+thick,"#a34e3a")
    for side in range(4):
        a=side*math.pi/2-.92
        # Banked chevrons on the tank repeat the rising path of the red thread.
        for k in range(22):
            t=k/22
            wrap(a-.26+t*.52,a-.26+(k+1)/22*.52,16.55+1.6*(1-abs(2*t-1)),
                 17.05+1.6*(1-abs(2*t-1)),"#aa4f3b")
        for j in range(12):
            wrap(a+.4,a+.4+(.12 if j%3 else .22),11+j*.32,11.045+j*.32,"#41555b")
    return [decals.object("Tank registration chevrons and inspection scale",B.vmat("Vehicle enamel markings",.41,.16))]


def touring_luggage():
    rack,case,leather=Batch(),Batch(),Batch()
    for x in (-.565,.565):
        for y in (-.49,.19):
            rack.box((x,y,1.45),(.13,.12,.065),"#373f40")
            rack.rod((x,y,1.47),(x*1.10,y,1.56),.023,"#9baba8")
        rack.pipe([(x,-.69,1.62),(x,-.63,1.56),(x,.30,1.56),(x,.34,1.62)],.023,"#b0b8b2")
    for y in (-.53,-.26,.02,.23): rack.rod((-.62,y,1.56),(.62,y,1.56),.024,"#a6ada5")
    rings=[]
    for z,w,d in [(1.59,.47,.31),(1.62,.49,.33),(1.85,.48,.32),(1.89,.45,.29)]:
        ring=[]
        for j in range(40):
            a=j*math.tau/40; c,s=math.cos(a),math.sin(a)
            ring.append((-.025+w*math.copysign(abs(c)**.28,c),-.15+d*math.copysign(abs(s)**.28,s),z))
        rings.append(ring)
    case.rings(rings,"#a38159")
    for x in (-.29,.24):
        leather.box((x,-.15,1.895),(.056,.55,.014),"#634737")
        for y in (-.474,.171):
            leather.box((x,y,1.746),(.057,.017,.25),"#654737")
            rack.box((x,y+(-.01 if y<0 else .01),1.75),(.071,.022,.052),"#b39b69")
    rack.pipe([(-.12,-.485,1.72),(-.12,-.526,1.78),(.08,-.526,1.78),(.08,-.485,1.72)],.014,"#655545")
    return [rack.object("Rain gutter roof rack and hardware",B.vmat("Rack chrome",.26,.72)),
            case.object("Travel case",B.vmat("Case canvas",.86)),leather.object("Leather case straps",B.vmat("Oiled leather",.69))]


def locomotive_gear():
    steel,trim=Batch(),Batch()
    for s in (-1,1):
        for y in (42,44,46,48,50):
            trim.box((s*1.266,y,2.51),(.052,1.46,1.10),"#263e38")
            for k in range(8):
                steel.box((s*1.308,y,2.08+k*.117),(.070,1.35,.037),"#69816d")
        for y in (39.2,42.5,45.5,48.5,51.7):
            steel.rod((s*1.48,y,.98),(s*1.48,y,1.98),.029,"#b8ad85")
        steel.pipe([(s*1.48,39.2,1.22),(s*1.48,39.2,1.98),(s*1.48,51.7,1.98)],.036,"#d2c493")
        for j in range(3):
            steel.box((s*1.45,56.5,.39+j*.24),(.28,.62,.055),"#948c72")
        steel.rod((s*.66,57.08,2.20),(s*.31,57.08,2.91),.024,"#27353b")
    pieces=[steel.object("Louvres, access steps and grab rails",B.vmat("Locomotive hardware",.48,.35)),
            trim.object("Recessed ventilation compartments",B.vmat("Locomotive recesses",.81))]
    for obj in pieces: obj.location.y=-5.5
    return pieces


def install(name):
    for obj in list(bpy.context.scene.objects):
        if obj.get("edition_fixture")==name: bpy.data.objects.remove(obj,do_unlink=True)
    pieces={"town":newspaper_kiosk,"city":viaduct,"future":propellant_gallery,"rocket":fairing_marks,
            "car":touring_luggage,"green_train":locomotive_gear}[name]()
    for obj in pieces: obj["edition_fixture"]=name
    return pieces


if __name__=="__main__":
    source=Path(bpy.data.filepath)
    install(source.stem)
    bpy.ops.file.pack_all()
    B.save_blend(str(source))
    B.export_glb(str(source.with_suffix(".glb")))
