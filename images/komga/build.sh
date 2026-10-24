#!/usr/bin/env bash
# Build yunixintel/komga for linux/loong64.
# Everything (Komga jar, sqlite-jdbc source, SQLite amalgamation) is fetched
# and checksum-verified inside the Docker build; no build-context payload.
set -Eeuo pipefail

cd "$(dirname "$0")"

IMAGE="${IMAGE:-yunixintel/komga}"
TAG="${TAG:-loong64}"
RELEASE="${RELEASE:-24.10-la5}"

docker build \
    --network=host \
    --progress=plain \
    -t "${IMAGE}:${TAG}" \
    -t "${IMAGE}:${RELEASE}" \
    .

docker image inspect "${IMAGE}:${TAG}" \
    --format 'image={{.RepoTags}} arch={{.Architecture}} os={{.Os}} size={{.Size}}'
