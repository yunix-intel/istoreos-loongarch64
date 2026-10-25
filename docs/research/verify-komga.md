# Komga 1.29.1 loong64 格式/封面功能验证

日期：2026-10-25
环境：Host A（SSH `loongson-lab`，LoongArch64，Docker 26.1.5）；镜像 `yunixintel/komga:loong64`
ID `sha256:7a5f8283b4be…0876a1f`（2026-10-24 构建）；运行时 JDK 21.0.11 BiSheng；Komga 1.29.1。
方法：全新 named volume，端口 14301/14302，样本均为最小构造文件；测试后容器/卷/数据已清理。

## 结论

| # | 项目 | 状态 | 结论 |
|---|---|---|---|
| 1 | CBZ / PDF / EPUB 扫描与阅读 | PASS | 三者均 READY；CBZ/PDF 页面 200，EPUB 走 manifest |
| 2 | RAR / CBR | PASS | 无 rar/unrar 工具，junrar 纯 Java 读取 RAR4 成功 |
| 3 | HEIF / JXL 封面 | FAIL | JDK 21 下 nightmonkeys 插件被禁用，无缩略图、无法解码 |
| 4 | Kobo 转换 | BLOCKED | 无 kepubify；同步可用但 KEPUB 转换被静默跳过 |
| 5 | 只读 `/data` | PASS | `:ro` 挂载下扫描、阅读正常 |
| 6 | 认证 / 首用户 | PASS | 首用户走 `/api/v1/claim` 一次性认领 |

## 1. CBZ / PDF / EPUB 扫描

```bash
docker run -d --name komga-verify -p 14301:25600 \
  -v komga-verify-config:/config -v /tmp/komga-verify/data:/data \
  yunixintel/komga:loong64
# 认领管理员后建库：POST /api/v1/libraries {"name":"Verify","root":"/data"}
```

| 样本 | series / books | media.status | mediaType | pagesCount | 阅读请求 | 缩略图 |
|---|---|---|---|---|---|---|
| CBZ（2 张 PNG） | 1 / 1 | READY | application/zip | 2 | `/pages/1` 200 image/png 99 B | 200 image/jpeg |
| PDF（1 页文字） | 1 / 1 | READY | application/pdf | 1 | `/pages/1` 200 application/pdf 816 B | 200 image/jpeg |
| EPUB（1 页文字） | 1 / 1 | READY | application/epub+zip | 1 | `/pages/1` **500**，`/manifest/epub` 200 | 404（无封面图） |
| EPUB（含 cover-image） | 1 / 1 | READY | application/epub+zip | 1 | manifest 200 | 200 image/jpeg 692 B |

EPUB 的 500 是明确的设计行为，不是扫描失败：
`{"status":500,"message":"Epub profile does not support getting page content"}`；
阅读器使用 `/manifest/epub`（`application/webpub+json`）。EPUB 的 `pagesCount=1`，
但 `/pages` 返回空数组，属正常语义。

## 2. RAR / CBR

- 镜像内 `command -v rar unrar 7z 7za` 均为空；jar 内含 `junrar-8.1.2.jar`。
- 用 Python 手工构造最小 RAR4（stored）并命名为 `.cbr`，内含 2 张 PNG。
- 结果：`READY`，`application/x-rar-compressed; version=4`，pagesCount=2；
  `/pages/1` 200 image/png 99 B；缩略图 200 image/jpeg。纯 Java RAR4 路径可用。

## 3. HEIF / JXL 封面（FAIL）

- jar 内含 `imageio-heif-1.1.0.jar`、`imageio-jxl-1.1.0.jar`，但实现只在
  `META-INF/versions/22/`；启动日志明确：
  `This plugin only supports Java 22, plugin will be disabled`（HEIF writer/reader、JXL reader 各一条）。
- 运行镜像为 JDK 21；启动时 `ImageConverter` 的可读 mediaType 列表不含 `image/jxl`、`image/heif`。
- 样本：ffmpeg/libjxl 生成 32×32 JXL；libheif `example.heic` 作为 HEIC 页。
- 扫描结果：JXL CBZ `READY` pages=2、HEIF CBZ `READY` pages=1，但 width/height 均为 null；
  原始页请求 200（仅透传 `image/jxl` / `image/heif`）；页缩略图 **500**
  `No suitable ImageReader found`；书/系列缩略图 **404**。
- 日志：`WARN ImageAnalyzer: no reader found` +
  `UnsupportedFormatException: No suitable ImageReader found for source data`。
- 容器内也没有 `libheif` / `libjxl`；即使换 JDK 22+，仍需补 loong64 原生库。

## 4. Kobo 转换（BLOCKED）

- 镜像内无 `kepubify`（`command -v` 为空，`/opt/komga` 只有 `komga.jar` 与 `native/`）。
- 启动日志：
  `WARN KepubConverter: Error while verifying executable: /usr/bin/kepubify`
  `... cannot run program "/usr/bin/kepubify": Exec failed, error: 2`
  `WARN ... kepubify path is not executable, not found or not valid: /usr/bin/kepubify`
- 用 `/api/v2/users/me/api-keys` 生成 API key 后实测：
  `GET /kobo/{key}/v1/initialization` 200；`GET /kobo/{key}/v1/library/sync` 200（返回 entitlements）；
  `GET /kobo/{key}/v1/books/{bookId}/file/epub` 200 `application/epub+zip`。
- 但下载字节与原 EPUB 完全一致（1052 B，sha256 同源文件），即未做 KEPUB 转换且无显式报错。
  结论：Kobo 同步协议可跑，KEPUB 转换不可用；要交付需补 loong64 的 kepubify 二进制。

## 5. 只读 `/data`

```bash
docker run -d --name komga-verify-ro -p 14302:25600 \
  -v komga-verify-ro-config:/config -v /tmp/komga-verify/data:/data:ro \
  yunixintel/komga:loong64
```

- 容器内 `touch /data/x` 与 `runuser -u komga -- touch /data/x` 均报
  `Read-only file system`；entrypoint 的 `chown /data` 失败被 `|| true` 吞掉，启动正常。
- 认领 + 建库 + 扫描后 7 本书全部 `READY`（CBZ/PDF/EPUB/CBR/JXL/HEIF/RO），
  CBZ `/pages/1` 200 image/png；无写入相关错误。

## 6. 认证 / 首用户

- 全新 `/config`：`GET /api/v1/claim` → `{"isClaimed":false}`；
  匿名 `GET /api/v2/users` 与 `POST /api/v1/users` 均 401。
- 初始化唯一入口是 claim，而非默认账号：
  `POST /api/v1/claim`，请求头 `X-Komga-Email` / `X-Komga-Password`，返回 200 及 ADMIN 用户
  （角色 ADMIN、FILE_DOWNLOAD、KOBO_SYNC、KOREADER_SYNC、PAGE_STREAMING、USER）。
- 再次 claim → 400 `This server has already been claimed`；之后 Basic Auth 正常，
  `GET /api/v2/users` 200。用户 API 已迁到 v2，`/api/v1/users` 返回 404。
- 商店文档应写清：首次启动无默认密码，需调用 claim 接口（Web UI 同流程）创建管理员。

## 剩余风险 / 未覆盖

- RAR5 未构造样本；junrar 8.1.2 理论上支持，但本次只实测 RAR4。
- HEIF/JXL 在 JDK 21 下确定不可用；升级 JDK 22+ 还需 loong64 的 libheif/libjxl，当前镜像无。
- Kobo KEPUB 依赖外部 kepubify（上游为 Go，需自行交叉编译 loong64）；同步本身可用。
- 样本为最小文件，未做大文件/损坏包/性能测试；EPUB 页面 500 属预期，不应误判为扫描失败。
