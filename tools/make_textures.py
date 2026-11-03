"""Original procedural texture set: paper grain, ink wipe, clouds, smoke, stars, seal."""
from __future__ import annotations
import math, random
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "textures"
OUT.mkdir(parents=True, exist_ok=True)
SERIF = "C:/Windows/Fonts/NotoSerifSC-VF.ttf"
rng = np.random.default_rng(20261029)


def value_noise(h, w, cell, octaves=5, seed=1):
    r = np.random.default_rng(seed)
    total = np.zeros((h, w), np.float32)
    amp = 1.0
    norm = 0.0
    for o in range(octaves):
        ch = max(2, int(h / (cell / (2 ** o))) + 2)
        cw = max(2, int(w / (cell / (2 ** o))) + 2)
        base = r.random((ch, cw)).astype(np.float32)
        img = Image.fromarray((base * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
        total += np.asarray(img, np.float32) / 255.0 * amp
        norm += amp
        amp *= 0.55
    return total / norm


def norm01(a):
    a = a - a.min()
    return a / max(a.max(), 1e-6)


def paper():
    h = w = 1024
    n = norm01(value_noise(h, w, 220, 6, 3) * 0.55 + value_noise(h, w, 28, 3, 5) * 0.45)
    fiber = np.zeros((h, w), np.float32)
    r = np.random.default_rng(4)
    for _ in range(900):
        x, y = r.integers(0, w), r.integers(0, h)
        ln = r.integers(8, 60)
        a = r.random() * math.tau
        for k in range(ln):
            xx = int(x + math.cos(a) * k)
            yy = int(y + math.sin(a) * k)
            if 0 <= xx < w and 0 <= yy < h:
                fiber[yy, xx] += r.uniform(0.1, 0.4)
    fiber = np.asarray(Image.fromarray((norm01(fiber) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6)), np.float32)
    v = np.clip(0.82 + n * 0.18 - fiber * 0.12, 0, 1)
    rgb = np.stack([v * 0.985, v * 0.975, v * 0.94], -1)
    Image.fromarray((rgb * 255).astype(np.uint8)).save(OUT / "paper.jpg", quality=92)
    # alpha grain for post overlay
    alpha = np.clip(0.5 + (n - 0.5) * 0.5, 0, 1)
    Image.fromarray((alpha * 255).astype(np.uint8)).convert("L").save(OUT / "grain.png")


def ink():
    s = 1024
    yy, xx = np.mgrid[0:s, 0:s].astype(np.float32)
    cx, cy = s * 0.5, s * 0.5
    dx, dy = (xx - cx) / (s * 0.5), (yy - cy) / (s * 0.5)
    r = np.sqrt(dx * dx + dy * dy)
    n = norm01(value_noise(s, s, 150, 6, 8))
    edge = 0.55 + 0.28 * (n - 0.5) + 0.06 * np.sin(np.arctan2(dy, dx) * 9)
    alpha = np.clip((edge - r) * 5.0, 0, 1)
    # few tendrils
    rr = np.random.default_rng(9)
    for _ in range(14):
        a = rr.random() * math.tau
        rad = rr.uniform(0.3, 0.55)
        ex, ey = math.cos(a) * rad, math.sin(a) * rad
        d = np.sqrt((dx - ex) ** 2 + (dy - ey) ** 2)
        alpha = np.maximum(alpha, np.clip((0.16 - d) * 6, 0, 1) * 0.85)
    alpha = np.asarray(Image.fromarray((alpha * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2)), np.float32) / 255
    img = np.zeros((s, s, 4), np.uint8)
    img[..., 0:3] = 30
    img[..., 3] = (alpha * 255).astype(np.uint8)
    Image.fromarray(img).save(OUT / "ink.png")


def cloud():
    h, w = 512, 1024
    n = norm01(value_noise(h, w, 260, 6, 11) * 0.6 + value_noise(h, w, 48, 4, 12) * 0.4)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    dx, dy = (xx - w / 2) / (w / 2), (yy - h * 0.55) / (h * 0.5)
    mask = np.clip(1.2 - np.sqrt(dx * dx * 0.55 + dy * dy * 1.8), 0, 1)
    a = np.clip((n - 0.42) * 3.2, 0, 1) * mask
    a = np.asarray(Image.fromarray((a * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(8)), np.float32) / 255
    border = np.minimum(np.minimum(np.arange(w)[None, :], w - 1 - np.arange(w)[None, :]), np.minimum(np.arange(h)[:, None], h - 1 - np.arange(h)[:, None]))
    a *= np.clip(border / 90.0, 0, 1)
    rgb = np.ones((h, w, 4), np.float32)
    rgb[..., 3] = a
    Image.fromarray((rgb * 255).astype(np.uint8)).save(OUT / "cloud.png")


def smoke():
    s = 256
    n = norm01(value_noise(s, s, 60, 5, 21))
    yy, xx = np.mgrid[0:s, 0:s].astype(np.float32)
    r = np.sqrt(((xx - s/2)/(s/2))**2 + ((yy - s/2)/(s/2))**2)
    a = np.clip((0.9 - r) * 1.8, 0, 1) * np.clip((n - 0.3) * 2.2, 0, 1)
    a = np.asarray(Image.fromarray((a * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(5)), np.float32) / 255
    img = np.ones((s, s, 4), np.float32)
    img[..., 3] = a
    Image.fromarray((img * 255).astype(np.uint8)).save(OUT / "smoke.png")


def glow():
    for name, size, power in [("star", 64, 2.2), ("sun", 512, 1.4), ("glow", 256, 2.0)]:
        s = size
        yy, xx = np.mgrid[0:s, 0:s].astype(np.float32)
        r = np.sqrt(((xx - s/2)/(s/2))**2 + ((yy - s/2)/(s/2))**2)
        a = np.clip(1 - r, 0, 1) ** power
        rgb = np.ones((s, s, 4), np.float32)
        rgb[..., 3] = a
        Image.fromarray((rgb * 255).astype(np.uint8)).save(OUT / f"{name}.png")


def shadow():
    s = 256
    yy, xx = np.mgrid[0:s, 0:s].astype(np.float32)
    r = np.sqrt(((xx - s/2)/(s/2))**2 + ((yy - s/2)/(s/2))**2)
    a = np.clip(1 - r, 0, 1) ** 1.6
    img = np.zeros((s, s, 4), np.float32)
    img[..., 3] = a * 0.55
    Image.fromarray((img * 255).astype(np.uint8)).save(OUT / "shadow.png")


def seal():
    s = 512
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([8, 8, s-8, s-8], radius=34, fill=(169, 47, 38, 255))
    d.rounded_rectangle([26, 26, s-26, s-26], radius=24, outline=(244, 225, 186, 225), width=8)
    f = ImageFont.truetype(SERIF, 176)
    text = "山河"
    # two vertical characters
    for i, ch in enumerate(text):
        bb = d.textbbox((0, 0), ch, font=f)
        tw, th = bb[2]-bb[0], bb[3]-bb[1]
        d.text(((s-tw)/2-bb[0], 62 + i*196 - bb[1]), ch, font=f, fill=(244, 225, 186, 255))
    # white cracks
    r = random.Random(5)
    for _ in range(30):
        x = r.randint(20, s-20); y = r.randint(20, s-20)
        d.line([(x, y), (x+r.randint(-30, 30), y+r.randint(-20, 20))], fill=(169, 47, 38, 255), width=r.randint(1, 3))
    img.save(OUT / "seal.png")


if __name__ == "__main__":
    paper(); ink(); cloud(); smoke(); glow(); shadow(); seal()
    print("textures done", [p.name for p in OUT.iterdir()])
