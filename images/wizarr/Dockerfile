FROM openeuler/openeuler:24.03 AS builder

RUN dnf install -y gcc make tar gzip xz-devel zlib-devel bzip2-devel libffi-devel openssl-devel sqlite-devel ncurses-devel readline-devel findutils  && dnf clean all && rm -rf /var/cache/dnf

WORKDIR /tmp
COPY Python-3.13.9.tgz /tmp/
RUN tar xzf Python-3.13.9.tgz  && cd Python-3.13.9  && ./configure --prefix=/usr/local --with-ensurepip=install  && make -j$(nproc)  && make install

RUN /usr/local/bin/python3.13 -m venv /opt/venv

RUN dnf install -y rust cargo && dnf clean all && rm -rf /var/cache/dnf

COPY vendor/ /tmp/vendor/
RUN /opt/venv/bin/pip install --no-cache-dir --no-index --no-deps /tmp/vendor/*.whl

COPY vendor-src/brotli-1.2.0.tar.gz /tmp/
RUN cd /tmp  && tar xzf brotli-1.2.0.tar.gz  && sed -i 's|#define BROTLI_MODEL(M) __attribute__((model(M)))|#define BROTLI_MODEL(M) /* M */|' brotli-1.2.0/c/common/platform.h  && /opt/venv/bin/pip install --no-cache-dir /tmp/brotli-1.2.0

COPY requirements.txt /tmp/requirements.txt
RUN /opt/venv/bin/pip install --no-cache-dir --prefer-binary --timeout 60 --retries 3       --index-url https://pypi.org/simple -r /tmp/requirements.txt

FROM openeuler/openeuler:24.03

RUN dnf install -y openssl-libs zlib bzip2-libs libffi xz-libs sqlite-libs ncurses-libs readline tzdata ca-certificates shadow-utils findutils  && dnf clean all && rm -rf /var/cache/dnf

COPY --from=builder /usr/local /usr/local
COPY --from=builder /opt/venv /opt/venv
ENV PATH=/opt/venv/bin:/usr/local/bin:/usr/local/sbin:/usr/sbin:/usr/bin:/sbin:/bin

RUN groupadd -r wizarr && useradd -r -g wizarr -d /app -s /sbin/nologin wizarr

WORKDIR /app
COPY --chown=wizarr:wizarr wizarr-2026.10.1/ /app/
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh  && mkdir -p /data/database /.cache  && chown -R wizarr:wizarr /data /.cache /app

ENV FLASK_ENV=production     FLASK_APP=run:app     HOST=0.0.0.0     PORT=5690     APP_VERSION=2026.10.1
USER wizarr
EXPOSE 5690
VOLUME ["/data"]
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["gunicorn","--config","gunicorn.conf.py","--umask","007","run:app"]
