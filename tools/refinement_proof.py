"""Pair browser frames of the two editions at matching positions on the scroll bar."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

root=Path(__file__).resolve().parents[1]
qa=root/"qa"/"refinement"
brush=ImageFont.truetype(str(root/"assets"/"sources"/"lettering"/"MaShanZheng-Regular.ttf"),53)
body=ImageFont.truetype("C:/Windows/Fonts/msyh.ttc",24)
small=ImageFont.truetype("C:/Windows/Fonts/msyh.ttc",19)
rows=[(201,"田埂晨","村后的池塘、系舟和跨渠石桥"),
      (400,"街市暮","电影院、停车架与本周放映海报"),
      (565,"城夜雨","雨街转角与迎面可读的长路里站"),
      (847,"山河速","两岸桥塔之间完整的通航水面"),
      (900,"星河远","越过岛界，远望星港与发射塔")]
canvas=Image.new("RGB",(1372,236+len(rows)*420),"#f3eddf")
d=ImageDraw.Draw(canvas)
d.text((39,24),"山河织路",font=brush,fill="#83392e")
d.text((40,97),"沿正式漫游路线，按相同进度截取浏览器画面。",font=body,fill="#45473c")
for x,caption in ((40,"调整前"),(705,"本次实景")):
    d.text((x,171),caption,font=body,fill="#713f32")
for i,(frame,title,details) in enumerate(rows):
    y=216+i*420
    for x,folder in ((40,"before"),(705,"after")):
        with Image.open(qa/folder/f"{frame}.jpg") as im:
            canvas.paste(im.resize((627,353),Image.Resampling.LANCZOS),(x,y))
    d.text((40,y+366),title,font=body,fill="#302f27")
    d.text((161,y+370),f"{frame/10:g}%　·　{details}",font=small,fill="#656253")
canvas.crop((0,0,canvas.width,216+len(rows)*420)).save(qa/"漫游细节对照.jpg",quality=92,subsampling=0)
