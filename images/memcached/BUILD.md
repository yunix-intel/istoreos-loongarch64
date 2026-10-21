# Memcached 1.6.42 (loong64) 构建记录

## 结论

- 镜像：`yunixintel/memcached:loong64` / `:24.10-la5`
- 大小：354MB，`linux/loong64`
- digest：`sha256:085ae16413b931b0f8829b2da54ee7363636a6f252afb0034d365040ce3b15ba`
- 版本：Memcached 1.6.42（openEuler 24.03 SP4）
- 验证：原始协议 `set/get` 成功、`stats` 返回 1.6.42、健康检查 healthy。

## 构建

```bash
docker build -t memcached:loong64 .
docker tag memcached:loong64 yunixintel/memcached:loong64
docker tag memcached:loong64 yunixintel/memcached:24.10-la5
docker push yunixintel/memcached:loong64
docker push yunixintel/memcached:24.10-la5
```

openEuler 的 `memcached` 包已创建 UID/GID 998:996 的 `memcached` 用户；
entrypoint 以 `-u memcached` 让服务降权，不需要额外安装 `gosu`/`runuser`。

## 运行时参数

默认启动：

```bash
docker run -d --name memcached -p 11211:11211 \
  -e MEMCACHED_MEMORY=128 yunixintel/memcached:loong64
```

| 环境变量 | 默认 | 对应参数 |
|---|---:|---|
| `MEMCACHED_MEMORY` | `64` | `-m`，单位 MB |
| `MEMCACHED_PORT` | `11211` | `-p` |
| `MEMCACHED_MAX_CONN` | `1024` | `-c` |
| `MEMCACHED_THREADS` | `4` | `-t` |

固定使用 `-l 0.0.0.0` 和 `-o modern`（启用现代内存分配器与 LRU 行为）。
自定义参数会完全覆盖默认命令：

```bash
docker run ... yunixintel/memcached:loong64 memcached -m 256 -p 11211 -l 0.0.0.0 -u memcached
```

## 注意

- Memcached 无认证、无持久化，数据只存在内存；重启即清空。
- 不要暴露到公网；只给同一 Docker 网络或可信内网使用。
- 宿主机内存不足时容器可能被 OOM kill；`MEMCACHED_MEMORY` 应明显小于可用内存。
- 应用侧需要相应客户端扩展：PHP 需 `memcached` 扩展，Python 需 `pymemcache`/`python-memcached`。
  本镜像只提供服务端，不改变应用镜像内的扩展。
- 健康检查只做 TCP 端口连通性检查，不执行协议级读写。

## 验证命令

```bash
# 原始协议
python3 - <<'PY'
import socket
s=socket.create_connection(("127.0.0.1",11211),5)
s.sendall(b"set foo 0 0 3\r\nbar\r\nget foo\r\n")
print(s.recv(4096).decode())
PY

# 运行状态
printf 'stats\r\n' | timeout 3 python3 -c 'import socket,sys;s=socket.create_connection(("127.0.0.1",11211));s.sendall(sys.stdin.buffer.read());print(s.recv(4096).decode())'
```
