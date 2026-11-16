"""Replace embedded lettering in an already assembled rail or future model."""
import sys
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
import blib as B

source=Path(bpy.data.filepath)
if source.stem not in ("rail","future"):
    raise ValueError(source)
assets=Path(B.ASSETS)
for file in (assets/"signs_atlas.png",assets/"textures"/"workshop_print.jpg"):
    for old in list(bpy.data.images):
        if Path(bpy.path.abspath(old.filepath)).name != file.name:
            continue
        new=bpy.data.images.load(str(file),check_existing=False)
        old.user_remap(new)
        bpy.data.images.remove(old)
        new.name=file.name
        new.pack()
bpy.context.preferences.filepaths.save_version=0
B.save_blend(str(source))
B.export_glb(str(source.with_suffix(".glb")))
