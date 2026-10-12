"""Package one character with the player into dist/<Name>.zip.

Usage: python scripts/make_zip.py mark

The zip holds the test page (showing only this character), the player code,
the character's prepared layers, the original pictures and a README.
"""

import os
import re
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRONOUNS = {"maya": "her", "mark": "him"}  # for the README; others get "them"

README = """{name} - TALKING PORTRAIT
{underline}

What's in this zip
------------------
player/index.html              Test page: type text, pick a voice, press Speak.
player/talking-portrait.js     The player code (blinking, breathing, lip-sync).
player/characters/{id}/        {name}: base picture, mouth and eye cut-outs,
                               and layers.json (where each sits).
source/                        The original Midjourney pictures (full size).

Trying it
---------
Browsers won't run the page straight from a double-click (they block loading
the files from disk), so it needs a small local web server:

  1. Unzip somewhere, e.g. your Desktop.
  2. Open a terminal in the "player" folder and run:
         python -m http.server 8765
  3. Open http://localhost:8765 in your browser and press Speak.

Using {pronoun} in an app
-------------------
Copy talking-portrait.js and the characters/{id} folder into the app, then:

    import {{ TalkingPortrait }} from "./talking-portrait.js";
    const {id} = await TalkingPortrait.create(element, "characters/{id}");
    {id}.say("Kumusta ka?", {{ lang: "fil-PH" }});   // browser voice, approximate lip-sync
    {id}.playVisemes([{{ t: 0, shape: "ah" }}, ...]); // exact timings from a TTS service

Mouth shapes: "closed", "half", "oh", "ah".
"""


def main():
    char_id = sys.argv[1]
    player = os.path.join(ROOT, "player")
    with open(os.path.join(player, "index.html"), encoding="utf-8") as f:
        page = f.read()
    match = re.search(rf'<option value="{char_id}">([^<]+)</option>', page)
    if not match:
        sys.exit(f"{char_id} is not in the test page's character list")
    name = match.group(1)
    # Keep only this character in the picker.
    page = re.sub(rf'\s*<option value="(?!{char_id}")[^"]+">[^<]+</option>', "", page)

    os.makedirs(os.path.join(ROOT, "dist"), exist_ok=True)
    out = os.path.join(ROOT, "dist", f"{name}.zip")
    top = name
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(f"{top}/README.txt", README.format(
            name=name.upper(), underline="=" * (len(name) + 18), id=char_id,
            pronoun=PRONOUNS.get(char_id, "them")))
        z.writestr(f"{top}/player/index.html", page)
        z.write(os.path.join(player, "talking-portrait.js"), f"{top}/player/talking-portrait.js")
        layers = os.path.join(player, "characters", char_id)
        for file in sorted(os.listdir(layers)):
            z.write(os.path.join(layers, file), f"{top}/player/characters/{char_id}/{file}")
        portraits = os.path.join(ROOT, "portraits", char_id)
        for file in sorted(os.listdir(portraits)):
            if file.endswith(".png") and "_diff" not in file and not file.startswith("example"):
                z.write(os.path.join(portraits, file), f"{top}/source/{file}")
    print(out, f"{os.path.getsize(out) / 1e6:.1f} MB")


main()
