FROM openeuler/openeuler:24.03

LABEL org.opencontainers.image.title="drawio" \
      org.opencontainers.image.version="32.5.5" \
      org.opencontainers.image.source="https://github.com/jgraph/drawio"

RUN dnf install -y nginx \
 && dnf clean all \
 && rm -rf /var/cache/dnf \
 && rm -rf /usr/share/nginx/html/* \
 && ln -sf /dev/stdout /var/log/nginx/access.log \
 && ln -sf /dev/stderr /var/log/nginx/error.log

COPY nginx.conf /etc/nginx/nginx.conf
COPY webroot/ /usr/share/nginx/html/

EXPOSE 8080
STOPSIGNAL SIGQUIT
CMD ["nginx", "-g", "daemon off;"]
