#!/usr/bin/env bash
set -Eeuo pipefail

CONFIG_DIR="${KOMGA_CONFIGDIR:-/config}"

# Volumes are created by Docker as root; prepare them before dropping privileges.
mkdir -p "$CONFIG_DIR" /data
if [ "$(stat -c %u "$CONFIG_DIR")" != "1110" ]; then
    chown -R 1110:1110 "$CONFIG_DIR"
fi
# /data may be mounted read-only; ownership there is optional.
chown 1110:1110 /data 2>/dev/null || true

# Always use the loongarch64 JNI built into the image, even if the caller
# overrides JAVA_OPTS for memory tuning.
case " ${JAVA_OPTS:-} " in
    *" -Dorg.sqlite.lib.path="*) ;;
    *)
        JAVA_OPTS="${JAVA_OPTS:-} -Dorg.sqlite.lib.path=/opt/komga/native -Dorg.sqlite.lib.name=libsqlitejdbc.so"
        ;;
esac

exec runuser -u komga -- java \
    ${JAVA_OPTS:--Xms256m -Xmx1g} \
    -Dspring.profiles.include=docker \
    -jar /opt/komga/komga.jar \
    --spring.config.additional-location="file:${CONFIG_DIR}/"
