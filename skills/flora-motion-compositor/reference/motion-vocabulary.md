# Motion vocabulary

The moves this aesthetic is actually made of, and which easing each one wants.
Everything here is a few lines of `anim` — the point of the list is to stop you
inventing motion per shot, which is what makes a film look assembled.

## Easing

| name | shape | use for |
|---|---|---|
| `snap` | fast out, long settle (bezier .16, 1) | **the default.** almost every entrance |
| `outExpo` | very fast out, hard settle | scale-ins, a rule drawing itself |
| `outQuint` | like outExpo, gentler | large plates that would otherwise feel thrown |
| `outCubic` | mild | opacity fades |
| `inOutSine` | symmetric, slow both ends | camera moves, a tilt settling |
| `outBack` | overshoots and returns | one accent per film, at most |
| `linear` | — | almost never. reads as broken |

**One rule:** entrances ease *out* (fast then settle), continuous motion eases
*in-out*, and nothing eases *in* alone unless it is leaving.

## The moves

### PLATE ENTRANCE — a screen arriving

The workhorse. Three properties, one duration band.

```json
"anim": [
  {"prop":"opacity","from":0,   "to":1,   "t":[0,0.5], "ease":"outCubic"},
  {"prop":"x",      "from":1330,"to":1180,"t":[0,1.3], "ease":"snap"},
  {"prop":"scale",  "from":0.93,"to":1.0, "t":[0,1.4], "ease":"outExpo"}
]
```

Travel 120–180px, scale from 0.92–0.95. More than that and it reads as a slide
transition rather than as a thing settling into place.

### THE TURN — a screen rotating to face you

The single most valuable line in the whole vocabulary. Animate the tilt toward
zero across the entire shot, slowly.

```json
{"prop":"tiltY","from":-30,"to":-16,"t":[0,3.0],"ease":"inOutSine"}
```

It never arrives at flat. Landing on 0 kills the depth exactly when the viewer
has settled into it.

### TYPE REVEAL — a headline arriving

```json
"reveal": {"mode":"words","stagger":0.055,"t":0.25,"dur":0.6,"rise":46,"ease":"snap"}
```

`rise` is roughly half the type size. Start it *before* the plate settles —
0.25s against a 1.3s plate move — so the two overlap. Sequential beats feel
twice as long as they are.

Use `mode: "lines"` for a subhead: word-staggering body copy is fussy and slows
the read.

### RULE DRAW — an accent line

```json
{"prop":"w","from":0,"to":72,"t":[0.15,0.7],"ease":"outExpo"}
```

Short, early, and above the headline. It is punctuation, not a layer.

### CAMERA PUSH — the whole frame

```json
"camera": [{"prop":"zoom","from":1.0,"to":1.05,"t":[0,3.0],"ease":"inOutSine"}]
```

3–6% across the shot. Runs the full duration, always — a camera that stops
moving mid-shot reads as a mistake.

### FOCUS PULL

`blur` from 12 to 0 over 0.6s with `outCubic`, on the plate only, while the
background stays sharp. One per film.

### HOLD

No animation at all, for an endcard or title. The camera push alone is enough
to keep it alive. Resist adding a second thing.

## Timing bands

```
plate entrance      1.2 - 1.5s      the longest move in a shot
type reveal         0.25 start, all units landed by 0.8s
rule draw           0.5s
camera push         the whole shot, always
focus pull          0.6s
```

**One dominant move per shot.** A plate that slides *and* rotates *and* scales
*and* fades is four moves; the eye reads it as noise. The entrance stack above
is three properties describing **one** move — a thing settling — which is why it
works.

## Shot lengths

Composited shots are cut to the same lengths as generated ones, so render each
scene longer than the beat needs and let `cut.json` take a window:

```
render      2.5 - 3.0s
cut         0.8 - 1.5s
```

The extra tail is free here — no credits, no queue — and it means a beat can
grow later without re-rendering. Unlike i2v, the **first frames are usable**:
there is no ease-in from a still, so a window can start at `in: 0.0`.

## Ground and palette

```
GROUND      near-black #0b0b0f to #191a24, vertical. never flat black.
ACCENT      one colour, used on the rule and nothing else.
TYPE        white headline, #9a9aa8 subhead. two weights, never three.
SHADOW      blur 60-80, opacity 0.5-0.6, dy 40-50. it is what puts the
            plate in the room.
VIGNETTE    0.4. the reason the plate reads as lit rather than pasted.
```

That palette is the genre. Deviate on the accent colour and the type, not on
the ground — a light-ground version of this aesthetic needs a different shadow
and a different vignette, and is a different design job.
