# The beat sheet

Twelve one-line beats, written and shown **before a single credit is spent**. This is
the cheapest thing in the skill and the thing a client actually reacts to.

## The spine

Every launch video in this genre runs the same shape. Deviate on content, not on order.

| beat | s | what it does | what the frame needs |
|---|---|---|---|
| COLD OPEN | 0.8 | buys attention before anyone knows what this is | one image, no type, high contrast, immediately legible as a shape |
| THE BEFORE | 1.2 | the tedious old way, **shown not described** | clutter, too many windows, a hand doing something slow |
| TURN | 0.5 | something snaps. the shortest beat in the film | one gesture, one state change. usually a `flash` transition |
| THE PRODUCT | 1.5 | first clean look. **this is the look plate** | hero framing, off-centre, room to move into, full look block |
| CAPABILITY ×3 | 1.0 ea | three things it does, one beat each | three different framings, same ground and light |
| PROOF | 1.2 | a result, a number, a real output | the thing it made, not the interface that made it |
| SCALE | 1.2 | many of them, or one out in the world | grid, wall, street — a change of scale from everything before |
| ENDCARD | 2.0 | wordmark + URL | a **still**. never generated as video. |

≈12s. Stretch to 20–30 by widening the capability run — three beats become five, or
each gains a companion. **Never by holding shots longer.** A slow launch video is a
dead one, and holding is exactly the instinct to resist.

## Cutting it to length

```
15s   drop SCALE, run two capabilities
30s   five capabilities, PROOF gets a companion beat, ENDCARD 2.5s
60s   don't. Two 30s films beat one 60s film, and the second one is free.
```

## What each frame prompt is made of

```
<LOOK BLOCK>     identical in all N prompts, pasted verbatim from the plate.
                 ground, light, palette, lens, texture, type treatment.

<THE FRAME>      what is in shot, where it sits, what the camera sees.
                 one sentence. this is the ONLY part that changes.

<MOTION ROOM>    "composed for motion: the subject is off-centre with room to
                 move into, and the background carries depth so a camera move
                 has parallax to find."

<TYPE CLAUSE>    either the exact string in quotes, or "no text anywhere in
                 this frame." Never neither.
```

The type clause is the one people skip. A negation on its own does not hold — where a
region must carry type, **supply the right text** and the model stops inventing.

## The move, per beat

Written into the i2v prompt, because Seedance 2.5 has no camera-lock parameter.

```
COLD OPEN     LOCKED      "locked-off camera, the frame does not move"
THE BEFORE    DRIFT       slow lateral, background separating
TURN          PUSH        fast in, the only quick move in the film
THE PRODUCT   PUSH        slow dolly in, 3-5% across the shot
CAPABILITY    LOCKED      let the content move, not the camera
PROOF         RACK        focus travels front to back
SCALE         DRIFT       wide lateral, parallax doing the work
ENDCARD       -           it's a still
```

**One move per shot.** Two moves in one 1-second beat reads as a mistake, and at these
durations nobody sees the second one anyway.

## Windows

Every shot is generated at 5 seconds and the cut takes 0.5–1.5s out of it.

```
in: 0.5     the default. i2v eases in from the still, so 0.0-0.4 is near-static.
in: 1.0+    for a PUSH — let the move build before you join it.
in: 0.0     only for a still.
```

When a shot is 80% wrong and 20% right, **that is a shot.** Move the window. Never
re-roll: Seedance has no seed, and the re-roll will not contain the good second.

## The music brief

`ElevenLabs Music v1` takes no parameters, so the whole brief is the prompt. Name the
bpm and put the same number in `cut.json`.

```
<genre and reference feel>, <bpm> bpm, <instrumentation>.
Starts sparse. A lift at <the TURN, in seconds>. Full arrangement from
<the PRODUCT> to the end. Resolves cleanly, no fade, no vocals.
Length: <film length + 5> seconds.
```

Ask for more than the film needs — `cut.py` trims, fades and normalises.

## Ordering the generations

The plate first, alone, and stop to look at it. Then everything else in one pass:

```
1 gen    THE PRODUCT frame        -- human check --
N gens   the other frames         one pass, fired together
N gens   the moves                one pass, fired together
1 gen    the track                fire with the moves; nothing depends on it
0 gens   the cut
```

Only the cut waits. Do not stagger the frames on a timer — that turns one wait into N
waits for nothing.
