---
name: flora-run-technique
description: Run a saved FLORA technique — a multi-step visual workflow such as background swap, relighting, upscale, model swap, or sketch-to-render. Use when the user names a technique, asks to transform an image they already have ("put this on a clean background", "match this lighting", "upscale this", "make this look photographed"), or asks what FLORA can do. Do not use for a plain text-to-image request with no source image, and do not use to inspect existing project work.
---

# Run a FLORA technique

Hosted MCP generation inputs are plural: call `flora_create_generations` with `{ "generations": [{ "workspace_id": "ws_…", "project_id": "prj_…", "type": "image", "prompt": "…" }] }` (1–20 items). Put per-generation fields, including optional `model`, `params`, and `reference_node_ids`, inside each item. Read `generations[]` in the response; retain successful entries' `run_id` and handle failures individually. Poll `flora_list_generations` with `{ "run_ids": ["run_…"] }`, even for one run; add `technique_id` for technique runs. Never retry successful items because another item failed.

Use dedicated tools for this workflow, including batches. `execute` is deprecated; use it only for an SDK operation without a dedicated tool. SDK examples below describe orchestration: use the corresponding dedicated tools, issue independent calls concurrently, retain every run id, and poll in later calls. Do not choose `execute` just to combine calls.

A technique is a saved workflow that chains several models. It is the thing FLORA
does that a single image model cannot: the steps, prompts, and model choices are
fixed by whoever authored it, so the same technique gives the same treatment every
time.

**Input:** the user's intent, plus any source image.
**Output:** the technique's output URLs, the charged cost, and the project the run
landed in.

## Steps

1. **Resolve the workspace.** If the connection already names the user's current
   workspace, use it. Otherwise call `flora_list_workspaces`; if there is more
   than one, ask which to bill before spending anything.

2. **Find the technique.** Call `flora_list_techniques` and match on the user's
   intent. It returns `run_cost` and a summary of inputs for each. If nothing fits,
   say so and offer `flora_create_generations` instead — do not force an unrelated technique.

3. **Get the exact input ids.** Call `flora_get_technique`. Its declared input ids
   are the keys `flora_run_technique` expects. Never guess them from the name.

4. **Get each image input to an HTTPS URL** (see Image inputs below).

5. **Run it.** Call `flora_run_technique` with `workspace_id`, `technique_id`, and
   an `inputs` object keyed by those ids. Omit optional text inputs entirely when
   the user gave no direction — an empty string is rejected, not treated as absent.

6. **Poll and report.** Poll `flora_list_generations` until status is `completed` or
   `failed`. Report the output URL, the charged cost, and a link to the project.

## Image inputs

FLORA fetches images server-side from an HTTPS URL. **Files the user attaches in
ChatGPT already have one** — they are hosted on `files.openai.com` or
`cdn.openai.com`, both allowlisted. Pass that URL straight to
`flora_create_asset` as `source`, or into the technique input directly.

Never base64-encode a file or try to upload bytes. If the image genuinely has no
URL, say that this environment cannot upload it and point the user at their FLORA
project to add it there.

## Rules

- **State the cost before running.** `run_cost` comes back from
  `flora_list_techniques`. Techniques range from free to several dollars per run.
- **You cannot see the output.** Runs return URLs, not pixels. Describe what was
  produced from the technique and the inputs; never claim to have looked at it.
- **On `input_validation_error`,** re-read `flora_get_technique`, rebuild `inputs`
  from what it returns, and retry once. Do not retry other failures — retries bill.
- **On insufficient credits,** surface the message and stop.
