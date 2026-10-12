# Talking Portraits

2D talking characters for a language-learning app (web + iPhone/Android). See README.md for the workflow and PLAN.md for decisions. Remote: https://github.com/TranquilBedlam/TalkingPortraits (branch `main`).

- A character is `portraits/<id>/base.png` plus Midjourney Editor edits of it (`mouth_half`, `mouth_oh`, `mouth_ah`, `eyes_closed`), and `regions.json` with the mouth/eye ellipses (1024 coordinates). `scripts/prepare_portrait.py <id>` cuts feathered layers into `player/characters/<id>/`; the player is `player/talking-portrait.js`.
- The user is not technical: give one step at a time, and draw the areas to erase (`scripts/draw_erase_examples.py <id>`) rather than describing them.
- Python: use `C:\Users\Warren\Desktop\Gridfinity Apps\UltimateGridfinityBuilder\.venv\Scripts\python.exe` (has Pillow). Read JSON with `utf-8-sig` (PowerShell writes a BOM).
- The 3D experiment (Blender 5.2.2 at `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe`, MPFB extension, `scripts/build_character.py`, `characters/*.json`) is kept for reference; it couldn't reach the Pixar look.
- Check the licence of any asset before adding it; note it in PLAN.md.
