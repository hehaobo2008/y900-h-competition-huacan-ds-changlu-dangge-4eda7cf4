"""Restore each CC0 plant's separate opacity map to its colour texture."""
from pathlib import Path
from PIL import Image
ROOT = Path(__file__).resolve().parent.parent / "assets" / "vegetation" / "source"
for name in ("grass_bermuda_01", "weed_plant_02"):
    root = ROOT / name
    color = Image.open(root / "textures" / (name + "_diff_1k.jpg")).convert("RGB")
    alpha = Image.open(root / "alpha.png").convert("L")
    if color.size != alpha.size:
        raise RuntimeError("Colour and alpha dimensions differ for " + name)
    color.putalpha(alpha)
    color.save(root / "basecolor_alpha.png")
