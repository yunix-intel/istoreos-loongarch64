FROM openeuler/openeuler:24.03
RUN dnf install -y --disablerepo=debuginfo --disablerepo=EPOL --disablerepo=source --disablerepo=update-source \
        --setopt=retries=1 --setopt=timeout=15 --setopt=install_weak_deps=False \
        ca-certificates tzdata curl bash gettext nginx && \
    dnf clean all && rm -rf /var/cache/dnf && \
    mkdir -p /var/www/app /var/lib/nginx /var/log/nginx /opt/data/assets && \
    chown -R nginx:nginx /var/lib/nginx /var/log/nginx
COPY app/ /var/www/app/
COPY nginx.conf.template /etc/nginx/nginx.conf.template
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod 0755 /usr/local/bin/docker-entrypoint.sh
ENV PENPOT_PUBLIC_URI=http://localhost:9001 \
    PENPOT_FLAGS="disable-email-verification disable-secure-session-cookies" \
    PENPOT_BACKEND_URI=http://penpot-backend:6060 \
    PENPOT_EXPORTER_URI=http://penpot-exporter:6061 \
    PENPOT_HTTP_SERVER_MAX_BODY_SIZE=367001600
EXPOSE 8080
VOLUME ["/opt/data/assets"]
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=5 \
    CMD curl -fsS http://127.0.0.1:8080/ >/dev/null || exit 1
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
