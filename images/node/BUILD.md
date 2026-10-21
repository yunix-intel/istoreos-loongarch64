# Node.js 24.22.1 linux-loong64 基础镜像

## 结论

- 镜像：`yunixintel/node:24.22.1` / `:loong64` / `:24.10-la5`
- 大小：420MB，`linux/loong64`
- digest：`sha256:0f4d19bb66e5251ec413aa902eb60b311c61177800c7f156880f5f36b9514fb5`
- 验证：`node -v` 24.22.1、`npm -v` 11.19.1、`corepack --version` 0.36.0；
  在 openEuler 24.03 容器内可直接运行。
- 旧的 Node 22.23.3 仍保留在 `yunixintel/node:22.23.3`，供需要固定 22 线的场景使用。

## 来源与校验

Node.js 官方主站不发布 linux-loong64 资产，但 Node 的 unofficial-builds
提供了完整的 24.22.1 loong64 构建：

```text
https://unofficial-builds.nodejs.org/download/release/v24.22.1/node-v24.22.1-linux-loong64.tar.xz
SHA256 5653027bb2f60b88771997000bb27c2983ae46176d35c26da352dc71ee6b6b58
```

该二进制的最高 glibc 符号要求是 `GLIBC_2.38`，与 openEuler 24.03 的 glibc
完全匹配，因此不需要像 vaultwarden 那样内置宿主 glibc 闭包。

Node 24 是当前 LTS（Krypton）；Homebridge 2.x 与 Node-RED 5.x 都支持。

## 构建

```bash
# 解压到构建上下文
tar xf node-v24.22.1-linux-loong64.tar.xz
docker build -t node:24.22.1-loong64 .
docker tag node:24.22.1-loong64 yunixintel/node:24.22.1
docker tag node:24.22.1-loong64 yunixintel/node:loong64
docker tag node:24.22.1-loong64 yunixintel/node:24.10-la5
docker push yunixintel/node:24.22.1
docker push yunixintel/node:loong64
docker push yunixintel/node:24.10-la5
```

镜像基于 openEuler 24.03，安装 `ca-certificates`、`tzdata`、`libstdc++`，
把 Node 运行时放在 `/opt/node24` 并加入 `PATH`。`include/` 保留给原生模块
编译使用。

## 用途

Node-RED 5 和 Homebridge 2 的 Dockerfile 都以
`FROM node:24.22.1-loong64` 作为构建阶段，并在运行阶段只复制
`/opt/node24/bin` 与 `/opt/node24/lib`，避免把 65MB 头文件带进运行镜像。

npm 全局前缀是 `/opt/node24`，不是 `/usr/local`：

```text
npm root -g   -> /opt/node24/lib/node_modules
npm prefix -g -> /opt/node24
```

编写 Dockerfile 时复制全局包要使用 `/opt/node24/lib/node_modules/...`，
CLI 符号链接放在 `/opt/node24/bin/...`。

## 注意

- 这是 unofficial-builds 资产，不是 nodejs.org 主站发布；版本与主站同源，
  但供应链审计时应记录 URL 与 SHA256。
- 镜像不包含 gcc/make；需要编译原生模块的应用应在自己的 build 阶段安装工具链。
- 运行镜像只需 `bin/` 和 `lib/`；`include/`、`share/` 仅构建阶段需要。
- Node 22 版本镜像仍可用，但 `loong64`/`24.10-la5` 浮动 tag 现在指向 Node 24。

## 验证命令

```bash
docker run --rm yunixintel/node:24.22.1 node -v
docker run --rm yunixintel/node:24.22.1 npm -v
docker run --rm yunixintel/node:24.22.1 sh -c 'npm root -g; npm prefix -g'
```
