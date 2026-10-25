#!/usr/bin/env python3
"""Validate the generated store-card descriptions."""

import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOG = os.path.join(ROOT, "images", "catalog.json")
DESC = os.path.join(ROOT, "store", "loong64-descriptions.json")

REQUIRED_MARKERS = ("linux/loong64", "龙芯版说明", "缺失功能", "额外依赖")


def main():
    catalog = json.load(io.open(CATALOG, encoding="utf-8"))
    doc = json.load(io.open(DESC, encoding="utf-8"))
    apps = doc["apps"]
    images = {x["image"] for x in catalog}
    errors = []

    expected = {x["image"].split("/", 1)[1] for x in catalog} - {"node", "node-sharp"}
    if set(apps) != expected:
        errors.append(f"app set mismatch: missing={sorted(expected - set(apps))} extra={sorted(set(apps) - expected)}")
    if doc.get("app_count") != len(expected):
        errors.append(f"app_count={doc.get('app_count')} expected={len(expected)}")

    for app_id, app in apps.items():
        if app.get("image") not in images:
            errors.append(f"{app_id}: image not in catalog")
        for lang in ("zh_cn", "en_us"):
            text = app["disclosure"][lang]
            if lang == "zh_cn":
                for marker in REQUIRED_MARKERS:
                    if marker not in text:
                        errors.append(f"{app_id}: zh_cn missing {marker}")
            elif "linux/loong64" not in text:
                errors.append(f"{app_id}: en_us missing architecture")
            if not app["quirk"][lang].strip():
                errors.append(f"{app_id}: empty quirk {lang}")
            if not app["missing"][lang].strip():
                errors.append(f"{app_id}: empty missing {lang}")

    if errors:
        print("\n".join(errors))
        return 1
    print(f"ok: {len(apps)} apps, all disclosures complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
