#!/usr/bin/env python3
"""comp.py - the frame compositor for flora-motion-compositor.

    Nothing is generated. Every pixel comes from a file or a font.

A scene is a JSON scene graph: layers with keyframed transforms, rendered
deterministically frame by frame and piped straight into ffmpeg. Type stays
type, screenshots stay screenshots, and the same scene renders identically
every time - there is no seed to lose and nothing to drift.

    comp.py scene.json                 render <id>.mp4
    comp.py scene.json --frame 1.2     one PNG at t=1.2s. the free check.
    comp.py scene.json --strip 6       six frames across the shot, as a strip
    comp.py scenes/ --all              every scene in a directory
    comp.py --svg logo.svg 2048        rasterise an SVG through headless Chrome
"""

import argparse, json, math, os, re, shutil, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
import numpy as np

# ---------------------------------------------------------------- plumbing

def ffmpeg_bin():
    for c in (os.environ.get("FFMPEG"), shutil.which("ffmpeg")):
        if c and Path(c).exists():
            return c
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        sys.exit("no ffmpeg. `brew install ffmpeg` or `pip3 install imageio-ffmpeg`")

FF = ffmpeg_bin()
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

FONT_DIRS = ["/System/Library/Fonts", "/System/Library/Fonts/Supplemental",
             "/Library/Fonts", str(Path.home() / "Library/Fonts")]
_fonts, _images = {}, {}


def find_font(name, weight="regular"):
    """Resolve a font by human name. Real fonts are the entire point of this
    tool - a missing one falls back loudly rather than silently to something
    that changes the design."""
    key = (name, weight)
    if key in _fonts:
        return _fonts[key]
    want = re.sub(r"[^a-z0-9]", "", f"{name}{'' if weight=='regular' else weight}")
    cands = []
    for d in FONT_DIRS:
        for p in Path(d).glob("*.tt*") if Path(d).exists() else []:
            cands.append(p)
    exact = [p for p in cands if re.sub(r"[^a-z0-9]", "", p.stem.lower()) == want]
    loose = [p for p in cands
             if re.sub(r"[^a-z0-9]", "", name.lower()) in
             re.sub(r"[^a-z0-9]", "", p.stem.lower())]
    hit = (exact or loose or [None])[0]
    if hit is None:
        print(f"  font '{name}' not found - falling back to Helvetica")
        hit = Path("/System/Library/Fonts/Helvetica.ttc")
        if not hit.exists():
            hit = Path("/System/Library/Fonts/Supplemental/Arial.ttf")
    _fonts[key] = str(hit)
    return _fonts[key]


def load_image(path):
    if path not in _images:
        _images[path] = Image.open(path).convert("RGBA")
    return _images[path]


def svg_to_png(svg, width, out=None):
    """macOS ships no SVG rasteriser, but Chrome is one. Logos arrive as SVG and
    have to become high-resolution transparent PNGs before they can be layers."""
    svg, out = Path(svg), Path(out or Path(svg).with_suffix(".png"))
    if not Path(CHROME).exists():
        sys.exit("no Chrome to rasterise the SVG - export a 4x PNG from the source app")
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-sandbox",
                    "--default-background-color=00000000",
                    f"--window-size={width},{width}",
                    f"--screenshot={out}", svg.resolve().as_uri()],
                   capture_output=True)
    if not out.exists():
        sys.exit(f"Chrome produced nothing for {svg}")
    im = Image.open(out).convert("RGBA")
    im.crop(im.getbbox() or (0, 0, *im.size)).save(out)   # trim the empty canvas
    print(f"  {svg.name} -> {out.name}  {Image.open(out).size}")
    return out

# ---------------------------------------------------------------- easing

def _bez(p1, p2):
    def f(t):
        u = t
        for _ in range(8):                       # Newton, plenty for 1/30s steps
            x = 3*(1-u)**2*u*p1 + 3*(1-u)*u*u*p2 + u**3
            d = 3*(1-u)**2*p1 + 6*(1-u)*u*(p2-p1) + 3*u*u*(1-p2)
            if abs(d) < 1e-6:
                break
            u -= (x - t) / d
        u = min(max(u, 0.0), 1.0)
        return 3*(1-u)**2*u*0 + 3*(1-u)*u*u*1 + u**3
    return f

EASE = {
    "linear":    lambda t: t,
    "inQuad":    lambda t: t*t,
    "outQuad":   lambda t: 1-(1-t)**2,
    "inOutQuad": lambda t: 2*t*t if t < .5 else 1-(-2*t+2)**2/2,
    "inCubic":   lambda t: t**3,
    "outCubic":  lambda t: 1-(1-t)**3,
    "inOutSine": lambda t: -(math.cos(math.pi*t)-1)/2,
    "outExpo":   lambda t: 1.0 if t >= 1 else 1-2**(-10*t),
    "inOutExpo": lambda t: t and (2**(20*t-10)/2 if t < .5 else (2-2**(-20*t+10))/2),
    "outBack":   lambda t: 1+2.70158*(t-1)**3+1.70158*(t-1)**2,
    "outQuint":  lambda t: 1-(1-t)**5,
}
EASE["snap"] = _bez(0.16, 1.0)          # the motion-graphics default: fast out, long settle


def ease(name, t):
    return EASE.get(name, EASE["snap"])(min(max(t, 0.0), 1.0))


def value(layer, prop, t, default):
    """The value of one property at time t. Later keys win, so overlapping
    animations on the same prop layer in order."""
    v = layer.get(prop, default)
    for a in layer.get("anim", []):
        if a.get("prop") != prop:
            continue
        t0, t1 = a.get("t", [0, 1])
        if t < t0:
            v = a["from"]
        elif t >= t1:
            v = a["to"]
        else:
            k = ease(a.get("ease", "snap"), (t - t0) / max(t1 - t0, 1e-6))
            v = a["from"] + (a["to"] - a["from"]) * k
    return v

# ---------------------------------------------------------------- 3D tilt

def _coeffs(dst, src):
    A, B = [], []
    for (dx, dy), (sx, sy) in zip(dst, src):
        A.append([dx, dy, 1, 0, 0, 0, -sx*dx, -sx*dy]); B.append(sx)
        A.append([0, 0, 0, dx, dy, 1, -sy*dx, -sy*dy]); B.append(sy)
    return np.linalg.lstsq(np.array(A, float), np.array(B, float), rcond=None)[0]


def tilt(im, rx=0.0, ry=0.0, rz=0.0, persp=1600.0):
    """Rotate a flat plate in 3D and project it. This is the one move that makes
    a UI screenshot stop looking like a screenshot - and it is a real projection,
    not a shear, so the near edge genuinely grows."""
    if abs(rx) < .01 and abs(ry) < .01 and abs(rz) < .01:
        return im, (0, 0)
    w, h = im.size
    ax, ay, az = map(math.radians, (rx, ry, rz))
    pts = []
    for x, y in ((-w/2, -h/2), (w/2, -h/2), (w/2, h/2), (-w/2, h/2)):
        z = 0.0
        y, z = y*math.cos(ax) - z*math.sin(ax), y*math.sin(ax) + z*math.cos(ax)
        x, z = x*math.cos(ay) + z*math.sin(ay), -x*math.sin(ay) + z*math.cos(ay)
        x, y = x*math.cos(az) - y*math.sin(az), x*math.sin(az) + y*math.cos(az)
        s = persp / max(persp - z, 1.0)
        pts.append((x*s, y*s))
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    ox, oy = min(xs), min(ys)
    ow, oh = int(math.ceil(max(xs)-ox)), int(math.ceil(max(ys)-oy))
    dst = [(x-ox, y-oy) for x, y in pts]
    src = [(0, 0), (w, 0), (w, h), (0, h)]
    out = im.transform((ow, oh), Image.PERSPECTIVE, _coeffs(dst, src),
                       Image.BICUBIC)
    return out, (ox + w/2, oy + h/2)      # offset of the plate centre in the new box


def rounded(im, r):
    if r <= 0:
        return im
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, im.width-1, im.height-1], r, fill=255)
    out = im.copy()
    out.putalpha(ImageChops.multiply(im.getchannel("A"), m))
    return out


def shadow(im, blur, opacity, dy, dx=0):
    a = im.getchannel("A").filter(ImageFilter.GaussianBlur(blur))
    s = Image.new("RGBA", im.size, (0, 0, 0, 0))
    s.putalpha(a.point(lambda v: int(v * opacity)))
    return s, (dx, dy)

# ---------------------------------------------------------------- layers

def render_image(L, t, W, H):
    im = load_image(str(L["_src"]))
    if L.get("w"):
        im = im.resize((int(L["w"]), max(1, round(im.height * L["w"] / im.width))),
                       Image.LANCZOS)
    elif L.get("h"):
        im = im.resize((max(1, round(im.width * L["h"] / im.height)), int(L["h"])),
                       Image.LANCZOS)
    im = rounded(im, L.get("radius", 0))
    tl = L.get("tilt") or {}
    rx = value(L, "tiltX", t, tl.get("x", 0.0))
    ry = value(L, "tiltY", t, tl.get("y", 0.0))
    rz = value(L, "tiltZ", t, tl.get("z", 0.0))
    im, _ = tilt(im, rx, ry, rz, tl.get("persp", 1600.0))
    return im


def render_text(L, t, W, H):
    """Words, lines or characters revealed on a stagger. Each unit carries its
    own delay, so the phrase arrives rather than appearing."""
    f = ImageFont.truetype(find_font(L.get("font", "Helvetica"),
                                     L.get("weight", "regular")),
                           int(L.get("size", 64)))
    track = L.get("track", 0)
    leading = L.get("leading", 1.15)
    maxw = L.get("width")
    words = str(L["text"]).split()
    lines, cur = [], []
    for w in words:
        trial = " ".join(cur + [w])
        if maxw and cur and f.getlength(trial) + track*len(trial) > maxw:
            lines.append(cur); cur = [w]
        else:
            cur.append(w)
    if cur:
        lines.append(cur)

    rv = L.get("reveal") or {}
    mode = rv.get("mode", "none")
    stag = float(rv.get("stagger", 0.06))
    t0 = float(rv.get("t", 0.0))
    dur = float(rv.get("dur", 0.55))
    rise = float(rv.get("rise", 0.0))
    eas = rv.get("ease", "snap")

    lh = int(f.size * leading)
    units = []                            # (word, x, y, stagger index, tile width)
    for li, ln in enumerate(lines):
        x = 0
        for w in ln:
            tilew = int(f.getlength(w) + track*len(w)) + int(f.size*0.6)
            units.append((w, x, li*lh, li if mode == "lines" else len(units), tilew))
            x += int(f.getlength(w + " ") + track*(len(w)+1))
    if not units:
        return Image.new("RGBA", (1, 1))

    # Width from where the tiles actually END. Re-measuring the joined string
    # under-reports it once tracking is negative, and the last word of the
    # longest line gets sliced off - visible on that one word only.
    tw = max(u[1] + u[4] for u in units)
    pad = int(abs(rise)) + int(f.size*0.4) + 8
    can = Image.new("RGBA", (tw + 8, lh*len(lines) + pad*2), (0, 0, 0, 0))
    col, base_op = L.get("color", "#ffffff"), float(L.get("opacity", 1.0))

    L["_pad"] = pad
    for w, x, y, idx, ww in units:
        k = 1.0 if mode == "none" else ease(eas, (t - (t0 + idx*stag)) / max(dur, 1e-6))
        if k <= 0:
            continue
        # Each word is composited as its OWN tile. Drawing everything onto one
        # canvas and then re-alphaing regions double-dims wherever two words
        # overlap, which on a tracked headline is most of them.
        tile = Image.new("RGBA", (max(ww, 1), int(f.size*1.8)), (0, 0, 0, 0))
        td = ImageDraw.Draw(tile)
        if track:
            cx = 0
            for ch in w:
                td.text((cx, 0), ch, font=f, fill=col)
                cx += f.getlength(ch) + track
        else:
            td.text((0, 0), w, font=f, fill=col)
        a = min(k, 1.0) * base_op
        if a < 0.999:
            tile.putalpha(tile.getchannel("A").point(lambda v: int(v*max(a, 0))))
        can.alpha_composite(tile, (int(x), int(y + pad + rise*(1-k))))
    return can


def render_rect(L, t, W, H):
    """A rule or bar that animates its own width starts at ZERO - and a
    zero-width rounded rect raises. Check every scene at t=0 and t=dur, never
    only in the middle; this one only ever failed on the first frame."""
    w, h = int(value(L, "w", t, 100)), int(value(L, "h", t, 100))
    if w < 1 or h < 1:
        return Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    r = int(min(L.get("radius", 0), w/2, h/2))
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([0, 0, w-1, h-1], r,
                                         fill=L.get("color", "#ffffff"))
    return im


RENDER = {"image": render_image, "text": render_text, "rect": render_rect}

# ---------------------------------------------------------------- frame

def background(scene, W, H):
    bg = scene.get("bg", "#000000")
    if isinstance(bg, str):
        return Image.new("RGBA", (W, H), bg)
    if bg.get("image"):
        im = load_image(str(bg["_src"]))
        s = max(W/im.width, H/im.height)
        im = im.resize((round(im.width*s), round(im.height*s)), Image.LANCZOS)
        return im.crop(((im.width-W)//2, (im.height-H)//2,
                        (im.width-W)//2+W, (im.height-H)//2+H))
    a, b = bg.get("from", "#000000"), bg.get("to", "#222222")
    ca = np.array([int(a.lstrip("#")[i:i+2], 16) for i in (0, 2, 4)], float)
    cb = np.array([int(b.lstrip("#")[i:i+2], 16) for i in (0, 2, 4)], float)
    ramp = np.linspace(0, 1, H)[:, None, None]
    arr = (ca[None, None, :]*(1-ramp) + cb[None, None, :]*ramp)
    arr = np.repeat(arr, W, axis=1).astype(np.uint8)
    return Image.fromarray(arr).convert("RGBA")


_vig = {}

def grade(im, g, i, W, H):
    if not g:
        return im
    arr = np.asarray(im.convert("RGB"), dtype=np.float32)
    v = float(g.get("vignette", 0))
    if v > 0:
        if (W, H, v) not in _vig:
            y, x = np.mgrid[0:H, 0:W]
            r = np.sqrt(((x-W/2)/(W/2))**2 + ((y-H/2)/(H/2))**2)
            _vig[(W, H, v)] = np.clip(1 - v*np.clip(r-0.35, 0, None)**1.6, 0, 1)[..., None]
        arr *= _vig[(W, H, v)]
    if g.get("brightness"):
        arr *= 1 + float(g["brightness"])
    if g.get("saturation") is not None:
        # Explicit weighted sum, not a matmul. Accelerate's float32 BLAS emits
        # spurious divide/overflow warnings on an (H,W,3)@(3,) contraction.
        lum = arr[..., 0]*0.299 + arr[..., 1]*0.587 + arr[..., 2]*0.114
        arr = lum[..., None] + (arr - lum[..., None]) * float(g["saturation"])
    gr = float(g.get("grain", 0))
    if gr > 0:
        # Seeded per FRAME INDEX, never per wall-clock. Two renders of the same
        # scene must be byte-identical or the whole "re-render is free" claim
        # quietly stops being true.
        rng = np.random.default_rng(1000 + i)
        arr += rng.normal(0, gr*255, (H, W, 1))
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")


def frame(scene, t, i, W, H):
    canvas = background(scene, W, H)
    for L in scene["layers"]:
        t0, t1 = L.get("in", 0.0), L.get("out", 1e9)
        if not (t0 <= t < t1):
            continue
        lt = t - t0
        im = RENDER[L["type"]](L, lt, W, H)
        sc = value(L, "scale", lt, 1.0)
        if abs(sc - 1.0) > 1e-3:
            im = im.resize((max(1, round(im.width*sc)), max(1, round(im.height*sc))),
                           Image.LANCZOS)
        rot = value(L, "rotate", lt, 0.0)
        if abs(rot) > 1e-3:
            im = im.rotate(rot, Image.BICUBIC, expand=True)
        bl = value(L, "blur", lt, 0.0)
        if bl > 0.1:
            im = im.filter(ImageFilter.GaussianBlur(bl))
        op = value(L, "opacity", lt, 1.0)
        ax, ay = L.get("at", [W/2, H/2])
        x, y = value(L, "x", lt, ax), value(L, "y", lt, ay)
        anc = L.get("anchor", "center")
        if anc in ("center", "top", "bottom"):
            x -= im.width/2
        if anc in ("center", "left", "right"):
            y -= im.height/2
        if anc in ("right", "topright", "bottomright"):
            x -= im.width
        if anc in ("bottom", "bottomleft", "bottomright"):
            y -= im.height
        # A text block reserves headroom for its rise; topleft means the top of
        # the TYPE, not the top of that padding, or every headline sits low.
        if anc.startswith("top") and L["type"] == "text":
            y -= L.get("_pad", 0)
        if L.get("shadow") and L["type"] == "image":
            s = L["shadow"]
            sh, (dx, dy) = shadow(im, s.get("blur", 50), s.get("opacity", .5)*op,
                                  s.get("dy", 30), s.get("dx", 0))
            canvas.alpha_composite(sh, (int(x+dx), int(y+dy)))
        if op < 0.999:
            im = im.copy()
            im.putalpha(im.getchannel("A").point(lambda v: int(v*max(op, 0))))
        canvas.alpha_composite(im, (int(x), int(y)))

    cam = scene.get("camera")
    if cam:
        z = value({"anim": cam}, "zoom", t, 1.0)
        cx = value({"anim": cam}, "px", t, 0.0)
        cy = value({"anim": cam}, "py", t, 0.0)
        if abs(z-1) > 1e-3 or cx or cy:
            cw, ch = W/z, H/z
            l, tp = (W-cw)/2 + cx, (H-ch)/2 + cy
            canvas = canvas.crop((round(l), round(tp), round(l+cw), round(tp+ch))) \
                           .resize((W, H), Image.LANCZOS)
    return grade(canvas, scene.get("grade"), i, W, H)

# ---------------------------------------------------------------- render

def resolve(scene, base):
    for L in scene["layers"]:
        if L["type"] == "image":
            p = Path(L["src"])
            p = p if p.is_absolute() else base / p
            if p.suffix.lower() == ".svg":
                p = svg_to_png(p, int(L.get("w", 1200) * 2))
            if not p.exists():
                sys.exit(f"layer {L.get('id','?')}: missing {p}")
            L["_src"] = p
    bg = scene.get("bg")
    if isinstance(bg, dict) and bg.get("image"):
        p = Path(bg["image"])
        bg["_src"] = p if p.is_absolute() else base / p
    return scene


def render(scene, base, out_dir):
    W, H = scene.get("size", [1920, 1080])
    fps = scene.get("fps", 30)
    n = max(1, round(scene["dur"] * fps))
    out = out_dir / f"{scene.get('id','shot')}.mp4"
    p = subprocess.Popen(
        [FF, "-hide_banner", "-loglevel", "error", "-y",
         "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps),
         "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "17",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out)],
        stdin=subprocess.PIPE)
    for i in range(n):
        p.stdin.write(frame(scene, i/fps, i, W, H).convert("RGB").tobytes())
    p.stdin.close()
    if p.wait() != 0:
        sys.exit("ffmpeg encode failed")
    return out, n

# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description="render a scene.json into a shot")
    ap.add_argument("scene", nargs="?")
    ap.add_argument("--frame", type=float, help="render one PNG at this time, then exit")
    ap.add_argument("--strip", type=int, help="N frames across the shot, as one strip")
    ap.add_argument("--all", action="store_true", help="scene is a directory")
    ap.add_argument("--svg", nargs=2, metavar=("FILE", "WIDTH"),
                    help="rasterise an SVG to a transparent PNG, then exit")
    ap.add_argument("-o", "--out", help="output directory")
    a = ap.parse_args()

    if a.svg:
        svg_to_png(a.svg[0], int(a.svg[1]))
        return
    if not a.scene:
        ap.error("give me a scene.json, a directory with --all, or --svg")

    sp = Path(a.scene).resolve()
    files = sorted(sp.glob("*.json")) if a.all else [sp]
    for f in files:
        scene = resolve(json.loads(f.read_text()), f.parent)
        W, H = scene.get("size", [1920, 1080])
        fps = scene.get("fps", 30)
        out_dir = Path(a.out) if a.out else f.parent
        out_dir.mkdir(parents=True, exist_ok=True)
        sid = scene.get("id", f.stem)

        if a.frame is not None:
            o = out_dir / f"{sid}-t{a.frame:g}.png"
            frame(scene, a.frame, round(a.frame*fps), W, H).convert("RGB").save(o)
            print(f"  {o}")
            continue
        if a.strip:
            ts = [scene["dur"]*k/(a.strip-1) if a.strip > 1 else 0
                  for k in range(a.strip)]
            tw = 480
            th = round(tw*H/W)
            sheet = Image.new("RGB", (tw*a.strip, th), (18, 18, 18))
            for k, t in enumerate(ts):
                sheet.paste(frame(scene, min(t, scene["dur"]-1/fps), round(t*fps),
                                  W, H).convert("RGB").resize((tw, th)), (k*tw, 0))
            o = out_dir / f"{sid}-strip.png"
            sheet.save(o)
            print(f"  {o}   t = {', '.join(f'{t:.2f}' for t in ts)}")
            continue

        o, n = render(scene, f.parent, out_dir)
        print(f"  {o}  {scene['dur']:.2f}s  {n} frames  {W}x{H}@{fps}  "
              f"({o.stat().st_size/1e6:.1f} MB)   0 generations spent.")


if __name__ == "__main__":
    main()
