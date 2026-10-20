#!/usr/bin/env python3
"""Verify all catalog images exist on Docker Hub with both tags and loong64 arch."""
import json
import sys
import urllib.request
from pathlib import Path

CATALOG = Path(__file__).resolve().parent.parent / "images" / "catalog.json"
TAGS = ("loong64", "24.10-la5")
failures = []

rows = json.loads(CATALOG.read_text(encoding="utf-8"))
for row in rows:
    repo = row["image"].split("/", 1)[1]
    for tag in TAGS:
        url = f"https://hub.docker.com/v2/repositories/yunixintel/{repo}/tags/{tag}"
        try:
            data = json.load(urllib.request.urlopen(url, timeout=20))
        except Exception as exc:
            failures.append(f"{repo}:{tag}: {exc}")
            continue
        archs = {(i.get("architecture"), i.get("os")) for i in data.get("images", [])}
        if archs != {("loong64", "linux")}:
            failures.append(f"{repo}:{tag}: unexpected archs {sorted(archs)}")
        print(f"OK {repo}:{tag} {data.get('digest', '')[:20]}")

if failures:
    print("\nFAILURES:", file=sys.stderr)
    print("\n".join(failures), file=sys.stderr)
    sys.exit(1)
print(f"\nAll {len(rows)} images have loong64 + 24.10-la5 tags.")
