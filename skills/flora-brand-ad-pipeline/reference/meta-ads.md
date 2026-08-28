# Meta Ads — the last stage

This page is the least proven part of the pipeline. Everything marked `TODO(measure)`
must be run and recorded before the skill is trustworthy end to end. Do not soften a
TODO into prose; an unmeasured claim here creates ads.

## The invariant

> **Paused, always. The agent stages; a human publishes.**

Concretely, the agent never:

- sets `status: "ACTIVE"` on an ad, ad set or campaign
- creates or raises a budget
- edits a schedule, an audience or a bid
- unpauses anything, including something it paused earlier in the same session

If the user asks for any of these, say plainly that this skill stops at paused. That is
not a limitation to route around — it is the whole reason the pipeline is safe to run
unattended.

## The creative path

An ad needs a creative; a creative needs an image Meta can serve. **Meta normally wants
its own copy of the image in the ad account** rather than serving from a third-party
URL: upload to the ad account's image endpoint, get back a hash, reference the hash from
the creative.

That has a consequence worth stating to the customer, because it surprises people:
**the Supabase CDN copy is not what Meta serves.** Supabase is the durable hosted master
the business controls. Meta takes a copy at creative-creation time and serves that.
Changing the Supabase object later does not change a live ad.

```
TODO(measure)  the exact ingest call on the API version in use, and whether it accepts
               a remote URL or requires bytes. If it accepts a URL, confirm whether it
               can reach the Supabase public URL, and record the timing.
TODO(measure)  whether an image hash is stable and reusable across creatives, and how
               long it persists in the ad account.
TODO(measure)  video ingest, which is a different endpoint and asynchronous. The FLORA
               side can produce video; do not assume the image path generalises.
TODO(measure)  whether an orphaned creative — created, but its ad call failed — is
               reusable on retry or must be recreated.
```

Order within the stage, one row at a time, writing to the manifest after each step:

```
1  ingest the hosted image into the ad account   ->  image reference
2  create the ad creative                        ->  meta_creative_id
3  create the ad, paused                         ->  meta_ad_id
```

Never batch step 3 across rows and write the ids at the end. One failure then loses
every id while the ads themselves still exist, and the next run has no way to know.

## Copy

Headlines, primary text, descriptions and the CTA come from the user or from
`brand.json`. **Do not generate ad copy here.** Product claims are limited to the
`claims` list on the product — adding "sweetest of the season" to a food ad is a
regulatory exposure, not a creative flourish.

## Errors

```
TODO(measure)  real error codes and verbatim messages for, at minimum:
                 - rejected or unsupported image dimensions
                 - a creative rejected at review time rather than at creation
                 - permission failures on the ad account
                 - rate limiting, and whether it is per-account or per-app
                 - a malformed ad account id, which is the likeliest operator mistake
```

Two classes to keep separate when they land, because the customer's next action differs:

- **Creation failure** — the object does not exist. Safe to fix and retry, once the
  manifest confirms nothing partial was made.
- **Review failure** — the object exists and Meta declined it. Never retry as-is. This
  is a human decision and often a copy or claim problem rather than an image problem.

## Reporting

The customer's review surface is Ads Manager, filtered to paused. Give them the direct
link to that filtered view alongside the contact sheet, and say in the same sentence
that nothing is live and no creative has been visually reviewed by the agent.
