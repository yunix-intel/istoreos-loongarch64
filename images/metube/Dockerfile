FROM openeuler/openeuler:24.03 AS pybuild
RUN sed -i 's|repo.openeuler.org|mirrors.aliyun.com/openeuler|g; s|^metalink=|#metalink=|' /etc/yum.repos.d/*.repo && \
    dnf install -y --disablerepo=debuginfo --disablerepo=EPOL --disablerepo=source --disablerepo=update-source \
        --setopt=retries=1 --setopt=timeout=15 --setopt=install_weak_deps=False \
        gcc gcc-c++ make tar xz curl ca-certificates findutils \
        zlib-devel bzip2-devel libffi-devel openssl-devel sqlite-devel \
        readline-devel ncurses-devel xz-devel gdbm-devel && \
    dnf clean all && rm -rf /var/cache/dnf

ARG PYTHON_VERSION=3.13.7
RUN curl -fsSLO "https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tgz" && \
    tar xf "Python-${PYTHON_VERSION}.tgz" && \
    cd "Python-${PYTHON_VERSION}" && \
    ./configure --prefix=/usr/local --with-ensurepip=install && \
    make -j"$(nproc)" && make install && \
    cd / && rm -rf "Python-${PYTHON_VERSION}" "Python-${PYTHON_VERSION}.tgz" && \
    rm -rf /usr/local/lib/python3.13/test \
           /usr/local/lib/python3.13/idlelib \
           /usr/local/lib/python3.13/turtledemo \
           /usr/local/lib/python3.13/ensurepip/_bundled \
           /usr/local/lib/libpython3.13.a && \
    find /usr/local -name '__pycache__' -prune -exec rm -rf {} +

ENV PATH=/usr/local/bin:$PATH
RUN python3 -m pip install --no-cache-dir --upgrade pip && \
    python3 -m pip install --no-cache-dir \
        aiohttp \
        "python-socketio>=5.0,<6.0" \
        yt-dlp \
        certifi \
        mutagen \
        pycryptodomex \
        requests \
        urllib3 \
        websockets \
        yt-dlp-ejs && \
    rm -rf /usr/local/include/python3.13 /usr/local/lib/python3.13/config-3.13-* && \
    find /usr/local -name '__pycache__' -prune -exec rm -rf {} +


FROM openeuler/openeuler:24.03
RUN sed -i 's|repo.openeuler.org|mirrors.aliyun.com/openeuler|g; s|^metalink=|#metalink=|' /etc/yum.repos.d/*.repo && \
    dnf install -y --disablerepo=debuginfo --disablerepo=EPOL --disablerepo=source --disablerepo=update-source \
        --setopt=retries=1 --setopt=timeout=15 --setopt=install_weak_deps=False \
        ca-certificates tzdata curl xz unzip ffmpeg \
        bash shadow util-linux procps-ng patch \
        libstdc++ openssl-libs libffi zlib bzip2-libs xz-libs sqlite-libs readline ncurses-libs gdbm && \
    dnf clean all && rm -rf /var/cache/dnf && \
    groupadd -g 1111 metube && \
    useradd -u 1111 -g 1111 -M -d /app -s /sbin/nologin metube

COPY --from=pybuild /usr/local /usr/local
COPY --from=yunixintel/node:24.22.1 /opt/node24 /opt/node24
COPY gosu /usr/local/bin/gosu

WORKDIR /app
COPY app ./app
COPY docker-entrypoint.sh ./
COPY patches ./patches
RUN patch -p1 < patches/metube-watchfiles.patch && \
    patch -p1 < patches/metube-entrypoint.patch && \
    rm -rf patches
COPY ui/dist/metube/browser ./ui/dist/metube/browser
RUN chmod 0755 docker-entrypoint.sh /usr/local/bin/gosu && \
    chown -R metube:metube /app && \
    mkdir -p /downloads && chown metube:metube /downloads

ENV PATH=/usr/local/bin:/opt/node24/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=Asia/Shanghai \
    PUID=1111 \
    PGID=1111 \
    UMASK=022 \
    DOWNLOAD_DIR=/downloads \
    STATE_DIR=/downloads/.metube \
    TEMP_DIR=/downloads \
    PORT=8082

VOLUME ["/downloads"]
EXPOSE 8082
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8082/ || exit 1
ENTRYPOINT ["/app/docker-entrypoint.sh"]
