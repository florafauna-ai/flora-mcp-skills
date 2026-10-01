# A complete cut extracted from a rendered edit

Start with [rendered-cut-document.json](rendered-cut-document.json), the public
`document` shape `flora_add_to_canvas` accepts. [rendered-cut-recipe.json](rendered-cut-recipe.json)
is the same cut in the editor's internal camelCase recipe, kept to explain field
meanings; the API does not accept it.

The source was the first picture item of the successfully rendered V4 landscape
basketball edit. This excerpt retains its exact timing, geometry, opacity,
crop/rotation/fade/audio settings, fps and composition dimensions. It removes
other cuts, separate audio, the logo and closing card, renames identifiers and
the filename, and replaces the source URL with an explicit placeholder. The
source edit rendered; this shortened, redacted excerpt has not itself been
rendered. Do not present it as a new verified output.

## Submit the right envelope

Read the JSON file rather than reconstructing it from a field list. Replace
`https://media.example.com/source.mp4` with a durable HTTPS video URL available
to the renderer. Set the source asset's dimensions, duration and audio flag to
the actual media metadata. The archived source was 1280 × 720, 14.041667 seconds,
with audio; those values are not a requirement on your footage.

For the public path, call `flora_add_to_canvas` with this structure (the named
variables below stand for actual JSON objects/strings, not literal placeholders):

```js
{
  workspace_id: workspaceId,
  project_id: projectId,
  add: [{ ref: "edit", type: "timeline", document: workedDocument }],
  skill: "flora-video-editor",
  skill_run_id: skillRunId
}
```

There is no prompt, model, aspect-ratio or resolution parameter on a Timeline. Composition size is inside
the document. Retrieve the assigned node's document when that tool is
available; confirm it contains the intended cut before spending on a render.

## What makes this an edit rather than an accepted blob

| Part            | Values in the worked cut                                              | Why it matters                                                                                                                                                                                                                              |
| --------------- | --------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Composition     | 24 fps, 1280 × 720                                                    | Gives frame timing and the coordinate system. Use supported positive fps and even composition dimensions within the workspace limits. 24 and landscape are creative choices.                                                                |
| Placement       | top −60, left −70, width 1433.6000000000001, height 806.4000000000001 | The item is enlarged and shifted within the composition. Negative coordinates and fractional dimensions are legitimate; this is a deliberate crop, not malformed data. These four numbers are placement, not the media's native dimensions. |
| Timeline timing | `from: 0`, 46 frames                                                  | The clip starts at the edit's first frame and lasts 46/24 seconds. Positive duration and track membership make it visible. The number 46 is the chosen cut, not a schema constant.                                                          |
| Source trim     | 0.08333333333333333 seconds                                           | At the composition's 24 fps, this offset maps to two trim frames. It does not establish the source file's native fps. Timeline position and source offset use different units.                                                              |
| Playback        | rate 1; gain 0 dB                                                     | The renderer reads rate/volume settings. Preserve complete numeric values on raw recipes; change them deliberately for speed or sound.                                                                                                      |
| Appearance      | opacity 1; crop sides 0; radius/rotation 0; visual/audio fades 0      | Retain the source's concrete settings. Opacity and fades are read directly; crop sides have zero defaults in the crop helper. Not every archived zero is a universally required field.                                                      |
| References      | track → `clip` → `source` → media URL                                 | The track lists an existing item, the item names an existing asset, and the asset resolves media. A canvas edge or a filename cannot replace these references.                                                                              |
| Track state     | hidden false, muted true                                              | Picture is visible and its embedded sound is muted, as in the source edit's picture track. That source used a separate soundtrack, which this excerpt omits; expect a silent cut unless you change the audio design.                        |

**The storage schema accepts recipes the renderer cannot render, and failure
arrives late.** Raw recipe validation checks geometry/timing fields only when
present. The video renderer performs crop/size arithmetic and computes fades
and volume from the item; missing numbers can produce invalid calculations or
an invisible layer. The editor's own item constructor supplies these values,
which is why an editor-created item can work while a hand-built minimal recipe
passes validation and fails later.

The public document converter narrows this gap: it validates references and
item kinds, supplies numeric appearance defaults, and either accepts all four
geometry fields or generates all four. Supply them explicitly when reproducing
a crop like this example. That conversion does not prove the media is reachable,
decodable or visually correct. Do not treat every field in an archived recipe
as a required public API field.

The raw example retains `deletedAssets: []` as the recipe container's normal
shape and both `mediaUrl`/`remoteUrl` for the media path. Public assets have one
`media_url`; the converter supplies the internal representation. The archive's
`isDraggingInTimeline` is transient state removed by recipe sanitization, not a
render requirement. `remoteFileKey`, file byte size and the ad-specific filename
are upload/display bookkeeping, not geometry. They are not the cure for a
missing item rectangle and were omitted or renamed here. `keepAspectRatio`
records editing behavior; it does not compute a missing rectangle for a raw item.

## What the prior/final pair actually teaches

The archived V4 prior and final recipes use the same assets and the same
composition/fps for each orientation. Both already contain complete geometry.
The final edit splits/re-times picture and audio segments: a 78-frame segment
becomes 62 plus 15 frames, with the second portion starting at 2.625 seconds;
another 140-frame segment becomes 46 plus 93 frames with a new source offset.
The closing card moves from frame 336 to 334 and grows from 24 to 26 frames,
keeping the whole composition at 360 frames (15 seconds at 24 fps).

These differences demonstrate precise editing, not a missing-field fix that
made rendering possible. Do not infer a render failure or cure from filenames
containing “prior.” When splitting a cut, update track membership, timeline
positions/durations and source trims together; align the separate audio cuts
too. A legal schema can still describe the wrong cut or an audible jump.

Portrait uses 1080 × 1920 and different item rectangles; it is not just a changed
composition header. One portrait close-up is 2560 × 1440 at left −740/top 240.
Those are framing choices for that footage, not a formula for every portrait
edit. For your own sources, choose the fit/crop explicitly and inspect the output.

The renderer draws tracks in reverse array order, so the first track is visually
on top (the source's logo track precedes its picture track). Preserve actual
stacking when copying cuts; do not reverse it based on a generic schema gloss.
