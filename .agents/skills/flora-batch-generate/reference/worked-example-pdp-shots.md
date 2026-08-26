# Worked example — six products, one style

This is the skill's hand-test, run against production. Every number below is measured,
not estimated. It is the canonical shape: **one consistent style, N products.**

## The brief

Six kitchen products need PDP shots that look like one shoot. The style is fixed; only
the subject noun changes.

## Phase 1 — plan

```ts
async function run(client) {
  const models = await client.models.list({ type: "image", limit: 100 })
  const m = models.getPaginatedItems().find((x) => x.model_id === "t2i-flux-2-klein-4b")
  return { credits: m.estimated_credits, seconds: m.estimated_seconds, params: m.params }
}
```

```
credits: 4        seconds: 25
params:  acceleration | aspect_ratio | seed | num_inference_steps
         aspect_ratio ∈ landscape_16_9 landscape_4_3 square_1_1 portrait_4_3 portrait_16_9
```

Quoted to the user: **6 items × 4 credits = 24 credits, about $0.024.** Confirmed
`square_1_1` is a real enum value before using it — the reason why is in `SKILL.md`
under Plan.

## Phase 2 — fire

The style string is built once and concatenated onto each subject. That is the whole
consistency mechanism; there is nothing cleverer needed.

```ts
const STYLE =
  "Studio product photograph on a seamless warm-grey backdrop, soft large softbox " +
  "from camera left, gentle falloff, subtle contact shadow, 85mm, centred, no props, no text."

const ITEMS = [
  { sku: "PO-01", subject: "a matte black ceramic pour-over coffee dripper" },
  { sku: "WB-04", subject: "a brushed steel insulated water bottle" },
  { sku: "AP-09", subject: "a folded oatmeal linen apron" },
  { sku: "CB-02", subject: "a walnut wood cutting board, rectangular" },
  { sku: "MJ-07", subject: "a clear glass measuring jug with printed markings" },
  { sku: "SB-03", subject: "a stack of three speckled stoneware bowls" },
]

const settled = await Promise.allSettled(
  ITEMS.map((item) =>
    client.generations.create({
      workspace_id: WS,
      project_id: PRJ,
      type: "image",
      prompt: `${item.subject}. ${STYLE}`,
      model: "t2i-flux-2-klein-4b",
      params: { aspect_ratio: "square_1_1" },
    }),
  ),
)
```

```
fire wall-clock   3,101 ms for all six
rejected          0
rate limiting     none
quoted at create  $0.004 each
```

## Phase 3 — poll

One `generations.list({ project_id, limit: 100 })` per cycle, five seconds apart.

```
cycles to all-terminal   3
average poll             269 ms
total time in polling    807 ms
wall-clock to complete   15,810 ms
```

Sequentially at the model's estimated 25s each, the same six would be about 150
seconds. The batch is **~10x faster for identical credits.**

## Phase 4 — settle

The undercount happened here, exactly as `SKILL.md` warns:

```
summed at the moment each item went terminal   $0.020    ← SB-03 had no charged_cost yet
re-listed after the batch settled              $0.024    ← all six at $0.004
```

A 17% undercount, from reading cost at detection instead of after settling. Nothing
errored and nothing looked wrong.

## The report

```
SKU      STATUS      COST     OUTPUT
PO-01    completed   $0.004   https://media.flora.ai/node-inputs/2026/8/25/…
WB-04    completed   $0.004   https://media.flora.ai/node-inputs/2026/8/25/…
AP-09    completed   $0.004   https://media.flora.ai/node-inputs/2026/8/25/…
CB-02    completed   $0.004   https://media.flora.ai/node-inputs/2026/8/25/…
MJ-07    completed   $0.004   https://media.flora.ai/node-inputs/2026/8/25/…
SB-03    completed   $0.004   https://media.flora.ai/node-inputs/2026/8/25/…

6/6 completed. Total $0.024 (settled). No failures.
```

## What else this test established

Run alongside the batch, on the same project:

- **`params: { aspect_ratio: "banana_9_9" }`** — accepted, ran, completed, charged
  $0.004, produced a square image. No validation error at any layer.
- **`model: "t2i-does-not-exist"`** — clean `400 input_validation_error`, free, with
  the accessible model list in the message.
- **`project_id: "prj_nope"`** — opaque `500 unknown_error`, not a 404.
- **`{ idempotencyKey: k }` twice** — two distinct `run_id`s, billed twice. The option
  is inert on this client.
- **`headers: { "Idempotency-Key": k }` twice** — second call `409
  idempotency_duplicate`, as intended. With default `maxRetries`, that doomed duplicate
  spent 1,798 ms in retries before giving up.

Total cost of the entire hand-test, batch and edge cases together: **11 generations,
about $0.05.**
