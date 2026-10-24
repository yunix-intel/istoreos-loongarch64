FROM openeuler/openeuler:24.03 AS build
RUN sed -i 's|repo.openeuler.org|mirrors.aliyun.com/openeuler|g; s|^metalink=|#metalink=|' /etc/yum.repos.d/*.repo && \
    dnf install -y --disablerepo=debuginfo --disablerepo=EPOL --disablerepo=source --disablerepo=update-source \
        --setopt=retries=1 --setopt=timeout=15 --setopt=install_weak_deps=False \
        python3 python3-devel python3-pip python3-setuptools python3-wheel \
        python3-cryptography python3-dbus \
        gcc gcc-c++ make cmake tar xz unzip curl findutils \
        openssl-devel libffi-devel zlib-devel && \
    dnf clean all && rm -rf /var/cache/dnf

WORKDIR /src
COPY requirements.txt ./
RUN grep -vE '^(orjson|cryptography)' requirements.txt > /tmp/req.txt && \
    python3 -m venv --system-site-packages /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir -r /tmp/req.txt

RUN curl -fsSL -o par2.tar.gz \
        https://github.com/Parchive/par2cmdline/releases/download/v0.8.1/par2cmdline-0.8.1.tar.gz && \
    tar xzf par2.tar.gz && cd par2cmdline-0.8.1 && \
    ./configure --build=loongarch64-unknown-linux-gnu --prefix=/usr/local && make -j"$(nproc)" && make install

RUN curl -fsSL -o unrar.tar.gz https://www.rarlab.com/rar/unrarsrc-7.1.10.tar.gz && \
    tar xzf unrar.tar.gz && cd unrar && \
    make -j"$(nproc)" && install -m 0755 unrar /usr/local/bin/unrar


FROM openeuler/openeuler:24.03
RUN sed -i 's|repo.openeuler.org|mirrors.aliyun.com/openeuler|g; s|^metalink=|#metalink=|' /etc/yum.repos.d/*.repo && \
    dnf install -y --disablerepo=debuginfo --disablerepo=EPOL --disablerepo=source --disablerepo=update-source \
        --setopt=retries=1 --setopt=timeout=15 --setopt=install_weak_deps=False \
        python3 python3-cryptography python3-dbus \
        ca-certificates tzdata curl xz unzip p7zip \
        bash shadow util-linux procps-ng && \
    dnf clean all && rm -rf /var/cache/dnf && \
    groupadd -g 1112 sabnzbd && \
    useradd -u 1112 -g 1112 -M -d /config -s /sbin/nologin sabnzbd && \
    mkdir -p /config /downloads && chown sabnzbd:sabnzbd /config /downloads

COPY --from=build /opt/venv /opt/venv
COPY --from=build /usr/local/bin/par2 /usr/local/bin/par2
COPY --from=build /usr/local/bin/unrar /usr/local/bin/unrar
COPY app /app
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod 0755 /usr/local/bin/docker-entrypoint.sh && \
    chown -R sabnzbd:sabnzbd /app

ENV PATH=/opt/venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=Asia/Shanghai \
    SABNZBD_CONFIG=/config \
    HOME=/config

WORKDIR /app
VOLUME ["/config", "/downloads"]
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=5 \
    CMD curl -fsSL http://127.0.0.1:8080/ >/dev/null || exit 1
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
