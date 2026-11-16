"""Five-car orbital-city maglev: two streamlined cabs and articulated passenger cars."""
import math,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
import blib as B
from build_future import loft_rings,rounded_yz
ROOT=Path(B.ROOT)
B.reset(2036)
shell=B.mat('Metro pearl ceramic','#dce5e2',rough=.34,metal=.24)
glass=B.mat('Metro smoked glazing','#23414c',rough=.22,metal=.30)
trim=B.mat('Metro teal belt','#407d83',rough=.42,metal=.25)
metal=B.mat('Metro brushed alloy','#829b9e',rough=.43,metal=.65)
dark=B.mat('Metro charcoal bellows','#263b43',rough=.83)
light=B.mat('Metro warm interior','#f9dfb4',rough=.4,emission='#ffdfad',emis_strength=.45)
head=B.mat('Metro headlight','#eefcff',emission='#d8f3ff',emis_strength=2)
tail=B.mat('Metro tail marker','#db6555',emission='#ea6958',emis_strength=.8)

def body_section(x,w=2.88,h=2.92,bottom=.24,r=.46):
    return rounded_yz(x,w,h,min(r,w*.46,h*.46),8,zc=bottom)
def box(name,size,loc,mat,bevel=.025):
    return B.box(name,size,loc,material=mat,bevel=bevel)
def side_panel(name,cx,z,w,h,side,mat,r=.10,y=1.448):
    # A rounded panel lies flush with the straight portion of the body.
    pts=[]
    for px,pz,a in [(w/2-r,h/2-r,0),(-w/2+r,h/2-r,math.pi/2),
                    (-w/2+r,-h/2+r,math.pi),(w/2-r,-h/2+r,3*math.pi/2)]:
        for j in range(7):
            q=a+j*math.pi/12;pts.append((cx+px+r*math.cos(q),side*y,z+pz+r*math.sin(q)))
    return B._finish(name,pts,[tuple(range(len(pts)))],None,mat,smooth=False)

def carriage(name,cab=False,rear=False):
    objects=[]
    if cab:
        profiles=[(-4.45,2.78,2.82,.28),(-4.25,2.88,2.92,.24),(1.8,2.88,2.92,.24),
                  (2.7,2.85,2.81,.26),(3.45,2.67,2.46,.29),(4.15,2.23,1.95,.31),
                  (4.85,1.61,1.33,.35),(5.35,.92,.74,.45),(5.6,.30,.31,.61)]
    else:
        profiles=[(-4.45,2.74,2.82,.28),(-4.25,2.88,2.92,.24),(4.25,2.88,2.92,.24),(4.45,2.74,2.82,.28)]
    objects.append(loft_rings(name+' continuous shell',[body_section(*p) for p in profiles],None,shell,True))
    # Quiet belt, dark connected glazing and differentiated doors, not luminous squares.
    for side in (-1,1):
        length=6.35 if cab else 8.22;cx=-1.0 if cab else 0
        objects.append(side_panel(name+' lower belt',cx,.83,length,.18,side,trim,r=.06))
        objects.append(side_panel(name+' window gasket',cx,2.09,length,1.01,side,dark,r=.15,y=1.452))
        windows=[-3.35,-2.04,-.73,.58] if cab else [-3.2,-1.6,0,1.6,3.2]
        for i,x in enumerate(windows):
            objects.append(side_panel(name+' glazing '+str(i),x,2.10,1.15 if cab else 1.37,.85,side,glass,r=.13,y=1.459))
            # Two restrained reflections make each pane read as curved glass.
            objects.append(side_panel(name+' reflected light '+str(i),x,2.41,.94 if cab else 1.15,.045,side,metal,r=.014,y=1.464))
        for x in ([-2.65] if cab else [-2.41,2.41]):
            objects.append(side_panel(name+' door seam',x,1.58,.88,2.13,side,metal,r=.08,y=1.469))
            objects.append(side_panel(name+' flush door',x,1.58,.82,2.07,side,shell,r=.07,y=1.475))
            objects.append(side_panel(name+' door window',x,2.04,.61,.93,side,glass,r=.08,y=1.481))
            objects.append(side_panel(name+' door centre',x,1.56,.018,1.93,side,dark,r=.006,y=1.484))
            objects.append(side_panel(name+' door threshold',x,.50,.80,.06,side,metal,r=.01,y=1.482))
        objects.append(side_panel(name+' cabin light',cx,2.61,2.28,.035,side,light,r=.01,y=1.462))
        objects.append(side_panel(name+' service hatch',.40 if cab else .75,1.18,1.04,.29,side,metal,r=.04,y=1.453))
    # Low fairings embrace the guide beam. Levitation modules sit under each bogie.
    objects.append(box(name+' underframe',(7.9,2.20,.35),(0,0,.34),dark,.10))
    for x in (-2.9,2.8):
        objects.append(box(name+' magnetic suspension',(1.66,2.55,.35),(x,0,.24),metal,.08))
        for side in (-1,1):
            objects.append(box(name+' suspension cover',(1.90,.25,.49),(x,side*1.20,.23),dark,.07))
    objects.append(box(name+' roof climate pod',(3.2,1.28,.18),(-.8,0,3.18),shell,.085))
    for x in [-2.05+i*.23 for i in range(12)]:
        objects.append(box(name+' roof vent',(.065,1.02,.016),(x,0,3.281),dark,.005))
    # Accordion connection and coupler are explicit geometry.
    for x in ([-4.55] if cab else [-4.55,4.55]):
        objects.append(box(name+' gangway',( .22,2.24,2.48),(x,0,1.65),dark,.10))
        for j in range(4):
            objects.append(box(name+' bellows rib',(.032,2.30,2.54),(x+(j-1.5)*.06,0,1.65),metal,.07))
        objects.append(box(name+' coupler',(.46,.40,.24),(x,0,.40),metal,.02))
    if cab:
        # Curved windshield follows the upper nose; no flat sticker across the cab.
        rings=[]
        def nose_profile(x):
            a,b=next((a,b) for a,b in zip(profiles,profiles[1:]) if a[0]<=x<=b[0])
            u=(x-a[0])/(b[0]-a[0])
            return [a[i]*(1-u)+b[i]*u for i in range(1,4)]
        for x in (2.50,3.00,3.50,4.02):
            w,h,bottom=nose_profile(x);r=.46
            row=[]
            for i in range(19):
                y=w*.43*(i/9-1)
                edge=max(0,abs(y)-(w/2-r))
                z=bottom+h-r+math.sqrt(max(0,r*r-edge*edge))+.038
                row.append((x,y,z))
            rings.append(row)
        verts=sum(rings,[]);faces=[]
        for j in range(3):
            for i in range(18):
                q=j*19+i;faces.append((q,q+1,q+20,q+19))
        objects.append(B._finish(name+' panoramic windshield',verts,faces,None,glass,smooth=True))
        objects.append(B.beam(name+' windshield centre',(2.50,0,3.14),(4.02,0,2.38),.025,.025,None,metal))
        for side in (-1,1):
            objects.append(B.beam(name+' lamp surround',(4.30,side*1.07,1.05),(4.93,side*.78,.90),.13,.09,None,dark))
            objects.append(B.beam(name+' headlight',(4.31,side*1.09,1.06),(4.92,side*.80,.91),.065,.048,None,tail if rear else head))
        objects.append(box(name+' nose service cover',(.16,.46,.25),(5.45,0,.72),trim,.06))
    joined=B.join_materials(name,objects,skip_prefixes=())
    anchor=B.empty(name,(0,0,0))
    for obj in joined:obj.parent=anchor
    return anchor

for i in range(5):
    car=carriage(['MetroCabFront','MetroCoach01','MetroCoach02','MetroCoach03','MetroCabRear'][i],i in (0,4),i==4)
    car.location.x=-i*9.45
    if i==4:car.rotation_euler.z=math.pi
bpy.ops.file.pack_all()
B.save_blend(str(ROOT/'assets/vehicles/future_metro.blend'))
B.export_glb(str(ROOT/'assets/vehicles/future_metro.glb'))
print('FUTURE METRO COMPLETE')
