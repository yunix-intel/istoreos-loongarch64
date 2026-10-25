#!/bin/bash
# Build yunixintel/karakeep from prebuilt x86_64 artifacts.
#
# The Docker build context must contain:
#   Dockerfile entrypoint.sh artifacts/{web,workers,db_migrations}
# artifacts/ is generated on an x86_64 host (see BUILD.md) and is intentionally
# not committed to this repository.
set -euo pipefail
cd "$(dirname "$0")"

IMAGE="${IMAGE:-yunixintel/karakeep}"
TAG="${TAG:-loong64}"
VERSION_TAG="${VERSION_TAG:-0.34.1}"

if [ ! -d artifacts/web ] || [ ! -d artifacts/workers ] || [ ! -d artifacts/db_migrations ]; then
    echo "artifacts/{web,workers,db_migrations} missing; see BUILD.md" >&2
    exit 1
fi

DOCKER_BUILDKIT="${DOCKER_BUILDKIT:-0}" \
docker build --network=host \
    -t "${IMAGE}:${TAG}" \
    -t "${IMAGE}:${VERSION_TAG}" \
    .

echo
docker images "${IMAGE}" --format '{{.Repository}}:{{.Tag}} {{.ID}} {{.Size}}'
