#!/usr/bin/env python3
"""Static validation for store/istore.

Checks:
  * 115 app-meta sources and metadata JSON schema
  * required Chinese/English LoongArch description text
  * generated runtime projection matches structured JSON
  * ipk outer/inner tar structure and payloads
  * Packages / Packages.gz / Packages.sig consistency

Exit code is non-zero when any hard check fails.
"""

from __future__ import annotations

import gzip
import hashlib
import io
import json
import re
import sys
import tarfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent

TOP_REQUIRED = [
    "name", "title", "title_en", "entry", "author", "website", "version",
    "release", "arch", "description", "description_en", "tags", "depends",
    "loong64",
]
LOONG_REQUIRED = [
    "schema", "image", "default_variant", "variants", "ports", "volumes",
    "env", "sidecars", "needs_host_network", "needs_docker_sock",
    "review", "runtime",
]
RUNTIME_REQUIRED = [
    "APP_ID", "APP_TITLE", "APP_IMAGE", "APP_DEFAULT_VARIANT", "APP_VARIANTS",
    "APP_PORTS", "APP_VOLUMES", "APP_ENV", "APP_SIDECARS",
    "APP_SIDECAR_COMMAND", "APP_SIDECAR_ENV", "APP_SIDECAR_VOLUMES",
    "APP_SIDECAR_PORTS", "APP_DEVICES", "APP_CAPS", "APP_GROUPS",
    "APP_SYSCTLS", "APP_HOST_NETWORK", "APP_DOCKER_SOCK", "APP_DOCKER_SOCK_RO",
    "APP_SHM", "APP_USER", "APP_COMMAND", "APP_RESTART", "APP_NETWORK_GROUP",
    "APP_REQUIRES_APP", "APP_HEALTH_PATH", "APP_HEALTH_PORT", "APP_MANUAL",
    "APP_REVIEW",
]

errors = []
warnings = []


def err(msg):
    errors.append(msg)


def warn(msg):
    warnings.append(msg)


def load_json(path: Path):
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def parse_runtime(text: str) -> dict:
    lines = text.split("\n")
    out = {}
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r"^([A-Z0-9_]+)='(.*)$", line)
        if not m:
            i += 1
            continue
        key, rest = m.group(1), m.group(2)
        buf = [rest]

        def closed(s):
            return s.endswith("'") and not s.endswith("\\'")

        while not closed(buf[-1]):
            i += 1
            if i >= len(lines):
                raise ValueError(f"unterminated runtime assignment {key}")
            buf.append(lines[i])
        val = "\n".join(buf)[:-1].replace("'\\''", "'")
        out[key] = val
        i += 1
    return out


def records(text: str):
    return [line.split("|") for line in text.split("\n") if line]


def check_meta(app_id: str, meta: dict):
    for key in TOP_REQUIRED:
        if key not in meta:
            err(f"{app_id}: missing top-level key {key}")
    if meta.get("name") != app_id:
        err(f"{app_id}: name != id")
    if meta.get("arch") != ["all"]:
        err(f"{app_id}: arch must be ['all']")
    if "龙芯版说明" not in meta.get("description", ""):
        err(f"{app_id}: description missing 龙芯版说明")
    if "LoongArch notes" not in meta.get("description_en", ""):
        err(f"{app_id}: description_en missing LoongArch notes")
    if not str(meta.get("entry", "")).startswith("/cgi-bin/luci/"):
        err(f"{app_id}: entry is not a LuCI path")

    l = meta.get("loong64", {})
    for key in LOONG_REQUIRED:
        if key not in l:
            err(f"{app_id}: loong64 missing {key}")
    if l.get("schema") != 1:
        err(f"{app_id}: loong64.schema != 1")
    if not l.get("image"):
        err(f"{app_id}: empty image")
    variants = l.get("variants", [])
    if not variants or not any(v.get("name") == "public" for v in variants):
        err(f"{app_id}: no public variant")
    for v in variants:
        if v.get("name") not in ("public", "private"):
            err(f"{app_id}: bad variant name {v.get('name')}")
        if v.get("name") == "public" and not str(v.get("image", "")).endswith(":24.10-la5"):
            warn(f"{app_id}: public image is not tagged 24.10-la5: {v.get('image')}")
        if v.get("name") == "private" and not str(v.get("image", "")).startswith("local/"):
            warn(f"{app_id}: private image is not local/: {v.get('image')}")

    ports = l.get("ports", [])
    primaries = [p for p in ports if p.get("primary")]
    if ports and len(primaries) != 1:
        err(f"{app_id}: expected exactly one primary port, got {len(primaries)}")
    for p in ports:
        c = p.get("container")
        h = p.get("host")
        if not isinstance(c, int) or not (1 <= c <= 65535):
            err(f"{app_id}: bad container port {c}")
        if not isinstance(h, int) or h < 0 or h > 65535:
            err(f"{app_id}: bad host port {h}")
        if p.get("proto") not in ("tcp", "udp"):
            err(f"{app_id}: bad proto {p.get('proto')}")
        if not p.get("name"):
            err(f"{app_id}: empty port name")

    for v in l.get("volumes", []):
        if not str(v.get("container", "")).startswith("/"):
            err(f"{app_id}: volume container not absolute: {v.get('container')}")
        if v.get("host") and not str(v.get("host")).startswith("/"):
            err(f"{app_id}: volume host not absolute: {v.get('host')}")
        if v.get("mode") not in ("rw", "ro"):
            err(f"{app_id}: bad volume mode {v.get('mode')}")
        if v.get("type") not in ("dir", "file"):
            err(f"{app_id}: bad volume type {v.get('type')}")
    prim_vols = [v for v in l.get("volumes", []) if v.get("primary")]
    if len(prim_vols) > 1:
        err(f"{app_id}: more than one primary volume")

    env_keys = []
    for e in l.get("env", []):
        key = e.get("key", "")
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
            err(f"{app_id}: bad env key {key}")
        if "|" in str(e.get("value", "")) or "^" in str(e.get("value", "")):
            err(f"{app_id}: env {key} contains a record separator")
        env_keys.append(key)
    if len(env_keys) != len(set(env_keys)):
        err(f"{app_id}: duplicate env keys")

    sc_names = []
    for s in l.get("sidecars", []):
        if not s.get("name") or not s.get("image"):
            err(f"{app_id}: sidecar missing name/image")
        sc_names.append(s.get("full_name"))
        if not set(s.get("enabled_variants", [])).issubset({"public", "private"}):
            err(f"{app_id}: sidecar {s.get('name')} bad enabled_variants")
        for v in s.get("volumes", []):
            if not str(v.get("host", "")).startswith("/"):
                err(f"{app_id}: sidecar volume host not absolute: {v.get('host')}")
    if len(sc_names) != len(set(sc_names)):
        err(f"{app_id}: duplicate sidecar full_name")

    review = l.get("review", {})
    if review.get("automation") not in ("auto", "needs_config", "manual"):
        err(f"{app_id}: bad automation {review.get('automation')}")
    if review.get("automation") == "manual" and not review.get("manual"):
        err(f"{app_id}: manual automation without manual reasons")

    # runtime projection consistency
    rt = parse_runtime(l.get("runtime", ""))
    for key in RUNTIME_REQUIRED:
        if key not in rt:
            err(f"{app_id}: runtime missing {key}")
    if rt.get("APP_ID") != app_id:
        err(f"{app_id}: runtime APP_ID mismatch")
    if rt.get("APP_IMAGE") != l.get("image"):
        err(f"{app_id}: runtime APP_IMAGE mismatch")

    expected_ports = [
        [p.get("name", ""), str(p.get("container")), str(p.get("host")),
         p.get("proto"), "1" if p.get("primary") else "0"]
        for p in ports
    ]
    actual_ports = records(rt.get("APP_PORTS", ""))
    if actual_ports != expected_ports:
        err(f"{app_id}: runtime APP_PORTS differs from JSON")

    expected_vols = [
        [v.get("name", ""), v.get("host", ""), v.get("container", ""),
         v.get("mode", "rw"), v.get("owner", ""), "1" if v.get("primary") else "0",
         v.get("type", "dir"), v.get("seed", "")]
        for v in l.get("volumes", [])
    ]
    actual_vols = records(rt.get("APP_VOLUMES", ""))
    if actual_vols != expected_vols:
        err(f"{app_id}: runtime APP_VOLUMES differs from JSON")

    expected_env = [
        [e.get("key", ""), e.get("value", ""), "1" if e.get("required") else "0",
         e.get("variants", "")]
        for e in l.get("env", [])
    ]
    actual_env = records(rt.get("APP_ENV", ""))
    if actual_env != expected_env:
        err(f"{app_id}: runtime APP_ENV differs from JSON")

    expected_sc = [
        [s.get("full_name", ""), s.get("image", ""), s.get("shm_size", ""),
         s.get("network", ""), ",".join(s.get("enabled_variants", [])),
         s.get("health", {}).get("cmd", ""), s.get("health", {}).get("interval", ""),
         s.get("health", {}).get("timeout", ""), str(s.get("health", {}).get("retries", 30)),
         "1" if s.get("preload") else "0"]
        for s in l.get("sidecars", [])
    ]
    actual_sc = records(rt.get("APP_SIDECARS", ""))
    if actual_sc != expected_sc:
        err(f"{app_id}: runtime APP_SIDECARS differs from JSON")


def read_ipk_control(ipk: Path):
    with tarfile.open(ipk, "r:gz") as outer:
        names = outer.getnames()
        if "./debian-binary" not in names:
            err(f"{ipk.name}: missing ./debian-binary")
            return None
        deb = outer.extractfile("./debian-binary").read()
        if deb != b"2.0\n":
            err(f"{ipk.name}: debian-binary is not 2.0")
        ctl_member = "./control.tar.gz" if "./control.tar.gz" in names else "control.tar.gz"
        data_member = "./data.tar.gz" if "./data.tar.gz" in names else "data.tar.gz"
        if ctl_member not in names:
            err(f"{ipk.name}: missing control.tar.gz")
            return None
        if data_member not in names:
            err(f"{ipk.name}: missing data.tar.gz")
            return None
        ctl_tgz = outer.extractfile(ctl_member).read()
        data_tgz = outer.extractfile(data_member).read()
    with tarfile.open(fileobj=io.BytesIO(ctl_tgz), mode="r:gz") as inner:
        ctl_names = inner.getnames()
        for name in ctl_names:
            if name in ("./control", "control", "./postinst", "postinst",
                        "./prerm", "prerm", "./conffiles", "conffiles"):
                if b"\r" in inner.extractfile(name).read():
                    err(f"{ipk.name}: {name} contains CR (CRLF payload)")
        for need in ("./control", "control"):
            if need in ctl_names:
                text = inner.extractfile(need).read().decode("utf-8")
                break
        else:
            err(f"{ipk.name}: control.tar.gz has no control")
            text = ""
        if "./postinst" not in ctl_names and "postinst" not in ctl_names:
            err(f"{ipk.name}: control.tar.gz has no postinst")
        if "./prerm" not in ctl_names and "prerm" not in ctl_names:
            err(f"{ipk.name}: control.tar.gz has no prerm")
    with tarfile.open(fileobj=io.BytesIO(data_tgz), mode="r:gz") as inner:
        data_names = inner.getnames()
    return text, data_names, data_tgz


def check_ipks(app_ids):
    public_url = "https://github.com/yunix-intel/istoreos-loongarch64"
    private_url = "https://github.com/yunix-intel/istore-la-private"
    feeds = [("public", public_url), ("private", private_url)]
    any_feed = False
    for feed, store_url in feeds:
        root = HERE / "feed" / feed
        meta_dir = root / "all" / "meta"
        luci_dir = root / "all" / "nas_luci"
        if not meta_dir.is_dir():
            warn(f"feed/{feed} not built; skipping its ipk checks")
            continue
        any_feed = True
        ipks = sorted(meta_dir.glob("app-meta-*.ipk"))
        if len(ipks) != len(app_ids):
            err(f"feed/{feed}: {len(ipks)} ipks, expected {len(app_ids)}")
        if not (root / "isfeeds.conf").is_file():
            err(f"feed/{feed}: missing isfeeds.conf")
        for app_id in app_ids:
            matches = list(meta_dir.glob(f"app-meta-{app_id}_*.ipk"))
            if len(matches) != 1:
                err(f"feed/{feed}/{app_id}: expected one ipk, found {len(matches)}")
                continue
            ipk = matches[0]
            parsed = read_ipk_control(ipk)
            if not parsed:
                continue
            control, data_names, data_tgz = parsed
            if f"Package: app-meta-{app_id}" not in control:
                err(f"{ipk.name}: control package name mismatch")
            if f"{feed} feed" not in control:
                err(f"{ipk.name}: control description missing feed label")
            need = [
                f"./usr/lib/opkg/meta/{app_id}.json",
                f"./usr/libexec/istorec/{app_id}.sh",
                f"./etc/config/{app_id}",
                f"./usr/share/istore-loong64/apps/{app_id}.conf",
            ]
            for n in need:
                if n not in data_names:
                    err(f"{ipk.name}: data missing {n}")
            with tarfile.open(fileobj=io.BytesIO(data_tgz), mode="r:gz") as inner:
                for name in data_names:
                    if name.endswith((".sh", ".conf")) or name.startswith("./etc/config/"):
                        raw = inner.extractfile(name).read()
                        if b"\r" in raw:
                            err(f"{ipk.name}: {name} contains CR (CRLF payload)")
            if f"./usr/lib/opkg/meta/{app_id}.json" not in data_names:
                continue
            with tarfile.open(fileobj=io.BytesIO(data_tgz), mode="r:gz") as inner:
                embedded_raw = inner.extractfile(f"./usr/lib/opkg/meta/{app_id}.json").read()
                conf_raw = inner.extractfile(
                    f"./usr/share/istore-loong64/apps/{app_id}.conf").read().decode("utf-8")
                uci_raw = inner.extractfile(f"./etc/config/{app_id}").read().decode("utf-8")
            try:
                embedded = json.loads(embedded_raw.decode("utf-8"))
            except Exception as exc:
                err(f"{ipk.name}: embedded JSON invalid: {exc}")
                continue
            l = embedded.get("loong64", {})
            variants = l.get("variants", [])
            names = [v.get("name") for v in variants]
            src_meta_path = (HERE / "src" / "app-meta" / app_id / "data" / "usr" /
                             "lib" / "opkg" / "meta" / f"{app_id}.json")
            src_has_private = False
            if src_meta_path.is_file():
                src = load_json(src_meta_path)
                src_has_private = any(v.get("name") == "private"
                                      for v in src.get("loong64", {}).get("variants", []))
            if feed == "public":
                if names != ["public"]:
                    err(f"feed/public/{app_id}: variants must be exactly ['public'], got {names}")
                if str(l.get("image", "")).startswith("local/"):
                    err(f"feed/public/{app_id}: public feed references local image")
                default = "public"
            else:
                if embedded.get("website") != store_url:
                    err(f"feed/private/{app_id}: website is not the private store URL")
                if src_has_private:
                    default = "private"
                    if l.get("default_variant") != "private":
                        err(f"feed/private/{app_id}: private-capable app must default private")
                    if not str(l.get("image", "")).startswith("local/"):
                        err(f"feed/private/{app_id}: private default image is not local/*")
                else:
                    default = "public"
                    if l.get("default_variant") != "public":
                        err(f"feed/private/{app_id}: default must stay public")
                    if str(l.get("image", "")).startswith("local/"):
                        err(f"feed/private/{app_id}: no private image but image is local/*")
                    if variants and variants[0].get("store_url") != store_url:
                        err(f"feed/private/{app_id}: public variant store_url is not private")
            if l.get("default_variant") != default:
                err(f"{ipk.name}: default_variant {l.get('default_variant')} != {default}")
            rt = parse_runtime(l.get("runtime", ""))
            if rt.get("APP_DEFAULT_VARIANT") != default:
                err(f"{ipk.name}: runtime default variant mismatch")
            if rt.get("APP_IMAGE") != l.get("image"):
                err(f"{ipk.name}: runtime image mismatch")
            if f"option variant '{default}'" not in uci_raw:
                err(f"{ipk.name}: UCI config does not default to {default}")
            if f"APP_DEFAULT_VARIANT='{default}'" not in conf_raw:
                err(f"{ipk.name}: conf does not default to {default}")

        generic = sorted(luci_dir.glob("luci-app-istore-loong64_*.ipk"))
        if len(generic) != 1:
            err(f"feed/{feed}: expected one generic ipk, found {len(generic)}")
        else:
            parsed = read_ipk_control(generic[0])
            if parsed:
                control, data_names, _ = parsed
                if "Package: luci-app-istore-loong64" not in control:
                    err("generic package name mismatch")
                for n in ("./usr/libexec/istorec/loong64.sh",
                          "./usr/lib/lua/luci/controller/istore_loong64.lua",
                          "./usr/lib/lua/luci/view/istore_loong64/app.htm",
                          "./usr/lib/lua/luci/view/istore_loong64/apps.htm",
                          "./etc/config/istore_loong64"):
                    if n not in data_names:
                        err(f"generic package missing {n}")
    if not any_feed:
        warn("neither feed/public nor feed/private is built")


def check_index(feed_dir: Path, expected_count: int):
    packages = feed_dir / "Packages"
    if not packages.is_file():
        err(f"{feed_dir.name}: missing Packages")
        return
    text = packages.read_text(encoding="utf-8")
    blocks = [b for b in text.strip().split("\n\n") if b.strip()]
    if len(blocks) != expected_count:
        err(f"{feed_dir.name}: Packages has {len(blocks)} entries, expected {expected_count}")
    seen = set()
    for block in blocks:
        fields = {}
        key = None
        for line in block.splitlines():
            if line[:1] in (" ", "\t") and key:
                fields[key] += " " + line.strip()
            elif ":" in line:
                key, val = line.split(":", 1)
                fields[key.strip()] = val.strip()
        pkg = fields.get("Package", "")
        if pkg in seen:
            err(f"{feed_dir.name}: duplicate package {pkg}")
        seen.add(pkg)
        fn = fields.get("Filename", "")
        ipk = feed_dir / fn
        if not ipk.is_file():
            err(f"{feed_dir.name}: {pkg}: missing {fn}")
            continue
        data = ipk.read_bytes()
        if str(len(data)) != fields.get("Size"):
            err(f"{feed_dir.name}: {pkg}: Size mismatch")
        digest = hashlib.sha256(data).hexdigest()
        if digest != fields.get("SHA256sum"):
            err(f"{feed_dir.name}: {pkg}: SHA256 mismatch")
    gz_path = feed_dir / "Packages.gz"
    if not gz_path.is_file():
        err(f"{feed_dir.name}: missing Packages.gz")
    else:
        try:
            raw = gzip.decompress(gz_path.read_bytes()).decode("utf-8")
        except Exception as exc:
            err(f"{feed_dir.name}: Packages.gz invalid: {exc}")
            raw = ""
        if raw != text:
            err(f"{feed_dir.name}: Packages.gz != Packages")
    if not (feed_dir / "Packages.sig").is_file():
        err(f"{feed_dir.name}: missing Packages.sig")


def main():
    descriptions = load_json(REPO / "store/loong64-descriptions.json")
    app_ids = list(descriptions["apps"].keys())
    src_root = HERE / "src" / "app-meta"
    dirs = sorted(p.name for p in src_root.iterdir() if p.is_dir()) if src_root.is_dir() else []
    if dirs != sorted(app_ids):
        missing = sorted(set(app_ids) - set(dirs))
        extra = sorted(set(dirs) - set(app_ids))
        if missing:
            err(f"missing app sources: {missing}")
        if extra:
            err(f"extra app sources: {extra}")

    manual = []
    counts = {"auto": 0, "needs_config": 0, "manual": 0}
    hosts = {}
    sidecar_names = {}
    for app_id in app_ids:
        meta_path = src_root / app_id / "data" / "usr" / "lib" / "opkg" / "meta" / f"{app_id}.json"
        if not meta_path.is_file():
            err(f"{app_id}: missing meta JSON")
            continue
        try:
            meta = load_json(meta_path)
        except Exception as exc:
            err(f"{app_id}: invalid JSON: {exc}")
            continue
        check_meta(app_id, meta)
        l = meta.get("loong64", {})
        counts[l.get("review", {}).get("automation", "auto")] = counts.get(
            l.get("review", {}).get("automation", "auto"), 0) + 1
        if l.get("review", {}).get("automation") == "manual":
            manual.append(app_id)
        if not l.get("needs_host_network"):
            for p in l.get("ports", []):
                key = (p.get("host"), p.get("proto"))
                if key in hosts and hosts[key] != app_id:
                    err(f"host port collision {key}: {hosts[key]} and {app_id}")
                hosts[key] = app_id
        for s in l.get("sidecars", []):
            name = s.get("full_name")
            if name in sidecar_names and sidecar_names[name] != app_id:
                err(f"sidecar name collision {name}: {sidecar_names[name]} and {app_id}")
            sidecar_names[name] = app_id

        control = src_root / app_id / "control"
        if not control.is_file():
            err(f"{app_id}: missing control")
        else:
            ctext = control.read_text(encoding="utf-8")
            for need in (f"Package: app-meta-{app_id}", "Architecture: all", "Section: meta"):
                if need not in ctext:
                    err(f"{app_id}: control missing {need}")
        wrapper = src_root / app_id / "data" / "usr" / "libexec" / "istorec" / f"{app_id}.sh"
        if not wrapper.is_file() or "loong64.sh" not in wrapper.read_text(encoding="utf-8"):
            err(f"{app_id}: wrapper missing or wrong")
        conf = src_root / app_id / "data" / "etc" / "config" / app_id
        if not conf.is_file() or "config main" not in conf.read_text(encoding="utf-8"):
            err(f"{app_id}: UCI config missing or wrong")

    check_ipks(app_ids)
    for feed_name in ("public", "private"):
        feed = HERE / "feed" / feed_name
        if feed.is_dir():
            check_index(feed / "all" / "meta", len(app_ids))
            check_index(feed / "all" / "nas_luci", 1)

    print(f"apps checked: {len(app_ids)}")
    print(f"automation: auto={counts.get('auto',0)} needs_config={counts.get('needs_config',0)} manual={counts.get('manual',0)}")
    print(f"manual apps ({len(manual)}): {' '.join(manual)}")
    if warnings:
        print(f"warnings: {len(warnings)}")
        for w in warnings[:50]:
            print("  WARN", w)
    if errors:
        print(f"ERRORS: {len(errors)}")
        for e in errors[:100]:
            print("  ERR ", e)
        return 1
    print("validation OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
