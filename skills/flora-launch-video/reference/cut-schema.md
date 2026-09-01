# cut.json

The edit list. This file is the source of truth for the film — keep it beside the
master forever. Every path in it is relative to the file's own directory.

```json
{
  "title": "Raylight",
  "fps": 30,
  "size": [1920, 1080],
  "bpm": 120,
  "grid": "beat",
  "music": { "src": "track.mp4", "in": 0.0, "fade_in": 0.0, "fade_out": 1.2 },
  "resize": { "fill": "blur" },
  "shots": [
    { "id": "cold",    "src": "shots/cold.mp4",   "in": 0.6, "dur": 0.8, "note": "cold open" },
    { "id": "before",  "src": "shots/before.mp4", "in": 0.5, "dur": 1.2, "note": "the old way" },
    { "id": "turn",    "src": "shots/turn.mp4",   "in": 1.1, "dur": 0.5,
      "transition": { "type": "flash", "duration": 0.08 }, "note": "it snaps" },
    { "id": "hero",    "src": "shots/hero.mp4",   "in": 0.5, "dur": 1.5, "note": "the product" },
    { "id": "endcard", "src": "frames/endcard.png",           "dur": 2.0,
      "transition": { "type": "dip", "duration": 0.4 }, "note": "wordmark + url, held" }
  ]
}
```

## Top level

| key | default | what it does |
|---|---|---|
| `title` | `"launch"` | kebab-cased into every output filename |
| `fps` | `30` | timeline frame rate; every duration lands on a whole frame |
| `size` | `[1920, 1080]` | master dimensions; sources are scaled and cropped to fit |
| `bpm` | — | tempo of the track. Required for `grid` to do anything |
| `grid` | `"free"` | `beat` \| `half` \| `bar` \| `free`. Quantises every shot duration |
| `pace` | `1.0` | global multiplier on every window. `--pace` overrides it |
| `music` | — | see below. Omit for a silent master |
| `resize` | `{"fill":"blur"}` | `blur` \| `flat` \| `black` background for the cutdowns |
| `shots` | required | in order |

### `music`

| key | default | |
|---|---|---|
| `src` | — | mp3, m4a, wav or an mp4 with an audio track |
| `in` | `0.0` | seconds into the track to start |
| `fade_in` | `0.0` | |
| `fade_out` | `1.0` | measured back from the end of the film |
| `gain_db` | `0` | applied before normalisation |

The track is padded if short, trimmed to the timeline, faded, and normalised to
**−14 LUFS / −1.5 dBTP**. You do not need to trim it yourself.

## A shot

| key | default | what it does |
|---|---|---|
| `src` | required | a clip, or a **still** (`.png .jpg .jpeg .webp .bmp .tif`) |
| `id` | `s1`, `s2`… | shows up in `--check` and on the contact sheet |
| `in` | `0.0` | seconds into the source where the window starts |
| `dur` | required | seconds **on the timeline**, before `pace` and `grid` |
| `speed` | `1.0` | `>1` faster, `<1` slower. Changes how much source is consumed |
| `transition` | `"cut"` | how this shot arrives. Ignored on the first shot |
| `note` | `""` | what the beat is for. Prints in `--check`; keep it honest |

### `transition`

`"cut"` (default, free and lossless) or `{"type": …, "duration": s}`:

`dissolve` · `flash` (through white) · `dip` (through black) · `wipe` · `slide` · `zoom`

A transition **eats its duration out of the running time** — two shots of 1.5s with a
0.3s dissolve occupy 2.7s, not 3.0s. `--check` accounts for this, and so does the
music fade. Duration is clamped to 40% of the shorter neighbour so no shot is fully
consumed.

## The arithmetic

```
out   = dur x pace,  quantised to the grid,  rounded to a whole frame
need  = out x speed                    <- source seconds consumed, starting at `in`
total = sum(out) - sum(transition durations)
```

A shot **overruns** when `in + need > source length`. `--check` reports the deficit
and exits non-zero.

## Stills

A still source is held for exactly `dur`. `in` and `speed` are ignored, it can never
overrun, and it accepts transitions on both sides like any other shot. This is how the
endcard, any full-screen type card and any held product shot are done — never as an
i2v run that happens not to move.

## Verbs

```bash
cut.py cut.json --check                 # the timeline as numbers. free, ~1s.
cut.py cut.json                         # render the master
cut.py cut.json --pace 0.8              # "snappier"  - every window x0.8
cut.py cut.json --pace 1.3              # "slow it down"
cut.py cut.json --snap bar              # override the grid for this render
cut.py cut.json --fit                   # repair overruns, then render
cut.py cut.json --contact               # first/mid/last frame strip
cut.py cut.json --resizes               # 9:16 and 1:1 cutdowns
cut.py cut.json -o DIR                  # write somewhere other than beside cut.json
cut.py --measure reference.mp4          # read a reference film's cut rate and tempo
```

`--pace` and `--snap` are **render-time overrides and are not saved**. When a pace is
the new truth, write it into `cut.json` as `"pace"` so the next person gets it too.

### `--fit`

Repairs an overrun in two steps, in this order, and prints what it did:

1. **pull the window earlier** — reduce `in` by up to the deficit. Free, no quality cost.
2. **stretch the shot** — drop `speed` so the available source fills the window.

It never shortens a shot and it never touches a still. If both steps are not enough
the source is simply too short for the beat: shorten `dur`, or use a different take.

## What this file is not

It is not a place to fix a picture. If a shot is wrong — wrong look, warped type,
broken geometry — no edit list value repairs it. Everything here is timing.
