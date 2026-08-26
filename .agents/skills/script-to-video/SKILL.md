---
name: script-to-video
description: >
  Turn a script or narrative into an ordered set of animated clips — script to shot
  list, shot list to consistent keyframe stills, keyframes to motion — through FLORA's
  MCP server. Runs as a staged pipeline with an explicit approval gate between stages,
  because each stage spends money animating the previous stage's output. Use for
  "turn this script into a video", "storyboard this and animate it", "make a video
  from this scene", or any script → image → video request. Do not use for a single
  still image, and do not use for a batch of unrelated independent items.
---

# script-to-video

## What it is

**A staged pipeline, not a batch.** A set of unrelated items can all be fired at once,
because no item's result changes what any other item should be. This is the opposite
case: the shot list decides what the keyframes are, and the keyframes are what the
video stage spends its money animating.

That dependency is the whole design constraint, and it is a financial one. Measured on
FLORA's current catalog:

```
cheapest still   t2i-flux-2-klein-4b     $0.004
cheapest motion  i2v-wan-2.2             $0.121   (measured, settled)
typical motion   i2v-kling-2.5           $0.327
                 i2v-seedance-pro        $0.347
```

**A clip costs 30–90x its keyframe.** So a keyframe that drifted off-style is not a
wasted still — it is a wasted still *plus* the far more expensive clip built on top of
it, discovered only after both are paid for. Every gate in this skill exists to catch a
mistake while it is still worth $0.004 instead of $0.35.

## The law

> **Never animate an unapproved frame.**
> Each stage ends with the user looking at what it produced and saying go. The gates are
> the product; the generations are just what happens between them.

## The three stages

```
1  SCRIPT    -> shot list      free          gate: user approves the list
2  SHOTS     -> keyframes      ~$0.004 each  gate: user approves the SET
3  KEYFRAMES -> clips          ~$0.12-0.35   deliver ordered clip URLs
```

---

## Stage 1 — script to shot list

Free. Nothing is spent, so this is where to be generous with thinking.

Break the script into discrete shots. One shot is one continuous camera setup — when
the camera cuts or the subject changes, that is a new shot. Give each:

```
id        s01, s02…      stable, and it stays with the shot through all three stages
frame     what is in it  subject, setting, what the viewer sees
camera    how it moves   angle, lens feel, push/pan/static
duration  rough seconds  most i2v models default to 5s clips
```

Show the **full list** and stop. Do not generate a single pixel before the user has
read it. A shot list is cheap to rewrite and a keyframe set is not, so an argument
about shot 4 belongs here — this is the cheapest gate in the pipeline and the one most
worth spending conversation on.

State the projected cost of the next two stages while the user is reading:

> 9 shots. Keyframes ≈ $0.04, clips ≈ $1.10 at $0.121 each. Approve the list?

---

## Stage 2 — shot list to keyframes

The hard problem is **consistency**. Nine independent generations of "the same
character" produce nine different people. Nothing in the model carries identity between
calls, so identity has to be carried by you.

### Lock one reference first

Pick a single image and pass it into every keyframe generation:

- **User-supplied** character sheet, style frame, or product shot — always prefer this.
- **Otherwise**, generate keyframe 1 alone, get it approved, and **that becomes the
  reference for every remaining shot.** Shot 1 is generated once and judged once; shots
  2–N inherit from it.

The reference is locked before the batch fires. Changing it mid-batch means the shots
before and after disagree, which is the exact failure this stage exists to prevent.

### How the reference actually reaches the model

> **Image inputs to a generation are `params.image_url` — singular, a plain string.**

Measured across `i2i` and `i2v`: a singular `image_url` is the mechanism. The plural
array form is accepted without complaint, **silently ignored, and still billed** — you
get a text-to-image render of your prompt with the reference nowhere in it, and no
error anywhere to tell you.

Confirm the field on the model you actually chose before firing the batch. Call
`models.list()` and read its `params`. Two things you will find:

- Reference inputs are usually **implied by the endpoint's modality prefix** (`i2i-`,
  `i2v-`) rather than declared as a named parameter. An `i2v-` model takes an image
  because it is an image-to-video endpoint; you will not see `image_url` in its
  parameter list.
- **A param value that is not in the model's enum is not rejected.** It is accepted,
  the run completes, it bills, and the model silently uses its default. Only an unknown
  *model id* returns a clean error. So validate your `aspect_ratio` and `resolution`
  against the model's own options before firing N of them.

### Fire the batch, then poll once

With the reference locked the shots are independent, so fire them together. Firing them
one at a time turns one wait into N waits for no benefit.

```ts
const settled = await Promise.allSettled(
  SHOTS.map((shot) =>
    client.generations.create({
      workspace_id: WS, project_id: PRJ, type: "image",
      prompt: `${shot.frame}. ${STYLE}`,
      model: "t2i-flux-2-klein-4b",
      params: { image_url: REFERENCE, aspect_ratio: "landscape_16_9" },
    }),
  ),
)

const fired: Record<string, string> = {}   // run_id -> shot id
const rejected: string[] = []
settled.forEach((r, i) => {
  if (r.status === "fulfilled") fired[r.value.run_id] = SHOTS[i].id
  else rejected.push(`${SHOTS[i].id}: ${r.reason?.message ?? r.reason}`)
})
return { fired, rejected }        // RETURN the map — variables do not persist
```

**`Promise.allSettled`, never `Promise.all`.** One rejected create must not discard the
run ids of the shots that did fire — those are billed and would become untrackable.

Then poll the whole batch with **one** call per cycle, not one call per shot:

```ts
const page = await client.generations.list({ project_id: PRJ, limit: 100 })
const byRun = Object.fromEntries(page.getPaginatedItems().map((g) => [g.run_id, g]))
```

Pass `limit: 100` explicitly — 100 is the API maximum and the default is lower, so a
long shot list silently reports its tail as unfinished forever. Key on
`status === "completed"`, never on `progress`: a *failed* run also reports
`progress: 100` with a populated `completed_at`.

### View every keyframe against the reference — all of them

**This is the gate that pays for the skill.** After the batch settles, look at each
keyframe *before* anything is animated. Not a sample. Every one.

The arithmetic is the argument: a drifted keyframe caught here costs $0.004 to redo. The
same keyframe caught after Stage 3 costs $0.004 **plus** the $0.12–$0.35 clip that was
animated from it, and the clip has to be regenerated too.

Judging is free. FLORA has image-to-text models that cost **0 credits** and return in
about six seconds:

```
i2t-gemini-3-5-flash-lite-i2t   0 credits   ~4s
i2t-gemini-3-6-flash-i2t        0 credits   ~6s
i2t-gemini-3-7-flash-i2t        0 credits   ~6s
```

> **Judge inputs are plural arrays. This is the opposite of generation inputs.**
> `i2t` takes `params.image_urls: [url]`. `v2t` takes `params.video_urls: [url]`.
> Passing the singular form makes the model answer **having seen nothing** — and a blind
> judge is an agreeable judge. Measured: handed `image_url` instead of `image_urls`, a
> judge passed a photo of a black ceramic coffee dripper against a goal describing a
> steel water bottle on a wooden table in hard sunlight. `verdict: pass`, zero defects.

So, per keyframe:

```ts
const check = await client.generations.create({
  workspace_id: WS, project_id: PRJ, type: "text",
  model: "i2t-gemini-3-7-flash-i2t",
  params: { image_urls: [REFERENCE, keyframeUrl] },   // PLURAL. ARRAY.
  prompt:
    "IMAGE 1 is the style reference. IMAGE 2 is a new keyframe.\n" +
    "First DESCRIBE both, then judge whether IMAGE 2 holds the same character, " +
    "palette, lighting and rendering style as IMAGE 1.\n\n" +
    'Return ONLY JSON: {"ref":"...","frame":"...","consistent":true|false,"drift":["..."]}',
})
```

Two details that decide whether this works:

- **Demand the description before the verdict.** Asking for a ruling first lets the
  model answer from your prompt text rather than from the pixels, and it rubber-stamps.
  With the description forced first, the same judge caught a softbox edge intruding on a
  frame that looked clean to the eye.
- **Strip markdown fences before parsing.** The same model returns bare JSON on one call
  and ` ```json ` fenced on the next, with no change to the prompt.
- Passing the **same URL twice** de-duplicates to one image — the model will report the
  second as missing. Reference and keyframe must be genuinely different URLs.

Then present the set — shot id, keyframe URL, and any drift the judge named — and get
**one clear approval on the whole set.** Re-shoot the drifted frames and re-gate. Only
then does Stage 3 exist.

---

## Stage 3 — keyframes to motion

### Quote from the video catalog, never from the image stage

Nothing about the still stage's cost or timing carries over. Pull real numbers before
firing:

```ts
const models = await client.models.list({ type: "video", limit: 100 })
const m = models.getPaginatedItems().find((x) => x.model_id === CHOICE)
// m.estimated_credits, m.estimated_seconds, m.params
```

Measured spread across `i2v` endpoints: **134 to 900+ credits**, and
`estimated_seconds` from **30 to 360**. Both vary by an order of magnitude, so a number
you remember from a previous run is not a number you may quote.

**`estimated_credits: 0` does not mean free.** Several endpoints — the Seedance 2.5
family among them — report `0` credits alongside a 300-second estimate. That is a gap
in the catalog, not a price. Never present a zero as free; fire one clip, read the
settled `charged_cost`, and quote from that.

Total the real figure and confirm before firing:

> 9 clips × $0.121 = $1.09. This is the expensive stage and it is not refundable if
> you dislike the motion. Go?

### Use more than one reference when the endpoint supports it

Some endpoints accept several reference images per generation, and more references
means tighter consistency — the model has more evidence of what the character and world
look like. Reach for it when it is available.

**But you have to look it up, not assume it.** Reference capacity is *not* declared in
`models.list().params` — video models expose only `duration`, `aspect_ratio`,
`resolution`, `seed` and similar. The capability is signalled by the **endpoint's
modality prefix** instead:

```
i2v-    one image drives the clip
r2v-    references-to-video — built for multiple reference inputs
m2v-…-vref   reference-conditioned variants
```

Endpoints like `r2v-seedance-2-5`, `i2v-gemini-omni-r2v-fal` and
`i2v-grok-imagine-i2v-references` exist for exactly this. If a specific capacity matters
to your plan, **verify it at runtime with `search_docs` or a single probe clip** rather
than trusting a remembered figure — the catalog does not publish per-endpoint reference
limits, and they change.

Where multiple references are supported, pass the locked style reference *plus* the
neighbouring approved keyframes, so each clip is anchored to the shots either side of it.

### Fire and poll as separate calls — this is not optional

The code sandbox gives roughly **five minutes total per `execute` call**, 30 seconds per
HTTP request. Video endpoints report `estimated_seconds` up to **360**. Some clips
cannot finish inside a single call *by design*.

Building a loop that waits for them returns a **502 Bad Gateway** and you lose the
run-id map — while the clips keep generating and keep billing, now untrackable. This was
hit twice while testing this skill: once waiting on a two-round loop, once on a poll
that also ran a judge.

So:

```
call 1   fire every approved keyframe, RETURN { run_id -> shot_id }
call 2   poll generations.list({ project_id, limit: 100 }), return what is terminal
call 3   poll again if anything is still running
```

Carry the map forward explicitly in each call. Variables do not persist between them.

### Read error_message, not just error_code

A moderation or content refusal frequently arrives wearing a **generic infrastructure
error code**. Codes like `GPU_PROVIDER_ERROR` and `GENERATION_NO_RESULT` are classified
as transient-retryable, but their message often says otherwise. A real measured example:

```
error_code:    GPU_PROVIDER_ERROR
error_message: "Your request was rejected by the safety system. …
                safety_violations=[sexual]."
```

The code says retry. The truth is that the prompt will be refused every time.

**So classify on the code, then read the message before acting.** If the message names
safety, moderation, a refusal or a policy, do not retry — rewrite the shot's prompt or
report it back. At $0.12–$0.35 a clip, blind-retrying a filtered prompt across a shot
list is precisely the spend this skill exists to prevent.

Genuinely transient failures — timeouts, provider unavailability — are worth exactly one
retry. A failed run generally does not cost, but **a retry is a new generation and does.**

---

## The assembly boundary

**This pipeline delivers an ordered set of clips. It does not deliver a cut.**

There is no server-side timeline, no transition rendering, and no final export on this
surface. Say so plainly rather than implying a finished film is coming:

> Nine clips, in script order, ready to drop on a timeline. Assembly, transitions,
> audio and grading happen in your edit tool — Premiere, Resolve, CapCut, whatever you
> use. I can't produce a single cut file from here.

Deliver in script order, keyed by shot id, so the set can be imported and laid down
without cross-referencing anything:

```
SHOT  DURATION  CLIP
s01   5s        https://media.flora.ai/…mp4
s02   5s        https://media.flora.ai/…mp4
s03   5s        https://media.flora.ai/…mp4  (re-shot — first take drifted on palette)

9 clips, script order. Total $1.09. Keyframes $0.04. Judging free.
```

Never reorder the clips to be helpful, and never silently drop a failed shot — a gap in
a numbered sequence is a bug the editor will find at the worst moment. Name it.

Video URLs may carry a query string (`?tr=orig`). **Report the full URL**; truncating at
the extension breaks the link. Media URLs are public, unsigned and permanent, so pasting
one into a shared transcript discloses that asset — worth a word when the script is
unreleased.

**You cannot watch the clips.** Every judgement in your report came from a model.
Attribute it that way and let the user overrule it.

---

## Gotchas

```
STAGE GATING
never animate          an unapproved frame. A drifted keyframe caught in Stage 2 costs
                       $0.004; caught in Stage 3 it costs that plus a $0.12-0.35 clip.
gate 1 is free         and it is the cheapest place to lose an argument about shot 4.
one approval           on the FULL keyframe set, not a sample, before Stage 3 fires.

CONSISTENCY
lock the reference     before the batch fires, never mid-batch.
no reference given     -> generate shot 1 alone, approve it, and use it as the
                       reference for every remaining shot.
params.image_url       SINGULAR STRING for generation inputs (i2i, i2v). The plural
                       array is silently ignored and still billed.
params.image_urls      PLURAL ARRAY for judging (i2t). v2t takes video_urls.
                       This is the OPPOSITE of the generation convention. Getting it
                       wrong makes the judge answer blind, and blind judges pass
                       everything.
describe first         force `observed` before `verdict` or the judge rules from your
                       prompt text instead of the pixels.
markdown fences        appear inconsistently on identical prompts. Strip before parsing.
same url twice         de-duplicates to one image. Reference and frame must differ.
free judges            i2t/v2t gemini 3.5-flash-lite, 3.6-flash, 3.7-flash = 0 credits.

VIDEO STAGE COST + TIMING
never reuse            still-stage numbers. Pull estimated_credits and estimated_seconds
                       from models.list({ type: "video" }) every time.
measured spread        134 to 900+ credits; 30 to 360 estimated seconds.
estimated_credits: 0   is a CATALOG GAP, not free. Seedance 2.5 reports 0 with a 300s
                       estimate. Fire one, read settled charged_cost, quote from that.
confirm the total      before firing. This stage is not refundable for taste.

REFERENCE COUNT
not in params          video models declare only duration/aspect_ratio/resolution/seed.
                       Reference capacity is signalled by the modality prefix — r2v-,
                       i2v-…-references, m2v-…-vref — not by a named field.
verify at runtime      with search_docs or one probe clip. Do not trust a remembered
                       per-endpoint reference limit; the catalog does not publish them.
more refs = tighter    consistency. Pass the style reference plus neighbouring approved
                       keyframes where the endpoint accepts them.

FAILURES
error_message          over error_code. GPU_PROVIDER_ERROR and GENERATION_NO_RESULT are
                       classified retryable but routinely carry a moderation refusal.
                       If the message names safety or policy, rewrite — never retry.
transient only         timeouts and provider-unavailable get exactly one retry.
                       Failures are generally refunded; retries bill again.
progress is not done   failed runs report progress: 100 and a completed_at. Key on
                       status === "completed" AND outputs being present.

SANDBOX
~5 min per call        30s per HTTP request. i2v estimates reach 360s, so some clips
                       cannot finish inside one call by design.
fire and poll apart    a waiting loop returns 502 and loses the run-id map while the
                       clips keep billing. Hit twice while testing this skill.
return the map         run_id -> shot_id, every call. Variables do not persist.
Promise.allSettled     never Promise.all — one rejection must not discard the run ids
                       of shots that did fire.
limit: 100             explicit on generations.list. The default is lower and silently
                       truncates a long shot list.

ASSEMBLY
no server-side cut     no timeline, no transitions, no export. Deliver ordered clip
                       URLs and say assembly happens in the user's edit tool.
full URLs              clips may carry ?tr=orig. Truncating breaks the link.
never reorder          or silently drop a shot. A gap in a numbered sequence is a bug.
```
