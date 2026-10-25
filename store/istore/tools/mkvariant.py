#!/usr/bin/env python3
"""Create a public or private feed variant of one app-meta source directory.

Usage:
  mkvariant.py <src-app-dir> <dest-app-dir> <public|private>
               <public-store-url> <private-store-url>

Public feed:
  * only the public image variant is kept
  * default_variant = public, image = public image

Private feed:
  * apps with a private single-image variant (linkwarden/karakeep) default to
    it and reference local/*; public remains available as an alternative
  * apps without a private image keep the public image but every store URL
    points at the private store

No image is pushed by this script.
"""

from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import gen_istore  # noqa: E402


def rewrite_control(path: Path, feed: str):
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"(?m)^Description: .*$",
                  f"Description:  Metadata (LoongArch64, {feed} feed)", text)
    if feed == "private":
        def bump(m):
            version = m.group(1)
            return f"Version: {version}" if version.endswith("-p1") else f"Version: {version}-p1"
        text = re.sub(r"(?m)^Version: (\S+)$", bump, text)
    path.write_text(text, encoding="utf-8", newline="\n")


def main():
    if len(sys.argv) != 6:
        raise SystemExit("usage: mkvariant.py <src> <dest> <public|private> <public-url> <private-url>")
    src = Path(sys.argv[1])
    dest = Path(sys.argv[2])
    feed = sys.argv[3]
    public_url = sys.argv[4]
    private_url = sys.argv[5]
    if feed not in ("public", "private"):
        raise SystemExit("feed must be public or private")

    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest)

    ctl = (dest / "control").read_text(encoding="utf-8")
    m = re.search(r"(?m)^Package: app-meta-(.+)$", ctl)
    if not m:
        raise SystemExit(f"{src}: cannot find package name")
    app_id = m.group(1)

    meta_path = dest / "data" / "usr" / "lib" / "opkg" / "meta" / f"{app_id}.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    l = meta["loong64"]
    variants = l.get("variants", [])
    pub = next((v for v in variants if v.get("name") == "public"), None)
    priv = next((v for v in variants if v.get("name") == "private"), None)
    if not pub:
        raise SystemExit(f"{app_id}: no public variant")

    if feed == "public":
        l["default_variant"] = "public"
        l["image"] = pub.get("image", l.get("image", ""))
        l["variants"] = [pub]
        l["store_url"] = public_url
        l["compose"] = pub.get("compose", l.get("compose", "")) or ""
        meta["website"] = public_url
        default = "public"
    else:
        meta["website"] = private_url
        l["store_url"] = private_url
        if priv:
            l["default_variant"] = "private"
            l["image"] = priv.get("image", l.get("image", ""))
            l["variants"] = [pub, priv]
            l["compose"] = priv.get("compose", "") or l.get("compose", "")
            default = "private"
        else:
            pub = dict(pub)
            pub["store_url"] = private_url
            l["default_variant"] = "public"
            l["image"] = pub.get("image", l.get("image", ""))
            l["variants"] = [pub]
            l["compose"] = l.get("compose", "")
            default = "public"

    l["runtime"] = gen_istore.render_runtime(l)
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
                         encoding="utf-8", newline="\n")

    conf = dest / "data" / "usr" / "share" / "istore-loong64" / "apps" / f"{app_id}.conf"
    conf.write_text(l["runtime"], encoding="utf-8", newline="\n")

    uci = dest / "data" / "etc" / "config" / app_id
    text = uci.read_text(encoding="utf-8")
    text = re.sub(r"(?m)^(\s*option variant )'.*'$", rf"\1'{default}'", text)
    uci.write_text(text, encoding="utf-8", newline="\n")

    rewrite_control(dest / "control", feed)
    print(f"{feed}: {app_id} default={default} image={l['image']}")


if __name__ == "__main__":
    main()
