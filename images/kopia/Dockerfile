FROM openeuler/openeuler:24.03

ENV KOPIA_CONFIG_PATH=/app/config/repository.config \
    KOPIA_LOG_DIR=/app/logs \
    KOPIA_CACHE_DIRECTORY=/app/cache \
    KOPIA_PERSIST_CREDENTIALS_ON_CONNECT=false \
    KOPIA_CHECK_FOR_UPDATES=false

RUN dnf install -y ca-certificates tzdata \
 && dnf clean all \
 && mkdir -p /app/config /app/cache /app/logs /app/repository

WORKDIR /app
COPY kopia /usr/bin/kopia
RUN chmod 0755 /usr/bin/kopia

EXPOSE 51515
ENTRYPOINT ["/usr/bin/kopia"]
CMD ["server","start","--insecure","--address=0.0.0.0:51515","--server-username=admin","--server-password=kopia"]
