FROM openeuler/openeuler:24.03

LABEL org.opencontainers.image.title="one-api" \
      org.opencontainers.image.version="v0.6.10" \
      org.opencontainers.image.description="OpenAI-compatible API gateway and management panel" \
      org.opencontainers.image.architecture="loong64"

ENV TZ=Asia/Shanghai
WORKDIR /data

COPY one-api /one-api
RUN chmod 0755 /one-api && mkdir -p /data/logs

EXPOSE 3000
VOLUME ["/data"]

ENTRYPOINT ["/one-api"]
CMD ["--port", "3000", "--log-dir", "/data/logs"]
