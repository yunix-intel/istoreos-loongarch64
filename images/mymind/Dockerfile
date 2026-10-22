FROM openeuler/openeuler:24.03
RUN dnf install -y --disablerepo=debuginfo --disablerepo=EPOL --disablerepo=source --disablerepo=update-source \
        --setopt=retries=1 --setopt=timeout=15 --setopt=install_weak_deps=False \
        nginx ca-certificates tzdata curl && \
    dnf clean all && rm -rf /var/cache/dnf && \
    mkdir -p /var/lib/nginx/tmp/{client_body,proxy,fastcgi,uwsgi,scgi} /var/log/nginx && \
    chown -R nginx:nginx /var/lib/nginx /var/log/nginx
COPY site/ /usr/share/nginx/html/
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=5s --retries=5 \
    CMD curl -fsS http://127.0.0.1/ >/dev/null || exit 1
CMD ["nginx", "-g", "daemon off;"]
