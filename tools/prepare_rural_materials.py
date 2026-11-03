"""Make colour adaptations of the downloaded CC0 sources; do not overwrite them."""
from pathlib import Path
from PIL import Image, ImageEnhance, ImageOps
import math

ROOT = Path(__file__).resolve().parent.parent / "assets" / "materials" / "polyhaven"

def recolor(asset, black, white, contrast=1.0):
    source = ROOT / asset / "Diffuse.jpg"
    gray = ImageOps.grayscale(Image.open(source).convert("RGB"))
    gray = ImageEnhance.Contrast(gray).enhance(contrast)
    result = ImageOps.colorize(gray, black=black, white=white)
    result.save(ROOT / asset / "Diffuse_rural.jpg", quality=94, subsampling=0)

# The original blue fabric is adapted to an undyed, warm linen; the original
# plaster is lightened for limewashed rural walls. Texture detail remains intact.
recolor("rough_linen", "#544a38", "#e2d3b2", 0.8)
recolor("white_plaster_rough_01", "#776b5a", "#f3eee2", 0.8)
recolor("clay_roof_tiles", "#3c403c", "#a4a397", 0.9)
recolor("dirt", "#c3bfb1", "#f5f1e8", 0.7)

# A faint irregular compressed-soil overlay: soft-edged, rather than two
# painted lines. It is used over actual shallow wheel depressions.
src = Image.open(ROOT / "dirt" / "Diffuse.jpg").convert("RGB")
src = ImageEnhance.Brightness(src).enhance(.78).convert("RGBA")
w, h = src.size
alpha = Image.new("L", src.size)
pixels = alpha.load()
for y in range(h):
    strength = .72 + .18*math.sin(y*.037) + .1*math.sin(y*.097)
    for x in range(w):
        t = abs((x/(w-1))*2-1)
        soft = max(0, 1-t*t)**2
        pixels[x,y] = int(85*soft*strength)
src.putalpha(alpha)
src.save(ROOT / "dirt" / "Diffuse_track.png")
