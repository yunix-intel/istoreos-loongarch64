#!/usr/bin/env python3
"""Build the CasaOS host-port reservation plan from current definitions."""

import glob
import io
import json
import os

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DESC = os.path.join(ROOT, "store", "loong64-descriptions.json")
APPS = os.path.join(ROOT, "store", "casaos", "Apps")
OUT = os.path.join(ROOT, "store", "casaos", "port-plan.json")


def main():
    descriptions = json.load(io.open(DESC, encoding="utf-8"))["apps"]
    existing = {}
    for path in glob.glob(os.path.join(APPS, "*", "docker-compose.yml")):
        app_id = os.path.basename(os.path.dirname(path))
        data = yaml.safe_load(io.open(path, encoding="utf-8"))
        port = data.get("x-casaos", {}).get("port_map")
        if port:
            existing[app_id] = int(port)

    used = set(existing.values())
    next_port = 18101
    plan = []
    for app_id in sorted(descriptions):
        if app_id in existing:
            port = existing[app_id]
            source = "existing-definition"
        else:
            while next_port in used:
                next_port += 1
            port = next_port
            used.add(port)
            next_port += 1
            source = "reserved"
        plan.append({
            "id": app_id,
            "image": descriptions[app_id]["image"],
            "host_port": port,
            "source": source,
            "category": descriptions[app_id]["category"],
        })

    out = {
        "schema": 1,
        "generated": "2026-10-25",
        "note": "Existing definitions keep 18001-18018; new apps are reserved from 18101. Apps needing multiple or fixed ports (e.g. wg-easy 51820/udp) must override this primary port.",
        "apps": plan,
    }
    with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write("\n")
    reserved = sum(1 for x in plan if x["source"] == "reserved")
    print(f"total={len(plan)} existing={len(existing)} reserved={reserved}")


if __name__ == "__main__":
    main()
