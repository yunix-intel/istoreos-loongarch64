# Sonarr v4.0.20.3014 on loong64
# Base: local openEuler 24.03; app built on host with .NET 9 SDK (9.0.201, loongarch64).
# net6.0 framework-dependent publish + host .NET 9.0.3 runtime copied in (same approach as jackett).
FROM openeuler/openeuler:24.03

# libicu for .NET globalization; sqlite-libs provides libsqlite3.so.0 used by System.Data.SQLite.
RUN dnf install -y libicu ca-certificates tzdata sqlite-libs \
    && dnf clean all && rm -rf /var/cache/dnf

COPY libstdc++.so.6.0.33 /usr/lib64/
RUN ln -sf libstdc++.so.6.0.33 /usr/lib64/libstdc++.so.6 \
    && ln -sf libsqlite3.so.0 /usr/lib64/libsqlite3.so

COPY dotnet-min/ /usr/share/dotnet/
COPY out/ /app/

ENV DOTNET_ROOT=/usr/share/dotnet \
    PATH=/usr/share/dotnet:$PATH \
    DOTNET_CLI_TELEMETRY_OPTOUT=1 \
    DOTNET_NOLOGO=1 \
    DOTNET_ROLL_FORWARD=LatestMajor \
    LD_LIBRARY_PATH=/app \
    HOME=/config \
    XDG_CONFIG_HOME=/config \
    TZ=UTC

RUN mkdir -p /config

EXPOSE 8989
VOLUME ["/config"]

ENTRYPOINT ["dotnet", "/app/Sonarr.dll", "-nobrowser", "-data=/config"]
