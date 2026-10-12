"""Draw the areas to erase in the image editor onto a character's base picture.

Usage: python scripts/draw_erase_examples.py mark

Reads portraits/<id>/regions.json (ellipses on the 1024 picture, the same
areas prepare_portrait.py cuts out) and writes example_erase_mouth.png and
example_erase_eyes.png into portraits/<id>/.
"""

import json
import os
import sys

from PIL import Image, ImageDraw

SIZE = 1024
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

folder = os.path.join(ROOT, "portraits", sys.argv[1])
base = Image.open(os.path.join(folder, "base.png")).convert("RGBA").resize((SIZE, SIZE), Image.LANCZOS)
with open(os.path.join(folder, "regions.json"), encoding="utf-8-sig") as f:
    regions = json.load(f)

for name, boxes in regions.items():
    checker = Image.new("RGBA", (SIZE, SIZE))
    cd = ImageDraw.Draw(checker)
    for y in range(0, SIZE, 8):
        for x in range(0, SIZE, 8):
            shade = 74 if (x // 8 + y // 8) % 2 else 98
            cd.rectangle((x, y, x + 7, y + 7), fill=(shade, shade + 4, shade + 16, 240))
    mask = Image.new("L", (SIZE, SIZE), 0)
    for box in boxes:
        ImageDraw.Draw(mask).ellipse(box, fill=255)
    img = base.copy()
    img.paste(checker, (0, 0), mask)
    draw = ImageDraw.Draw(img)
    for box in boxes:
        draw.ellipse(box, outline=(0, 200, 120, 255), width=3)
    img.crop((250, 180, 774, 700)).convert("RGB").save(os.path.join(folder, f"example_erase_{name}.png"))
