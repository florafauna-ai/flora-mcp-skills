# FLORA MCP Skills

Workflows for pointing your agent at [FLORA](https://flora.ai) and getting real work
back — not just tool access.

FLORA's MCP server gives any agent the ability to generate images, video, audio and
text, run saved multi-step techniques, and read and write a FLORA canvas. That is the
raw capability. **This repo is the judgment layer**: when to use which model, what the
gotchas are, what a good result looks like, and what to do when one comes back wrong.

Every skill here is hand-tested against production. Numbers in them are measured, not
estimated.

---

## Install

One command. FLORA's MCP server is hosted, authenticated over OAuth, and needs no API
key — the first call opens a browser to sign in.

**Claude Code**

```bash
claude mcp add --transport http flora https://agents.flora.ai/mcp
```

**Codex**

```bash
codex mcp add flora --transport http https://agents.flora.ai/mcp
```

**Cursor, Windsurf, Zed, and other MCP clients** — add to your MCP config:

```json
{
  "mcpServers": {
    "flora": {
      "type": "http",
      "url": "https://agents.flora.ai/mcp"
    }
  }
}
```

**ChatGPT** — FLORA is in the app directory; enable it there.

### Then add the skills

The server is the capability; the skills are how your agent knows what to do with it.

**Claude Code — one command, skills and server together.** This repo is also a plugin
marketplace, so installing it wires up the MCP server *and* all four skills:

```bash
claude plugin marketplace add flora-ai/flora-mcp-skills
claude plugin install flora-mcp-skills@flora
```

**Any other agent — copy the skills in:**

```bash
git clone https://github.com/flora-ai/flora-mcp-skills.git
cp -r flora-mcp-skills/skills/* .codex/skills/       # Codex
cp -r flora-mcp-skills/skills/* .cursor/rules/       # Cursor
```

**Or no install at all** — point your agent straight at one skill:

```
Read https://raw.githubusercontent.com/flora-ai/flora-mcp-skills/main/skills/flora-batch-generate/SKILL.md
and follow it for these 40 products.
```

---

## Start here: stop chatting, start batching

The single highest-leverage thing you can do with FLORA's MCP server is **stop treating
it as a chatbot and start treating it as a pipeline.**

One request at a time, waiting for each, is the default an agent falls into and it is
the slowest possible use of the server. FLORA runs generations concurrently. The
serialisation is entirely on the agent's side.

Measured on a real six-item batch: fired together, **15.8 seconds**. The same six run
one after another: about **150 seconds**. Identical credits, identical outputs, one
tenth the wall clock — and the gap widens linearly with the size of your list.

> **[`flora-batch-generate`](skills/flora-batch-generate/SKILL.md) is the flagship skill
> in this repo.** If you read one thing here, read that. It turns a product list, a set
> of campaign variants, a folder of source images, or a spreadsheet into one parallel
> batch, polls it correctly, and tells you exactly what failed and why.

---

## Skills by use case

### Scale — many items, one treatment

| Skill | Use it when |
|---|---|
| **[flora-batch-generate](skills/flora-batch-generate/SKILL.md)** ★ | You have a list — products, SKUs, campaign variants, localisations, scenes — and want one asset per row under a single consistent style. Handles parallel firing, batch polling, per-item variables, partial failure and retry classification. **Start here.** |

### Refine — get one thing right, without burning credits

| Skill | Use it when |
|---|---|
| **[flora-refine-loop](skills/flora-refine-loop/SKILL.md)** ★ | The first result is wrong and you need to drive it to a specific goal — "that's not quite right", "closer, but the X is off". Uses a **free** vision judge to name the defect, changes the prompt to fix it, and stops when the goal is met or the defect stops moving. Reach for this the moment someone is re-running the same prompt hoping for a better roll. |

### Sequence — script to moving pictures

| Skill | Use it when |
|---|---|
| **[script-to-video](skills/script-to-video/SKILL.md)** | You have a script or narrative and want animated clips. Staged pipeline with approval gates — script → shot list → consistent keyframes → motion — because a clip costs 30–90x its keyframe, so a drifted still must be caught before it is animated. Delivers ordered clip URLs, not a finished cut. |

### Transform — you already have the image

| Skill | Use it when |
|---|---|
| **[flora-run-technique](skills/flora-run-technique/SKILL.md)** | You want a saved multi-step FLORA workflow applied to a source image — background swap, relight, upscale, model swap, sketch-to-render. |

### Present — turn finished work into a deliverable

| Skill | Use it when |
|---|---|
| **[flora-mockup-deck](skills/flora-mockup-deck/SKILL.md)** | You have a finished ad creative and need it placed in the world — out-of-home placements, social resizes, and a contact sheet. The artwork is reproduced exactly and never regenerated. |

### Iterate — build on what exists

| Skill | Use it when |
|---|---|
| **[flora-canvas-iterate](skills/flora-canvas-iterate/SKILL.md)** | The user refers to an existing project or canvas — "the hero images from last week", "what's in the Meridian project" — and wants to revise rather than start over. |

★ = flagship, most heavily tested.

---

## What a good skill looks like here

The bar is set by `flora-batch-generate` and `flora-mockup-deck`. Both share a shape,
and it is not "a description of the tools":

- **A law.** One sentence naming the invariant the skill exists to protect.
  *"N items is one wait, not N waits."* *"A re-run with an unchanged prompt is not a
  refinement."* If you cannot write that sentence, the skill is not ready.
- **Measured numbers.** `265ms`, `3.45x`, `17% undercount`, `limit: 100`. Not "fast",
  not "expensive", not "usually works".
- **Named gotchas.** The specific thing that silently ate someone's credits, written
  down with what it looked like when it happened. The most valuable content in this
  repo is the failure someone already paid for.
- **What it does *not* do.** Where the skill stops, stated plainly, so an agent does
  not improvise past its tested edge.

Thin wrappers around tool descriptions are not useful — agents can already read tool
schemas. The value is the judgment that only comes from running it.

---

## Contributing

**Some of the best FLORA workflows are already being built by users, independently of
us.** Two we know of:

- **Pedro Padilla's agentic marketing pipeline** — an end-to-end campaign flow driven
  through the MCP server rather than the canvas.
- **Will Bovill's Figma + FLORA storyboard workflow** — pulling frames from Figma,
  generating against them, and assembling the result back into a board.

Neither started as a feature request. Both are the kind of thing this repo exists to
surface, so that the next person does not have to rediscover it.

If you have built a workflow that works, **[send it back](CONTRIBUTING.md)**. The bar
is the four bullets above, and the process is a pull request.

---

## Reference

- **FLORA MCP endpoint** — `https://agents.flora.ai/mcp` (streamable HTTP, OAuth)
- **API and SDK docs** — the server's own `search_docs` tool, or
  [docs.flora.ai](https://docs.flora.ai)
- **Two ways to call FLORA from a skill:**
  - **Named tools** — `flora_generate`, `flora_run_technique`, `flora_list_models` and
    friends. Simple, one call per action. Best for single-shot work.
  - **`execute`** — runs TypeScript against a pre-authenticated SDK client. Best for
    batches, because a whole fan-out fits in one call. Limits: ~5 minutes per call, 30s
    per HTTP request, and no variables persist between calls.

### Verified against

Every tool name and SDK method used in these skills was checked against the live server.
When a skill stops working, re-check this first — it is the thing that rots.

```
endpoint      https://agents.flora.ai/mcp   (streamable HTTP, Clerk OAuth)
API base      https://app.flora.ai/api/v1
SDK           FLORA/JS 0.10.0               (the version inside the execute sandbox)
tools         14 referenced, all present
SDK methods   generations.create · generations.list · generations.retrieve
              models.list · projects.create · assets.create
              techniques.runs.create · techniques.runs.retrieve
```

Two things that do **not** exist and are easy to reach for: `models.retrieve` (use
`models.list().find()`) and `runs.action` (use the `flora_run_action` tool).

FLORA also ships an in-browser MCP surface (WebMCP) that operates a live canvas
directly. It has a **different, larger tool vocabulary** — `flora_run_batch`,
`flora_get_batch_status`, `flora_get_generations`, `flora_edit_layers` and others — and
these skills do not target it. If you are writing a skill against the browser surface,
check its tool names separately; they are not interchangeable with the hosted server's.

## Licence

MIT. See [LICENSE](LICENSE).
