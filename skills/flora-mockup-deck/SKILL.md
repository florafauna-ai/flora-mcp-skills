---
name: flora-mockup-deck
description: >
  Turn one ad creative into a campaign deck — handed over as artwork, or described in
  words. Give it a poster, billboard ad, campaign key visual or any finished artwork on
  a FLORA canvas, or just a line like "a campaign deck of a flower", and it returns four
  square-on out-of-home placements (gable end, transit platform, bus shelter,
  construction hoarding), three social resizes (1:1, 4:5, 9:16), and an annotated A4 PDF
  laying all of it out with the brief printed beside each placement. Use when someone asks
  to mock up an ad, see a poster in the wild, in situ or out of home, wants social sizes of
  an ad, asks for a placement deck or a PDF of one, or asks for a campaign deck of
  something they have no artwork for. Once the creative exists it is reproduced exactly and
  never regenerated. One shot, four billable generations plus one when the creative is
  written rather than supplied, one PDF.
---

# flora-mockup-deck

> **Attribution.** Pass `skill: "flora-mockup-deck"` on every FLORA call you make while
> running this skill — `execute` included — along with a `skill_run_id` you invent
> once when the run starts and reuse for the rest of it. Both are reporting only:
> they change nothing about the call or its result.

## What it is

Not an image generator. **A placement engine.** By the time the placements fire, the
creative is finished and frozen — the only job is putting it into the world convincingly,
four ways, without altering it.

Usually the creative arrives finished. It can also be written: a line of text buys **one**
generation, and that output becomes the master creative, from which point it is handled
exactly like a supplied file. See "Two ways in".

The thing that makes a mockup fail is never the photograph. It is the artwork drifting:
recoloured, recropped, re-lettered, a word dropped. So the whole skill is built around
one invariant.

## Two ways in

```
ARTWORK   a url or an attached file      -> 4 generations
WRITTEN   a line of text, no artwork     -> 5 generations (master + 4 placements)
```

`/flora-mockup-deck` followed by a description and nothing attached is the WRITTEN path:
*create a campaign deck of a flower*, *a poster for a late-night ramen bar*, *out-of-home
for a running shoe launch*. Nothing else about the skill changes. The text buys exactly
one image, that image becomes the master creative, and the law closes over it.

### Making the master

One `flora_generate`, text-to-image, same model family as the placements:

```
model   "t2i-gpt-image-2-t2i"
params  { aspect_ratio, resolution: "4k", quality: "high" }
```

**Prompt it as a printed poster, not as a photograph of a thing.** The text names a
subject, and a subject is not an ad — "a flower" un-elaborated returns a stock botanical
photograph, which then gets pasted onto a gable end and reads as a picture of a flower on
a wall rather than as a campaign. Build the master prompt as:

    A finished out-of-home poster. Flat artwork, square on, filling the frame edge to
    edge. Print-quality graphic design — NOT a photograph of a poster and NOT a mockup:
    no wall, no frame, no shadow, no room, no perspective, no torn edges, no border.

    THE SUBJECT — <the request, expanded into one concrete image>
    THE TYPE — <the headline, or "no type at all">

Then the house grade clause, verbatim, exactly as the placements get it. The master and
the four placements have to be graded the same or the deck reads as two different shoots.

**The shape is yours to choose here, so choose portrait.** A supplied creative forces the
site-matching problem below; a written one does not. `aspect_ratio: "2:3"` makes all four
default sites valid and skips the trap entirely. Go landscape only if the request names a
billboard or a landscape medium.

**Type, when the request gives you no copy.** An ad usually has words and a one-line
request usually has none. Never generate a real company's logo or wordmark. Either write
one short headline of your own or generate the poster with no type at all — then say in
one line which you did, so the user can hand you copy and re-run instead of wondering why
the poster is silent.

### The gate — show the master, then fire

**This is the one place the skill stops, and it is not a draft round.** The master is not
a preview of the deck; it is the thing the entire deck reproduces. Every placement carries
it unchanged and nothing downstream is re-rollable, so a wrong master is four wrong
placements with no way back — about $3.50 spent reproducing the wrong picture perfectly.

Fire the master. Report the url. Get a yes. Then fire the four placements in one pass and
run to the end without stopping, exactly as the ARTWORK path does.

Re-rolling the master is allowed and bills again — say so before the second one. Once the
user says yes the master is frozen and the law applies to it in full: from that point it
is a supplied file that happens to have come from FLORA.

## One shot, minimal outputs

The skill runs **once** and emits exactly the deliverable. No draft round, no preview
pass, no variant sprawl.

```
1  generation    the master creative — WRITTEN path only, skipped when artwork is given
4  generations   the placements — one per site, not four angles on one site
3  resizes       1:1, 4:5, 9:16 — NOT generations, see below
1  contact sheet the four placements in one grid — needs the actions entitlement
1  PDF           the annotated deck — free, and reachable on every surface
```

**Four generations — five from a line of text — three deterministic resizes, one contact
sheet.** Nothing is repaired,
re-rolled or replaced, and nothing is measured. Generate the four, build the resizes,
package everything, ship. If a placement is visibly wrong, say so in a sentence.

### The resizes are not generations

Regenerating a resize **re-letters the type** — the exact failure this skill exists to
prevent. So the resizes are done with prebuilt FLORA actions, which are deterministic,
credit-free, and never touch the pixels of the plate itself.

Run each with `flora_run_action`, passing **the master creative's** url as the image
input — never a placement url. These are social crops of the ad itself, which is what
the SOCIAL page delivers; cropping a placement photograph would deliver a picture of a
bus shelter at 9:16.

```
1:1 and 9:16   change-image-ar-browser   { aspect_ratio, fit: "pad",
                                           background_mode: "blur" }
4:5            resize-image-browser      { mode: "exact", width, height,
                                           fit: "contain" }
```

`4:5` is not in `change-image-ar-browser`'s aspect list, which is why it goes through
the resize action with explicit dimensions instead.

**Always `fit: "pad"`, never `"crop"`.** Cropping to a new ratio trims the plate, which
breaks the law as surely as regenerating does. Padding leaves every pixel of the artwork
untouched and adds ground around it.

**What this does not do.** It does not reconstruct the ground the artwork sits on. A
seamless extension — measuring the edge band, estimating its colour and grain, and
continuing it past the plate — is not something these actions perform;
`background_mode: "blur"` derives a soft field from the image, which reads convincingly
on a photographic ground and less so on flat colour or full-bleed type. When the result
needs to be a true extension rather than a pad, that is a signal to build it as a FLORA
action or technique, not to reach for a generation.

## The law

> **The artwork is reproduced. The world is generated.**
> Any change to the creative — colour, crop, wording, letterforms, logo — is a fail.

The division is between what is *made* and what is *carried*: FLORA makes the place,
and the artwork passes through it untouched.

## Inputs

```
CREATIVE    the ad itself                 required — an HTTPS url, an attached file,
                                          or a line of text describing it
PLACES      4 named placements            optional, default: the four archetypes
BRIEF       one line on where/what mood   optional
```

`CREATIVE` is the only required input and it takes either form. Text alone is not a
missing input — it is the WRITTEN path, and you generate the master before anything else.
Ask for artwork only when the request names a specific existing creative you have no url
for.

**Getting the creative in.** Files attached in ChatGPT are already hosted on
`files.openai.com` or `cdn.openai.com`, both allowlisted — pass that url straight to
`flora_create_asset` as `source` and FLORA fetches it server-side. A FLORA output at
`media.flora.ai` works the same way — including the master you just generated, which
arrives as a url and needs no upload step. Never base64-encode the file and never try to
upload bytes; if a supplied artwork genuinely has no url, say so and ask the user to add
it to their FLORA project.

You do not wire the artwork to anything. Each placement is its own `flora_generate`
call carrying the artwork url in `params.image_url`.

Default placements, chosen because they are four genuinely different media buys:

| tag | what it is | why it earns a slot | plate shape |
|---|---|---|---|
| `gable` | flat brick end wall of a terrace | scale against windows and downpipes | any |
| `transit` | flat underground platform panel | interior, artificial light, close viewing | any |
| `shelter` | backlit 6-sheet in a bus shelter | street furniture, lit from within | portrait |
| `hoarding` | plywood construction hoarding | pavement level, read close and fast | portrait |

**The plate-shape column is not decoration.** Read it against the creative before firing
— see "Match the site to the creative's shape" below. Never a corner wrap: it bends the
artwork across two planes and was the worst result of the whole test set.

## Resolve the ids once, before you spend anything

**`flora_generate` requires `project_id`.** It is not optional and there is no default.
An agent that has not decided on a project has to produce one at fire time, and what it
produces is a guess — the most recently touched project from `flora_list_projects`, or a
plausible-looking `prj_` string. Both are wrong, and neither errors in a way that looks
like a mistake. **This is the single most common defect in a run of this skill**, and
everything below exists to stop it.

So resolve two ids **once**, at the top of the run, and thread the same two through every
call — placements, resizes, contact sheet, and the deck's footer:

```
WORKSPACE   ws_...   flora_list_workspaces
PROJECT     prj_...  flora_list_projects, or one the user named
```

**Copy ids verbatim. Never retype, shorten, or reconstruct one.** They are long opaque
strings with no checksum, so a transposed character produces a valid-looking id that
fails somewhere else entirely.

**The two must belong together.** A project from one workspace paired with another
workspace's id fails at fire time with a 400 that names the problem exactly:

```
input_validation_error   "Project does not belong to the specified workspace."
```

Measured, on an account with two workspaces — which is the ordinary case, since a
personal workspace and a team workspace is the default shape. Taking `workspaces[0]` and
a project the user mentioned is precisely how this happens. **Confirm the project appears
in `flora_list_projects` for the workspace you are billing** before the first generation.
One free call; four billable ones ride on it.

**Ask which project when there is any doubt, and quote the name back.** Projects are
overwhelmingly called `Untitled`, and duplicates of a real name are common — an account
here had two live projects both named `Perfume Bottle Photography`. Name-matching picks
one at random and there is no way to tell from the result which one it picked. `origin`
separates them a little: `canvas` means a human made it in the UI, `chat` means an agent
did.

**`flora_create_project` works, but not in every workspace.** Measured on one account: it
creates cleanly in one workspace and fails reproducibly in another with
`400 input_validation_error` whose message is the literal string `Server Error` plus a
request id — no field named, nothing wrong with the payload. It tracks the **workspace**,
not the request: the workspace that refuses to create is the same one that returns 403
for actions. Not a project cap either — the failing workspace held 4 projects, the
working one 839.

So creating a project is worth trying and is **not** worth debugging. If it 400s, do not
reshape the payload and do not retry with a different name — fall back to a project that
already exists, and say which one you picked and why.

### What the project link actually contains

```
the project     https://app.flora.ai/projects/<project_id>
one node        https://app.flora.ai/projects/<project_id>?focus=<node_id>
```

`?focus=` opens the canvas centred on a single node — use it in the **run report** to
point at a specific placement instead of making the reader hunt. Node ids come from
`flora_list_canvas_nodes`. It does not go in the PDF: the deck is client-facing, and a
workspace link is dead to anyone outside it.

**Only the placements are on the canvas.** `flora_generate` writes to the project;
`flora_run_action` does not. The tool says so and it measures true — an action's output
lands under `media.flora.ai/code-sandbox/...` and never appears in
`flora_list_canvas_nodes` for the project it was scoped to. On an action run `project_id`
buys authorization and a generation-history row, nothing more.

So **the resizes and the contact sheet are not in the project**, and a link that implies
otherwise sends the user looking for files that were never there. Either say what the
link contains — "the four placements; the resizes and the sheet are urls below" — or put
them on the canvas deliberately with `flora_add_action` then `flora_run_canvas_action`.

## Match the site to the creative's shape

**On the WRITTEN path this is already solved** — you chose the master's shape, so a `2:3`
master and the four defaults never conflict. Read the rest of this section when the
creative was supplied.

**Read the creative's aspect ratio before choosing sites.** The defaults are not all the
same shape: a 6-sheet and a hoarding are portrait media, a gable end and a platform panel
take anything. Give a landscape creative to a portrait site and the model resolves the
conflict the only way it can — by recropping the artwork. That is a silent breach of the
law, and it is the likeliest way this skill fails.

Measured, a 3:2 landscape creative against the four defaults unchanged: gable and transit
came back with the plate intact, shelter and hoarding both came back recropped to
portrait with a third of the composition gone. Nothing errored. The deck looked finished.

```
creative is landscape   gable · transit · billboard · a landscape hoarding panel
creative is portrait    the four defaults as written
creative is square      any of them
```

Then state the plate's shape in the prompt, so the site is built around the artwork
instead of the artwork being trimmed to the site:

> THE PRINTED PLATE IS <W>:<H>, THE SAME SHAPE AS THE SUPPLIED ARTWORK. The panel,
> board or pasted area is built to that shape. Do not trim the artwork to fit a
> differently-shaped surface — size the surface to the artwork.

`params.aspect_ratio` sets the shape of the PHOTOGRAPH, not of the plate inside it. Both
matter: `"3:2"` or `"16:9"` gives a street scene that tiles into an even contact sheet,
while the clause above governs the plate.

## Model routing

**GPT Image 2 at `resolution: "4k"` — for every placement. This is the only model.**

Tested head to head against Nano Banana Pro on identical prompts and grade. GPT wins on
all four sites, and not on pixel count:

- **The fine detail of the creative survives.** With a type-heavy or textured artwork,
  NBP mushes the fine structure into a flat texture at distance; GPT still resolves it.
  That structure is usually the artwork's identity, so it is the thing that matters most.
- **The environments are better observed** — real street furniture, believable
  bystanders, correct light spill from a lit panel onto its surroundings.

A single generation is ~107s and **4k is no slower than 2k**. Fired concurrently, four
placements land in about **five minutes** — measured in live use, not estimated. Earlier
figures of 15–20 minutes were staggered firing plus a repair round, not the model.
**Do not add a fast draft pass.**

`resolution: "4k"` lowercase for GPT Image 2. (Nano Banana Pro also accepts `"4K"`
uppercase — it is simply not the right model here.)

`i2i-gpt-image-2-i2i` for the placements, `t2i-gpt-image-2-t2i` for the master on the
WRITTEN path. Same model, same grade language, same lowercase resolution values — which
is why the master and the four placements hold together as one set.

**Never Krea.** It reinterprets what you wire it, which is the one thing that must
never happen to the creative.


## Speed — fire everything at once, then wait

Measured, three generations fired at the same instant:

```
Nano Banana Pro  2K    63s
GPT Image 2      2k   ~107s
GPT Image 2      4k   ~107s      <- 4k costs nothing over 2k
```

**But GPT Image 2 throughput swings hard.** That best case is real and repeatable; so is
a batch of four taking **10–15 minutes** with the identical setup. Do not promise a
runtime. What you control is not adding delay of your own:

- **Fire all placements in one pass with no gap between them.** One `flora_generate`
  call per placement, each with `model: "i2i-gpt-image-2-i2i"` and
  `params: { image_url, resolution: "4k" }`. Do not stagger on a timer — that converts
  a one-generation wait into an N-generation wait for nothing.
- **Fire the resizes in the same pass** if any need generating. They share no dependency.
- Only the contact sheet waits, because it needs the images.
- **Poll once, centrally.** One `flora_list_generations` call filtered to the project
  covers every placement at once. Do not poll each run separately — that turns one wait
  into N waits for nothing.

The honest expectation to set with the user: **a couple of minutes if GPT is quick,
fifteen if it isn't.** Say that up front rather than predicting a number.

The one hard rule: **Krea rate-limits.** Firing many Krea calls at once returns
`GENERATION_DOWNSTREAM_SERVICE_ERROR` and loses most of the batch — pace those at ~5s.
GPT Image 2 and Nano Banana Pro need no pacing.

**"One shot" means one deck, not one generation round — and you do not stop to repair.**
Stated plainly because the ambiguity itself cost time in live use: a run hesitated over
whether it was allowed to fix a bad placement. It is not.

The master gate on the WRITTEN path is the single exception, and it resolves before any
placement exists. Once the four are firing, nothing stops.

## Prompt architecture

One invariant block, four scene lines. Only the scene changes.

```
Place the supplied artwork into a real photograph of the world as an out-of-home
advertisement.

THE ARTWORK IS REPRODUCED EXACTLY. Its composition, colours and type come through
unchanged. Do not recolour, recrop, redraw or re-letter it, do not add or remove a
word, do not add a logo. It reads clearly at a glance.

THE ARTWORK SITS ON THE SURFACE CORRECTLY. It takes the perspective of the surface
it is printed on, takes that scene's daylight and shadow, and picks up the surface
texture underneath. Printed material in a real place, never a flat rectangle pasted
onto a photo.

The photograph around it is real, candid and unstyled — ordinary weather, ordinary
light, ordinary passers-by. Full-frame camera, natural depth of field, no HDR, no
gloss, no lens flare, no CGI sheen.

THE WHOLE ARTWORK IS VISIBLE. Every edge of it sits inside the photograph — nothing
is cropped by the frame, cut off by a pole, hidden behind a tree or run off the top of
the wall. Every line of type in the artwork reads complete.

No extra text anywhere beyond the artwork itself and signage that genuinely belongs
to that street.

THE PLACEMENT — <scene>
```


## The house grade

Extracted by measuring the 36-frame colour-grading field on the canvas, not by eye.
This is the skill's **style**, and it goes in every placement prompt verbatim. It is
described in words, never wired as a reference — wiring a graded still drags its
composition in with it.

```
                measured            reads as
shadows         neutral, black pt 9  deep, never crushed
midtones        R-8.3 G+6.9 B+1.5    green-cyan cast
highlights      R-21.3 G+16.8 B+4.5  strongly green-cyan
white point     143 / 255            rolls off early — nothing reaches white
contrast        41 (std luma)        flat curve, no punch
saturation      48%                  rich but never vivid
```

The clause:

> THE HOUSE GRADE — the whole photograph is graded this way, and this matters as much
> as the composition.
>
> Shot on film and printed slightly flat. The tonal range is COMPRESSED: shadows deep
> and neutral but never crushed, and the highlights ROLL OFF EARLY — nothing reaches
> paper white, not the sky, not a lit sign. The brightest thing in frame sits well
> below white. Low contrast, gentle S-curve, no punch.
>
> A GREEN-CYAN CAST runs through the midtones and especially the highlights — skies,
> pale walls, concrete and daylight lean eucalyptus and sea-green rather than blue or
> warm. Reds and skin pulled back and desaturated. There is no orange-and-teal, no
> warm/cool split. The cool green IS the light.
>
> Colour moderately rich, never vivid. Fine film grain. Slight halation on the
> brightest edges. No HDR, no clarity, no glow, no saturation boost.

**A strongly-coloured LIGHT direction overrides the grade.** Measured: a placement
directed "blue hour, pavement wet" came back blue, not green-cyan, while the three
daylight and interior sites in the same batch held the grade exactly. Time-of-day words
carry their own colour and they win. Keep the set to overcast, flat grey, daylight and
interior artificial light; if a brief genuinely needs dusk, restate the green-cyan cast
inside that placement's LIGHT line rather than trusting the shared clause to hold.

**The trap this avoids.** Writing "ordinary weather, ordinary light, ordinary
passers-by" produces exactly that — flat, characterless placements. Light and camera
must be *directed* per placement (focal length, height, time of day, one human
moment), and the grade holds them together as a set.

## Direction, per placement

Every scene line carries three things beyond the location:

```
SHOT     focal length, camera height, angle       e.g. 85mm compressed from down the road
LIGHT    time of day and what it does to surfaces e.g. overcast, wet road holding reflection
MOMENT   one human beat                           e.g. one person stopped, looking up
```

Without these the model defaults to eye-level, midday, nobody — and every placement
looks the same.

**Keep the human beat OFF the artwork's plane.** The invariant block bans the artwork
being "hidden behind a tree", but the MOMENT direction actively asks for a person near
the ad, and the two pull against each other. On the live run the transit brief said
"walking past mid-frame" and the model put the commuter squarely across the panel,
blocking the left of the lower two lines. The plate was unaltered — an occlusion, not a
re-letter — but the placement no longer read.

So place the figure deliberately, in the direction itself: *in the near foreground and
cropped*, *at the far end of the shelter*, *stopped on the opposite kerb*. Say where the
person is relative to the ad, never just that they are in shot. The three placements that
did this came back clean; the one that said "mid-frame" did not.


## Square on, always

The single biggest driver of placement quality. Three-quarter and corner-wrap views
bend the artwork across two planes; the type distorts and stops reading. Tested
directly: a scaffold banner wrapping a building corner was the worst result of the
whole set, and the same creative shot perpendicular was the best.

Goes in every placement prompt:

> THE CAMERA IS SQUARE ON TO THE ARTWORK. The lens is perpendicular to the printed
> surface, so the ad sits in frame as a TRUE RECTANGLE, flat and undistorted, read
> straight. Only slight keystone is acceptable.
> - NO three-quarter view. NO oblique or angled view of the surface.
> - The artwork NEVER wraps a corner and NEVER bends across two planes.
> - It is on ONE flat plane facing the camera.
> - No fisheye, no wide-angle bowing, no perspective warp through the type.
>
> AND THE SURFACE ITSELF RUNS FLAT ACROSS THE FRAME. The wall, hoarding or panel the
> artwork sits on does not recede to a vanishing point, is not seen down its length,
> and its far end is not visible. Both the artwork AND the thing it is printed on face
> the camera.

**Why the second half exists.** A hoarding once obeyed "the artwork is on one flat plane"
while running the *hoarding* to a vanishing point — so the artwork bent along with it and
the type foreshortened. Banning oblique views of the artwork is not enough; the surface
has to be called out separately.

**Get variety from SITE and SCALE, not from camera angle.** A 6-sheet bus shelter, a
pavement-level hoarding and a billboard over traffic are genuinely different media
buys. The same wall from three angles is one placement photographed three times.

The four sites, fixed — chosen because they are genuinely different media buys:
`gable` (flat end wall) · `transit` (platform panel) · `shelter` (backlit 6-sheet) ·
`hoarding` (construction). Swap one only if the brief names a specific environment.

## Gotchas

```
API SHAPE
flora_generate        the ONLY way to run a generation. Returns a run_id; poll it with
                      flora_get_run. Wiring nodes with flora_add_to_canvas creates them
                      INERT — nothing on this server runs a wired generation node, so
                      never expect a canvas patch to fire anything.
params.image_url      the input image for an i2i model, as a SINGLE STRING. This is the
                      whole image-to-image mechanism.
                      params.image_urls (plural, array) is accepted without complaint,
                      silently IGNORED, and still billed — you get a text-to-image
                      render of the prompt with the creative nowhere in it. Measured.
flora_get_run         DO NOT poll a batch with this. It can report status "running" and
                      progress 0 for a run that has already finished — measured at 16
                      MINUTES of "running" on a run whose own record showed
                      started_at -> completed_at 120s apart, with outputs present the
                      whole time. A loop waiting for it to flip never exits.
run status            poll flora_list_generations filtered to the project instead: one
                      call covers the whole batch and reports terminal state. Key on
                      status == "completed" AND outputs being present — completed_at on
                      its own does not mean done, and neither does a "running" status
                      mean it is not.
flora_run_action      runs a prebuilt action headlessly on inputs supplied inline.
                      Credit-free and deterministic — where the resizes and the contact
                      sheet come from. It does NOT touch the canvas: outputs land under
                      media.flora.ai/code-sandbox/... and never appear as canvas nodes.
                      project_id only scopes authorization and generation history.
                      Entitled per workspace: a workspace without it returns
                      403 forbidden "Actions are not enabled for this workspace.
                      Upgrade your plan to use actions." That kills BOTH the resizes and
                      the contact sheet, so check it before promising either. The PDF
                      does not depend on actions and still builds.
flora_create_project  works in some workspaces and 400s in others on the SAME account,
                      tracking the workspace rather than the request. The message is the
                      literal string "Server Error" with a request id and no field — it
                      is NOT your payload, so reshaping it does nothing. Fall back to an
                      existing project. The workspace that refuses this is the same one
                      that refuses actions.
flora_list_canvas_nodes  returns media nodes with their asset urls. Use
                      flora_get_canvas for structure and how nodes connect.
ids                   project_id is REQUIRED on flora_generate, and it must belong to
                      the workspace you pass, or: 400 input_validation_error "Project
                      does not belong to the specified workspace."
credits               every placement bills. State the total and get a yes before the
                      first call. Nothing is refundable and retries bill again.
                      The charged_cost flora_generate returns AT FIRE TIME UNDERSTATES
                      the bill: measured 0.253 quoted against 0.873 actually charged,
                      3.45x. Quote from a completed run's charged_cost, or say plainly
                      that the figure is a floor. Four 4k placements are ~$3.50, not ~$1.
                The WRITTEN path adds a fifth generation at the same rate — quote ~$4.40,
                and quote it BEFORE the master, not before the placements.
media urls            fetchable with no credentials. Path contains the date — read the
                      full url, never reconstruct it.

MODEL PARAMS
GPT Image 2           resolution "2k" / "4k" lowercase. 4k costs no more time than 2k.
Nano Banana Pro       resolution "2K" / "4K" uppercase.
Krea                  creativity is an enum: raw | low | medium | high.
generate_audio        agent-gated; including it rejects the WHOLE changeset.
changeset validation  ONE bad param fails the ENTIRE changeset, not one node. Probe a
                      single node when unsure — the error returns valid_values.

RATE LIMITS
Krea                  rate-limits hard. Pace at ~5s or lose most of the batch to
                      GENERATION_DOWNSTREAM_SERVICE_ERROR.
GPT / NBP             no pacing needed. Fire concurrently.

RESULTS
media urls            fetchable with no credentials. Everything this skill produces is
                      a url, not a local file — there is no filesystem on this surface.
                      Report urls; never claim to have written or opened a file.
```

## The deck is an annotated PDF

**The deliverable is a paginated A4-landscape PDF**, built locally from HTML and printed
by headless Chrome. Not a server-side render — there is no PDF endpoint — and not a
contact sheet standing in for one.

"Annotated" is the whole point. A grid of placements is a contact sheet: it shows what
came back. The deck prints the SHOT / LIGHT / MOMENT you actually asked for beside each
placement, so a media planner reads the brief next to the result and can act on it. Print
what you **asked for**, not a description of what came back.

```bash
cd <project>/Deliverables
HTML=$(python3 build_mockup_deck.py deck.json --check)   # fetches, packs, measures
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless \
  --disable-gpu --no-sandbox --no-pdf-header-footer \
  --print-to-pdf="${HTML%.html}.pdf" \
  --virtual-time-budget=25000 "file://$PWD/$HTML"
```

**Take the html path from the builder's stdout, as above.** It names the file after the
work, so the deck and the PDF match without you retyping a title into a shell command.

The builder is in the appendix at the foot of this file, and its docstring carries the
`deck.json` shape. Put the placement urls straight into it — the builder downloads and
caches them into `src/` on first run, so there is no separate fetch step to get wrong. Write it out beside the deliverables and run it there. Land the HTML
next to the PDF — it re-renders in about two seconds, so a layout tweak never costs a
regeneration.

**Keep `--no-sandbox`.** Chrome will not launch as root or inside a container without it,
which is most of the surfaces this skill runs on, and the failure is a bare non-zero exit
that reads like the deck is impossible rather than like a missing flag.

### A dropped image is silent — make the builder say so

**This is the single most common way the deck comes out wrong.** Every section is
conditional on its images resolving, so a plate that will not load does not leave a hole:
the whole page is **dropped**, the remaining footers renumber over the gap, and the build
exits 0. Measured on a deliberately broken set — a missing local file and a 404 url —
the deck came out at **4 pages instead of 6, numbered 1..4**, with the cover plate gone
and nothing on stdout to say so. It looks like a finished, slightly short deck.

So the builder collects every unresolved image, names it, and **exits non-zero**:

```
3 image(s) did not resolve:
  creative: ALSO-MISSING.png
  TRANSIT: MISSING.png
  SHELTER: https://media.flora.ai/does-not-exist.png
  fix these or pass --partial to ship the deck without them
```

Fix them and re-run. `--partial` is the deliberate escape hatch for a genuinely
incomplete set — and if you use it, say in the final message which placements are missing
from the deck. Never report a page count you did not read back.

### Measure the page, don't look at it

`--check` loads the deck in the same headless Chrome that will print it, walks every
`.page`, and reports anything outside its content box — which side, how many pixels, which
element. Three seconds, and it exits non-zero.

```
page 1  SCROLL  +1236px
page 1  OVERFLOW  top +1236.3px  div.cover-txt
page 1  OVERFLOW  bottom +1105.7px  p.standfirst
```

That is an overlong standfirst running off the cover, named and quantified, without
rendering a PDF or looking at anything. The layout loop is where this skill's wall-clock
actually goes — render, squint at a thumbnail, guess which rule is wrong, render again —
and **almost none of those rounds are taste. They are geometry.** A screenshot is a
terrible way to read a number.

```
build with --check       free and instant; repeat until PASS
render the PDF           once nothing is overflowing
read the pages back      pdftoppm -png -r 60 out.pdf pg -- taste only, and only now
```

**A green check is not proof the page is good.** It proves nothing is outside its box. It
cannot see a distorted aspect ratio, a weak cover, or dead space. That is what the single
visual pass is for — do not skip it because the checker passed, and do not spend it on
geometry the checker already covers.

**If you change the CSS, verify the verifier.** Break the layout on purpose and confirm it
goes red before trusting a green check. This is genuinely easy to get wrong: removing
`max-height` from the placement image still reports PASS, because `align-items: center`
shrinks the flex item — the oversized image distorts instead of overflowing and the page
box stays clean. Confirm the failing build contains the bad rule AND that the reported
failure is the one you meant to cause.

**Say the full path to the PDF in the final message.** A deck nobody can find is not a
deliverable.

### Get the PDF out on every surface

**The PDF is the deliverable. Take the best route the surface allows — do not skip
straight to "can't".** Chrome is how route 1 prints; it is not what makes the deck
possible.

```
1  shell + Chrome     build, then print headless             -> a .pdf on disk
2  shell, no Chrome   build, user opens the html, Cmd-P      -> Save as PDF
3  no filesystem      run --remote, hand over the html       -> user prints it
```

Route 2 costs nothing: `@page { size: A4 landscape }` is honoured by the browser's own
print dialog, so **File → Print → Save as PDF** produces the same document the headless
flag would.

Route 3 is what makes this work on **claude.ai and ChatGPT**. With `--remote` the html
references the `media.flora.ai` urls instead of inlining the bytes, which drops it to
**8.5 KB** on a four-placement set — small enough to hand over as a file. Measured: those
urls load into a browser with no credentials and print exactly as inlined images do. So
the answer on a hosted surface is "here is the deck, open it and print" — one click from
a PDF, not unavailable.

Only say the deck cannot be built if all three fail. Never synthesise a PDF out of tool
output.

**The builder downscales before embedding, and that is not optional.** Chrome re-embeds
source images badly: measured on a four-placement set of full-resolution 4k PNGs,
**113 MB** of PDF against **3.6 MB** at 2400px JPEG q88 — 31x, with nothing lost, since
the widest slot in this layout resolves ~2185px at 300dpi. A deck nobody can attach to an
email is not a document you can send, so packing is on by default and caches into
`packed/` beside the source.

`--no-pack` exists for the case where a client genuinely wants the print-resolution file,
and it is almost never what you want — the full-resolution plates ship **alongside** the
deck as separate urls, which is what a media planner actually needs. `--remote` skips
packing entirely, since it references the urls rather than embedding anything.

### The contact sheet, as a fallback

Still worth building where actions are available: one composite image, credit-free and
deterministic, that a user can drop straight into a deck of their own.

```
flora_run_action  side-by-side-composite-browser
  inputs  the four placements, in site order: gable, transit, shelter, hoarding
  params  { layout: "grid-2x2", normalize: "match-shortest", gap: 24,
            background: "#ffffff" }
```

Use `layout: "auto"` when the count is not four. `normalize: "match-shortest"`
downscales to the smallest edge, which keeps every tile the same size without upscaling
anything.

**Labels, if the user wants them,** come from `add-text-to-image-browser` run over the
composite — not from burning text into a placement. Never annotate a placement itself;
the plate has to stay clean.

**This is a generalist skill.** It runs on any poster for any client, so nothing is
branded: no logo, no mark, no client name in the chrome. If a client name is wanted, it
is a text parameter on the label pass, never a template edit.

## Naming and what comes back

```
the master       one url, from flora_generate — WRITTEN path only
the placements   four urls, one per site, from flora_generate — ON the canvas
the resizes      three urls, from flora_run_action — NOT on the canvas
the contact      one url, from side-by-side-composite-browser — NOT on the canvas
the deck         a local .pdf path, built by the deck builder
the project      https://app.flora.ai/projects/<project_id>
```

Everything except the PDF is a url. Report the project link with the ids you resolved at
the top of the run — not one reconstructed at the end, and not the workspace id, which is
the substitution to watch for since both are long `_`-prefixed strings.

### Where the files land

On a surface with a filesystem, **always write to `<project>/Deliverables/`.** Create it
if it is missing. Never leave the deck in a scratch or temp directory, never drop it in
`~/Downloads`, and never leave it loose in the project root — across three live runs the
deck landed in three different places and had to be hunted for.

```
the source    <project>/Deliverables/<Poster-Title>-deck.html
the output    <project>/Deliverables/<Poster-Title>-deck.pdf
the plates    <project>/Deliverables/<Poster-Title>-deck-assets/    fetched + packed
```

The builder derives all three from `title`, so they are consistent by construction and two
runs coexist. **`Deliverables/` is shared by every run of this skill**, which is the whole
reason the prefix is not decoration: a bare `out.html` or `assets/` in there belongs to
nobody and the next deck silently overwrites it.

**The fetch cache is keyed on the full url, not the filename.** Every run of this skill
produces a gable, a transit, a shelter and a hoarding, so two decks in one folder collide
on basename alone. Measured, before the urls were hashed in: two decks whose gables
differed only by url both embedded the *first* run's plate, with no error and a clean
layout check. A wrong plate is worse than a missing one — a missing one at least changes
the page count.

**Check what is already in `Deliverables/` before writing.** The filenames come from the
title, so a re-run of the same poster lands on top of the previous one by construction. Say
so rather than silently overwriting it.

Write the **HTML source beside the PDF**. It re-renders through headless Chrome in
seconds, so a layout tweak never costs a regeneration — that is the difference between a
deck you can revise and one you have to rebuild. Ship the full-resolution plates alongside
it too: the deck's copies are packed for reading, the originals are for using.

Name the **work**, not the client — the poster's title, kebab-cased — and use it as the
label when you report each url, so a user collecting several runs can tell them apart.
`Many Hands` -> `Many-Hands-gable`, `Many-Hands-contact`. If the creative has no title,
synthesise one from what is actually in the picture. On the WRITTEN path, synthesise it
from the request *before* firing the master, so the master and everything descended from
it carry one name — `Many-Hands-master`, then `Many-Hands-gable`.

The urls are public, unsigned and permanent. Putting one in a transcript discloses that
asset to anyone who sees the transcript — worth a word to the user when the creative is
unreleased.

## Delivery — the deck structure

One page per thing. Never grid placements two-up; a placement is the deliverable and it
gets a page. **Every layout the skill produced appears in the deck** — if it was made,
it ships.

This is the page plan the builder implements. The footer carries the **title**, the
**date** and the page number, and nothing else.

**No project id and no canvas link anywhere in the rendered PDF.** The deck is a
client-facing document and both are internal plumbing: `prj_a1b2c3…` means nothing to a
media planner, and an `?focus=` link is dead to anyone outside the workspace — it reads as
a broken link in a document that is otherwise finished. Keep the ids in the run report,
which is where someone tracing the deck back to its canvas will actually look, and keep
the deck itself something you can hand to a client unedited.

```
1  COVER        title, one-paragraph standfirst, and a spec strip:
                CREATIVE / SOURCE (px + ratio) / PLACEMENTS / SOCIAL.
                SOURCE reads SUPPLIED or GENERATED, and on the WRITTEN path the
                standfirst carries the request verbatim, so the deck records what
                was actually asked for.
                The creative sits on this page — text one side, plate the other.
                The standfirst MUST state that the creative is reproduced and
                never regenerated; that sentence is the deck's only statement of
                the law, so it does not get cut. On the WRITTEN path that law
                starts at the master, not before it — say so in the same sentence
                rather than implying the poster was handed over finished.
2+ PLACEMENTS   ONE PAGE EACH. Image left at ~70% width. Right column carries:
                  <site name> as a heading
                  SHOT    focal length, camera height, angle
                  LIGHT   time of day and what it does to the surfaces
                  MOMENT  the human beat
                then one sentence of plain observation about the site.
n  SOCIAL       REQUIRED, never omitted. The master and all three resizes at
                MATCHED WIDTH, bottom-aligned on a shared baseline, heights left
                free to climb. Each under a TWO-PART CAPTION — the USE on the
                left, the RATIO right-aligned against it:
                  MASTER          16:9
                  FEED            1:1
                  FEED PORTRAIT   4:5
                  STORY · REEL    9:16
                The resizes are part of the deliverable — a deck without them is
                half the job.
```

**No standalone blow-up of the creative.** An earlier version of this structure spent
page 2 re-showing the artwork large and alone, directly after the cover had already shown
it. That is padding: the reader has just looked at it, and a second look at the same
image teaches them nothing they did not have a page ago.

The cover carries the plate AND the standfirst that states the law, which is everything
the blow-up page was there for. Six pages that each do a job beat seven where one is a
repeat — a deck earns its length by what changes page to page.

Cut it from the total too, not just the sequence: renumber so the footers run 1..6 with
no gap where the old page used to be.

**Caption the use, not just the ratio.** `9:16` is a number; `STORY · REEL` is where the
file goes. A media planner reads the deck to find out what they have been given, and a
column of bare ratios makes them do the translation themselves. So the use is the
caption's headline — set in the deck's label weight, left-aligned under the image — and
the ratio sits quietly right-aligned on the same line as the supporting fact.

Getting this wrong is subtle rather than dramatic: leading with the ratio and dropping
the use to small print underneath *looks* complete and still reads as a contact sheet.
The use-name is the part that makes the page a delivery.

**Match the width, not the height.** "Shared baseline" means a common BOTTOM EDGE with
every crop set to the same width — so the heights climb left to right and the page shows
you, at a glance, that 9:16 is tall and 16:9 is a letterbox. The shapes are the content
of this page.

Height-matching instead is the trap, and it is an easy misreading of "baseline". It
makes 1:1, 4:5 and 9:16 come out at nearly the same width, the ratios stop being legible
AS ratios, and the one thing the page exists to demonstrate quietly disappears — while
still looking like a finished layout.

Size it off the tallest crop, which is 9:16. With a matched width W the stack is
`W x 16/9` tall, so W is bounded by the vertical space left under the header, and the row
is bounded by `4W + 3 gaps` across. Solve the vertical first — running the 9:16 off the
bottom of the page is the failure mode here, not running out of width.

Print the SHOT / LIGHT / MOMENT you actually asked for, not a description of the result.
It is the brief, and it makes the deck a document someone can act on rather than a
contact sheet.

**No audit block, no pass/fail marks, no measurement table.** If something is visibly
wrong with a placement, say so in the one-line observation in plain language. Otherwise
let the work speak.

## Reporting back

The full path to the PDF, the project link, and the urls. Name which placement is
strongest and why, and name any that failed and what specifically drifted — in plain
sentences, not a table. There is no audit block and no pass/fail column anywhere in this
skill's output.

Say what the project link contains, since it is not everything you are handing over: the
placements are on that canvas, the resizes and the contact sheet are not.

On the WRITTEN path, report the master's url as well and label it the master. It is a
deliverable — the user now owns a poster they did not have — not scaffolding for the
deck. Say in one line what you decided on their behalf: the shape you chose, and whether
you wrote a headline, so the next run can change either.

## Appendix — build_mockup_deck.py

Write this out beside the deliverables and run it there; it resolves image paths relative
to `deck.json`, whose shape is in the docstring. **Nothing to install** — stdlib, plus
`PIL` if it happens to be there and `sips` if it is not.

It does the whole tail of the build in one call: fetch the urls, pack the plates, lay out
the pages, measure them, and fail loudly on anything that did not resolve.

```
python3 build_mockup_deck.py deck.json --check   the normal run
  --check       measure every page in headless Chrome; non-zero on overflow
  --partial     build anyway when an image will not resolve
  --remote      reference the urls instead of embedding; ~8 KB html, no packing
  --pack=N      cap embedded plates at N px wide, JPEG q88. Default 2400.
  --no-pack     embed at full resolution. Measured 113 MB against 3.6 MB packed.
```

**It targets python 3.9**, which is what macOS ships, hence the
`from __future__ import annotations` at the top. Do not remove it and do not reach for
3.10-only syntax: this has to run on a stock machine with nothing set up. `PIL` is used
for the downscale when it is there; where it is missing the builder falls back to `sips`,
and where neither exists it says so and embeds full size rather than failing.

Verified on a four-placement, four-resize set in inline, url-only and `--remote` mode:
**6 pages** each — cover, four placements, social. Measured on that set: a url-only
`deck.json` goes from urls to a checked 3.6 MB PDF in 2.5s. The pages were read back as
images to confirm the social page comes out at matched width on a shared bottom edge with
the heights climbing, which is the one thing that page exists to demonstrate.

```python
#!/usr/bin/env python3
"""Pack a mockup-deck run into an A4-landscape annotated PDF.

Usage:  python3 build_mockup_deck.py deck.json --check  ->  <Title>-deck.html beside it

    --check      measure every page in headless Chrome; non-zero on overflow
    --partial    build even though an image did not resolve (say which, if you use it)
    --remote     reference the media urls instead of inlining; ~8 KB html, no packing
    --pack=N     cap embedded plates at N px wide as JPEG q88. Default 2400.
    --no-pack    embed at full resolution. Measured 113 MB against 3.6 MB packed.

Artifacts are named after the work, since Deliverables/ is shared by every run:
    <Title>-deck.html      the source, re-renders in ~2s
    <Title>-deck.pdf       what you hand over
    <Title>-deck-assets/   fetched originals under src/, downscaled under packed/

Then render, taking the html path from this script's stdout:
    HTML=$(python3 build_mockup_deck.py deck.json --check)
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless \
      --disable-gpu --no-sandbox --no-pdf-header-footer \
      --print-to-pdf="${HTML%.html}.pdf" --virtual-time-budget=25000 "file://$PWD/$HTML"

deck.json:
{
  "title":       "Your Agents Joined",
  "standfirst":  "One paragraph. MUST say the creative is reproduced, never regenerated.",
  "date":        "2026-08-30",
  "creative":    {"file": "master.png", "px": "2048 x 1152", "ratio": "16:9",
                  "source": "SUPPLIED"},
  "placements":  [{"site": "GABLE END", "file": "gable.png",
                   "shot":  "85mm, compressed from down the road",
                   "light": "overcast, wet road holding reflection",
                   "moment":"one person stopped on the opposite kerb",
                   "note":  "One sentence of plain observation."}],
  "social":      [{"use": "MASTER", "ratio": "16:9", "file": "master.png"},
                  {"use": "FEED",   "ratio": "1:1",  "file": "feed.png"}]
}

Every image entry takes "file" (a local path), "url" (a media.flora.ai link), or both.
A url with no local file is downloaded once into src/ and cached, so a deck.json of urls
builds on its own with no curl step. Media urls are public and unsigned, so they load for
anyone.

A section whose images do not resolve is DROPPED, and the footers renumber over the gap --
so a short deck looks like a complete one. That is why an unresolved image is named on
stderr and exits non-zero rather than quietly shrinking the deck. Pass --partial when the
set is genuinely incomplete and you mean to ship it anyway.
"""

from __future__ import annotations  # macOS ships python 3.9; keeps `str | None` legal

import base64
import hashlib
import html
import json
import mimetypes
import pathlib
import re
import subprocess
import sys
import urllib.request

# A4 landscape, in mm.
PAGE_W, PAGE_H = 297.0, 210.0
MARGIN = 14.0
FOOTER_H = 12.0
USABLE_W = PAGE_W - 2 * MARGIN
USABLE_H = PAGE_H - 2 * MARGIN - FOOTER_H


REMOTE = "--remote" in sys.argv  # reference media urls instead of inlining the bytes
PARTIAL = "--partial" in sys.argv  # build anyway when an image will not resolve
CHECK = "--check" in sys.argv  # measure every page in headless Chrome after building
PACK = 0 if "--no-pack" in sys.argv else next(
    (int(a.split("=")[1]) for a in sys.argv if a.startswith("--pack=")), 2400
)

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

MISSES: list = []  # images that did not resolve; the run fails on these, see main()
ASSETS: list = []  # one-element holder for this run's <Title>-deck-assets/ directory


def embed(path: pathlib.Path) -> str | None:
    """Inline an image as a data URI so the PDF has no external dependencies."""
    if not path.exists():
        return None
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode()


def fetch(url: str, dest: pathlib.Path) -> pathlib.Path | None:
    """Cache a media url on disk. Media urls are public, so no credentials are needed.

    Downloading is the builder's job rather than the caller's: a deck.json carrying urls
    should build on its own, and a hand-run curl per placement is a step to get wrong.
    An already-populated file is left alone, so a re-run costs nothing.
    """
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            data = r.read()
    except Exception as exc:
        print(f"  fetch failed {dest.name}: {exc}", file=sys.stderr)
        return None
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return dest


def slug(title: str) -> str:
    """'Many Hands' -> 'Many-Hands'. Names every artifact after the WORK."""
    keep = "".join(c if (c.isalnum() or c in " -_") else "" for c in str(title or ""))
    return "-".join(keep.split()) or "Untitled"


def cache_name(url: str, hint: str) -> str:
    """A cache filename that is unique to the URL, not just to its basename.

    Every run of this skill produces a gable, a transit, a shelter and a hoarding, so
    two decks built in the same folder collide on basename alone -- and the second run
    silently embeds the FIRST run's plate. Measured: two decks whose gables differed
    only by url both came out carrying the same image, with no error and a clean layout
    check. A wrong plate is worse than a missing one; a missing one changes the page
    count. Hashing the url is what makes the cache safe to share.
    """
    stem, dot, ext = pathlib.Path(hint).name.rpartition(".")
    digest = hashlib.sha1(url.encode()).hexdigest()[:8]
    return f"{stem or 'img'}-{digest}{dot}{ext or 'png'}"


def pack(path: pathlib.Path, cap: int) -> pathlib.Path:
    """Downscale one plate to `cap` px wide as JPEG q88, cached beside it in packed/.

    Chrome re-embeds source images badly: measured on a four-placement set, 113 MB of
    PDF from full-resolution 4k PNGs against 3.6 MB at 2400px -- 31x, with nothing lost,
    since the widest slot in this layout resolves ~2185px at 300dpi. A deck nobody can
    attach to an email is not a document you can send, so this is on by default.
    """
    if not path.exists():
        return path
    dest = ASSETS[0] / "packed" / (path.stem + ".jpg")
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        from PIL import Image  # optional: the only non-stdlib thing here, and it has a fallback

        im = Image.open(path).convert("RGB")
        if im.width > cap:
            im = im.resize((cap, round(im.height * cap / im.width)), Image.LANCZOS)
        im.save(dest, "JPEG", quality=88, optimize=True)
        return dest
    except ImportError:
        pass
    try:  # macOS ships sips, so a stock machine with no PIL still packs
        subprocess.run(
            ["sips", "-s", "format", "jpeg", "-s", "formatOptions", "88",
             "-Z", str(cap), str(path), "--out", str(dest)],
            capture_output=True, check=True, timeout=120,
        )
        return dest if dest.exists() else path
    except (OSError, subprocess.SubprocessError):
        print(f"  pack unavailable for {path.name} -- embedding full size", file=sys.stderr)
        return path


def src(item: dict, root: pathlib.Path) -> str | None:
    """Resolve one image to something an <img> can load.

    Inlined local bytes win: the deck is then self-contained and survives being moved.
    A url with no local file is fetched once into src/ and inlined from there. Pass
    --remote to skip all of that and reference the urls directly, which keeps the html
    a few KB -- small enough to hand over as a file on a surface with no filesystem.
    """
    url = item.get("url")
    if REMOTE:
        if not url:
            MISSES.append(f'{item.get("site") or item.get("use") or "creative"}: --remote needs a url')
        return url or None
    local = root / item["file"] if item.get("file") else None
    if local is None or not local.exists():
        if url:
            hint = item.get("file") or url.rsplit("/", 1)[-1].split("?")[0]
            local = fetch(url, ASSETS[0] / "src" / cache_name(url, hint))
    if local is None or not local.exists():
        MISSES.append(
            f'{item.get("site") or item.get("use") or "creative"}: '
            f'{item.get("file") or url or "no file and no url"}'
        )
        return None
    got = embed(pack(local, PACK) if PACK else local)
    if not got:
        MISSES.append(f'{item.get("site") or item.get("use") or "creative"}: unreadable')
    return got


def esc(s: object) -> str:
    return html.escape(str(s or ""))


def ratio_to_hw(ratio: str) -> float:
    """'9:16' -> 16/9, the height-per-unit-width multiplier."""
    try:
        w, h = (float(n) for n in ratio.replace("x", ":").split(":"))
        return h / w if w else 1.0
    except (ValueError, ZeroDivisionError):
        return 1.0


def footer(deck: dict, n: int) -> str:
    """TITLE and DATE are the only parameters in the chrome.

    No project id and no canvas link. The deck is a client-facing document, and both
    of those are internal plumbing: an id means nothing to a media planner, and a
    canvas link is dead to anyone outside the workspace. Trace the deck back through
    the run report, which is where the ids belong.
    """
    return (
        f'<div class="ftr"><span>{esc(deck.get("title", ""))}</span>'
        f'<span>{esc(deck.get("date", ""))}</span><span>{n}</span></div>'
    )


def cover(deck: dict, root: pathlib.Path, n: int) -> str:
    cre = deck.get("creative") or {}
    plate_src = src(cre, root)
    spec = [
        ("CREATIVE", deck.get("title", "")),
        ("SOURCE", " · ".join(x for x in (cre.get("source"), cre.get("px"), cre.get("ratio")) if x)),
        ("PLACEMENTS", str(len(deck.get("placements") or []))),
        ("SOCIAL", " · ".join((s.get("ratio", "") for s in deck.get("social") or [])) or "—"),
    ]
    rows = "".join(
        f'<div class="spec-row"><span class="k">{esc(k)}</span>'
        f'<span class="v">{esc(v)}</span></div>'
        for k, v in spec
        if v
    )
    plate = f'<div class="cover-plate"><img src="{plate_src}"></div>' if plate_src else ""
    return f"""<section class="page cover">
  <div class="cover-txt">
    <h1>{esc(deck.get("title", "Untitled"))}</h1>
    <p class="standfirst">{esc(deck.get("standfirst", ""))}</p>
    <div class="spec">{rows}</div>
  </div>
  {plate}
  {footer(deck, n)}
</section>"""


def placement(deck: dict, p: dict, root: pathlib.Path, n: int) -> str:
    img = src(p, root)
    if not img:
        return ""
    brief = "".join(
        f'<div class="brief-row"><span class="k">{k}</span>'
        f'<span class="v">{esc(p.get(k.lower()))}</span></div>'
        for k in ("SHOT", "LIGHT", "MOMENT")
        if p.get(k.lower())
    )
    note = f'<p class="note">{esc(p["note"])}</p>' if p.get("note") else ""
    return f"""<section class="page place">
  <div class="place-img"><img src="{img}"></div>
  <div class="place-col">
    <h2>{esc(p.get("site", ""))}</h2>
    <div class="brief">{brief}</div>
    {note}
  </div>
  {footer(deck, n)}
</section>"""


def social(deck: dict, root: pathlib.Path, n: int) -> str:
    """Matched WIDTH, bottom-aligned on a shared baseline. Heights climb.

    Size off the tallest crop. With matched width W the stack is W * (h/w) tall, so W
    is bounded twice: by the row across, and by the vertical space under the header.
    Solve the vertical first -- running the 9:16 off the bottom is the failure mode
    here, not running out of width.
    """
    items = [s for s in (deck.get("social") or []) if src(s, root)]
    if not items:
        return ""
    gap, head = 8.0, 26.0
    tallest = max(ratio_to_hw(s.get("ratio", "1:1")) for s in items)
    w_across = (USABLE_W - gap * (len(items) - 1)) / len(items)
    w_down = (USABLE_H - head) / tallest
    w = min(w_across, w_down)
    cells = "".join(
        f'<div class="cell" style="width:{w:.2f}mm">'
        f'<img style="width:{w:.2f}mm" src="{src(s, root)}">'
        f'<div class="cap"><span class="use">{esc(s.get("use"))}</span>'
        f'<span class="ratio">{esc(s.get("ratio"))}</span></div></div>'
        for s in items
    )
    return f"""<section class="page social">
  <h2>SOCIAL</h2>
  <div class="row" style="gap:{gap}mm">{cells}</div>
  {footer(deck, n)}
</section>"""


CSS = f"""
@page {{ size: A4 landscape; margin: 0; }}
* {{ box-sizing: border-box; }}
body {{ margin: 0; font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
        color: #17150f; background: #fff; -webkit-print-color-adjust: exact; }}
.page {{ position: relative; width: {PAGE_W}mm; height: {PAGE_H}mm;
         padding: {MARGIN}mm {MARGIN}mm {MARGIN + FOOTER_H}mm; overflow: hidden;
         page-break-after: always; }}
.page:last-child {{ page-break-after: auto; }}
img {{ display: block; max-width: 100%; max-height: 100%; object-fit: contain; }}

.ftr {{ position: absolute; left: {MARGIN}mm; right: {MARGIN}mm; bottom: 7mm;
        display: flex; justify-content: space-between; font-size: 7.5pt;
        letter-spacing: .08em; color: #8a8478; border-top: .3mm solid #ddd8cd;
        padding-top: 2mm; }}

.cover {{ display: flex; gap: 12mm; align-items: center; }}
.cover-txt {{ width: 40%; }}
.cover-plate {{ width: 60%; height: 100%; display: flex; align-items: center; }}
h1 {{ font-size: 30pt; line-height: 1.05; margin: 0 0 6mm; letter-spacing: -.02em; }}
.standfirst {{ font-size: 10pt; line-height: 1.6; margin: 0 0 8mm; color: #3d382f; }}
.spec-row, .brief-row {{ display: flex; gap: 4mm; font-size: 8pt; padding: 1.6mm 0;
                         border-top: .3mm solid #e6e1d6; }}
.spec-row .k, .brief-row .k {{ width: 24mm; flex: none; letter-spacing: .09em;
                               color: #8a8478; }}
.spec-row .v, .brief-row .v {{ color: #17150f; }}

.place {{ display: flex; gap: 9mm; align-items: center; }}
.place-img {{ width: 70%; height: 100%; display: flex; align-items: center; }}
.place-col {{ width: 30%; }}
h2 {{ font-size: 13pt; margin: 0 0 5mm; letter-spacing: .04em; }}
.note {{ font-size: 8.5pt; line-height: 1.55; color: #4a443c; margin: 6mm 0 0; }}

.social .row {{ display: flex; align-items: flex-end; justify-content: flex-start; }}
.social .cell {{ display: flex; flex-direction: column; justify-content: flex-end; }}
.cap {{ display: flex; justify-content: space-between; align-items: baseline;
        margin-top: 2.5mm; border-top: .3mm solid #e6e1d6; padding-top: 1.8mm; }}
.use {{ font-size: 8pt; letter-spacing: .09em; }}
.ratio {{ font-size: 7.5pt; color: #8a8478; }}
"""


def build(deck_path: pathlib.Path) -> pathlib.Path:
    deck = json.loads(deck_path.read_text())
    root = deck_path.parent
    # Deliverables/ is shared by every run of this skill, so name each artifact after the
    # work: Many-Hands-deck.html beside Many-Hands-deck-assets/. A bare out.html belongs
    # to nobody, and the next run overwrites it without a word.
    name = slug(deck.get("title"))
    ASSETS[:] = [root / f"{name}-deck-assets"]
    pages, n = [], 1
    pages.append(cover(deck, root, n))
    for p in deck.get("placements") or []:
        page = placement(deck, p, root, n + 1)
        if page:
            n += 1
            pages.append(page)
    page = social(deck, root, n + 1)
    if page:
        n += 1
        pages.append(page)
    out = root / f"{name}-deck.html"
    out.write_text(
        f"<!doctype html><meta charset=utf-8><title>{esc(deck.get('title'))}</title>"
        f"<style>{CSS}</style>{''.join(pages)}"
    )
    return out


PROBE = """
<script>
document.addEventListener('DOMContentLoaded', function () {
  var out = [], pages = document.querySelectorAll('.page');
  pages.forEach(function (pg, i) {
    var cs = getComputedStyle(pg), r = pg.getBoundingClientRect();
    var box = {l: r.left + parseFloat(cs.paddingLeft), t: r.top + parseFloat(cs.paddingTop),
               rt: r.right - parseFloat(cs.paddingRight), b: r.bottom - parseFloat(cs.paddingBottom)};
    if (pg.scrollHeight - pg.clientHeight > 1)
      out.push('page ' + (i + 1) + '  SCROLL  +' + (pg.scrollHeight - pg.clientHeight).toFixed(0) + 'px');
    pg.querySelectorAll('*').forEach(function (el) {
      if (el.closest('.ftr')) return;
      var b = el.getBoundingClientRect();
      if (!b.width && !b.height) return;
      var tag = el.tagName.toLowerCase() + (el.className ? '.' + String(el.className).split(' ')[0] : '');
      [['left', box.l - b.left], ['top', box.t - b.top],
       ['right', b.right - box.rt], ['bottom', b.bottom - box.b]].forEach(function (q) {
        if (q[1] > 1) out.push('page ' + (i + 1) + '  OVERFLOW  ' + q[0] + ' +' + q[1].toFixed(1) + 'px  ' + tag);
      });
    });
  });
  var pre = document.createElement('pre');
  pre.id = 'layoutcheck';
  pre.textContent = out.length ? out.join('\\n') : 'PASS ' + pages.length + ' pages';
  document.body.appendChild(pre);
});
</script>
"""


def check(out: pathlib.Path) -> bool:
    """Walk every page in headless Chrome and report anything outside its content box.

    Three seconds, and it reads a number instead of a screenshot. The layout loop is
    where this skill's wall-clock actually goes -- render, squint at a thumbnail, guess
    which rule is wrong, render again -- and almost none of those rounds are taste.
    They are geometry: content taller than its page, a row wider than its column, a
    plate sliding under the footer. Run this until it passes, THEN look once.
    """
    probed = out.resolve().parent / "_probe.html"
    probed.write_text(out.read_text() + PROBE)
    try:
        dom = subprocess.run(
            [CHROME, "--headless", "--disable-gpu", "--no-sandbox",
             "--virtual-time-budget=20000", "--dump-dom", probed.as_uri()],
            capture_output=True, text=True, timeout=300,
        ).stdout
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"layout check skipped: {exc}", file=sys.stderr)
        return True
    finally:
        probed.unlink(missing_ok=True)
    m = re.search(r'<pre id="layoutcheck">(.*?)</pre>', dom, re.S)
    if not m:
        print("layout check: no probe output -- the page did not load", file=sys.stderr)
        return False
    report = html.unescape(m.group(1).strip())
    print(report, file=sys.stderr)
    return report.startswith("PASS")


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    out = build(pathlib.Path(args[0] if args else "deck.json"))
    ok = True
    if MISSES:
        # A page whose image will not resolve is DROPPED and the footers renumber over
        # the gap, so a short deck looks like a complete one. Never let that pass quietly.
        print(f"\n{len(MISSES)} image(s) did not resolve:", file=sys.stderr)
        for m in MISSES:
            print(f"  {m}", file=sys.stderr)
        if PARTIAL:
            print("  --partial: building the deck without them", file=sys.stderr)
        else:
            print("  fix these or pass --partial to ship the deck without them", file=sys.stderr)
            ok = False
    if CHECK and not check(out):
        ok = False
    print(out)
    print(f"  render to: {out.with_suffix('.pdf').name}", file=sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
```
