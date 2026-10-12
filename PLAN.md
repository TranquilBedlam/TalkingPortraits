# Plan

## Update (2026-10-11): switched to 2D talking portraits
MPFB couldn't get near the Pixar-style reference, so characters are now pictures made in Midjourney: `portraits/<id>/base.png` plus Editor edits that change only the mouth (`mouth_half`, `mouth_oh`, `mouth_ah`) or eyes (`eyes_closed`). `scripts/prepare_portrait.py <id>` cuts these into soft-edged layers in `player/characters/<id>/`, and `player/talking-portrait.js` shows them with blinking, breathing and lip-sync (approximate from text with the browser's voice, or exact via `playVisemes()` with a TTS service's timings). The 3D notes below are kept for reference.

## Decisions (2026-10-11)
- **Look:** stylised. Proposed: semi-stylised characters built on MPFB (MakeHuman for Blender), with exaggerated proportions (larger head and eyes, simpler features) and toon shading. Alternative: anime look made by hand in VRoid Studio. **Chosen: MPFB semi-stylised**, aiming as close as it can get to a Pixar/Disney-style look (big warm eyes, soft skin, friendly expressions), framed as a talking head (head to just below the chest). Known limit: it won't fully reach that look. First test character: an attractive, curvy Filipina woman in friendly everyday clothes.
- **Lip-sync:** yes. Every character gets the same set of mouth shapes (visemes) and a few expressions (smile, surprise, blink).
- **First batch:** four characters (see below).
- **Tool:** Claude Code drives Blender; no separate generator app, no API key.
- **Language app (recommended):** React + three.js (react-three-fiber) web app, packaged for iPhone and Android with Capacitor. One codebase.
- **Lip-sync at runtime:** text-to-speech that returns mouth-shape timings (for example Azure Speech viseme events); for recorded audio, timings made in advance with Rhubarb Lip Sync.

## Export targets (per character)
- Format: glTF binary (`.glb`), one file per character.
- Size: about 10-20k triangles, textures 1K-2K, compressed; aim for a few MB.
- One skeleton shared by all characters, so every animation works on every character.
- Mouth shapes as glTF morph targets with fixed names (see `characters/_schema.md`).

## The first four characters
| ID | Name | Description |
|---|---|---|
| mei | Mei | East Asian woman, 20s |
| kwame | Kwame | West African man, 30s |
| priya | Priya | South Asian woman, 40s |
| mateo | Mateo | Latin American man, 20s |

Names, ages and backgrounds are placeholders; change them freely.

## Steps
1. Install Blender (blender.org) and add MPFB from Blender's Extensions menu (Edit > Preferences > Get Extensions, search "MPFB"), plus its asset packs.
2. Check MPFB's scripting support and write `scripts/build_character.py`.
3. Build one test character, look at the preview, settle the stylised look.
4. Build all four; check them in a simple three.js test page (web and phone).
5. Add shared animations (idle, wave, nod, point, talk).
6. Lip-sync test: a character speaks a sentence with text-to-speech.

## Assets installed
| Pack | Licence | Installed |
|---|---|---|
| makehuman_system_assets (hair, clothes, skins, eyes, eyebrows, eyelashes, teeth, tongue) | CC0 | 2026-10-11 |

## To check during setup
- How far MPFB proportions can be pushed while the face rig and mouth shapes still work.
- Licences of any extra clothes, hair and animations (for example Mixamo's terms for use in an app).
