FROM openeuler/openeuler:24.03
RUN dnf install -y --setopt=install_weak_deps=False ca-certificates tzdata curl && \
    dnf clean all && rm -rf /var/cache/dnf
WORKDIR /app
COPY gotify-app /app/gotify-app
ENV GOTIFY_SERVER_PORT=8080 \
    GOTIFY_DATABASE_DIALECT=sqlite3 \
    GOTIFY_DATABASE_CONNECTION=/data/gotify.db
VOLUME ["/data"]
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --retries=5 \
    CMD curl -fsS http://127.0.0.1:8080/health || exit 1
ENTRYPOINT ["/app/gotify-app"]
CMD ["serve"]
