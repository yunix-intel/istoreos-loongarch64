#!/usr/bin/env python3
"""Apply the generated LoongArch disclosure text to CasaOS app definitions."""

import io
import json
import os

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
APPS = os.path.join(ROOT, "store", "casaos", "Apps")
EXPORT = os.path.join(ROOT, "store", "exports", "casaos-descriptions.json")


def main():
    with io.open(EXPORT, encoding="utf-8") as f:
        descriptions = json.load(f)["apps"]

    updated = 0
    for app_id in sorted(os.listdir(APPS)):
        compose = os.path.join(APPS, app_id, "docker-compose.yml")
        if not os.path.isfile(compose):
            continue
        if app_id not in descriptions:
            print(f"skip {app_id}: no description")
            continue
        with io.open(compose, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            print(f"skip {app_id}: not a mapping")
            continue
        desc = descriptions[app_id]
        casa = data.setdefault("x-casaos", {})
        arches = casa.setdefault("architectures", [])
        if "loong64" not in arches:
            arches.append("loong64")
        casa["title"] = desc["title"]
        casa["category"] = desc["category"]
        casa["tagline"] = desc["tagline"]
        casa["description"] = desc["description"]
        with io.open(compose, "w", encoding="utf-8", newline="\n") as f:
            yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False, width=120)
        updated += 1
    print(f"updated {updated} definitions")


if __name__ == "__main__":
    main()
