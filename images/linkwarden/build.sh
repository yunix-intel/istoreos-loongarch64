#!/bin/bash
# Build yunixintel/linkwarden from prebuilt x86_64 artifacts.
#
# The build context must contain:
#   Dockerfile entrypoint.sh prisma-migrate.mjs artifacts/
# artifacts/ is generated on an x86_64 host (see BUILD.md) and is intentionally
# not committed to this repository.
set -euo pipefail
cd "$(dirname "$0")"

IMAGE="${IMAGE:-yunixintel/linkwarden}"
TAG="${TAG:-loong64}"
VERSION_TAG="${VERSION_TAG:-24.10-la5}"
UPSTREAM_TAG="${UPSTREAM_TAG:-2.16.3}"

if [ ! -d artifacts/node_modules ] || [ ! -d artifacts/apps/web/.next ] || \
   [ ! -d artifacts/apps/worker ]; then
    echo "artifacts/ incomplete; see BUILD.md" >&2
    exit 1
fi
if [ ! -x artifacts/node_modules/@esbuild/linux-loong64/bin/esbuild ]; then
    echo "artifacts/ is missing the loong64 esbuild binary; see BUILD.md" >&2
    exit 1
fi

DOCKER_BUILDKIT="${DOCKER_BUILDKIT:-0}" \
docker build --network=host \
    -t "${IMAGE}:${TAG}" \
    -t "${IMAGE}:${VERSION_TAG}" \
    -t "${IMAGE}:${UPSTREAM_TAG}" \
    .

echo
docker images "${IMAGE}" --format '{{.Repository}}:{{.Tag}} {{.ID}} {{.Size}}'
