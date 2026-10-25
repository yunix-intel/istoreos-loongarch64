#!/usr/bin/env python3
"""Make sidecar readiness dependencies satisfiable.

Several generated definitions used `condition: service_healthy` without a
healthcheck on the database/Redis/MinIO sidecar. Compose then either refuses
to start or waits forever. Add the healthcheck each of our sidecar images
supports; downgrade unknown targets to service_started.
"""
from __future__ import annotations

import glob
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent.parent
APPS = ROOT / "store" / "casaos" / "Apps"

CHECKS = {
    "postgres": {
        "test": ["CMD-SHELL", 'pg_isready -U "$${POSTGRES_USER:-postgres}" -d "$${POSTGRES_DB:-postgres}"'],
        "interval": "5s",
        "timeout": "5s",
        "retries": 20,
        "start_period": "10s",
    },
    "mariadb": {
        "test": ["CMD-SHELL", 'mysqladmin ping -h 127.0.0.1 -uroot -p"$${MYSQL_ROOT_PASSWORD}" --silent'],
        "interval": "5s",
        "timeout": "5s",
        "retries": 30,
        "start_period": "15s",
    },
    "redis": {
        "test": ["CMD-SHELL", 'if [ -n "$$REDIS_PASSWORD" ]; then redis-cli -a "$$REDIS_PASSWORD" ping; else redis-cli ping; fi'],
        "interval": "5s",
        "timeout": "5s",
        "retries": 20,
        "start_period": "5s",
    },
    "minio": {
        "test": ["CMD-SHELL", "curl -fsS http://127.0.0.1:9000/minio/health/live >/dev/null"],
        "interval": "5s",
        "timeout": "5s",
        "retries": 30,
        "start_period": "10s",
    },
}


def kind(image: str) -> str | None:
    image = image.lower()
    for key in ("postgres", "mariadb", "redis", "minio"):
        if key in image:
            return key
    return None


def main() -> None:
    added = downgraded = 0
    warnings: list[str] = []
    for filename in sorted(glob.glob(str(APPS / "*" / "docker-compose.yml"))):
        path = Path(filename)
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            continue
        services = data.get("services") or {}
        changed = False
        for svc in services.values():
            if not isinstance(svc, dict):
                continue
            deps = svc.get("depends_on")
            if isinstance(deps, list):
                converted = {}
                for dep_name in deps:
                    target = services.get(dep_name)
                    key = kind(str(target.get("image", ""))) if isinstance(target, dict) else None
                    if key:
                        if not target.get("healthcheck"):
                            target["healthcheck"] = dict(CHECKS[key])
                            added += 1
                        converted[dep_name] = {"condition": "service_healthy"}
                    else:
                        converted[dep_name] = {"condition": "service_started"}
                        if isinstance(target, dict):
                            warnings.append(
                                f"{path.parent.name}:{dep_name} unknown image {target.get('image')!r}"
                            )
                        else:
                            warnings.append(f"{path.parent.name}: missing service {dep_name}")
                svc["depends_on"] = converted
                changed = True
                continue
            if not isinstance(deps, dict):
                continue
            for dep_name, dep_cfg in deps.items():
                if not isinstance(dep_cfg, dict) or dep_cfg.get("condition") != "service_healthy":
                    continue
                target = services.get(dep_name)
                if not isinstance(target, dict):
                    dep_cfg["condition"] = "service_started"
                    downgraded += 1
                    warnings.append(f"{path.parent.name}:{svc.get('container_name', '?')} -> missing service {dep_name}")
                    changed = True
                    continue
                key = kind(str(target.get("image", "")))
                if key is None:
                    dep_cfg["condition"] = "service_started"
                    downgraded += 1
                    warnings.append(f"{path.parent.name}:{dep_name} unknown image {target.get('image')!r}")
                    changed = True
                    continue
                if not target.get("healthcheck"):
                    target["healthcheck"] = dict(CHECKS[key])
                    added += 1
                    changed = True
        if changed:
            path.write_text(
                yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=120),
                encoding="utf-8",
                newline="\n",
            )
    print(f"healthchecks added={added} downgraded={downgraded}")
    for warning in warnings:
        print("WARN", warning)


if __name__ == "__main__":
    main()
