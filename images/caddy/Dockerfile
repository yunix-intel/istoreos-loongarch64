FROM scratch
ENV XDG_DATA_HOME=/data \
    XDG_CONFIG_HOME=/config
COPY ca-certificates.crt /etc/ssl/certs/ca-certificates.crt
COPY caddy /usr/bin/caddy
COPY Caddyfile /etc/caddy/Caddyfile
EXPOSE 80 443 8080
CMD ["/usr/bin/caddy", "run", "--config", "/etc/caddy/Caddyfile", "--adapter", "caddyfile"]
