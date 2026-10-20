FROM scratch
COPY ca-certificates.crt /etc/ssl/certs/ca-certificates.crt
COPY gatus /gatus
COPY config.yaml /config/config.yaml
ENV GATUS_CONFIG_PATH=/config/config.yaml \
    PORT=8080
EXPOSE 8080
ENTRYPOINT ["/gatus"]
