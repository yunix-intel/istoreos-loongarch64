# Ente Web (loong64) 构建记录

## 结论

- 镜像：`yunixintel/ente-web:loong64` / `:24.10-la5`
- 大小：约 103MB（Hub 压缩；本地 243MB）
- digest：`sha256:feda42de4d593fb793d3139984b16da0b911e2a079d2232a583ef9d9b75efe67`
- 上游：`ente-io/ente` commit `1353a65`（2026-10）
- 验证：
  - 10 个端口（3000–3006、3008–3010）全部 200
  - photos `/gallery` 200
  - WASM 以 `application/wasm` 返回
  - 启动后占位符 0 处，`ENTE_API_ORIGIN` 在 17 个 JS 文件中生效
  - `docker restart` 改 origin 后可重新生效（模板复制方案）

## 构建链路

1. 源码：`git clone https://github.com/ente-io/ente`，切到构建时 commit `1353a65`。
2. 工具链（x86_64 WSL2）：Node 24.22.1、Rust 1.99.1 + wasm32、`nightly-2026-08-13`（cast 的 `-Z build-std` 需要）、wasm-bindgen 0.2.125、binaryen 120。
   脚本见 [`build-scripts/setup-toolchain.sh`](build-scripts/setup-toolchain.sh) 与 [`build-scripts/build-all.sh`](build-scripts/build-all.sh)。
3. 10 个 Next.js 16.4.2 应用全部静态导出（`output: export`），构建时写死占位符：
   ```bash
   NEXT_PUBLIC_ENTE_ENDPOINT=ENTE_API_ORIGIN_PLACEHOLDER npm run build:photos
   # albums accounts auth cast share embed paste locker memories 同理
   ```
4. 产物 `web/apps/<app>/out` 汇总为构建上下文 `out/<app>/`（1179 文件，84MB）。
5. 运行阶段基于 `cr.loongnix.cn/library/nginx:1.30.0`，一个 80 端口外的 10 个 server 块，分别指向各应用静态目录。

## 运行时契约

- 端口与应用对应：

  | 端口 | 应用 | 端口 | 应用 |
  |---|---|---|---|
  | 3000 | photos | 3005 | share |
  | 3001 | accounts | 3006 | embed |
  | 3002 | albums | 3008 | paste |
  | 3003 | auth | 3009 | locker |
  | 3004 | cast | 3010 | memories |

- `ENTE_API_ORIGIN` 必须指向 ente server（museum）的 HTTP 地址，例如 `http://<host>:8080`。
- 启动时把 `/out` 模板复制到 `/srv/ente`，在副本里替换占位符并改写 nginx root；
  因此改 `ENTE_API_ORIGIN` 后 `docker restart` 就能生效，不必重建容器。
- 无持久化卷；所有状态都在 ente server / PostgreSQL / S3。

## 遇到的问题

- **Rust 工具链下载卡死**：`static.rust-lang.org` 在 WSL 内不可用，改用
  `RUSTUP_DIST_SERVER=https://mirrors.ustc.edu.cn/rust-static`。
- **混装工具链**：中断安装留下 1.99.0 host + 1.99.1 wasm std，`E0514`；卸载 stable 后重装。
- **crates.io 卡住**：`~/.cargo/config.toml` 用 USTC sparse 源替换 crates-io。
- **wasm-opt 下载卡住**：wasm-pack 从 GitHub 拉 binaryen；改用 USTC Ubuntu 的
  `binaryen_120` deb 解包后放进 PATH。
- **cast 需要 nightly**：`rust/bindings/wasm/cast/rust-toolchain.toml` 固定
  `nightly-2026-08-13` 且需要 `rust-src` 做 `-Z build-std`。
- **占位符替换不可逆**：若直接在 `/out` 上 `sed -i`，第二次启动没有占位符可替换，
  改 origin 无效；本镜像改为复制到 `/srv/ente` 再改。

## 限制

- 仅静态导出：没有 Next.js 服务端、API routes、图片优化器；未知路径回退到各应用 `index.html`。
- 不保证逐字节可复现（Next build ID/时间戳），但源码 commit 与 lockfile 固定。
- 未做与真实 ente server 的登录/上传端到端联调；需要 server + PostgreSQL + MinIO 三件套。
