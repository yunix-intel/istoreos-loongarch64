FROM openeuler/openeuler:24.03
ARG HOMER_VERSION=v26.08.3

RUN dnf install -y --setopt=install_weak_deps=False \
        nginx unzip curl ca-certificates && \
    dnf clean all && rm -rf /var/cache/dnf

RUN curl -fsSL -o /tmp/homer.zip \
        "https://github.com/bastienwirtz/homer/releases/download/${HOMER_VERSION}/homer.zip" && \
    mkdir -p /usr/share/nginx/html && \
    unzip -qo /tmp/homer.zip -d /usr/share/nginx/html && \
    rm -f /tmp/homer.zip

COPY nginx.conf /etc/nginx/nginx.conf
COPY config.yml /usr/share/nginx/html/assets/config.yml

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8080/ || exit 1
CMD ["nginx", "-g", "daemon off;"]
