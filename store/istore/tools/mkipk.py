#!/usr/bin/env python3
"""Build an OpenWrt/iStore .ipk deterministically.

Layout matches the upstream iStore meta packages:
  outer tar.gz: ./debian-binary, ./data.tar.gz, ./control.tar.gz
  control.tar.gz: ./control, ./postinst, ./prerm, ./conffiles (optional)
  data.tar.gz: ./etc/..., ./usr/...

Usage: mkipk.py <source-dir> <output.ipk>

<source-dir> must contain `control` and `data/`; optional `postinst`,
`prerm`, `conffiles`, `preinst`, `postrm`.
"""

from __future__ import annotations

import gzip
import io
import os
import sys
import tarfile
from pathlib import Path

EPOCH = int(os.environ.get("SOURCE_DATE_EPOCH", "1792886400"))
CONTROL_FILES = ["preinst", "postinst", "prerm", "postrm", "conffiles"]


def gz_bytes(data: bytes) -> bytes:
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb", compresslevel=9, mtime=0, filename="") as gz:
        gz.write(data)
    return buf.getvalue()


def lf(data: bytes) -> bytes:
    """Normalize CRLF for text payloads built on Windows."""
    if b"\x00" in data:
        return data
    return data.replace(b"\r\n", b"\n")


def add_dir(tar: tarfile.TarFile, name: str):
    ti = tarfile.TarInfo(name)
    ti.type = tarfile.DIRTYPE
    ti.mode = 0o755
    ti.uid = ti.gid = 0
    ti.uname = ti.gname = "root"
    ti.mtime = EPOCH
    tar.addfile(ti)


def add_file(tar: tarfile.TarFile, name: str, data: bytes, mode: int = 0o644):
    ti = tarfile.TarInfo(name)
    ti.size = len(data)
    ti.mode = mode
    ti.uid = ti.gid = 0
    ti.uname = ti.gname = "root"
    ti.mtime = EPOCH
    tar.addfile(ti, io.BytesIO(data))


def tar_bytes(entries):
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w", format=tarfile.USTAR_FORMAT) as tar:
        add_dir(tar, "./")
        for name, data, mode in entries:
            add_file(tar, name, data, mode)
    return buf.getvalue()


def build_control(src: Path) -> bytes:
    control = (src / "control").read_text(encoding="utf-8")
    if not control.endswith("\n"):
        control += "\n"
    entries = [("./control", control.encode("utf-8"), 0o644)]
    for fn in CONTROL_FILES:
        p = src / fn
        if p.is_file():
            mode = 0o755 if fn not in ("conffiles",) else 0o644
            entries.append((f"./{fn}", lf(p.read_bytes()), mode))
    return gz_bytes(tar_bytes(entries))


def build_data(src: Path) -> bytes:
    data_root = src / "data"
    if not data_root.is_dir():
        raise SystemExit(f"{src}: missing data/ directory")
    entries = []
    dirs = set()

    def ensure_parents(rel: str):
        parts = rel.split("/")
        for i in range(1, len(parts)):
            d = "/".join(parts[:i])
            if d and d not in dirs:
                dirs.add(d)
                add_dir(tar, f"./{d}/")

    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w", format=tarfile.USTAR_FORMAT) as tar:
        add_dir(tar, "./")
        for path in sorted(data_root.rglob("*")):
            rel = path.relative_to(data_root).as_posix()
            if path.is_dir():
                ensure_parents(rel)
                add_dir(tar, f"./{rel}/")
                dirs.add(rel)
            elif path.is_file():
                ensure_parents(rel)
                mode = 0o755 if (path.suffix == ".sh" or path.name in ("postinst", "prerm")) else 0o644
                add_file(tar, f"./{rel}", lf(path.read_bytes()), mode)
    return gz_bytes(buf.getvalue())


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: mkipk.py <source-dir> <output.ipk>")
    src = Path(sys.argv[1])
    out = Path(sys.argv[2])
    if not (src / "control").is_file():
        raise SystemExit(f"{src}: missing control")
    out.parent.mkdir(parents=True, exist_ok=True)

    control_tgz = build_control(src)
    data_tgz = build_data(src)
    debian = b"2.0\n"

    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w", format=tarfile.USTAR_FORMAT) as tar:
        add_file(tar, "./debian-binary", debian, 0o644)
        add_file(tar, "./data.tar.gz", data_tgz, 0o644)
        add_file(tar, "./control.tar.gz", control_tgz, 0o644)

    out.write_bytes(gz_bytes(buf.getvalue()))
    print(f"{out} ({out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
