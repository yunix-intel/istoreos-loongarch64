FROM openeuler/openeuler:24.03

LABEL org.opencontainers.image.title="Portainer CE" \
      org.opencontainers.image.description="Portainer Community Edition server (loong64)" \
      org.opencontainers.image.version="2.45.2" \
      org.opencontainers.image.vendor="Portainer.io" \
      io.portainer.server="true"

RUN dnf install -y ca-certificates tzdata \
 && dnf clean all \
 && rm -rf /var/cache/dnf /var/cache/yum

COPY src/dist/portainer /portainer
COPY src/dist/public /public
COPY src/dist/mustache-templates /mustache-templates

VOLUME /data
WORKDIR /

EXPOSE 9000
EXPOSE 9443
EXPOSE 8000

ENTRYPOINT ["/portainer"]
