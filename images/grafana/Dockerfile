FROM openeuler/openeuler:24.03 AS assets
RUN dnf install -y --setopt=install_weak_deps=False findutils && dnf clean all
COPY public /public
RUN find /public -name '*.map' -delete

FROM openeuler/openeuler:24.03
RUN dnf install -y --setopt=install_weak_deps=False \
        ca-certificates tzdata curl shadow util-linux && \
    dnf clean all && rm -rf /var/cache/dnf && \
    groupadd -g 472 grafana && \
    useradd -u 472 -g 472 -M -d /usr/share/grafana -s /sbin/nologin grafana && \
    mkdir -p /usr/share/grafana/bin /usr/share/grafana/public /usr/share/grafana/conf \
             /usr/share/grafana/data/plugins-bundled \
             /etc/grafana/provisioning/datasources /etc/grafana/provisioning/dashboards \
             /etc/grafana/provisioning/notifiers /etc/grafana/provisioning/plugins \
             /etc/grafana/provisioning/alerting \
             /var/lib/grafana/plugins /var/log/grafana && \
    chown -R grafana:grafana /usr/share/grafana /etc/grafana /var/lib/grafana /var/log/grafana
COPY grafana /usr/share/grafana/bin/grafana
COPY --from=assets /public /usr/share/grafana/public
COPY defaults.ini /usr/share/grafana/conf/defaults.ini
COPY grafana.ini /etc/grafana/grafana.ini
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod 0755 /usr/local/bin/docker-entrypoint.sh /usr/share/grafana/bin/grafana
ENV GF_PATHS_HOME=/usr/share/grafana \
    GF_PATHS_CONFIG=/etc/grafana/grafana.ini \
    GF_PATHS_DATA=/var/lib/grafana \
    GF_PATHS_LOGS=/var/log/grafana \
    GF_PATHS_PLUGINS=/var/lib/grafana/plugins \
    GF_PATHS_PROVISIONING=/etc/grafana/provisioning
EXPOSE 3000
VOLUME ["/var/lib/grafana"]
HEALTHCHECK --interval=30s --timeout=5s --retries=5 \
    CMD curl -fsS http://127.0.0.1:3000/api/health >/dev/null || exit 1
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["server", "--homepath=/usr/share/grafana", "--config=/etc/grafana/grafana.ini"]
