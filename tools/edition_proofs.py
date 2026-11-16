"""Build the print crop, fixed-camera comparison and storage audit from the shipped files."""
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
QA = ROOT / "qa" / "edition"
DIST = ROOT / "dist"
FONTS = Path("C:/Windows/Fonts")


def draw_comparison():
    years = ["1980s", "1990s", "2010s", "2020s", "未来"]
    titles = ["田埂晨", "街市暮", "城夜雨", "山河速", "星河远"]
    ids = ["rural", "town", "city", "rail", "future"]
    canvas = Image.new("RGB", (1390, 1925), "#f3ecdf")
    draw = ImageDraw.Draw(canvas)
    serif = ImageFont.truetype(str(FONTS / "simsun.ttc"), 43)
    body = ImageFont.truetype(str(FONTS / "msyh.ttc"), 22)
    tiny = ImageFont.truetype(str(FONTS / "msyh.ttc"), 16)
    draw.text((38, 25), "山河织路　五幕同机位对照", font=serif, fill="#231f19")
    draw.text((40, 86), "同一场景位置、视线与视场角。左为上一版，右为本次细修，均取自浏览器。", font=tiny, fill="#625b50")
    for x, label in [(143, "改造前"), (766, "本次交付")]:
        draw.text((x, 132), label, font=body, fill="#933d31")
    for i, name in enumerate(ids):
        y = 174 + i * 346
        draw.text((38, y + 139), titles[i], font=body, fill="#231f19")
        draw.text((40, y + 176), years[i], font=tiny, fill="#756d61")
        for x, version in [(143,ROOT/"qa"/"refinement"/"previous"), (766,QA/"final")]:
            with Image.open(version / (name + ".jpg")) as frame:
                canvas.paste(frame.resize((588,331),Image.Resampling.LANCZOS),(x,y))
    canvas.save(QA / "五幕同机位对照.jpg", quality=94, subsampling=0)
    with Image.open(QA / "final" / "overview.jpg") as frame:
        frame.crop((63,198,1194,898)).save(QA / "final" / "overview-print.jpg",quality=96)
    gallery=Image.new("RGB",(1304,1230),"#f3ecdf")
    guide=ImageDraw.Draw(gallery)
    guide.text((29,16),"山河织路　五幕实景",font=serif,fill="#231f19")
    guide.text((844,42),"手绘动画风格　/　交互作品运行画面",font=tiny,fill="#615c50")
    for i,(name,label,year) in enumerate(zip(ids+["overview"],titles+["五岛展卷"],years+["总览"])):
        x,y=29+(i%2)*637,86+(i//2)*378
        file=(name+"-route" if name!="overview" else name)+".jpg"
        with Image.open(QA/"final"/file) as frame:
            gallery.paste(frame.resize((607,341),Image.Resampling.LANCZOS),(x,y))
        guide.text((x,y+344),label,font=body,fill="#322b26")
        guide.text((x+122,y+349),year,font=tiny,fill="#965240")
    gallery.save(ROOT/"qa"/"animation"/"五幕实景.jpg",quality=93,subsampling=0)


def audit():
    rows = []
    for folder in ("zones","vehicles"):
        for file in sorted((DIST / "assets" / folder).glob("*.glb")):
            with file.open("rb") as stream:
                header = stream.read(20)
                doc = json.loads(stream.read(int.from_bytes(header[12:16],"little")))
            triangles = 0
            for mesh in doc["meshes"]:
                for primitive in mesh["primitives"]:
                    if primitive.get("mode",4) == 4:
                        accessor = primitive.get("indices",primitive["attributes"]["POSITION"])
                        triangles += doc["accessors"][accessor]["count"] // 3
            rows.append(dict(type=folder,name=file.stem,storedTriangles=triangles,bytes=file.stat().st_size,
                             materials=len(doc.get("materials",[])),embeddedImages=len(doc.get("images",[]))))
    runtime = [DIST / name for name in ("index.html","app.js","style.css")]
    runtime.extend(file for file in (DIST / "assets").rglob("*") if file.is_file())
    report = dict(assets=rows,onlineBytes=sum(file.stat().st_size for file in runtime),
                  offlineBytes=(DIST / "山河织路-离线单文件.html").stat().st_size,
                  paintedTextures=len(list((DIST/"assets"/"painted").glob("*.webp"))),
                  storedModelTriangles=sum(row["storedTriangles"] for row in rows))
    (QA / "asset-audit.json").write_text(json.dumps(report, indent=2) + "\n",encoding="utf-8")


if __name__ == "__main__":
    draw_comparison()
    audit()
