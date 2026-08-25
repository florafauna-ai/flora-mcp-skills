# Failure codes — the complete table

`SKILL.md` carries the abridged version, which covers everything you hit in practice.
This is the full mapping, for the case where a batch returns a code that is not there.

Two different layers fail, and they are not interchangeable.

## Layer 1 — HTTP, at create time

The item never became a run. Nothing billed. These come back as a thrown error from
`generations.create()` with a `status` and a `code`.

| status | code | retry? |
|---|---|---|
| 400 | `invalid_json` | no — fix the body |
| 400 | `input_validation_error` | no — fix and re-fire, free |
| 401 | `unauthorized` / `invalid_api_key` | no — auth is broken, stop the batch |
| 402 | `insufficient_credits` | no — **stop the whole batch** |
| 403 | `forbidden` / `paid_plan_required` | no |
| 404 | `not_found` | no |
| 409 | `idempotency_duplicate` | no — this item already fired, go find its run |
| 429 | `rate_limited` | yes — SDK auto-retries with backoff |
| 500 | `internal_error` / `unknown_error` | once — but check your `prj_`/`ws_` ids first |

A malformed project id returns an opaque `500 unknown_error`, not a 404. Measured.
Do not read a 500 on a create as an outage until the ids are confirmed good.

## Layer 2 — the run failed after it started

The run exists. `status: "failed"`, with `error_code` and `error_message`. Grouped by
the platform's own retry hint.

### retry_now — transient, safe to re-fire once

```
GENERATION_PROVIDER_TIMEOUT        GENERATION_FAILED_TO_START
GPU_PROVIDER_ERROR                 GENERATION_FAILED_TO_UPLOAD
GENERATION_GENERIC_ERROR           GENERATION_FAILED_TO_UPDATE
SERVER_ERROR                       GENERATION_FAILED_TO_GET
GENERATION_PREGENERATION_FAILED    GENERATION_POSTGENERATION_FAILED
GENERATION_MAP_AFTER_REQUEST_FAILED
```

### retry_later — provider under load, back off first

```
GENERATION_DOWNSTREAM_SERVICE_ERROR    GENERATION_QUEUE_TOO_LARGE
GENERATION_INVALID_PROVIDER_RESPONSE   GENERATION_QUEUE_NOT_MOVING
GENERATION_NO_RESULT                   GENERATION_CIRCUIT_BREAKER_OPEN
GENERATION_MODAL_POLL_ERROR            AUDIO_GENERATION_ERROR
GENERATION_PROVIDER_FAILED_TO_GET_STATUS
```

### change_input — never retry as-is, it will fail identically

```
GENERATION_PROMPT_MODERATED     GENERATION_INVALID_PARAMS
LLM_REFUSAL                     GENERATION_INVALID_URL
GENERATION_INPUT_VALIDATION     GENERATION_ENDPOINT_NOT_FOUND
GENERATION_MAP_BEFORE_REQUEST_FAILED    GENERATION_PROVIDER_NOT_SUPPORTED
```

### not_retryable — report it and move on

```
BILLING_NOT_ENOUGH_CREDITS      BILLING_CREDITS_LIMIT_EXCEEDED
BILLING_WOULD_EXCEED_LIMIT      BILLING_FAILED_TO_RESERVE_CREDITS
GENERATION_NOT_PAID             GENERATION_CANCELLED
ACCESS_* (all of them)          *_ENTITLEMENT_REQUIRED (all of them)
```

## The trap in this table

**Two `retry_later` codes and one `retry_now` code are routinely moderation refusals.**

`GPU_PROVIDER_ERROR` and `GENERATION_NO_RESULT` both surface a model declining a
subject — real people, sensitive content, an input it will not process — under a code
that says the provider had a problem. A measured example:

```
error_code:    GPU_PROVIDER_ERROR
error_message: "Your request was rejected by the safety system. …
                safety_violations=[sexual]."
```

Classify by `error_code`, then **read `error_message` before acting on it**. If the
message names safety, moderation, a refusal, or a policy, treat the item as
`change_input` no matter what the code says. In a batch the cost of getting this wrong
compounds: an automatic retry tier will re-bill the same refusal on every pass.

## Credits and refunds

Every category except `INSUFFICIENT_CREDITS` is marked refundable, so a failed run
generally does not cost. A **retry is a new generation and bills again** — which is
why the tiers above matter more than they would if retrying were free.
