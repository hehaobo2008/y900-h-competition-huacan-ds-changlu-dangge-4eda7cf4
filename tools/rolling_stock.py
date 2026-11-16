"""Six-car EMU with two lofted cabs, wraparound windscreens and running gear."""
import math
from pathlib import Path
import bpy
import blib as B
from model_craft import Batch


def build_train():
    B.reset(2021)
    shell = B.vmat("EMU_enamel",.31,.20)
    glazing = B.vmat("EMU_laminated_glass",.15,.42)
    alloy = B.vmat("EMU_machined_alloy",.40,.63)
    polymer = B.vmat("EMU_rubber",.82)
    light = B.mat("EMU_headlight","#fff2cf",emission="#ffebbe",emis_strength=1.35)
    body,glass,metal,rubber,lamps = Batch(),Batch(),Batch(),Batch(),Batch()
    half = 12.34
    for i in range(6):
        cy = -62.5+25*i
        facing = -1 if i==0 else 1
        cab = i in (0,5)
        def skin(y, a, lift=0):
            # d is the distance behind the tip. The low chine reaches its full
            # width before the windscreen rises into the roof.
            d = half-facing*(y-cy)
            def ease(v):
                v = max(0,min(v,1))
                return v*v*(3-2*v)
            w = 1.63 if not cab else .13+1.50*ease((d+.52)/5.7)
            top = 3.84 if not cab else 1.12+2.72*ease((d+.15)/8.4)
            bottom = .67 if not cab else .67+.29*(1-ease(d/4))
            co,si = math.cos(a),math.sin(a)
            def power(v,n): return math.copysign(abs(v)**n,v)
            x = (w+lift)*power(co,.56)
            z = (top+bottom)/2 + ((top-bottom)/2+lift)*power(si,.67)
            return (x,y,z)
        def strip(batch, y0,y1, a0,a1, color, lift=.018, lengths=14, widths=2):
            pts,faces = [],[]
            for k in range(lengths+1):
                y = y0+(y1-y0)*k/lengths
                for j in range(widths+1):
                    pts.append(skin(y,a0+(a1-a0)*j/widths,lift))
            for k in range(lengths):
                for j in range(widths):
                    a=k*(widths+1)+j
                    faces.append((a,a+widths+1,a+widths+2,a+1))
            batch.part(pts,faces,color,True)
        ring_count = 48
        n_sections = 58 if cab else 12
        rings = [[skin(cy-half+2*half*k/n_sections,-math.tau*j/ring_count)
                  for j in range(ring_count)] for k in range(n_sections+1)]
        body.rings(rings,"#e3e8e4")
        straight = cy + facing*(half-7.7)
        ylo,yhi = cy-half+.38,cy+half-.38
        if cab and facing==1: yhi=straight
        if cab and facing==-1: ylo=straight
        for side in (-1,1):
            def angle(a): return a if side>0 else math.pi-a
            strip(body,cy-half+.08,cy+half-.08,angle(-.57),angle(-.34),"#5c747e")
            strip(body,cy-half+.12,cy+half-.12,angle(-.265),angle(-.19),"#aa4936",.022)
            strip(glass,ylo,yhi,angle(.035),angle(.38),"#243a48",.021)
            # Separate glazing units have a rubber reveal, a sky reflection
            # near the top and a fine centre divider.
            count = 6 if cab else 9
            lo,hi=ylo+1.35,yhi-1.35
            for k in range(count):
                mid=lo+(k+.5)*(hi-lo)/count
                for a,b,c in [(.069,.329,"#435f6e"),(.252,.305,"#64828a")]:
                    strip(glass,mid-.63,mid+.63,angle(a),angle(b),c,.034,2,2)
            for y in ([cy-facing*10.4] if cab else [cy-10.4,cy+10.4]):
                for off in (-.51,.51):
                    strip(body,y+off-.012,y+off+.012,angle(-.50),angle(.43),"#52666b",.036,1,8)
                strip(glass,y-.30,y+.30,angle(.075),angle(.32),"#253d48",.047,1,3)
                metal.box((side*1.61,y+.27,1.9),(.065,.22,.035),"#8a9695")
            if cab:
                # Narrow swept-back headlights follow the nose surface.
                for a,b,c,layer in [(-.13,.20,"#273a45",glass),(.025,.14,"#f7ebc7",lamps)]:
                    strip(layer,cy+facing*(half-1.7),cy+facing*(half-3.05),
                          angle(a),angle(b),c,.030 if layer is glass else .044,12,3)
        if cab:
            pts,faces=[],[]
            for k in range(11):
                u=k/10
                for j in range(33):
                    t=j/32
                    a=math.radians(23+134*t)
                    d=3.4+2.0*u+1.15*abs(2*t-1)**2
                    pts.append(skin(cy+facing*(half-d),a,.031))
            for k in range(10):
                for j in range(32):
                    a=k*33+j
                    faces.append((a,a+1,a+34,a+33))
            glass.part(pts,faces,"#233b48",True)
            for a in (.98,2.16):
                metal.rod(skin(cy+facing*(half-3.70),a,.05),skin(cy+facing*(half-4.55),a+.19,.05),.023,"#1d272a")
        for by in (cy-8.45,cy+8.45):
            if cab and (by-cy)*facing>0: by-=facing*1.75
            rubber.box((0,by,.65),(2.08,3.5,.38),"#384247")
            for yy in (by-.98,by+.98):
                metal.rod((-.88,yy,.435),(.88,yy,.435),.105,"#666f70")
                for s in (-1,1):
                    rubber.rod((s*.73,yy,.435),(s*.90,yy,.435),.435,"#353c3d",20)
                    metal.rod((s*.89,yy,.435),(s*.95,yy,.435),.33,"#7a8382",20)
                    metal.rod((s*.94,yy,.435),(s*1.01,yy,.435),.13,"#414a49",12)
        acy = cy-facing*3 if cab else cy
        body.box((0,acy,3.90),(1.62,3.45,.20),"#b9c3c2")
        for k in range(16): metal.box((0,acy-1.44+k*.19,4.01),(1.36,.044,.025),"#536970")
        if i<5:
            for k in range(5):
                rubber.box((0,cy+half+.035+k*.065,2.16),(2.71-(k%2)*.10,.061,2.75),"#353e40")
    for cy in (-37.5,37.5):
        for x in (-.51,.51):
            metal.pipe([(x,cy-1.1,4.05),(x,cy+.8,4.98),(x,cy-.33,6.0)],.045,"#38474d")
            metal.pipe([(x,cy+.82,4.05),(x,cy-.55,4.82),(x,cy-.33,6.0)],.032,"#52636a")
        metal.rod((-.95,cy-.33,6.0),(.95,cy-.33,6.0),.048,"#4c514c")
    for batch,name,material in [(body,"Coach shells and livery",shell),(glass,"Cab and coach glazing",glazing),
                                 (metal,"Running gear and current collectors",alloy),
                                 (rubber,"Gangways and bogies",polymer),(lamps,"Cab lamps",light)]:
        batch.object(name,material)
    out=Path(B.ROOT)/"assets"/"vehicles"
    B.save_blend(str(out/"hsr.blend"))
    B.export_glb(str(out/"hsr.glb"))
