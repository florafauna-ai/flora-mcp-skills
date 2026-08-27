---
name: flora-pdp-deck
description: >
  Turn a product into a shoppable PDP asset set and an annotated PDF. Drop a
  product photo into the chat -- and a model frame if you have one -- and it
  returns clean studio plates, on-model views, and an A4 deck. Works from a
  single image. The product is reference-locked and never re-described. Use when
  someone asks for PDP assets, product detail page imagery, an on-model set, a
  product gallery, shots of this product on a model, or a product recreated
  de-branded and shot on a person. Do not use for placing finished artwork in
  the world -- that is flora-mockup-deck -- or for a one-off image with no set
  around it.
---

# flora-pdp-deck

Self-contained. The deck builder is at the foot of this file; write it out and run it.

## What it is

Not an image generator. **A consistency engine.** The product exists; the job is
putting it in front of a camera many times without it drifting between frames.

> **The product is reference-locked. The world and the pose are generated.**
> A seam moving, a strap ending somewhere new, a colour drifting — that is a fail.

## What you can get from what you have

Start here. What the user hands you decides what you can honestly promise, and the
limits are not obvious.

```
one product photo        1 clean plate + N on-model or context frames + a deck
  + a model frame        the same, with a real person holding or wearing it
several real photographs one plate per photograph, plus the above
```

**A single reference cannot be rotated by asking.** The `SHOT:` line changes framing;
it does not turn the product. Measured — four plates from one photo, byte-identical
prompt block, only the shot line varying:

```
mean absolute grey difference, 0 = identical
  three-quarter  vs  rear 180 deg      3.21    <- opposite faces requested
  front          vs  three-quarter     6.39
  each plate     vs  the reference     8.06 - 8.74
```

The plates differed from **each other less than each differed from its own source**.
Four requested angles, four near-duplicates. On an asymmetric product it shows
directly: a wax drip specified on one side stayed on that side in the frame asked to
show the opposite face.

So from one photo: **generate one plate, not four.** Then spend the budget on
on-model and context frames, where the composition genuinely changes and the model
has real work to do. Say this to the user before firing. Four billed duplicates is
the expensive way to learn it.

## Intake — the image is in the chat, not in FLORA

The user drops a photo into the conversation. **It is not in FLORA.** Nothing
generates until you put it there, and this is the step that stalls a run.

### Find the URL first

Almost every chat attachment already has one, and a URL is the only intake that works
everywhere:

```
Claude, web and API      uploads.anthropic.com
ChatGPT and OpenAI API   files.openai.com, cdn.openai.com
a FLORA output           media.flora.ai
an MCP image block       the url field on the block
```

Then FLORA fetches it server-side — no bytes through the transport:

```
flora_create_asset  { source: "<https url>", workspace_id, project_id }
```

Pass `project_id` and it lands on the canvas. Without it, follow with
`flora_attach_asset`; an unattached asset is invisible to the run.

### When there is no URL

With a shell: `flora_create_asset { source: "signed-url", content_type, file_name }`,
POST the file to the returned `upload` object, then `flora_complete_asset`.

Without a shell — Claude.ai web and ChatGPT both — **you cannot upload.** Say so and
ask for a link, or for the user to drop the image on a canvas and give you the project
id. Do not stall silently pretending to work. And never base64 an image through
`execute`: the sandbox cannot reach upload hosts and the encoding burns tokens for a
call that fails anyway.

### Prove it landed

`flora_list_canvas_nodes` must show the node with a url. That url is what goes into
`params.image_url`. **Read the full url from the response, never reconstruct it** — the
path carries a date and an opaque segment. Media urls need no credentials, so pull the
image down and look at it before spending on it.

## Two references through a one-image API

Hosted `flora_generate` takes **one** `image_url`. `params.image_urls` plural is
accepted, silently ignored, and still billed.

To get a product *and* a model into one frame, stitch them into a single sheet first
with a credit-free action, and pass the sheet:

```
flora_run_action  side-by-side-composite-browser
                  { layout: "horizontal-2", normalize: "match-largest" }
                  -> one image, 9 seconds, 0 credits
```

Measured, it works. A product plate left, a street portrait right, returned one unified
studio photograph: her face, hair and clothing carried over, the candle and its holder
carried over, the street and the tote bag she was wearing both gone, the ground
overridden to the plates' seamless. No diptych, no gutter.

**The reference contract does the work.** Say which panel is truth for what, and say
what *not* to take — not the split layout, not the gutter, not the right panel's street
or crop or pose. Then name each of those again in `FAIL IF`. Without that the sheet's
own layout leaks into the output.

**What a composite costs is fine detail.** The one asymmetric feature — a wax drip —
survived all four plain-reference plates and vanished in the composite frame. Halving a
reference's linear resolution does that. Composite for identity, wardrobe, shape and
colour; do not trust it to hold a seam, a stitch or a drip. Put the fine detail in
`FAIL IF` and check it by eye.

## Law 1 — reference, do not describe

A set generated from a written spec alone looks *plausible* and is *inconsistent*. Each
frame invents the unstated details independently. A strap specified as existing but not
where it *terminated* ended two-thirds down the panel in one frame and ran over the
bottom seam in another. Both obeyed the prompt.

So the prompt says "the truth of the product is attached" rather than enumerating it.

On the browser surface, wire the approved plates into every downstream frame and
**verify the edges bound** — `flora_apply_changeset` can return `ok: true` and still
leave zero inbound edges. Read `connects[]` for `bound: true`, then re-read two or three
targets and check `edges.in.length`. Wire by UUID; short `nX` ids are reassigned as the
canvas mutates.

On hosted there are no edges — the reference is `params.image_url`, or a composite.

## Law 2 — name the failure, not the ideal

Describing what you want does not prevent the specific thing that goes wrong.
Forbidding it does.

| written as the ideal | drifted | rewritten as the failure | held |
|---|---|---|---|
| "worn high and snug" | bag floated off the back | "NO daylight, NO gap, NO wedge of background between the back panel and his body" | yes |
| "same bag throughout" | orange tabs appeared mid-clip | "no orange patch, tab, tag, label or stitching appears anywhere else on the bag" | yes |
| "dead level, no tilt" | camera looked down on all four plates | "FAIL IF the elliptical opening of the dish is visible; the rim reads as a straight line" | — |

Every prompt ends in a `FAIL IF:` list naming the specific drift in the model's own
terms. Not a style note — a spec.

Note the third row. "Dead level, no downward or upward tilt" reads like a failure and is
not one; it is still an ideal. Name the **artefact you would see**, not the camera
setting you wanted.

## Prompt architecture

One invariant block, one line that changes.

```
REFERENCE CONTRACT    which attachment is truth for what, and what NOT to take
THE PRODUCT           panel by panel, seam by seam
NO BRANDING           if de-branding, state it as the ONE permitted deviation
MODEL                 identity and wardrobe, "unchanged every frame"
RIG                   the camera finish -- ground, light, contrast, grain
SHOT                  <-- the only line that changes
FINISH / FAIL IF      grade, then the named failures
```

Only `SHOT:` varies across a set. That invariance is what makes frames read as one
shoot — though it buys consistency without guaranteeing it: one plate of four invented a
horizon line the other three lacked, from an identical RIG block. Look at the set.

**The camera finish comes from a reference, in words.** A client supplies a look whose
*grade* they want, not whose subject they want. Read the plate and write the grade out;
never wire it as a reference, which drags its composition in.

```
warm cream      warm cream seamless with a sand cast, broad soft frontal daylight,
                low contrast, slightly lifted blacks, rich-but-unsaturated colour,
                fine even film grain, medium-format film not digital studio
```

When the model plate's ground differs from the product plates', **say which one wins and
tell the user you overrode it.** Taking identity from one plate and set from another is
normal; doing it silently is not.

## The shots — split by what the product does

Twelve variations of "worn" is one shot photographed twelve times. Split by **function**,
and let the product set the split.

```
convertible bag   4 tote-mode carries, 4 pack-mode, 2 conversion, 2 detail
single-mode bag   drop conversion; add context and scale frames
apparel           front / back / movement / detail
footwear          angles on-foot, in motion, macro
small goods       few full-lengths, more in-hand scale frames, more macro
```

Every shot line carries **camera height and focal length**. Without them the model
defaults to eye-level 50mm and the set reads flat.

Conversion frames — the mechanism half-done — are the weakest in every run. Hands read
as *handling* the straps, not stowing them. If conversion matters, wire a reference
showing the mechanism mid-action; description alone has not carried it.

## Model routing

**GPT Image 2, `quality: "high"` — every plate, every view.**

- Fine structure survives: stitching, webbing, a debossed patch, laminated zip tape.
- It renders legible type when a layout needs it.
- **It does not harmonise neutrals.** Nano Banana Pro drifts a black product toward
  charcoal against a warm ground; GPT holds it.

Plates and views `3:4`; key visual `16:9`, `resolution: "2k"`. Resolution defaults to
`1k`, so asking for `2k` is load-bearing. Quality already defaults to `high`.

**Seedream 5 Pro** is a poor fit — a 5000-character prompt cap compresses the invariant
block past where it holds, it has no 4:5, and it caps at 2k.

## Timing — the poll lies

```
GPT Image 2  3:4  2k high     ~105-118s of actual work, measured four times
```

**The run poll lags far behind the run, and the lag is unbounded.** Measured twice:

```
true span (created_at -> completed_at)     observed as "running"
105 s                                      ~25 min
110 s                                      ~48 min
```

`progress` never moved off `0` on either — it is a placeholder, not a progress bar. A
*technique* run does report real progress (40 → 70 → 94 → 100), and a credit-free
*action* completed and read back correctly in 9 seconds with no lag. The lag belongs to
generation runs.

**Never conclude anything from elapsed poll time.** Do not re-fire, do not report a
hang, do not tell the user it is stuck. Poll `flora_list_generations`, not
`flora_get_run`. When it lands, read `completed_at` and report *that* as the duration.
Tell the user the queue is opaque and the wait is not the work.

## De-branding

Legitimate and routine, with one discipline: **state the removal as the single permitted
deviation from the reference**, so the model knows every other pixel is still binding.

```
BRANDING - THE ONE CHANGE FROM THE REFERENCE
The product carries NO branding of any kind. Remove every mark: no emblem, logo,
wordmark, printed, embroidered, moulded or woven mark, no label, tag or lettering
anywhere. Every surface is plain. Where the reference shows a mark, render plain
material.
```

Back it with a `FAIL IF` clause, and check the back panel specifically — wordmarks live
there and survive when a front logo has gone.

Watch the other direction too. A third-party technique can *inject* branding: one
returned eight views of a different, branded product entirely (below).

## Delivery — the deck

A4 landscape, one page per thing. Neutral chrome. Only `PROJECT` and `DATE` are
parameters, both in the footer.

```
1   COVER        title, spec strip, hero image full width beneath
2   THE PRODUCT  the plates across, with one line stating they are wired in
3   THE SET      contact sheet -- how a gallery actually reads
4+  EACH VIEW    ONE PAGE EACH. Image left ~47%. Right column: MODE / SHOT / GRADE.
                 Print the SHOT you ASKED FOR, not a description of the result --
                 it is the brief, and it makes the deck actionable
n   KEY VISUAL   full width, one paragraph on the layout, if the set earns one
```

No audit block, no pass/fail marks. If a frame is visibly wrong, say so in one plain
sentence when reporting back, not in the deck.

Write the builder from the appendix and run it beside the deliverables — it resolves
`assets` and writes the html relative to the CWD:

```bash
cd <project>/Deliverables
python3 build_pdp_deck.py deck.json
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless \
  --disable-gpu --no-pdf-header-footer --print-to-pdf="out.pdf" \
  --virtual-time-budget=25000 "file://$PWD/out.html"
```

Every section is conditional on its files existing, so **the deck builds from a partial
set and rebuilds as assets arrive** — drop `kv-plate.png` in and re-run to get the key
visual pages. A one-plate, one-view run produces a valid four-page deck. The docstring
carries the `deck.json` shape and the expected filenames.

Land it at `<project>/Deliverables/`, HTML beside the PDF — it re-renders in about two
seconds, so a layout tweak never costs a regeneration.

**Check the render, do not assume it.** Read the PDF pages back as images. Overflow into
the footer is the common failure — a 16:9 at full page width is too tall once a heading
and caption are on the page; cap it around 229mm wide.

**Say the full path in the final message.**

Video in a PDF embeds as a Rich Media annotation but **only Acrobat plays it.** Preview,
Chrome, Safari and every phone viewer show a static poster and look broken. If a set
includes a film: poster frame large, a filmstrip across the take, and the `.mp4` shipped
beside the PDF.

## Gotchas

```
HOSTED SERVER
one reference          i2i reproduces the reference's VIEWPOINT. The SHOT line does not
                       rotate the subject. Four angles from one photo = four duplicates,
                       billed four times.
params.image_url       the i2i input, a SINGLE STRING. params.image_urls plural is
                       accepted, IGNORED, and still billed.
techniques             a declared imageUrl input may be IGNORED. One returned 8 views of
                       the branded product it was authored on, status completed, no
                       warning. Its output ids named that product -- read them first.
                       Probe once and LOOK before routing a set through it.
technique outputs      absent from flora_list_technique_runs. Use execute ->
                       client.techniques.runs.retrieve(runId, {techniqueId}).
flora_get_run          500s on a TECHNIQUE run despite claiming to poll them. Works for
                       actions. Lags badly for generations.
flora_run_technique    takes no project_id -- it creates its OWN project.
wired gen nodes        INERT. flora_add_to_canvas creates them; nothing runs one.
                       flora_run_canvas_action runs ACTION nodes only, credit-free.
flora_add_to_canvas    add-only. Re-declaring an existing id creates a SECOND node and
                       warns. A 200 with warnings is not a clean apply.
flora_get_canvas       its diagram is a picture, not a document. Sending it back
                       duplicates every node it declares.
charged_cost           a generation quoted 0.253 and settled 0.519 -- 2.05x, twice. A
                       technique settled at exactly its quote. Do not generalise the
                       markup. Quote from a COMPLETED run or call the number a floor.
runs API over curl     needs the API key. Media urls do not.
media urls             credential-free; the path contains the date -- never reconstruct.

WEBMCP
flora_add_nodes        cannot create edges -- use flora_apply_changeset
flora_get_node_details takes `ids`, max 20
short ids              reassigned as the canvas mutates -- wire by UUID
spend modal            blocks the PRIOR call. After approval, RE-FIRE.
deletion               needs a human confirm in the tab, separate from spend
page reload            clears spend approval AND in-page state. Re-read prompts off
                       the nodes.
changeset validation   ONE bad param fails the ENTIRE changeset; the error returns
                       valid_values. Probe one node when unsure.
```

## Reporting back

Contact-sheet the set. Name the strongest and why. Name every frame that drifted and
**what specifically** drifted — not "frame 5 is weak" but "frame 5 uses the tote handles
over the shoulders rather than the padded harness, so it sits in the pack-mode block
showing a tote-mode carry."

**Do not verify by numbers.** Pairwise pixel difference across one technique's eight
frames was 4.8x higher than across four hand-prompted plates, which reads as far better
angle separation and was exactly wrong — the separation was a different object, not a
better camera. Only looking caught it.

Say plainly which frames you checked by eye and which you did not. A set nobody looked
at is a contact sheet, not a delivery.

---

## Appendix — build_pdp_deck.py

Write this out verbatim beside the deliverables and run it. Its docstring is the spec for
`deck.json` and for the filenames it expects inside the assets directory.

```python
#!/usr/bin/env python3
"""
build_pdp_deck.py -- packs a PDP asset set into an A4-landscape deck.

Reads a config JSON, emits <name>-deck.html beside it, then render with:

  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless \
    --disable-gpu --no-pdf-header-footer --print-to-pdf="<name>-deck.pdf" \
    --virtual-time-budget=25000 "file://$PWD/<name>-deck.html"

Every section is conditional on its files existing, so the deck can be built
before the whole set has landed and rebuilt as assets arrive.

config.json:
{
  "title":   "Axios 20 Tote",
  "project": "Axios 20 Tote -- PDP Set 02",
  "date":    "26 August 2026",
  "assets":  "assets2",
  "grade":   "Scanned medium-format film",
  "product_note": "one paragraph on construction and that the plates are wired in",
  "set_note":     "one paragraph on why the set splits the way it does",
  "kv_note":      "one paragraph on the key visual layout",
  "grade_line":   "printed in the GRADE row of every view page",
  "shots": [["01","TOTE MODE","Carried at his side","the SHOT line you ASKED FOR"], ...]
}

Expected filenames in <assets>/:
  prod-front.png prod-34.png prod-side.png prod-back.png   product plates
  pdp-01.png ... pdp-12.png                                the views
  kv-plate.png                                             key visual (optional)
"""
import json, base64, os, sys

cfg = json.load(open(sys.argv[1] if len(sys.argv) > 1 else 'deck.json'))
A          = cfg['assets']
TITLE      = cfg['title']
PROJECT    = cfg['project']
DATE       = cfg['date']
GRADE      = cfg.get('grade', '')
GRADE_LINE = cfg.get('grade_line', GRADE)
shots      = cfg['shots']

def have(p):  return os.path.exists(os.path.join(A, p))
def b64(p):
    with open(os.path.join(A, p), 'rb') as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode()

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
@page{size:297mm 210mm;margin:0}
body{font-family:Georgia,'Times New Roman',serif;background:#fff;color:#1c1a17;-webkit-print-color-adjust:exact;print-color-adjust:exact}
.page{width:297mm;height:210mm;padding:16mm 18mm 14mm;position:relative;page-break-after:always;overflow:hidden;background:#faf8f4}
.page:last-child{page-break-after:auto}
.eyebrow{font-family:'Helvetica Neue',Arial,sans-serif;font-size:7pt;letter-spacing:.22em;text-transform:uppercase;color:#8a8177}
.foot{position:absolute;left:18mm;right:18mm;bottom:8mm;border-top:.4pt solid #d8d2c8;padding-top:2.5mm;display:flex;justify-content:space-between;font-family:'Helvetica Neue',Arial,sans-serif;font-size:6.5pt;letter-spacing:.12em;text-transform:uppercase;color:#8a8177}
h1{font-size:40pt;font-weight:400;letter-spacing:-.015em;line-height:1.02}
h2{font-size:19pt;font-weight:400;letter-spacing:-.01em}
.spec{display:flex;gap:14mm;border-top:.4pt solid #d8d2c8;border-bottom:.4pt solid #d8d2c8;padding:3.5mm 0;margin:6mm 0}
.spec div{font-family:'Helvetica Neue',Arial,sans-serif}
.spec .k{font-size:6.5pt;letter-spacing:.18em;text-transform:uppercase;color:#8a8177;margin-bottom:1.5mm}
.spec .v{font-size:9pt;color:#1c1a17}
.grid4{display:grid;grid-template-columns:repeat(4,1fr);gap:6mm}
.grid4 img{width:100%;display:block;background:#fff}
.grid6{display:grid;grid-template-columns:repeat(6,1fr);gap:4mm}
.grid6 img{width:100%;display:block}
.cap{font-family:'Helvetica Neue',Arial,sans-serif;font-size:6.5pt;letter-spacing:.14em;text-transform:uppercase;color:#8a8177;margin-top:2mm}
.split{display:flex;gap:10mm;height:148mm;align-items:flex-start}
.split .im{width:47%;height:100%;display:flex;align-items:flex-start;justify-content:center}
.split .im img{max-width:100%;max-height:100%;display:block}
.split .tx{width:53%;padding-top:1mm}
.meta{margin-top:7mm}
.meta .r{display:flex;gap:5mm;padding:2.6mm 0;border-top:.4pt solid #e2ddd4}
.meta .r:last-child{border-bottom:.4pt solid #e2ddd4}
.meta .k{font-family:'Helvetica Neue',Arial,sans-serif;font-size:6.5pt;letter-spacing:.16em;text-transform:uppercase;color:#8a8177;width:22mm;flex:none;padding-top:.6mm}
.meta .v{font-size:9pt;line-height:1.5;color:#3a352e}
.note{margin-top:7mm;font-size:9pt;line-height:1.55;color:#4a443c}
.wide img{width:229mm;display:block;margin:0 auto}
"""

P = []
def page(inner, n):
    P.append(f'<div class="page">{inner}'
             f'<div class="foot"><span>{PROJECT}</span><span>{DATE}</span>'
             f'<span>{n:02d}</span></div></div>')

n = 1
# Labels are the product's, not this file's. Override with cfg["plates"].
PLATES = [tuple(x) for x in cfg['plates']] if cfg.get('plates') else [
    ('prod-front.png', 'Front'), ('prod-34.png', 'Three-quarter'),
    ('prod-side.png', 'Side'),   ('prod-back.png', 'Back')]

# 1 COVER -- key visual if present, else the strongest worn view
spec = [('Product plates', f'{sum(1 for f,_ in PLATES if have(f))} · 864×1152 · 3:4'),
        ('PDP views',      f'{len(shots)} · 864×1152 · 3:4')]
if have('kv-plate.png'): spec.append(('Key visual', '1 · 2560×1440 · 16:9'))
if GRADE:                spec.append(('Grade', GRADE))
spec.append(('Branding', 'None — removed throughout'))
spec_html = "".join(f'<div><div class="k">{k}</div><div class="v">{v}</div></div>' for k, v in spec)

if have('kv-plate.png'):
    hero = f'<img src="{b64("kv-plate.png")}" style="width:196mm;height:auto;display:block;margin:2mm 0 0">'
else:
    # A short set has no pdp-05. Fall back to the first frame that actually exists,
    # then to a product plate, then to nothing -- never assume a fixed filename.
    cand = [f'pdp-{s[0]}.png' for s in shots] + [f for f, _ in PLATES]
    pick = next((f for f in cand if have(f)), None)
    hero = (f'<img src="{b64(pick)}" style="width:auto;height:104mm;display:block;margin:2mm auto 0">'
            if pick else '')
page(f'<div class="eyebrow">Product detail page — asset set</div>'
     f'<h1 style="margin-top:5mm">{TITLE}</h1>'
     f'<div class="spec">{spec_html}</div>{hero}', n); n += 1

# 2 THE PRODUCT
if any(have(f) for f, _ in PLATES):
    cells = "".join(f'<div><img src="{b64(f)}"><div class="cap">{lbl}</div></div>'
                    for f, lbl in PLATES if have(f))
    page(f'<div class="eyebrow">The product</div>'
         f'<h2 style="margin:4mm 0 6mm">Reproduced in every frame</h2>'
         f'<div class="grid4">{cells}</div>'
         f'<div class="note" style="max-width:170mm">{cfg.get("product_note","")}</div>', n); n += 1

# 3 CONTACT SHEET
cells = "".join(f'<div><img src="{b64(f"pdp-{s[0]}.png")}"><div class="cap">{s[0]}</div></div>'
                for s in shots if have(f'pdp-{s[0]}.png'))
_have = sum(1 for s in shots if have(f'pdp-{s[0]}.png'))
page(f'<div class="eyebrow">The set</div>'
     f'<h2 style="margin:4mm 0 6mm">{_have} view{"" if _have == 1 else "s"}</h2>'
     f'<div class="grid6">{cells}</div>'
     f'<div class="note" style="max-width:170mm">{cfg.get("set_note","")}</div>', n); n += 1

# 4.. ONE PAGE PER VIEW
for idx, mode, name, shot in shots:
    if not have(f'pdp-{idx}.png'): continue
    page(f'<div class="eyebrow">{mode}</div>'
         f'<h2 style="margin:3mm 0 5mm">{idx} — {name}</h2>'
         f'<div class="split"><div class="im"><img src="{b64(f"pdp-{idx}.png")}"></div>'
         f'<div class="tx"><div class="meta">'
         f'<div class="r"><div class="k">Mode</div><div class="v">{mode.title()}</div></div>'
         f'<div class="r"><div class="k">Shot</div><div class="v">{shot}</div></div>'
         f'<div class="r"><div class="k">Grade</div><div class="v">{GRADE_LINE}</div></div>'
         f'</div></div></div>', n); n += 1

# n KEY VISUAL
if have('kv-plate.png'):
    page(f'<div class="eyebrow">Campaign</div>'
         f'<h2 style="margin:3mm 0 5mm">Key visual</h2>'
         f'<div class="wide"><img src="{b64("kv-plate.png")}"></div>'
         f'<div class="note" style="max-width:229mm;margin-top:5mm">{cfg.get("kv_note","")}</div>', n); n += 1

out = cfg.get('out', f"{TITLE.replace(' ', '-')}-deck")
html = (f"<!doctype html><html><head><meta charset='utf-8'>"
        f"<title>{TITLE}</title><style>{CSS}</style></head><body>{''.join(P)}</body></html>")
open(f'{out}.html', 'w').write(html)
print(f"{out}.html  --  {n-1} pages")
```
