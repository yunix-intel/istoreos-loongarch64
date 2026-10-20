FROM openeuler/openeuler:24.03

RUN dnf install -y ca-certificates tzdata git \
    && dnf clean all

ENV GOGS_CUSTOM=/data/gogs

WORKDIR /app/gogs
COPY gogs /app/gogs/gogs
RUN chmod +x /app/gogs/gogs

VOLUME ["/data"]
EXPOSE 3000 22

ENTRYPOINT ["/app/gogs/gogs", "web", "--config", "/data/gogs/conf/app.ini"]
