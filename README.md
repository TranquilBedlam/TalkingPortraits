# Talking Portraits

Pixar-style talking characters for a language-learning app (web and phones). Each character is a picture made in Midjourney plus a few edited copies where only the mouth or eyes change; a small JavaScript player stacks them to make the character blink, breathe and lip-sync.

## Making a character
1. In Midjourney, make a front-facing head-and-chest portrait with a closed-mouth smile. Save it as `portraits/<id>/base.png`.
2. Write `portraits/<id>/regions.json` (mouth and eye ellipses on the 1024 picture) and run
   `python scripts/draw_erase_examples.py <id>` to draw the areas to erase.
3. In Midjourney's Editor, starting from `base.png` every time, erase one area and repaint it. Save as:
   `mouth_half.png`, `mouth_oh.png`, `mouth_ah.png` (mouth area) and `eyes_closed.png` (eye areas).
4. Check each one: `python scripts/check_portrait.py portraits/<id> mouth_half.png`
5. Cut the layers: `python scripts/prepare_portrait.py <id>` writes `player/characters/<id>/`.

## Trying it
```
python -m http.server 8765 --directory player
```
Then open http://localhost:8765 (the page can't be opened straight from disk).

## Using it in an app
Copy `player/talking-portrait.js` and `player/characters/<id>/`, then:
```js
import { TalkingPortrait } from "./talking-portrait.js";
const maya = await TalkingPortrait.create(element, "characters/maya");
maya.say("Kumusta ka?", { lang: "fil-PH" });   // browser voice, approximate lip-sync
maya.playVisemes([{ t: 0, shape: "ah" }]);     // exact timings from a TTS service
```
Mouth shapes: `closed`, `half`, `oh`, `ah`.

## Folders
| Folder | Contents |
|---|---|
| `portraits/<id>/` | Midjourney pictures, `regions.json`, erase examples |
| `player/` | Test page, player code, prepared characters |
| `scripts/` | Picture checks and layer cutting; `build_character.py` is the earlier 3D (Blender + MPFB) experiment |
| `characters/` | Settings for the 3D experiment |

See `PLAN.md` for decisions and history.
