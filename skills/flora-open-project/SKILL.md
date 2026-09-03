---
name: flora-open-project
description: Open a specific FLORA project canvas and get oriented before doing work — sign an in-harness browser into the canvas with WebMCP when the agent has one, otherwise work through the hosted MCP tools, then read the canvas and propose what to do next. Use when the user names a workspace and project ("open my Meridian project", "let's work on this canvas"), pastes a canvas link, or arrives from FLORA's "Open in agent" button. Do not use to create a new project.
---

# Open a FLORA project

**The law: the sign-in link is a session, not a URL.** It opens once, in a tab
the agent controls, and appears nowhere else — not in a reply, not in a log.

Starting point for a session on one canvas. Ends with the canvas in front of
the agent (in its own browser tab or via the hosted tools) and a short offer of
what to do next, so the user's first real request lands on a canvas the agent
has already read.

**Input:** a workspace id (`ws_…`) and a project id (`prj_…`).
**Output:** the canvas open and read, plus starter or continuation ideas.

## Steps

1. **Get the ids.** Both a workspace id and a project id are required before
   anything else. If the user gave a canvas URL, the project id is the
   `/projects/<id>` segment, prefixed `prj_`. If either is missing, resolve it:
   `flora_list_workspaces`, then `flora_list_projects` with the workspace, and
   match on the user's wording. Ask if the match is ambiguous; never create a
   project here.

2. **Check for an in-harness browser with WebMCP.** Some hosts give the agent
   its own browser tab and a JavaScript tool (Claude Code Desktop and Claude
   Cowork do; others may). The test is capability, not host name: can you open
   a URL in a tab you control *and* run JavaScript in that page? If yes, take
   the browser path; if no, take the hosted path. Do not guess — a host that
   only has a fetch/HTTP tool has no browser.

3. **Browser path.** Call `flora_open_project` with the project id and, if the
   user asked for a specific session length, `session_hours` (1–24, default 8).
   Open the returned `url` in a new tab. It signs you in as the user and lands
   on the canvas with `?webmcp_embed=1`. Rules that follow from that:
   - The link works exactly once and acts as the user for the whole session:
     never print it, paste it into a reply, or reload it. Navigate within the
     tab instead, and keep `webmcp_embed=1` on the URL.
   - Drive the canvas only through the in-page tools on
     `navigator.modelContext`. List them with
     `navigator.modelContext.listTools().map(t => t.name)`. Calls are async and
     the JavaScript tool may not await, so stash and poll:
     `window.__r = {}; navigator.modelContext.callTool({name: "flora_get_canvas", arguments: {}}).then(x => window.__r.a = x)`
     then read `window.__r.a` (`structuredContent` holds the parsed result).
   - Typical flow: `flora_get_canvas` → `flora_add_nodes` → `flora_generate`
     (pass `expected_project_id`) → `flora_wait_for_generation`.
   - `spend_approval_pending` means an approval dialog is open in the tab; only
     the user can accept it. Ask them, then retry.
   - Do not attach a separate FLORA pane or use look-alike plugin tools
     (`flora_show_canvas`, `flora_pane_*`); the tab is the canvas.

4. **Hosted path.** Tell the user in one sentence how you are working: through
   FLORA's hosted MCP, so every change lands in their real project and they can
   watch it at the project's `canvas_url` (from `flora_get_project`). Then use
   the `flora_*` tools as usual.

5. **Read the canvas.** `flora_get_canvas` for the graph; on the hosted path add
   `flora_list_canvas_nodes` for media and asset URLs. Say what is there in a
   sentence or two — node count, what kinds of media, any obvious workflow.

6. **Offer next steps.**
   - **Blank canvas:** offer two or three concrete starters. Draw on what you
     already know about the user and their work (their brand, product, recent
     requests) first. If you know nothing about them, call
     `flora_discover_skills` without a name and offer the two or three skills
     that fit best, each as a one-line prompt they could type.
   - **Existing content:** offer exactly two ways to continue the work that is
     already there, grounded in what you read — extend a workflow, resize or
     restyle an existing asset, fill a gap the graph suggests. Name the nodes
     you mean so the user can confirm.

   Then stop and wait. Do not generate anything before the user picks.

## Rules

- **Ids first.** No canvas read, no link, no ideas until both ids are known.
- **The link is a secret.** It is a signed-in session as the user. It goes into
  a browser tab you control and nowhere else.
- **Read before proposing.** Ideas come from the canvas and the user, not from
  the tool list.
- **Generation spends credits.** Quote a cost before running anything the user
  picks.
