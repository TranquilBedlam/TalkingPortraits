"""Turn a folder of portrait pictures into layers for the talking player.

Usage: python scripts/prepare_portrait.py maya

Reads portraits/<id>/base.png and the variations (mouth_*.png, eyes_closed.png),
all made from base.png in an image editor so only the mouth or eyes differ.
Writes player/characters/<id>/: base.webp plus one small cut-out per variation
(the mouth or eye area with soft edges) and layers.json with their positions.
"""

import json
import os
import sys

from PIL import Image, ImageDraw, ImageFilter

SIZE = 1024
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Areas that change, as ellipses (left, top, right, bottom) on the 1024 picture.
# They match the areas erased in the editor (see portraits/<id>/example_erase_*.png).
# A character's own portraits/<id>/regions.json overrides these (Maya's values).
REGIONS = {
    "mouth": [(405, 400, 598, 535)],
    "eyes": [(335, 260, 475, 357), (520, 250, 655, 345)],
}
FEATHER = 10  # soft edge in pixels


def region_for(name):
    return "eyes" if name.startswith("eyes") else "mouth"


def main():
    char_id = sys.argv[1]
    src = os.path.join(ROOT, "portraits", char_id)
    out = os.path.join(ROOT, "player", "characters", char_id)
    os.makedirs(out, exist_ok=True)

    regions = REGIONS
    regions_file = os.path.join(src, "regions.json")
    if os.path.exists(regions_file):
        with open(regions_file, encoding="utf-8-sig") as f:
            regions = json.load(f)

    base = Image.open(os.path.join(src, "base.png")).convert("RGB").resize((SIZE, SIZE), Image.LANCZOS)
    base.save(os.path.join(out, "base.webp"), quality=90)

    layers = {"size": SIZE, "layers": {}}
    for file in sorted(os.listdir(src)):
        name, ext = os.path.splitext(file)
        if ext.lower() != ".png" or name == "base" or "_diff" in name or name.startswith("example"):
            continue
        var = Image.open(os.path.join(src, file)).convert("RGB")
        if var.size != (SIZE, SIZE):
            var = var.resize((SIZE, SIZE), Image.LANCZOS)

        mask = Image.new("L", (SIZE, SIZE), 0)
        draw = ImageDraw.Draw(mask)
        for box in regions[region_for(name)]:
            draw.ellipse(box, fill=255)
        mask = mask.filter(ImageFilter.GaussianBlur(FEATHER))
        left, top, right, bottom = mask.getbbox()

        patch = var.crop((left, top, right, bottom)).convert("RGBA")
        patch.putalpha(mask.crop((left, top, right, bottom)))
        patch.save(os.path.join(out, name + ".webp"), quality=92)
        layers["layers"][name] = {"x": left, "y": top, "w": right - left, "h": bottom - top}
        print(f"{name}: {right - left}x{bottom - top} at {left},{top}")

    with open(os.path.join(out, "layers.json"), "w", encoding="utf-8") as f:
        json.dump(layers, f, indent=2)


main()
