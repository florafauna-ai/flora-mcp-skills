---
name: flora-brand-ad-pipeline
description: >
  Produce brand-controlled ad creative for a product launch and carry it all the way
  through archive, hosting and ad creation — FLORA generation under a locked brand
  treatment, then Google Drive for archive, then Supabase storage for hosting, then
  Meta Ads creatives left in paused state for a human to review. Use when someone asks
  for launch creative, campaign assets for a new product line, ads for a store or a
  season, "a set of ads for the strawberry launch", or "get these staged for me to
  review". Do not use for a one-off image with no campaign around it — that is
  flora-batch-generate — and never use it to unpause, publish, or set a budget on an ad.
---

# flora-brand-ad-pipeline

> **Attribution.** Pass `skill: "flora-brand-ad-pipeline"` on every FLORA call you
> make while running this skill — `execute` included — along with a `skill_run_id`
> you invent once when the run starts and reuse for the rest of it. Both are
> reporting only: they change nothing about the call or its result.

## What it is

Not a creative assistant. **A conveyor.** A product line goes in one end; paused ads,
an archived master and a hosted CDN copy come out the other, with one record tying
every ad back to the generation that made it.

FLORA is one stage of four. Most of what makes this reliable is not the generation —
it is refusing to advance a stage that has not been proven, and keeping enough state on
disk that a re-run repairs the pipeline instead of duplicating it.

## The law

> **The brand is an input, not an instruction.**

Fixed colours, a price that must always be visible, product reference shots: these
decay the moment they are carried as prose an agent retypes each run. Agents
paraphrase. A paraphrased brand drifts, and it drifts silently across every item in a
batch — nobody sees it until a human opens the ads.

So the brand never lives in this file, and never lives in a prompt you compose:

- **The treatment lives in a saved FLORA technique.** A technique's steps, prompts and
  model choices are fixed by its author, so it gives the same treatment every time and
  the agent cannot rewrite the middle of it. Whatever can move out of prose and into a
  technique, move.
- **The product lives in a reference image.** Reference-locked, never re-described.
- **The values live in `brand.json`.** Colours, price format, placement sizes, product
  reference ids. See `reference/brand.md`. Read it; do not inline it.
- **The price is composited, not generated.** No image model renders a price string
  reliably, and "price always visible" is a compliance requirement, not a style note.
  Overlay it deterministically and the question becomes a boolean.

## The rule

> **Pipeline state lives in the manifest, not in the conversation.**

One JSON record per campaign, written after every stage and read before every stage.
Every row carries one `asset_key` that travels the whole way — FLORA run, Drive file,
Supabase object, Meta creative. Contract in `reference/manifest.md`.

Two things this buys, neither optional:

- **A re-run repairs rather than duplicates.** Meta will cheerfully create a second
  identical paused ad. The manifest is the only thing that knows the first one exists.
  Variables do not persist between `execute` calls and the agent's context will not
  survive the campaign.
- **A bad creative is traceable.** Someone spots a wrong price in Ads Manager. Without
  the join key there is no path back to the prompt, the technique version, or the
  reference shot that produced it.

## Inputs

```
CAMPAIGN     what is launching — the line, the store, the season      required
PRODUCTS     the SKUs, with a reference shot for each                 required
BRAND        path to brand.json                                       required
PLACEMENTS   which sizes to produce                        optional, brand.json default
MANIFEST     path to an existing campaign manifest          optional, resumes if present
```

If `BRAND` is missing, stop. Do not improvise a palette or a price treatment from the
campaign description — that is exactly the failure the law exists to prevent.

## The five stages

Each stage ends in something a human could reject. Keep them as separate calls; do not
build a loop that must outlive the sandbox.

### 1. Resolve — free, and it is where the campaign is saved

Nothing here spends.

- Read `brand.json`. Confirm the palette, the price format and the placement list back
  to the user in their own vocabulary.
- Read the manifest if one exists. **Report what is already done before proposing
  work.** A resumed campaign that re-fires completed rows is the expensive failure here.
- Resolve the workspace with `flora_list_workspaces`. More than one, ask which to bill.
- Resolve the technique with `flora_get_technique`. Its declared input ids are the keys
  the run expects — never guess them from the name.
- Confirm every product has a reference shot reachable as an HTTPS URL.
- Total the cost across products x placements and **wait for a yes.**

> **One reference photo yields one good plate, not four.** Measured on `flora-pdp-deck`:
> four angles requested from a single reference came back near-identical — three-quarter
> against rear-180 differed by 3.21 mean absolute grey, less than each differed from its
> own source image. Spend the budget on placements and context frames, where the
> composition genuinely changes. Say this before the customer budgets a four-angle set.

### 2. Generate — delegate, do not reimplement

Hand the fan-out to **`flora-batch-generate`**. It already owns the parts that go wrong:
fire every item before polling any item, `Promise.allSettled` so one rejection does not
discard billed run ids, `limit: 100` explicit on the poll, status-only completion
checks, and the run-time error taxonomy.

This skill adds two things on top of it:

- The per-item variable is the product; the constant is the technique, not a style
  string. Batch `techniques.runs.create()` when the treatment is a technique — the
  idempotency key is then a **body field**, `idempotency_key`, not a header.
- Write `flora_run_id` into the manifest **at fire time, not at completion.** A run you
  fired and lost is billing right now and is unidentifiable.

### 3. Finish — the price layer, then the QC gate

The generated frame is not the deliverable. The deliverable is the frame plus the
deterministic layers.

- Composite the price and the logo lockup per `brand.json`. A FLORA action does this at
  0 credits — the composite actions measured at ~9 seconds on `flora-pdp-deck` — or do
  it in your own code if you already have an image pipeline.
- Then run the QC gate. **These are the only brand checks that can be made honestly:**

```
dimensions and aspect ratio match the placement spec
the price layer is present and above the minimum size
the palette check passes against brand.json
the file opens and is non-trivial in size
```

> **You cannot see any image.** Every check above is structural. Nothing here tells you
> the creative is good, on-brand, or appetising. Never say that it is. Report the URLs
> and the checks that passed, and let the contact sheet and the paused ads do the rest.

Build one contact sheet — a single grid of the whole campaign, one URL — and put it in
front of the user before anything leaves FLORA.

### 4. Distribute — archive, then host

Order matters. **Archive before hosting, host before advertising.** Each stage should
only ever read from the stage before it, so a failure is always a resume point rather
than a fork.

- **Google Drive** is the master archive. Upload the full-resolution finished frame.
  Record `drive_file_id`.
- **Supabase storage** is the serving copy. Upload the web-optimised derivative. Record
  the object path and the public URL.

FLORA media URLs are public, unsigned and permanent. That is the real argument for the
Supabase copy — a live ad must not depend on a URL you do not control. It is also worth
a word to the user on an unreleased launch: pasting a `media.flora.ai` URL into a shared
transcript publishes that asset to anyone who reads it.

### 5. Create ads — paused, always

See `reference/meta-ads.md` for the creative path and the error codes.

> **Paused is an invariant, not a default.** Never unpause. Never set or raise a budget.
> Never create a campaign object the user did not ask for. If the user asks you to
> publish, say plainly that this skill stops at paused and let them do it themselves.

Record `meta_creative_id` and `meta_ad_id` in the manifest as each is created, one row
at a time. A batch write at the end loses everything if the last call fails.

## The gates

```
1  cost              before firing        state credits and dollars, wait for a yes
2  structural QC     before upload        dimensions, price layer, palette
3  contact sheet     before Meta          one grid, one URL, for a human
4  paused            in Meta              the human publishes, never the agent
```

A gate the user has not answered is not a gate. Do not proceed on silence.

## Partial failure at each boundary

The pipeline is not a transaction, and each boundary fails into a different sentence.
Never abort a paid batch partway — generations already running will finish and bill
regardless, so abandoning them loses their URLs and saves nothing.

```
FLORA ok, composite failed    the generation is paid and archivable. Archive it,
                              mark the row blocked at finish, do not re-generate.
composite ok, Drive failed    retry Drive. Nothing downstream has happened.
Drive ok, Supabase failed     retry Supabase. The master is safe.
Supabase ok, Meta failed      the asset is live and hosted and no ad exists. This is
                              the safe failure. Report it and stop; do not retry
                              blind, because a partially-created ad may already exist.
Meta creative ok, ad failed   TODO(measure): confirm whether the orphaned creative is
                              reusable on retry or must be recreated.
```

Every one of these ends in the same action: write the row's state to the manifest, then
report. A failure that is not in the manifest will be re-run from the start.

## Gotchas

```
BRAND
prose brand           the drift is silent and only visible to a human at the end.
                      Technique + reference image + brand.json, never a retyped prompt.
generated price       models render price strings unreliably. Composite it.
one reference         cannot be rotated by asking. 3.21 mean grey between opposite
                      faces requested from the same source. One plate per reference.

FLORA
params not validated  an unknown param VALUE is accepted, runs, completes and bills at
                      the default. Only an unknown MODEL is a clean 400. Validate
                      against models.list() params before firing.
charged_cost          a quote at create, eventually consistent on list. Re-read after
                      the batch is terminal or report the total as a floor.
technique idempotency body field idempotency_key. Generations use a header. Do not
                      carry one pattern to the other.
media urls            public, unsigned, permanent.

PIPELINE
no manifest write     a stage whose result is not written is a stage that will be
                      re-run. Write after every stage, not at the end.
batch the final write and one failure loses every id in the batch.
sandbox               ~5 minutes total per execute call, 30s per HTTP request. Fire
                      and poll are separate calls. So are the four stages.

META
TODO(measure)         creative ingest path, rate limits, and the real error strings.
                      See reference/meta-ads.md.
```

## Reporting back

One row per asset, keyed on the thing the customer thinks in — the SKU and the
placement, never the `run_id`.

```
ASSET             PLACEMENT   COST     STATE      META
straw-hero-1x1    1:1         $0.004   paused     ad 1203…
straw-hero-9x16   9:16        $0.004   paused     ad 1204…
straw-punnet-4x5  4:5         —        blocked    composite failed, price layer absent
```

Then four lines and stop:

- **the total** — settled, or explicitly a floor if any `charged_cost` was missing.
- **the contact sheet URL** — the one link a human should open first.
- **what is blocked, and at which boundary.**
- **what you did not do** — rows skipped, a batch stopped on 402, ads not created.

Say plainly that nothing is live and that no creative has been visually reviewed.

## Edges

This skill does not:

- **Publish.** It stops at paused. Budgets, schedules, audiences and unpausing are the
  user's, every time.
- **Write copy.** Headlines, primary text and CTAs come from the user or from
  `brand.json`. Generating ad copy is a different job with a different reviewer.
- **Handle a single image.** One asset with no campaign around it is
  `flora-batch-generate`, or `flora-run-technique` if a technique already fits.
- **Place finished artwork in the world.** Billboards, transit and in-situ mockups are
  `flora-mockup-deck`.
- **Judge the creative.** It cannot see it. Structural checks and a contact sheet are
  the whole of what it can offer.
