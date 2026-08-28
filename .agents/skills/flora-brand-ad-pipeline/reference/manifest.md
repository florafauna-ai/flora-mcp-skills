# The manifest — the join-key contract

One JSON file per campaign. Written after every stage, read before every stage. It is
the only thing that survives a lost conversation, a timed-out sandbox, or a re-run
three days later.

## The join key

Every row carries one `asset_key`, and that key is what every other system's id hangs
off. Build it from facts that cannot change mid-campaign:

```
{campaign}-{sku}-{placement}      straw-launch-STRAW500G-feed_1x1
```

Not from a timestamp, not from a run id, not from an index into a list the user might
re-order. A key that changes between runs makes the manifest useless at exactly the
moment it is needed.

## Row shape

```jsonc
{
  "campaign": "straw-launch",
  "brand_file": "…/brand.json",
  "rows": [
    {
      "asset_key": "straw-launch-STRAW500G-feed_1x1",
      "sku": "STRAW-500G",
      "placement": "feed_1x1",

      "state": "paused",          // see the state machine below
      "blocked_reason": null,     // verbatim error string when state is "blocked"

      "flora_run_id": "run_…",    // written AT FIRE TIME, not at completion
      "flora_url": "https://media.flora.ai/…",
      "charged_cost": 0.004,      // re-read after the batch is terminal

      "finished_url": "https://…",   // after the price composite
      "qc": { "dimensions": true, "price_layer": true, "palette": true },

      "drive_file_id": "1AbC…",
      "supabase_path": "straw-launch/straw-launch-STRAW500G-feed_1x1.jpg",
      "supabase_url": "https://…",

      "meta_creative_id": "1203…",
      "meta_ad_id": "1204…"
    }
  ]
}
```

## State machine

```
planned  ->  fired  ->  generated  ->  finished  ->  archived  ->  hosted  ->  paused
                 \           \             \             \            \
                  ----------- blocked -----------------------------------
```

Forward only. A row never moves backwards, and `blocked` is terminal until a human
decides what to do with it. Resuming a campaign means picking up every row at its
recorded state — not restarting the pipeline and hoping the later stages are idempotent.

## Rules

- **Write `flora_run_id` at fire time.** A generation you fired and did not record is
  billing now and cannot be identified later. `Promise.allSettled` exists so that one
  rejected create does not discard the ids of the items that did fire; the manifest
  exists so those ids outlive the call.
- **Write one row at a time downstream.** Batching the Meta writes to the end means one
  failure loses every id in the batch, and the ads still exist.
- **Read before proposing.** The first thing a resumed campaign reports is what is
  already done. Proposing work before reading the manifest is how a campaign gets two
  of every ad.
- **Never rewrite history.** A re-generated asset is a new row with a suffixed key
  (`…-feed_1x1-r2`), not an overwrite. The old row's Drive and Meta ids still point at
  real objects a human may be looking at.
- **The manifest is the report.** Do not maintain a second summary in the conversation
  that can disagree with it.

## Idempotency across the four systems

Each system offers something different, and none of them offers enough on its own.

```
FLORA generations   Idempotency-Key HEADER. Key released on a failed request; burned
                    for 7200s by a run that failed after creation — retry needs a new
                    key, suffix it. The SDK's idempotencyKey request option is inert.
FLORA techniques    idempotency_key BODY field. Different shape, same purpose.
Google Drive        TODO(measure): confirm behaviour of a repeated upload with the same
                    name in the same folder — duplicate file or replace.
Supabase storage    deterministic object path from asset_key makes an upload naturally
                    idempotent. Decide upsert vs fail-on-exist and record which.
Meta Ads            TODO(measure): no reliable idempotency assumed. The manifest is the
                    guard. Never create an ad for a row that already has a meta_ad_id.
```

The general rule: **the manifest is the idempotency layer.** Per-system keys are a
second line of defence, not the design.
