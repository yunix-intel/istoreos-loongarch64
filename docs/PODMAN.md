# Podman / Dockerman 栈（loong64 OpenWrt）

这份文档记录 la5 固件里容器栈的组成、构建坑和运行方式。它不是“装一个 podman 包”那么简单：
podman 5.5+ 删除了 boltdb，SQLite 成为唯一数据库后端，而 SQLite 需要 CGO。

## 1. 组成

| 组件 | 版本/来源 | 说明 |
|---|---|---|
| podman | 5.8.8，CGO 重编 | 静态 musl 版不行：`go-sqlite3 requires cgo` |
| crun | 1.30.1，musl 静态自编 | `--disable-seccomp/caps/criu/bpf/dl`，json-c/argp 用 staging |
| conmon | loong64 包 | 容器监控 |
| runc | 1.6.0 自编 | feed 1.1.14 的 `syscall_linux_64.go` 无 loong64 build tag |
| netavark / aardvark-dns | Alpine loong64 | 以 tar.gz 首启解压，避免 OpenWrt ABI 检查 |
| dockerd / containerd / docker CLI | la5 config 内置 | 供 iStore 应用和 dockerman 使用 |
| luci-app-dockerman | 0.5.26 | 纯 Lua；去掉 `@(aarch64||arm||x86_64)` 架构锁 |
| luci-lib-docker | 0.3.4 | 避免 feeds/luci 同名包抢占 |

## 2. 构建/打包坑

1. **podman 5.8.8 静态版启动失败**：`go-sqlite3 requires cgo`。
   必须 `CGO_ENABLED=1` 用 musl-gcc 编，把 SQLite 静态编入；boltdb 配置已被静默忽略。
2. **libseccomp 无 loongarch**：runc/dockerd 去掉 seccomp 依赖与 build tag；
   crun 编时 `--disable-seccomp`。
3. **containerd 1.7.22 vendored cilium/ebpf** 的 `endian_le.go` 无 loong64 build tag，需补。
4. **OpenWrt ABI 检查**：静态 musl 二进制直接放 `package/files` 会触发 `libc.musl-*` 依赖错误；
   改为 tar.gz + 首启解压。
5. **rootfs 分区**：docker+podman 栈后 1GB 会顶满，`make_ext4fs` 段错误；la5 改为 1.5GB。
6. 改包后必须 `make package/install` 再 `make target/install`，否则 rootfs 还是旧的。

## 3. 运行

OpenWrt 真机（la5 固件）首启会自动 `enable dockerd`。
podman 嵌套测试命令：

```bash
podman run --rm \
  --network=host \
  --security-opt seccomp=unconfined \
  --cgroups=disabled \
  --runtime crun \
  alpine:latest echo PODMAN-OK
```

`--network=none` 同样可用；`bridge` 需要宿主内核 `nft_conntrack`，
Loongnix 6.6.52 默认没有该模块，所以 bridge 暂不可用。

## 4. Dockerman

- dockerman 连的是宿主 Docker socket，不是 podman socket：
  `uci set dockerd.dockerman.socket_path='/root/docker.sock'`。
- OpenWrt 的 `/var/run` 是 tmpfs，不能把 socket 挂到 `/var/run` 下；
  用持久路径 `/root/docker.sock`。
- 容器内验证：`docker -H unix:///root/docker.sock ps` 能列出宿主容器。
- LuCI 菜单需要 `luci-compat`、`luci-lib-docker`、`luci-lib-ip`；docker CLI/ttyd/iptables-nft 在运行时另装。

## 5. 固件位置

- 公版 la5 已内置 dockerd/containerd/docker/tini + podman 三件套/netavark。
- 私人 p1 也包含同一栈，镜像在私有库，不公开。
- 发布资产：`release-24.10-la5/istoreos-...img.gz` 与 `opkg-feed-loongarch64_generic.tar.gz`。

## 6. 验证清单

```bash
podman info
podman run --rm --network=none --security-opt seccomp=unconfined --cgroups=disabled --runtime crun alpine true
docker ps
docker -H unix:///root/docker.sock ps
```

全部通过才认为容器栈可用；bridge 网络单独标注为“需要宿主 nft_conntrack”。
