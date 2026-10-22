FROM openeuler/openeuler:24.03
RUN dnf install -y --disablerepo=debuginfo --disablerepo=EPOL --disablerepo=source --disablerepo=update-source \
        --setopt=retries=1 --setopt=timeout=15 --setopt=install_weak_deps=False \
        ca-certificates tzdata curl bash shadow util-linux \
        perl perl-local-lib libarchive libffi openssl-libs ImageMagick redis expat zlib && \
    dnf clean all && rm -rf /var/cache/dnf && \
    groupadd -g 9001 koyomi && useradd -u 9001 -g 9001 -M -d /home/koyomi -s /bin/bash koyomi && \
    mkdir -p /home/koyomi/lanraragi/{content,thumb,database,log,temp} && \
    chown -R koyomi:koyomi /home/koyomi
COPY perl5 /home/koyomi/perl5
COPY app /home/koyomi/lanraragi
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod 0755 /usr/local/bin/docker-entrypoint.sh && chown -R koyomi:koyomi /home/koyomi
ENV PATH=/home/koyomi/perl5/bin:$PATH \
    PERL5LIB=/home/koyomi/perl5/lib/perl5:/home/koyomi/perl5/lib/perl5/loongarch64-linux-thread-multi \
    LRR_NETWORK=http://*:3000 \
    LRR_UID=9001 \
    LRR_GID=9001
WORKDIR /home/koyomi/lanraragi
EXPOSE 3000
VOLUME ["/home/koyomi/lanraragi/content", "/home/koyomi/lanraragi/thumb", "/home/koyomi/lanraragi/database"]
HEALTHCHECK --interval=30s --timeout=5s --retries=10 \
    CMD curl -fsS http://127.0.0.1:3000/ >/dev/null || exit 1
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
