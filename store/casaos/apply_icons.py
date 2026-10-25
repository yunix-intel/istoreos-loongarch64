#!/usr/bin/env python3
"""Set x-casaos.icon for every definition from icon-map.json.

CasaOS's own AppStore uses PascalCase directories, so the old
`Apps/<id>/icon.png` URLs 404. selfh.st/icons covers the long tail.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent.parent
APPS = ROOT / "store" / "casaos" / "Apps"
MAPPING = ROOT / "store" / "casaos" / "icon-map.json"
BASE = "https://cdn.jsdelivr.net/gh/selfhst/icons@main/png"


def main() -> None:
    mapping = json.loads(MAPPING.read_text(encoding="utf-8"))
    updated = skipped = 0
    for app_id, icon_name in sorted(mapping.items()):
        path = APPS / app_id / "docker-compose.yml"
        if not path.is_file():
            skipped += 1
            continue
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            skipped += 1
            continue
        casa = data.setdefault("x-casaos", {})
        casa["icon"] = f"{BASE}/{icon_name}.png"
        path.write_text(
            yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=120),
            encoding="utf-8",
            newline="\n",
        )
        updated += 1
    print(f"icons updated={updated} missing={skipped}")


if __name__ == "__main__":
    main()
