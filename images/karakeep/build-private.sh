#!/bin/bash
# Build the PRIVATE single-container Karakeep image (Karakeep + LBrowser).
#
# LOCAL ONLY.  The resulting image embeds LBrowser, whose license does not
# clearly permit redistribution.  Do not tag it under yunixintel/* and never
# push it to any registry.
#
# Prerequisites on the build host:
#   yunixintel/karakeep:0.34.1
#   local/lbrowser-embedded:3.4.2293.2-local
set -euo pipefail
cd "$(dirname "$0")"

IMAGE="${IMAGE:-local/karakeep-private}"
TAG="${TAG:-0.34.1-p1}"

case "$IMAGE" in
    local/*) ;;
    *) echo "refusing to build '$IMAGE': private image must be local/*" >&2; exit 1 ;;
esac

if ! docker image inspect yunixintel/karakeep:0.34.1 >/dev/null 2>&1; then
    echo "missing base image yunixintel/karakeep:0.34.1" >&2
    exit 1
fi
if ! docker image inspect local/lbrowser-embedded:3.4.2293.2-local >/dev/null 2>&1; then
    echo "missing browser image local/lbrowser-embedded:3.4.2293.2-local" >&2
    exit 1
fi

DOCKER_BUILDKIT="${DOCKER_BUILDKIT:-0}" \
docker build --network=host \
    -f Dockerfile.private \
    -t "${IMAGE}:${TAG}" \
    .

echo
docker images "${IMAGE}:${TAG}" --format '{{.Repository}}:{{.Tag}} {{.ID}} {{.Size}}'
