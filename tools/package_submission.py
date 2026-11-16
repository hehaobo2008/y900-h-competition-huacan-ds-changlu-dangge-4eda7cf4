"""Bundle the playable work and jury-facing assets; an author may add signed paperwork."""
import argparse
from pathlib import Path
from tempfile import NamedTemporaryFile
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--author", help="用于赛区要求的实名文件名")
parser.add_argument("--pledge", type=Path, help="已签署的正式原创承诺书")
parser.add_argument("--team", type=Path, help="团队分工说明")
args = parser.parse_args()
author = (args.author or "").strip()
if any(c in author for c in '<>:"/\\|?*') or author in (".",".."):
    parser.error("作者姓名包含文件名不支持的字符")
prefix = f"数字媒体设计_山河织路_{author}" if author else "山河织路"
out = DIST / (prefix + ".zip" if author else "山河织路-参赛材料.zip")
assets = []


def include(src, folder, label):
    src = Path(src)
    if not src.is_file():
        raise FileNotFoundError(src)
    assets.append((src, f"{folder}/{prefix}_{label}{src.suffix.lower()}"))


include(DIST / "山河织路-离线单文件.html","01_交互作品","离线交互作品")
include(DIST / "山河织路-演示片.mp4","02_演示影像","操作与实景")
screens = [
    ("desktop-cover","桌面_封面"),("desktop-memory","桌面_家信"),("desktop-opening","桌面_开书序章"),
    ("desktop-rail","桌面_山河"),("desktop-overview","桌面_展卷"),("desktop-wish","桌面_回信"),
    ("desktop-ending","桌面_尾声"),("phone-cover","手机_封面"),("phone-travel","手机_漫游"),
    ("phone-memory","手机_家信"),("phone-wish","手机_回信"),("landscape-overview","横屏_展卷"),
]
for file, label in screens:
    include(ROOT/"qa"/"optimized"/(file+".png"),"03_高保真界面",label)
for i, label in enumerate(("作品概念","五幕实景","交互流程","美术工艺","尾声"),1):
    include(ROOT/"docs"/"boards"/f"board_0{i}.png","04_设计展板",f"0{i}_{label}")
for label in ("交互流程图","设计说明"):
    include(ROOT/"docs"/(label+".pdf"),"05_作品说明",label)
include(ROOT/"assets"/"sources"/"作品素材说明.md","05_作品说明","作品素材说明")
for project, license_file in (("three","LICENSE"),("meshoptimizer","LICENSE.md")):
    src = ROOT/"node_modules"/project/license_file
    assets.append((src, f"05_作品说明/软件许可/{project}.txt"))
for font in ("mashanzheng","zcoolqingkehuangyou"):
    assets.append((ROOT/"assets"/"sources"/"lettering"/(font+"-OFL.txt"),f"05_作品说明/字体许可/{font}-OFL.txt"))
assets.append((ROOT/"assets"/"sources"/"lettering"/"sources.json","05_作品说明/字体许可/字体版本与来源.json"))
assets.append((ROOT/"assets"/"sources"/"quaternius-stylized-nature"/"License_Standard.txt","05_作品说明/模型许可/Quaternius_树木_CC0.txt"))
if args.pledge:
    include(args.pledge,"06_作者材料","原创承诺书")
if args.team:
    include(args.team,"06_作者材料","团队分工")

guide = """山河织路　｜　实时三维互动长卷

解压后，用支持 WebGL 2 的桌面浏览器打开“01_交互作品”里的 HTML。首次打开为静音，点击声音按钮可以开启。手机浏览器可从部署后的网页进入。作品支持桌面键鼠、触屏竖屏与横屏。

女儿问：“妈，明晚点火的时候，你在哪里看我？”小禾说，在门口的灯下。五封信从灶边的字条写到发射前的留言。第一封里守灯的孩子后来进了城，在雨里的站台等回小禾。如今轮到小禾留下来，等女儿报平安。

点击“走进长卷”或从目录选择时代。轻滑、拨动滚轮或用方向键前行。先听女儿与小禾的对话，再从展开的旧书走入村口。第一幕可自由漫步，WASD 移动、C 低身、Esc 返回。触屏使用方向控件。章名旁交代写信人的境况。接近信里的地点，镜头逐渐放慢，中央的朱红封面显现，随后家书展开。合上继续，或在工具栏回翻。可留一封到终点回信。桥上松手也能目送两列动车各自驶入山洞，然后收到妈妈的语音。未选时默认读女儿从星河港发来的留言。终点可以写回信。点亮后，从地面目送火箭飞远，化成一颗心，也可以直接看尾声。展卷选岛，从目的地远景缓缓推近。

影片共 102 秒，含操作提示、五幕实景与尾声。高保真界面为运行实录 PNG，展板为五张 2400 × 1500 PNG。设备、视觉规范、制作流程与素材说明见“05_作品说明”。

五幕采用手绘动画风格的三维场景。绘景使用图像生成工具辅助制作，三种列车模型沿用作者提供的《轨上清风》项目，第二至五幕选用 Quaternius 的 CC0 树模，乡村底模保留 Poly Haven 的 CC0 基础材质。制作归属详见作品素材说明。
"""
with NamedTemporaryFile(dir=DIST, prefix=".submission-", suffix=".zip", delete=False) as temp:
    pending = Path(temp.name)
try:
    with ZipFile(pending,"w",compression=ZIP_DEFLATED,compresslevel=6) as bundle:
        bundle.writestr(prefix+"_观看与操作.txt",guide)
        for src, archive_name in assets:
            method = ZIP_DEFLATED if src.suffix.lower() in (".html",".txt",".md") else ZIP_STORED
            bundle.write(src,archive_name,compress_type=method)
    with ZipFile(pending) as bundle:
        broken = bundle.testzip()
        if broken:
            raise ValueError(f"ZIP checksum failed for {broken}")
        count = len(bundle.namelist())
    pending.replace(out)
    print(f"{out.name} · {count} files · {out.stat().st_size:,} bytes")
finally:
    pending.unlink(missing_ok=True)
