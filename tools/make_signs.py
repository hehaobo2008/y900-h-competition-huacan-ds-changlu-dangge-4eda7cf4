"""Generate an original shop-sign atlas for the five dioramas.
Text, palette, wear and layout are authored here; no external images."""
from __future__ import annotations
import json, math, random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets"
OUT.mkdir(exist_ok=True)
SERIF = "C:/Windows/Fonts/NotoSerifSC-VF.ttf"
SANS = "C:/Windows/Fonts/NotoSansSC-VF.ttf"
W, H = 4096, 2048
rng = random.Random(20261029)

SIGNS = [
    # key, text, sub, style, bg, fg, w, h, vertical
    ("fu", "福", "", "paper", "#b5372f", "#f5d9a8", 300, 300, False),
    ("chunlian_a", "春满人间", "", "paper", "#a92f28", "#f6dfae", 170, 620, True),
    ("chunlian_b", "岁岁平安", "", "paper", "#a92f28", "#f6dfae", 170, 620, True),
    ("gengdu", "耕读传家", "山河村", "wood", "#3b2b1f", "#e4c58a", 560, 190, False),
    ("cun", "山河村", "SHANHE VILLAGE", "stone", "#4a4a44", "#ddd6c4", 520, 170, False),
    ("fengshou", "丰收", "", "paper", "#c94532", "#f7e4b8", 360, 200, False),
    ("baihuo", "春风百货", "日用百货 · 针纺织品", "paint", "#e8dcc2", "#9e2f28", 620, 220, False),
    ("zhaoxiang", "时光照相馆", "黑白 · 彩色 · 证件照", "paint", "#dfe5e2", "#263b4a", 620, 220, False),
    ("lifa", "人民理发店", "理发 · 烫发", "paint", "#e6e0d1", "#324c5b", 600, 200, False),
    ("shudian", "长路书店", "图书 · 文具 · 课本", "paint", "#d8dfd2", "#3f5238", 600, 210, False),
    ("fandian", "山河饭店", "住宿 · 餐饮", "paint", "#e3cba6", "#7c2f24", 600, 210, False),
    ("gongxiaoshe", "供销社", "农业生产资料 · 生活用品", "paint", "#d9c9a8", "#8a2e26", 620, 210, False),
    ("dianying", "电影院", "今日放映 · 售票处", "marquee", "#6f2530", "#f4d49a", 660, 220, False),
    ("binggun", "冰棍 3分", "", "paper", "#e8d9b8", "#b04431", 420, 150, False),
    ("xiubiao", "修表配钥匙", "", "paint", "#d7d0bf", "#3b3a34", 500, 160, False),
    ("lushe", "旅社", "", "paint", "#d8d3c4", "#8e3228", 380, 190, False),
    ("bashi", "班车", "山河 — 县城", "paint", "#d9e2dd", "#2d4c5a", 480, 170, False),
    ("yeshi", "夜市长街", "NIGHT MARKET", "neon", "#120d18", "#ff7a4d", 680, 220, False),
    ("chalou", "山河茶楼", "茶 · 点心", "neon", "#171016", "#ffc46b", 600, 210, False),
    ("shufang", "城市书房", "24H READING", "neon", "#0c141e", "#a9e7ff", 600, 210, False),
    ("yingyuan", "光影影院", "CINEMA", "neon", "#160e1c", "#ff5f9e", 640, 220, False),
    ("bianli", "24H 便利", "便利店", "neon", "#0b1a13", "#8ff5b0", 560, 190, False),
    ("guidao", "轨道大厦", "GUDAO TOWER", "metal", "#3b4148", "#e2e6e4", 620, 190, False),
    ("changluli", "长路里", "CHANGLU LI", "neon", "#150f12", "#ffd9a0", 600, 200, False),
    ("mian", "面馆", "牛肉面", "neon", "#1a120b", "#ffcf6a", 380, 180, False),
    ("huoguo", "火锅", "", "neon", "#1b0b0a", "#ff5c48", 380, 180, False),
    ("yaodian", "药店", "24H", "neon", "#0a1712", "#7dffc0", 380, 180, False),
    ("neon_ye", "夜", "", "neon", "#120b16", "#ff7cc8", 300, 300, False),
    ("yunling", "云岭站", "YUNLING STATION", "station", "#1e3b63", "#f2f6fa", 640, 190, False),
    ("qiaoming", "山河大桥", "SHANHE BRIDGE", "metal", "#39414a", "#e8ecea", 560, 170, False),
    ("xinghe", "星河港", "XINGHE SPACEPORT", "future", "#0a1620", "#c8fff4", 640, 200, False),
    ("xincheng", "山河新城", "SHANHE NEW CITY", "future", "#0b1520", "#e6f7ff", 640, 200, False),
    ("lingtan", "零碳社区", "ZERO CARBON", "future", "#0a1814", "#a8ffcf", 560, 180, False),
    ("exit", "出口", "EXIT", "station", "#1c3d2e", "#f1f7f1", 360, 150, False),
    ("platform", "站台", "PLATFORM", "station", "#1e3b63", "#f2f6fa", 360, 150, False),
]


def hexc(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


LETTERING = OUT / "sources" / "lettering"
BRUSH = str(LETTERING / "MaShanZheng-Regular.ttf")
SHOP = str(LETTERING / "ZCOOLQingKeHuangYou-Regular.ttf")


def font(size, family):
    face = ImageFont.truetype(family, size)
    if family == SANS:
        face.set_variation_by_axes([660])
    return face


def fit(text, max_w, max_h, family, stroke=0):
    lo, hi = 10, 340
    best = font(10, family)
    probe = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    while lo <= hi:
        mid = (lo + hi) // 2
        f = font(mid, family)
        box = probe.textbbox((0, 0), text, font=f, stroke_width=stroke)
        tw, th = box[2] - box[0], box[3] - box[1]
        if tw <= max_w and th <= max_h:
            best = f
            lo = mid + 1
        else:
            hi = mid - 1
    return best


def draw_sign(key, text, sub, style, bg, fg, w, h, vertical):
    S = 2  # supersample
    Wp, Hp = w * S, h * S
    img = Image.new("RGBA", (Wp, Hp), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    bgc, fgc = hexc(bg), hexc(fg)
    if style in ("neon", "future"):
        for y in range(Hp):
            t = y / Hp
            c = tuple(int(bgc[i] * (0.55 + 0.7 * (1 - t))) for i in range(3))
            d.line([(0, y), (Wp, y)], fill=c + (255,))
        d.rounded_rectangle([3*S, 3*S, Wp-3*S, Hp-3*S], radius=7*S,
                            outline=tuple(min(255, int(v*0.9)) for v in fgc) + (255,), width=2*S)
    elif style == "paper":
        d.rectangle([0, 0, Wp, Hp], fill=bgc + (255,))
        d.rectangle([7*S, 7*S, Wp-7*S, Hp-7*S], outline=fgc + (255,), width=2*S)
        d.rectangle([13*S, 13*S, Wp-13*S, Hp-13*S], outline=fgc + (160,), width=1*S)
    elif style == "wood":
        for y in range(Hp):
            t = y / Hp
            c = tuple(int(bgc[i] * (0.8 + 0.35 * math.sin(t * 9 + i))) for i in range(3))
            d.line([(0, y), (Wp, y)], fill=c + (255,))
        d.rectangle([8*S, 8*S, Wp-8*S, Hp-8*S], outline=fgc + (200,), width=2*S)
    elif style == "stone":
        d.rectangle([0, 0, Wp, Hp], fill=bgc + (255,))
        d.rectangle([6*S, 6*S, Wp-6*S, Hp-6*S], outline=(40, 40, 36, 255), width=3*S)
    elif style == "marquee":
        d.rectangle([0, 0, Wp, Hp], fill=bgc + (255,))
        d.rectangle([6*S, 6*S, Wp-6*S, Hp-6*S], outline=fgc + (255,), width=2*S)
        for i in range(14):
            x = 18*S + i * (Wp - 36*S) / 13
            d.ellipse([x-4*S, 4*S, x+4*S, 12*S], fill=(255, 225, 160, 255))
    elif style == "station":
        d.rectangle([0, 0, Wp, Hp], fill=bgc + (255,))
        d.rectangle([4*S, 4*S, Wp-4*S, Hp-4*S], outline=(235, 242, 248, 255), width=2*S)
    elif style == "metal":
        for y in range(Hp):
            t = y / Hp
            c = tuple(int(bgc[i] * (0.8 + 0.3 * (1 - t))) for i in range(3))
            d.line([(0, y), (Wp, y)], fill=c + (255,))
        d.rectangle([5*S, 5*S, Wp-5*S, Hp-5*S], outline=(210, 216, 214, 200), width=2*S)
    else:  # paint
        for y in range(Hp):
            t = y / Hp
            c = tuple(int(bgc[i] * (0.93 + 0.12 * (1 - t))) for i in range(3))
            d.line([(0, y), (Wp, y)], fill=c + (255,))
        d.rectangle([4*S, 4*S, Wp-4*S, Hp-4*S], outline=(60, 48, 38, 160), width=2*S)
    family = BRUSH if style in ("paper", "stone", "wood") or key in ("chalou", "mian", "huoguo") else SHOP
    if style in ("station", "metal", "future"):
        family = SANS
    inset = 15*S
    ink = Image.new("L", img.size)
    letters = ImageDraw.Draw(ink)
    def center_line(draw, words, band, family, width):
        x0, y0, x1, y1 = band
        f = fit(words, (x1-x0)*width, y1-y0, family)
        l,t,r,b = f.getbbox(words)
        draw.text(((x0+x1-l-r)/2, (y0+y1-t-b)/2), words, font=f, fill=255)
    if vertical:
        ch = (Hp-2*inset)/len(text)
        for i, char in enumerate(text):
            center_line(letters, char, (inset,inset+i*ch,Wp-inset,inset+(i+1)*ch),family,.85)
    else:
        top = Hp*.13
        bottom = Hp*(.64 if sub else .84)
        center_line(letters,text,(inset,top,Wp-inset,bottom),family,.92)
    if style in ("neon","future"):
        halo = ink.filter(ImageFilter.GaussianBlur(4*S))
        img.paste(fgc+(255,),mask=halo)
        img.paste(tuple(min(255,int(c*.70+78)) for c in fgc)+(255,),mask=ink)
    else:
        if style not in ("paper","paint"):
            img.paste((42,35,30,255),(2*S,3*S,Wp+2*S,Hp+3*S),ink)
        img.paste(fgc+(255,),mask=ink)
    if sub:
        small = Image.new("L", img.size)
        center_line(ImageDraw.Draw(small),sub,(inset,Hp*.724,Wp-inset,Hp*.875),SANS,.80)
        img.paste(fgc+(255,),mask=small)
    d = ImageDraw.Draw(img)
    if style not in ("paper","neon","future"):
        rr=2*S
        for xx in (inset//2,Wp-inset//2):
            for yy in (inset//2,Hp-inset//2):
                d.ellipse((xx-rr,yy-rr,xx+rr,yy+rr), fill=(93,83,68,255))
                d.line((xx-rr,yy,xx,yy-rr),fill=(206,191,161,255),width=S)
    if style not in ("neon", "future"):
        wear = Image.new("RGBA",img.size)
        d = ImageDraw.Draw(wear)
        for _ in range(int(w * h / 2200)):
            x0, y0 = rng.uniform(0, Wp), rng.uniform(0, Hp)
            ln = rng.uniform(2, 18) * S
            d.line([(x0, y0), (x0+ln, y0+rng.uniform(-3, 3)*S)],
                   fill=(50, 40, 30, rng.randint(10, 30)), width=1*S)
        img = Image.alpha_composite(img,wear)
        veil = Image.new("RGBA", img.size, (0, 0, 0, 0))
        vd = ImageDraw.Draw(veil)
        for i in range(6):
            vd.rectangle([0, 0, Wp, Hp], outline=(35, 28, 20, 10), width=(i+1)*4*S)
        img = Image.alpha_composite(img, veil)
    return img.resize((w, h), Image.LANCZOS)


def pack(items):
    pad = 10
    x = y = pad
    row_h = 0
    rects = {}
    for it in items:
        w, h = it[6], it[7]
        if x + w + pad > W:
            x = pad
            y += row_h + pad
            row_h = 0
        if y + h + pad > H:
            raise RuntimeError("atlas overflow")
        rects[it[0]] = (x, y, w, h)
        x += w + pad
        row_h = max(row_h, h)
    return rects


def main():
    rects = pack(SIGNS)
    atlas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    meta = {"atlas": "signs_atlas.png", "size": [W, H], "rects": {}}
    for it in SIGNS:
        key, text, sub, style, bg, fg, w, h, vert = it
        img = draw_sign(key, text, sub, style, bg, fg, w, h, vert)
        x, y, ww, hh = rects[key]
        atlas.alpha_composite(img, (x, y))
        meta["rects"][key] = {
            "uv": [x / W, 1 - (y + hh) / H, (x + ww) / W, 1 - y / H],
            "px": [x, y, ww, hh], "text": text, "style": style
        }
    atlas.save(OUT / "signs_atlas.png", optimize=True)
    (OUT / "signs_atlas.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    print("signs atlas", len(SIGNS), "signs", atlas.size)


if __name__ == "__main__":
    main()
