---
name: flora-video-resize
description: Generatively resize/reframe an input video into multiple aspect ratios (9:16, 16:9, 4:5, 1:1, etc.) using FLORA's video-to-video models, preserving the source's look, feel, subject, grade, and timing. Use whenever the user wants a video in different ARs, formats, or placements — "make a 9:16 from this ad", "resize this video for Reels/TikTok/YouTube", "different aspect ratios from this 1:1", "reframe without cropping", "outpaint this video". Also trigger on "video resize" in any FLORA/demo context.
---

# FLORA Generative Video Resize

Turn ONE source video into every target aspect ratio, generatively — no black bars, no crop — while keeping the original's subject, wardrobe, motion, lighting, grade, on-screen text, and timing.

## Trigger

User supplies a video (upload or URL) and wants it in other aspect ratios/formats. Ask (or infer) target ARs — default set: 9:16, 16:9, 4:5.

## Critical API fact (the #1 failure mode)

`flora_generate` **silently ignores** any attempt to pass a source video via `params` (e.g. `video_url`) or an `inputs` array — it will happily run text-to-video from your prompt and burn credits producing an unrelated clip. A v2v model ONLY receives the source through a **canvas edge**. Never call `flora_generate` for v2v without a wired `node_id`.

## Steps

1. **Probe the source.** `ffprobe` → width/height/AR, duration, audio stream. Extract 2–3 frames (`ffmpeg -ss N -vframes 1`) and LOOK at them: note subject (identity, wardrobe, pose), scene, motion, camera move, color grade, and every piece of on-screen text/logo verbatim. These feed the prompt.
2. **Upload to FLORA.** `flora_create_asset` (URL fetch if the file has a URL; otherwise `source="signed-url"` → POST bytes from shell → `flora_complete_asset`). Create/choose a project; `flora_attach_asset` puts the asset on the canvas and returns its node id.
3. **Pick the model** (all take the source via canvas edge; AR is a native output param):
   - **Seedance 2.5** (`v2v-seedance-2-5`) — DEFAULT. ARs: 16:9, 9:16, 4:3, 3:4, 1:1, 21:9; duration up to 30s (match the source!); 480p–1080p; keeps/regenerates audio. Verified: preserves grade, wardrobe, scene, and re-typesets brand text cleanly. Actual cost ≈ 1.2 credits/sec at 1080p (the catalog's "estimated_credits: 0" for gateway models is WRONG — quote ~14 credits for a 12s 1080p run before firing).
   - **Kling O3 Pro Edit** (`v2v-kling-o3-edit`) — quality alternative, ARs 16:9/1:1/9:16 only, ~933 est. credits.
   - **WAN 2.6 v2v** (`v2v-wan-2.6`) — has 3:4/4:3, but duration caps at 10s.
   - **Gemini Omni 1.1 Flash v2v** — 16:9/9:16 only, up to 4K.
   - **4:5 is native nowhere**: generate 3:4 (WAN) or 9:16 (Seedance), then the FREE `change-video-ar` action to center-crop the small delta.
4. **Wire the graph.** `flora_add_to_canvas` — node type comes from the label suffix, exactly `id["Label (Video)"]`; use `graph LR`, reference the asset node by bare id:
   ```
   graph LR
     <assetNodeId> --> r1["Reframe 9x16 (Video)"]
   ```
   with `node_params: {"r1": {"model": "v2v-seedance-2-5", "prompt": <prompt>, "model_parameters": {"aspect_ratio": "9:16", "resolution": "1080p", "duration": "<source seconds>"}}}`. One node per target AR — add them all in one call, all edges from the same asset node.
5. **Run each node.** The MCP `flora_generate` tool has no `node_id` field, so use `execute`:
   ```ts
   client.generations.create({ workspace_id, project_id, node_id: "r1", type: "video", model: "v2v-seedance-2-5", prompt, params: { aspect_ratio: "9:16", resolution: "1080p", duration: "12" } })
   ```
   Fire all ARs concurrently; poll with `flora_get_run` (~3–5 min each).
6. **Prompt recipe** (fill from step 1; one prompt per AR):
   - Open with the transform: "Reframe this video from {source AR} to {target AR} {vertical/landscape}."
   - Pin what must not change: "Keep the original composition, subject ({specific description: identity, wardrobe, prop}), camera position, {specific camera move}, lighting, color grade, and timing exactly as in the source."
   - Direct the new pixels: "The original frame spans the full {width for vertical / height for horizontal} of the new frame; generate new content only in the revealed {top and bottom / left and right} margins, seamlessly continuing {specific scene elements}." (Without "spans the full width", Seedance may shrink the source into an inset window and build a reveal around it — sometimes a great effect, but not a reframe.)
   - Lock the type: "Preserve all on-screen text and logos exactly, glyph for glyph: {list each string verbatim}." Small prop text (SIM cards, labels) still drifts — flag it in QC.
   - Close with negatives: "Do not zoom, crop, restyle, re-time, or alter the subject."
7. **Post-process.** Download outputs; if an output is silent but the source had audio and durations match (±0.5s), remux the source audio: `ffmpeg -i out.mp4 -i src.mp4 -map 0:v -map 1:a -c copy final.mp4`. Derive 4:5 from the nearest native AR with the free `change-video-ar` action.

## Verification

For EVERY output before delivering: `ffprobe` confirms target AR, duration ≈ source, audio present. Extract frames at 3 timestamps and compare against the source frames: subject identity and wardrobe intact, grade matched, every text string legible and correctly spelled, no letterboxing, no inset-window layout (unless requested). One failed check → one retry with the prompt tightened on the failing aspect (or fallback model); still failing → deliver best output with the defect named honestly. Report actual `charged_cost` per run and the FLORA project link.
