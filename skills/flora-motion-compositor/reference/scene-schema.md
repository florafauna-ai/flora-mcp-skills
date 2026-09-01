# scene.json

One file per shot. It is the source of truth — a rendered mp4 is a build
artefact. Paths are relative to the scene file's own directory.

## Top level

| key | default | |
|---|---|---|
| `id` | filename stem | names the output: `<id>.mp4` |
| `size` | `[1920, 1080]` | |
| `fps` | `30` | |
| `dur` | required | seconds |
| `bg` | `"#000000"` | a hex string, a gradient, or an image — see below |
| `grade` | — | `vignette` `grain` `saturation` `brightness` |
| `camera` | — | a list of anim entries on `zoom`, `px`, `py` |
| `layers` | required | back to front |

### `bg`

```json
"bg": "#0b0b0f"
"bg": {"from": "#0b0b0f", "to": "#191a24"}          vertical gradient
"bg": {"image": "plate.png"}                         cover-fitted, centre-cropped
```

A FLORA generation used as `bg.image` is the one place the generative and
composited halves meet inside a single shot.

### `grade`

| key | range | |
|---|---|---|
| `vignette` | 0–1 | 0.35–0.5 is the useful band |
| `grain` | 0–0.02 | 0.006 is visible on a gradient and invisible on a screenshot |
| `saturation` | 0–2 | 0.95 pulls a UI's blues back a touch |
| `brightness` | −1–1 | |

Grain is seeded on the **frame index**. Do not replace that with anything
time-based — byte-identical re-renders are a load-bearing property.

### `camera`

Applied after everything, as a crop-and-rescale of the finished frame.

```json
"camera": [{"prop":"zoom","from":1.0,"to":1.05,"t":[0,3.0],"ease":"inOutSine"}]
```

`zoom` > 1 pushes in. `px` / `py` pan in pixels. A 3–6% push across the whole
shot is the house default; more than 10% reads as a zoom effect rather than as
a camera.

## Layers

Common to all three types:

| key | default | |
|---|---|---|
| `type` | required | `image` \| `text` \| `rect` |
| `id` | — | for your own reference; prints nowhere |
| `at` | `[W/2, H/2]` | position |
| `anchor` | `center` | `left` `right` `top` `bottom` `topleft` `topright` `bottomleft` `bottomright` |
| `opacity` | `1.0` | |
| `in` / `out` | `0` / ∞ | the layer exists only inside this window; its own animation clock starts at `in` |
| `anim` | `[]` | keyframes, see below |

Animatable props on any layer: `x` `y` `scale` `rotate` `opacity` `blur`.
Images add `tiltX` `tiltY` `tiltZ`. Rects add `w` `h`.

### `anim`

```json
{"prop":"x", "from":1330, "to":1180, "t":[0.0,1.3], "ease":"snap"}
```

Before `t[0]` the value is `from`; after `t[1]` it is `to`. Multiple entries on
one prop apply in order, so a later one wins where they overlap.

### `image`

| key | |
|---|---|
| `src` | png/jpg/webp, or **svg** (rasterised through Chrome on load) |
| `w` or `h` | target size; the other dimension follows the aspect |
| `radius` | corner rounding, applied before the tilt |
| `tilt` | `{"x":deg, "y":deg, "z":deg, "persp":1600}` |
| `shadow` | `{"blur":70, "opacity":0.55, "dy":46, "dx":0}` |

`tilt` is a true 3D projection. `y` −25…−12 and `x` 4…10 is the working band;
`persp` 1600–2200, lower being a wider lens.

### `text`

| key | default | |
|---|---|---|
| `text` | required | |
| `font` | `Helvetica` | resolved by name from the system font dirs |
| `weight` | `regular` | appended to the name when matching (`bold`, `light`…) |
| `size` | `64` | px |
| `color` | `#ffffff` | |
| `width` | — | wrap width. Omit for a single line |
| `leading` | `1.15` | multiple of `size` |
| `track` | `0` | letter-spacing in px; negative tightens |
| `reveal` | — | see below |

```json
"reveal": {"mode":"words", "stagger":0.055, "t":0.25, "dur":0.6,
           "rise":46, "ease":"snap"}
```

`mode` is `words`, `lines` or `none`. `t` is when the first unit starts, `dur`
how long each takes, `rise` how far below its resting place each unit begins.
Keep `stagger` at or under 0.07 and the whole reveal under 0.8s — beyond that a
headline reads as arriving twice.

### `rect`

`w`, `h`, `color`, `radius`. Both `w` and `h` animate, which is how a rule draws
itself on. A zero dimension renders nothing rather than raising.

## Verbs

```bash
comp.py scene.json                      # render <id>.mp4
comp.py scene.json --frame 0            # one PNG. check t=0 AND t=dur.
comp.py scene.json --strip 6            # N frames across the shot, as one strip
comp.py scenes/ --all -o shots/         # every scene in a directory
comp.py --svg logo.svg 2048             # SVG -> trimmed transparent PNG
comp.py scene.json -o DIR
```

## What this file is not

It is not a place to fix an asset. A soft screenshot stays soft, a wrong logo
stays wrong — recapture it. Everything here is layout and motion.
