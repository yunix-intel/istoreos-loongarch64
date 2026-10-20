FROM openeuler/openeuler:24.03
RUN dnf install -y --setopt=install_weak_deps=False ca-certificates tzdata curl && \
    dnf clean all && rm -rf /var/cache/dnf && \
    mkdir -p /etc/alertmanager /alertmanager && \
    chown 65534:65534 /alertmanager
COPY alertmanager /bin/alertmanager
COPY amtool /bin/amtool
COPY alertmanager.yml /etc/alertmanager/alertmanager.yml
EXPOSE 9093 9094
VOLUME ["/alertmanager"]
USER 65534:65534
HEALTHCHECK --interval=30s --timeout=5s --retries=5 \
    CMD curl -fsS http://127.0.0.1:9093/-/healthy || exit 1
ENTRYPOINT ["/bin/alertmanager"]
CMD ["--config.file=/etc/alertmanager/alertmanager.yml", "--storage.path=/alertmanager"]
