"""Prepare runtime textures from the full-resolution original painting plates."""
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "assets" / "sources" / "painted"
OUT = ROOT / "assets" / "painted"
OUT.mkdir(parents=True, exist_ok=True)
for name in ("day", "night", "market-horizon", "avenue-horizon", "port-horizon", "river-horizon"):
    path = SRC / (name + ".png")
    if path.exists():
        with Image.open(path) as image:
            image.convert("RGB").save(OUT / (name + ".webp"), quality=90, method=5)
for sheet, names in [("plants", ["camphor","willow","pine","reeds"]),
                     ("people", ["harvester","family","umbrella","scientist"]),
                     ("thickets", ["copse","foreshore","conifers","rice"]),
                     ("elevations", ["balcony","tenement","laboratory","cottage"]),
                     ("walls", ["lime","tiles","earth","puddles"]),
                     ("shops", ["granary","market","noodles","orangery"])]:
    with Image.open(SRC / (sheet + ".png")) as image:
        w, h = image.size
        for i, name in enumerate(names):
            x, y = (i % 2) * (w // 2), (i // 2) * (h // 2)
            tile = image.crop((x+2, y+2, x+w//2-2, y+h//2-2))
            if sheet in ("plants","people","thickets"):
                bbox = tile.getchannel("A").point(lambda a: 255 if a > 40 else 0).getbbox()
                if bbox:
                    tile = tile.crop(bbox)
            tile.save(OUT / (name + ".webp"), quality=91, alpha_quality=98, method=5)
