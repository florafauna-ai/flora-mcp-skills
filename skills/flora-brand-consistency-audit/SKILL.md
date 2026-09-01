---
name: flora-brand-consistency-audit
description: Judge a set of generated assets against a brand's actual rules — subject and product identity, palette, lighting and treatment, framing and crop system, logo and type lockups, background rules, and output specs — and return findings with severity, evidence and a fix per finding. Use after a batch generation, before a client review, before assets go to an ad platform or a PDP, and whenever a set is individually acceptable but collectively inconsistent. Trigger on "does this match the brand", "review this batch", "check these against the guidelines", "are these on-brand", "the set doesn't hang together", "QA these before we send them", or any request to sign off generated output against a brand book. Not for checking whether the workspace's references are set up — that is creative-context-audit.
---

# flora-brand-consistency-audit

> **Attribution.** Pass `skill: "flora-brand-consistency-audit"` on every FLORA call you
> make while running this skill — `execute` included — along with a `skill_run_id` you
> invent once when the run starts and reuse for the rest of it. Both are reporting only:
> they change nothing about the call or its result.

**This audit is cheap, not free.** Listing assets and reading records costs nothing.
Looking at an image costs a vision call — **measured 0.005–0.006 per image**, so a
stratified sample of a dozen is under a dime and a 200-asset close-read is not. Sampling
is a budget decision as much as an attention one. Quote the sample size before you start.

The failure this catches is specific and it is not ugliness: **200 assets that are each individually fine and collectively do not agree.** Nothing errors. Every asset passes on its own. The set fails.

Judging assets one at a time cannot catch it. The method here is built around that.

## What this supplies

The standard, extracted from the brand book into rules you can actually check, plus the set-level method that finds drift a per-asset review structurally cannot. Without the extracted standard, brand feedback is taste — and taste loses to the loudest person in the review.

## Step 1 — Extract the standard before looking at anything

**Do not open the assets first.** Looking first anchors you, and you will rationalise what you see.

Turn the brand book into checkable rules. A rule is checkable when two people applying it to the same asset reach the same verdict. Work through these dimensions and write the rule or write "not specified":

| Dimension | A checkable rule looks like |
| --- | --- |
| **Subject / product identity** | "Same SKU across the set: colourway, sole geometry, logo placement, stitching all match the reference plate" |
| **Palette** | "Background within the warm neutral range; no cool grey. Product colour matches reference, no shift" |
| **Lighting & treatment** | "Single soft key from camera-left, soft shadow, no hard specular hits on the product" |
| **Framing & crop** | "Product occupies 60–70% of frame height, centred, consistent margin" |
| **Logo & type lockup** | "Lockup bottom-left, clear space equal to logo height, never overlapping the product" |
| **Background & environment** | "Studio seamless only, or approved environment list — no invented interiors" |
| **Output spec** | Aspect ratios, resolution, file type required by the destination |

Rules the client cannot supply are **not** rules you invent. Mark them "not specified" and say so in the findings — an unspecified dimension is a decision the client has not made, and surfacing it is worth more than a guess dressed as a finding.

If the client cannot supply rules for any dimension, stop. There is no standard, so there is no audit — there is only your opinion, and you should say that plainly rather than deliver it as findings.

## Step 2 — Read the set, not the assets

Pull the set with `flora_list_assets({ project_id })` — or `flora_list_canvas_nodes({ project_id })` for what is actually on the canvas. The two disagree: an action's output is an asset but never a canvas node, so a set audited from the canvas alone silently omits every resize and composite.

Check first, across the whole set, before close-reading anything:

- **Spec conformance** — dimensions and file type on every asset. Off-spec assets are objective failures and cost nothing to find. Catch them here, not in the review. **Do not read them off the asset record** — see below, it does not say what it looks like it says.
- **Completeness** — one asset per intended row. A batch that silently returned 194 of 200 looks complete in a grid.
- **Status** — anything not `ready` is a failure, not a pending item.
- **Modality** — filter on `content_type` before anything else. A real project mixes images and video, and a palette or framing finding computed over an `mp4` is noise. Measured: a 10-asset project held 3 videos alongside 7 images.

### The asset record cannot answer the spec question

Measured on one project, and this is the trap in the whole step:

```
width / height   NULL on 3 of 5 assets from a SINGLE generation batch. Populated on
                 the other 2. flora_get_asset returns null for the same asset, so
                 there is no second endpoint to ask.
size_bytes       12,021,479 on the record. 969,929 actually served. 12.4x.
content_type     "image" — a modality, not a MIME type. It cannot answer "is this
                 a PNG".
the url          ends .png and serves Content-Type: image/jpeg, signature ffd8ffdb.
                 With Vary: Accept, so the format is NEGOTIATED per request — a
                 browser may be handed WebP. File type is not a property of the
                 asset at all.
```

So an agent that checks spec from the record reports confident nonsense: nulls read as
zero, a 12 MB original that ships as 1 MB, and a `.png` that is a JPEG.

**Ask the file instead** — free, no credentials, `Accept-Ranges` honoured:

```
HEAD <url>                     -> real Content-Type and Content-Length
GET <url> Range: bytes=0-15    -> 206, and the magic number settles the format
                                  89504e47 PNG · ffd8ff JPEG · 52494646 WebP
```

**This runs on the client, never inside `execute`.** The sandbox reaches no host but the
FLORA API — a `fetch` at `media.flora.ai` from `execute` returns `TypeError: fetch
failed`, measured. So spec conformance needs a shell or a fetch tool on the surface
you are running on.

**On a surface with neither — claude.ai, ChatGPT — you cannot verify spec. Say so.**
Do not substitute the vision model's guess: asked to estimate dimensions it returned
`750x1000` for an image that is `3520x2352`. Report spec as unchecked rather than wrong,
and audit the dimensions you *can* check — orientation and framing — from the pixels.

**When a destination spec names a file type, say which one you tested** — the stored
original or the delivered file. For an ad platform or a PDP it is the delivered one that
gets rejected, and it is the one nobody checks.

Then look at the set **as a set**. Lay it out as a contact sheet, not a scroll — `flora_run_action` with `side-by-side-composite-browser`, which is credit-free but **entitled per workspace**: it returns `403 "Actions are not enabled for this workspace"` on plans without it. Where that fires, fall back to judging in generation order and say the set-level pass was done serially. The set-level questions:

- Does the **palette drift** across the run — do the last twenty read cooler or warmer than the first twenty?
- Does the **treatment hold** — same lighting logic on every asset, or does it wander?
- Does the **subject stay itself** — same product, or the same product's cousin by asset 80?
- Is there a **cluster** — do assets sharing an input, a prompt variant, or a batch position fail together? Clustered failures point at the workflow; scattered ones point at the prompt.

Ordering matters: sort by generation order to see drift, then group by input to see clusters.

## Step 3 — Close-read a stratified sample

Do not eyeball 200. Sample deliberately:

- The **reference plate** or hero asset — everything else is judged against it.
- **First, middle, last** by generation order — drift shows up here.
- Every asset flagged at set level.
- A random handful from the unflagged remainder, to test whether the set-level pass was real.

Compare each sampled asset **against the reference plate side by side**, dimension by dimension. Never from memory.

### Seeing the image, when you cannot see the image

The MCP returns urls, not pictures. On a surface that cannot open one, judge with a
vision model and make it describe before it rules:

```
flora_generate  type: "text", model: "i2t-gemini-3-7-flash-i2t"
                params: { image_urls: [url] }     <- PLURAL. ARRAY.
```

**`image_urls` for i2t. `image_url` for i2i. They are inverted, and getting it wrong is
silent.** Measured on one image, same model, same prompt: with `image_url` the judge
returned a confident description of *a gold torque choker necklace* — an image that does
not exist anywhere in the project — and billed 0.005. With `image_urls` it returned the
bus shelter that was actually there, transcribed the headline correctly, and billed
0.006. Both runs reported `completed`. Nothing errored.

So an audit built on the singular form invents its own evidence and reads as a clean
pass. **Ask the judge to transcribe something you can independently verify** — the
headline, the SKU on the pack — and check it against the brief. A judge that cannot
quote the type in the plate is not looking at the plate.

Order the JSON with `observed` first and demand the description before the verdict, or
the model rules from your rule text rather than the pixels.

## Findings format

One row per finding. Evidence is the `asset_id` — a finding without one cannot be acted on.

```
[SEVERITY] Dimension — what is wrong
Evidence: <asset_id(s)>, and what specifically differs from the rule
Scope: <this asset | this cluster of N | the whole set>
Action: <re-run with X changed | accept as within tolerance | escalate to the client as an unspecified rule>
```

Severity:

- **Reject** — breaks a stated brand rule. Cannot ship. Identity drift, wrong lockup, off-spec output.
- **Fix** — within the rule's spirit but visibly inconsistent with the set. Palette or treatment wander.
- **Flag** — a dimension the brand book does not cover, where the set has made a choice on the client's behalf. Not a defect; a decision they need to make.

**Scope is what makes findings actionable.** "Fifteen assets share this defect and they all came from the same input" is a workflow fix. Fifteen separate findings is a re-shoot.

Lead the report with the set-level verdict and the cluster findings. Individual asset findings go last — they are the least useful part and reviewers stop reading.

## Breaks when

- **The rules were never written down.** Then the findings are taste, and taste loses the argument. This is the failure mode of the whole type.
- **Assets are judged individually.** Per-asset review returns "these all look fine" on a set that does not hang together. That verdict is how inconsistent work ships.
- **The reference plate is itself off-brand.** Everything is judged against it, so validate the plate against the brand book before using it as the benchmark.
- **The audit is run after the client review** rather than before it. Finding drift in the room is not an audit, it is a post-mortem with an audience.
- **Tolerance is never agreed.** "Slightly warmer" is a Fix to you and a Reject to the brand team. Agree the tolerance for palette and treatment before the first audit, in writing.

## Pairs with

Run against the output of `flora-batch-generate` as standard — collective inconsistency is that skill's named failure mode, and this is the check for it. Where drift traces back to ungrounded references rather than the prompt, the fix is upstream: run `creative-context-audit` on the workspace instead of re-running the batch.

## Handing it over

The deliverable that survives you is the **extracted rule set**, not the report. A client with their brand book turned into checkable rules can audit every future batch themselves. A client who has your findings has one batch reviewed and a reason to call you about the next one.
