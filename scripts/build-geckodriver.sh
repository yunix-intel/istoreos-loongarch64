#!/bin/bash
# Build geckodriver v0.37.1 for loong64 inside openEuler 24.03 (glibc 2.38).
# Usage: ./scripts/build-geckodriver.sh [source-dir] [output-file]
# Must build inside the target base image: a host-built binary on Loongnix
# (glibc 2.41) requires GLIBC_2.39 and will not start in the openEuler image.
set -euo pipefail

SRC="${1:-/tmp/geckodriver-src}"
OUT="${2:-$(pwd)/geckodriver}"

if [ ! -d "$SRC/.git" ]; then
  rm -rf "$SRC"
  git clone --depth 1 --branch v0.37.1 https://github.com/mozilla/geckodriver "$SRC"
fi

docker run --rm -v "$SRC":/src -w /src openeuler/openeuler:24.03 bash -c '
set -eux
dnf install -y --setopt=install_weak_deps=False gcc make curl ca-certificates tar gzip >/dev/null
export RUSTUP_HOME=/tmp/rustup CARGO_HOME=/tmp/cargo
curl -fsSL https://static.rust-lang.org/rustup/dist/loongarch64-unknown-linux-gnu/rustup-init -o /tmp/rustup-init
chmod +x /tmp/rustup-init
/tmp/rustup-init -y --profile minimal --default-toolchain stable >/tmp/rustup.log 2>&1
/tmp/cargo/bin/cargo build --release --locked 2>&1 | tail -5
'

install -m 0755 "$SRC/target/release/geckodriver" "$OUT"
"$OUT" --version
