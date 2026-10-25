#!/usr/bin/env python3
"""Generate deterministic opkg Packages / Packages.gz for a feed directory.

Usage: mkindex.py <feed-dir>

If USIGN_KEY is set and `usign` is available, Packages.sig is a real usign
signature; otherwise Packages.sig is written empty (unsigned development feed).
"""

from __future__ import annotations

import gzip
import hashlib
import io
import os
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

FIELDS = [
    "Package", "Version", "Depends", "Provides", "SourceName", "Section",
    "Architecture", "Installed-Size", "Filename", "Size", "SHA256sum",
    "Description",
]


def read_control(ipk: Path) -> dict:
    with tarfile.open(ipk, "r:gz") as outer:
        member = None
        for name in ("./control.tar.gz", "control.tar.gz"):
            try:
                member = outer.getmember(name)
                break
            except KeyError:
                continue
        if member is None:
            raise SystemExit(f"{ipk}: no control.tar.gz")
        control_tgz = outer.extractfile(member).read()
    with tarfile.open(fileobj=io.BytesIO(control_tgz), mode="r:gz") as inner:
        member = None
        for name in ("./control", "control"):
            try:
                member = inner.getmember(name)
                break
            except KeyError:
                continue
        if member is None:
            raise SystemExit(f"{ipk}: no control file")
        text = inner.extractfile(member).read().decode("utf-8", "replace")
    data = {}
    key = None
    for line in text.splitlines():
        if line[:1] in (" ", "\t") and key:
            data[key] += "\n" + line.strip()
        elif ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            data[key] = value.strip()
    return data


def gz(data: bytes) -> bytes:
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb", compresslevel=9, mtime=0, filename="") as fh:
        fh.write(data)
    return buf.getvalue()


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: mkindex.py <feed-dir>")
    feed = Path(sys.argv[1])
    ipks = sorted(feed.glob("*.ipk"))
    if not ipks:
        raise SystemExit(f"{feed}: no .ipk files")

    entries = []
    manifest = []
    for ipk in ipks:
        ctl = read_control(ipk)
        data = ipk.read_bytes()
        ctl["Filename"] = ipk.name
        ctl["Size"] = str(len(data))
        ctl["SHA256sum"] = hashlib.sha256(data).hexdigest()
        ctl.setdefault("Installed-Size", "1")
        entries.append(ctl)
        manifest.append(f"{ctl.get('Package','')} {ctl.get('Version','')} {ipk.name} {len(data)} {ctl['SHA256sum']}")

    entries.sort(key=lambda c: c.get("Package", ""))
    blocks = []
    for ctl in entries:
        lines = []
        for field in FIELDS:
            if field in ctl and ctl[field] != "":
                value = ctl[field].replace("\n", " ")
                lines.append(f"{field}: {value}")
        # keep any extra control fields after the known ones
        for field, value in ctl.items():
            if field not in FIELDS and field not in ("Filename", "Size", "SHA256sum"):
                lines.append(f"{field}: {value}")
        blocks.append("\n".join(lines))
    packages = "\n\n".join(blocks) + "\n"
    (feed / "Packages").write_text(packages, encoding="utf-8", newline="\n")
    (feed / "Packages.gz").write_bytes(gz(packages.encode("utf-8")))
    (feed / "Packages.manifest").write_text("\n".join(manifest) + "\n", encoding="utf-8", newline="\n")

    sig = feed / "Packages.sig"
    usign_key = os.environ.get("USIGN_KEY", "")
    if usign_key and shutil.which("usign"):
        subprocess.run(["usign", "-S", "-m", str(feed / "Packages"), "-s", usign_key, "-x", str(sig)],
                       check=True)
        print(f"{feed}: signed with {usign_key}")
    else:
        sig.write_bytes(b"")
        print(f"{feed}: unsigned Packages.sig (set USIGN_KEY to sign)")


if __name__ == "__main__":
    main()
