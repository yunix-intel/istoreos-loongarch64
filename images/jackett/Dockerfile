# Jackett v0.24.2867 on loong64
# Base: local openEuler 24.03; app built on host with .NET 9 SDK (9.0.201, loongarch64).
# Framework-dependent publish + host .NET 9.0.3 runtime copied in (same approach as jellyfin).
FROM openeuler/openeuler:24.03

# libicu is required by .NET globalization; ca-certificates for HTTPS indexers.
RUN dnf install -y libicu ca-certificates tzdata     && dnf clean all && rm -rf /var/cache/dnf

COPY libstdc++.so.6.0.33 /usr/lib64/
RUN ln -sf libstdc++.so.6.0.33 /usr/lib64/libstdc++.so.6

COPY dotnet-min/ /usr/share/dotnet/
COPY out/ /app/

ENV DOTNET_ROOT=/usr/share/dotnet     PATH=/usr/share/dotnet:$PATH     DOTNET_CLI_TELEMETRY_OPTOUT=1     DOTNET_NOLOGO=1     XDG_CONFIG_HOME=/config     HOME=/config     TZ=UTC

RUN mkdir -p /config

EXPOSE 9117
VOLUME ["/config"]

ENTRYPOINT ["dotnet", "/app/jackett.dll", "--NoRestart", "--NoUpdates"]
