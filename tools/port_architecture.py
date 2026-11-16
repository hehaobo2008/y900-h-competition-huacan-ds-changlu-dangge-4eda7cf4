"""Architecture of the coastal research district. All dimensions are in metres."""
import math
import blib as B
from model_craft import Batch
from city_architecture import footprint

PORCELAIN = "#c3c6b9"
SHADE = "#7d9999"
BRONZE = "#957d62"
REVEAL = "#384e54"
PANE = "#446c75"
WARM = "#bba78b"


def between(a,b,t):
    return tuple(u+(v-u)*t for u,v in zip(a,b))


def deck(shell,x,y,w,d,z,thick,color,r=1.2):
    shape=footprint(x,y,w,d,r)
    shell.rings([[(a,b,z-thick) for a,b in shape],[(a,b,z) for a,b in shape]],color,False)


def solar_roof(shell,x,y,w,d,z):
    # Tilted south-facing photovoltaic tables on raised kerbs with walkways between rows.
    for j in range(max(1,int(d/3.7))):
        cy=y-d*.5+2+j*3.7
        for k in range(max(1,int(w/3.3))):
            cx=x-w*.5+1.8+k*3.3
            shell.box((cx,cy,z+.32),(.4,1.0,.64),SHADE)
            pts=[(cx-1.48,cy-1.26,z+.40),(cx+1.48,cy-1.26,z+.40),
                 (cx+1.48,cy+1.26,z+.96),(cx-1.48,cy+1.26,z+.96)]
            shell.panel(pts,"#384f5c")
            shell.rod(pts[2],pts[3],.045,SHADE,5)


def research(shell,glass,x,y,w,d,height,lean,base,spacing):
    # Two continuous, tapered wings. A sloping crown conceals their plant floors.
    count=round(height/3.8)
    shapes=[]
    for n in range(count+1):
        t=n/count
        cx=x+lean*t*t
        s=1-.23*t*t
        shape=footprint(cx,y,w*s,d*(1-.14*t),min(w,d)*.28*s)
        shapes.append([(a,b,base+t*height+max(0,(t-.78)/.22)*(a-cx)/w*8) for a,b in shape])
    for f,(lower,upper) in enumerate(zip(shapes,shapes[1:])):
        for j,a in enumerate(lower):
            k=(j+1)%len(lower)
            b,c,e=lower[k],upper[k],upper[j]
            sill1,sill2=between(a,e,.19),between(b,c,.19)
            shell.panel([a,b,sill2,sill1],SHADE if f%5 else PORCELAIN)
            bays=max(1,round(math.dist(a,b)/spacing))
            for m in range(bays):
                left,right=m/bays,(m+1)/bays
                occupied=(f+3*j+m//2)%19==1 and bays>2
                color=WARM if occupied else PANE if j<10 else "#527d84"
                glass.panel([between(sill1,sill2,left),between(sill1,sill2,right),between(e,c,right),between(e,c,left)],color)
                if bays==1 and j%2:continue
                t=m/bays
                p,q=between(a,b,t),between(e,c,t)
                shell.rod(p,q,.17 if m else .27,PORCELAIN,6)
    # Paired exterior braces shade alternating four-storey bays on the sunward side.
    if height>60:
        for first in range(1,count-3,4):
            lower,upper=shapes[first],shapes[first+4]
            for j in (9,19):
                k=(j+1)%len(lower)
                a,b=lower[j],lower[k]
                high_left,high_right=upper[j],upper[k]
                if math.dist(a,b)<3:continue
                for f in (.25,.75):
                    joint=between(high_left,high_right,f)
                    shell.rod(between(a,b,f-.245),joint,.22,PORCELAIN,8)
                    shell.rod(between(a,b,f+.245),joint,.22,PORCELAIN,8)
    cap=shapes[-1]
    shell.panel(cap,PORCELAIN)
    for j,a in enumerate(cap):
        b=cap[(j+1)%len(cap)]
        shell.rod(a,b,.29,PORCELAIN,7)
    deck(shell,x,y,w+2.1,d+2.1,base+.45,.55,PORCELAIN,2)


def planting(shell,x,y,z,width):
    # A low continuous planter with a clipped salt-tolerant hedge.
    shell.box((x,y,z+.25),(width,1.22,.5),BRONZE)
    shape=footprint(x,y,width-.28,1.06,.46)
    shell.rings([[(a,b,z+.46) for a,b in shape],[(a,b,z+.97) for a,b in shape]],"#627c63")


def housing(shell,glass,x,y,w,d,tiers,base):
    # Each upper volume withdraws from the waterfront to create a usable garden, with
    # genuine two-room bays, deep external galleries and a continuous stair core.
    for i,n in enumerate(tiers):
        depth=d-i*2.7
        cy=y+i*1.35
        width=w-i*1.35
        floor_h=3.22
        h=n*floor_h
        front,back=cy-depth/2,cy+depth/2
        shell.box((x,cy,base+h*.5),(width-.92,depth-1.48,h),REVEAL)
        bays=max(3,int(width/3.8))
        pitch=(width-1.55)/bays
        for f in range(n):
            z=base+f*floor_h
            deck(shell,x,cy,width+.30,depth+.30,z+.58,.58,PORCELAIN)
            deck(shell,x,cy,width+.38,depth+.38,z+floor_h,.31,SHADE)
            for k in range(bays):
                xx=x+(k-(bays-1)*.5)*pitch
                color=WARM if (k//2+f+i*3)%8==2 else PANE
                for face,sign in [(front,-1),(back,1)]:
                    yy=face-sign*.48
                    glass.box((xx,yy,z+1.78),(pitch-.26,.16,2.12),color)
                    shell.box((xx+.38,yy+sign*.12,z+1.78),(.12,.16,2.21),REVEAL)
                    shell.box((xx-pitch*.5,face-sign*.22,z+1.69),(.36,.83,2.70),PORCELAIN)
                    if f==0 and i==0:
                        for l in range(3):
                            shell.box((xx-.54+l*.21,face+sign*.13,z+2.18),(.085,.49,1.55),BRONZE)
                if k%3==1:
                    shell.box((xx,front-.77,z+.5),(pitch*1.14,1.53,.21),SHADE)
                    for side in (-1,1):
                        shell.box((xx+side*pitch*.55,front-.76,z+1.08),(.12,1.55,.95),PORCELAIN)
                    shell.box((xx,front-1.48,z+.76),(pitch*1.14,.17,.34),PORCELAIN)
                    shell.box((xx,front-1.48,z+1.53),(pitch*1.14,.11,.12),BRONZE)
                    shell.box((xx,front-1.48,z+1.12),(.075,.10,.66),SHADE)
            for side in (-1,1):
                xx=x+side*(width/2-.24)
                for k in range(max(2,int(depth/4))):
                    yy=cy+(k-(max(2,int(depth/4))-1)*.5)*3.25
                    glass.box((xx,yy,z+1.71),(.15,2.51,2.02),PANE)
                    shell.box((xx+side*.13,yy-1.48,z+1.66),(.55,.62,2.72),PORCELAIN)
                    shell.box((xx+side*.12,yy,z+1.71),(.12,.105,2.15),BRONZE)
        base+=h
        deck(shell,x,cy,width+.7,depth+.65,base+.12,.36,PORCELAIN)
        if i<len(tiers)-1:
            planting(shell,x,front+.62,base+.12,width*.60)
            for sx in (-1,1):
                shell.box((x+sx*width*.38,front+.82,base+.48),(2.15,.5,.46),BRONZE)
        else:
            solar_roof(shell,x,cy,width*.72,depth*.63,base+.15)


def link(shell,glass,x,y1,y2,floor,width):
    # Landings extend into both wings. Guard, glazing and truss share the same bearings.
    long=y2-y1
    shell.box((x,(y1+y2)/2,floor),(width,long,.68),PORCELAIN)
    shell.box((x,(y1+y2)/2,floor+3.55),(width+.36,long,.37),PORCELAIN)
    for side in (-1,1):
        xx=x+side*(width/2-.15)
        glass.box((xx,(y1+y2)/2,floor+1.83),(.15,long,2.98),PANE)
        spans=max(2,round(long/4))
        for i in range(spans):
            a=y1+long*i/spans
            b=y1+long*(i+1)/spans
            shell.rod((xx+side*.12,a,floor+.24),(xx+side*.12,b,floor+3.44),.14,SHADE,6)


def civic(shell,glass,x,y,w,d,base):
    # A shaded ground-floor reading room with a slatted colonnade and a roof garden.
    deck(shell,x,y,w+4,d+4,base+.32,.46,PORCELAIN)
    shell.box((x,y,base+2.61),(w,d,4.65),REVEAL)
    for side in (-1,1):
        yy=y+side*(d/2+.08)
        for k in range(7):
            xx=x+(k-3)*w/7.3
            glass.box((xx,yy,base+2.46),(w/7.3-.14,.15,3.95),PANE if k%3 else WARM)
        for k in range(7):
            xx=x+(k-3)*w/7
            shell.rod((xx,yy+side*1.4,base+.3),(xx,yy+side*1.4,base+5.2),.16,BRONZE,8)
    deck(shell,x,y,w+4.6,d+4.4,base+5.42,.46,PORCELAIN)
    planting(shell,x,y-d*.45,base+5.42,w*.63)
    solar_roof(shell,x,y+.7,w*.63,d*.48,base+5.42)


def waterfront_shelter(shell,x,y,base):
    # A timber reading terrace under a continuous, curved photovoltaic canopy.
    deck(shell,x,y,13.6,6.4,base+.38,.52,PORCELAIN,1.3)
    for dx in (-5.15,0,5.15):
        for dy in (-1.86,1.86):
            shell.rod((x+dx,y+dy,base+.37),(x+dx,y+dy,base+3.76),.15,BRONZE,9)
    roof=[]
    for i in range(17):
        dx=-6.65+i*.83
        z=base+3.74+.55*math.cos(dx*.23)
        roof.append(((x+dx,y-3.0,z),(x+dx,y+3.0,z+.43)))
    for (a,b),(c,d) in zip(roof,roof[1:]):
        shell.panel([a,c,d,b],"#486268")
        shell.rod(a,b,.068,BRONZE,6)
        shell.rod(a,c,.067,PORCELAIN,6)
        shell.rod(b,d,.067,PORCELAIN,6)
    for dx in (-3.5,3.5):
        shell.box((x+dx,y+1.2,base+.75),(4.6,.76,.24),BRONZE)
        for offset in (-1.75,1.75):
            shell.box((x+dx+offset,y+1.2,base+.56),(.24,.71,.4),SHADE)
        shell.box((x+dx,y+1.48,base+1.18),(4.6,.13,.60),BRONZE)
    planting(shell,x,y-2.35,base+.38,7.15)


def install(ground):
    shell,glass=Batch(),Batch()
    def g(x,y):return ground(x,y)-.13
    research(shell,glass,-50,26,20,15,84,-5,g(-50,26),3.6)
    research(shell,glass,-54,47,15,13,65,3,g(-54,47),3.2)
    link(shell,glass,-51,31,43,g(-50,26)+38,3.8)
    research(shell,glass,-18,24,18,13,48,3,g(-18,24),3.7)
    research(shell,glass,-73,0,17,14,58,2.8,g(-73,0),4)
    for x,y,w,d,floors in [(30,-8,17,14,(3,2,2)),(36,15,21,16,(3,2,2,1)),
                            (14,45,20,15,(2,2,2)),(-40,-26,21,13,(3,2,2)),
                            (-105,47,19,13,(2,2,1)),(-125,53,16,12,(2,1)),(38,80,19,13,(2,2))]:
        housing(shell,glass,x,y,w,d,floors,g(x,y))
    for x,y,w,d in [(-17,-27,16,10),(-16,47,20,12),(-128,16,17,10)]:
        civic(shell,glass,x,y,w,d,g(x,y))
    waterfront_shelter(shell,39,-29,g(39,-29))
    shell.object("Coastal district structure and sunshades",B.vmat("Port ceramic, oak and aluminium",.66,.12))
    glass.object("Coastal district glazing",B.vmat("Coastal low emissivity glass",.31,.23))

