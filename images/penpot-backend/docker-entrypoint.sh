#!/usr/bin/env bash
set -Eeuo pipefail

cd /opt/penpot/backend

if [ -z "${PENPOT_SECRET_KEY:-}" ]; then
    echo "PENPOT_SECRET_KEY is required (generate with: python3 -c 'import secrets; print(secrets.token_urlsafe(64))')" >&2
    exit 1
fi

exec java \
    -Djava.util.logging.manager=org.apache.logging.log4j.jul.LogManager \
    -Dlog4j2.configurationFile=log4j2.xml \
    -XX:-OmitStackTraceInFastThrow \
    -XX:+ExitOnOutOfMemoryError \
    ${JVM_OPTS:-} \
    -jar penpot.jar -m app.main
