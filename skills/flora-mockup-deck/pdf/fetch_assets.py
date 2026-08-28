#!/usr/bin/env python3
"""Download every canvas asset listed in assets.json into src/.

Requires media.flora.ai to be permitted by the session's egress policy.
"""
import json, os, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "src")

def main():
    spec = json.load(open(os.path.join(HERE, "assets.json")))
    os.makedirs(SRC, exist_ok=True)
    failed = 0
    for node in spec["nodes"]:
        dest = os.path.join(SRC, node["file"])
        if os.path.exists(dest) and os.path.getsize(dest) > 0:
            print(f"have  {node['file']}")
            continue
        try:
            with urllib.request.urlopen(node["url"], timeout=60) as r:
                data = r.read()
            open(dest, "wb").write(data)
            print(f"got   {node['file']}  {len(data):,}B")
        except Exception as exc:
            failed += 1
            print(f"FAIL  {node['file']}  {exc}")
    if failed:
        print(f"\n{failed} asset(s) failed. If this is a 403, media.flora.ai is still "
              f"blocked by the environment's network policy.")
        sys.exit(1)

if __name__ == "__main__":
    main()
