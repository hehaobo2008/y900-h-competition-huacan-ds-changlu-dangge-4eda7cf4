"""Export the shop signs' actual brush outlines and the display-title font subset."""
import json
from pathlib import Path
from fontTools import subset
from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont

ROOT=Path(__file__).resolve().parents[1]
FACES=ROOT/"assets"/"sources"/"lettering"


class SignPen(BasePen):
    def __init__(self,glyphs,upm,offset):
        super().__init__(glyphs)
        self.commands=[]
        self.upm,self.offset=upm,offset

    def command(self,op,*points):
        args=[v for x,y in points for v in (round((x+self.offset)/self.upm,4),round(y/self.upm,4))]
        self.commands.append([op,*args])

    def _moveTo(self,p): self.command("M",p)
    def _lineTo(self,p): self.command("L",p)
    def _qCurveToOne(self,a,b): self.command("Q",a,b)
    def _curveToOne(self,a,b,c): self.command("C",a,b,c)
    def _closePath(self): self.command("Z")


def letters(words,face,tracking):
    with TTFont(FACES/face) as font:
        glyphs=font.getGlyphSet()
        upm=font["head"].unitsPerEm
        cursor=0
        result=[]
        for ch in words:
            glyph=glyphs[font.getBestCmap()[ord(ch)]]
            pen=SignPen(glyphs,upm,cursor)
            glyph.draw(pen)
            result.append(pen.commands)
            cursor+=glyph.width+upm*tracking
        return result


brush="MaShanZheng-Regular.ttf"
shop="ZCOOLQingKeHuangYou-Regular.ttf"
signs={word:letters(word,face,space) for word,face,space in (
    ("供销合作社",brush,.20),("东街副食",shop,.23),("灯下面馆",brush,.19),("育苗温室",shop,.15))}
(ROOT/"src"/"shop_letters.json").write_text(json.dumps(signs,ensure_ascii=False,separators=(",",":")),"utf8")
with TTFont(FACES/brush) as font:
    subsetter=subset.Subsetter()
    subsetter.populate(text="山河织路田埂晨街市暮城夜雨山河速星河远五座时代之岛全卷总览")
    subsetter.subset(font)
    font.flavor="woff"
    target=ROOT/"assets"/"fonts"
    target.mkdir(exist_ok=True)
    font.save(target/"shanhe-titles.woff")
