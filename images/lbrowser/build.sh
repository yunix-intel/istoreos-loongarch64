#!/usr/bin/env bash
# Build the LoongArch64 LBrowser/Playwright runtime image.
#
#   ./build.sh            runtime image, no LBrowser payload (mount at run time)
#   ./build.sh embedded   local-only image with the deb unpacked inside
set -euo pipefail
cd "$(dirname "$0")"

mode="${1:-mount}"
case "${mode}" in
    mount)
        DOCKER_BUILDKIT=0 docker build --network=host \
            -t local/lbrowser-runtime:3.4.2293.2 \
            -t local/lbrowser-runtime:loong64 .
        ;;
    embedded)
        DOCKER_BUILDKIT=0 docker build --network=host \
            --build-arg INSTALL_LBROWSER=1 \
            -t local/lbrowser-embedded:3.4.2293.2-local .
        ;;
    *)
        echo "usage: $0 [mount|embedded]" >&2
        exit 2
        ;;
esac
