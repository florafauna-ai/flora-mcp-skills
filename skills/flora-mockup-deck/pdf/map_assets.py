#!/usr/bin/env python3
"""Propose a role->file manifest from the downloaded assets' aspect ratios.

Social formats are identified by ratio (16:9 / 1:1 / 4:5 / 9:16). Remaining
landscape photographs are the placement shots and are listed for manual
assignment, since only the imagery distinguishes hoarding from billboard.
"""
import glob, json, os
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "src")

TARGETS = {"fmt_master": 16/9, "fmt_1x1": 1.0, "fmt_4x5": 4/5, "fmt_9x16": 9/16}

def main():
    files = sorted(glob.glob(os.path.join(SRC, "*.png")) +
                   glob.glob(os.path.join(SRC, "*.jpg")))
    info = []
    for path in files:
        with Image.open(path) as im:
            w, h = im.size
        info.append((os.path.basename(path), w, h, w / h))

    print(f"{'file':28s} {'size':>14s} {'ratio':>7s}  guess")
    used, roles = set(), {}
    for name, w, h, r in info:
        best, err = min(((k, abs(r - v) / v) for k, v in TARGETS.items()),
                        key=lambda t: t[1])
        guess = best if err < 0.03 else ("placement / landscape" if r > 1.2 else "?")
        if err < 0.03 and best not in roles:
            roles[best], _ = name, used.add(name)
        print(f"{name:28s} {w:>6d}×{h:<7d} {r:>7.3f}  {guess}")

    print("\nlandscape candidates for the four placement pages:")
    for name, w, h, r in info:
        if name not in used and r > 1.2:
            print(f"  {name}")
    print("\nProposed roles (merge into manifest.json after checking the images):")
    print(json.dumps(roles, indent=2))

if __name__ == "__main__":
    main()
