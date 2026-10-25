# Reusable Node.js 24.22.1 + sharp 0.35.5 + libvips 8.18.7 base image for
# LoongArch64 (linux/loong64).
#
# libvips is built once here; applications should reuse /opt/vips and
# /opt/node_modules/sharp instead of building libvips again.
#
# Pinned sources:
#   libvips 8.18.7  sha256 5baaead3b0bb20ffdb9e9ff09aa9fda08620923df77b63b436654cb5e0b3bf94
#   sharp   0.35.5  sha256 3b6bbbe6b308f5c383938ca4a31926cd5d79c4651ed8c5fda16a97da2014a9ac

# ---------------------------------------------------------------------------
# Stage 1: build libvips with exactly the codecs sharp needs
# ---------------------------------------------------------------------------
FROM openeuler/openeuler:24.03 AS libvips

ARG VIPS_VERSION=8.18.7
ARG VIPS_SHA256=5baaead3b0bb20ffdb9e9ff09aa9fda08620923df77b63b436654cb5e0b3bf94
ARG VIPS_URL=https://github.com/libvips/libvips/releases/download/v${VIPS_VERSION}/vips-${VIPS_VERSION}.tar.xz

RUN dnf install -y --setopt=install_weak_deps=False \
        ca-certificates curl tar xz \
        meson ninja-build gcc-c++ pkgconf \
        glib2-devel expat-devel libjpeg-turbo-devel libpng-devel \
        libwebp-devel libtiff-devel lcms2-devel libexif-devel zlib-devel && \
    dnf clean all && rm -rf /var/cache/dnf

WORKDIR /tmp
RUN curl -fsSL --retry 3 -o vips.tar.xz "${VIPS_URL}" && \
    echo "${VIPS_SHA256}  vips.tar.xz" | sha256sum -c - && \
    tar xf vips.tar.xz

WORKDIR /tmp/vips-${VIPS_VERSION}
RUN meson setup build --prefix=/opt/vips --libdir=lib \
        -Dauto_features=disabled \
        -Dmodules=disabled \
        -Dintrospection=disabled \
        -Dexamples=false \
        -Ddocs=false \
        -Dcplusplus=true \
        -Djpeg=enabled \
        -Dpng=enabled \
        -Dwebp=enabled \
        -Dtiff=enabled \
        -Dexif=enabled \
        -Dlcms=enabled \
        -Dzlib=enabled && \
    ninja -C build && \
    ninja -C build install

# ---------------------------------------------------------------------------
# Stage 2: compile the sharp native addon against the global libvips
# ---------------------------------------------------------------------------
FROM yunixintel/node:24.22.1 AS sharp

ARG SHARP_VERSION=0.35.5
ARG SHARP_SHA256=3b6bbbe6b308f5c383938ca4a31926cd5d79c4651ed8c5fda16a97da2014a9ac
ARG SHARP_URL=https://registry.npmjs.org/sharp/-/sharp-${SHARP_VERSION}.tgz

# curl is not part of the base Node image; gcc/make/python3/pkgconf and the
# -devel packages are needed by node-gyp and by pkg-config.  vips.pc lists the
# codec libraries in Requires.private, so pkg-config needs their .pc files even
# though only the vips headers are included.
RUN dnf install -y --setopt=install_weak_deps=False \
        curl gcc-c++ make python3 pkgconf glib2-devel \
        expat-devel libjpeg-turbo-devel libpng-devel libwebp-devel \
        libtiff-devel lcms2-devel libexif-devel zlib-devel && \
    dnf clean all && rm -rf /var/cache/dnf

COPY --from=libvips /opt/vips /opt/vips

RUN curl -fsSL --retry 3 -o /tmp/sharp-${SHARP_VERSION}.tgz "${SHARP_URL}" && \
    echo "${SHARP_SHA256}  /tmp/sharp-${SHARP_VERSION}.tgz" | sha256sum -c -

# node-addon-api and node-gyp are build-time-only; keep them out of the final
# /opt/node_modules tree.
RUN mkdir -p /tmp/builddeps && cd /tmp/builddeps && \
    npm install --no-audit --no-fund --ignore-scripts \
        node-addon-api@8.9.2 node-gyp@12.4.0

# --install-strategy=nested keeps sharp's runtime deps (@img/colour,
# detect-libc, semver) inside sharp/node_modules, so the final image only has
# to copy /opt/node_modules/sharp.
RUN printf '{"name":"node-sharp","private":true}\n' > /opt/package.json && \
    cd /opt && npm install --no-audit --no-fund --ignore-scripts \
        --install-strategy=nested /tmp/sharp-${SHARP_VERSION}.tgz

RUN cd /opt/node_modules/sharp && \
    NODE_PATH=/tmp/builddeps/node_modules \
    SHARP_FORCE_GLOBAL_LIBVIPS=1 \
    PKG_CONFIG_PATH=/opt/vips/lib/pkgconfig \
    LD_LIBRARY_PATH=/opt/vips/lib \
    /tmp/builddeps/node_modules/.bin/node-gyp rebuild --directory=src && \
    test -f /opt/node_modules/sharp/src/build/Release/sharp-linux-loong64-${SHARP_VERSION}.node

# Drop object files and build metadata; keep only the loadable .node addon.
RUN cd /opt/node_modules/sharp/src && \
    rm -rf build/Release/obj.target build/Release/obj build/Release/.deps \
           build/.deps build/Makefile build/*.mk build/config.gypi \
           build/Release/*.a && \
    rm -rf /tmp/builddeps /tmp/sharp-${SHARP_VERSION}.tgz

# ---------------------------------------------------------------------------
# Stage 3: runtime
# ---------------------------------------------------------------------------
FROM yunixintel/node:24.22.1

RUN dnf install -y --setopt=install_weak_deps=False \
        glib2 expat libjpeg-turbo libpng libwebp libtiff \
        lcms2 libexif zlib libstdc++ && \
    dnf clean all && rm -rf /var/cache/dnf

COPY --from=libvips /opt/vips /opt/vips
COPY --from=sharp /opt/node_modules/sharp /opt/node_modules/sharp

ENV NODE_PATH=/opt/node_modules \
    LD_LIBRARY_PATH=/opt/vips/lib \
    SHARP_FORCE_GLOBAL_LIBVIPS=1

CMD ["node", "-e", "console.log(require('sharp').versions)"]
