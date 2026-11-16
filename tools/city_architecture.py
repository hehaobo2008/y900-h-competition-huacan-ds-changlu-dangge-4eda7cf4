"""Massing, ribbon windows and street arcades for the rain sequence (Blender metres)."""
import math
import random
import blib as B
from model_craft import Batch


def footprint(x, y, width, depth, radius):
    a,b = width/2,depth/2
    r = min(radius,a*.90,b*.90)
    outline = []
    for cx,cy,start in ((a-r,b-r,0),(-a+r,b-r,90),(-a+r,-b+r,180),(a-r,-b+r,270)):
        for j in range(5):
            angle = math.radians(start+22.5*j)
            outline.append((x+cx+r*math.cos(angle),y+cy+r*math.sin(angle)))
    return outline


def level(batch, outline, bottom, top, color):
    rings=[[(x,y,z) for x,y in outline] for z in (bottom,top)]
    batch.rings(rings,color,False,caps=False)
    batch.panel(rings[-1],color)


def panes(batch, outline, z, height, rng, style, floor):
    # Glazing sits in a continuous pressure-plate frame. Corner lights wrap with the glass.
    for j, a in enumerate(outline):
        b = outline[(j+1) % len(outline)]
        dx,dy = b[0]-a[0], b[1]-a[1]
        length = math.hypot(dx,dy)
        normal = (dy/length, -dx/length)
        bays = max(1, round(length/(3.2 if style == "res" else 3.8)))
        run = rng.randrange(11)
        for k in range(bays):
            def pt(f,h,offset=.095):
                return (a[0]+dx*(k+f)/bays+normal[0]*offset,
                        a[1]+dy*(k+f)/bays+normal[1]*offset,z+h)
            light = (k//(2 if style=="res" else 3)+run)%11
            shade = (.48*normal[0]+.59*normal[1]+math.sin((floor+j*.15)*.35)*.21)
            cold = "#526c80" if shade>.35 else "#394e65" if shade<-.35 else "#465e73"
            tone = ("#ccaf86" if light==0 else "#a18f7f" if light==1 else cold)
            gap=min(.12,.085/(length/bays))
            batch.panel([pt(gap,0),pt(1-gap,0),pt(1-gap,height),pt(gap,height)],tone)
            if length/bays < 1.3: continue
            # Extruded edge reveal and sill keep depth legible at oblique angles.
            batch.panel([pt(gap,0,.31),pt(gap,0),pt(gap,height),pt(gap,height,.31)],"#687782")
            batch.panel([pt(0,0,.32),pt(1,0,.32),pt(1,0),pt(0,0)],"#89949b")
            if style=="res":
                batch.panel([pt(.58,0,.16),pt(.62,0,.16),pt(.62,height,.16),pt(.58,height,.16)],"#53606b")
                if (k+run)%4==0:
                    blind=height*(.49 if (k+floor)%2 else .74)
                    batch.panel([pt(gap,blind,.13),pt(.58,blind,.13),pt(.58,height,.13),pt(gap,height,.13)],"#868584")
            elif style=="grid" and k%2==0:
                batch.panel([pt(.96,0,.44),pt(1,0,.44),pt(1,height,.44),pt(.96,height,.44)],"#8d999f")


def building(x,y,w,d,h,style,seed,far=False):
    rng = random.Random(seed)
    masonry,windows = Batch(),Batch()
    base = {"res":"#696d78","grid":"#58697b","glass":"#485e75","step":"#62677b"}[style]
    trim = {"res":"#979086","grid":"#93898c","glass":"#758d98","step":"#a18f88"}[style]
    if far:
        tiers = [(0,.71,1),(.71,.90,.82),(.90,1,.54)]
    else:
        tiers = {"res":[(0,.59,1),(.59,.82,.88),(.82,1,.67)],
                 "glass":[(0,.64,1),(.64,.85,.94),(.85,.955,.79),(.955,1,.60)],
                 "step":[(0,.38,1),(.38,.63,.82),(.63,.83,.65),(.83,1,.48)],
                 "grid":[(0,.74,1),(.74,.93,.82),(.93,1,.62)]}[style]
    podium = 5.5 if far else 8.1
    def ring(cx,cy,ww,dd):
        return footprint(cx,cy,ww,dd,min(ww,dd)*(.39 if style=="glass" else .22 if style=="res" else .15))
    street = ring(x,y,w+3.6,d+3.6)
    level(masonry,street,.12,podium,"#596372")
    panes(windows,street,.68,podium*.69,rng,"grid",0)
    level(masonry,ring(x,y,w+5,d+5),podium-.55,podium-.20,trim)
    for index,(start,end,scale) in enumerate(tiers):
        cx=x+(1-scale)*w*(.27 if seed%2 else -.24)
        cy=y+(1-scale)*d*(.21 if seed%3 else -.27)
        a,b=podium+(h-podium)*start,podium+(h-podium)*end
        ww,dd=w*scale,d*scale
        shape=ring(cx,cy,ww,dd)
        level(masonry,shape,a,b-.55,base)
        over=ring(cx,cy,ww+.61,dd+.61)
        level(masonry,over,b-.55,b,trim)
        count=max(1,round((b-a)/(5.8 if far else 3.7)))
        story=(b-a)/count
        for f in range(count):
            sill=a+f*story+.70
            panes(windows,shape,sill,min((story-.98)*.86,2.65),rng,style,f)
            if not far and (f%3==1 if style=="res" else f%5==2):
                level(masonry,over,sill-.48,sill-.26,trim)
        if style=="glass" and not far:
            for j in (1,3,6,8,11,13,16,18):
                px,py=shape[j]
                masonry.rod((px,py,a),(px,py,b),.14,trim,6)
    if style in ("grid","step"):
        crown=ring(cx,cy,ww*.66,dd*.73)
        level(masonry,crown,h,h+2.1,base)
        masonry.rod((cx,cy,h+2.1),(cx,cy,h+5.5),.16,trim,6)
    if not far:
        facade_details(masonry, x, y, w, d, podium, podium+(h-podium)*tiers[0][1], style, seed)
        roof_details(masonry, cx, cy, ww, dd, h, style)
    result=[masonry.object("Terraced skyline masonry",B.vmat("City facades",.78)),
            windows.object("Ribbon glazing and curtains",B.vmat("City window colour",.40,.14))]
    return result


def facade_details(batch,x,y,w,d,podium,first_setback,style,seed):
    # Give the four kinds of tower different occupations at pedestrian height.
    street = 1 if x<0 else -1
    face=x+street*(w+3.6)/2
    for k in (-1,0,1):
        cy=y+k*min(4,d*.17)
        batch.box((face+street*.21,cy,2.17),(.42,3.08,4.06),"#354655")
        for offset in (-1.24,0,1.24):
            batch.box((face+street*.45,cy+offset,2.14),(.13,.13,3.87),"#a29175")
        batch.box((face+street*.48,cy,3.54),(.15,2.64,.14),"#c8b393")
    batch.box((face+street*1.15,y,4.48),(2.55,min(d*.78,14.0),.36),"#626d72")
    for side in (-1,1):
        cy=y+side*min(d*.35,6.2)
        batch.rod((face+street*2.12,cy,.2),(face+street*2.12,cy,4.36),.15,"#8d8175",8)
    if style in ("res","step"):
        for floor in range(3,9,2):
            z=podium+floor*3.7
            if z+1.2>=first_setback: break
            cy=y+(.16 if seed%2 else -.16)*d
            edge=x+street*w*.5
            batch.box((edge+street*.61,cy,z),(1.46,5.3,.24),"#9b9189")
            for off in (-2.45,-1.21,0,1.21,2.45):
                batch.rod((edge+street*1.22,cy+off,z+.12),(edge+street*1.22,cy+off,z+1.15),.049,"#81878a",6)
            batch.rod((edge+street*1.22,cy-2.55,z+1.15),(edge+street*1.22,cy+2.55,z+1.15),.073,"#b6aaa0",8)
            batch.box((edge+street*.62,cy+1.3,z+.33),(.76,1.67,.4),"#776d63")
            batch.box((edge+street*.64,cy+1.33,z+.60),(.69,1.53,.23),"#657965")


def roof_details(batch,cx,cy,w,d,h,style):
    # Anchor equipment, parapets and maintenance doors to the last setback.
    outline=footprint(cx,cy,w-.38,d-.38,min(w,d)*(.36 if style=="glass" else .16))
    for a,b in zip(outline,outline[1:]+outline[:1]):
        batch.rod((*a,h+.28),(*b,h+.28),.16,"#95999a",6)
    deck=h+(2.1 if style in ("grid","step") else 0)
    batch.box((cx,cy,deck+.88),(w*.37,d*.42,1.76),"#77828a")
    batch.box((cx,cy,deck+1.88),(w*.40,d*.45,.22),"#a99f91")
    for k in range(5):
        batch.box((cx,cy-d*.214,deck+.45+k*.22),(w*.25,.12,.092),"#444e59")
    ux=cx+w*.20
    for j in (-1,1):
        uy=cy+j*d*.115
        batch.box((ux,uy,deck+.41),(1.24,1.4,.82),"#868c8c")
        batch.rod((ux,uy,deck+.82),(ux,uy,deck+.99),.45,"#46555e",12)
        for a in (0,math.pi/3,2*math.pi/3):
            dx,dy=.38*math.cos(a),.38*math.sin(a)
            batch.rod((ux-dx,uy-dy,deck+1.01),(ux+dx,uy+dy,deck+1.01),.045,"#a5aa9f",5)


def noodle_corner():
    masonry,glass=Batch(),Batch()
    outline=footprint(19,-18,11.8,14,3.9)
    level(masonry,outline,.12,15.6,"#687583")
    rng=random.Random(37)
    for i in range(3):
        z=4.58+3.60*i
        panes(glass,outline,z,2.46,rng,"res",i)
        level(masonry,footprint(19,-18,12.8,15,4.2),z-.54,z-.22,"#b2a18b")
    level(masonry,footprint(19,-18,12.8,15,4.2),15.3,15.72,"#b5a98e")
    level(masonry,footprint(19.8,-18.4,8.1,10.2,2.9),15.72,17.28,"#737e80")
    for y in (-21.0,-15.0):
        masonry.rod((10.80,y,.17),(10.80,y,3.73),.18,"#948673",10)
    masonry.box((12.45,-18,3.79),(4.0,8.32,.35),"#778281")
    for y in (-21.86,-14.14):
        masonry.box((12.28,y,1.92),(3.62,.19,3.55),"#8c827b")
        for z in (.56,.71,3.26): masonry.box((12.26,y,z),(3.68,.23,.12),"#b09d81")
    for i in range(4):
        y=-23.3+i*3.23
        masonry.rod((13.15,y,.18),(13.15,y,3.64),.092,"#79654e",8)
    masonry.pipe([(14.13,-24.30,14.89),(14.13,-24.30,4.04),(13.81,-24.30,3.83),(13.81,-24.30,.20)],.089,"#9b847c",8)
    return [masonry.object("Rounded corner apartments and shop arcade",B.vmat("City facades",.78)),
            glass.object("Corner bay windows",B.vmat("City window colour",.40,.14))]
