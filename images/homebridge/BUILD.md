# Homebridge 2.4.0 + Config UI 5.29.0 (loong64) 构建记录

## 结论

- 镜像：`yunixintel/homebridge:loong64` / `:24.10-la5`
- 大小：582MB，`linux/loong64`
- digest：`sha256:93632682f3233daccc20a2d0ffa144b4571e1fbae5da0684a183ced5608c30ee`
- 版本：Homebridge 2.4.0（HAP 2.2.2）+ Homebridge Config UI X 5.29.0 / Node.js 22.23.3
- 验证：Homebridge 2.4.0 启动、UI `:8581` 返回 200、标题 Homebridge、
  `hb-service` 同时拉起 UI 与 Homebridge、健康检查 healthy。

## 运行时与架构变化

openEuler 24.03 自带 Node 20，不满足 Homebridge 2.x / UI 5.x 的 Node ≥22.9/22.12。
因此使用 unofficial-builds 的 Node 22.23.3 loong64 基础镜像
`yunixintel/node:22.23.3`（见 [../node/BUILD.md](../node/BUILD.md)）。

Homebridge Config UI 5 不再由 Homebridge 插件自己启动 Web 服务；它由
`hb-service` 作为 supervisor 同时运行 UI 和 Homebridge。单独运行
`homebridge` 只会启动 HomeKit 核心，8581 不会监听。

## node-pty 的 loong64 处理

Config UI 依赖 `@homebridge/node-pty-prebuilt-multiarch@0.14.1`。它的 npm 包：

- 只带 `linux-x64/ia32/arm/arm64` 预编译；
- `files` 字段刻意不包含 `src/unix`，所以无法从 npm 包直接源码编译。

处理方式：

1. `npm install -g --ignore-scripts` 安装 Homebridge/UI，跳过失败的预编译安装。
2. clone `homebridge/node-pty-prebuilt-multiarch` 的 `v0.14.1` 源码。
3. `npm install --ignore-scripts && npx node-gyp rebuild`，在 loong64 上编出
   `build/Release/pty.node`（约 78KB）。
4. 把 `pty.node` 复制到 UI 包内的
   `@homebridge/node-pty-prebuilt-multiarch/build/Release/`。

这样保留 Web 终端功能，同时运行镜像不需要 gcc/make。

## 构建

```bash
docker build -t homebridge:loong64 .
docker tag homebridge:loong64 yunixintel/homebridge:loong64
docker tag homebridge:loong64 yunixintel/homebridge:24.10-la5
docker push yunixintel/homebridge:loong64
docker push yunixintel/homebridge:24.10-la5
```

**另一个踩坑**：Homebridge 2.4.0 的 npm bin 是 `bin/homebridge.js`，不是
`bin/homebridge`。运行阶段必须创建：

```dockerfile
RUN ln -s ../lib/node_modules/homebridge/bin/homebridge.js /opt/node22/bin/homebridge
```

直接 `COPY` npm 生成的符号链接会被解引用，`fs.realpathSync` 解析到错误目录。

## 运行

HomeKit 依赖 mDNS，推荐 host 网络：

```bash
docker run -d --name homebridge --network=host \
  -v homebridge-data:/homebridge \
  yunixintel/homebridge:loong64
```

entrypoint 默认执行：

```text
node /opt/node22/lib/node_modules/homebridge-config-ui-x/dist/bin/hb-service.js \
  run -U /homebridge --docker
```

- Config UI：`http://<host>:8581/`。
- HomeKit 端口：`51826`；host 网络下可直接被 iOS 发现。
- 数据目录 `/homebridge`：`config.json`、`homebridge.log`、持久化缓存、插件都在这里。
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
- Node 22 来自 unofficial-builds，审计时记录其 URL 与 SHA256（见 node 镜像文档）。

## 验证命令

```bash
curl -fsS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8581/
docker exec homebridge /opt/node22/bin/homebridge -V
docker exec homebridge ps -ef | grep -E 'hb-service|homebridge'
docker logs homebridge | grep -E 'Started Homebridge|Homebridge UI'
```
