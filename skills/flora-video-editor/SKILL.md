---
name: flora-video-editor
description: >
  Assemble and edit existing media in FLORA's Timeline video editor through MCP:
  author or revise the saved timeline, render it, and put the finished video on
  the canvas. Use for cutting clips together, arranging tracks, adding titles or
  audio, and revising an existing edit. Do not use for generating new footage
  from a prompt or script, resizing a single video, or rendering a motion scene
  outside the Timeline editor.
---

# flora-video-editor

> **Attribution.** Pass `skill: "flora-video-editor"` on every FLORA call you
> make while running this skill, along with a `skill_run_id`
> you invent once when the run starts and reuse for the rest of it. Both are
> reporting only: they change nothing about the call or its result.

The saved timeline is the edit. Canvas edges, a node label, and the rendered
video are different things: changing one does not necessarily change the others.
Work toward a saved, readable composition first, then render that composition
and retain the resulting media independently of the Timeline node.

This skill uses the hosted MCP's Timeline document capability. Check the current
tool catalog before writing: look for the `timeline` type and `document` field on
`flora_add_to_canvas` add entries, and for `flora_get_canvas_node_document`.
If `timeline` is unsupported, stop and explain the deployment limitation; do not
create an Image node with a Timeline-looking name.

Use dedicated tools for every step here. Do not substitute a generative video
model for the user's requested edit. Generate missing footage separately with
`flora-script-to-video`; use `flora-video-resize` for a single-video resize and
`flora-motion-compositor` for its separate motion-scene workflow.

## Build an edit that can be read back

Identify the actual workspace and project. Read graph structure with
`flora_get_canvas`, then use `flora_list_canvas_nodes({project_id})` to obtain
existing media nodes and their asset URLs; follow pagination for more sources.
The graph alone does not contain those URLs, and idle generation nodes have no
media to list. Decide the composition dimensions, fps, cut points,
track order, titles and audio from the user's brief. Retain durable media URLs
and their real dimensions/durations; a canvas node ID is not a media URL.

For an existing Timeline on a deployment with document readback, read its full body with
`flora_get_canvas_node_document({workspace_id, project_id, node_id})` before
editing. Preserve unrelated items, tracks and assets. The returned `revision`
belongs to this saved document, not to the canvas graph fingerprint. Submit the
whole modified document through a canvas changeset update with that revision as
`base_revision`; on `revision_conflict`, read again and reconcile the user's edit
instead of overwriting newer work. Write with `flora_update_canvas_node_document`
(node_id, the whole document, base_revision).

On a legacy deployment without document readback, do not replace an existing
edit unless you have its complete saved recipe from the user. Never reconstruct
that content from a canvas read.

For a new node, call `flora_add_to_canvas` with
`add: [{ref: "edit", type: "timeline", label?: ..., document: ...}]`. A timeline
add rejects `prompt`, `model`, `params` and `content_url`. Use the assigned id
from the returned `created` map for later reads/runs, not the temporary `edit`
ref you chose.

Timeline nodes reject generative configuration: prompt, model, aspect ratio,
resolution, model parameters and direct `content_url`. Their content is the
saved draft. Incoming media edges can seed the editor when someone opens it;
they do not supply clips to a headless render. Write the clips into the document.

## Geometry is part of the content

The public document uses snake_case and a versioned wrapper:
`{kind: "timeline", schema_version: 1, fps, composition_width,
composition_height, tracks, items, assets}`. Tracks list item IDs; `items` and
`assets` are records keyed by their IDs. Each item's `id` must match its key,
each track reference must exist, and media items' `asset_id` must name an asset
of a supported type (an audio item can also use a video asset's soundtrack).
`from` and `duration_in_frames` use frames; source offsets
such as `video_start_from_in_seconds` use seconds. Duration is explicit, not
inferred from the media file. The renderer paints tracks in reverse array order:
the first track is visually on top. Preserve that order when adding overlays.

**A document accepted for storage is not proof it can render.** The API takes
only the public `document`; the editor's internal camelCase recipe in the
reference folder is there to read field meanings, never to send. Do not invent a
minimal document: editor items carry concrete `top`, `left`, `width`, `height`,
opacity and type-specific crop, rotation, typography and audio settings. Missing
render fields can survive validation and fail later.

On the public document path, either supply all four geometry fields
(`top`, `left`, `width`, `height`) or omit all four. Partial geometry is rejected.
Omitting them lets the server fit and center media using its dimensions and
seed editor defaults; text and captions have their own default placement. Set
all four when a deliberate crop, overlay or title placement matters. Read back
the normalized document to inspect the actual geometry before rendering.

Before composing your first document, read [the worked cut](reference/worked-cut.md)
and its complete [public document](reference/rendered-cut-document.json). It is
extracted from a successfully rendered edit, with real item geometry and every
video-layer setting retained. The reference also supplies the corresponding
[internal recipe](reference/rendered-cut-recipe.json) and explains the fields
that storage validation allows you to omit but the renderer consumes. Replace
the explicit media placeholder with your own source and its metadata; the
example is not a fetchable sample video or a request to run a paid test.

Use the public document when available. A successful save/readback proves
persistence and normalization; only examining the rendered video proves the
intended cut. Hold render spend while resolving a schema error, rather than
probing field combinations by repeatedly rendering.

## Render, then keep polling the same run

Run the saved node with `flora_run_canvas_nodes`. Save every started `run_id`
and its `poll_url` before doing anything else. A skipped node did not start a
render: `timeline_no_document` means save a document first;
`timeline_not_entitled` means the workspace cannot use this capability. Read the
message as well as the reason. Older deployments may use the broader
`video_editor_run_not_supported`; do not retry a capability refusal as though
it were a transient renderer failure.

Poll the exact started run through its `poll_url` (`GET /runs/{runId}`).
The hosted tool `flora_list_generations({run_ids: [run_id]})` polls the exact
started run. Omit `technique_id` for Timeline runs. Calling the tool without
`run_ids` lists generation history instead and does not poll the render.
Polling advances detached jobs through upload and finalization; it
is not just a progress read. A background finalizer also exists, but do not
rely on it to replace tracking your run. Keep polling in later calls with a
reasonable wait until a terminal status. Do not hold a single call open in
a long polling loop, and do not start another render because one is still running.

Require `status: "completed"` and a video output before reporting success.
Preserve full URLs, including query strings, and output asset IDs when present.
If a run fails, inspect its message, correct the saved content when appropriate,
and decide whether a new billable render is warranted. If observation must stop,
hand back the run ID and pending status so work can resume without duplicating it.

## Account for the render and deliver visible media

Timeline renders use the video editor's own render usage/reservation path, not
the generation-model credit estimate. Started run responses deliberately omit
model/cost estimates; absent costs do not mean free. Generation-history version
rows for Timeline renders also lack render cost fields. Use the workspace's
video-editor usage/billing information for render spend, and say when that data
is unavailable. Generation history can establish the separate costs of footage
generated upstream; it cannot substitute for Timeline render accounting.

Retain the completed run's video URL even if the canvas definition has no new
output. A headless finalizer stores an asset/version; do not assume it updated
the canvas node's live output state or made downstream edges usable. A Timeline
can be recognized as a video-output node, but a connection alone does not prove
the rendered media is available to a downstream model.

For reliable standalone playback on the board, use `flora_attach_asset` with
the completed output's asset ID and project ID. If only a URL is available,
`flora_add_to_canvas` can import it with an add entry
`{ref, type: "video", content_url}` (plus `workspace_id` and `project_id`),
creating a static playback node; a content_url add takes no prompt or model.
Read the canvas afterward and return the actual project link, playback node ID
and finished video URL. Do not claim a Timeline edit is visibly delivered just
because the render API returned success.
