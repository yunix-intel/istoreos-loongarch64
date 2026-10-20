FROM openeuler/openeuler:24.03
RUN dnf install -y --setopt=install_weak_deps=False ca-certificates tzdata curl && \
    dnf clean all && rm -rf /var/cache/dnf
COPY prometheus /bin/prometheus
COPY promtool /bin/promtool
COPY prometheus.yml /etc/prometheus/prometheus.yml
EXPOSE 9090
VOLUME ["/prometheus"]
HEALTHCHECK --interval=30s --timeout=5s --retries=5 \
    CMD curl -fsS http://127.0.0.1:9090/-/healthy || exit 1
ENTRYPOINT ["/bin/prometheus"]
CMD ["--config.file=/etc/prometheus/prometheus.yml", "--storage.tsdb.path=/prometheus"]
