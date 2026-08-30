# flora-mockup-deck / pdf

A paginated PDF assembler for the placement deck, for surfaces that have a
filesystem.

`SKILL.md` is written for the MCP-only surface, where there is no disk and the
deliverable is a contact-sheet url: *"when a real paginated PDF is required, say
plainly that this surface returns images and the user can assemble them."* In
Claude Code there **is** a disk, so this assembles them.

It changes nothing about how the deck is produced. The placements and resizes
are still made by the skill — this only lays the finished urls out on pages, in
the structure `SKILL.md` specifies.

## Use

```bash
pip install -r requirements.txt

cp assets.example.json assets.json     # fill in from flora_list_canvas_nodes
python fetch_assets.py                 # -> src/
python map_assets.py                   # proposes roles; merge into manifest.json
python build_deck.py                   # -> out/flora-placement-deck.pdf
python build_deck.py --check           # which assets resolved
```

Any unmapped or missing asset renders as a labelled placeholder frame, so the
deck always builds — useful for reviewing layout before the imagery lands.

`map_assets.py` identifies the four social formats by aspect ratio (16:9, 1:1,
4:5, 9:16) and lists the remaining landscape photographs for manual assignment,
since only the imagery distinguishes a hoarding from a billboard.

## Structure it builds

Six pages, 1280×720pt (16:9), following `SKILL.md`:

| page | content |
|---|---|
| 1 | Cover — plate one side, standfirst the other, spec strip: CREATIVE / SOURCE / PLACEMENTS / SOCIAL. The standfirst states the law. |
| 2–5 | One placement each. Image left at 70%; right column carries SHOT / LIGHT / MOMENT and one line of plain observation. |
| 6 | Social — master and three resizes at **matched width, bottom-aligned**, captioned by USE with the ratio right-aligned. |

Two things in here are load-bearing, both called out in `SKILL.md`:

**Matched width, not matched height.** The social page sizes every crop to one
width and lets the heights climb off a shared bottom edge, so the staircase
shows you that 9:16 is tall and 16:9 is a letterbox. Height-matching flattens
all four to nearly the same width and quietly destroys the one thing the page
exists to demonstrate — while still looking like a finished layout. Width is
solved off the tallest crop (9:16), so vertical space binds, not horizontal.

**Unbranded chrome.** No mark or client name in the furniture; the skill is a
generalist placement engine that runs on any poster for any client.

## Notes

- `assets.json` is gitignored. Canvas media urls are public, unsigned and
  permanent, so committing them to this public repo would disclose unreleased
  creative.
- `media.flora.ai` must be reachable. On a sandboxed runner it may be blocked by
  the egress policy, in which case `fetch_assets.py` reports the 403 and the
  deck still builds with placeholders.
- SHOT / LIGHT / MOMENT are deck copy. The generation runs do not store the
  prompts, so on an existing canvas these have to be written from the briefs you
  used, or read off the photographs — they are not recoverable from the API.
