---
name: flora-trend-board
description: Scan a fixed set of trend sources on a schedule, score which signals are actually moving, and render the strongest ones as generated mood boards posted into a team channel. Use for daily or weekly trend scans in footwear, apparel, fashion, beauty, interiors, furniture, automotive or any category with a visual trend cycle — colourway shifts, silhouette and form moves, material and finish direction, competitor launches, and cultural moments. Trigger on "what's moving in [category]", "trend scan", "trend report", "competitor watch", "mood board of what's happening", "keep the design team plugged in", "daily trend digest", or a request to replace a written trend report nobody reads with something visual. Also use when setting up the source list for a new client or vertical, when the boards are coming back samey, or when the scan is posting noise. Do not use for a one-off mood board with no source set behind it — that is a plain generation, and this skill is the scan, not the picture. Do not use to judge finished work against a brand standard, which is flora-brand-consistency-audit, and do not use it to place a finished creative into the world, which is flora-mockup-deck.
---

# Trend scan → mood board

Replaces the weekly trend report nobody reads. Scans a named source set, ranks signals by how fast they are moving rather than how interesting they sound, and renders the top ones as generated mood boards in the channel the design team already lives in.

The design team's job is to react to the boards. Nobody should have to open a document.

## What this supplies

The source set, the velocity scoring that decides what surfaces, and the divergence rule that stops four boards from looking like one board four times. Without those you get an RSS reader that renders pictures.

## 1. Source set

**This is client-specific and must be built before the first run.** A generic source list produces generic trends. Build roughly 25 sources across five tiers — the tier mix is what makes the scan early rather than late:

| Tier | What it catches | Roughly |
| --- | --- | --- |
| **Origin** — runway, trade shows, material fairs, design weeks, patent and colourway filings | signals 2–4 seasons out | 5 |
| **Trade** — category press, industry newsletters, forecasting services | signals this season | 5 |
| **Competitor** — direct competitors' product pages, drops, campaign feeds | what rivals committed to | 6 |
| **Retail** — the accounts that actually stock the category, resale and marketplace movers | what is selling now | 5 |
| **Culture** — subculture forums, athlete/creator accounts, music and film adjacency | why any of it is happening | 4 |

Rules:
- Name every source with a URL. "Fashion blogs" is not a source.
- Confirm each one is reachable before the first run; a source that 403s silently becomes a blind spot the scan never reports.
- A list weighted to Retail and Culture reports what is already mainstream. If the client wants early, Origin and Competitor carry the weight.
- Record why each source is on the list. Sources get stale and this is what lets someone prune it later.
- Record **how** each source is read, not only its URL. See below — for most of the list, a plain fetch is not the answer.

### Most of a good source list will not answer a plain fetch

**Measured, building a 25-source footwear list from scratch: 15 reachable, 10 not.**
Plain `curl`, following redirects, browser user-agent. The failures were not spread
evenly:

| Tier | Reachable | What blocked |
| --- | --- | --- |
| Origin | 5/5 | — |
| Trade | 5/5 | — |
| **Competitor** | **2/6** | 403, 403, 403, 406 |
| **Retail** | **2/5** | 403, 403, 404 |
| **Culture** | **1/4** | 403, 403, connection timeout |

Editorial publishes to be read by machines. Commerce and community do not. Brand
product pages, resale marketplaces and forums sit behind bot protection as their
default posture, so **the two tiers that carry an early signal are the two that
fail**, and the tier mix that survives a naive build is the one weighted to Trade —
which is the mix the skill above tells you not to build.

This is the starting state, not a degradation. Do not read a 60% reachable list as
a list that broke; read it as a list that was never wired.

Per blocked source, in order of preference:

1. **A feed or an endpoint.** Many walled sites publish an unwalled one — a brand
   newsroom RSS instead of the drops page, a forum's JSON endpoint instead of its
   HTML. Prefer these; they are stable and intended for this.
2. **An official API,** where the category has one.
3. **A rendered fetch** through a headless browser, which clears most 403s because
   the block is on the client, not on you.
4. **Substitute the source.** A competitor covered by a trade title you can already
   read is worth more than one you cannot read at all.
5. **Drop it and say so.** A named gap beats a silent one.

Record the chosen method beside the URL. A source that needs a rendered fetch and
gets a plain one returns 403 forever, and the scan reports nothing rather than
reporting a problem.

## 2. Signal extraction

From each source, pull signals in these classes only. Anything that does not fit a class is noise:

- **Colourway** — a colour or combination appearing where it did not before
- **Silhouette / form** — proportion, volume, sole geometry, cut
- **Material / finish** — textile, texture, treatment, hardware
- **Competitor move** — a launch, collab, reposition, or price move
- **Cultural moment** — an event, person, or subculture pulling the category

Each signal carries: class, one-line description, source, first-seen date, and a representative image URL where one exists.

## 3. Velocity scoring — the actual judgment

Rank by movement, not by interest. For each signal:

- **Spread** — how many *independent* sources carry it in the current window. Three sources syndicating one press release is one source.
- **Acceleration** — mentions this window vs the previous window. Flat is not a trend.
- **Tier depth** — a signal appearing in Origin *and* Retail is further along than one appearing in Origin alone. Note which tiers it has reached.
- **Direction** — accelerating, plateau, or decaying. Decaying signals still matter: a colour dying is a decision.

Surface the top four by acceleration × tier depth. Say the score alongside each board — a board with no number attached is a mood, not a signal.

Discard: single-source signals, anything already reported in the last three runs unless its direction changed, and anything the client's own product line already ships.

## 4. Four prompts, four different lenses

The failure mode of this skill is four prompts written off the same digest that generate four near-identical boards. Prevent it structurally: **each prompt takes a different lens, and each takes a different signal.** Never four takes on one trend.

Assign one lens per prompt, no repeats in a run:

1. **Material close-up** — the texture, weave, treatment or finish, shot as a detail, with swatches and samples in frame.
2. **In context / on body** — the product being used, worn, or lived with, in the environment the trend belongs to.
3. **Studio desk** — the flat-lay of the design process: sketches, spec sheets, samples, tools, colour chips on a work surface.
4. **Cultural scene** — the moment, place, or subculture driving it, with the product incidental rather than hero.

Write each prompt fully — subject, lens, lighting, palette, surface, framing — as a standalone generation prompt. Include the trend's actual colour values and material names; a prompt that says "trending colours" generates last year's.

Before firing: read the four prompts side by side. If two could be swapped without anyone noticing, one is wrong — rewrite it, do not regenerate it.

**State the lens as what is in frame, never as what is not.** Measured: a material
close-up prompt ending "no full shoe visible" returned a full shoe, centred, as the
hero. The negative was ignored and the lens collapsed onto the same product shot the
other three lenses produce — which is the exact failure this section exists to
prevent, arriving through the prompt rather than through the digest.

Write the frame instead. "Macro detail, the weave filling the frame, swatches and a
brass rule beside it, shot at 100mm" leaves no room for a product hero without
saying the word product. A lens described by exclusion is a lens the model is free
to ignore.

## 5. Generate and assemble

Fire the four prompts concurrently through the FLORA MCP — four together is roughly the time of one, sequentially it is four times the wait. Quote the run cost before the first scheduled run so nobody discovers the daily spend at month end.

Assemble as one board per signal, each labelled with: trend name, class, velocity score, tiers reached, and the sources it came from. The label is what makes it actionable — an unlabelled mood board is decoration.

## 6. Deliver

Post into the channel the team already uses — Slack, Teams, or wherever the design conversation happens. Image first, text underneath, sources as links. Nobody opens an attachment.

**Post nothing when nothing moved.** A scan that posts every day regardless trains the channel to scroll past it. Silence on a quiet day is what keeps the loud days credible.

## 7. Cadence and staleness

Daily suits fast categories (footwear, streetwear, beauty); weekly suits slower ones (interiors, furniture, automotive). Match the cadence to how fast the category's signals actually change, not to how often someone wants an update.

The failure of this type is silent staleness — the scan runs, the boards render, and they are quietly wrong. Check every run:

- **Source reachability.** Count sources that returned content, against the count that worked on the day you built the list — not against the number of URLs. A drop from 25 to 19 with no error is the failure this skill dies of; a list that only ever answered 15 of 25 is a different failure, and it happened before the first run.
- **New-signal count.** Zero new signals across 25 sources means the scan broke, not that the category stopped.
- **Repeat rate.** The same trend surfacing four runs running means the scoring window is too wide or the discard rule is not firing.
- **Board divergence.** If the four boards in a run look alike, the lens assignment was not enforced.

## Setting this up for a new client

1. Build the source set with the client, tier by tier. This is a working session, not a task — the design team knows their Origin sources and you do not.
2. Confirm every URL resolves.
3. Run once manually and review the four boards together with the team. Wrong boards here mean the source mix is wrong, not the prompts.
4. Agree the cadence, the channel, and the run cost.
5. Schedule it, and hand over the source list as an editable document. If they cannot add and remove sources without you, this is not installed — you are the trend service.
