#!/usr/bin/env bash
# Build all 10 Ente web apps as static exports with the runtime endpoint placeholder.
set -euo pipefail
export PATH="$HOME/.cargo/bin:$HOME/node24/bin:$HOME/tools/binaryen-120/usr/bin:$PATH"
export LD_LIBRARY_PATH="$HOME/tools/binaryen-120/usr/lib/x86_64-linux-gnu:${LD_LIBRARY_PATH:-}"
export NEXT_PUBLIC_ENTE_ENDPOINT=ENTE_API_ORIGIN_PLACEHOLDER
export NEXT_TELEMETRY_DISABLED=1
export RUSTUP_DIST_SERVER=https://mirrors.ustc.edu.cn/rust-static

cd "$HOME/ente-build/web"
npm ci --registry=https://registry.npmmirror.com --no-audit --no-fund

for app in photos albums accounts auth cast share embed paste locker memories; do
    echo "=== build:$app ==="
    npm run "build:$app"
done

echo "=== outputs ==="
for app in photos albums accounts auth cast share embed paste locker memories; do
    du -sh "apps/$app/out"
done
