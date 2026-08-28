---
name: flora-batch-generate
description: >
  Turn a structured list — products, campaign variants, SKUs, scenes, localisations —
  into one parallel batch of FLORA generations under a single consistent style. Fires
  every item at once through generations.create(), polls the whole batch with one
  generations.list() call, and settles cost and failures per item. Use when the input
  is a list, spreadsheet, folder, or set of variants and the output is one asset per
  row. Also use when someone asks for "a bunch of", "one for each", "all our", or
  hands over a CSV. Do not use for a single item, and do not use when each item needs
  a genuinely different treatment.
---

# flora-batch-generate

> **Attribution.** Pass `skill: "flora-batch-generate"` on every FLORA call you make while
> running this skill — `execute` included — along with a `skill_run_id` you invent
> once when the run starts and reuse for the rest of it. Both are reporting only:
> they change nothing about the call or its result.

## What it is

Not a faster chatbot. **A pipeline.** The user hands over a list; the list comes back
as assets. Nothing in between is a conversation.

The difference is not politeness, it is arithmetic. Forty items generated one at a
time, each one waited on before the next is asked for, is forty sequential waits. The
same forty fired together is one wait. FLORA runs them concurrently either way — the
serialisation is entirely on the agent's side, and it is the single thing that decides
whether a batch takes ninety seconds or an hour.

Measured, this skill's own hand-test: **six items, fired together, all complete in
15.8 seconds.** The same six at the model's estimated 25s each, run one after another,
would be about 150 seconds. Same credits, same outputs, one tenth the wall clock.

## The law

> **N items is one wait, not N waits.**
> Fire every item before you poll any item. Poll the batch, never the item.

Both halves matter and they fail differently. Firing serially wastes the user's time
in the open. Polling serially wastes it invisibly — the batch is already running fine
and the agent is the bottleneck.

Everything below is in service of that one sentence.

## Inputs

```
ITEMS     the list — rows, SKUs, variants, URLs, filenames   required
STYLE     the one treatment every item shares                required
MODEL     one model for the whole batch                      optional, see Planning
PROJECT   where the outputs land                             optional, one is created
```

**One style, N items.** This is the shape the skill exists for: a single consistent
treatment, varied only by the per-item variable. A product list becomes PDP shots by
holding the lighting, backdrop, lens and framing fixed and changing only the subject
noun. If two items genuinely need different treatments, that is two batches — say so
rather than quietly blending them, because a blended batch has no consistent style and
the user cannot tell which axis moved.

## The four phases

Plan, fire, poll, settle. They are separate because **the sandbox will not hold all
four for a slow model** — see Gotchas. Keep them as separate `execute` calls and the
skill survives any batch size.

---

### 1. Plan — free, and it is where the batch is saved

Nothing here spends. Everything here prevents spend.

```ts
async function run(client) {
  const models = await client.models.list({ type: "image", limit: 100 })
  const m = models.getPaginatedItems().find((x) => x.model_id === "t2i-flux-2-klein-4b")
  return {
    model: m.model_id,
    credits_each: m.estimated_credits,   // 4
    seconds_each: m.estimated_seconds,   // 25
    params: m.params,                    // the ONLY valid param names and enum values
  }
}
```

**Total the cost and stop.** Multiply and state it plainly — *"24 items x 4 credits =
96 credits, about $0.10. Proceed?"* — then wait for a yes. Do this even when the
per-item figure is trivial. The batch is exactly where a trivial figure stops being
trivial, and the user is the one who finds out.

Measured conversion on the hand-test: `estimated_credits: 4` settled at
`charged_cost: 0.004`, so **1 credit ≈ $0.001**. Quote credits and dollars both.

**Validate every param against `m.params` before firing.** This is not defensive
tidiness, it is the most expensive silent failure on this surface:

> An unknown **model** is a clean 400 at create time, free, with the accessible model
> list in the error message. An unknown **param value** is not validated at all. It is
> accepted, it runs, it completes, and **it bills** — the model silently falls back to
> the default.

Measured: `params: { aspect_ratio: "banana_9_9" }` returned a `run_id`, ran to
`completed`, charged $0.004, and produced a square image. No error anywhere. Across
forty items a single typo'd enum in the per-item variable is forty paid renders at the
wrong aspect ratio, discovered by a human looking at the outputs.

Also confirm the item list back to the user — the parsed rows and the count — before
spending. A misparsed CSV column is free to fix now and billable to fix later.

---

### 2. Fire — all of them, in one pass, with no gap

```ts
async function run(client) {
  const WS = "ws_…", PRJ = "prj_…"
  const STYLE =
    "Studio product photograph on a seamless warm-grey backdrop, soft large softbox " +
    "from camera left, gentle falloff, subtle contact shadow, 85mm, centred, no props, no text."
  const ITEMS = [
    { sku: "PO-01", subject: "a matte black ceramic pour-over coffee dripper" },
    { sku: "WB-04", subject: "a brushed steel insulated water bottle" },
    // …
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

  const fired: Record<string, string> = {}
  const rejected: string[] = []
  settled.forEach((r, i) => {
    if (r.status === "fulfilled") fired[r.value.run_id] = ITEMS[i].sku
    else rejected.push(`${ITEMS[i].sku}: ${r.reason?.message ?? r.reason}`)
  })

  return { project_id: PRJ, fired, rejected }   // RETURN the map. It is the batch.
}
```

**`Promise.allSettled`, never `Promise.all`.** One rejected create must not discard the
run_ids of the items that did fire. With `Promise.all` a single 400 throws away the
whole array and you have billed generations you can no longer identify — they are
running, they will charge, and nothing in the transcript knows their ids.

**Return the `run_id → item` map and log it.** Variables do not persist between
`execute` calls. That map is the only link between a run and the row it came from;
losing it means a completed batch you cannot report on.

**No pacing.** Measured: six concurrent creates completed the fire phase in **3.1
seconds** with no rate limiting. Do not stagger on a timer — that is the serial failure
mode wearing a safety costume. The two real exceptions are named under Gotchas.

---

### 3. Poll — one call for the whole batch

```ts
async function run(client) {
  const PRJ = "prj_…"
  const FIRED = { "run_a": "PO-01", "run_b": "WB-04" /* …from phase 2 */ }

  const page = await client.generations.list({ project_id: PRJ, limit: 100 })

  const byRun: Record<string, any> = Object.fromEntries(
    page.getPaginatedItems().map((g) => [g.run_id, g]),
  )
  const terminal: any[] = []
  const running: string[] = []
  for (const [runId, sku] of Object.entries(FIRED)) {
    const g = byRun[runId]
    if (g && (g.status === "completed" || g.status === "failed")) {
      terminal.push({ sku, status: g.status, url: g.outputs?.[0]?.url, error_code: g.error_code })
    } else {
      running.push(sku)
    }
  }
  return { total: Object.keys(FIRED).length, settled: terminal.length, running, terminal }
}
```

**One `list()` covers the batch. `retrieve()` covers one item.** That is the whole
argument, and it is worth the measured numbers because the serial habit is strong:

```
1  list({ limit: 100 })   covering 100 runs      265 ms
20 retrieve()  in parallel                       838 ms
20 retrieve()  in series                        6238 ms
```

One list is **24x faster than twenty serial retrieves while covering five times as
many runs**. And this is per poll cycle: a forty-item batch polled every five seconds
for three minutes is 36 cycles. Central polling spends ten seconds of that on polling.
Serial retrieval spends 36 × 40 × 312ms — about seventy-five minutes of round trips
inside a three-minute batch. It does not finish; it thrashes.

**`limit: 100` explicitly, every time.** 100 is the API's hard maximum
(`limit` is validated `min(1).max(100)`). It is *not* the default — the MCP
`flora_list_generations` tool defaults to **20**, so a 30-item batch polled without an
explicit limit silently reports ten items as "still running" forever. Past 100 items,
page with `cursor`; do not slice a bigger page client-side.

**Filter by `project_id`.** A batch in its own project makes the poll exact. Without
it you are paging the account's whole history to find your forty.

**Key on `status`, never on `progress` or `completed_at`.** Measured: a *failed* run
reports `progress: 100` and a populated `completed_at`. Both look like success. Only
`status === "completed"` plus a present `outputs` array means an asset exists.

`generation_id` and `run_id` are the same value on every row — index on whichever, but
do not treat them as two keys into two things.

---

### 4. Settle — cost, then failures

**Re-read cost after the batch is terminal, not at the moment each item finishes.**
`charged_cost` is eventually consistent. Measured on the hand-test: at the instant the
sixth item flipped to `completed` its `charged_cost` was **absent**, and summing then
reported **$0.020 against a true $0.024 — a 17% undercount**. Re-listed a minute later,
all six carried `charged_cost: 0.004`.

So: poll on `status`, then do one final `list()` for the money. If a field is still
missing, report the total as a floor and say so — never present an undercount as the
bill.

The same caution applies at the other end. **The `charged_cost` returned by
`create()` is a quote, not the bill.** On this batch the quote matched exactly
($0.004 → $0.004), which is precisely why it cannot be trusted: on a heavier model the
quote has been measured at **0.253 against 0.873 actually charged, 3.45x**. Quote from
a settled run or state plainly that the figure is a floor.

## When a batch partially fails

A batch is not a transaction. Some items complete, some fail, and the two need
different sentences. **Never abort a paid batch partway** — the items already running
will finish and bill regardless, so abandoning them buys nothing and loses their URLs.

Failures arrive at two different moments and they are not the same problem.

### Create-time rejection — free, and usually your fault

The item never became a run. Nothing billed. These are in `rejected[]` from phase 2.

| status | code | meaning | action |
|---|---|---|---|
| 400 | `input_validation_error` | bad model id, malformed body | fix and re-fire — free |
| 402 | `insufficient_credits` | out of credits | **stop the whole batch**, tell the user |
| 429 | `rate_limited` | workspace throttled | retry — see Gotchas |
| 409 | `idempotency_duplicate` | key already used | this item already fired; find its run |
| 500 | `unknown_error` | often a malformed `prj_`/`ws_` id | check the ids before assuming an outage |

A 402 mid-batch is the one case that justifies stopping: every remaining create will
fail the same way, and firing them anyway just fills the report with noise.

### Run-time failure — it ran, then it broke

The run exists and carries `error_code` and `error_message`. Classify by code:

| retry | codes |
|---|---|
| **retry now** — transient | `GENERATION_PROVIDER_TIMEOUT`, `GPU_PROVIDER_ERROR`, `GENERATION_GENERIC_ERROR`, `GENERATION_FAILED_TO_START`, `GENERATION_FAILED_TO_UPLOAD`, `SERVER_ERROR` |
| **retry later** — provider under load | `GENERATION_DOWNSTREAM_SERVICE_ERROR`, `GENERATION_QUEUE_TOO_LARGE`, `GENERATION_QUEUE_NOT_MOVING`, `GENERATION_CIRCUIT_BREAKER_OPEN`, `GENERATION_INVALID_PROVIDER_RESPONSE`, `GENERATION_NO_RESULT` |
| **change the input** — never retry as-is | `GENERATION_PROMPT_MODERATED`, `LLM_REFUSAL`, `GENERATION_INPUT_VALIDATION`, `GENERATION_INVALID_PARAMS`, `GENERATION_INVALID_URL` |
| **report, do not retry** | `BILLING_NOT_ENOUGH_CREDITS`, `GENERATION_NOT_PAID`, any `ACCESS_*`, `GENERATION_CANCELLED` |

> **Read `error_message`, not just `error_code`.** Two of the retryable codes routinely
> carry a moderation refusal. Measured, a real failed run:
> `GPU_PROVIDER_ERROR` — *"Your request was rejected by the safety system …
> safety_violations=[sexual]"*. The code says retry now; the truth is change the input.
> `GENERATION_NO_RESULT` behaves the same way — the model declining a subject, wearing
> a provider-unavailable code. Retrying either blind bills the same refusal again, and
> in a batch it does so on a loop.

Failed generations are refundable, so a failure usually costs nothing. **A retry is a
new generation and bills again.** Retry once, silently, only for the transient tier;
anything else goes in the report for the user to decide.

### Retrying safely

**The SDK's `idempotencyKey` request option does nothing on this client. Use the
header.**

```ts
// INERT — measured: two calls with the same key produced two run_ids and billed twice.
client.generations.create(body, { idempotencyKey: key })

// CORRECT — the second call returns 409 idempotency_duplicate.
client.generations.create(body, { headers: { "Idempotency-Key": key }, maxRetries: 0 })
```

The client declares an `idempotencyHeader` and never assigns it, so the option is read
and dropped. This matters because the option is the obvious thing to reach for and its
failure is invisible: the retry succeeds, the user is billed twice, nothing errors.

What the header actually gives you, and what it does not:

- It is a **duplicate suppressor, not a response replayer.** A repeated key returns a
  409 error, not the original run. You cannot use it to recover a lost `run_id`.
- The key is **released when the request fails**. That is the designed use: a create
  that returned a network error or a 5xx can be safely re-fired with the same key, and
  you will not double-bill if the first one actually landed.
- A run that failed *after* it was created has **burned its key for two hours**
  (TTL 7200s). Retrying that item needs a *new* key — suffix it, `${sku}-r2`.
- Keys are scoped to workspace + operation + destination, so `sku` alone is a safe key
  within one project and collides across two.
- Set `maxRetries: 0` on any call you expect might duplicate. The SDK treats 409 as
  retryable, so a duplicate burns **~1.8s** in retries that can never succeed.

## Gotchas

```
SANDBOX
execute timeout       ~5 minutes total per call, 30s per HTTP request. A 40-item batch
                      on a ~107s model will NOT fire-and-finish inside one call. This
                      is why fire and poll are separate calls: fire, return the run_id
                      map, poll in a later call. Never build a loop that must outlive
                      the sandbox.
no variables persist   between execute calls. Return or log the run_id -> item map or
                      the batch is unrecoverable.
no filesystem         every deliverable is a URL. Never claim to have written a file.

FIRING
Promise.allSettled    not Promise.all. One rejection must not discard the run_ids of
                      items that did fire — those are billed and now untrackable.
no pacing needed      6 concurrent creates fired in 3.1s, no throttling. Do not stagger.
Krea models           the exception: they rate-limit hard and lose most of a concurrent
                      batch to GENERATION_DOWNSTREAM_SERVICE_ERROR. Pace those at ~5s.
rate limit scope      keyed on WORKSPACE, not user or key. A big batch competes with
                      itself and with teammates on the same workspace. 429 is
                      `rate_limited`; the SDK auto-retries it with backoff
                      (maxRetries defaults to 2), so most of it self-heals.

POLLING
limit: 100            always explicit. 100 is the API maximum; the MCP tool's default
                      is 20, which silently truncates any batch over 20.
status only           progress: 100 and completed_at are BOTH set on failed runs.
generation_id         is the same value as run_id, not a second key.

COST
params not validated  an unknown param VALUE is accepted, runs, and bills at the
                      default. Only an unknown MODEL is a clean 400. Validate against
                      models.list() params before firing.
charged_cost at fire  is a quote. Measured elsewhere at 0.253 quoted vs 0.873 charged.
charged_cost on list  is eventually consistent — absent for a moment after a run goes
                      terminal. Summing at detection undercounted by 17%. Re-read.
failures refund       a failed run generally does not cost. A retry is a new
                      generation and does.

IDEMPOTENCY
generations           header only: headers: { "Idempotency-Key": … }
techniques.runs       body field: { idempotency_key: … }
                      Do not carry the pattern across; each ignores the other's shape.
```

## Batching a technique instead of a model

When every item needs the *same multi-step treatment* rather than the same prompt —
background swap, relight, sketch-to-render — batch `techniques.runs.create()` instead
of `generations.create()`. The law and the four phases are unchanged. Two differences:

- The idempotency key is a **body field**, `idempotency_key`, not a header.
- Cost comes from the technique's `run_cost`, not from a model's `estimated_credits`.

Resolve one technique for the whole batch. Items needing two techniques are two
batches.

## Not polling at all

Every create accepts a `callback_url` — an HTTPS endpoint that receives a signed POST
when the run reaches a terminal state (`run.completed` / `run.failed`), HMAC-SHA256
signed via `Flora-Signature`, retried three times with backoff.

If the user has somewhere to receive a webhook, that is strictly better than polling
and it removes the sandbox timeout from the problem entirely. Most agent sessions do
not, which is why this skill is written around polling — but ask, on a batch large
enough that polling is the awkward part.

## Reporting back

One row per item, in the order the user gave them. The SKU or filename is the key the
user thinks in — lead with it, never with the `run_id`.

```
SKU      STATUS      COST     OUTPUT
PO-01    completed   $0.004   https://media.flora.ai/…
WB-04    completed   $0.004   https://media.flora.ai/…
AP-09    failed      —        GENERATION_PROMPT_MODERATED — "linen apron" flagged;
                              needs a reworded prompt, not a retry
```

Then three lines and stop:

- **the total** — settled, or explicitly a floor if any `charged_cost` was still missing
- **what failed and which tier it is in** — retried-and-recovered, retryable, or needs
  a changed input. Do not silently retry anything outside the transient tier.
- **what you did not do** — items not fired, a batch stopped on 402, a truncated page.

**You cannot see any output.** Report URLs and let the user judge them. Never
characterise an image you have not been shown.

Media URLs are public, unsigned and permanent. Pasting one into a transcript discloses
that asset to anyone who reads it — worth a word when the batch is unreleased work.
