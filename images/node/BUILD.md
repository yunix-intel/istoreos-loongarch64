# Node.js 22.23.3 linux-loong64 基础镜像

## 结论

- 镜像：`yunixintel/node:22.23.3` / `:loong64` / `:24.10-la5`
- 大小：417MB，`linux/loong64`
- digest：`sha256:99d0b28f671ae32b754eedf283ca912cd5b8a58e60c79ebe5bd26e214da09692`
- 验证：`node -v` 22.23.3、`npm -v` 10.9.9、`corepack --version` 0.36.0；
  在 openEuler 24.03 容器内可直接运行。

## 来源与校验

Node.js 官方主站不发布 linux-loong64 资产，但 Node 的 unofficial-builds
提供了完整的 22.23.3 loong64 构建：

```text
https://unofficial-builds.nodejs.org/download/release/v22.23.3/node-v22.23.3-linux-loong64.tar.xz
SHA256 c5594c2342faa1cad5e5cf93a8502082aaa9aadafe8114d12c2f61e9fdee9599
```

该二进制的最高 glibc 符号要求是 `GLIBC_2.38`，与 openEuler 24.03 的 glibc
完全匹配，因此不需要像 vaultwarden 那样内置宿主 glibc 闭包。

## 构建

```bash
# 解压到构建上下文
tar xf node-v22.23.3-linux-loong64.tar.xz
docker build -t node:22.23.3-loong64 .
docker tag node:22.23.3-loong64 yunixintel/node:22.23.3
docker tag node:22.23.3-loong64 yunixintel/node:loong64
docker tag node:22.23.3-loong64 yunixintel/node:24.10-la5
docker push yunixintel/node:22.23.3
docker push yunixintel/node:loong64
docker push yunixintel/node:24.10-la5
```

镜像基于 openEuler 24.03，安装 `ca-certificates`、`tzdata`、`libstdc++`，
把 Node 运行时放在 `/opt/node22` 并加入 `PATH`。`include/` 保留给原生模块
编译使用。

## 用途

Node-RED 5 和 Homebridge 2 的 Dockerfile 都以
`FROM node:22.23.3-loong64` 作为构建阶段，并在运行阶段只复制
`/opt/node22/bin` 与 `/opt/node22/lib`，避免把 65MB 头文件带进运行镜像。

Node 应用的全局 npm 前缀是 `/opt/node22`，不是 `/usr/local`：

```text
npm root -g  -> /opt/node22/lib/node_modules
npm prefix -g -> /opt/node22
```

编写 Dockerfile 时复制全局包要使用 `/opt/node22/lib/node_modules/...`，
CLI 符号链接放在 `/opt/node22/bin/...`。

## 注意

- 这是 unofficial-builds 资产，不是 nodejs.org 主站发布；版本与主站同源，
  但供应链审计时应记录 URL 与 SHA256。
- Node 22 是 LTS 线；需要 Node 24/26 时应重新评估 loong64 构建可用性。
- 镜像不包含 gcc/make；需要编译原生模块的应用应在自己的 build 阶段安装工具链。
- 运行镜像只需 `bin/` 和 `lib/`；`include/`、`share/` 仅构建阶段需要。

## 验证命令

```bash
docker run --rm yunixintel/node:22.23.3 node -v
docker run --rm yunixintel/node:22.23.3 npm -v
docker run --rm yunixintel/node:22.23.3 sh -c 'npm root -g; npm prefix -g'
```
