# Redis 7.2.14 (loong64) 构建记录

## 结论

- 镜像：`yunixintel/redis:loong64` / `:24.10-la5`
- 大小：296MB，`linux/loong64`
- digest：`sha256:424db4cd0e160494db4886ad8a6915ef2d74012e1b51e3049c80aa50cf013137`
- 版本：Redis 7.2.14（openEuler 24.03 SP4 包）
- 验证：`PING`、`SET/GET`、重启后数据仍在、`REDIS_PASSWORD` 生效、
  `redis-cli` 健康检查 healthy。

## 构建

```bash
docker build -t redis:loong64 .
docker tag redis:loong64 yunixintel/redis:loong64
docker tag redis:loong64 yunixintel/redis:24.10-la5
docker push yunixintel/redis:loong64
docker push yunixintel/redis:24.10-la5
```

openEuler 的 `redis` 包已经是 7.2.x，官方镜像又无 loong64 资产，因此直接基于
系统包构建，避免源码编译和 glibc 偏差。

## 配置

镜像内配置 `/usr/local/etc/redis/redis.conf`：

```text
bind 0.0.0.0
protected-mode no
port 6379
dir /data
appendonly yes
appendfsync everysec
save 3600 1
save 300 100
save 60 10000
```

默认开启 AOF（`/data/appendonlydir`）并保留 RDB 快照规则。容器以 `redis`
用户运行，`/data` 已 chown。

## 启动

```bash
# 无密码（仅限可信内网）
docker run -d --name redis -p 6379:6379 -v redis-data:/data yunixintel/redis:loong64

# 带密码
docker run -d --name redis -p 6379:6379 -v redis-data:/data \
  -e REDIS_PASSWORD='change-me' yunixintel/redis:loong64
```

`REDIS_PASSWORD` 由 entrypoint 追加到临时配置副本，不会修改镜像内原文件。
密码不要包含空格或 `#`，否则 Redis 配置解析会截断。

## 注意

- 日志中的 `Memory overcommit must be enabled` 是宿主内核
  `vm.overcommit_memory` 设置提示；生产建议在宿主执行
  `sysctl vm.overcommit_memory=1`，家用低负载可忽略。
- 默认配置为了容器可用性关闭了 `protected-mode`；暴露到公网必须设置
  `REDIS_PASSWORD`，并在前面加防火墙或反向代理。
- 数据卷建议用命名卷；若挂宿主目录，需 `chown -R redis:redis <dir>`
  （openEuler 的 redis UID/GID 为 998:996，可用 `id redis` 确认）。
- 自定义启动参数会完全覆盖默认配置：`docker run ... redis:loong64 redis-server /my/redis.conf`。

## 验证命令

```bash
docker exec redis redis-cli ping
docker exec redis redis-cli set foo bar
docker restart redis && docker exec redis redis-cli get foo
docker exec redis redis-cli info server | grep redis_version
```
