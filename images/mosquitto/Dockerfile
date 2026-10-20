FROM openeuler/openeuler:24.03
RUN dnf install -y --setopt=install_weak_deps=False \
        mosquitto util-linux ca-certificates tzdata && \
    dnf clean all && rm -rf /var/cache/dnf && \
    mkdir -p /mosquitto/config /mosquitto/data /mosquitto/log && \
    chown -R mosquitto:mosquitto /mosquitto/data /mosquitto/log
COPY mosquitto.conf /mosquitto/config/mosquitto.conf
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod 0755 /usr/local/bin/docker-entrypoint.sh
EXPOSE 1883
VOLUME ["/mosquitto/data", "/mosquitto/log"]
HEALTHCHECK --interval=30s --timeout=5s --retries=5 \
    CMD bash -c 'exec 3<>/dev/tcp/127.0.0.1/1883' || exit 1
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
