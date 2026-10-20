# xTeVe 2.2.0.200 on loong64
# Static (CGO_ENABLED=0) Go build done on host with Go 1.24.4 + loong64.
FROM openeuler/openeuler:24.03

# ca-certificates for HTTPS (EPG/update checks); ffmpeg for optional stream buffering.
RUN dnf install -y ca-certificates tzdata ffmpeg \
    && dnf clean all && rm -rf /var/cache/dnf

COPY xteve /usr/local/bin/xteve
RUN chmod 0755 /usr/local/bin/xteve && mkdir -p /config

ENV TZ=UTC

EXPOSE 34400
VOLUME ["/config"]

ENTRYPOINT ["/usr/local/bin/xteve", "-config", "/config", "-port", "34400"]
