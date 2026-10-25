#!/usr/bin/env python3
"""Validate CasaOS app definitions before import.

Checks structure, image policy, LoongArch disclosure, data paths, port
collisions and port_map consistency. Exit code 1 on any error.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("PyYAML is required: python3 -m pip install pyyaml")

ROOT = Path(__file__).resolve().parent
APPS = Path(os.environ.get("CASAOS_APPS", ROOT / "Apps"))
PORT_PLAN = ROOT / "port-plan.json"
ALLOWED_PREFIXES = ("yunixintel/", "local/") if os.environ.get("CASAOS_PRIVATE") else ("yunixintel/",)

REQUIRED_DISCLOSURE = ("龙芯版说明", "缺失功能", "额外依赖")
PUBLIC_TAGS = {":24.10-la5", ":loong64"}
DOCKER_SOCK_APPS = {
    "watchtower",
    "portainer",
    "dpanel",
    "woodpecker-agent",
    "webvirtcloud",
    "dozzle",
}
MEDIA_PREFIXES = ("/DATA/AppData/", "/DATA/Media", "/DATA/Gallery", "/DATA/Documents")
SYSTEM_MOUNT_PREFIXES = ("/run/udev", "/lib/modules", "/dev/", "/proc", "/sys")
WHOLE_DATA_ALLOWED = {"filebrowser"}
ROOT_MOUNT_ALLOWED = {"node-exporter"}
NO_PORT_APPS = {"unpackerr", "watchtower"}


def load_plan() -> dict[str, dict]:
    data = json.loads(PORT_PLAN.read_text(encoding="utf-8"))
    return {item["id"]: item for item in data["apps"]}


def published_ports(service: dict) -> list[int]:
    ports = []
    for item in service.get("ports", []) or []:
        if isinstance(item, dict):
            value = item.get("published")
        else:
            # short syntax: "8080:80" or "80" (container only, not published)
            parts = str(item).split(":")
            value = parts[-2] if len(parts) >= 2 else None
        if value not in (None, ""):
            try:
                ports.append(int(str(value).split("-")[0]))
            except ValueError:
                pass
    return ports


def validate(path: Path, plan: dict[str, dict]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    app_id = path.parent.name
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return [f"YAML parse failed: {exc}"], warnings
    if not isinstance(doc, dict):
        return ["top level is not a mapping"], warnings

    if doc.get("name") != app_id:
        errors.append(f"name {doc.get('name')!r} != directory {app_id!r}")
    services = doc.get("services")
    if not isinstance(services, dict) or not services:
        return errors + ["missing services"], warnings

    for svc_name, svc in services.items():
        if not isinstance(svc, dict):
            errors.append(f"service {svc_name}: not a mapping")
            continue
        if "build" in svc:
            errors.append(f"service {svc_name}: build is not allowed in a store definition")
        image = svc.get("image", "")
        if not image.startswith(ALLOWED_PREFIXES):
            errors.append(f"service {svc_name}: image {image!r} is not an allowed image")
        elif not os.environ.get("CASAOS_PRIVATE") and not any(
            image.endswith(tag) for tag in PUBLIC_TAGS
        ):
            errors.append(f"service {svc_name}: image {image!r} lacks a public tag")
        if not svc.get("restart"):
            warnings.append(f"service {svc_name}: no restart policy")
        for vol in svc.get("volumes", []) or []:
            if isinstance(vol, dict):
                source = str(vol.get("source", ""))
            else:
                source = str(vol).split(":")[0]
            if not source or not source.startswith("/"):
                continue  # named volume
            if source.startswith("/var/run/docker.sock"):
                if app_id not in DOCKER_SOCK_APPS:
                    errors.append(f"service {svc_name}: unexpected docker.sock mount")
                continue
            if source.startswith(SYSTEM_MOUNT_PREFIXES):
                continue
            if source == "/" and app_id in ROOT_MOUNT_ALLOWED:
                continue
            if not source.startswith(MEDIA_PREFIXES):
                if source.rstrip("/") == "/DATA" and app_id in WHOLE_DATA_ALLOWED:
                    continue
                errors.append(f"service {svc_name}: host path outside /DATA: {source}")
            if (
                "$AppID" not in source
                and source.rstrip("/") != "/DATA"
                and source != "/"
                and not source.startswith(MEDIA_PREFIXES)
            ):
                warnings.append(f"service {svc_name}: path does not use $AppID: {source}")

    x = doc.get("x-casaos")
    if not isinstance(x, dict):
        return errors + ["missing x-casaos"], warnings
    if "loong64" not in (x.get("architectures") or []):
        errors.append("x-casaos.architectures must contain loong64")
    for key in ("main", "author", "category", "developer", "icon", "index"):
        if not x.get(key):
            errors.append(f"x-casaos.{key} missing")
    if x.get("main") not in services:
        errors.append(f"x-casaos.main {x.get('main')!r} is not a service")
    desc = x.get("description") or {}
    zh = desc.get("zh_cn", "") if isinstance(desc, dict) else ""
    for token in REQUIRED_DISCLOSURE:
        if token not in zh:
            errors.append(f"description.zh_cn missing {token!r}")
    if "linux/loong64" not in zh and "loong64" not in zh:
        errors.append("description.zh_cn does not state the architecture")
    for key in ("title", "tagline"):
        val = x.get(key)
        if not isinstance(val, dict) or not val.get("zh_cn") or not val.get("en_us"):
            errors.append(f"x-casaos.{key} needs zh_cn and en_us")

    expected = plan.get(app_id, {}).get("host_port")
    port_map = str(x.get("port_map", ""))
    main = services.get(x.get("main"), {}) if isinstance(x.get("main"), str) else {}
    main_ports = published_ports(main) if isinstance(main, dict) else []
    if port_map:
        if port_map not in {str(p) for p in main_ports}:
            errors.append(f"port_map {port_map} not published by main service {main_ports}")
    elif "network_mode" not in main and app_id not in NO_PORT_APPS:
        warnings.append("no port_map and main service is not host-networked")
    if expected is not None and port_map and port_map != str(expected):
        warnings.append(f"port_map {port_map} differs from plan {expected}")

    return errors, warnings


def main() -> int:
    plan = load_plan()
    paths = sorted(APPS.glob("*/docker-compose.yml"))
    all_errors: dict[str, list[str]] = {}
    all_warnings: dict[str, list[str]] = {}
    ports: dict[int, list[str]] = {}
    for path in paths:
        app_id = path.parent.name
        errors, warnings = validate(path, plan)
        if errors:
            all_errors[app_id] = errors
        if warnings:
            all_warnings[app_id] = warnings
        try:
            doc = yaml.safe_load(path.read_text(encoding="utf-8"))
            for svc in (doc.get("services") or {}).values():
                if isinstance(svc, dict):
                    for port in published_ports(svc):
                        ports.setdefault(port, []).append(app_id)
        except Exception:
            pass

    for port, owners in sorted(ports.items()):
        if len(set(owners)) > 1:
            all_errors.setdefault("(ports)", []).append(
                f"host port {port} used by {sorted(set(owners))}"
            )

    print(f"definitions: {len(paths)}")
    for app_id, warnings in sorted(all_warnings.items()):
        for warning in warnings:
            print(f"WARN  {app_id}: {warning}")
    for app_id, errors in sorted(all_errors.items()):
        for error in errors:
            print(f"ERROR {app_id}: {error}")
    print(f"ok={len(paths) - len(all_errors)} errors={sum(map(len, all_errors.values()))}")
    return 1 if all_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
