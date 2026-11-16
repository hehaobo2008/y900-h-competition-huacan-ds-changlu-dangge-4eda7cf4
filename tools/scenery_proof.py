from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

root=Path(__file__).resolve().parents[1]/"qa/scenery"
paper="#f2ecdf";ink="#332f29";muted="#665d4e"
font=lambda size:ImageFont.truetype("C:/Windows/Fonts/msyh.ttc",size)
serif=lambda size:ImageFont.truetype("C:/Windows/Fonts/simsun.ttc",size)
out=Image.new("RGB",(1550,2063),paper);draw=ImageDraw.Draw(out)
draw.text((38,23),"山河织路　四幕里的树",font=serif(43),fill=ink)
draw.text((40,88),"同一地点、镜头高度与视场角。第一幕沿用原有田埂绘景。",font=font(20),fill=muted)
for x,label in [(40,"改动前"),(790,"本次实景")]:
    draw.text((x,132),label,font=font(23),fill="#994e3d")
rows=[
    ("lane","东街","阔叶街树收在树池里，店面和檐下的视线留给行人。"),
    ("city-trees","雨夜都市","树冠窄而高，从树下能读到站牌和路口信号。"),
    ("river-pines","山河大桥","松树和阔叶树沿坡混植，从侧面可以分辨枝条与后排林冠。"),
    ("port-trees","未来星港","曲干庭树栽进步道的种植池，临水一侧留给行走和登船。")]
for i,(file,name,caption) in enumerate(rows):
    y=180+i*466
    for side,sub in enumerate(("planting-before","planting-after")):
        with Image.open(root/sub/(file+".jpg")) as image:
            out.paste(image.resize((716,419),Image.Resampling.LANCZOS),(40+750*side,y))
    draw.text((41,y+427),name,font=font(21),fill=ink)
    draw.text((188,y+429),caption,font=font(18),fill=muted)
out.save(root/"四幕树木前后对照.jpg",quality=92,subsampling=0)
