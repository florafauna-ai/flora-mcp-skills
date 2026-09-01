---
name: flora-launch-video
description: >
  Turn words into a launch video. Give it a product, a wordmark, a screenshot or a
  piece of inspo to re-create on a FLORA canvas, and it returns a beat sheet, a look
  plate, look-locked frames, animated shots, a scored track, and a cut master plus
  9:16 and 1:1 cutdowns. The cut is a JSON edit list, so "make it snappier" or "slow
  it down" re-renders in three seconds and spends nothing. Use when someone wants a
  product launch video, app promo, SaaS teaser, feature announcement, hero video,
  sizzle, trailer or motion graphics, wants a reference film re-created, or asks to
  re-pace, re-cut or re-time something already made. One script, N shots, one cut. Do not use when the subject already exists as a
  screenshot, logo, packshot or Figma frame — that is flora-motion-compositor,
  which is free and holds type perfectly. Do not use when the deliverable is
  ordered clips for someone else to edit rather than a finished cut — that is
  flora-script-to-video, which gates the spend stage by stage. Do not use for a
  single still.
---

# flora-launch-video

## What it is

Not a video generator. **A cut.**

A launch video is thirty seconds of eight to fourteen shots, most of them under a
second and a half, landing on a wordmark. Every part of that except the pictures is
*timing* — and timing is the one thing you must never spend a generation on.

So the skill splits hard down the middle:

```
EXPENSIVE, SLOW, IRREVERSIBLE      the shots.  minutes each, no seed, no undo
FREE, INSTANT, INFINITELY REDONE   the cut.    3 seconds, 0 credits, JSON
```

Everything the person will actually ask for after the first viewing — *snappier,
hold that longer, lose the third one, start on the product, cut it to 15* — lives
entirely on the free side. That is the whole design.

## The two laws

> **1. The shots are generated once. The cut is data.**
> Any pacing, ordering, trim or duration note is a re-render of `cut.json`, never a
> regeneration. A shot re-rolled to fix timing is a fail — and with Seedance there
> is no seed, so the re-roll does not come back the same. You lose the take.

> **2. Type is set in an image node. It is never spoken to a video model.**
> Wordmarks, supers, URLs, UI copy. A video model warps letterforms within about a
> dozen frames. The wordmark card is a **still held in the cut**; a super that must
> survive a move is frame 1 and frame 2 of a `firstFrameLastFrame` pair, so the
> model only travels between two frames a human already approved.

Law 2 is why `cut.py` takes a `.png` as a shot source. The endcard is not a
five-second i2v run that happens to hold still. It is a picture, held.

## Check the sibling first

**`flora-motion-compositor` is the other half of this skill.** One question decides
which one a shot belongs to: *does the subject already exist?*

```
EXISTS      a UI screenshot, a logo, a product photo, a Figma frame
            -> flora-motion-compositor. 0 credits, perfect type, no drift.

MUST BE MADE  a world, a mood, a place, a person, a physical product
            -> here. generation is the only route.
```

For a **software** launch most beats are a real screen, and generating a fake UI is
strictly worse than compositing the real one — hallucinated copy, mushy chrome, a
product that is not yours. Law 2 above exists only because generation cannot hold
type; the compositor makes it moot.

**They meet in this file.** A composited shot is an ordinary mp4 and drops straight
into `cut.json` beside a generated one — verified end to end, mixed timeline, one
grid, one track. Run both and cut them together rather than forcing one skill to do
the other's job.

## The shape

```
STEP 0   0 gens    the script       Claude writes the beat sheet from words
STEP 1   1 gen     the look plate   one frame that sets the whole film
         -- human check --  the plate is the contract; a bad plate poisons twelve shots
STEP 2   N gens    the frames       every beat as a still, look-locked to the plate
STEP 3   N gens    the moves        each still -> i2v, one named move each
STEP 4   1-2 gens  the track        ElevenLabs Music, and SFX if the cut needs accents
STEP 5   0 gens    THE CUT          cut.json + cut.py.  free, instant, re-runnable
```

Twelve beats costs about **26 generations and one round of waiting**. Every revision
after that costs **zero**.

**What is measured and what is not.** The cut engine's numbers in this document were
measured here, on this machine, against known-truth material — durations, the xfade
failure, the still shortfall, the wall-clock. The canvas mechanics are inherited from
`flora-mcp-mockup-deck` and `client-task` and are live-confirmed there. The i2v shot
behaviour is from standing notes plus the model registry, **not** from a live run of
this skill — confirm the Seedance timings on the first one and correct the numbers
here.

## Step 0 — the script, before anything generates

Twelve one-line beats, each with a duration, before a single credit is spent. This is
cheap, it is the thing the client actually reacts to, and it is what makes the shot
prompts writable.

The default spine, which is the one every launch video in this genre actually uses:

```
COLD OPEN     0.8s   one image, no type. buys attention.
THE BEFORE    1.2s   the tedious old way, shown not described
TURN          0.6s   the shortest beat in the film. something snaps.
THE PRODUCT   1.5s   first clean look. this is the hero frame.
CAPABILITY    1.0s   x3   three things it does, one beat each
PROOF         1.2s   a result, a number, or a real output
SCALE         1.2s   many of them, or one in the world
ENDCARD       2.0s   wordmark + URL. a STILL. held.
```

Roughly 12s. Stretch to 20–30 by widening the capability run, never by holding shots
longer — a slow launch video is a dead one.

Write it out and show it before generating. `reference/beat-sheet.md` carries the
archetypes and what each beat's frame prompt needs.

## Step 1 — the look plate

**One image establishes the film. Every other frame is a variation on it, never a
fresh idea.** Same law as `flora-elements-to-3d`, for the same reason: twelve
independently-prompted frames are twelve different films.

Generate one frame — usually THE PRODUCT beat, because it is the one that has to be
right — and stop. Look at it. Then extract its look into a **block of words** you
paste verbatim into all eleven other prompts: ground, light, palette, lens, texture,
type treatment.

Describe the look in words. **Do not wire the plate as a reference into the other
frames** — that drags its composition and its subject along, and you get twelve
photographs of the same object.

### The inspo lane

"Give it some inspo and have it re-create it." A reference contributes exactly two
things and they travel down **two different lanes**:

```
LOOK  ->  WORDS    grade, lens, ground, motion vocabulary, type treatment
                   -> the look block, in every frame prompt
CUT   ->  NUMBERS  shot count, median shot length, where the dissolves are, tempo
                   -> bpm / grid / durations in cut.json
```

Measure the second one instead of guessing it:

```bash
python3 scripts/cut.py --measure reference.mp4
```

It reports shot count, cuts per 10s, min/median/mean/max shot length, the full length
list, and the best-fit tempo. On a known 8-shot, 1.00s-per-shot reference it returned
6 shots at a 1.00s median and a beat of exactly 1.000s — the median is the number that
matters and it came back exact. Two caveats it prints for you: it under-counts cuts
between visually similar shots, and a tempo and its double describe the same grid
(60bpm on beats is 120bpm on halves — take whichever matches your track).

**Never wire the inspo into an image or video model.** Krea in particular follows the
reference and ignores the prompt. And per the prompt-leakage rule: describe how the
reference is *made*, never what it *shows* — "hard top light, 85mm, matte charcoal
ground, no gradient" not "a phone on a desk".

## Step 2 — the frames

Every beat becomes a still first. Non-negotiable, for three reasons: a still is 60–90
seconds against 5 minutes, you can see it is wrong before paying for the move, and it
is the only place type is legible.

The prompt is one invariant block plus one beat line:

```
<THE LOOK BLOCK - identical in all N prompts, pasted verbatim from the plate>

<THE FRAME - what is in shot, where it sits, what the camera is doing>

The frame is composed for MOTION: the subject is off-centre with room to move
into, and the background carries depth so a camera move has parallax to find.

No text anywhere in this frame except <the exact string, in quotes> / no text
anywhere in this frame.
```

That last line matters more than it looks. Per the standing note: to keep the wrong
text out of a region that must carry type, **supply the right text** — a negation
alone does not hold. And where a frame must be typographically clean, say *no text
anywhere*, because these models will invent a caption.

## Step 3 — the moves

One still, one i2v, one named move. The move is written into the prompt because
**Seedance 2.5 has no camera-lock parameter** — "locked-off camera, no camera
movement, the frame does not move" goes in the prompt or you do not get it.

```
LOCKED      nothing moves but the subject                the safe default
PUSH        slow dolly in, 3-5% over the shot            the reveal
DRIFT       lateral parallax, background separating      texture beats
RACK        focus travels front to back                  proof beats
```

Two things that decide whether the cut works at all:

**Generate long, cut short.** Seedance's floor is 4 seconds and the beats are 0.6–1.5.
So *every shot is a 5-second source and the cut takes a window out of it*. Do not try
to generate a one-second clip; you cannot, and asking for a fast action inside five
seconds gets you a slow one. Ask for a slow, continuous move and let the cut choose
the second that is good.

**The first half-second is dead.** i2v eases in from the still, so the opening frames
are near-static. Windows start around `"in": 0.5`, not `0.0`. The schema defaults
accordingly.

**Never re-roll a take you liked part of.** No seed means the re-roll is a different
take. If 0.8 seconds of it are good, that is a shot — move the window, do not
regenerate.

## Step 4 — the track

`ElevenLabs Music v1` (`t2a-elevenlabs-music-t2a`). It takes **no parameters**, so the
entire brief is the prompt: genre, tempo in bpm, instrumentation, arc, and the length.
Name the bpm explicitly and put the same number in `cut.json` — that is what makes the
cuts land on the music instead of near it.

Ask for slightly more than the film needs. `cut.py` trims, pads, fades out and
loudness-normalises to −14 LUFS on its own.

Accents (`t2a-elevenlabs-sfx`) are optional and go on at most three cuts — the turn,
the product, the endcard. More than that and it reads as a stock template.

## Step 5 — the cut

```bash
python3 scripts/cut.py cut.json --check          # the timeline as numbers. free.
python3 scripts/cut.py cut.json --contact --resizes
python3 scripts/cut.py cut.json --pace 0.8       # "make it snappier"
python3 scripts/cut.py cut.json --pace 1.3       # "slow it down"
python3 scripts/cut.py cut.json --snap bar       # land the cuts wider
python3 scripts/cut.py cut.json --fit            # repair overruns automatically
```

Measured on this machine: **a five-shot 1080p timeline with a dissolve, a scored
track, both cutdowns and a contact sheet renders in 3.1 seconds.** That number is the
skill. It is why "make it snappier" is a conversation and not a project.

`--check` is the free pass and it runs first, always. It prints every shot's window,
speed, position on the timeline, source length and transition, flags anything that
runs past the end of its source, names anything off the beat grid, and compares the
track's length against the timeline. It exits non-zero on a problem. **A timing
problem is a number, and a screenshot is a terrible way to read a number.**

Full schema and every verb: `reference/cut-schema.md`.

### Cut on the grid

At 120bpm a beat is 0.5s and a bar is 2s. Set `bpm` and `grid: "beat"` and every
shot's duration quantises to the beat before rendering. This single setting is most
of the difference between a cut that reads professional and one that reads like
clips in a row. `--snap bar` widens it for a slower, more filmic piece.

### The cutdowns are pads, not crops

A centre-crop from 16:9 to 9:16 guillotines the supers — and the type is the
deliverable, so that is Law 2 failing at the last step. `--resizes` letterboxes onto
a blurred, darkened copy of the frame (`"resize": {"fill": "flat"}` uses a solid
sampled from the master's edge band instead).

Neither is a true vertical. **A full-bleed 9:16 needs its own frames and its own i2v
pass.** Say that rather than shipping a letterbox as one.

## Model routing

| job | model | params |
|---|---|---|
| frames carrying type or UI | **GPT Image 2** `i2i-gpt-image-2-i2i` | `quality:"high"`, `aspect_ratio:"16:9"`, `resolution:"2k"` |
| frames locked to the plate's geometry | **Nano Banana Pro** `t2i-gemini-3-pro` | `resolution:"2K"` — uppercase, and always explicit |
| the moves | **Seedance 2.5** `i2v-gengateway-seedance-2-5-i2v` | `duration:"5"`, `aspect_ratio:"16:9"`, `resolution:"1080p"` |
| a super that must survive a move | **Kling 2.5 Turbo Pro** `i2v-kling-2.5` | two `imageUrl` edges → resolves to `firstFrameLastFrame` |
| the track | **ElevenLabs Music v1** `t2a-elevenlabs-music-t2a` | none — the brief is the prompt |
| accents | **ElevenLabs Sound Effects** `t2a-elevenlabs-sfx` | |

**GPT Image 2 for anything with letterforms in it.** That is the whole reason it is
here; it is slower and dearer than the alternatives and it is worth it exactly where
type is.

**Never Krea for a frame.** It reinterprets what you wire it, which is fatal to a
look-locked set, and it rate-limits hard when fired in a batch.

**Set every resolution explicitly.** Stored defaults fail, and the casing differs
between families (`"2k"` lowercase for GPT Image 2, `"2K"` uppercase for Nano Banana
Pro) — a wrong value fails the *entire* changeset, not one node.

## Gotchas

```
API SHAPE
flora_add_nodes        CANNOT create edges. Use flora_apply_changeset to add and
                       connect atomically in one call.
flora_get_node_details takes `ids`, not `node_ids`. Max 20 per call.
flora_generate         takes a single `id`, not an array.
text edge overrides    a node wired {to: <node>, in: "text"} runs the upstream
                       text, and its own prompt is dead weight. The fallback is
                       SILENT - a failed text node lets the image node generate
                       from its own stored prompt and report done. Confirm a
                       chain by reading the text node's output.text.
imageUrl               the connect handle is `imageUrl`, not `image_url`. There
                       is no `imageUrls` - wire TWO imageUrl edges into one video
                       node and it resolves to firstFrameLastFrame by itself.
polling                fire all generations in one pass, then poll once centrally
                       over all node ids. Never flora_wait_for_generation.
spend modal            the first flora_generate of a session returns ok:false
                       with spend_approval_pending. Re-fire everything; the
                       second identical call goes through.
navigator.modelContext missing on first load more often than not. Reload the
                       project URL keeping webmcp_embed=1.
short ids              nX ids are reassigned between sessions. Wire by UUID.
canvas read            truncates at 300 nodes. Filter, do not page.

MODEL PARAMS
Seedance 2.5           no camera-lock param and NO SEED. Write the lock into the
                       prompt; accept that takes are not reproducible.
Seedance duration      "4".."30" as STRINGS, or "auto". Not integers.
GPT Image 2            resolution "1k"/"2k"/"4k" lowercase.
Nano Banana Pro        resolution "2K"/"4K" uppercase.
generate_audio         agent-gated; including it rejects the WHOLE changeset.
changeset validation   ONE bad param fails the ENTIRE changeset. Probe a single
                       node when unsure - the error returns valid_values.

RATE LIMITS
Krea                   rate-limits hard. ~5s spacing or lose most of the batch.
GPT / NBP / Seedance   no pacing needed. Fire concurrently.
3D / heavy queues      space kickoffs ~5s; a dozen at ~1s apart mostly return
                       CLIENT_KICKOFF_THREW.

LOCAL TOOLING
ffmpeg                 not on PATH on this machine. cut.py falls back to the
                       static build inside imageio_ffmpeg automatically. There
                       is no ffprobe in that build, so cut.py parses durations
                       out of the ffmpeg header instead.
media urls             fetchable with no credentials. Read the full url, never
                       reconstruct it - the path contains the date. Fetch each
                       one as its own plain command and check the byte sizes;
                       curl inside $(...) with a heredoc silently writes 0 bytes.
```

### Three ffmpeg traps this engine already encodes

Measured here, each one after it broke a render:

- **Never chain `xfade`.** A five-shot chain emitted 239 frames stamped across
  **2.01s instead of 7.60s**, and CFR conversion then dropped 178 of them — while
  exiting 0 and producing a playable file. `cut.py` renders each transition as its
  own pairwise piece and concatenates losslessly.
- **`tpad` and `setpts` both clear the frame rate** to `1/0`, and `xfade` refuses a
  source that is not declared CFR. The rate has to be re-asserted after each.
- **A still bounded by an input `-t` loses its last frame.** Every still came back
  exactly 1/fps short and every shot after it slid. Bound stills at the output.

## Naming and where it lands

```
the skill      flora-launch-video
the folder     <project>/Deliverables/<Title>-launch/
  cut.json                 the edit. the source of truth. keep it.
  <Title>.mp4              the master, 1920x1080
  <Title>-9x16.mp4         vertical cutdown
  <Title>-1x1.mp4          square cutdown
  <Title>-contact.png      first/mid/last of every shot
  shots/                   the i2v outputs at full resolution
  frames/                  the stills, including the endcard
  track.mp4                the music
```

**Always write to `<project>/Deliverables/`.** Create it if it is missing. Never leave
the film in a scratch directory, in `~/Downloads`, or loose in the project root.
Prefix every subfolder with the title — `Deliverables/` is shared across runs and a
bare `shots/` in there belongs to nobody.

**Keep `cut.json` and `shots/` beside the master.** They are what make the film
revisable; without them the next change is a regeneration. Check whether a folder for
this title already exists before writing, and say so rather than overwriting it.

**Say the full path in the final message.**

## The audit

Run it on the contact sheet, before anyone watches the film. Score each shot out of 5:

| axis | what a 5 looks like |
|---|---|
| look match | indistinguishable from the plate — same ground, light, palette, lens |
| type | every letterform correct and legible at the size it appears |
| motion | one clear intentional move; no warping, no drift in the geometry |
| window | the shot is *good* across the whole window the cut takes, not just at 0.0 |

Anything at 3 or below gets a **new window first**. Only regenerate if no window in
the five seconds works. Run the audit as an on-canvas text node with the rubric in
the node — and **on Opus 4.8, not Opus 5**, which refuses image audits that read
people.

## The client surface

If someone will open this again without you, `client-task` applies on top: CAPS group
names (`WRITE THE SCRIPT`, `SET THE LOOK`, `MAKE THE SHOTS`, `PUT IT TOGETHER`), one
lowercase caption per group, and a `NOT RIGHT? JUST SAY SO` critique group.

The thing to teach them is one sentence: **the pictures are made once, the timing is
free.** Then hand them `--pace` and let them drive it themselves.

## Failure atlas

| symptom | cause | fix |
|---|---|---|
| the wordmark warps or misspells | type was spoken to a video model | make it a still and hold it in the cut |
| shot 3 onward is a frame late | a source came in short of nominal | already handled — `tpad` tops it up; check `--check` for the flag |
| the film is 2s long and plays 239 frames | chained xfade collapsed the timebase | pairwise transitions, then concat. Never chain. |
| the whole cut feels amateur | shots not on the beat | set `bpm` and `grid: "beat"` |
| twelve shots that don't look related | each frame prompted independently | one look plate, one look block, pasted verbatim |
| the re-roll came back different | Seedance has no seed | move the window instead; never re-roll a take you liked |
| every shot opens static | i2v eases in from the still | start the window at `in: 0.5`, not 0.0 |
| the vertical crops the headline off | centre-crop instead of pad | `--resizes` pads; full-bleed needs its own generation |
| the music ends before the picture | dissolves eat their duration out of the timeline | `--check` prints usable track vs timeline; it is already accounted for |
| a picture is right but the pacing is wrong | — | this is never a regeneration. `--pace`, or edit `dur`. |
| an image node reports done but ignored its chain | upstream text node failed; the fallback is silent | read the text node's `output.text` |
| `--check` says OVERRUN | the window runs past the end of its source | `--fit` pulls it earlier, then stretches. Do not regenerate. |

## Reporting back

The master, the contact sheet, and the runtime. Name the strongest shot and why, name
any shot whose window is compromised, and state plainly which of the two cutdowns is
a real deliverable and which is a letterbox. Then say the sentence that matters:
**re-pacing costs nothing, so ask for it.**
