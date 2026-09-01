---
name: flora-motion-compositor
description: >
  Animate assets that already exist. Give it a UI screenshot, a logo, a product
  photo, a Figma export or a FLORA plate, and it returns real motion-graphics
  shots — 3D-tilted screens, staggered type reveals, camera moves, drop shadows,
  grade — rendered deterministically from a JSON scene graph, with type staying
  pin-sharp because it is real type. Use for SaaS and app launch videos, feature
  announcements, UI demos, product teasers, title cards, endcards, lower thirds,
  logo animations, or any shot whose subject is a screenshot rather than an
  invention. Sibling to flora-launch-video: this makes shots, that one cuts them.
  Nothing is generated and nothing drifts. Do not use when the subject does not
  exist yet and has to be invented — that is flora-launch-video. Do not use to
  change an asset's aspect ratio, which is flora-image-resize, or to place a
  finished creative into a real-world scene, which is flora-mockup-deck.
---

# flora-motion-compositor

## What it is

Not a generator. **A compositor.**

> **Nothing is generated. Every pixel comes from a file or a font.**

That one sentence buys everything a generative pipeline has to fight for. Type is
real type, so it is pin-sharp at any resolution and always spelled right. The
product is the actual product, because it is the actual screenshot. There is no
seed to lose, no drift, no re-roll, and **two renders of the same scene are
byte-identical** — verified, not assumed.

## When this instead of flora-launch-video

One question decides it: **does the subject already exist?**

| | this skill | `flora-launch-video` |
|---|---|---|
| the subject | exists — UI, logo, photo, Figma frame, a FLORA plate | has to be made |
| use for | SaaS launch, feature announcement, UI demo, endcard, title | brand film, campaign, fashion, physical product |
| type | free and perfect | a fight, worked around with stills and f2v pairs |
| drift | none, by construction | real — no seed, no undo |
| cost per shot | 0 credits, ~12s of CPU | minutes and credits |
| cannot | invent a world | hold a wordmark |

**They are not alternatives, they are two halves.** For a software launch most
beats are a real screen and belong here; the atmosphere beats belong there. Run
both and cut them together.

### They meet at cut.json

Every shot this renders is an ordinary mp4 that drops straight into a
`flora-launch-video` cut:

```
comp.py scenes/ --all -o shots/     # N scenes -> N mp4s
cut.py cut.json --check             # the same edit list, mixed sources
```

A generated atmosphere beat and a composited UI beat sit side by side in one
timeline. `cut.py` does not care which made which — and re-pacing the whole film
is still free.

## Requirements

`comp.py` is the only skill in this repo that ships executable code. It needs:

```
python3 + Pillow + numpy      hard requirement. numpy missing is a crash, not a warning.
ffmpeg                        resolved in order: $FFMPEG, then PATH, then the copy
                              inside imageio_ffmpeg. None of the three and it exits
                              saying so — `brew install ffmpeg` or
                              `pip3 install imageio-ffmpeg`.
Chrome                        only for `--svg`. Everything else runs without it.
```

**It is macOS-only in two places.** The SVG rasteriser is a hardcoded
`/Applications/Google Chrome.app` path, and fonts resolve across the macOS font
directories. Both fail with a message rather than silently, and neither is reached
by a scene that uses PNG assets and a font that exists. Ported elsewhere, those are
the two functions to change.

## The shape

```
STEP 1   assets     screenshots at 2x, logos as SVG, plates from FLORA
STEP 2   scenes     one scene.json per shot
         -- check at t=0 and t=dur, free --
STEP 3   render     comp.py -> one mp4 per shot
STEP 4   cut        cut.json -> the film
```

Nothing in that costs a credit except a FLORA plate, if you use one.

## Step 1 — assets

```
SCREENSHOTS   capture at 2x device pixel ratio, minimum. The tilt magnifies the
              near edge, and a 1x capture goes soft exactly where the eye lands.
LOGOS         SVG. `comp.py --svg logo.svg 2048` rasterises it through headless
              Chrome to a trimmed transparent PNG - macOS ships no SVG
              rasteriser, but Chrome is one.
PLATES        a FLORA generation used as a background. This is the one place the
              two skills overlap inside a single shot: generated ground,
              composited foreground.
FONTS         resolved by human name from the system font directories. A missing
              font falls back to Helvetica and SAYS SO - it never silently
              swaps a typeface and changes the design.
```

**Never screenshot a screenshot.** Re-capturing a scaled UI puts a second
resampling grid over the first and it moirés under the tilt.

## Step 2 — the scene graph

One JSON file per shot. Layers, each with keyframed properties:

```json
{ "id": "hero", "size": [1920,1080], "fps": 30, "dur": 3.0,
  "bg": {"from": "#0b0b0f", "to": "#191a24"},
  "grade": {"vignette": 0.45, "grain": 0.006, "saturation": 0.95},
  "camera": [{"prop":"zoom","from":1.0,"to":1.05,"t":[0,3.0],"ease":"inOutSine"}],
  "layers": [
    { "type":"image", "src":"ui.png", "w":1180, "radius":18, "at":[1180,520],
      "tilt": {"y": -22, "x": 7, "persp": 1900},
      "shadow": {"blur": 70, "opacity": 0.55, "dy": 46},
      "anim":[ {"prop":"x","from":1330,"to":1180,"t":[0,1.3],"ease":"snap"},
               {"prop":"scale","from":0.93,"to":1.0,"t":[0,1.4],"ease":"outExpo"},
               {"prop":"tiltY","from":-30,"to":-16,"t":[0,3.0],"ease":"inOutSine"} ] },
    { "type":"text", "text":"Ship the launch film, not the deck",
      "font":"Helvetica","weight":"bold","size":80,"width":470,"track":-2,
      "at":[150,300],"anchor":"topleft",
      "reveal":{"mode":"words","stagger":0.055,"t":0.25,"rise":46,"ease":"snap"} }
  ] }
```

Full field reference: `reference/scene-schema.md`.
The move vocabulary and which easing to use: `reference/motion-vocabulary.md`.

### The tilt is the shot

`"tilt": {"y": -22, "x": 7, "persp": 1900}` is what stops a UI screenshot looking
like a UI screenshot. It is a **real 3D projection** — corners rotated in space
and divided through by depth — not a shear, so the near edge genuinely grows and
the far edge genuinely shrinks. A shear looks wrong and you cannot say why.

Defaults that work: `y` between −25 and −12, `x` between 4 and 10, `persp` 1600–2200.
Lower `persp` is a wider lens and a more aggressive convergence.

**Animate `tiltY` toward zero across the shot.** Starting at −30 and settling at
−16 makes the screen appear to turn to face you. That single keyframe does more
than any other line in the file.

### Type is set, not generated

Real fonts, real tracking, real leading, wrapped to a `width`. `reveal` staggers
the words in on a delay, each with its own rise and easing, so a headline
*arrives* rather than appearing.

Three things worth knowing:

- **Each word composites as its own tile.** Drawing everything onto one canvas
  and re-alphaing regions double-dims wherever two words overlap — which, on a
  negatively-tracked headline, is most of them.
- **Canvas width comes from where the tiles end**, not from re-measuring the
  joined string. Re-measuring under-reports once tracking is negative and slices
  the last word of the longest line — visible on that one word only.
- **`anchor: "topleft"` means the top of the type**, not the top of the reserved
  rise headroom. Otherwise every headline sits low by the rise amount.

## Step 3 — check before you encode

```bash
comp.py scene.json --frame 0        # 0.5s. the free check.
comp.py scene.json --frame 3.0
comp.py scene.json --strip 6        # 1.0s. six frames across the shot.
comp.py scene.json                  # 12s for a 3s 1080p shot
comp.py scenes/ --all -o shots/     # batch
```

**Check t=0 and t=dur, never only the middle.** Measured on the first live scene
here: a rule that animates its own width starts at zero, a zero-width rounded
rect raises, and the shot rendered perfectly at t=1.4 and t=1.6 while being
completely unrenderable. Frame zero is where scenes break.

Then `--strip 6` for the eye pass. The strip shows the *arc* — whether the type
lands before the plate settles, whether anything is still moving at the end —
which no single frame can.

Measured on this machine: **single frame 0.5s, six-frame strip 1.0s, full 3s
1080p shot 12s** (~7.5 rendered fps). Re-rendering a whole 12-shot film after a
design change is about two minutes and costs nothing.

## Grade

`vignette`, `grain`, `saturation`, `brightness`. Keep it restrained — this
aesthetic is defined by clean ground and a soft vignette, not by filters.

**Grain is seeded on the frame index, never on wall-clock.** That is what makes
two renders byte-identical, and it is the reason "re-render is free" stays true
rather than quietly becoming "re-render is nearly the same".

## Gotchas

```
RENDERING
frame 0            check it. Animated width/height start at zero and a
                   zero-size rounded rect raises. Mid-shot frames hide it.
determinism        grain RNG is seeded per frame index. Never use wall-clock,
                   never np.random without a seed - it breaks byte-identity.
numpy on Apple     an (H,W,3)@(3,) float32 matmul emits spurious divide/overflow
                   warnings through Accelerate. Use an explicit weighted sum.
Pillow 13          Image.fromarray(arr, "RGB") - the mode argument is deprecated.
                   Pass the array alone.
resampling         LANCZOS for scaling plates, BICUBIC for the perspective
                   transform. NEAREST anywhere near a screenshot moirés.
speed              frames pipe to ffmpeg as rawvideo over stdin. Never write
                   PNG sequences - it is several times slower and fills a disk.

ASSETS
SVG                no rsvg, no inkscape, no cairosvg on this machine. Chrome
                   headless is the rasteriser: --svg file.svg 2048.
screenshots        2x minimum. The tilt magnifies the near edge.
fonts              resolved by name across /System/Library/Fonts{,/Supplemental},
                   /Library/Fonts and ~/Library/Fonts. A miss falls back to
                   Helvetica and prints a warning - read the output.
ffmpeg             not on PATH here. comp.py falls back to the static build
                   inside imageio_ffmpeg automatically.

LAYOUT
white on white     type over a light screenshot vanishes. It is not clipping -
                   it is the same colour. Narrow the wrap width, or put the
                   plate where the type is not.
anchors            center (default) / left / right / top / bottom / topleft /
                   topright / bottomleft / bottomright. Only topleft-family
                   anchors compensate for a text block's rise headroom.
```

## Where it lands

```
<project>/Deliverables/<Title>-launch/
  assets/          the screenshots, logos, plates. the inputs.
  scenes/          one scene.json per shot. THE SOURCE OF TRUTH.
  shots/           the rendered mp4s
  cut.json         the edit list (flora-launch-video)
  <Title>.mp4      the film
```

**`scenes/` is the deliverable, not `shots/`.** A shot is a build artefact; the
scene is what a revision edits. Keep both, and keep `assets/` — a scene without
its assets is not re-renderable.

Never leave output in a scratch directory or `~/Downloads`. Say the full path in
the final message.

## The client surface

`client-task` applies if someone will open this without you, with one difference
worth stating: **this skill has no prompts to hide.** There is no model to route
around and nothing to phrase carefully — a scene is numbers and text. The thing
to teach is that changing a headline means editing one string in one file, and
that re-rendering costs nothing but a minute.

## Failure atlas

| symptom | cause | fix |
|---|---|---|
| crash on encode, fine on `--frame 1.5` | an animated width starts at 0 | already guarded; always check t=0 |
| a word missing from the headline | white type over a white screenshot | narrow `width`, or move the plate |
| the last word of one line is sliced | canvas measured from the joined string | already fixed — width comes from tile extents |
| headline sits low | `anchor` not a topleft-family value | `"anchor": "topleft"` |
| the screen looks like a sticker | shear instead of projection, or no shadow | use `tilt`, add `shadow` |
| the screen looks flat and dead | `tiltY` is static | animate it toward zero across the shot |
| soft, crawling UI detail | 1x screenshot, or a screenshot of a screenshot | recapture at 2x from source |
| two renders differ | an unseeded RNG crept in | grain seeds on frame index only |
| a typeface changed | font not found, fell back | read the warning; install it or name it exactly |
| type reads as "arriving twice" | reveal stagger too long for the shot | stagger ≤ 0.07s; the whole reveal under 0.8s |

## Reporting back

The strip, the shot list with durations, and the render time. Name which shots
are composited and which are generated if the film mixes both — a reviewer
should know which frames can be re-typed for free and which cannot.
