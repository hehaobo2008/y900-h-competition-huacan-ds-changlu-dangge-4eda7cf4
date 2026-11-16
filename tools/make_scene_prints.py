"""Prepare cinema bill paintings and the apartment-window atlas for the native models."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from make_signs import BRUSH,SHOP

assets=Path(__file__).resolve().parents[1]/"assets"
source=assets/"sources"/"scene-print"
out=assets/"textures"
with Image.open(source/"cinema.png") as raw:
    sheet=Image.new("RGB",(1272,600))
    for i,(title,fg,bg) in enumerate((("秋信","#fbe8bf","#893e31"),("桥上春风","#fff0b7","#386c66"),("山月行","#fce2b6","#263e59"))):
        w=raw.width//3
        tile=raw.crop((i*w,55,(i+1)*w,raw.height-70)).resize((404,472),Image.Resampling.LANCZOS)
        paper=Image.new("RGB",(424,600),"#e4d7ba")
        paper.paste(tile,(10,10))
        d=ImageDraw.Draw(paper)
        d.rectangle((10,482,413,589),fill=bg)
        d.text((212,519),title,font=ImageFont.truetype(BRUSH,64),anchor="mm",fill=fg)
        d.text((212,568),"山 河 县 电 影 院　·　公 映",font=ImageFont.truetype(SHOP,17),anchor="mm",fill=fg)
        sheet.paste(paper,(i*424,0))
    sheet.save(out/"cinema-bills.jpg",quality=94,subsampling=0)
with Image.open(source/"night-windows.png") as raw:
    raw.convert("RGB").resize((1152,768),Image.Resampling.LANCZOS).save(out/"night-rooms.jpg",quality=92,subsampling=0)
