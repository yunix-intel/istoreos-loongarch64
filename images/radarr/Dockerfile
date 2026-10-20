# Radarr v6.4.4.10685 on loong64
# Base: local openEuler 24.03; app built on host with .NET 9 SDK (9.0.201, loongarch64).
# net8.0 framework-dependent publish + host .NET 9.0.3 runtime copied in (same approach as jackett).
# libe_sqlite3.so is a locally built SQLite 3.53.4 with SourceGear-compatible options.
# libMonoPosixHelper.so is a local loong64 shim for the Mono.Posix helper.
FROM openeuler/openeuler:24.03

# libicu is required by .NET globalization; ca-certificates for HTTPS indexers.
RUN dnf install -y libicu ca-certificates tzdata \
    && dnf clean all && rm -rf /var/cache/dnf

COPY libstdc++.so.6.0.33 /usr/lib64/
RUN ln -sf libstdc++.so.6.0.33 /usr/lib64/libstdc++.so.6

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

EXPOSE 7878
VOLUME ["/config"]

ENTRYPOINT ["dotnet", "/app/Radarr.dll", "-nobrowser", "-data=/config"]
