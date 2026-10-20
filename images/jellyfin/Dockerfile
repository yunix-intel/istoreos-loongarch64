FROM openeuler/openeuler:24.03
RUN yum install -y ffmpeg libicu fontconfig dejavu-sans-fonts google-noto-cjk-fonts && yum clean all && rm -rf /var/cache/yum
COPY libstdc++.so.6.0.33 /usr/lib64/
RUN ln -sf libstdc++.so.6.0.33 /usr/lib64/libstdc++.so.6
COPY dotnet-min/ /usr/share/dotnet/
COPY app/ /jellyfin/
ENV DOTNET_ROOT=/usr/share/dotnet
ENV PATH="/usr/share/dotnet:${PATH}"
ENV DOTNET_CLI_TELEMETRY_OPTOUT=1
ENV DOTNET_NOLOGO=1
EXPOSE 8096
VOLUME ["/config", "/media"]
ENTRYPOINT ["dotnet", "/jellyfin/jellyfin.dll", "--webdir", "/jellyfin/jellyfin-web", "--ffmpeg", "/usr/bin/ffmpeg", "--datadir", "/config"]
