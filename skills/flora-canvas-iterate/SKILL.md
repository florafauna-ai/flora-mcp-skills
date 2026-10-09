---
name: flora-canvas-iterate
description: Find and build on work that already exists in a FLORA project — inspect a canvas, review generation costs, regenerate specific assets, or route existing Deck and slide edits to flora-deck-editor. Use when the user refers to a named project, "my canvas", or earlier work ("the hero images from last week", "edit slide two"). Do not use to start new work in an empty project.
---

# Iterate on existing FLORA work

Hosted MCP generation inputs are plural: call `flora_create_generations` with `{ "generations": [{ "workspace_id": "ws_…", "project_id": "prj_…", "type": "image", "prompt": "…" }] }` (1–20 items). Put per-generation fields, including optional `model`, `params`, and `reference_node_ids`, inside each item. Read `generations[]` in the response; retain successful entries' `run_id` and handle failures individually. Poll `flora_list_generations` with `{ "run_ids": ["run_…"] }`, even for one run; add `technique_id` for technique runs. Never retry successful items because another item failed.

Use dedicated tools for this workflow, including batches. SDK examples below describe orchestration: use the corresponding dedicated tools, issue independent calls concurrently, retain every run id, and poll in later calls.

A FLORA project outlives the conversation. Its canvas, every generation, and the
cost of each are all still there, so revision starts from what exists rather than
from a blank prompt.

**Input:** a project reference and the change wanted.
**Output:** what is on the canvas today, plus requested asset or Deck changes.

## Steps

1. **Find the project.** `flora_list_projects` (most recently active first) and
   match on the user's wording. Never create a project when the user named an
   existing one — ask if the name is ambiguous.

2. **Read what is there.** `flora_get_canvas` for structure and how nodes connect;
   `flora_list_canvas_nodes` for the media nodes and their asset URLs. Use
   `flora_list_generations` to see what was made, with cost and status.

3. **Identify the assets or Deck the user means.** Name them back before changing anything.
   "Two hero images, both generated Tuesday" is confirmable; "the ones you meant"
   is not.

4. **Apply the change.** For existing Deck text, layout, styling, or source-binding
   edits, load `flora-deck-editor` with `flora_discover_skills` and follow its
   capability checks and read/modify/write workflow. Keep the existing Deck;
   a slide edit does not require regenerating its assets.
   For asset regeneration, use `flora_create_generations`, or re-run the original
   technique with `flora_run_technique` when the asset came from one —
   `flora_list_technique_runs` shows which technique produced what.

5. **Report** the changed Deck or new outputs, any generation cost, where they
   landed, and what was verified.

## Rules

- **Read before writing.** The user may have edited the canvas between turns.
- **Asset regeneration is additive.** Regenerating adds new nodes; it does not replace the
  originals. Say so, so the user knows the earlier version is still there.
  Requested Deck edits update the existing document through `flora-deck-editor`.
- **Confirm before spending.** State the cost of the regeneration and wait.
- **You cannot see any asset.** You have URLs, node labels, and generation
  metadata. Reason from those; never claim to have looked at the artwork.
- Prefer the narrowest read that answers the question. A whole-canvas dump on a
  large project is mostly noise.
