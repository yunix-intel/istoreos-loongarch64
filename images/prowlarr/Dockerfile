# Prowlarr 2.6.5.5623 on loong64
# Backend built from source with .NET 9 SDK 9.0.201 (target net8.0, framework-dependent).
# Run with .NET 9 runtime using DOTNET_ROLL_FORWARD=LatestMajor (no .NET 8 loong64 runtime available).
FROM openeuler/openeuler:24.03

# libicu is required by .NET globalization; ca-certificates for HTTPS indexers.
RUN dnf install -y libicu ca-certificates tzdata \
    && dnf clean all && rm -rf /var/cache/dnf

# Newer libstdc++ from host (same approach as the local jackett image).
COPY libstdc++.so.6.0.33 /usr/lib64/
RUN ln -sf libstdc++.so.6.0.33 /usr/lib64/libstdc++.so.6

# .NET 9.0.3 runtime (loongarch64), copied from /home/yunix/dotnet.
COPY dotnet-min/ /usr/share/dotnet/
# Published app + UI + loongarch64 libe_sqlite3.so + libMonoPosixHelper.so.
COPY out/ /app/

ENV DOTNET_ROOT=/usr/share/dotnet \
    PATH=/usr/share/dotnet:$PATH \
    DOTNET_CLI_TELEMETRY_OPTOUT=1 \
    DOTNET_NOLOGO=1 \
    DOTNET_ROLL_FORWARD=LatestMajor \
    XDG_CONFIG_HOME=/config \
    HOME=/config \
    TZ=UTC

RUN mkdir -p /config

EXPOSE 9696
VOLUME ["/config"]

ENTRYPOINT ["dotnet", "/app/Prowlarr.dll", "-nobrowser", "-data=/config"]
