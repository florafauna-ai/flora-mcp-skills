#!/usr/bin/env python3
"""Build the FLORA "Your Agents Joined" OOH placement deck as a 16:9 PDF.

Follows the deck structure in skills/flora-mockup-deck/SKILL.md: cover carrying
the plate and the standfirst that states the law, one page per placement with
SHOT / LIGHT / MOMENT, and a social page at MATCHED WIDTH on a shared baseline
so the ratios stay legible as ratios.

Images are read from src/ via manifest.json. Any unmapped or missing asset is
drawn as a labelled placeholder, so the deck renders end-to-end regardless.

    python build_deck.py            # build out/flora-placement-deck.pdf
    python build_deck.py --check    # report which assets resolved
"""

import json
import os
import sys

from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.pdfbase.pdfmetrics import stringWidth

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "src")
OUT = os.path.join(HERE, "out", "flora-placement-deck.pdf")

# --- page + design system -------------------------------------------------
W, H = 1280.0, 720.0                     # 16:9 screen deck, in points

INK = HexColor("#0A0A0A")                # page ground
PANEL = HexColor("#131413")              # text panel ground
PAPER = HexColor("#FFFFFF")
MUTED = HexColor("#8C9186")              # stone / olive gray
ACCENT = HexColor("#A8B49A")             # olive, from the master creative
DIM = HexColor("#5E625C")
RULE = HexColor("#2A2C29")

REG = "Helvetica"
BOLD = "Helvetica-Bold"
MARGIN = 56.0


# --- text helpers ---------------------------------------------------------
def wrap(text, font, size, max_w):
    words, lines, cur = text.split(), [], ""
    for word in words:
        trial = f"{cur} {word}".strip()
        if stringWidth(trial, font, size) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def para(c, text, x, y, max_w, font=REG, size=11.5, leading=17.5, color=MUTED):
    c.setFillColor(color)
    c.setFont(font, size)
    for line in wrap(text, font, size, max_w):
        c.drawString(x, y, line)
        y -= leading
    return y


def tracked(c, text, x, y, font=BOLD, size=9.0, space=2.4, color=ACCENT):
    """Letter-spaced label, used for eyebrow/kicker lines."""
    c.setFillColor(color)
    c.setFont(font, size)
    for ch in text:
        c.drawString(x, y, ch)
        x += stringWidth(ch, font, size) + space
    return x


# --- image helpers --------------------------------------------------------
def load(role, manifest):
    name = manifest.get(role)
    if not name:
        return None
    path = os.path.join(SRC, name)
    return path if os.path.exists(path) else None


def placeholder(c, x, y, w, h, label, note):
    c.saveState()
    c.setFillColor(HexColor("#161816"))
    c.rect(x, y, w, h, stroke=0, fill=1)
    c.setStrokeColor(RULE)
    c.setLineWidth(1)
    c.rect(x, y, w, h, stroke=1, fill=0)
    c.setDash(4, 5)
    c.line(x, y, x + w, y + h)
    c.line(x, y + h, x + w, y)
    c.setDash()
    cw, ch = min(w - 24, 330.0), 50.0
    cx, cy = x + (w - cw) / 2, y + (h - ch) / 2
    c.setFillColor(INK)
    c.rect(cx, cy, cw, ch, stroke=0, fill=1)
    c.setStrokeColor(RULE)
    c.rect(cx, cy, cw, ch, stroke=1, fill=0)
    c.setFillColor(MUTED)
    c.setFont(BOLD, 9.5)
    c.drawCentredString(x + w / 2, cy + 30, label[:44])
    c.setFillColor(DIM)
    c.setFont(REG, 7.5)
    c.drawCentredString(x + w / 2, cy + 16, note[:58])
    c.restoreState()


def draw_image(c, path, x, y, w, h, mode="fill", label="", note=""):
    """mode='fill' crops to the box; mode='fit' letterboxes inside it."""
    if not path:
        placeholder(c, x, y, w, h, label, note)
        return
    from PIL import Image

    img = Image.open(path)
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    iw, ih = img.size

    if mode == "fill":
        target, cur = w / h, iw / ih
        if cur > target:                        # too wide -> crop sides
            new_w = int(ih * target)
            off = (iw - new_w) // 2
            img = img.crop((off, 0, off + new_w, ih))
        elif cur < target:                      # too tall -> crop top/bottom
            new_h = int(iw / target)
            off = (ih - new_h) // 2
            img = img.crop((0, off, iw, off + new_h))
        c.drawImage(ImageReader(img), x, y, w, h, mask="auto")
    else:
        scale = min(w / iw, h / ih)
        dw, dh = iw * scale, ih * scale
        c.drawImage(ImageReader(img), x + (w - dw) / 2, y + (h - dh) / 2,
                    dw, dh, mask="auto")


# --- page furniture -------------------------------------------------------
def ground(c):
    c.setFillColor(INK)
    c.rect(0, 0, W, H, stroke=0, fill=1)


def footer(c, left, right):
    # Deliberately unbranded chrome: the skill is a generalist placement engine
    # and carries no mark or client name in the furniture.
    c.setStrokeColor(RULE)
    c.setLineWidth(0.75)
    c.line(MARGIN, 40, W - MARGIN, 40)
    c.setFillColor(DIM)
    c.setFont(REG, 8.0)
    c.drawString(MARGIN, 23, left)
    c.drawRightString(W - MARGIN, 23, right)


# --- content --------------------------------------------------------------
STANDFIRST = (
    "Out-of-home placement study for the Your Agents Joined campaign: four "
    "real-world sites, plus the master creative resized for social delivery. "
    "The creative is reproduced exactly in every frame — it is placed into each "
    "photograph, never regenerated, recropped or re-lettered."
)

SPEC = [
    ("CREATIVE", "Your Agents Joined"),
    ("SOURCE", "2048 × 1152  ·  16:9"),
    ("PLACEMENTS", "4 sites"),
    ("SOCIAL", "1:1  ·  4:5  ·  9:16"),
]

# SHOT / LIGHT / MOMENT are read from the placement photographs: the original
# prompt briefs are not recorded against the runs on this canvas.
PLACEMENTS = [
    {
        "role": "placement_gable", "n": "01", "site": "Building gable wall",
        "shot": "Street level, wide — the full gable in frame, square on",
        "light": "Overcast daylight, flat grey across the brick",
        "moment": "A cyclist crossing the near kerb, well below the plate",
        "obs": "The full master reads square-on and uncropped against the brick.",
    },
    {
        "role": "placement_subway", "n": "02", "site": "Subway platform",
        "shot": "Platform level, the panel seen down its length",
        "light": "Interior artificial light on green tile",
        "moment": "Empty platform, track side open",
        "obs": "Shot at a receding angle, so the plate foreshortens — read this "
               "one as a context view rather than a fidelity reference.",
    },
    {
        "role": "placement_roadside", "n": "03", "site": "Roadside billboard",
        "shot": "Low, from the opposite carriageway — board above the traffic line",
        "light": "Overcast, wet road holding the reflection",
        "moment": "One car passing beneath, motion-blurred",
        "obs": "Elevated sightline; the artwork is complete and square in frame.",
    },
    {
        "role": "placement_hoarding", "n": "04", "site": "Construction hoarding",
        "shot": "Pavement level, square to the timber run",
        "light": "Flat daylight, no direct sun on the plate",
        "moment": "A pedestrian with a backpack along the near edge, clear of the artwork",
        "obs": "Square-on with crisp textural clarity and no interference at the "
               "poster boundary — the strongest placement in the set.",
    },
]

# use / ratio / supporting fact — captioned by USE first, per the skill.
FORMATS = [
    {"role": "fmt_master", "use": "MASTER",        "ratio": "16:9", "fact": "Native  ·  2048 × 1152", "rw": 16, "rh": 9},
    {"role": "fmt_1x1",    "use": "FEED",          "ratio": "1:1",  "fact": "Blurred extension",      "rw": 1,  "rh": 1},
    {"role": "fmt_4x5",    "use": "FEED PORTRAIT", "ratio": "4:5",  "fact": "Black letterbox",        "rw": 4,  "rh": 5},
    {"role": "fmt_9x16",   "use": "STORY · REEL",  "ratio": "9:16", "fact": "Blurred extension",      "rw": 9,  "rh": 16},
]


def page_cover(c, manifest):
    ground(c)
    img_w = W * 0.60
    draw_image(c, load("master", manifest), W - img_w, 0, img_w, H, "fill",
               "MASTER CREATIVE  ·  16:9", "2048 × 1152 — src/ asset pending")

    x, tw = MARGIN, W * 0.40 - MARGIN - 40
    tracked(c, "PLACEMENT DECK", x, H - 96)

    c.setFillColor(PAPER)
    for i, line in enumerate(["YOUR AGENTS", "JOINED"]):
        c.setFont(BOLD, 46)
        c.drawString(x, H - 158 - i * 52, line)

    c.setStrokeColor(ACCENT)
    c.setLineWidth(2)
    c.line(x, H - 262, x + 54, H - 262)

    para(c, STANDFIRST, x, H - 294, tw, size=11, leading=17)

    y = H - 408
    for key, val in SPEC:
        c.setStrokeColor(RULE)
        c.setLineWidth(0.75)
        c.line(x, y + 22, x + tw, y + 22)
        c.setFillColor(DIM)
        c.setFont(BOLD, 8.5)
        c.drawString(x, y, key)
        c.setFillColor(PAPER)
        c.setFont(REG, 11)
        c.drawString(x + 108, y, val)
        y -= 38

    footer(c, "Placement deck", "1 / 6")
    c.showPage()


def page_placement(c, manifest, item, page_no):
    ground(c)
    img_w = W * 0.70
    draw_image(c, load(item["role"], manifest), 0, 0, img_w, H, "fill",
               item["site"].upper(), "placement photograph — src/ asset pending")

    px, pw = img_w, W - img_w
    c.setFillColor(PANEL)
    c.rect(px, 0, pw, H, stroke=0, fill=1)

    x, tw = px + 34, pw - 68
    tracked(c, f"PLACEMENT {item['n']}", x, H - 92)

    c.setFillColor(PAPER)
    y = H - 138
    for line in wrap(item["site"], BOLD, 23, tw):
        c.setFont(BOLD, 23)
        c.drawString(x, y, line)
        y -= 29

    c.setStrokeColor(ACCENT)
    c.setLineWidth(2)
    c.line(x, y - 12, x + 44, y - 12)

    y -= 48
    for key in ("shot", "light", "moment"):
        c.setFillColor(ACCENT)
        c.setFont(BOLD, 8.0)
        c.drawString(x, y, key.upper())
        y = para(c, item[key], x, y - 15, tw, size=10, leading=14.5,
                 color=PAPER) - 14

    c.setStrokeColor(RULE)
    c.setLineWidth(0.75)
    c.line(x, y + 6, x + tw, y + 6)
    para(c, item["obs"], x, y - 14, tw, size=9.5, leading=14.5, color=MUTED)

    c.setFillColor(HexColor("#3A3D38"))
    c.setFont(BOLD, 64)
    c.drawString(x, 74, item["n"])

    footer(c, item["site"], f"{page_no} / 6")
    c.showPage()


def page_social(c, manifest):
    """Matched WIDTH, bottom-aligned on a shared baseline.

    Heights are left free to climb, so the page shows at a glance that 9:16 is
    tall and 16:9 is a letterbox. Height-matching instead would flatten every
    ratio to nearly the same width and lose the one thing this page proves.
    """
    ground(c)

    tracked(c, "SOCIAL DELIVERY", MARGIN, H - 66)
    c.setFillColor(PAPER)
    c.setFont(BOLD, 25)
    c.drawString(MARGIN, H - 104, "Format set")
    c.setFillColor(DIM)
    c.setFont(REG, 10)
    c.drawRightString(W - MARGIN, H - 104,
                      "Derived from the single 16:9 master — padded, never re-cropped")

    baseline, gap = 132.0, 24.0
    max_h = 430.0                                   # vertical space is the binding
    cell_w = max_h * 9 / 16                         # constraint; 9:16 is the tallest
    row_w = 4 * cell_w + 3 * gap
    x0 = (W - row_w) / 2

    for i, fmt in enumerate(FORMATS):
        cx = x0 + i * (cell_w + gap)
        ch = cell_w * fmt["rh"] / fmt["rw"]
        draw_image(c, load(fmt["role"], manifest), cx, baseline, cell_w, ch,
                   "fill", fmt["ratio"], "src/ asset pending")

        c.setStrokeColor(RULE)
        c.setLineWidth(0.75)
        c.line(cx, baseline - 10, cx + cell_w, baseline - 10)

        c.setFillColor(PAPER)                       # USE leads the caption
        c.setFont(BOLD, 11)
        c.drawString(cx, baseline - 30, fmt["use"])

        c.setFillColor(DIM)                         # fact + ratio share a line
        c.setFont(REG, 8)
        c.drawString(cx, baseline - 46, fmt["fact"])
        c.setFillColor(ACCENT)
        c.setFont(BOLD, 8.5)
        c.drawRightString(cx + cell_w, baseline - 46, fmt["ratio"])

    footer(c, "Social delivery  ·  format set", "6 / 6")
    c.showPage()


def main():
    with open(os.path.join(HERE, "manifest.json")) as fh:
        manifest = json.load(fh)["roles"]

    if "--check" in sys.argv:
        missing = 0
        for role, name in manifest.items():
            path = os.path.join(SRC, name) if name else None
            ok = bool(path and os.path.exists(path))
            missing += 0 if ok else 1
            print(f"{'ok     ' if ok else 'MISSING'}  {role:20s} {name or '(unmapped)'}")
        print(f"\n{len(manifest) - missing}/{len(manifest)} assets resolved")
        return

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    c = rl_canvas.Canvas(OUT, pagesize=(W, H))
    c.setTitle("Your Agents Joined — Placement Deck")
    c.setSubject("Out-of-home placement study")

    page_cover(c, manifest)
    for i, item in enumerate(PLACEMENTS):
        page_placement(c, manifest, item, i + 2)
    page_social(c, manifest)

    c.save()
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
