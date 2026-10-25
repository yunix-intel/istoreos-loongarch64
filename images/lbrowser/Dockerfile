# Reusable Chromium/Playwright runtime for linux/loong64.
#
# Default (INSTALL_LBROWSER=0): a runtime image with every shared library
# LBrowser needs, but no LBrowser payload.  Mount the host installation
# read-only at run time:
#     -v /opt/apps/lbrowser:/opt/apps/lbrowser:ro
#
# Local testing only (INSTALL_LBROWSER=1): download and unpack the Loongnix deb
# into /opt/apps/lbrowser.  Do NOT publish an image built with this flag: the
# package ships no LICENSE/COPYING/copyright file, so redistribution is not
# clearly permitted.

FROM yunixintel/node:24.22.1 AS lbrowser-deb

ARG LBROWSER_VERSION=3.4.2293.2-1.stable
ARG LBROWSER_URL=https://pkg.loongnix.cn/loongnix/25/pool/main/l/lbrowser/lbrowser_3.4.2293.2-1.stable_loong64.deb
ARG LBROWSER_SHA256=2ecfb08bd35b0aadf13bc2d09ac35175d9825caf3c82d0859e5acb00b7dd5b6a
ARG INSTALL_LBROWSER=0

# Optional local-only payload.  The URL is pinned and verified before unpacking.
# With INSTALL_LBROWSER=0 this stage produces an empty directory, so the final
# image contains no LBrowser bytes at all.
RUN set -eux; \
    mkdir -p /out/opt/apps/lbrowser; \
    if [ "${INSTALL_LBROWSER}" = "1" ]; then \
        dnf install -y --setopt=install_weak_deps=False dpkg; \
        dnf clean all; rm -rf /var/cache/dnf /var/cache/yum; \
        curl -fL --retry 3 -o /tmp/lbrowser.deb "${LBROWSER_URL}"; \
        echo "${LBROWSER_SHA256}  /tmp/lbrowser.deb" | sha256sum -c -; \
        dpkg-deb -x /tmp/lbrowser.deb /out; \
        rm -f /tmp/lbrowser.deb; \
        test -x /out/opt/apps/lbrowser/lbrowser; \
    fi


FROM yunixintel/node:24.22.1

ENV PLAYWRIGHT_LAUNCH_OPTIONS_EXECUTABLE_PATH=/opt/apps/lbrowser/lbrowser \
    LBROWSER_EXECUTABLE=/opt/apps/lbrowser/lbrowser \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# LBrowser links GTK 2 and GTK 3, NSS/NSPR, CUPS, ALSA/PulseAudio and the usual
# X11/AT-SPI stack.  openEuler 24.03's glibc 2.38 satisfies the deb's >= 2.37.
RUN dnf install -y --setopt=install_weak_deps=False --setopt=tsflags=nodocs \
        alsa-lib \
        at-spi2-atk \
        at-spi2-core \
        avahi-libs \
        ca-certificates \
        cairo \
        cups-libs \
        dbus-libs \
        expat \
        fontconfig \
        freetype \
        gdk-pixbuf2 \
        glib2 \
        gnutls \
        gtk2 \
        gtk3 \
        iproute \
        kmod-libs \
        krb5-libs \
        libX11 \
        libXcomposite \
        libXcursor \
        libXdamage \
        libXext \
        libXfixes \
        libXi \
        libXinerama \
        libXrandr \
        libXrender \
        libatomic \
        libdrm \
        libffi \
        libjpeg-turbo \
        libpng \
        libstdc++ \
        libxcb \
        libxkbcommon \
        mesa-libgbm \
        nspr \
        nss \
        pango \
        pcre2 \
        pulseaudio-libs \
        systemd-libs \
        tzdata \
        dejavu-fonts \
        google-noto-sans-cjk-sc-fonts && \
    dnf clean all && rm -rf /var/cache/dnf /var/cache/yum && \
    mkdir -p /opt/apps/lbrowser /workspace

COPY --from=lbrowser-deb /out/opt/apps/lbrowser/ /opt/apps/lbrowser/

COPY cdp-proxy.mjs /usr/local/lib/lbrowser/cdp-proxy.mjs
COPY docker-entrypoint.sh /usr/local/bin/lbrowser-entrypoint.sh
RUN chmod 0755 /usr/local/bin/lbrowser-entrypoint.sh

ENV CDP_LISTEN_HOST=0.0.0.0 \
    CDP_LISTEN_PORT=9222 \
    CDP_UPSTREAM_HOST=127.0.0.1 \
    CDP_UPSTREAM_PORT=9223

WORKDIR /workspace
EXPOSE 9222
ENTRYPOINT ["/usr/local/bin/lbrowser-entrypoint.sh"]
CMD ["node"]
