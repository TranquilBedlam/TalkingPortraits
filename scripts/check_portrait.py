"""Check that a portrait variation lines up with base.png.

Usage: python scripts/check_portrait.py portraits/maya mouth_half.png
Prints the sizes and where the two pictures differ, and writes <name>_diff.png
(white = changed) next to them, so a variation that changed more than the
erased area is easy to spot.
"""

import os
import sys

from PIL import Image, ImageChops

folder, name = sys.argv[1], sys.argv[2]
base = Image.open(os.path.join(folder, "base.png")).convert("RGB")
var = Image.open(os.path.join(folder, name)).convert("RGB")
print("base", base.size, "variation", var.size)
if var.size != base.size:
    var = var.resize(base.size, Image.LANCZOS)
    print("resized variation to match")

diff = ImageChops.difference(base, var).convert("L").point(lambda v: 255 if v > 24 else 0)
box = diff.getbbox()
changed = 1 - diff.histogram()[0] / (base.size[0] * base.size[1])
print("changed area box:", box, f"changed pixels: {changed:.1%}")
diff.save(os.path.join(folder, os.path.splitext(name)[0] + "_diff.png"))
