#!/bin/bash
# Build the private-only single-container Linkwarden (LBrowser baked in).
#
# Output must stay in the local/ namespace: the LBrowser payload is not
# redistributable, so this script refuses any other repository prefix.
set -euo pipefail
cd "$(dirname "$0")"

IMAGE="${IMAGE:-local/linkwarden-private}"
TAG="${TAG:-2.16.3-p1}"
BASE="${BASE:-yunixintel/linkwarden:2.16.3}"
LBROWSER_IMAGE="${LBROWSER_IMAGE:-local/lbrowser-embedded:3.4.2293.2-local}"

case "$IMAGE" in
    local/*) ;;
    *) echo "refusing to build '$IMAGE': private image must be local/*" >&2; exit 1 ;;
esac

for ref in "$BASE" "$LBROWSER_IMAGE"; do
    if ! docker image inspect "$ref" >/dev/null 2>&1; then
        echo "missing local image: $ref" >&2
        exit 1
    fi
done

# The base image must carry the email templates; a missing copy only shows up
# at runtime as ENOENT /data/apps/web/templates/verifyEmail.html.
if ! docker run --rm --entrypoint test "$BASE" -f /data/apps/web/templates/verifyEmail.html; then
    echo "$BASE is missing /data/apps/web/templates/verifyEmail.html; rebuild the public image" >&2
    exit 1
fi

DOCKER_BUILDKIT="${DOCKER_BUILDKIT:-0}" \
docker build --network=host \
    -f Dockerfile.private \
    --build-arg "LBROWSER_IMAGE=${LBROWSER_IMAGE}" \
    -t "${IMAGE}:${TAG}" \
    .

echo
docker images "${IMAGE}" --format '{{.Repository}}:{{.Tag}} {{.ID}} {{.Size}}'
