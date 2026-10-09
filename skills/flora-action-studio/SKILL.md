---
name: flora-action-studio
description: >
  Open FLORA's live action studio: run a prebuilt action, a workspace's own
  custom action, or a technique (custom action flow) so the result shows inline
  with the action's declared parameters as live controls the user adjusts
  themselves. Use when the user wants to tweak, tune or iterate on a transform
  rather than describe it — "let me adjust the colour grade", "give me sliders
  for this", "I want to play with the settings", "quantize this logo to a few
  colours and let me pick how many", "run my custom action on this", "turn my
  own code into an action I can tune" — or names an action or technique and
  wants to see and refine its output. Also use when the user wants to create,
  write or fix their own action ("can we create our own action", "make me a
  pixelate action", "turn this into an action", "my action failed, fix it")
  and when they name a transform to apply ("color grade it", "pixelate this",
  "quantize the logo"). Do not use for a plain generation with no source media
  (flora_create_generations), to inspect existing work (flora-canvas-iterate),
  or when the user wants one fixed result with no adjustment.
---

# FLORA action studio

Use dedicated tools for this workflow. Issue independent calls concurrently and retain every run
id. Polling belongs to the studio once it is open; only a host without MCP Apps (no studio)
needs `flora_list_generations` from you.

Actions are deterministic transforms (crop, colour grade, resize, overlay, a user's own
code) that spend no credits; techniques are saved multi-step workflows that bill `run_cost`
per run. In MCP Apps hosts, `flora_run_action`, `flora_run_canvas_action` and
`flora_run_technique` open the **action studio**: the action's declared parameters become
controls, and **nothing runs until the user clicks Apply**, which runs it once with the
settings on screen. A browser-runtime action that exports a `preview` (most prebuilt
`*-browser` actions, and a custom JavaScript ES module that exports one) previews **live in
the user's browser** while they edit, exactly as on the canvas; other runtimes (Python,
node) show the input or the last result until Apply. Techniques show their cost on the
Apply button. The studio waits for each run itself. You never see pixels; the user does.
Your job is to open the studio on the right action with sensible values, then continue
from what the studio hands back.

**Input:** source media (an HTTPS URL, a canvas node, or an attached file) and what the user
wants to adjust.
**Output:** a studio open on the inputs, then the run the user applied: its run id, status,
output URLs and final values.

## Steps

1. **Resolve the workspace, and for actions a project.** Use the connection's current
   workspace when it names one, else `flora_list_workspaces`. Action runs (headless or on a
   canvas) need a project too: pick or create one with `flora_list_projects` /
   `flora_create_project` (`prj_…`). A technique run takes only `technique_id` and `inputs`;
   do not create a project for it.

2. **Pick the action.**
   - Prebuilt: `flora_search_actions` with a query ("color grade", "crop", "resize"). The
     catalog uses US spelling: search "color", not "colour". If a search finds nothing, retry
     with one plain word ("color", "blur") before concluding no prebuilt fits. Read the
     result's `params`: the keys, types, ranges and options the studio will show.
   - Custom (the user's own code or a transform no prebuilt covers): write the code with
     `@flora-*` annotations and create it with `flora_add_action` passing `code` and
     `language` (see Custom actions below). This needs a canvas project.
   - Technique (custom action flow): `flora_list_techniques` and match on intent;
     `flora_get_technique` gives the input ids and `run_cost`.

3. **Get the source onto FLORA.** The API accepts any public HTTPS URL, but action and
   technique runtimes load media only from FLORA's own and allowlisted hosts
   (`media.flora.ai`, `ik.imagekit.io` and the like); anything else fails on Apply with
   "Failed to load inputs".
   - Canvas path: place the source with `flora_add_to_canvas` and its `content_url`. The
     canvas re-hosts it, so no asset is needed first.
   - Headless runs and techniques: for any URL outside those hosts (a chat attachment
     from uploads.anthropic.com, files.openai.com, cdn.openai.com or claude.ai, or an
     external link), call `flora_create_asset` with `source` and pass its returned `url`.
   - An asset created with `project_id` is normally already on that canvas (node
     `mcp_upload_…`); check with `flora_get_canvas` and attach it with `flora_attach_asset`
     only if that node is missing, or the image lands there twice. Never base64-encode.

4. **Open the studio with reasonable values.** Pass `open_only: true` on the run tool:
   the studio opens on the inputs and nothing runs or bills until the user clicks Apply.
   (Leave `open_only` out when the user asked you to run the action now rather than tune it,
   and in a host without MCP Apps, where the call itself must run.)
   Send only declared parameter keys (snake_case, as `params[]` lists them); omit the rest
   so defaults apply.
   - Prebuilt, headless: `flora_run_action` with `workspace_id`, `project_id`, `action_id`,
     `inputs: [{ "type": "image", "url": "…" }]` and `params`. Nothing lands on the canvas
     until the user saves it from the studio.
   - On the canvas (prebuilt or custom): place the action with `flora_add_action`, add the
     source with `flora_add_to_canvas` (`type: "static_image"`, `content_url`) connected
     to it in the same call (`connect: [{"from": "<ref>", "to": "<node id>"}]`; to name
     the slot, `in` is the declared input's `name`, e.g. `"source"`, never a modality such
     as `"image"`), then `flora_run_canvas_action` with `project_id` and the
     node id. Outputs come back from `flora_list_generations`; a browser open on the
     canvas materialises them as result nodes, a run started from here may not, so read
     `flora_get_canvas` before telling the user something is on the canvas. Check the tool
     first: when `flora_run_canvas_action` lists a `params` argument, pass values there to
     set them on the node before the run; when it lists none, this FLORA release cannot
     change a canvas action's settings from the studio (its controls open read-only), so
     tune a prebuilt action headlessly instead.
   - Technique: `flora_run_technique` with `technique_id` and `inputs` keyed by the ids
     from `flora_get_technique`. State the cost first; each run bills.

5. **Hand over, then wait.** Tell the user the studio is open, what the controls do, and that
   **Apply** runs it, in one or two sentences, then end your turn. Do not start a run
   yourself, do not poll `flora_list_generations`, do not ask the user to "send a message so
   I can check", do not offer variations: the studio previews browser actions live, runs
   on Apply (showing the cost first for a technique) and waits for the result. In a host
   that renders no MCP Apps (a terminal, an API client: no studio appears), you read the run
   yourself with `flora_list_generations`, at most once every 15 seconds: a sooner read is
   refused with `retry_after_seconds`. If you can wait (a shell `sleep`), wait
   `estimated_seconds` before the first read and `retry_after_seconds` (or 15 s) between
   reads, until it is `completed` or `failed`, then report the outputs. If you cannot wait,
   read once; if the run is still going, give the user its run id, say it is running, and
   end your turn. Read it again on their next message. Never send reads back to back.

6. **Continue from what they apply.** Each Apply updates your context with a
   `floraActionResult`: `runId`, `status` (`running`, then `completed` or `failed` with its
   `error`), `outputs` (ids, types, urls) and the final `values`. It never carries image
   bytes: open an output url if you need to look at it, and never ask the user to resend an
   image. Treat those values as the user's decision. To build on the result, pass an output url as
   an input to the next action or technique, add it to the canvas with `flora_add_to_canvas`
   (`content_url`), or read the run back with `flora_list_generations` (`run_ids`, plus
   `technique_id` for a technique run). To offer a different starting point, open the studio
   again with new values.

## Custom actions

A custom action is code the workspace owns, created with `flora_add_action` (`code`,
`language`, optional `label` and `runtime`) instead of `action_id`. Declare its contract in
comment lines at the top of the file, one annotation per line, `# @flora-x: value` in Python
and `// @flora-x: value` in JavaScript (a space instead of the colon also works):

| Annotation           | Value                                                                                             |
| -------------------- | ------------------------------------------------------------------------------------------------- |
| `@flora-name`        | `"Pixelate"` — the node's name                                                                    |
| `@flora-description` | `"Blocky pixels"`                                                                                 |
| `@flora-inputs`      | JSON array of `{"name", "type"}`; types `image`, `video`, `audio`, `text`, `model3d`              |
| `@flora-outputs`     | **required**, same shape; a run without outputs produces nothing                                  |
| `@flora-params`      | JSON array of `{"key", "label", "type", "default", "min", "max", "step", "options", "visibleIf"}` |

- Every `@flora-params` entry needs a `key`, a `label`, a `type` **and** a `default` of that
  type (a number for `number`, `true`/`false` for `boolean`, a string for `select`, `color`
  and `text`); an entry missing any of them is rejected with the reason. Types: `number` (with
  `min` and `max` it becomes a slider), `boolean`, `color`, `select` (with
  `options: [{"label", "value"}]`), `text`, `point2d`, `point3d`, `interval`;
  `visibleIf: [{"key": "other", "equals": true}]` hides a control until a sibling matches.
- Keys are declared camelCase (`blockSize`) and read in code the same way. Action reads and
  runs use their snake_case form (`block_size`); `flora_get_canvas` lists a custom node's
  params under the declared keys. Writes accept either.
- The workspace plan must include custom actions; a 403 names the remedy. Do not retry.

### Runtime contracts (what your code can call)

Choose the runtime by language and by whether the user should get a live preview:

**Python** (`language: "python"`, runs in FLORA's sandbox; no live preview). Pillow, NumPy,
OpenCV (`cv2`), moviepy, `qrcode`, and `ffmpeg`/`ffprobe`/ImageMagick on the CLI are
available.

- `get_input(i)` returns a dict `{"index", "type", "name", "path"}`; a `text` input carries
  `"text"` instead of `"path"`. It is **not** a file object or an image: open the path
  yourself, e.g. `Image.open(get_input(0)["path"])`. `get_inputs()` lists them all.
- `get_param("key", default)` reads a tunable by its declared camelCase key.
- `write_output("name.png", data)` writes one declared output (bytes, str, or JSON-able);
  the extension sets its type. Outputs fill the declared slots in **filename order**, so
  with several outputs prefix the names to sort as declared (`0-result.png`, `1-mask.png`).
- `raise FloraUserError("message")` for an error the user should read.

A complete, tested Python action (the eval fixture `poster-palette.py`):

```python
# @flora-name: "Poster palette"
# @flora-description: "Quantize an image to a few flat colors"
# @flora-inputs: [{"name": "source", "type": "image"}]
# @flora-outputs: [{"name": "poster", "type": "image"}]
# @flora-params: [
#   {"key": "colorCount", "label": "Number of colors", "type": "select", "default": "6", "options": [{"label": "2", "value": "2"}, {"label": "4", "value": "4"}, {"label": "6", "value": "6"}, {"label": "8", "value": "8"}]},
#   {"key": "smoothing", "label": "Curve smoothing", "type": "number", "default": 20, "min": 0, "max": 100, "step": 1},
#   {"key": "transparentBackground", "label": "Transparent background", "type": "boolean", "default": false},
#   {"key": "backgroundColor", "label": "Background", "type": "color", "default": "#ffffff", "visibleIf": [{"key": "transparentBackground", "equals": false}]}
# ]
import io
from PIL import Image, ImageFilter
source = Image.open(get_input(0)["path"]).convert("RGBA")
smoothing = int(get_param("smoothing", 20))
if smoothing:
    source = source.filter(ImageFilter.ModeFilter(size=1 + smoothing // 10))
transparent = bool(get_param("transparentBackground", False))
# Flatten onto the background first: quantizing straight from RGBA turns
# transparent pixels black.
flat = Image.new("RGBA", source.size, "#ffffff" if transparent else get_param("backgroundColor", "#ffffff"))
flat.alpha_composite(source)
colors = int(get_param("colorCount", "6"))
if transparent:
    # Choose the palette from the visible pixels only: a hidden backdrop would
    # take a palette entry and pull edge colours toward it.
    rgb = source.convert("RGB")
    alpha = source.getchannel("A")
    visible = [p for p, a in zip(rgb.getdata(), alpha.getdata()) if a > 0] or [(255, 255, 255)]
    visible = visible[:: max(1, len(visible) // 200_000)]
    sample = Image.new("RGB", (len(visible), 1))
    sample.putdata(visible)
    poster = rgb.quantize(palette=sample.quantize(colors=colors)).convert("RGBA")
    poster.putalpha(alpha)
else:
    poster = flat.convert("RGB").quantize(colors=colors).convert("RGBA")
buffer = io.BytesIO()
poster.save(buffer, format="PNG")
write_output("poster.png", buffer.getvalue())
```

**JavaScript on the node runtime** (`language: "javascript"`, `runtime: "node"` or plain
script code; no live preview): the same helpers in camelCase — `getInput(i)` gives
`{ path }` or `{ text }`, `getParam(key, default)`, `writeOutput("out.png", buffer)`;
`sharp` and `canvas` are preloaded; `throw new FloraUserError("message")`.

**JavaScript as an ES module in the browser** (`language: "javascript"`; the runtime
resolves to `browser` when the module `export`s `execute`, or pass `runtime: "browser"`).
This is what gives the user a **live preview** in the studio and on the canvas. Browser APIs
only (Canvas 2D, WebGL, WebCodecs); no `fetch`, no Node helpers.

- `export async function execute({ inputs, params, state })` renders the final output and
  returns `{ type: "image", dataUrl }` (or an array of outputs). Inputs are
  `{ type, dataUrl, name }` or `{ type: "text", text }`.
- `export const preview = { mode: "wysiwyg", mount({ el, inputs, params, state, onState }) }`
  paints the same thing into `el` and returns `{ update({ params, inputs, state }), dispose() }`;
  the studio calls `update` on every edit. `onState(json)` records interaction state the
  kept run replays through `execute({ state })`.

A complete, tested browser action (the fixture `pixelate-browser.js`):

```js
// @flora-name: "Pixelate"
// @flora-description: "Blocky pixels, tuned live"
// @flora-inputs: [{"name": "source", "type": "image"}]
// @flora-outputs: [{"name": "pixelated", "type": "image"}]
// @flora-params: [
//   {"key": "blockSize", "label": "Block size", "type": "number", "default": 12, "min": 2, "max": 64, "step": 1},
//   {"key": "grid", "label": "Show grid", "type": "boolean", "default": false}
// ]
function load(dataUrl) {
  return new Promise((resolve, reject) => {
    const image = new Image()
    image.onload = () => resolve(image)
    image.onerror = () => reject(new Error("The source image could not be decoded."))
    image.src = dataUrl
  })
}
function paint(canvas, image, params) {
  const block = Math.max(1, Math.round(Number(params.blockSize ?? 12)))
  canvas.width = image.naturalWidth
  canvas.height = image.naturalHeight
  const ctx = canvas.getContext("2d")
  const small = document.createElement("canvas")
  small.width = Math.max(1, Math.round(canvas.width / block))
  small.height = Math.max(1, Math.round(canvas.height / block))
  small.getContext("2d").drawImage(image, 0, 0, small.width, small.height)
  ctx.imageSmoothingEnabled = false
  ctx.clearRect(0, 0, canvas.width, canvas.height)
  ctx.drawImage(small, 0, 0, small.width, small.height, 0, 0, canvas.width, canvas.height)
  if (params.grid) {
    // Lines on the actual block edges: a block is canvas / small in each direction.
    const cellX = canvas.width / small.width
    const cellY = canvas.height / small.height
    ctx.strokeStyle = "rgba(0, 0, 0, 0.25)"
    ctx.lineWidth = 1
    ctx.beginPath()
    for (let i = 1; i < small.width; i++) {
      const x = Math.round(i * cellX) + 0.5
      ctx.moveTo(x, 0)
      ctx.lineTo(x, canvas.height)
    }
    for (let j = 1; j < small.height; j++) {
      const y = Math.round(j * cellY) + 0.5
      ctx.moveTo(0, y)
      ctx.lineTo(canvas.width, y)
    }
    ctx.stroke()
  }
}
export async function execute({ inputs, params }) {
  const image = await load(inputs.find((input) => input.type === "image").dataUrl)
  const canvas = document.createElement("canvas")
  paint(canvas, image, params)
  return { type: "image", dataUrl: canvas.toDataURL("image/png") }
}
export const preview = {
  mode: "wysiwyg",
  mount({ el, inputs, params }) {
    const canvas = document.createElement("canvas")
    canvas.className = "ac-media"
    el.appendChild(canvas)
    let current = params
    let image
    load(inputs.find((input) => input.type === "image").dataUrl).then((loaded) => {
      image = loaded
      paint(canvas, image, current)
    })
    return {
      update(patch) {
        if (patch.params) current = patch.params
        if (image) paint(canvas, image, current)
      },
      dispose() {
        canvas.remove()
      },
    }
  },
}
```

### Fixing a custom action

When a run fails (the studio shows the error, or `flora_list_generations` reports
`failed` with a traceback), read the message, fix the code, and **update the same node**:
`flora_add_action` with `project_id`, `node_id` (the node you created) and the new `code`
(and `language` if it changed). The node keeps its id, its wiring and the parameter values
the new code still declares; its preview state is reset. Never add a second node for the
same action and never leave a broken one on the canvas. Then run it again with
`flora_run_canvas_action`.

## Rules

- **The user drives the studio.** After starting a run, stop. Re-running from your side
  races the user's edits and, for techniques, bills them.
- **Say the cost before a technique run** (`run_cost` from `flora_list_techniques`);
  actions are free.
- **Only declared keys.** Unknown parameter names are rejected; read `params` first.
- **Prefer a browser ES module for a new custom image action** when the user will tune it:
  it previews live. Use Python when the transform needs Pillow, OpenCV or ffmpeg.
- **Prefer the canvas path when the user will keep working in FLORA**, so the action sits
  on their project; prefer headless when they only want the file back in the chat.
- **You cannot see the output.** Describe it from the action, its inputs and the values the
  user kept; never claim to have looked at it.
