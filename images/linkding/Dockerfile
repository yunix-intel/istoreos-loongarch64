# linkding v1.47.0 loong64 image
# Base: openEuler 24.03 LTS SP4 (has loongarch64 packages; Docker Hub has no loong64 python image)
# Python 3.13.16 built from source (linkding requires >=3.13, openEuler only ships 3.11)
# Frontend: npm/esbuild; @esbuild/linux-loong64 0.28.2 exists in package-lock, so no cross-build needed

# ---- Stage 1: frontend bundle (esbuild, arch-specific binary available for loong64) ----
FROM openeuler/openeuler:24.03 AS nodebuild
RUN dnf install -y nodejs npm \
    && dnf clean all \
    && node --version && npm --version
WORKDIR /build
COPY src/linkding-1.47.0/package.json src/linkding-1.47.0/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY src/linkding-1.47.0/bookmarks/frontend ./bookmarks/frontend
COPY src/linkding-1.47.0/bookmarks/styles ./bookmarks/styles
RUN npm run build \
    && ls -l bookmarks/static/bundle.js bookmarks/static/theme-light.css bookmarks/static/theme-dark.css

# ---- Stage 2: build CPython 3.13 + install Python dependencies ----
FROM openeuler/openeuler:24.03 AS pybuild
ARG PYTHON_VERSION=3.13.16
RUN dnf install -y gcc gcc-c++ make \
        openssl-devel bzip2-devel libffi-devel zlib-devel sqlite-devel xz-devel \
        ncurses-devel readline-devel pcre-devel pcre2-devel libicu-devel \
        rust cargo pkgconf git wget unzip findutils diffutils \
    && dnf clean all
COPY src/Python-${PYTHON_VERSION}.tgz /tmp/Python.tgz
RUN cd /tmp \
    && tar xzf Python.tgz \
    && cd Python-${PYTHON_VERSION} \
    && ./configure --prefix=/usr/local --with-ensurepip=install --enable-loadable-sqlite-extensions \
    && make -j"$(nproc)" \
    && make install \
    && python3 --version \
    && python3 -m pip --version
# cryptography 50 has no loong64 wheel -> maturin/rust; OPENSSL_NO_VENDOR uses openEuler OpenSSL
ENV OPENSSL_NO_VENDOR=1
RUN python3 -m pip install --no-cache-dir --upgrade pip setuptools wheel \
    && python3 -m pip install --no-cache-dir \
        "beautifulsoup4>=4.14.3" \
        "bleach>=6.4.0" \
        "bleach-allowlist>=1.0.3" \
        "django>=6.0.7" \
        "djangorestframework>=3.16.1" \
        "huey>=2.5.5" \
        "markdown>=3.10" \
        "mozilla-django-oidc>=5.0.2" \
        "requests>=2.33.0" \
        "supervisor>=4.3.0" \
        "uwsgi>=2.0.31" \
        "waybackpy>=3.0.6" \
    && python3 -m pip check

# ---- Stage 3: SQLite ICU extension (case-insensitive search/collation) ----
FROM openeuler/openeuler:24.03 AS icubuild
RUN dnf install -y gcc make sqlite-devel libicu-devel pkgconf \
    && dnf clean all
COPY src/icu.c /src/icu.c
RUN cd /src \
    && gcc -fPIC -shared icu.c $(pkg-config --libs --cflags icu-uc icu-io) -o /libicu.so \
    && ls -l /libicu.so

# ---- Stage 4: runtime ----
FROM openeuler/openeuler:24.03
RUN dnf install -y openssl-libs zlib bzip2-libs libffi xz-libs ncurses-libs readline \
        sqlite-libs libicu pcre pcre2 ca-certificates shadow curl mailcap \
    && dnf clean all \
    && groupadd -r www-data \
    && useradd -r -g www-data -d /etc/linkding -s /usr/sbin/nologin www-data
COPY --from=pybuild /usr/local /usr/local
RUN ln -sf /usr/local/bin/python3 /usr/local/bin/python
ENV PATH=/usr/local/bin:$PATH
WORKDIR /etc/linkding
COPY src/linkding-1.47.0/ ./
COPY --from=nodebuild /build/bookmarks/static/bundle.js /build/bookmarks/static/bundle.js.map bookmarks/static/
COPY --from=nodebuild /build/bookmarks/static/theme-light.css /build/bookmarks/static/theme-dark.css bookmarks/static/
COPY --from=icubuild /libicu.so ./libicu.so
# collect with prod settings: no STATICFILES_DIRS, matches what uwsgi serves from ./static
RUN mkdir -p data \
    && DJANGO_SETTINGS_MODULE=bookmarks.settings.prod python3 manage.py collectstatic --noinput \
    && chmod +x bootstrap.sh
ENV LD_SERVER_HOST=0.0.0.0
ENV UWSGI_MAX_FD=4096
EXPOSE 9090
VOLUME ["/etc/linkding/data"]
HEALTHCHECK --interval=30s --retries=3 --timeout=2s CMD curl -f http://localhost:9090/health || exit 1
CMD ["./bootstrap.sh"]
