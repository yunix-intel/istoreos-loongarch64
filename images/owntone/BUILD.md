# OwnTone 29.3 (loong64) 构建记录

## 结论

- 镜像：`yunixintel/owntone:loong64` / `:24.10-la5`
- Hub 压缩大小：约 355MB（本地镜像 980MB）
- digest：`sha256:52c3e49c9f69f0fbcefe34ef186f70a48ca5f7e3cb5fff1d71924d06e6717b8f`
- 版本：OwnTone 29.3
- 验证：`/` 200、Web UI 可访问、健康检查 healthy
- 定位：DAAP/DACP/AirPlay 音乐服务器，替代 iTunes 共享

## 构建链路

1. 从源码 `autoreconf -fi`，配置：

   ```bash
   ./configure --prefix=/usr \
     --disable-spotify --disable-chromecast \
     --enable-install-user --disable-install-systemd
   ```

2. 编译产物 `/out/usr/sbin/owntone`、`/out/usr/lib/owntone`、
   `/out/usr/share/owntone`。
3. 运行阶段基于 `openeuler/openeuler:24.03`，安装：
   `libconfuse libevent json-c libsodium libplist libcurl libgcrypt libunistring
   sqlite-libs ffmpeg libwebsockets avahi avahi-tools avahi-libs dbus alsa-lib
   openssl-libs libxml2 zlib`。
4. entrypoint 启动 `dbus-daemon --system --fork` 与
   `avahi-daemon --daemonize --no-chroot`，再以 UID 998 的 `owntone` 用户运行。

## 遇到的问题

- **`AM_ICONV` / `AC_LIB_PREPARE_PREFIX` 未定义**：缺 gettext 宏，
  安装 `gettext-devel` 后重新 `autoreconf -fi`。
- **libwebsockets 找不到 `openssl/ssl.h`**：补 `openssl-devel`。
- **运行时 mDNS 初始化失败**：即使加了 `--mdns-no-rsp --mdns-no-daap
  --mdns-no-cname --mdns-no-web`，OwnTone 仍要求系统有 Avahi/D-Bus。
  镜像内安装并启动 `dbus-daemon` 与 `avahi-daemon` 解决。
- **日志文件权限**：entrypoint 先 `touch` 并 `chown` `/var/log/owntone.log`，
  否则降权后无法写日志。

## 运行

```bash
docker run -d --name owntone -p 3689:3689 \
  -v /path/to/music:/srv/music \
  -v owntone-cache:/var/cache/owntone \
  yunixintel/owntone:loong64
```

- Web UI/DAAP：`3689`。
- 音乐目录挂到 `/srv/music`；首次启动会扫描并建库。
- AirPlay 发现依赖容器网络能发 mDNS（host 网络或 macvlan 更稳）。
- 配置模板在 `/etc/owntone.conf`，可挂载覆盖。
- 该镜像以 `avahi-daemon` 在容器内运行；若宿主机已占用 Avahi，
  跨容器发现可能不稳定，此时建议 `--network host`。
