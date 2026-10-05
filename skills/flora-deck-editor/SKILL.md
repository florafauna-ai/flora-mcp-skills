---
name: flora-deck-editor
description: >
  Read, create, and edit native editable Deck nodes in FLORA through hosted MCP.
  Use for decks, slides, presentations, and edits to an existing slide's text,
  layout, styling, or source bindings. Authors saved slide documents; it does not
  generate campaign/PDP assets or provide headless presentation rendering or PDF
  export. Use flora-mockup-deck or flora-pdp-deck for those asset sets and their
  separate HTML/PDF delivery workflows.
---

# flora-deck-editor

> **Attribution.** Pass `skill: "flora-deck-editor"` on every FLORA call you
> make while running this skill, along with one invented
> `skill_run_id` reused for this run. Both fields are reporting only.

The saved Deck document owns the slides. A canvas label, graph edge, image of a
slide, or PDF is not that editable document.

## Check capability and resolve the project

Check the current tool catalog for `flora_add_to_canvas` accepting `add`
entries with `type: "deck"` and a `document`, for
`flora_get_canvas_node_document`, and for `flora_update_canvas_node_document`,
the whole-document write under `base_revision`. If the update tool is absent,
report that this deployment cannot edit Deck documents rather than
falling back to code. Do not request credentials.

These instructions require the hosted document tools. WebMCP's Deck commands
are a different surface; do not assume they accept this full-document contract.
If required capabilities are absent, report the limitation. Do not create an
Image node with a Deck-looking name or silently substitute a PDF.

Resolve the actual workspace and project with `flora_list_workspaces` and
`flora_list_projects` as needed. Keep the project the user named; create one
with `flora_create_project` only when new project work is requested. Read
`flora_get_canvas({workspace_id, project_id})` for structure. Use
`flora_list_canvas_nodes({project_id})`, following pagination, to identify media
and their asset URLs. Graph labels are not slide bodies or proof that a source
has produced usable content.

## Create or revise the saved document

For a new Deck, send only the new node to `flora_add_to_canvas` with
`workspace_id`, `project_id` and
`add: [{ "ref": "deck", "type": "deck", "label": "Launch", "document": {...} }]`.
A Deck label is its title. Do not add generation parameters such as prompt,
model, or params. Omitting `document` creates a blank Deck; it does not
assemble slides from labels. Use the node ID the `created` map returns for
subsequent calls, not your `deck` ref. Check warnings.

For an existing Deck, first call
`flora_get_canvas_node_document({workspace_id, project_id, node_id})`.
Keep the returned `document` and `revision`. Modify only the requested content
in a copy of the complete document. Preserve unrelated slides and layers,
their stable IDs, order, hidden/visible states, guides, source bindings,
transforms, and styling. A graph or document summary is insufficient to rebuild
an existing Deck. A read-only request ends after inspection; it needs no write.

Send the whole modified document to
`flora_update_canvas_node_document({workspace_id, project_id, node_id, document, base_revision})`
with the observed revision as `base_revision`. Keep initial inspection and
post-write readback on `flora_get_canvas_node_document`.

For example, to edit one inline title:

1. `flora_get_canvas_node_document` returns the document and its `revision`.
   Re-read it if the revision no longer matches what you inspected.
2. In your copy, find the slide by `slides[].id`, then the layer under
   `slides[].document.layers` (a `content_type: "text"` layer whose content is
   `kind: "inline"` carries editable `text`).
3. `flora_update_canvas_node_document` applies the whole edited document back
   under `base_revision` set to the revision you read.

Nothing persists between calls — carry the inspected revision forward
explicitly rather than assuming an earlier read is still current.
On a changed revision or `revision_conflict`, reread and reconcile with the newest
document. Never retry the stale body without its revision. If concurrent edits
keep conflicting, report the conflict and retain the intended change for a
later retry. Observed revision checks do not serialize simultaneous
collaborators. An unchanged document need not advance the revision.

## Geometry is part of the content

The public document uses snake_case, `kind: "deck"`, and `schema_version: 1`.
It contains 1–200 slides, each with a 1920 × 1080 frame, up to 256 layers, and
a total document limit of 4 MiB of UTF-8 JSON. Each layer map key must match its
`id`, and `layer_order` must list each layer exactly once in paint order
(later layers appear on top). Slide IDs must be unique. Keep existing IDs;
assign new IDs when creating additional slides or layers.

`transform.position` is in pixels. **`transform.scale` contains dimensionless
multipliers, never pixel dimensions.** Divide the desired box width and height
by the layer's reference width and height:

- Text: reference width = `frame.pixel_width`; reference height =
  `round(font_size * 7.5)`. Default `font_size` is 144. Text lives in `content`;
  typography lives in `text_data`. Changing font size changes the reference
  height, so recalculate scale to keep a chosen pixel box.
- Shapes: reference size is 512 × 512.
- Media: the editor normalizes the source aspect ratio to a 1024-pixel longest
  edge (round the shorter edge to at least 1 pixel). Resolved asset dimensions
  take precedence; `source_dimensions` supplies an aspect-ratio fallback.
  Do not divide by the original file's pixel dimensions. Preserve existing
  transforms when retaining an existing media layout.

This complete one-slide document makes a 1200 × 240 text box at (100, 100):
`1200 / 1920 = 0.625` and `240 / round(96 * 7.5) = 1/3`.
Pass it as the new node's `document`:

```json
{
  "kind": "deck",
  "schema_version": 1,
  "slides": [
    {
      "id": "slide_1",
      "hidden": false,
      "guides": { "vertical": [], "horizontal": [] },
      "document": {
        "schema_version": 1,
        "frame": { "pixel_width": 1920, "pixel_height": 1080, "fill": "#ffffff" },
        "layer_order": ["title"],
        "layers": {
          "title": {
            "id": "title",
            "name": "Title",
            "visible": true,
            "content_type": "text",
            "content": { "kind": "inline", "text": "Hello Deck" },
            "text_data": { "font_family": "Inter", "font_size": 96, "text_color": "#000000" },
            "transform": {
              "position": { "x": 100, "y": 100 },
              "scale": { "x": 0.625, "y": 0.3333333333333333 },
              "rotation": 0,
              "opacity": 1
            }
          }
        }
      }
    }
  ]
}
```

The box's right edge is 1300 and bottom edge is 340, within 1920 × 1080.
The example is schema-checked and resolved through the slide renderer's geometry
code. That establishes its pixel box, not visual quality or text fit in every font.

## Layer fields the example does not show

The example is one inline-text layer, so it demonstrates the arithmetic rather
than the vocabulary. Unknown fields reject server-side by JSON pointer, so use
these names rather than guessing; a rejected write is not a reason to create a
second Deck.

Every layer carries `id`, `name`, `visible`, and `transform`, plus optional
`locked`, `blend_mode` (`normal`, `multiply`, `screen`, `overlay`, `soft-light`
and the other Photoshop-style modes), `fill`, and `adjustments`. `transform`
takes optional `rotation` and `opacity` (0–1) alongside `position` and `scale`.

- **Text** (`content_type: "text"`): typography lives in `text_data` —
  `font_family`, `font_size`, `text_color`, `font_weight` (1–1000),
  `font_style` (`normal`/`italic`), `text_align` (`left`/`center`/`right`),
  `text_vertical_align` (`top`/`middle`/`bottom`), `line_height`,
  `letter_spacing`, `auto_width`.
  **`letter_spacing` is an em fraction, not pixels**: the renderer multiplies it
  by the font size, so `0.18` is wide display tracking and `5` is five ems per
  character, which shreds the line. Useful values sit between −0.05 and 0.2.
  `line_height` is a unitless multiplier; omitting it falls back to CSS
  `normal`, which varies by font, so set it whenever a box is sized to fit an
  exact number of lines.
- **Shape** (`content_type: "shape"`): `primitive` (`square`, `circle`,
  `triangle`) and `shape_color` are both required; `corner_radius` is optional.
  A square at low `transform.opacity` is how a scrim behind text is built.
- **Media** (`content_type: "image"`): `fit` is `contain`, `cover`, or
  `stretch`. Full-bleed artwork wants `cover`, which crops to the layer box
  rather than letterboxing inside it.

## Keep source bindings intentional

Inline text uses `content: {kind: "inline", text: "..."}`. Live text uses
`content: {kind: "node_output", node_id: "...", output_key?: "..."}`.
Do not detach live text into inline text unless that is the requested change.

Media layers use `content_type: "image"` and either
`source: {kind: "node_output", node_id: "...", output_key?: "..."}` or
`source: {kind: "asset", asset_id: "asset_..."}`. They can carry `video` or
`model3d` settings; 3D requires a node-output source. Use the current API schema
for advanced fields. A media URL is not an asset ID: import missing media with
`flora_create_asset`, then use the returned asset or canvas node ID.

Source node references can name an existing node in this project or a node
declared in the same request. Readback resolves them to UUIDs; preserve those
UUIDs and any `output_key`. Confirm the referenced output actually exists and
has the expected media type. A bare canvas edge does not author slide content.
Do not regenerate missing assets as part of a layout edit; route requested
asset generation to the appropriate skill and return to this one for assembly.

## Read back, check bounds, and report

Read the persisted document with `flora_get_canvas_node_document` after each
write. Confirm the requested text, slide count/order, stable IDs, source
bindings, and unrelated content. Check schema errors by their field paths;
do not repeatedly create new Decks to repair one failed edit.

For each changed box, calculate `width = abs(scale.x) * referenceWidth` and
`height = abs(scale.y) * referenceHeight`. Require finite, positive sizes.
For unrotated content intended to stay inside the slide, check `x >= 0`,
`y >= 0`, `x + width <= 1920`, and `y + height <= 1080`. For rotated layers,
check the rotated bounds; preserve deliberate cropping or off-slide placement.
Also check visibility, opacity, text wrapping, and overlap where relevant.
Text-content checks alone cannot catch a box scaled to millions of pixels.

A text layer's box clips what it holds: the glyphs render at `font_size` and
wrap to the box width, and whatever passes the box height is cut off. Scaling a
text layer changes that box, never the type size. So check each text box against
its own content too — `height / (line_height * font_size)` is the number of
lines it can show — and remember that neither tracking nor leading appears in
the bounds arithmetic above. A layer can pass every bounds check with its text
clipped away.

Return the actual project link, Deck node ID, and what changed. Distinguish
saved/read-back content, numeric bounds checks, and any visual inspection.
Persistence and valid bounds do not prove fonts, wrapping, source loading,
cropping, or overall appearance; state when those remain unverified.

This capability authors documents. It provides no native headless presentation
render or PDF export operation. Do not run a Deck as a generation to obtain a
PDF. For PDP/campaign PDF delivery, keep the explicit workflow in
`flora-pdp-deck` or `flora-mockup-deck` and report each deliverable separately.
