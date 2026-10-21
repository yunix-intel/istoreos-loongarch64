# Homebridge 1.11.4 + Config UI 4.80.0 (loong64) 构建记录

## 结论

- 镜像：`yunixintel/homebridge:loong64` / `:24.10-la5`
- 大小：449MB，`linux/loong64`
- digest：`sha256:d90b3f1c3bed34dada1cf9508738a12cd673eaaa68ef80677053c5fce890e9e7`
- 版本：Homebridge 1.11.4（HAP 0.14.3）+ Homebridge Config UI X 4.80.0
- 验证：Homebridge 启动并输出配对码、UI `:8581` 返回 200、标题 Homebridge、
  健康检查 healthy。

## 版本边界（重要）

Homebridge 2.x 与 Config UI 5.x 都要求 Node.js ≥22.9/22.12，而 openEuler 24.03
只提供 Node.js 20.18.2。因此本镜像固定在仍支持 Node 20 的最后一档：

- `homebridge@1.11.4`
- `homebridge-config-ui-x@4.80.0`

Node.js 20 已进入 EOL，Homebridge 1.x 也不是当前主线。这个镜像适合在龙芯上
“能用、可管理”的场景；对安全更新有硬要求时，应等 loong64 Node 22 运行时可用后
再升级到 Homebridge 2.x。

## 构建

```bash
docker build -t homebridge:loong64 .
docker tag homebridge:loong64 yunixintel/homebridge:loong64
docker tag homebridge:loong64 yunixintel/homebridge:24.10-la5
docker push yunixintel/homebridge:loong64
docker push yunixintel/homebridge:24.10-la5
```

多阶段构建：

- `build` 阶段安装 `gcc-c++ make python3`，执行
  `npm install -g --unsafe-perm homebridge@1.11.4 homebridge-config-ui-x@4.80.0`；
  Config UI 的部分原生依赖在此阶段编译。
- 运行阶段只保留 Node/npm，复制 `/usr/local/lib/node_modules`。

**踩坑**：`/usr/local/bin/homebridge` 是 npm 创建的符号链接。直接
`COPY --from=build` 会把符号链接解引用成普通文件，脚本里的
`fs.realpathSync(__filename)` 于是解析到 `/usr/local/lib`，启动时报
`Cannot find module '/usr/local/lib/cli'`。必须在运行阶段重新创建符号链接：

```dockerfile
RUN ln -s ../lib/node_modules/homebridge/bin/homebridge /usr/local/bin/homebridge
```

## 运行

HomeKit 依赖 mDNS，推荐 host 网络：

```bash
docker run -d --name homebridge --network=host \
  -v homebridge-data:/homebridge \
  yunixintel/homebridge:loong64
```

- Config UI：`http://<host>:8581/`。
- HomeKit 端口：`51826`；host 网络下可直接被 iOS 发现。
- 数据目录 `/homebridge`：`config.json`、持久化缓存、插件都在这里。
- 容器以 UID 1000（`homebridge`）运行；挂宿主目录需
  `chown -R 1000:1000 <dir>`。
- 首次启动会从镜像复制最小 `config.json`，其中已包含 Config UI 平台：

```json
{
  "platforms": [
    { "platform": "config", "name": "Config", "port": 8581 }
  ]
}
```

## 注意

- 默认配对码是 `031-45-154`，桥 MAC 是 `0E:5A:2B:3C:4D:5E`；首次进入 UI 后应修改，
  避免与其它实例冲突。
- bridge 网络下 UI 可用，但 HomeKit 的 mDNS 广播通常无法跨网段；生产用 host 网络。
- 运行镜像保留 npm，可在 UI 里安装插件；但没有 gcc/make，带原生编译步骤的插件会失败。
  需要时基于本 Dockerfile 的 build 阶段自建带编译器的变体。
- 升级 Homebridge 大版本前备份整个 `/homebridge`；插件与缓存不只在 config.json。
- Homebridge 1.x / Node 20 的安全更新已结束，公网暴露 UI 时必须加反向代理认证。

## 验证命令

```bash
curl -fsS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8581/
docker exec homebridge runuser -u homebridge -- homebridge -V
docker logs homebridge | grep -E 'Homebridge v|Homebridge UI'
docker exec homebridge ls -la /homebridge
```
