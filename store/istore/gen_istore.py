#!/usr/bin/env python3
"""Generate iStore app-meta sources for the 115 LoongArch64 applications.

Reads:
  store/loong64-descriptions.json          titles / categories
  store/exports/istore-descriptions.json   Chinese/English HTML descriptions
  store/casaos/port-plan.json              primary host-port allocation
  store/private/links.json                 public/private image variants
  images/<id>/Dockerfile*                  EXPOSE / VOLUME / USER
  store/istore/data/runtime-overrides.json curated runtime facts

Writes (deterministically):
  store/istore/src/app-meta/<id>/...
  store/istore/data/build-manifest.json
"""

from __future__ import annotations

import json
import os
import re
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent

RELEASE = 20261025
APP_VERSION = "24.10-la5"
PKG_VERSION = "1.0.0-r20261025"
PUBLIC_IMAGE_TAG = "24.10-la5"
PUBLIC_REF = "yunixintel"
PROJECT_URL = "https://github.com/yunix-intel/istoreos-loongarch64"
PRIVATE_URL = "https://github.com/yunix-intel/istore-la-private"

CATEGORY_TAGS = {
    "Media": ["media", "tool"],
    "Cloud": ["cloud", "storage"],
    "Developer": ["dev", "tool"],
    "Networking": ["net", "tool"],
    "Security": ["security", "tool"],
    "Monitoring": ["monitor", "tool"],
    "Productivity": ["productivity", "tool"],
    "Backup": ["backup", "tool"],
    "Downloaders": ["download", "tool"],
    "Utilities": ["tool"],
    "Database": ["database", "tool"],
    "Automation": ["automation", "tool"],
    "Photos": ["photo", "tool"],
    "Documents": ["document", "tool"],
    "Finance": ["finance", "tool"],
}

PRIMARY_PORT = {
    "navidrome": 4533,
    "vaultwarden": 8443,
    "gogs": 3000,
    "qbittorrent-ee": 8080,
    "nextcloud": 8080,
    "kodexplorer": 8080,
    "wallabag": 8080,
    "typecho": 8080,
    "heimdall": 8080,
    "it-tools": 8080,
    "excalidraw": 8080,
    "syncthing": 8384,
    "portainer": 9000,
    "nginx-proxy-manager": 81,
    "homebridge": 8581,
    "minio": 9000,
    "sftpgo": 8080,
    "go2rtc": 1984,
    "mediamtx": 8888,
    "ente-web": 3000,
    "woodpecker-server": 8000,
    "woodpecker-agent": 3000,
    "pihole": 80,
    "adguardhome": 3000,
    "caddy": 80,
    "wg-easy": 51821,
    "registry": 5000,
    "alertmanager": 9093,
    "node-exporter": 9100,
    "mihomo": 9090,
    "memos": 5230,
    "code-server": 8443,
    "gitea": 3000,
    "miniflux": 8080,
    "firefly-iii": 8080,
    "phpmyadmin": 8080,
    "vaultwarden": 8443,
}

PRIMARY_VOLUME = {
    "/data", "/app/data", "/appdata", "/data/data", "/config", "/var/www/html/data",
    "/var/www/html/storage", "/var/www/wallabag/data", "/etc/linkding/data",
    "/opt/memos/data", "/home/coder", "/homebridge", "/var/lib/grafana",
    "/var/lib/woodpecker", "/var/lib/registry", "/var/lib/sftpgo", "/app/vikunja/files",
    "/app/config", "/etc/headscale", "/opt/scrutiny/config", "/var/www/piwigo/_data",
    "/var/www/bookstack/storage", "/var/www/matomo/config", "/srv/webvirtcloud/data",
    "/opt/adguardhome/work", "/etc/pihole", "/etc/mihomo", "/etc/easytier",
    "/etc/wireguard", "/etc/letsencrypt", "/prometheus", "/alertmanager",
    "/var/cache/ntfy", "/var/www/FreshRSS/data", "/srv/sftpgo/data",
}

MEDIA_HOST = {
    "/media": "/mnt/media",
    "/music": "/mnt/music",
    "/books": "/mnt/books",
    "/downloads": "/mnt/downloads",
    "/movies": "/mnt/movies",
    "/tv": "/mnt/tv",
    "/audiobooks": "/mnt/audiobooks",
    "/srv/music": "/mnt/music",
    "/srv/comics": "/mnt/comics",
    "/srv": "/mnt/files",
    "/path/to/media": "/mnt/media",
    "/path/to/music": "/mnt/music",
}

SYSTEM_PATH = {
    "/var/run/docker.sock", "/proc", "/sys", "/", "/run/udev", "/lib/modules",
    "/opt/apps/lbrowser", "/mnt",
}

FILE_VOLUMES = {
    "/usr/share/nginx/html/assets/config.yml": "config.yml",
    "/usr/share/nginx/html/conf.yml": "conf.yml",
    "/etc/caddy/Caddyfile": "Caddyfile",
    "/etc/prometheus/prometheus.yml": "prometheus.yml",
    "/etc/alertmanager/alertmanager.yml": "alertmanager.yml",
    "/config/config.yaml": "config.yaml",
    "/database": "",
}

FILE_EXT = (".yml", ".yaml", ".conf", ".toml", ".ini", ".cfg", ".json")

KNOWN_VOLUME_NAMES = {
    "/data": "data",
    "/app/data": "data",
    "/data/data": "data",
    "/appdata": "appdata",
    "/config": "config",
    "/app/config": "config",
    "/etc/gitea": "config",
    "/etc/headscale": "config",
    "/opt/scrutiny/config": "config",
    "/var/www/html/config": "config",
    "/var/www/html/data": "data",
    "/var/www/html/storage": "storage",
    "/var/www/html/usr": "usr",
    "/var/www/html": "html",
    "/var/www/wallabag/data": "data",
    "/var/www/bookstack/storage": "storage",
    "/var/www/bookstack/public/uploads": "uploads",
    "/var/www/piwigo/local": "local",
    "/var/www/piwigo/_data": "data",
    "/var/www/piwigo/galleries": "galleries",
    "/var/www/piwigo/upload": "upload",
    "/var/www/matomo/config": "config",
    "/var/www/matomo/tmp": "tmp",
    "/var/www/FreshRSS/data": "data",
    "/etc/linkding/data": "data",
    "/opt/memos/data": "data",
    "/home/coder": "home",
    "/homebridge": "homebridge",
    "/var/lib/grafana": "data",
    "/var/lib/woodpecker": "data",
    "/var/lib/registry": "data",
    "/auth": "auth",
    "/var/lib/sftpgo": "data",
    "/srv/sftpgo/data": "data",
    "/srv/sftpgo/backups": "backups",
    "/srv/webvirtcloud/data": "data",
    "/var/www/.ssh": "ssh",
    "/app/vikunja/files": "files",
    "/db": "db",
    "/opt/scrutiny/config": "config",
    "/opt/data/assets": "assets",
    "/etc/headscale": "config",
    "/var/lib/headscale": "data",
    "/etc/wireguard": "wireguard",
    "/lib/modules": "modules",
    "/etc/letsencrypt": "letsencrypt",
    "/prometheus": "data",
    "/alertmanager": "data",
    "/var/cache/ntfy": "cache",
    "/etc/ntfy": "config",
    "/etc/pihole": "etc",
    "/opt/adguardhome/work": "work",
    "/opt/adguardhome/conf": "conf",
    "/etc/mihomo": "config",
    "/etc/easytier": "config",
    "/mosquitto/config": "config",
    "/mosquitto/data": "data",
    "/mosquitto/log": "log",
    "/cache": "cache",
    "/data/.hermes": "hermes",
    "/workspace": "workspace",
    "/configs": "configs",
    "/database": "database",
    "/srv": "files",
    "/run/udev": "udev",
    "/proc": "proc",
    "/sys": "sys",
    "/": "rootfs",
}

PORT_NAMES = {
    22: "ssh", 53: "dns", 80: "http", 81: "admin", 443: "https", 1883: "mqtt",
    1935: "rtmp", 1984: "http", 2022: "sftp", 3000: "http", 3001: "http",
    3306: "mysql", 5000: "http", 5006: "http", 5055: "http", 5230: "http",
    5432: "postgres", 5690: "http", 6379: "redis", 6767: "http", 6881: "bittorrent",
    7474: "http", 7575: "http", 7745: "http", 7878: "http", 8000: "http",
    8080: "http", 8082: "http", 8083: "http", 8096: "http", 8123: "http",
    8181: "http", 8384: "http", 8443: "https", 8554: "rtsp", 8555: "webrtc",
    8787: "http", 8888: "hls", 8889: "webrtc", 9000: "s3", 9001: "console",
    9090: "api", 9091: "http", 9093: "http", 9094: "gossip", 9100: "metrics",
    9117: "http", 9633: "metrics", 9696: "http", 9898: "http", 11211: "memcached",
    13378: "http", 1411: "http", 22300: "http", 25600: "http", 34400: "http",
    51820: "wireguard", 51821: "http", 19035: "http", 21027: "discovery",
    22000: "sync", 9001: "console",
}

FIXED_PORT_FALLBACK_NOTE = (
    "固定端口 {port} 已被前面的应用占用，本应用自动改用 {actual}；"
    "两个应用不应同时启动在同一台机器上。"
)


def load_json(path: Path):
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def sanitize_id(value: str) -> str:
    s = re.sub(r"[^a-z0-9_-]+", "-", value.lower()).strip("-")
    return s or "app"


def shq(value) -> str:
    return "'" + str(value).replace("'", "'\\''") + "'"


def clean_field(value) -> str:
    s = str(value) if value is not None else ""
    return s.replace("\r", " ").replace("\n", " ").replace("|", "%7C").replace("^", "%5E")


def read_dockerfile(app_id: str):
    folder = REPO / "images" / app_id
    ports = []
    volumes = []
    user = ""
    if not folder.is_dir():
        return ports, volumes, user
    for path in sorted(folder.glob("Dockerfile*")):
        text = path.read_text(encoding="utf-8", errors="replace")
        text = re.sub(r"\\\s*\n\s*", " ", text)
        for m in re.finditer(r"(?im)^\s*EXPOSE\s+(.+)$", text):
            for tok in m.group(1).split():
                ports.extend(normalize_port_token(tok))
        for m in re.finditer(r"(?im)^\s*VOLUME\s+(.+)$", text):
            raw = m.group(1).strip()
            items = []
            if raw.startswith("["):
                try:
                    items = json.loads(raw)
                except Exception:
                    items = re.findall(r'"([^"]*)"|\'([^\']*)\'', raw)
                    items = [a or b for a, b in items]
            else:
                items = raw.split()
            for item in items:
                v = normalize_volume_path(item)
                if v:
                    volumes.append(v)
        for m in re.finditer(r"(?im)^\s*USER\s+(\S+)", text):
            user = m.group(1).strip()
    # de-duplicate, preserve order
    seen_ports = set()
    unique_ports = []
    for p in ports:
        key = (p["container"], p["proto"])
        if key not in seen_ports:
            seen_ports.add(key)
            unique_ports.append(p)
    ports = unique_ports
    volumes = list(dict.fromkeys(volumes))
    return ports, volumes, user


def normalize_port_token(tok: str):
    tok = tok.strip().replace("–", "-").replace("—", "-")
    if not tok:
        return []
    proto = "tcp"
    if "/" in tok:
        tok, proto = tok.rsplit("/", 1)
        proto = proto.lower()
        if proto not in ("tcp", "udp"):
            proto = "tcp"
    if tok.startswith("${"):
        tok = "4533"  # navidrome ND_PORT
    if "-" in tok:
        a, b = tok.split("-", 1)
        try:
            a, b = int(a), int(b)
            if 0 < b - a <= 32:
                return [{"container": p, "proto": proto} for p in range(a, b + 1)]
        except ValueError:
            return []
    try:
        port = int(tok)
    except ValueError:
        return []
    if not (0 < port <= 65535):
        return []
    return [{"container": port, "proto": proto}]


def normalize_volume_path(path: str):
    if not isinstance(path, str):
        return ""
    p = path.strip().strip('"').strip("'").rstrip(",")
    if p.startswith("./"):
        p = p[2:]
    if not p.startswith("/"):
        p = "/" + p
    if len(p) > 1:
        p = p.rstrip("/")
    if p in ("/tmp", "/var/tmp"):
        return ""
    return p


def volume_type(container: str) -> str:
    if container in FILE_VOLUMES:
        return "file" if FILE_VOLUMES[container] else "dir"
    base = os.path.basename(container)
    if base.lower().endswith(FILE_EXT):
        return "file"
    return "dir"


def volume_name(container: str, used: set) -> str:
    if container in KNOWN_VOLUME_NAMES:
        name = KNOWN_VOLUME_NAMES[container]
    else:
        name = os.path.basename(container).strip("/") or "data"
        name = re.sub(r"[^a-zA-Z0-9_.-]+", "-", name).strip("-") or "data"
    base = name
    i = 2
    while name in used:
        name = f"{base}-{i}"
        i += 1
    used.add(name)
    return name


def host_for_volume(container: str, app_id: str, name: str, vtype: str) -> str:
    if container in MEDIA_HOST:
        return MEDIA_HOST[container]
    if container in SYSTEM_PATH:
        return container
    if vtype == "file" or container in FILE_VOLUMES:
        base = FILE_VOLUMES.get(container) or os.path.basename(container)
        if base:
            return f"/srv/{app_id}/{base}"
    return f"/srv/{app_id}/{name}"


def choose_primary_port(app_id: str, ports, explicit):
    if explicit:
        return int(explicit)
    if app_id in PRIMARY_PORT:
        return PRIMARY_PORT[app_id]
    if not ports:
        return 0
    tcp = [p["container"] for p in ports if p.get("proto", "tcp") == "tcp"]
    for preferred in (80, 8080, 3000, 9000, 8384, 8096, 4533, 5006, 5230, 8443):
        if preferred in tcp:
            return preferred
    return tcp[0] if tcp else ports[0]["container"]


def port_name(port: int, proto: str, used: set) -> str:
    base = PORT_NAMES.get(port, f"port-{port}")
    if proto == "udp" and not base.endswith("-udp"):
        base = base + "-udp"
    name = base
    i = 2
    while name in used:
        name = f"{base}-{i}"
        i += 1
    used.add(name)
    return name


def build_ports(app_id: str, ov: dict, base_ports, plan_host: int, index: int, used_hosts: set, notes: list):
    raw = []
    if "ports" in ov:
        for p in ov["ports"]:
            raw.append({"container": int(p["container"]), "proto": p.get("proto", "tcp"),
                        "name": p.get("name", ""), "host": p.get("host"), "primary": bool(p.get("primary"))})
    else:
        for p in base_ports:
            raw.append({"container": int(p["container"]), "proto": p.get("proto", "tcp"),
                        "name": "", "host": None, "primary": False})

    if not raw:
        return []

    primary = None
    for p in raw:
        if p.get("primary"):
            primary = p["container"]
            break
    if primary is None:
        primary = choose_primary_port(app_id, raw, ov.get("primary_port"))
        for p in raw:
            if p["container"] == primary and p["proto"] == "tcp":
                p["primary"] = True
                break
        else:
            for p in raw:
                if p["container"] == primary:
                    p["primary"] = True
                    break

    fixed = set(int(x) for x in ov.get("fixed_ports", []))
    host_network = bool(ov.get("host_network"))
    names = set()
    secondary = 0
    result = []
    for p in raw:
        host = p.get("host")
        if host_network:
            host = p["container"]
        elif host is None:
            if p["container"] in fixed:
                host = p["container"]
            elif p.get("primary"):
                host = plan_host or p["container"]
            else:
                host = 20000 + index * 16 + secondary
                secondary += 1
        host = int(host)
        # avoid collision with other apps, except tcp/udp pairs inside this app
        original = host
        guard = 0
        while host in used_hosts and not host_network:
            host += 1
            guard += 1
            if guard > 200:
                break
        if host != original and original in fixed:
            notes.append(FIXED_PORT_FALLBACK_NOTE.format(port=original, actual=host))
        if not host_network:
            used_hosts.add(host)
        name = p.get("name") or port_name(p["container"], p["proto"], names)
        names.add(name)
        result.append({
            "name": name,
            "container": p["container"],
            "host": host,
            "proto": p["proto"],
            "primary": bool(p.get("primary")),
        })
    return result


def build_volumes(app_id: str, ov: dict, base_volumes, docker_user: str):
    raw = []
    seen = set()
    for v in base_volumes:
        raw.append({"container": v})
        seen.add(v)
    for v in ov.get("volumes", []):
        c = normalize_volume_path(v["container"])
        if c in seen:
            for item in raw:
                if item["container"] == c:
                    item.update({k: val for k, val in v.items() if k != "container"})
                    break
        else:
            item = {"container": c}
            item.update({k: val for k, val in v.items() if k != "container"})
            raw.append(item)
            seen.add(c)

    used_names = set()
    result = []
    owner_default = ""
    if re.fullmatch(r"\d+(?::\d+)?", docker_user or ""):
        owner_default = docker_user
    for item in raw:
        container = item["container"]
        vtype = item.get("type") or volume_type(container)
        name = item.get("name") or volume_name(container, used_names)
        used_names.add(name)
        host = item.get("host") or host_for_volume(container, app_id, name, vtype)
        seed = item.get("seed") or (FILE_VOLUMES.get(container, "") if vtype == "file" else "")
        result.append({
            "name": name,
            "host": host,
            "container": container,
            "mode": item.get("mode", "rw"),
            "owner": item.get("owner", owner_default),
            "primary": bool(item.get("primary", False)),
            "type": vtype,
            "seed": seed,
        })

    if result:
        explicit = [v for v in result if v["primary"]]
        if not explicit:
            for v in result:
                if v["container"] in PRIMARY_VOLUME:
                    v["primary"] = True
                    break
            else:
                result[0]["primary"] = True
        else:
            for v in explicit[1:]:
                v["primary"] = False
    return result


def template_replace(value: str, base: str, db_user: str, db_name: str) -> str:
    return (value.replace("${BASE}", base)
                 .replace("${DB_USER}", db_user)
                 .replace("${DB_NAME}", db_name))


def build_sidecars(app_id: str, ov: dict, templates: dict):
    sidecars = []
    for sc in ov.get("sidecars", []):
        tpl_name = sc["template"]
        if tpl_name not in templates:
            raise SystemExit(f"{app_id}: unknown sidecar template {tpl_name}")
        tpl = templates[tpl_name]
        name = sc.get("name", tpl_name)
        full = sc.get("full_name", f"{app_id}-{name}")
        base = sc.get("base") or ov.get("network_group") or app_id
        db_user = sc.get("db_user", sanitize_id(app_id).replace("-", "_"))
        db_name = sc.get("db_name", db_user)
        enabled = sc.get("enabled_variants", ["public", "private"])
        if isinstance(enabled, str):
            enabled = [enabled]
        env = []
        for e in tpl.get("env", []):
            env.append({
                "key": e["key"],
                "value": template_replace(e["value"], base, db_user, db_name),
                "required": bool(e.get("required", False)),
            })
        volumes = []
        for v in tpl.get("volumes", []):
            volumes.append({
                "name": v["name"],
                "host": template_replace(v["host"], base, db_user, db_name),
                "container": v["container"],
                "mode": v.get("mode", "rw"),
                "owner": v.get("owner", ""),
            })
        health = tpl.get("health", {})
        sidecars.append({
            "name": name,
            "full_name": full,
            "template": tpl_name,
            "image": tpl["image"],
            "command": list(tpl.get("command", [])),
            "shm_size": tpl.get("shm_size", ""),
            "network": "",
            "enabled_variants": enabled,
            "preload": bool(tpl.get("preload", False)),
            "env": env,
            "volumes": volumes,
            "ports": [],
            "health": {
                "cmd": template_replace(health.get("cmd", ""), base, db_user, db_name),
                "interval": health.get("interval", ""),
                "timeout": health.get("timeout", ""),
                "retries": int(health.get("retries", 30)),
            },
            "db_user": db_user,
            "db_name": db_name,
        })
    return sidecars


def sidecar_by_template(sidecars, tpl):
    for s in sidecars:
        if s["template"] == tpl:
            return s
    return None


def sidecar_env_for_app(app_id: str, sidecars, ov: dict):
    """Environment derived from sidecar topology (hostnames, secrets, URLs)."""
    env = []

    def add(key, value, required=False, variants=""):
        env.append({"key": key, "value": value, "required": required, "variants": variants})

    pg = sidecar_by_template(sidecars, "postgres")
    db = sidecar_by_template(sidecars, "mariadb")
    redis = sidecar_by_template(sidecars, "redis")
    minio = sidecar_by_template(sidecars, "minio")
    lb = sidecar_by_template(sidecars, "lbrowser")

    if app_id == "joplin-server" and pg:
        add("APP_BASE_URL", "${PUBLIC_URL}", True)
        add("DB_CLIENT", "pg", True)
        add("POSTGRES_HOST", pg["full_name"], True)
        add("POSTGRES_PORT", "5432", True)
        add("POSTGRES_DATABASE", pg["db_name"], True)
        add("POSTGRES_USER", pg["db_user"], True)
        add("POSTGRES_PASSWORD", "${SECRET:pg_password}", True)
        add("DEFAULT_ADMIN_PASSWORD", "${SECRET:admin_password}", True)
    elif app_id == "linkwarden" and pg:
        add("DATABASE_URL", f"postgresql://{pg['db_user']}:${{SECRET:pg_password}}@{pg['full_name']}:5432/{pg['db_name']}", True)
        add("NEXTAUTH_URL", "${PUBLIC_URL}/api/v1/auth", True)
        add("NEXTAUTH_SECRET", "${SECRET:nextauth_secret}", True)
        add("STORAGE_FOLDER", "data", True)
        if lb:
            add("PLAYWRIGHT_WS_URL", f"http://{lb['full_name']}:9222", False, "public")
    elif app_id == "karakeep":
        add("NEXTAUTH_URL", "${PUBLIC_URL}", True)
        add("NEXTAUTH_SECRET", "${SECRET:nextauth_secret}", True)
        if lb:
            add("BROWSER_WEB_URL", f"http://{lb['full_name']}:9222", False, "public")
        add("CRAWLER_STORE_PDF", "true", False)
    elif app_id == "miniflux" and pg:
        add("DATABASE_URL", f"postgres://{pg['db_user']}:${{SECRET:pg_password}}@{pg['full_name']}:5432/{pg['db_name']}?sslmode=disable", True)
        add("RUN_MIGRATIONS", "1", True)
        add("CREATE_ADMIN", "1", True)
        add("ADMIN_USERNAME", "admin", True)
        add("ADMIN_PASSWORD", "${SECRET:admin_password}", True)
    elif app_id == "jellystat" and pg:
        add("POSTGRES_IP", pg["full_name"], True)
        add("POSTGRES_PORT", "5432", True)
        add("POSTGRES_DB", pg["db_name"], True)
        add("POSTGRES_USER", pg["db_user"], True)
        add("POSTGRES_PASSWORD", "${SECRET:pg_password}", True)
        add("JWT_SECRET", "${SECRET:jwt_secret}", True)
    elif app_id == "ente-server" and pg:
        add("ENTE_DB_HOST", pg["full_name"], True)
        add("ENTE_DB_NAME", pg["db_name"], True)
        add("ENTE_DB_USER", pg["db_user"], True)
        add("ENTE_DB_PASSWORD", "${SECRET:pg_password}", True)
        if minio:
            add("ENTE_S3_ENDPOINT", f"{minio['full_name']}:9000", True)
            add("ENTE_S3_KEY", "istoreadmin", True)
            add("ENTE_S3_SECRET", "${SECRET:minio_password}", True)
    elif app_id == "penpot-backend" and pg:
        add("PENPOT_PUBLIC_URI", "http://${HOST_IP}:9001", True)
        add("PENPOT_SECRET_KEY", "${SECRET:penpot_secret}", True)
        add("PENPOT_DATABASE_URI", f"postgresql://{pg['full_name']}/{pg['db_name']}", True)
        add("PENPOT_DATABASE_USERNAME", pg["db_user"], True)
        add("PENPOT_DATABASE_PASSWORD", "${SECRET:pg_password}", True)
        if redis:
            add("PENPOT_REDIS_URI", f"redis://{redis['full_name']}:6379/0", True)
        add("PENPOT_FLAGS", "disable-email-verification disable-secure-session-cookies", False)
    elif app_id == "penpot-frontend":
        add("PENPOT_PUBLIC_URI", "http://${HOST_IP}:9001", True)
        add("PENPOT_BACKEND_URI", "http://penpot-backend:6060", True)
        add("PENPOT_FLAGS", "disable-email-verification disable-secure-session-cookies", False)
    elif app_id == "bookstack" and db:
        add("APP_URL", "${PUBLIC_URL}", True)
        add("DB_HOST", db["full_name"], True)
        add("DB_DATABASE", db["db_name"], True)
        add("DB_USERNAME", db["db_user"], True)
        add("DB_PASSWORD", "${SECRET:mysql_password}", True)
    elif app_id == "piwigo" and db:
        add("PIWIGO_DB_HOST", db["full_name"], True)
        add("PIWIGO_DB_NAME", db["db_name"], True)
        add("PIWIGO_DB_USER", db["db_user"], True)
        add("PIWIGO_DB_PASSWORD", "${SECRET:mysql_password}", True)
    return env


def merge_env(*lists):
    out = {}
    order = []
    for lst in lists:
        for e in lst or []:
            key = e["key"]
            if key not in out:
                order.append(key)
            out[key] = {
                "key": key,
                "value": "" if e.get("value") == "__UNSET__" else e.get("value", ""),
                "required": bool(e.get("required", False)),
                "variants": e.get("variants", ""),
            }
    return [out[k] for k in order]


def build_review(app_id: str, ov: dict, has_dockerfile: bool, auto_notes):
    review = ov.get("review", {}) or {}
    manual = list(review.get("manual", []) or [])
    substantive = list(review.get("notes", []) or [])
    substantive.extend(auto_notes)
    if not has_dockerfile:
        substantive.append("无 Dockerfile，端口/卷来自 docs/RUNBOOK.md 端口索引与人工核对。")
    if manual:
        automation = "manual"
    elif ov.get("needs_config"):
        automation = "needs_config"
    else:
        automation = "auto"
    notes = list(dict.fromkeys(substantive))
    notes.append("未在 OpenWrt/iStoreOS 真机上执行安装回归；仅做 ipk 结构与 JSON schema 静态校验。")
    return {
        "automation": automation,
        "manual": manual,
        "notes": notes,
    }


def build_loong64(app_id: str, desc: dict, ov: dict, overrides: dict, plan_host: int,
                  index: int, links: dict, used_hosts: set):
    base_ports, base_volumes, docker_user = read_dockerfile(app_id)
    has_dockerfile = (REPO / "images" / app_id).is_dir() and any(
        (REPO / "images" / app_id).glob("Dockerfile*"))
    auto_notes = []
    ports = build_ports(app_id, ov, base_ports, plan_host, index, used_hosts, auto_notes)
    volumes = build_volumes(app_id, ov, base_volumes, docker_user)
    sidecars = build_sidecars(app_id, ov, overrides["sidecar_templates"])

    env = merge_env(
        ov.get("env", []),
        sidecar_env_for_app(app_id, sidecars, ov),
    )

    if ov.get("host_network"):
        auto_notes.append("使用 host 网络：端口直接占用宿主端口，不能与其它应用重复监听 53/80 等端口。")
    if ov.get("docker_sock"):
        auto_notes.append("挂载宿主 Docker socket；容器可控制宿主 Docker，只应安装可信应用。")
    if sidecars:
        auto_notes.append("安装器会先启动 sidecar：" + ", ".join(s["full_name"] for s in sidecars) + "。")
    if not ports:
        auto_notes.append("该应用没有对外 Web/服务端口（后台任务或需外部连接）。")

    review = build_review(app_id, ov, has_dockerfile, auto_notes)

    public_image = f"{PUBLIC_REF}/{app_id}:{PUBLIC_IMAGE_TAG}"
    variants = [{"name": "public", "image": public_image, "store_url": PROJECT_URL}]
    compose = ""
    pub = links.get("public", {}).get("apps", {}).get(app_id)
    priv = links.get("private", {}).get("apps", {}).get(app_id)
    if pub:
        variants[0]["image"] = pub.get("image", public_image)
        variants[0]["store_url"] = links.get("public", {}).get("store_url", PROJECT_URL)
        if pub.get("compose"):
            compose = pub["compose"]
    if priv:
        variants.append({
            "name": "private",
            "image": priv.get("image", ""),
            "store_url": links.get("private", {}).get("store_url", PRIVATE_URL),
            "compose": priv.get("compose", ""),
        })
        if not compose:
            compose = priv.get("compose", "")

    loong64 = {
        "schema": 1,
        "source": "dockerfile+runbook+override" if has_dockerfile else "runbook+override",
        "image": variants[0]["image"],
        "default_variant": "public",
        "variants": variants,
        "compose": compose,
        "ports": ports,
        "volumes": volumes,
        "env": env,
        "sidecars": [
            {
                "name": s["name"],
                "full_name": s["full_name"],
                "template": s["template"],
                "image": s["image"],
                "command": s["command"],
                "shm_size": s["shm_size"],
                "network": s["network"],
                "enabled_variants": s["enabled_variants"],
                "preload": s["preload"],
                "env": s["env"],
                "volumes": s["volumes"],
                "ports": s["ports"],
                "health": s["health"],
            }
            for s in sidecars
        ],
        "needs_host_network": bool(ov.get("host_network")),
        "needs_docker_sock": bool(ov.get("docker_sock")),
        "docker_sock_ro": bool(ov.get("docker_sock_ro", True)),
        "devices": list(ov.get("devices", [])),
        "cap_add": list(ov.get("cap_add", [])),
        "group_add": list(ov.get("group_add", [])),
        "sysctls": list(ov.get("sysctls", [])),
        "shm_size": ov.get("shm_size", ""),
        "user": ov.get("user", ""),
        "command": list(ov.get("command", [])),
        "restart": ov.get("restart", "unless-stopped"),
        "network_group": ov.get("network_group", ""),
        "requires_app": ov.get("requires_app", ""),
        "health": ov.get("health", {}),
        "review": review,
        "category": desc.get("category", "Utilities"),
        "image_size": desc.get("image_size", ""),
    }
    return loong64


def render_runtime(l: dict) -> str:
    def rec(fields):
        return "|".join(clean_field(x) for x in fields)

    variants = "\n".join(rec([v.get("name", ""), v.get("image", ""), v.get("store_url", "")])
                         for v in l.get("variants", []))
    ports = "\n".join(rec([p.get("name", ""), p.get("container", 0), p.get("host", 0),
                           p.get("proto", "tcp"), 1 if p.get("primary") else 0])
                      for p in l.get("ports", []))
    volumes = "\n".join(rec([v.get("name", ""), v.get("host", ""), v.get("container", ""),
                             v.get("mode", "rw"), v.get("owner", ""),
                             1 if v.get("primary") else 0, v.get("type", "dir"),
                             v.get("seed", "")])
                        for v in l.get("volumes", []))
    env = "\n".join(rec([e.get("key", ""), e.get("value", ""),
                         1 if e.get("required") else 0, e.get("variants", "")])
                    for e in l.get("env", []))

    sidecars = []
    sc_cmd = []
    sc_env = []
    sc_vols = []
    sc_ports = []
    for s in l.get("sidecars", []):
        h = s.get("health", {}) or {}
        sidecars.append(rec([
            s.get("full_name", ""), s.get("image", ""), s.get("shm_size", ""),
            s.get("network", ""), ",".join(s.get("enabled_variants", [])),
            h.get("cmd", ""), h.get("interval", ""), h.get("timeout", ""),
            h.get("retries", 30), 1 if s.get("preload") else 0,
        ]))
        if s.get("command"):
            sc_cmd.append("^".join([s.get("full_name", "")] + [clean_field(a) for a in s["command"]]))
        for e in s.get("env", []):
            sc_env.append(rec([s.get("full_name", ""), e.get("key", ""), e.get("value", ""),
                               1 if e.get("required") else 0]))
        for v in s.get("volumes", []):
            sc_vols.append(rec([s.get("full_name", ""), v.get("name", ""), v.get("host", ""),
                                v.get("container", ""), v.get("mode", "rw"),
                                v.get("owner", "")]))
        for p in s.get("ports", []):
            sc_ports.append(rec([s.get("full_name", ""), p.get("container", 0),
                                 p.get("host", 0), p.get("proto", "tcp")]))

    lines = [
        f"APP_ID={shq(l.get('name', ''))}",
        f"APP_TITLE={shq(l.get('title', ''))}",
        f"APP_IMAGE={shq(l.get('image', ''))}",
        f"APP_DEFAULT_VARIANT={shq(l.get('default_variant', 'public'))}",
        f"APP_VARIANTS={shq(variants)}",
        f"APP_PORTS={shq(ports)}",
        f"APP_VOLUMES={shq(volumes)}",
        f"APP_ENV={shq(env)}",
        f"APP_SIDECARS={shq(chr(10).join(sidecars))}",
        f"APP_SIDECAR_COMMAND={shq(chr(10).join(sc_cmd))}",
        f"APP_SIDECAR_ENV={shq(chr(10).join(sc_env))}",
        f"APP_SIDECAR_VOLUMES={shq(chr(10).join(sc_vols))}",
        f"APP_SIDECAR_PORTS={shq(chr(10).join(sc_ports))}",
        f"APP_DEVICES={shq(chr(10).join(clean_field(x) for x in l.get('devices', [])))}",
        f"APP_CAPS={shq(chr(10).join(clean_field(x) for x in l.get('cap_add', [])))}",
        f"APP_GROUPS={shq(chr(10).join(clean_field(x) for x in l.get('group_add', [])))}",
        f"APP_SYSCTLS={shq(chr(10).join(clean_field(x) for x in l.get('sysctls', [])))}",
        f"APP_HOST_NETWORK={shq(1 if l.get('needs_host_network') else 0)}",
        f"APP_DOCKER_SOCK={shq(1 if l.get('needs_docker_sock') else 0)}",
        f"APP_DOCKER_SOCK_RO={shq(1 if l.get('docker_sock_ro', True) else 0)}",
        f"APP_SHM={shq(l.get('shm_size', ''))}",
        f"APP_USER={shq(l.get('user', ''))}",
        f"APP_COMMAND={shq('^'.join(clean_field(x) for x in l.get('command', [])))}",
        f"APP_RESTART={shq(l.get('restart', 'unless-stopped'))}",
        f"APP_NETWORK_GROUP={shq(l.get('network_group', ''))}",
        f"APP_REQUIRES_APP={shq(l.get('requires_app', ''))}",
        f"APP_HEALTH_PATH={shq((l.get('health') or {}).get('path', ''))}",
        f"APP_HEALTH_PORT={shq((l.get('health') or {}).get('port', ''))}",
        f"APP_MANUAL={shq('; '.join(l.get('review', {}).get('manual', [])))}",
        f"APP_REVIEW={shq('; '.join(l.get('review', {}).get('notes', [])))}",
        "",
    ]
    return "\n".join(lines)


def description_for(app_id: str, exports: dict, desc: dict):
    zh = ""
    en = ""
    e = exports.get(app_id, {})
    html = e.get("description_html", {}) if isinstance(e, dict) else {}
    zh = html.get("zh_cn", "") or desc.get("istore_description_html", {}).get("zh_cn", "")
    en = html.get("en_us", "") or desc.get("istore_description_html", {}).get("en_us", "")
    if "龙芯版说明" not in zh:
        zh = "<p><strong>龙芯版说明</strong></p>" + zh
    if "LoongArch notes" not in en:
        en = "<p><strong>LoongArch notes</strong></p>" + en
    return zh, en


def write_file(path: Path, data: str, mode: int = 0o644):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data, encoding="utf-8", newline="\n")
    try:
        os.chmod(path, mode)
    except OSError:
        pass


def write_app_sources(app_id: str, meta: dict, runtime: str, primary_host: int, primary_data: str):
    base = HERE / "src" / "app-meta" / app_id
    data = base / "data"
    write_file(base / "control",
               f"Package: app-meta-{app_id}\n"
               f"Version: {PKG_VERSION}\n"
               f"Depends: libc, luci-app-istore-loong64, docker-deps\n"
               f"Provides: app-meta-{app_id}-any\n"
               f"SourceName: app-meta-{app_id}\n"
               f"Section: meta\n"
               f"Architecture: all\n"
               f"Installed-Size: 1\n"
               f"Maintainer: yunix-intel\n"
               f"Description:  Metadata for {app_id} (LoongArch64)\n")
    write_file(base / "postinst", "#!/bin/sh\n"
               '[ "${IPKG_NO_SCRIPT}" = "1" ] && exit 0\n'
               "[ -s ${IPKG_INSTROOT}/lib/functions.sh ] || exit 0\n"
               ". ${IPKG_INSTROOT}/lib/functions.sh\n"
               "default_postinst $0 $@\n", 0o755)
    write_file(base / "prerm", "#!/bin/sh\n"
               "[ -s ${IPKG_INSTROOT}/lib/functions.sh ] || exit 0\n"
               ". ${IPKG_INSTROOT}/lib/functions.sh\n"
               "default_prerm $0 $@\n", 0o755)
    write_file(base / "conffiles", f"/etc/config/{app_id}\n")

    write_file(data / "usr/lib/opkg/meta" / f"{app_id}.json",
               json.dumps(meta, ensure_ascii=False, indent=2) + "\n")
    write_file(data / "usr/libexec/istorec" / f"{app_id}.sh",
               "#!/bin/sh\n"
               f"exec /usr/libexec/istorec/loong64.sh {shq(app_id)} \"$@\"\n", 0o755)
    write_file(data / "usr/share/istore-loong64/apps" / f"{app_id}.conf", runtime)
    write_file(data / "etc/config" / app_id,
               f"config main 'main'\n"
               f"\toption enabled '1'\n"
               f"\toption variant 'public'\n"
               f"\toption image ''\n"
               f"\toption host_port '{primary_host}'\n"
               f"\toption data_path '{primary_data}'\n"
               f"\toption env_file '/etc/istore-loong64/env/{app_id}.env'\n")

    total = sum(p.stat().st_size for p in data.rglob("*") if p.is_file())
    installed_kb = max(1, (total + 1023) // 1024)
    control = (base / "control").read_text(encoding="utf-8")
    control = re.sub(r"(?m)^Installed-Size: .*$", f"Installed-Size: {installed_kb}", control)
    write_file(base / "control", control)


def main():
    descriptions = load_json(REPO / "store/loong64-descriptions.json")
    exports = load_json(REPO / "store/exports/istore-descriptions.json")
    port_plan = load_json(REPO / "store/casaos/port-plan.json")
    links = load_json(REPO / "store/private/links.json")
    overrides = load_json(HERE / "data/runtime-overrides.json")

    apps = descriptions["apps"]
    app_ids = list(apps.keys())
    export_apps = exports.get("apps", exports)
    plan = {e["id"]: e["host_port"] for e in port_plan["apps"]}
    ov_apps = overrides.get("apps", {})

    src_root = HERE / "src" / "app-meta"
    if src_root.exists():
        shutil.rmtree(src_root)
    src_root.mkdir(parents=True)

    used_hosts = set()
    manifest = {"schema": 1, "generated": "2026-10-25", "release": RELEASE,
                "package_version": PKG_VERSION, "app_count": len(app_ids), "apps": {}}

    for index, app_id in enumerate(app_ids):
        desc = apps[app_id]
        ov = ov_apps.get(app_id, {})
        loong64 = build_loong64(app_id, desc, ov, overrides, plan.get(app_id, 0),
                                index, links, used_hosts)
        zh, en = description_for(app_id, export_apps, desc)
        title = desc.get("title", {})
        meta = {
            "name": app_id,
            "title": title.get("zh_cn") or app_id,
            "title_en": title.get("en_us") or app_id,
            "entry": f"/cgi-bin/luci/admin/services/istore-loong64/app?app={app_id}",
            "author": "yunix-intel",
            "website": PROJECT_URL,
            "version": APP_VERSION,
            "release": RELEASE,
            "arch": ["all"],
            "description": zh,
            "description_en": en,
            "tags": CATEGORY_TAGS.get(desc.get("category", "Utilities"), ["tool"]),
            "depends": ["luci-app-istore-loong64", "docker-deps"],
            "loong64": loong64,
        }
        # runtime needs the title; rebuild after title is known
        loong64["title"] = meta["title"]
        loong64["name"] = app_id
        loong64["runtime"] = render_runtime(loong64)

        primary = next((p for p in loong64["ports"] if p.get("primary")), None)
        primary_host = primary["host"] if primary else 0
        primary_vol = next((v for v in loong64["volumes"] if v.get("primary")), None)
        primary_data = primary_vol["host"] if primary_vol else ""
        write_app_sources(app_id, meta, loong64["runtime"], primary_host, primary_data)

        manifest["apps"][app_id] = {
            "title": meta["title"],
            "image": loong64["image"],
            "automation": loong64["review"]["automation"],
            "manual": loong64["review"]["manual"],
            "ports": len(loong64["ports"]),
            "volumes": len(loong64["volumes"]),
            "sidecars": [s["full_name"] for s in loong64["sidecars"]],
            "host_network": loong64["needs_host_network"],
            "docker_sock": loong64["needs_docker_sock"],
        }

    write_file(HERE / "data/build-manifest.json",
               json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")

    auto = sum(1 for a in manifest["apps"].values() if a["automation"] == "auto")
    needs = sum(1 for a in manifest["apps"].values() if a["automation"] == "needs_config")
    manual = sum(1 for a in manifest["apps"].values() if a["automation"] == "manual")
    print(f"generated {len(app_ids)} app-meta sources under {src_root}")
    print(f"automation: auto={auto} needs_config={needs} manual={manual}")
    print(f"host ports reserved: {len(used_hosts)}")


if __name__ == "__main__":
    main()
