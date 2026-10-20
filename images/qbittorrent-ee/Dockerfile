FROM openeuler/openeuler:24.03

LABEL org.opencontainers.image.title="qBittorrent-Enhanced-Edition (nox)" \
      org.opencontainers.image.version="5.2.4.10" \
      org.opencontainers.image.source="https://github.com/c0re100/qBittorrent-Enhanced-Edition" \
      org.opencontainers.image.description="Headless qBittorrent-EE, static loongarch64-musl binary"

# ca-certificates + tzdata (present in base; installed conditionally if missing)
RUN rpm -q ca-certificates tzdata >/dev/null 2>&1 || dnf install -y ca-certificates tzdata; \
    dnf clean all 2>/dev/null || true; rm -rf /var/cache/dnf

COPY extract/qbittorrent-nox /usr/bin/qbittorrent-nox
RUN chmod 0755 /usr/bin/qbittorrent-nox \
 && mkdir -p /config /downloads

VOLUME ["/config", "/downloads"]
EXPOSE 8080 6881 6881/udp

ENTRYPOINT ["/usr/bin/qbittorrent-nox", "--profile=/config", "--webui-port=8080"]
