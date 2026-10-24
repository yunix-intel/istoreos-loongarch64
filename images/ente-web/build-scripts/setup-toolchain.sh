#!/usr/bin/env bash
# Idempotent toolchain setup for the Ente web build (WSL x86_64).
set -euo pipefail
export PATH="$HOME/.cargo/bin:$HOME/node24/bin:$PATH"

# 1. Rust: use USTC mirror; static.rust-lang.org is unusable here.
export RUSTUP_DIST_SERVER=https://mirrors.ustc.edu.cn/rust-static
export RUSTUP_UPDATE_ROOT=https://mirrors.ustc.edu.cn/rust-static/rustup
rustup toolchain install stable --profile minimal \
    --target wasm32-unknown-unknown,loongarch64-unknown-linux-gnu,loongarch64-unknown-linux-musl
# rust/bindings/wasm/cast/rust-toolchain.toml pins this nightly; without it
# wasm-pack waits forever on static.rust-lang.org.
rustup toolchain install nightly-2026-08-13 --profile minimal \
    --component rust-src --target wasm32-unknown-unknown

# 2. crates.io mirror (source replacement, appended once).
if ! grep -q "source.ustc" "$HOME/.cargo/config.toml" 2>/dev/null; then
    cat >> "$HOME/.cargo/config.toml" <<'CFG'

[source.crates-io]
replace-with = "ustc"

[source.ustc]
registry = "sparse+https://mirrors.ustc.edu.cn/crates.io-index/"
CFG
fi

# 3. wasm-opt: wasm-pack downloads from GitHub and stalls. Use Ubuntu binaryen.
if [ ! -x "$HOME/tools/binaryen-120/usr/bin/wasm-opt" ]; then
    mkdir -p "$HOME/tools/deb" "$HOME/tools/binaryen-120"
    curl -fsSL -o "$HOME/tools/deb/binaryen.deb" \
      https://mirrors.ustc.edu.cn/ubuntu/pool/universe/b/binaryen/binaryen_120-4build1_amd64.deb
    dpkg-deb -x "$HOME/tools/deb/binaryen.deb" "$HOME/tools/binaryen-120"
fi
echo "toolchain ready: $(rustc --version)"
