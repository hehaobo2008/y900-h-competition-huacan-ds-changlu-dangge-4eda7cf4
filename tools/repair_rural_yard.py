"""One-time correction of the current unbatched editable rural source."""
from pathlib import Path
import math
import sys
import bpy
sys.path.insert(0, str(Path(__file__).resolve().parent))
import blib as B

posts = [o for o in bpy.context.scene.objects if o.name.startswith("Sample_yard_gate_post")]
hinges = [o for o in bpy.context.scene.objects if o.name.startswith("Sample_hinge_strap")]
if len(posts) != 2 or len(hinges) != 4:
    raise RuntimeError("Expected two yard posts and four hinge straps")
target_x = 9.5/4+1.3-1.5
for ob in posts:
    side = -1 if ob.location.x < -24 else 1
    ob.location.x = -24 + side*target_x*math.cos(.05) + 5*math.sin(.05)
    ob.location.y = 2 + side*target_x*math.sin(.05) - 5*math.cos(.05)
for ob in hinges:
    attr = ob.data.color_attributes.get("Col")
    for color in attr.data:
        color.color = (*B.srgb("#5d574b"),1)
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
print("REPAIRED_YARD_SOURCE")
