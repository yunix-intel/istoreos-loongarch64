FROM openeuler/openeuler:24.03

ENV TZ=Asia/Shanghai \
    PORT=8080 \
    SHIORI_DIR=/data

RUN dnf install -y ca-certificates tzdata \
    && dnf clean all \
    && mkdir -p /data

WORKDIR /data

COPY shiori /usr/local/bin/shiori
RUN chmod 755 /usr/local/bin/shiori

EXPOSE 8080
ENTRYPOINT ["/usr/local/bin/shiori"]
CMD ["server"]
