"""Draw the edition's original botanical cutouts and diegetic sign lettering."""
import math
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parents[1]/"assets"/"textures"
OUT.mkdir(parents=True,exist_ok=True)
rng = random.Random(1983)


def spray():
    im = Image.new("RGBA",(512,512))
    d = ImageDraw.Draw(im)
    def branch(x,y,angle,length,depth):
        bend = rng.uniform(-.28,.28)
        tip = (x+length*math.cos(angle+bend),y+length*math.sin(angle+bend))
        d.line([(x,y),tip],fill=(97,86,56,255),width=depth*2+1)
        for j in range(1,8):
            u=j/8
            px=x+(tip[0]-x)*u
            py=y+(tip[1]-y)*u
            for s in (-1,1):
                a=angle+s*rng.uniform(.48,1.18)
                if depth>0 and j in (2,4,6):
                    branch(px,py,a,length*rng.uniform(.33,.49),depth-1)
                else:
                    l=rng.uniform(14,31)*(1.12-.28*u)
                    w=l*rng.uniform(.18,.28)
                    vx,vy=math.cos(a),math.sin(a)
                    q=(px+vx*l*.5,py+vy*l*.5)
                    end=(px+vx*l,py+vy*l)
                    c=rng.choice([(73,98,58),(104,124,72),(124,139,80),(89,118,71),(149,154,89),(108,131,76)])
                    d.polygon([(px,py),(q[0]-vy*w,q[1]+vx*w),end,(q[0]+vy*w*.88,q[1]-vx*w*.88)],fill=c+(255,))
                    d.line([(px,py),end],fill=tuple(min(255,n+22) for n in c)+(255,),width=1)
    for ang in (-2.42,-2.06,-1.71,-1.43,-1.10,-.76):
        branch(254+rng.uniform(-9,9),485,ang,rng.uniform(204,273),2)
    im.save(OUT/"leaf_spray.png",optimize=True)


def rice():
    im=Image.new("RGBA",(384,384))
    d=ImageDraw.Draw(im)
    for k in range(34):
        bx,by=rng.randint(0,383),rng.randint(355,394)
        h=rng.randint(158,325)
        lean=rng.uniform(-54,66)
        end=(bx+lean,by-h)
        c=rng.choice([(165,152,72),(190,168,79),(155,151,69),(194,171,93)])
        d.line([(bx,by),(bx+lean*.24,by-h*.58),end],fill=c+(255,),width=2)
        for s in (-1,1):
            root=(bx+lean*.17,by-h*rng.uniform(.18,.39))
            d.polygon([root,(root[0]+s*12,root[1]-38),(root[0]+s*rng.randint(23,56),root[1]-rng.randint(62,118)),(root[0]+s*6,root[1]-32)],fill=rng.choice([(137,144,67),(164,155,73),(179,170,89)])+(255,))
        side=1 if lean>0 else -1
        last=end
        for j in range(10):
            t=(j+1)/10
            tip=(end[0]+side*32*t,end[1]-14*math.sin(math.pi*t)+22*t*t)
            d.line([last,tip],fill=(178,145,66,255),width=2)
            for s in (-1,1):
                x,y=tip[0]+s*3,tip[1]+j*.55
                d.ellipse([x-2,y-1,x+2,y+6],fill=rng.choice([(212,176,89),(230,198,115),(183,151,71)])+(255,))
            last=tip
    im.save(OUT/"rice_panicles.png",optimize=True)


def signs():
    width,height=1024,512
    im=Image.new("RGB",(width*2,height*2))
    def font(size,serif=False):
        options=(["C:/Windows/Fonts/simsun.ttc","/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc"] if serif else
                 ["C:/Windows/Fonts/msyhbd.ttc","/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"])
        return ImageFont.truetype(next(p for p in options if Path(p).exists()),size)
    panels=[
        ("村口粮站","晚稻收储","净谷过秤　•　晒场交接","仓 字　〇 三", "#ded0a6","#463e2d","#954c35"),
        ("山河邮电","报刊零售亭","早报　　画报　　文学月刊","零 售　〇 二", "#284d49","#e0cd9d","#bc9b65"),
        ("长路里","末班列车","雨夜候车　　请循阶上桥","东 口　〇 一", "#183b46","#c7ded7","#d38d67"),
        ("星 河 港","发射勤务区","低温推进剂　/　输送廊","PAD    05", "#c9d5d1","#243e46","#9f4937")]
    for i,(small,title,sub,code,bg,ink,accent) in enumerate(panels):
        tile=Image.new("RGB",(width,height),bg); d=ImageDraw.Draw(tile)
        d.rectangle((16,16,width-17,height-17),outline=ink,width=4)
        d.rectangle((27,27,width-28,height-28),outline=accent,width=2)
        d.text((54,41),small,font=font(40,True),fill=ink)
        d.text((968,49),code,font=font(30),fill=accent,anchor="ra")
        d.line((54,116,970,116),fill=accent,width=4)
        from make_signs import BRUSH, SHOP, SANS, font as lettering
        title_face = lettering(139, (BRUSH,SHOP,SANS,SANS)[i])
        d.text((511,251),title,font=title_face,fill=accent,anchor="mm")
        d.text((508,248),title,font=title_face,fill=ink,anchor="mm")
        d.line((54,363,970,363),fill=accent,width=2)
        d.text((510,423),sub,font=font(41),fill=ink,anchor="mm")
        for x in (39,985):
            for y in (39,473): d.ellipse((x-4,y-4,x+4,y+4),fill=accent)
        im.paste(tile,((i%2)*width,(i//2)*height))
    im.save(OUT/"workshop_print.jpg",quality=91,subsampling=0)


if __name__=="__main__":
    spray(); rice(); signs()
