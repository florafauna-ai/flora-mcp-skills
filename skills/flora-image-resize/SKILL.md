---
name: flora-image-resize
description: >
  Generatively resize/reframe a source image into other aspect ratios (9:16, 16:9,
  1:1, 4:3, 3:4, 21:9) using FLORA's image-to-image models, holding the subject,
  props, palette and grade rather than cropping or letterboxing. Use when someone
  wants one image in several placements — "make a 9:16 from this hero", "resize
  this for Stories", "I need this banner as a square", "reframe without cropping",
  "outpaint this image", "same shot, different ratios". Also trigger on "image
  resize" in any FLORA context. Do not use when the original pixels must survive
  untouched — a legal-approved pack shot, an approved ad creative, anything
  already signed off — because this re-renders the frame; use the free
  `change-image-ar-browser` action for those. Do not use for video, which is
  flora-video-resize, and do not use to place finished artwork into a scene,
  which is flora-mockup-deck.
---

# FLORA Generative Image Resize

One source image into every placement's aspect ratio, generatively — no bars, no
crop that loses the subject.

## The law

**A reframe is a re-render that holds the subject, not an extension that holds the
pixels.** The model rebuilds the whole frame in the new shape, carrying subject,
props, palette and grade across. It does not paste the original in and paint the
margins. If a pixel must survive review unchanged, do not generate — pad or crop.

This is the one place this skill differs from `flora-video-resize`, whose v2v
prompt recipe can instruct the source to span the full width. It does not transfer.

## Trigger

User supplies an image (upload or URL) and wants other aspect ratios. Ask or infer
the targets — default set: 9:16, 16:9, 1:1.

## The source goes in `params`, and that is not true of video

`flora_generate` **does** accept an i2i source through `params.image_url`:

```json
{ "model": "i2i-qwen-image-edit", "type": "image",
  "params": { "aspect_ratio": "9:16", "image_url": "https://…/source.png" } }
```

Verified — a 1024×1024 source returned 864×1536 with the subject, every prop, the
palette and the grade carried across. **Do not copy the canvas-edge workaround from
`flora-video-resize`.** That skill's #1 failure mode is that v2v silently ignores a
source passed this way and bills you for an unrelated text-to-video clip. i2i does
not behave that way, and wiring a canvas graph to get around a problem you do not
have costs you two extra calls per ratio.

Sanity-check the first run anyway: if the output shares no props with the source,
the source was dropped and everything after it is text-to-image.

## Models

| Model | AR control | Est. | Use |
| --- | --- | --- | --- |
| `i2i-qwen-image-edit` | **native `aspect_ratio`** — 21:9, 16:9, 4:3, 3:2, 1:1, 2:3, 3:4, 9:16, 9:21 | 40 cr / ~25s | **Default.** The only one you can actually aim. |
| `i2i-qwen-image-edit-plus` | same | 40 cr / ~120s | 5× slower for the same quote. Only if Edit degrades the subject. |
| `i2i-imagen-3-outpainting` | **none** — `seed` only | 54 cr / ~26s | Extends edges. You cannot tell it the target shape. |
| `i2i-out-flux-2-pro` | **none** — `outpaint_mode`, `auto_crop` only | see below | Same. |

**The models named "outpaint" are the wrong reach.** An agent matching on the word
gets `i2i-imagen-3-outpainting` or `i2i-out-flux-2-pro`, neither of which exposes an
aspect ratio — the one parameter this job is about. Reach for `i2i-qwen-image-edit`.

**`i2i-out-flux-2-pro` reports `estimated_credits: 0`.** It is not free. Its
provider is `generation_gateway`, and the catalog reports 0 for every model behind
that gateway — the same defect `flora-video-resize` names for Seedance. Never quote
a gateway model's cost from the catalog.

## Costs are quoted high

Measured on `i2i-qwen-image-edit`: **quoted `charged_cost: 0.036` at submit,
actually charged `0.02` on completion.** Quote from the submit value so nobody is
surprised upward, and report the completion value as the real number. Four ratios
is roughly 0.08, not 0.15.

## 4:5 exists nowhere

Not in `i2i-qwen-image-edit`'s options, and not in the free AR action either. Both
stop at 3:4 and 2:3. Generate the nearest native ratio — **3:4** — then trim the
small delta with the free `change-image-ar-browser` action. Never ask the model for
4:5; `aspect_ratio` is an enum and an unlisted value is not honoured.

## Steps

1. **Look at the source.** Note subject, wardrobe or packaging, every prop, the
   background, the grade, and every text string verbatim. These go in the prompt —
   the model is rebuilding the frame and will drop anything you do not name.
2. **Pick the ratios.** Default 9:16, 16:9, 1:1. Derive 4:5 from 3:4.
3. **Fire all ratios concurrently** through `flora_generate` with
   `params.image_url` and `params.aspect_ratio`. Concurrent is one wait; sequential
   is N waits, and each run is ~25s.
4. **Prompt, one per ratio:**
   - Open with the transform: `Reframe this image from {source AR} to {target AR}.`
   - Pin what carries: `Keep the subject ({name it: identity, wardrobe, packaging}),
     every prop ({list them}), the background, lighting and colour grade exactly as
     in the source.`
   - Direct the new area: `Extend the scene into the revealed {top and bottom /
     left and right}, continuing {name the surface or backdrop}.`
   - Lock the type: `Reproduce all text and logos glyph for glyph: {each string}.`
   - Close: `Do not restyle, recolour, or replace the subject.`
5. **Poll** with `flora_get_run`. The output URL may land under `node-inputs/`
   rather than `node-outputs/` — that is normal for an i2i result, not an error.

## Verification

Check every output before delivering:

- **Ratio.** Confirm the pixel dimensions divide to the target. 864×1536 is 9:16.
- **Prop survival.** List the source's props and tick each one off in the output.
  This is the check that catches a silent text-to-image — the subject may look
  right in style while every object around it changed.
- **Text.** Read every string. Re-rendered frames re-typeset, and small prop text
  drifts first.
- **Composition drift.** Expect the subject to move and change scale; that is the
  law, not a defect. Reject only if it is cropped out, restyled, or duplicated.

One failed check → one retry with the prompt tightened on the failure. Still
failing → deliver the best output and name the defect. Report the completion
`charged_cost` per run and the project link.

## Breaks when

- **The source is an approved asset.** The frame gets rebuilt; approval does not
  survive it. Pad or crop instead.
- **Fine print must be legible.** Re-typesetting is a re-render, not a copy.
- **The source is already extreme.** A 21:9 panorama to 9:16 is ~85% new pixels;
  the model is inventing a picture with a hint, and it looks like it.

## Pairs with

`flora-video-resize` for the moving version of the same job. `flora-mockup-deck`
when the ask is to place finished artwork into the world rather than change its
shape — that one reproduces the artwork exactly and never regenerates it.
