---
name: flora-mockup-deck
description: >
  Turn one finished ad creative into a campaign deck. Give it a poster, billboard
  ad, campaign key visual or any finished artwork on a FLORA canvas, and it returns
  four square-on out-of-home placements (gable end, transit platform, bus shelter,
  construction hoarding), three social resizes (1:1, 4:5, 9:16), and one contact
  sheet laying all of it out. Use when someone asks to mock up an ad, see a poster in
  the wild, in situ or out of home, wants social sizes of an ad, or asks for a
  placement deck. The artwork is reproduced exactly and never regenerated. One shot,
  four billable generations, one contact sheet.
---

# flora-mockup-deck

## What it is

Not an image generator. **A placement engine.** The creative already exists and is
finished — the only job is putting it into the world convincingly, four ways, without
altering it.

The thing that makes a mockup fail is never the photograph. It is the artwork drifting:
recoloured, recropped, re-lettered, a word dropped. So the whole skill is built around
one invariant.

## One shot, minimal outputs

The skill runs **once** and emits exactly the deliverable. No draft round, no preview
pass, no variant sprawl.

```
4  generations   the placements — one per site, not four angles on one site
3  resizes       1:1, 4:5, 9:16 — NOT generations, see below
1  contact sheet the four placements in one grid
```

**Four generations, three deterministic resizes, one contact sheet.** Nothing is repaired,
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
CREATIVE    finished artwork              required — an HTTPS url or an attached file
PLACES      4 named placements            optional, default: the four archetypes
BRIEF       one line on where/what mood   optional
```

**Getting the creative in.** Files attached in ChatGPT are already hosted on
`files.openai.com` or `cdn.openai.com`, both allowlisted — pass that url straight to
`flora_create_asset` as `source` and FLORA fetches it server-side. A FLORA output at
`media.flora.ai` works the same way. Never base64-encode the file and never try to
upload bytes; if the artwork genuinely has no url, say so and ask the user to add it
to their FLORA project.

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

## Match the site to the creative's shape

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
run status            a run can report completed_at while status is STILL "running"
                      with no outputs. Key on status == "completed" AND outputs being
                      present; completed_at on its own does not mean done.
flora_run_action      runs a prebuilt action headlessly on inputs supplied inline.
                      Actions are credit-free and deterministic — this is where the
                      resizes and the contact sheet come from, not local scripts.
flora_list_canvas_nodes  returns media nodes with their asset urls. Use
                      flora_get_canvas for structure and how nodes connect.
credits               every placement bills. State the total and get a yes before the
                      first call. Nothing is refundable and retries bill again.
                      The charged_cost flora_generate returns AT FIRE TIME UNDERSTATES
                      the bill: measured 0.253 quoted against 0.873 actually charged,
                      3.45x. Quote from a completed run's charged_cost, or say plainly
                      that the figure is a floor. Four 4k placements are ~$3.50, not ~$1.
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

## The deck is a contact sheet, not a PDF

There is no server-side PDF. The deliverable is a single composite image built with
`side-by-side-composite-browser` — credit-free, deterministic, and returned as a url the
user can open or drop into a deck themselves.

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

**When a real paginated PDF is required,** say plainly that this surface returns images
and the user can assemble them. Do not attempt to synthesise a PDF from tool output.

## Naming and what comes back

Nothing is written to disk. Every deliverable is a url returned by a run:

```
the placements   four urls, one per site, from flora_generate
the resizes      three urls, from flora_run_action
the contact      one url, from side-by-side-composite-browser
```

Name the **work**, not the client — the poster's title, kebab-cased — and use it as the
label when you report each url, so a user collecting several runs can tell them apart.
`Many Hands` -> `Many-Hands-gable`, `Many-Hands-contact`. If the creative has no title,
synthesise one from what is actually in the picture.

The urls are public, unsigned and permanent. Putting one in a transcript discloses that
asset to anyone who sees the transcript — worth a word to the user when the creative is
unreleased.

## Delivery — the deck structure

One page per thing. Never grid placements two-up; a placement is the deliverable and it
gets a page. **Every layout the skill produced appears in the deck** — if it was made,
it ships.

```
1  COVER        title, one-paragraph standfirst, and a spec strip:
                CREATIVE / SOURCE (px + ratio) / PLACEMENTS / SOCIAL.
                The creative sits on this page — text one side, plate the other.
                The standfirst MUST state that the creative is reproduced and
                never regenerated; that sentence is the deck's only statement of
                the law, so it does not get cut.
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

Four placements, contact-sheeted together, plus the measurement table. Name which one
is strongest and why, and name any that failed and what specifically drifted.
