#!/usr/bin/env python3
"""cut.py - the edit engine for flora-launch-video.

    The shots are generated once. The cut is data.

Everything in this file is deterministic, free, and safe to re-run. Pacing,
order, trim points, transitions and cutdowns all live in cut.json; none of them
ever cost a generation. "Make it snappier" is `--pace 0.8`, not a re-roll.

    cut.py cut.json --check          dry run: the timeline as numbers, no render
    cut.py cut.json                  render the master
    cut.py cut.json --pace 0.8       snappier (windows x0.8)
    cut.py cut.json --pace 1.3       slower
    cut.py cut.json --snap bar       land cuts on bars instead of beats
    cut.py cut.json --fit            auto-repair overruns, then render
    cut.py cut.json --contact        first/mid/last frame strip, for the eye pass
    cut.py cut.json --resizes        9:16 and 1:1 cutdowns from the master
"""

import argparse, json, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path

# ---------------------------------------------------------------- ffmpeg

def ffmpeg_bin():
    """FFMPEG env > PATH > the static build imageio_ffmpeg ships."""
    for cand in (os.environ.get("FFMPEG"), shutil.which("ffmpeg")):
        if cand and Path(cand).exists():
            return cand
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        pass
    sys.exit("no ffmpeg. `brew install ffmpeg`, or `pip3 install imageio-ffmpeg`, "
             "or set FFMPEG=/path/to/ffmpeg")

FF = ffmpeg_bin()

def run(args, quiet=True):
    p = subprocess.run([FF, "-hide_banner", "-y", *args],
                       capture_output=True, text=True)
    if p.returncode != 0:
        sys.stderr.write(p.stderr[-4000:])
        raise SystemExit(f"ffmpeg failed: {' '.join(str(a) for a in args[:8])} ...")
    return p.stderr

_DUR = re.compile(r"Duration:\s*(\d+):(\d\d):(\d\d\.\d+)")
_DIM = re.compile(r"Video:.*?[,\s](\d{2,5})x(\d{2,5})[,\s]")

STILL = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}

_probe_cache = {}

def probe(path):
    """(duration_s, w, h). No ffprobe in the imageio build, so parse the header.

    A still returns an infinite duration - it can be held for any length, which
    is exactly why the endcard is a still and not a five-second i2v run."""
    path = str(path)
    if path in _probe_cache:
        return _probe_cache[path]
    if Path(path).suffix.lower() in STILL:
        try:
            from PIL import Image
            wh = Image.open(path).size
        except Exception:
            wh = (0, 0)
        _probe_cache[path] = (float("inf"), *wh)
        return _probe_cache[path]
    p = subprocess.run([FF, "-hide_banner", "-i", path],
                       capture_output=True, text=True)
    err = p.stderr
    m = _DUR.search(err)
    dur = (int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))) if m else 0.0
    d = _DIM.search(err)
    wh = (int(d.group(1)), int(d.group(2))) if d else (0, 0)
    if dur == 0.0:
        sys.exit(f"could not read a duration from {path} - is it a video file?")
    _probe_cache[path] = (dur, *wh)
    return _probe_cache[path]

# ---------------------------------------------------------------- timeline

class Shot:
    __slots__ = ("i", "id", "src", "tin", "dur", "speed", "trans", "note",
                 "out", "need", "over", "srcdur", "srcw", "srch", "fitted", "xf",
                 "still")

    def __init__(self, i, d, base):
        self.i = i
        self.id = d.get("id", f"s{i+1}")
        self.src = str((base / d["src"]).resolve()) if not os.path.isabs(d["src"]) else d["src"]
        self.tin = float(d.get("in", 0.0))
        self.dur = float(d["dur"])
        self.speed = float(d.get("speed", 1.0))
        t = d.get("transition", "cut")
        self.trans = t if isinstance(t, dict) else {"type": t}
        self.note = d.get("note", "")
        self.fitted = ""
        self.xf = 0.0
        if not Path(self.src).exists():
            sys.exit(f"shot {self.id}: missing source {self.src}")
        self.still = Path(self.src).suffix.lower() in STILL
        self.srcdur, self.srcw, self.srch = probe(self.src)


def quantize(x, step, minimum):
    return max(minimum, round(x / step) * step)


def build(cut, pace, snap, fit):
    base = cut["_base"]
    fps = cut.get("fps", 30)
    bpm = float(cut.get("bpm", 0) or 0)
    beat = 60.0 / bpm if bpm else 0.0
    grid = snap or cut.get("grid", "free")
    step = {"beat": beat, "bar": beat * 4, "half": beat / 2}.get(grid, 0.0)

    shots = [Shot(i, d, base) for i, d in enumerate(cut["shots"])]
    frame = 1.0 / fps

    for s in shots:
        s.out = s.dur * pace
        if step:
            s.out = quantize(s.out, step, step)
        s.out = round(s.out / frame) * frame                 # land on a whole frame
        s.need = s.out * s.speed                             # source seconds consumed
        s.over = 0.0 if s.still else round((s.tin + s.need) - s.srcdur, 4)
        if fit and s.over > 0:
            pull = min(s.tin, s.over)                        # 1. pull the window earlier
            if pull > 0:
                s.tin = round(s.tin - pull, 4)
                s.over = round(s.over - pull, 4)
                s.fitted = f"in -{pull:.2f}s"
            if s.over > 0:                                   # 2. then stretch the shot
                avail = max(frame, s.srcdur - s.tin)
                s.speed = round(avail / s.out, 4)
                s.need = s.out * s.speed
                s.over = 0.0
                s.fitted = (s.fitted + " " if s.fitted else "") + f"speed {s.speed:.2f}x"

    # Crossfade overlap, resolved here so the report, the music and the render
    # all agree on the running time. A dissolve EATS its duration out of the
    # timeline - get this wrong and the music fade lands in the wrong place.
    for i, s in enumerate(shots):
        t = s.trans.get("type", "cut")
        if i == 0 or t == "cut":
            s.xf = 0.0
            continue
        d = float(s.trans.get("duration", 0.25))
        d = min(d, shots[i - 1].out * 0.4, s.out * 0.4)      # bodies stay positive
        s.xf = round(max(frame, d) / frame) * frame
    return shots, fps, step, grid


def report(cut, shots, fps, step, grid, pace):
    w, h = cut.get("size", [1920, 1080])
    total = round(sum(s.out for s in shots) - sum(s.xf for s in shots), 4)
    print(f"\n{cut.get('title','untitled')}   {len(shots)} shots   "
          f"{total:.2f}s   {w}x{h} @ {fps}fps   grid={grid}"
          + (f" ({cut.get('bpm')}bpm)" if cut.get("bpm") else "")
          + (f"   pace={pace}" if pace != 1.0 else ""))
    print(f"{'#':>2}  {'id':<10} {'in':>6} {'out':>6} {'spd':>5} {'at':>7} "
          f"{'src':>6} {'trans':<9} note")
    at, bad, warn = 0.0, 0, 0
    for s in shots:
        at = round(at - s.xf, 4)
        flag = ""
        if s.over > 0:
            flag, bad = f"  OVERRUN +{s.over:.2f}s", bad + 1
        elif s.fitted:
            flag = f"  fit: {s.fitted}"
        if (s.srcw, s.srch) != (w, h) and s.srcw:
            flag += f"  [src {s.srcw}x{s.srch} -> reframed]"
            warn += 1
        tr = s.trans.get("type", "cut")
        tr = tr if s.xf == 0 else f"{tr} {s.xf:.2f}"
        sd = " still" if s.still else f"{s.srcdur:>6.2f}"
        print(f"{s.i+1:>2}  {s.id:<10} {s.tin:>6.2f} {s.out:>6.2f} {s.speed:>5.2f} "
              f"{at:>7.2f} {sd:>6} {tr:<9} {s.note}{flag}")
        at = round(at + s.out, 4)
    if step:
        off = [f"{s.id} {s.out:.2f}s" for s in shots
               if abs(s.out / step - round(s.out / step)) > 1e-6]
        if off:
            print(f"\noff the {grid} grid: {', '.join(off)}")
    mus = cut.get("music", {}).get("src")
    if mus:
        mp = Path(mus)
        mp = mp if mp.is_absolute() else cut["_base"] / mp
        if mp.exists():
            md = probe(mp)[0] - float(cut["music"].get("in", 0))
            print(f"\nmusic  {mp.name}  {md:.2f}s usable vs {total:.2f}s timeline"
                  + ("  SHORT - will be padded with silence" if md < total - 0.05 else ""))
        else:
            print(f"\nmusic  MISSING: {mp}")
            bad += 1
    print()
    return bad, total

# ---------------------------------------------------------------- render

VCODEC = ["-c:v", "libx264", "-preset", "medium", "-crf", "18",
          "-pix_fmt", "yuv420p", "-movflags", "+faststart"]


def norm(w, h, fps, speed, pad=True):
    """Normalise a source into the timeline's shape, speed and rate.

    tpad clones the last frame for up to a second and the output -t then cuts
    it back to length. Generated clips routinely land 0.03-0.10s under their
    nominal duration; without the top-up every shot after a short one slides."""
    f = []
    if abs(speed - 1.0) > 1e-6:
        f.append(f"setpts=PTS/{speed:.6f}")
    f += [f"scale={w}:{h}:force_original_aspect_ratio=increase",
          f"crop={w}:{h}", "setsar=1", f"fps={fps}"]
    if pad:
        # tpad leaves the stream with frame_rate 1/0, and xfade refuses a source
        # that is not declared CFR - so re-assert the rate on the way out.
        f += ["tpad=stop_mode=clone:stop_duration=1", f"fps={fps}"]
    return ",".join(f)


def src_args(s, at, length, fps):
    """The input half of a piece. A still is looped for exactly as long as the
    timeline wants it; a clip is seeked into."""
    if s.still:
        # No input -t. Bounding the LOOP drops the last frame (measured: every
        # still came back exactly 1/fps short, and every shot after it slid).
        # The output -t / trim does the bounding instead, and counts frames.
        return ["-loop", "1", "-framerate", str(fps), "-i", s.src]
    return ["-ss", f"{s.tin + at * s.speed:.4f}", "-i", s.src]


def piece(s, at, length, w, h, fps, out):
    """`length` seconds of the timeline, starting `at` seconds into shot s."""
    run([*src_args(s, at, length, fps),
         "-an", "-vf", norm(w, h, fps, s.speed, pad=not s.still), "-t", f"{length:.4f}",
         "-fps_mode", "cfr", "-r", str(fps), *VCODEC, str(out)])
    return out


XF = {"dissolve": "fade", "flash": "fadewhite", "dip": "fadeblack",
      "wipe": "wipeleft", "slide": "slideleft", "zoom": "zoomin"}


def transition(a, b, d, kind, w, h, fps, out):
    """One pairwise xfade, rendered in a single call.

    Deliberately NOT a chained xfade graph. Chaining collapses the output
    timebase - measured on ffmpeg 7.1, a five-shot chain emitted 239 frames
    stamped across 2.01s instead of 7.60s, and CFR conversion then dropped 178
    of them. Pairwise into pieces, then concat, is exact."""
    run([*src_args(a, a.out - d, d, fps), *src_args(b, 0.0, d, fps),
         "-filter_complex",
         f"[0:v]{norm(w,h,fps,a.speed,pad=not a.still)},trim=0:{d:.4f},"
         f"setpts=PTS-STARTPTS,fps={fps}[a];"
         f"[1:v]{norm(w,h,fps,b.speed,pad=not b.still)},trim=0:{d:.4f},"
         f"setpts=PTS-STARTPTS,fps={fps}[b];"
         f"[a][b]xfade=transition={XF.get(kind,'fade')}:duration={d:.4f}:offset=0[v]",
         "-map", "[v]", "-an", "-t", f"{d:.4f}",
         "-fps_mode", "cfr", "-r", str(fps), *VCODEC, str(out)])
    return out


def render_timeline(shots, w, h, fps, tmp, out_path):
    """Every shot becomes body pieces; every dissolve becomes its own piece.
    The pieces share codec, size and rate, so the concat is a stream copy."""
    pieces, n = [], len(shots)
    for i, s in enumerate(shots):
        d_in = s.xf
        d_out = shots[i + 1].xf if i + 1 < n else 0.0
        if d_in > 0:
            pieces.append(transition(shots[i - 1], s, d_in,
                                     s.trans.get("type", "dissolve"),
                                     w, h, fps, tmp / f"t{i:03d}.mp4"))
        body = round(s.out - d_in - d_out, 4)
        if body > 0.5 / fps:
            pieces.append(piece(s, d_in, body, w, h, fps, tmp / f"b{i:03d}.mp4"))
    lst = tmp / "concat.txt"
    lst.write_text("".join(f"file '{p}'\n" for p in pieces))
    run(["-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(out_path)])
    return out_path


def add_music(cut, silent, total, out_path):
    m = cut.get("music") or {}
    src = m.get("src")
    if not src:
        shutil.copy(silent, out_path)
        return False
    p = Path(src)
    p = p if p.is_absolute() else cut["_base"] / p
    if not p.exists():
        print(f"  music missing ({p}) - shipping silent")
        shutil.copy(silent, out_path)
        return False
    fo = float(m.get("fade_out", 1.0))
    fi = float(m.get("fade_in", 0.0))
    st = max(0.0, total - fo)
    af = ["apad", f"atrim=0:{total:.4f}", "asetpts=N/SR/TB"]
    if fi > 0:
        af.append(f"afade=t=in:st=0:d={fi:.3f}")
    af += [f"afade=t=out:st={st:.4f}:d={fo:.3f}",
           f"volume={float(m.get('gain_db', 0)):.2f}dB",
           "loudnorm=I=-14:TP=-1.5:LRA=11"]
    run(["-i", str(silent), "-ss", f"{float(m.get('in', 0)):.4f}", "-i", str(p),
         "-filter_complex", f"[1:a]{','.join(af)}[a]",
         "-map", "0:v", "-map", "[a]", "-c:v", "copy",
         "-c:a", "aac", "-b:a", "192k", "-shortest", str(out_path)])
    return True


# ---------------------------------------------------------------- cutdowns

def edge_colour(master, tmp):
    """Sampled ground for the pad. Median of the frame's outer band, not the mean -
    a bright wordmark or a dark plate drags a mean and the bars stop matching."""
    f = tmp / "probe.png"
    run(["-ss", "0.5", "-i", str(master), "-frames:v", "1", str(f)])
    try:
        from PIL import Image
    except ImportError:
        return "black"
    im = Image.open(f).convert("RGB")
    w, h = im.size
    band = int(min(w, h) * 0.06) or 1
    px = (list(im.crop((0, 0, w, band)).getdata())
          + list(im.crop((0, h - band, w, h)).getdata()))
    px.sort(key=lambda c: c[0] * 299 + c[1] * 587 + c[2] * 114)
    r, g, b = px[len(px) // 2]
    return f"0x{r:02x}{g:02x}{b:02x}"


def resizes(cut, master, out_dir, stem, tmp):
    """PAD, never crop.

    A centre-crop from 16:9 to 9:16 guillotines the supers, and the type IS the
    deliverable - the same failure the whole skill is built to avoid, arriving
    at the last step. Default fill is a blurred, darkened copy of the frame,
    which reads as a finished social asset; `"resize": {"fill": "flat"}` uses a
    solid sampled from the master's edge band instead.

    Neither is a true vertical. A full-bleed 9:16 needs its own frames and its
    own i2v pass - say that plainly rather than shipping a letterbox as one."""
    mode = (cut.get("resize") or {}).get("fill", "blur")
    bg = edge_colour(master, tmp) if mode == "flat" else None
    made = []
    for tag, (W, H), y in (("9x16", (1080, 1920), "(H-h)/2.6"),
                           ("1x1", (1080, 1080), "(H-h)/2")):
        out = out_dir / f"{stem}-{tag}.mp4"
        if mode == "blur":
            vf = (f"split[a][b];"
                  f"[a]scale={W}:{H}:force_original_aspect_ratio=increase,"
                  f"crop={W}:{H},boxblur=40:2,eq=brightness=-0.14:saturation=0.55[bg];"
                  f"[b]scale={W}:-2:force_original_aspect_ratio=decrease[fg];"
                  f"[bg][fg]overlay=(W-w)/2:{y},setsar=1")
        else:
            col = bg if mode == "flat" else "black"
            vf = (f"scale={W}:-2:force_original_aspect_ratio=decrease,"
                  f"pad={W}:{H}:(ow-iw)/2:{y.replace('H','oh').replace('h','ih')}"
                  f":color={col},setsar=1")
        run(["-i", str(master), "-vf", vf, *VCODEC, "-c:a", "copy", str(out)])
        made.append(out)
    print(f"  cutdowns letterboxed, fill={mode}"
          + (f" ({bg})" if bg else "")
          + " - full-bleed vertical needs its own generation pass")
    return made


def contact(shots, out_dir, stem, tmp, cut_w=1920, cut_h=1080):
    from PIL import Image, ImageDraw
    cols, tw = 3, 480
    tiles = []
    for s in shots:
        for frac, tag in ((0.0, "in"), (0.5, "mid"), (0.98, "out")):
            f = tmp / f"c_{s.i}_{tag}.png"
            if s.still:
                run(["-i", s.src, "-frames:v", "1", str(f)])
                tiles.append((f"{s.id} still", f))
                break
            run(["-ss", f"{s.tin + s.need * frac:.4f}", "-i", s.src,
                 "-frames:v", "1", str(f)])
            tiles.append((f"{s.id} {tag}", f))
    from PIL import ImageOps
    ims = [(lbl, Image.open(p).convert("RGB")) for lbl, p in tiles]
    th = int(tw * cut_h / cut_w)
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw, rows * (th + 22)), (18, 18, 18))
    d = ImageDraw.Draw(sheet)
    for i, (lbl, im) in enumerate(ims):
        x, y = (i % cols) * tw, (i // cols) * (th + 22)
        # FIT, never stretch. A source at a different aspect gets letterboxed
        # here exactly as the render reframes it - a squashed tile sends the
        # eye pass hunting for a distortion that is not in the film.
        t = ImageOps.contain(im, (tw, th))
        sheet.paste(t, (x + (tw - t.width) // 2, y + (th - t.height) // 2))
        d.text((x + 6, y + th + 5), lbl, fill=(210, 210, 210))
    out = out_dir / f"{stem}-contact.png"
    sheet.save(out)
    return out

# ---------------------------------------------------------------- reference

def measure(ref, thresh=0.35):
    """Read a reference film's EDIT, not its look.

    An inspo clip contributes two separate things and they travel down two
    separate lanes: the LOOK becomes words in every frame prompt, and the CUT
    becomes numbers in cut.json. This measures the second one, so "re-create
    this" stops being a vibe. Never wire the reference into an image model -
    that drags its composition and its subject in with it."""
    p = subprocess.run([FF, "-hide_banner", "-i", str(ref), "-an",
                        "-vf", f"select='gt(scene,{thresh})',metadata=print",
                        "-f", "null", "-"], capture_output=True, text=True)
    cuts = [float(m) for m in re.findall(r"pts_time:([0-9.]+)", p.stderr)]
    dur = probe(ref)[0]
    bounds = [0.0] + cuts + [dur]
    lens = [round(b - a, 2) for a, b in zip(bounds, bounds[1:]) if b - a > 0.08]
    if not lens:
        print(f"{Path(ref).name}: {dur:.2f}s, no cuts detected at scene>{thresh}. "
              f"One continuous shot, or lower the threshold.")
        return
    avg = sum(lens) / len(lens)
    lens_s = sorted(lens)
    med = lens_s[len(lens_s) // 2]
    print(f"\n{Path(ref).name}   {dur:.2f}s   {len(lens)} shots   "
          f"{len(lens)/dur*10:.1f} cuts per 10s")
    print(f"shot lengths  min {min(lens):.2f}  median {med:.2f}  "
          f"mean {avg:.2f}  max {max(lens):.2f}")
    print("             ", "  ".join(f"{l:.2f}" for l in lens[:24])
          + (" ..." if len(lens) > 24 else ""))
    if len(lens) < 4:
        print("\ntoo few shots for a tempo fit - copy the shot lengths straight "
              "into cut.json and set grid \"free\".\n")
        return
    # A cut film is usually locked to a tempo. Find the bpm whose beat best
    # explains the shot lengths - that is the grid to give cut.json.
    best = min(((sum(abs(l / (60/b) - round(l / (60/b))) for l in lens) / len(lens), b)
                for b in range(60, 181)), key=lambda x: x[0])
    err, bpm = best
    print(f"\nbest-fit grid  {bpm} bpm  (beat {60/bpm:.3f}s, "
          f"mean off-grid error {err:.3f} beats)")
    print(f"suggested      \"bpm\": {bpm}, \"grid\": "
          f"\"{'beat' if med < 2*60/bpm else 'bar'}\", "
          f"and {len(lens)} shots averaging {avg:.2f}s\n")
    print("  (a tempo and its double describe the same grid - 60bpm on beats is "
          "120bpm on halves. Take whichever matches the track.)")
    if err > 0.18:
        print("  weak tempo fit - the reference is probably cut to picture, "
              "not to music. Use grid \"free\" and copy the shot lengths.\n")


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description="render a cut.json launch video")
    ap.add_argument("cut", nargs="?")
    ap.add_argument("--measure", metavar="REF",
                    help="read a reference film's cut rate and tempo, then exit")
    ap.add_argument("--pace", type=float, default=1.0,
                    help="multiply every window. 0.8 snappier, 1.3 slower")
    ap.add_argument("--snap", choices=["beat", "bar", "half", "free"],
                    help="override the cut grid")
    ap.add_argument("--fit", action="store_true",
                    help="repair overruns: pull the window earlier, then stretch")
    ap.add_argument("--check", action="store_true", help="dry run, no render")
    ap.add_argument("--contact", action="store_true", help="also emit the frame strip")
    ap.add_argument("--resizes", action="store_true", help="also emit 9:16 and 1:1")
    ap.add_argument("-o", "--out", help="output directory (default: beside cut.json)")
    a = ap.parse_args()

    if a.measure:
        measure(a.measure)
        return
    if not a.cut:
        ap.error("give me a cut.json, or --measure a reference film")

    cp = Path(a.cut).resolve()
    cut = json.loads(cp.read_text())
    cut["_base"] = cp.parent
    if a.pace == 1.0 and "pace" in cut:
        a.pace = float(cut["pace"])

    shots, fps, step, grid = build(cut, a.pace, a.snap, a.fit)
    bad, total = report(cut, shots, fps, step, grid, a.pace)

    if bad:
        print(f"{bad} problem(s). Re-run with --fit to repair, or edit cut.json.")
        print("Do NOT regenerate a shot to fix a timing problem - retime it.\n")
        if a.check:
            sys.exit(1)
        sys.exit(1)
    if a.check:
        print("timeline OK\n")
        return

    w, h = cut.get("size", [1920, 1080])
    out_dir = Path(a.out) if a.out else cp.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = re.sub(r"[^A-Za-z0-9]+", "-", cut.get("title", "launch")).strip("-")
    master = out_dir / f"{stem}.mp4"

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        silent = render_timeline(shots, w, h, fps, tmp, tmp / "silent.mp4")
        scored = add_music(cut, silent, total, master)
        made = [master]
        if a.resizes:
            made += resizes(cut, master, out_dir, stem, tmp)
        if a.contact:
            made.append(contact(shots, out_dir, stem, tmp, w, h))

    for m in made:
        print(f"  {m}  ({m.stat().st_size/1e6:.1f} MB)")
    print(f"\n{total:.2f}s, {len(shots)} shots, "
          f"{'scored' if scored else 'silent'}"
          + (f", pace {a.pace}" if a.pace != 1.0 else "")
          + ".  0 generations spent.\n")


if __name__ == "__main__":
    main()
