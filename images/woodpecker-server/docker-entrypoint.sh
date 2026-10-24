#!/bin/sh
set -e

DATA_DIR=/var/lib/woodpecker
SECRET_FILE="$DATA_DIR/agent-secret"

mkdir -p "$DATA_DIR"
chown -R woodpecker:woodpecker "$DATA_DIR"

if [ "$#" -eq 0 ]; then
    set -- woodpecker-server
fi

if [ -z "$WOODPECKER_AGENT_SECRET" ] && [ -z "$WOODPECKER_AGENT_SECRET_FILE" ]; then
    if [ ! -s "$SECRET_FILE" ]; then
        head -c 32 /dev/urandom | od -An -tx1 | tr -d ' \n' > "$SECRET_FILE"
        chmod 0600 "$SECRET_FILE"
        chown woodpecker:woodpecker "$SECRET_FILE"
        echo "woodpecker: generated agent secret at $SECRET_FILE (mount this volume or set WOODPECKER_AGENT_SECRET)"
    fi
    WOODPECKER_AGENT_SECRET=$(cat "$SECRET_FILE")
    export WOODPECKER_AGENT_SECRET
fi

if [ -z "$WOODPECKER_GRPC_SECRET" ]; then
    GRPC_FILE="$DATA_DIR/grpc-secret"
    if [ ! -s "$GRPC_FILE" ]; then
        head -c 32 /dev/urandom | od -An -tx1 | tr -d ' \n' > "$GRPC_FILE"
        chmod 0600 "$GRPC_FILE"
        chown woodpecker:woodpecker "$GRPC_FILE"
    fi
    WOODPECKER_GRPC_SECRET=$(cat "$GRPC_FILE")
    export WOODPECKER_GRPC_SECRET
fi

if [ "$(id -u)" = "0" ]; then
    exec runuser -u woodpecker -- "$@"
fi
exec "$@"
