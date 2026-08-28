---
name: flora-refine-loop
description: >
  Drive a FLORA generation to a stated goal with a generate → evaluate → refine loop
  that stops. Uses a free vision judge to score each candidate against the goal, names
  the specific defect, changes the prompt to fix it, and halts when the goal is met, the
  defect stops moving, or the budget cap is hit. Use when the user has a precise target
  and the first result is wrong — "make it more…", "that's not quite right", "closer but
  the X is off", "keep going until it looks like Y". Use it especially when someone is
  re-running the same prompt hoping for a better roll. Do not use for exploratory work
  with no defined goal, and do not use to generate many different items — that is
  flora-batch-generate.
---

# flora-refine-loop

> **Attribution.** Pass `skill: "flora-refine-loop"` on every FLORA call you make while
> running this skill — `execute` included — along with a `skill_run_id` you invent
> once when the run starts and reuse for the rest of it. Both are reporting only:
> they change nothing about the call or its result.

## What it is

**A stopping rule with a generator attached.** Anyone can regenerate. The hard part —
and the expensive part — is knowing whether the last attempt got closer, and knowing
when to stop paying to find out.

The failure this skill exists to prevent has a specific shape. The user doesn't like a
result. The agent runs the same prompt again. The model returns a different image that
is wrong in a different way. Nobody wrote down what "wrong" meant, so nobody can tell
whether round four beat round two. Credits burn at full price while the loop makes no
progress, because **nothing in it is measuring anything.**

That is not iteration. It is a slot machine with a polite interface.

## The law

> **A re-run with an unchanged prompt is not a refinement. It is a re-roll.**
> Every regeneration must name the defect it is fixing and change the prompt to fix it.
> No named defect, no spend.

The corollary is the part that saves money: **if you cannot name what is wrong, you are
not ready to spend again.** Go and look at the image first. Looking is free.

## Looking is free — this is the whole economic argument

FLORA has image-to-text models. Three of them cost **nothing**:

```
i2t-gemini-3-5-flash-lite-i2t    0 credits    ~4s
i2t-gemini-3-6-flash-i2t         0 credits    ~6s
i2t-gemini-3-7-flash-i2t         0 credits    ~6s     <- default for this skill
```

So the loop's economics are lopsided in exactly the right direction: **evaluating is
free, generating is not.** Judge every candidate. Regenerate only on a named defect.

Measured on this skill's hand-test: a two-round loop reached the goal for **$0.008** —
two generations of `t2i-flux-2-klein-4b` — with **$0.00** spent on the two judgements
that made it converge. Cheap models exist for the generator too; use them while the
*prompt* is still being tuned and switch to the expensive one only once the loop passes.

If a judge needs to be better than free, `i2t-gemini-3-flash` and
`i2t-claude-sonnet-4-6-vertex-i2t` are 8 credits (~$0.008). Do not reach for
`i2t-gpt-5-5-i2t` (100 credits) or `i2t-openai-o3-deep-research` (900 credits, 10
minutes) — a judge that costs more than the generation defeats the point.

## The one thing that silently breaks this entire skill

> **For `i2t` models the image parameter is `image_urls` — plural, an ARRAY.**
> `params.image_url` (singular string) is accepted without complaint, **silently
> ignored**, and the model answers having seen nothing.

**This is the opposite of the `i2i` convention**, where `image_url` singular is the
mechanism and the plural array is the one that gets dropped. The two families disagree,
and nothing warns you.

Measured. Asked to describe an image, with an explicit instruction to say `NO IMAGE
RECEIVED` if it could not see one:

```
params: { image_url: "<dripper>" }       -> "NO IMAGE RECEIVED."
params: { image_urls: ["<dripper>"] }    -> "a matte black pour-over coffee carafe
                                            and dripper set … neutral beige background"
```

The danger is not the error. There is no error. The danger is that **a blind judge is
an agreeable judge.** Before this was found, the judge was handed a photo of a black
ceramic coffee dripper and a goal describing *a brushed steel water bottle lying on a
wooden table in hard sunlight with a visible logo*, and returned:

```json
{"verdict":"pass","defects":[],"fix_instruction":""}
```

A refine loop built on that does not merely fail — it certifies. It reports passes it
never saw, and it does so in confident structured JSON. **Verify the judge can see
before trusting a single verdict** (there is a smoke test below).

## The loop

Four steps. Steps 2 and 3 are free.

```
1  GENERATE   one candidate            costs credits
2  JUDGE      against the written goal free
3  DECIDE     pass · refine · stop     free
4  REFINE     change the prompt, once  → back to 1
```

### 0. Write the goal down first

The loop cannot start without a goal specific enough to fail against. "Make it look
better" is not a goal; it is a mood. Convert it into checkable clauses:

```
GOAL: A single white ceramic mug on a plain black surface. The mug handle points to
the RIGHT. Top-down bird's-eye view looking straight down. No other objects, no text.
```

Every clause is something a judge can rule on. If the user's brief has no such clauses,
**ask one question to get them** rather than starting a loop that cannot terminate.
Agree the budget cap in the same breath: *"I'll give this up to 3 rounds, about $0.03.
Stop me sooner?"*

### 1. Generate

One candidate. Not four. A batch of variants is a different tool — this loop learns
from each result, and firing four at once throws that away.

### 2. Judge — describe before ruling

```ts
const judge = async (client, url, goal) => {
  const r = await client.generations.create({
    workspace_id: WS, project_id: PRJ, type: "text",
    model: "i2t-gemini-3-7-flash-i2t",
    params: { image_urls: [url] },              // PLURAL. ARRAY. See above.
    prompt:
      `Strict QA judge. First DESCRIBE what you see, then compare to the GOAL, then rule.\n\n` +
      `GOAL: ${goal}\n\n` +
      `Return ONLY JSON, no fence:\n` +
      `{"observed":"...","verdict":"pass"|"fail",` +
      `"defects":["concrete mismatch vs the goal"],` +
      `"fix_instruction":"one concrete PROMPT change that fixes the biggest defect, else empty"}`,
  })
  const g = await poll(r.run_id)
  return JSON.parse(String(g.outputs?.[0]?.url ?? "{}").replace(/```json\s*|```/g, "").trim())
}
```

**`observed` must come before `verdict` in the schema, and the prompt must demand the
description first.** This is not decoration. Asking for a verdict first lets the model
answer from the goal text alone; making it describe the pixels first forces the
comparison to actually happen. With the ordering in place the judge caught a softbox
edge intruding into a frame that looked clean to the eye.

**Always strip markdown fences.** The same model returns bare JSON on one call and
` ```json ` fenced on the next, with no change to the prompt. Parse defensively or the
loop dies on a formatting coin-flip.

**Judge output is text, and text arrives in `outputs[0].url`.** The field is named
`url` for every modality — for `type: "text"` it holds the content itself, not a link.

### 3. Decide

```
verdict == "pass"                          -> STOP. Deliver.
new, nameable defect + a prompt change     -> REFINE. Spend again.
same defect as last round                  -> STOP. Escalate to the user.
round == budget cap                        -> STOP. Report the best candidate.
```

The third line is the one that saves the money. **A defect that survives a genuine
prompt change is a model limitation, not a bad roll.** Spending another round on it buys
a differently-wrong image. Say so plainly and hand the decision back:

> Three rounds in, the handle still points left. The prompt says right each time, so
> this model isn't following it. Options: try `t2i-seedream-v4`, accept round 2, or
> mirror the image with a free action.

### 4. Refine

Feed `fix_instruction` back into the prompt. One defect at a time — fixing the biggest
one often resolves the others, and fixing three at once means you learn nothing about
which change worked.

Measured, the hand-test:

```
round 1   "a white ceramic mug on a black surface"
          -> fail: "camera angle is a side view rather than top-down"
          -> fix:  "Capture the mug from a direct top-down overhead perspective"

round 2   "a white ceramic mug on a plain black surface, handle pointing right.
           Capture the mug from a direct top-down overhead perspective looking
           straight down."
          -> pass: 0 defects
```

Two rounds. $0.008. The second prompt is the first prompt plus the judge's sentence.

## Do not build the stop condition on similarity

The intuitive design — *compare the new image to the old one and stop if they are
near-duplicates* — **fails open**, and it fails open in the direction that costs money.

The judge does compare two images correctly; pass two URLs in the array and it will
describe both and rule. But asked whether two generations *of an identical prompt* were
near-duplicates, it said **no** both times:

```
same prompt, same seed   -> near_duplicate: false
                            "Image 1 includes a stem with two green leaves,
                             while Image 2 shows only a bare lemon"
same prompt, no seed     -> near_duplicate: false
                            "presented from different angles and orientations"
```

Both answers are literally true and completely useless. Two re-rolls are never
pixel-identical, so a similarity gate always returns "different" and always authorises
another spend. **That is the credit burn, re-implemented as a safety check.**

Ask the defect question instead: *"is the specific defect from last round still
present?"* That is binary, grounded in the goal, and it converges.

**Seed will not save you either.** Two runs with an identical prompt and an identical
`seed: 424242` produced visibly different images — one lemon with leaves, one without.
Seed is not a reliable pin on this endpoint, so "same seed, so it'll be the same image"
is not a safe assumption to build a loop on.

## Smoke-test the judge before the first paid round

Free, four seconds, and it is the difference between QA and theatre:

```ts
// Expect a real description. "NO IMAGE RECEIVED" means the param name is wrong.
params: { image_urls: [url] },
prompt: "Describe the main object and the background colour in one sentence. " +
        "If you cannot see an image, reply exactly: NO IMAGE RECEIVED."
```

Run this once per session against the first candidate. If it comes back blind, every
verdict after it is fiction.

## Gotchas

```
THE JUDGE
image_urls            PLURAL ARRAY for i2t. Singular image_url is silently ignored and
                      the model answers blind — agreeably. Inverts the i2i convention.
same url twice        [A, A] is de-duplicated to ONE image; the model reports image 2
                      as missing. You cannot self-compare this way.
describe first        demand `observed` before `verdict`, or the judge rules from the
                      goal text and rubber-stamps.
markdown fences       appear inconsistently on identical prompts. Always strip before
                      JSON.parse.
text output           lands in outputs[0].url — the field is `url` for every modality.
free judges           gemini 3.5-flash-lite / 3.6-flash / 3.7-flash are 0 credits.
                      Never use o3-deep-research (900 credits, ~10 min) as a judge.

THE LOOP
one candidate         per round. Four at once discards the thing that makes this a loop.
one defect            per refinement. Fixing three at once teaches you nothing.
budget cap            agreed with the user BEFORE round 1, and enforced.
same defect twice     is a model limitation. Stop and escalate; do not re-roll.
seed                  same prompt + same seed produced different images. Not a pin.

SANDBOX
split the rounds      a full loop (generate + judge + generate + judge) can exceed the
                      code sandbox gateway and return a 502. Run one round per execute
                      call, returning the candidate url and the judgement each time.
                      Variables do not persist — carry the goal and the defect forward
                      explicitly.

COST
judge free, gen paid  so judge everything and generate reluctantly.
cheap while tuning    t2i-flux-2-klein-4b is $0.004. Tune the prompt on it, then run
                      the final pass on the expensive model. GPT Image 2 is $0.873 —
                      220x — and a loop run on it is where the complaint comes from.
charged_cost          is eventually consistent; re-read after the loop to total it.
```

## Reporting back

Show the trajectory, not just the winner. The rounds are the evidence that the spend
bought progress.

```
ROUND  VERDICT  DEFECT                                  COST
1      fail     side view, not top-down                 $0.004
2      pass     —                                       $0.004

Goal met in 2 rounds. Total $0.008 (judging was free).
https://media.flora.ai/…
```

If the loop stopped without passing, say which of the three stop conditions fired and
what the surviving defect was. **Never present a capped-out loop as a success**, and
never quietly deliver round 5 when round 2 was better — if an earlier candidate scored
higher, deliver that one and say so.

**You cannot see the images yourself.** Every judgement in the report came from the
vision model, so attribute it that way and let the user overrule it. The judge is a
fast, free second opinion, not the client.
