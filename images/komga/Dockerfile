# Komga 1.29.1 for linux/loong64.
# The application jar is pure JVM bytecode; only xerial sqlite-jdbc needs a
# native loongarch64 build, produced in the sqlite-native stage below.

FROM openeuler/openeuler:24.03 AS sqlite-native

ARG SQLITE_JDBC_VERSION=3.53.4.0
ARG SQLITE_AMALGAMATION=3530400
ARG SQLITE_JDBC_SHA256=9dded7305b4f3bab596d6a40eaab0cf0d3afad60006eb80073492103b06b081c
ARG SQLITE_AMALGAMATION_SHA256=1e71ddf93849c6a6ecf58b827c0692073d2dd7ee40196158068f7b29f422e87d

RUN dnf install -y --disablerepo=debuginfo --disablerepo=EPOL --disablerepo=source \
        --disablerepo=update-source --setopt=retries=1 --setopt=timeout=20 \
        --setopt=install_weak_deps=False \
        gcc make perl zip unzip curl ca-certificates java-21-openjdk-devel && \
    dnf clean all && rm -rf /var/cache/dnf

WORKDIR /src
RUN curl -fsSL -o sqlite-jdbc.tar.gz \
        "https://github.com/xerial/sqlite-jdbc/archive/refs/tags/${SQLITE_JDBC_VERSION}.tar.gz" && \
    echo "${SQLITE_JDBC_SHA256}  sqlite-jdbc.tar.gz" | sha256sum -c - && \
    tar xzf sqlite-jdbc.tar.gz
RUN curl -fsSL -o "sqlite-amalgamation-${SQLITE_AMALGAMATION}.zip" \
        "https://www.sqlite.org/2026/sqlite-amalgamation-${SQLITE_AMALGAMATION}.zip" && \
    echo "${SQLITE_AMALGAMATION_SHA256}  sqlite-amalgamation-${SQLITE_AMALGAMATION}.zip" | sha256sum -c -

# Upstream Makefile patches sqlite3.c (extension functions, compile options)
# and builds NativeDB.c + sqlite3.c with the same flags as released artifacts.
# Linux-loongarch64 is not in known_targets, so the Makefile falls back to the
# Default flags; OS_NAME must be explicit or the output path loses the OS name.
RUN mkdir -p "sqlite-jdbc-${SQLITE_JDBC_VERSION}/target" && \
    cp "sqlite-amalgamation-${SQLITE_AMALGAMATION}.zip" "sqlite-jdbc-${SQLITE_JDBC_VERSION}/target/" && \
    cd "sqlite-jdbc-${SQLITE_JDBC_VERSION}" && \
    JAVA_HOME=/usr/lib/jvm/java-21-openjdk \
        make OS_NAME=Linux OS_ARCH=loongarch64 native


FROM openeuler/openeuler:24.03

ARG KOMGA_VERSION=1.29.1
ARG KOMGA_SHA256=e9cafae1ec6d0d117c2375fff9ecb737ed384eede2afea9716bcb555d96ea834

RUN dnf install -y --disablerepo=debuginfo --disablerepo=EPOL --disablerepo=source \
        --disablerepo=update-source --setopt=retries=1 --setopt=timeout=20 \
        --setopt=install_weak_deps=False \
        java-21-openjdk-headless curl tzdata util-linux ca-certificates && \
    dnf clean all && rm -rf /var/cache/dnf && \
    groupadd -g 1110 komga && \
    useradd -u 1110 -g 1110 -M -d /config -s /bin/false komga && \
    mkdir -p /opt/komga/native /config /data && \
    chown 1110:1110 /config /data

COPY --from=sqlite-native \
    /src/sqlite-jdbc-3.53.4.0/src/main/resources/org/sqlite/native/Linux/loongarch64/libsqlitejdbc.so \
    /opt/komga/native/libsqlitejdbc.so

RUN curl -fsSL -o /opt/komga/komga.jar \
        "https://github.com/gotson/komga/releases/download/${KOMGA_VERSION}/komga-${KOMGA_VERSION}.jar" && \
    echo "${KOMGA_SHA256}  /opt/komga/komga.jar" | sha256sum -c - && \
    chown -R 1110:1110 /opt/komga

COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod 0755 /usr/local/bin/docker-entrypoint.sh

ENV KOMGA_CONFIGDIR=/config \
    JAVA_OPTS="-Xms256m -Xmx1g -Dorg.sqlite.lib.path=/opt/komga/native -Dorg.sqlite.lib.name=libsqlitejdbc.so"

WORKDIR /opt/komga
EXPOSE 25600
VOLUME ["/config", "/data"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=120s --retries=3 \
    CMD curl -fsS http://127.0.0.1:25600/actuator/health | grep -q '"status":"UP"'

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
