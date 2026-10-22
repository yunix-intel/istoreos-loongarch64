FROM openeuler/openeuler:24.03
RUN dnf install -y --disablerepo=debuginfo --disablerepo=EPOL --disablerepo=source --disablerepo=update-source \
        --setopt=retries=1 --setopt=timeout=15 --setopt=install_weak_deps=False \
        ca-certificates tzdata ffmpeg bash shadow util-linux curl && \
    dnf clean all && rm -rf /var/cache/dnf && \
    useradd -u 1026 -M -d /config -s /bin/bash csf && \
    mkdir -p /config /media && chown -R csf:csf /config /media
COPY chinesesubfinder /usr/bin/chinesesubfinder
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod 0755 /usr/bin/chinesesubfinder /usr/local/bin/docker-entrypoint.sh
ENV TZ=Asia/Shanghai LITE_MODE=true
WORKDIR /config
EXPOSE 19035
VOLUME ["/config", "/media"]
HEALTHCHECK --interval=30s --timeout=5s --retries=10 \
    CMD curl -fsS http://127.0.0.1:19035/ >/dev/null || exit 1
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
