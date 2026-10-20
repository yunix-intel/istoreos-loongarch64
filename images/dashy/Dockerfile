FROM openeuler/openeuler:24.03
RUN dnf install -y --setopt=install_weak_deps=False \
        nginx curl ca-certificates && \
    dnf clean all && rm -rf /var/cache/dnf
COPY dist/ /usr/share/nginx/html/
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8080/ || exit 1
CMD ["nginx", "-g", "daemon off;"]
