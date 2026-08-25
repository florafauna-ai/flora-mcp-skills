# Contributing a skill

If you have built a FLORA workflow that reliably works, we want it here. This page is
the whole process.

## What we are looking for

A skill worth adding is one where **someone already paid to learn something.** You ran
it, it broke in a specific way, you found out why, and now you know the thing that is
not in any tool description.

Good candidates:

- A workflow you run repeatedly and have tuned — the model you settled on and why, the
  prompt structure that stopped it drifting, the parameter that quietly ruins it.
- A pipeline that crosses tools — FLORA plus Figma, plus a spreadsheet, plus a CMS.
- A use case we clearly have not covered. Video, audio, and localisation are wide open.

Not useful:

- A restatement of what the tools do. Agents read tool schemas already.
- A prompt with no workflow around it. That is a good prompt, not a skill.
- Something you have run once. The value here is repetition — the second and third runs
  are where the gotchas appear.

## The bar

Every skill in this repo is expected to have all four. `skills/flora-batch-generate/`
and `skills/flora-mockup-deck/` are the reference implementations; read one before you
start writing.

1. **A law.** One sentence naming the invariant the skill protects. *"N items is one
   wait, not N waits."* *"The artwork is reproduced. The world is generated."* If you
   cannot write that sentence, the skill is not ready — you have a procedure, not a
   principle, and an agent will not know when to deviate.

2. **Measured numbers.** `265ms`. `limit: 100`. `0.253 quoted against 0.873 charged`.
   Not "fast", not "cheap", not "usually fine". If you write a number, you should be
   able to say what you ran to get it.

3. **Named gotchas.** The specific failure, what it looked like, and what to do
   instead. *"An unknown param value is accepted, runs, completes and bills at the
   default"* is worth more than a page of best practice. Include the error code and the
   error message verbatim where you have them.

4. **A stated edge.** What the skill does not do, so an agent does not improvise past
   where you tested. Say plainly when something should be a different skill.

## Layout

```
skills/your-skill-name/
  SKILL.md                    required
  reference/*.md              optional — long tables, worked examples, full taxonomies
```

`SKILL.md` opens with YAML frontmatter:

```yaml
---
name: flora-your-skill-name
description: >
  What it does, then when to use it, then when NOT to. The agent decides whether to
  load your skill from this text alone, so it must contain the words a user would
  actually say. End with an explicit "Do not use for …".
---
```

The `description` is the single highest-leverage field in the file. A skill that never
fires is worth nothing, and it fires on this text. Name concrete trigger phrases — the
things a user types — not an abstract category.

Keep `SKILL.md` to the judgment. Push long tables, full error taxonomies and worked
transcripts into `reference/`, and link to them.

## Style

- Prose, short sentences, active voice. One idea per sentence.
- Say *why*, not *what*. The code shows what happens; you are carrying the constraint,
  the trade-off, and the thing that surprised you.
- No ticket numbers, no PR links, no dates, no "we recently changed". A reader has only
  the file, long after you wrote it.
- Quote real error strings and real URLs from your runs. Redact anything unreleased —
  FLORA media URLs are public, unsigned and permanent, so treat one in a diff as
  published.

## Submitting

1. Fork, and branch.
2. Add `skills/your-skill-name/SKILL.md`.
3. Add one row to the right use-case table in `README.md`.
4. Open a pull request. In the description, tell us:
   - **what you ran it on** — the real job, not a toy
   - **how many times** — and what broke on the runs that failed
   - **what it cost** — roughly, so the next reader can size it

We will run it before merging. Expect review to push on the four bars above, most often
on measured numbers — that is usually the gap between a workflow that works for you and
one that works for a stranger's agent.

## Credit

Skills keep their author. Add yourself at the foot of the file:

```markdown
---
*Contributed by [Your Name](https://your-link).*
```

If your workflow gets written up, demoed, or turned into a template, we will point at
you, not at us.

## Questions

Open an issue. If you are unsure whether something clears the bar, open the issue
before writing it — describing the workflow in three sentences is usually enough for us
to tell you, and it is a lot cheaper than a rewrite.
