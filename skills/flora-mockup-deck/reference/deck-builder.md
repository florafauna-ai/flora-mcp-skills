# The deck builder

`build_mockup_deck.py` — packs a mockup-deck run into an A4-landscape annotated PDF.
Write this file out beside the deliverables and run it there; it resolves image paths
relative to `deck.json`.

```bash
cd <project>/Deliverables
curl -O <each placement url>          # media urls need no credentials
python3 build_mockup_deck.py deck.json
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless \
  --disable-gpu --no-pdf-header-footer --print-to-pdf="Your-Deck.pdf" \
  --virtual-time-budget=25000 "file://$PWD/out.html"
```

Images are inlined as data URIs, so the HTML is self-contained and the PDF has no
external dependencies — it survives being moved, and Chrome never races a file read.

**Every section is conditional on its files existing.** A run that lost one placement
still builds a valid deck; drop the missing file in and re-run. It re-renders in about
two seconds, so a layout tweak never costs a regeneration.

**It targets python 3.9**, which is what macOS ships — hence the
`from __future__ import annotations` at the top. Do not remove it and do not reach for
3.10-only syntax; the script has to run on a stock machine with nothing installed.
`PIL` is not required.

## Verified

Rendered on a four-placement, four-resize set: **6 pages** — cover, four placements,
social. The social page was read back as an image to confirm the crops come out at
matched width on a shared bottom edge with heights climbing left to right, which is the
one thing that page exists to demonstrate.

## The script

```python
#!/usr/bin/env python3
"""Pack a mockup-deck run into an A4-landscape annotated PDF.

Usage:  python3 build_mockup_deck.py deck.json   ->  writes out.html beside it

Then render:
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless \
      --disable-gpu --no-pdf-header-footer --print-to-pdf="out.pdf" \
      --virtual-time-budget=25000 "file://$PWD/out.html"

deck.json:
{
  "title":       "Your Agents Joined",
  "standfirst":  "One paragraph. MUST say the creative is reproduced, never regenerated.",
  "project_url": "https://app.flora.ai/projects/prj_...",
  "project_id":  "prj_...",
  "date":        "2026-08-30",
  "creative":    {"file": "master.png", "px": "2048 x 1152", "ratio": "16:9",
                  "source": "SUPPLIED"},
  "placements":  [{"site": "GABLE END", "file": "gable.png",
                   "shot":  "85mm, compressed from down the road",
                   "light": "overcast, wet road holding reflection",
                   "moment":"one person stopped on the opposite kerb",
                   "note":  "One sentence of plain observation.",
                   "node_url": "https://app.flora.ai/projects/prj_...?focus=<node_id>"}],
  "social":      [{"use": "MASTER", "ratio": "16:9", "file": "master.png"},
                  {"use": "FEED",   "ratio": "1:1",  "file": "feed.png"}]
}

Every section is conditional on its files existing, so a partial set still builds a
valid deck. Drop a missing placement in and re-run; it re-renders in about two seconds,
so a layout tweak never costs a regeneration.
"""

from __future__ import annotations  # macOS ships python 3.9; keeps `str | None` legal

import base64
import html
import json
import mimetypes
import pathlib
import sys

# A4 landscape, in mm.
PAGE_W, PAGE_H = 297.0, 210.0
MARGIN = 14.0
FOOTER_H = 12.0
USABLE_W = PAGE_W - 2 * MARGIN
USABLE_H = PAGE_H - 2 * MARGIN - FOOTER_H


def embed(path: pathlib.Path) -> str | None:
    """Inline an image as a data URI so the PDF has no external dependencies."""
    if not path.exists():
        return None
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode()


def esc(s: object) -> str:
    return html.escape(str(s or ""))


def ratio_to_hw(ratio: str) -> float:
    """'9:16' -> 16/9, the height-per-unit-width multiplier."""
    try:
        w, h = (float(n) for n in ratio.replace("x", ":").split(":"))
        return h / w if w else 1.0
    except (ValueError, ZeroDivisionError):
        return 1.0


def footer(deck: dict, n: int) -> str:
    """PROJECT and DATE are the only parameters in the chrome."""
    url, pid = deck.get("project_url"), deck.get("project_id")
    if url:
        project = f'<a href="{esc(url)}">{esc(pid or url)}</a>'
    else:
        project = esc(pid or "—")
    return (
        f'<div class="ftr"><span>PROJECT {project}</span>'
        f'<span>{esc(deck.get("date", ""))}</span><span>{n}</span></div>'
    )


def cover(deck: dict, root: pathlib.Path, n: int) -> str:
    cre = deck.get("creative") or {}
    src = embed(root / cre["file"]) if cre.get("file") else None
    spec = [
        ("CREATIVE", deck.get("title", "")),
        ("SOURCE", " · ".join(x for x in (cre.get("source"), cre.get("px"), cre.get("ratio")) if x)),
        ("PLACEMENTS", str(len(deck.get("placements") or []))),
        ("SOCIAL", " · ".join((s.get("ratio", "") for s in deck.get("social") or [])) or "—"),
    ]
    rows = "".join(
        f'<div class="spec-row"><span class="k">{esc(k)}</span>'
        f'<span class="v">{esc(v)}</span></div>'
        for k, v in spec
        if v
    )
    plate = f'<div class="cover-plate"><img src="{src}"></div>' if src else ""
    return f"""<section class="page cover">
  <div class="cover-txt">
    <h1>{esc(deck.get("title", "Untitled"))}</h1>
    <p class="standfirst">{esc(deck.get("standfirst", ""))}</p>
    <div class="spec">{rows}</div>
  </div>
  {plate}
  {footer(deck, n)}
</section>"""


def placement(deck: dict, p: dict, root: pathlib.Path, n: int) -> str:
    src = embed(root / p["file"])
    if not src:
        return ""
    brief = "".join(
        f'<div class="brief-row"><span class="k">{k}</span>'
        f'<span class="v">{esc(p.get(k.lower()))}</span></div>'
        for k in ("SHOT", "LIGHT", "MOMENT")
        if p.get(k.lower())
    )
    note = f'<p class="note">{esc(p["note"])}</p>' if p.get("note") else ""
    link = (
        f'<a class="node" href="{esc(p["node_url"])}">open on canvas</a>'
        if p.get("node_url")
        else ""
    )
    return f"""<section class="page place">
  <div class="place-img"><img src="{src}"></div>
  <div class="place-col">
    <h2>{esc(p.get("site", ""))}</h2>
    <div class="brief">{brief}</div>
    {note}
    {link}
  </div>
  {footer(deck, n)}
</section>"""


def social(deck: dict, root: pathlib.Path, n: int) -> str:
    """Matched WIDTH, bottom-aligned on a shared baseline. Heights climb.

    Size off the tallest crop. With matched width W the stack is W * (h/w) tall, so W
    is bounded twice: by the row across, and by the vertical space under the header.
    Solve the vertical first -- running the 9:16 off the bottom is the failure mode
    here, not running out of width.
    """
    items = [s for s in (deck.get("social") or []) if embed(root / s.get("file", ""))]
    if not items:
        return ""
    gap, head = 8.0, 26.0
    tallest = max(ratio_to_hw(s.get("ratio", "1:1")) for s in items)
    w_across = (USABLE_W - gap * (len(items) - 1)) / len(items)
    w_down = (USABLE_H - head) / tallest
    w = min(w_across, w_down)
    cells = "".join(
        f'<div class="cell" style="width:{w:.2f}mm">'
        f'<img style="width:{w:.2f}mm" src="{embed(root / s["file"])}">'
        f'<div class="cap"><span class="use">{esc(s.get("use"))}</span>'
        f'<span class="ratio">{esc(s.get("ratio"))}</span></div></div>'
        for s in items
    )
    return f"""<section class="page social">
  <h2>SOCIAL</h2>
  <div class="row" style="gap:{gap}mm">{cells}</div>
  {footer(deck, n)}
</section>"""


CSS = f"""
@page {{ size: A4 landscape; margin: 0; }}
* {{ box-sizing: border-box; }}
body {{ margin: 0; font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
        color: #17150f; background: #fff; -webkit-print-color-adjust: exact; }}
.page {{ position: relative; width: {PAGE_W}mm; height: {PAGE_H}mm;
         padding: {MARGIN}mm {MARGIN}mm {MARGIN + FOOTER_H}mm; overflow: hidden;
         page-break-after: always; }}
.page:last-child {{ page-break-after: auto; }}
img {{ display: block; max-width: 100%; max-height: 100%; object-fit: contain; }}

.ftr {{ position: absolute; left: {MARGIN}mm; right: {MARGIN}mm; bottom: 7mm;
        display: flex; justify-content: space-between; font-size: 7.5pt;
        letter-spacing: .08em; color: #8a8478; border-top: .3mm solid #ddd8cd;
        padding-top: 2mm; }}
.ftr a {{ color: #8a8478; text-decoration: none; }}

.cover {{ display: flex; gap: 12mm; align-items: center; }}
.cover-txt {{ width: 40%; }}
.cover-plate {{ width: 60%; height: 100%; display: flex; align-items: center; }}
h1 {{ font-size: 30pt; line-height: 1.05; margin: 0 0 6mm; letter-spacing: -.02em; }}
.standfirst {{ font-size: 10pt; line-height: 1.6; margin: 0 0 8mm; color: #3d382f; }}
.spec-row, .brief-row {{ display: flex; gap: 4mm; font-size: 8pt; padding: 1.6mm 0;
                         border-top: .3mm solid #e6e1d6; }}
.spec-row .k, .brief-row .k {{ width: 24mm; flex: none; letter-spacing: .09em;
                               color: #8a8478; }}
.spec-row .v, .brief-row .v {{ color: #17150f; }}

.place {{ display: flex; gap: 9mm; align-items: center; }}
.place-img {{ width: 70%; height: 100%; display: flex; align-items: center; }}
.place-col {{ width: 30%; }}
h2 {{ font-size: 13pt; margin: 0 0 5mm; letter-spacing: .04em; }}
.note {{ font-size: 8.5pt; line-height: 1.55; color: #4a443c; margin: 6mm 0 0; }}
.node {{ display: inline-block; margin-top: 6mm; font-size: 7.5pt;
         letter-spacing: .07em; color: #8a8478; }}

.social .row {{ display: flex; align-items: flex-end; justify-content: flex-start; }}
.social .cell {{ display: flex; flex-direction: column; justify-content: flex-end; }}
.cap {{ display: flex; justify-content: space-between; align-items: baseline;
        margin-top: 2.5mm; border-top: .3mm solid #e6e1d6; padding-top: 1.8mm; }}
.use {{ font-size: 8pt; letter-spacing: .09em; }}
.ratio {{ font-size: 7.5pt; color: #8a8478; }}
"""


def build(deck_path: pathlib.Path) -> pathlib.Path:
    deck = json.loads(deck_path.read_text())
    root = deck_path.parent
    pages, n = [], 1
    pages.append(cover(deck, root, n))
    for p in deck.get("placements") or []:
        page = placement(deck, p, root, n + 1)
        if page:
            n += 1
            pages.append(page)
    page = social(deck, root, n + 1)
    if page:
        n += 1
        pages.append(page)
    out = root / "out.html"
    out.write_text(
        f"<!doctype html><meta charset=utf-8><title>{esc(deck.get('title'))}</title>"
        f"<style>{CSS}</style>{''.join(pages)}"
    )
    return out


if __name__ == "__main__":
    target = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "deck.json")
    print(build(target))

```
