FROM openeuler/openeuler:24.03

LABEL org.opencontainers.image.title="it-tools" \
      org.opencontainers.image.version="2024.10.22-7ca5933" \
      org.opencontainers.image.source="https://github.com/CorentinTh/it-tools"

RUN dnf install -y nginx \
    && dnf clean all \
    && rm -rf /var/cache/dnf

COPY nginx.conf /etc/nginx/nginx.conf
COPY dist /usr/share/nginx/html

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
