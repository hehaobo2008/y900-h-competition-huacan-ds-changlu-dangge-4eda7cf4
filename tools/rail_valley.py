"""The two bores and the terrain above them, in Blender coordinates."""
import math
import random
import blib as B
from model_craft import Batch

MOUTH, EDGE, RADIUS, SPRING, INVERT = 108, 150, 6.9, 36.1, 31.5


def ease(lo, hi, value):
    t = max(0, min(1, (value-lo)/(hi-lo)))
    return t*t*(3-2*t)


def ground(base, x, y, covered=None):
    natural=base(x,y)
    covered=abs(y)>=MOUTH if covered is None else covered
    depth=max(0,abs(y)-MOUTH)
    crest=46.7+5.4*ease(0,18,depth)+1.7*math.sin(x*.19+depth*.11)+.9*math.cos(y*.13-x*.23)
    weight=1-ease(7,32,abs(x-1.1*math.sin(y*.16)))
    rise=weight*max(0,crest-natural)
    apron=ease(MOUTH-22,MOUTH,abs(y))*ease(8.1,19,abs(x))
    return natural+rise*(1 if covered else apron)


def terrain(base, material):
    # Separate the vertices on the two sides of each mouth. The discontinuity
    # is filled by the actual headwall. The rest of the island is one heightfield.
    vertices, faces, colors, indices=[],[],[],{}
    dark,light=B.srgb("#435e54"),B.srgb("#939482")
    def vertex(x,y,covered):
        step=covered and abs(y)==MOUTH and abs(x)<34
        key=(x,y,step)
        if key not in indices:
            indices[key]=len(vertices)
            vertices.append((x,y,ground(base,x,y,covered)))
        return indices[key]
    def face(ids,color):
        faces.append(tuple(ids));colors.append(color)
    for y in range(-EDGE,EDGE,2):
        covered=abs(y+1)>MOUTH
        for x in range(-160,160,2):
            q=[vertex(a,b,covered) for a,b in ((x,y),(x+2,y),(x+2,y+2),(x,y+2))]
            z=vertices[q[0]][2]
            shade=min(1,.20+z/100+.15*math.sin(x*.067+y*.12)+.08*math.sin(y*.34))
            face(q,B.mix(dark,light,shade) if z>1 else B.srgb("#817c65"))
    perimeter=([(x,-EDGE) for x in range(-160,160,2)]+[(160,y) for y in range(-EDGE,EDGE,2)]
               +[(x,EDGE) for x in range(160,-160,-2)]+[(-160,y) for y in range(EDGE,-EDGE,-2)])
    for (x,y),(a,b) in zip(perimeter,perimeter[1:]+perimeter[:1]):
        i,j=vertex(x,y,abs(y)>=MOUTH),vertex(a,b,abs(b)>=MOUTH)
        k=len(vertices); vertices.extend([(x,y,-.08),(a,b,-.08)])
        face((j,i,k,k+1),B.srgb("#748173"))
    return B._finish("Valley terrain and cut edges",vertices,faces,None,material,face_colors=colors,smooth=True)


def portals(base, stone_mat, rock_mat, metal_mat):
    fill, stone, fixtures, liner=Batch(),Batch(),Batch(),Batch()
    colors=["#a8a297","#b6b0a1","#aaa799","#b9b4a7","#afaa9c"]
    for side in (-1,1):
        def p(x,depth,z): return (x,side*(MOUTH+depth),z)
        def arch(a,r): return r*math.cos(a),SPRING+r*math.sin(a)
        def curve(r):
            return [(-r,INVERT)]+[arch(math.pi*(1-i/32),r) for i in range(33)]+[(r,INVERT)]
        def strip(batch,a,da,b,db,color):
            for (ax,az),(bx,bz),(cx,cz),(dx,dz) in zip(a,a[1:],b,b[1:]):
                batch.panel([p(ax,da,az),p(bx,da,bz),p(dx,db,dz),p(cx,db,cz)],color)
        def front_height(x,upper):
            left=2*math.floor(x/2);f=(x-left)/2
            return (1-f)*ground(base,left,side*MOUTH,upper)+f*ground(base,left+2,side*MOUTH,upper)
        # Follow the exact terrain edge grid, with extra abscissae at each arch joint.
        xs=sorted(set([*range(-34,35,2),-RADIUS,RADIUS]+[x for x,_ in curve(RADIUS)]))
        for x,nx in zip(xs,xs[1:]):
            if nx-x<.0001: continue
            opening=abs((x+nx)/2)<RADIUS
            def sill(a):
                return SPRING+math.sqrt(max(0,RADIUS**2-a*a)) if opening else front_height(a,False)
            z0,z1=sill(x),sill(nx)
            t0,t1=front_height(x,True),front_height(nx,True)
            if max(t0-z0,t1-z1)>.001:
                # A rock band and a darker layer of earth beneath the grassy lip.
                middle=lambda z,t: z+(t-z)*.74
                for a,b,c,d,col in [(z0,z1,middle(z0,t0),middle(z1,t1),"#828477"),
                                    (middle(z0,t0),middle(z1,t1),t0,t1,"#74826a")]:
                    fill.panel([p(x,0,a),p(nx,0,b),p(nx,0,d),p(x,0,c)],col)
            if opening:
                fill.panel([p(x,0,front_height(x,False)),p(nx,0,front_height(nx,False)),
                            p(nx,0,INVERT),p(x,0,INVERT)],"#797a6e")
        inner,outer=curve(RADIUS),curve(RADIUS+.93)
        # Add the dressed front between the ring and the overlying south/north bank.
        head_top=44.75
        for (x,z),(nx,nz) in zip([(-9.35,INVERT),*outer],[*outer,(9.35,INVERT)]):
            if nx-x<.001: continue
            stone.panel([p(x,-.29,z),p(nx,-.29,nz),p(nx,-.29,head_top),p(x,-.29,head_top)],"#98998b")
        for hand in (-1,1):
            for row in range(8):
                stone.box(p(hand*8.59,-.32,INVERT+.82+row*1.6),(1.42,.15,1.55),colors[(row+side)%5])
            fixtures.box(p(hand*8.55,-.44,39.1),(.26,.12,.31),"#505b54")
        for i in range(11):
            stone.box(p((i-5)*1.71,-.17,head_top+.17),(1.69,.95,.34),colors[(i+2)%5])
        strip(stone,outer,-.44,inner,-.44,"#696d66")
        strip(stone,outer,-.44,outer,.12,"#8b9182")
        for d0,d1,col in [(-.62,1,"#686e69"),(1,4,"#555e59"),(4,10,"#384342"),(10,19,"#293536"),(19,34,"#172326")]:
            strip(liner,inner,d0,inner,d1,col)
        n=23
        for k in range(n):
            lo=math.pi*k/n+.0035; hi=math.pi*(k+1)/n-.0035
            top=RADIUS+(1.20 if k==n//2 else .93)
            outline=[arch(lo,RADIUS),arch(hi,RADIUS),arch(hi,top),arch(lo,top)]
            stone.rings([[p(x,d,z) for x,z in outline] for d in (-.67,-.45)],colors[(k+side)%len(colors)],False)
        for hand in (-1,1):
            for row in range(4):
                h=(SPRING-INVERT)/4
                stone.box(p(hand*(RADIUS+.46),-.36,INVERT+(row+.5)*h),(.89,.62,h-.04),colors[row])
            for d in (2.5,9,16.5,24):
                fixtures.box(p(hand*(RADIUS-.14),d,36.05),(.18,.9,.40),"#404d50")
                fixtures.box(p(hand*(RADIUS-.25),d,36.04),(.07,.65,.17),"#e6caa0")
            # The flared wings run into the slope all the way down to their footings.
            for d0,d1 in [(-8,-5),(-5,-2),(-2,.15)]:
                ring=[]
                for d in (d0,d1):
                    x=hand*(8.02-d*.48);bottom=base(x,side*(MOUTH+d))-.25
                    top=37.8+d*.48
                    ring.append([p(x,d,bottom),p(x+hand*.78,d,bottom),p(x+hand*.59,d,top),p(x,d,top)])
                stone.rings(ring,"#898d80",False)
            stone.box(p(hand*5.96,16.5,32.95),(1.1,34.1,.34),"#777b70")
        liner.box(p(0,16.6,INVERT-.23),(RADIUS*2,34.6,.46),"#263134")
        liner.panel([p(x,34,z) for x,z in inner],"#121b21")
    return [fill.object("Excavated headwalls",rock_mat),stone.object("Masonry portal voussoirs",stone_mat),
            fixtures.object("Tunnel inspection fittings",metal_mat),liner.object("Arched tunnel linings",rock_mat)]


def bank_woodland(base, shore):
    from planted_trees import plant
    rng=random.Random(8217)
    occupied=[]
    for _ in range(1950):
        x,y=rng.uniform(-156,156),rng.uniform(-147,147);bank=abs(y-shore(x))
        if bank<39.2 or (abs(x)<9.5 and abs(y)<MOUTH+3): continue
        if MOUTH-12<abs(y)<MOUTH+2 and abs(x)<16: continue
        if any(math.hypot(x-a,y-b)<9 for a,b in [(-52,-72),(-38,-80),(-66,-84),(54,-76)]): continue
        density=math.sin(.087*x+.9*math.cos(.061*y))+math.cos(.136*y-.06*x)
        if density<-.27 or (density<.57 and rng.random()<.57):continue
        if any((x-a)**2+(y-b)**2<22 for a,b in occupied): continue
        occupied.append((x,y))
        z=ground(base,x,y)-.09
        h=rng.uniform(6.0,12.3)*(1.16 if density>.9 else .88)
        family="pine" if bank>60 and rng.random()<.76 else "river"
        plant(family,x,y,z,h,h*rng.uniform(.36,.55) if family=="pine" else h*rng.uniform(.65,.88))

