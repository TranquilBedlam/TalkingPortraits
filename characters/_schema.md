# Character settings

One JSON file per character, named `<id>.json`. Values are deliberately tool-neutral; the build script maps them to MPFB settings.

| Key | Type | Meaning |
|---|---|---|
| `id` | text | File and export name, lowercase |
| `name` | text | Display name |
| `sex` | `"female"` / `"male"` | |
| `age` | number | Years |
| `ethnicity` | object | Mix of `african`, `asian`, `european` weights, summing to 1 (MPFB's three sliders) |
| `height` | 0-1 | 0.5 = average |
| `build` | 0-1 | 0 = slim, 0.5 = average, 1 = heavy |
| `skin_tone` | hex colour | |
| `hair` | object | `style`, `colour` |
| `eyes` | object | `colour` |
| `clothes` | list | Items with `type` and `colour` |
| `accessories` | list | For example `"glasses"` |
| `personality` | text | Notes for expressions and poses |
| `stylise` | object | `head_scale`, `eye_scale` (1 = realistic), `toon_shading` |

Mouth shapes every character gets (glTF morph target names): `viseme_sil`, `viseme_PP`, `viseme_FF`, `viseme_TH`, `viseme_DD`, `viseme_kk`, `viseme_CH`, `viseme_SS`, `viseme_nn`, `viseme_RR`, `viseme_aa`, `viseme_E`, `viseme_I`, `viseme_O`, `viseme_U`, plus `blink`, `smile`, `surprise`.
