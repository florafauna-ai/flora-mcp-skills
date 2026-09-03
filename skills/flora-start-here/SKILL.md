---
name: flora-start-here
description: Entry point for FLORA's MCP server. Use this skill when (1) an agent has the FLORA MCP connected and needs to decide which flora-* skill applies to a request, (2) the request involves generating images, video, or audio, running a saved FLORA technique, or reading and writing a FLORA canvas, (3) the user has a list of products, SKUs, or variants and wants consistent assets, or (4) a first FLORA result came back wrong and needs to be driven to a goal. Routes to the specialised flora-* skills; does not generate on its own.
---

# FLORA MCP Skills — start here

FLORA's MCP server (`https://agents.flora.ai/mcp`) gives an agent raw capability: generate images, video, audio, and text; run saved multi-step techniques; read and write a FLORA canvas. These skills are the judgment layer — which model, what the gotchas are, what a good result looks like, what to do when one comes back wrong. Every number in them is measured against production, not estimated.

## Route by what the user has

| User has… | Wants… | Load |
|---|---|---|
| A list (products, SKUs, variants, scenes) | One asset per row, one consistent style | `flora-batch-generate` ★ |
| A wrong first result | It driven to a specific goal, not re-rolled blind | `flora-refine-loop` ★ |
| A script or narrative | Animated clips with a consistent character | `flora-script-to-video` |
| Generated clips or stills | Cut together into a sequence with motion | `flora-motion-compositor` |
| An existing image | A saved workflow applied (relight, upscale, background swap, sketch-to-render) | `flora-run-technique` |
| A finished image | New aspect ratios or sizes without regenerating | `flora-image-resize` |
| A finished video | New aspect ratios without regenerating | `flora-video-resize` |
| A finished ad creative | Out-of-home placements, social resizes, annotated PDF | `flora-mockup-deck` |
| A product photo (+ optional model frame) | Studio plates, on-model views, PDP deck | `flora-pdp-deck` |
| A product launch | Generate → archive → host → paused Meta ads | `flora-brand-ad-pipeline` |
| A set of generated assets | Checked against brand rules before shipping | `flora-brand-consistency-audit` |
| A theme, season, or category | A visual research board of directions | `flora-trend-board` |
| An existing project or canvas | Revise what's there rather than start over | `flora-canvas-iterate` |

★ = flagship, most heavily tested.

## Two laws that apply everywhere

1. **N items is one wait, not N waits.** FLORA runs generations concurrently; serialisation is on the agent's side. Six items fired together: 15.8 s. The same six sequentially: ~150 s. Identical credits.
2. **A re-run with an unchanged prompt is not a refinement.** Name the defect, change the prompt, or stop.

## How to call FLORA

- **Named tools** (`flora_generate`, `flora_run_technique`, `flora_list_models`, …) — one call per action. Best for single-shot work.
- **`execute`** — TypeScript against a pre-authenticated SDK client. Best for batches, because a whole fan-out fits in one call. Limits: ~5 min per call, 30 s per HTTP request, no state between calls.

Not present and easy to reach for: `models.retrieve` (use `models.list().find()`) and `runs.action` (use the `flora_run_action` tool).

## What this skill does not do

It does not generate anything. Once routed, load the specific skill and follow it — that file holds the model choices, cost numbers, and failure modes this one deliberately omits.
