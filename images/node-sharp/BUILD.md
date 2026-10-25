# Node.js 24.22.1 + sharp 0.35.5 + libvips 8.18.7 (loong64) 基础镜像

## 结论

- 镜像：`yunixintel/node-sharp:24.22.1` / `:loong64`
- 大小：446MB（`docker images`），Hub 压缩后 157MB（149.5 MiB）
- digest：`sha256:b7dd366c629d363df4d8737317f8425478eb770b52c50fbca4bab332a5c49f49`
  （`:24.22.1` 与 `:loong64` 同 digest）
- 版本：Node.js 24.22.1、sharp 0.35.5、libvips 8.18.7
- 平台：`linux/loong64`，openEuler 24.03 / glibc 2.38
- 验证：`sharp.versions` 显示 libvips 8.18.7；256×256 源图
  `resize(128,128).webp()` 110 字节；`sharp('in.jpg')` 的 JPEG/PNG/WebP
  输出均非空；`ldd` 无 `not found`；`.node` 为 LoongArch ELF；
  “应用自带 sharp 包 + 只放 `.node`”的复用方式也已实跑通过。

## 用途

给 Karakeep、Linkwarden、Joplin 等依赖 sharp 的 Node 应用使用。sharp 官方
预编译包没有 `linux-loong64` 资产，普通 `npm install sharp` 在龙芯上会失败。
本镜像只在构建期编一次 libvips 与 sharp 原生插件，应用侧直接复用：

- `/opt/vips`：libvips 8.18.7 安装前缀（库、头文件、pkg-config 文件）；
- `/opt/node_modules/sharp`：可用的 sharp 0.35.5 包，含
  `src/build/Release/sharp-linux-loong64-0.35.5.node` 及其运行时依赖。

## 来源与校验

| 组件 | 版本 | URL | SHA-256 |
|---|---|---|---|
| libvips | 8.18.7 | `https://github.com/libvips/libvips/releases/download/v8.18.7/vips-8.18.7.tar.xz` | `5baaead3b0bb20ffdb9e9ff09aa9fda08620923df77b63b436654cb5e0b3bf94` |
| sharp | 0.35.5 | `https://registry.npmjs.org/sharp/-/sharp-0.35.5.tgz` | `3b6bbbe6b308f5c383938ca4a31926cd5d79c4651ed8c5fda16a97da2014a9ac` |

Dockerfile 在 `RUN` 里用 `sha256sum -c` 校验源码与 npm tarball，校验失败即终止
构建。

libvips 的 meson 配置固定为：

```text
--prefix=/opt/vips --libdir=lib
-Dauto_features=disabled -Dmodules=disabled -Dintrospection=disabled
-Dexamples=false -Ddocs=false -Dcplusplus=true
-Djpeg=enabled -Dpng=enabled -Dwebp=enabled -Dtiff=enabled
-Dexif=enabled -Dlcms=enabled -Dzlib=enabled
```

`auto_features=disabled` 会关掉所有未显式启用的可选依赖，因此最终只带
JPEG/PNG/WebP/TIFF 与 EXIF/LCMS，不引入 HEIF/JXL/PDF/SVG/ImageMagick 等。

## 构建

```bash
# 在 LoongArch64 构建机（openEuler 24.03 / Docker 26）上：
cd images/node-sharp
docker build --progress=plain -t yunixintel/node-sharp:24.22.1 .
docker tag yunixintel/node-sharp:24.22.1 yunixintel/node-sharp:loong64
```

三个阶段：

1. `libvips`：`openeuler/openeuler:24.03`，安装 meson/ninja/gcc-c++/pkgconf 与
   glib2/expat/jpeg/png/webp/tiff/lcms2/libexif/zlib 的 devel 包，下载并校验
   8.18.7 源码，`meson setup` + `ninja install` 到 `/opt/vips`。
2. `sharp`：基于 `yunixintel/node:24.22.1`，复制 `/opt/vips`，安装
   `node-addon-api@8.9.2`、`node-gyp@12.4.0`（仅构建期）与 sharp tarball；
   用
   `SHARP_FORCE_GLOBAL_LIBVIPS=1 PKG_CONFIG_PATH=/opt/vips/lib/pkgconfig LD_LIBRARY_PATH=/opt/vips/lib`
   执行 `node-gyp rebuild --directory=src`，产出
   `sharp-linux-loong64-0.35.5.node`。sharp 的运行时依赖用
   `--install-strategy=nested` 收进 `sharp/node_modules`，所以运行阶段只复制
   `/opt/node_modules/sharp` 即可。
3. 运行阶段：基于 `yunixintel/node:24.22.1`，安装
   glib2/expat/libjpeg-turbo/libpng/libwebp/libtiff/lcms2/libexif/zlib/libstdc++
   运行时库，复制 `/opt/vips` 与 `/opt/node_modules/sharp`，设置
   `NODE_PATH=/opt/node_modules`、`LD_LIBRARY_PATH=/opt/vips/lib`、
   `SHARP_FORCE_GLOBAL_LIBVIPS=1`。

构建期需要 codec 的 `-devel` 包：`vips.pc` 的 `Requires.private` 列出了
expat/libexif/libjpeg/libpng/libwebp/libtiff/lcms2，`pkg-config` 解析
`vips-cpp` 时会要求这些 `.pc` 文件存在，否则 include 路径为空，编译报
`vips/vips8: No such file or directory`。

## 在应用中复用

### 方式 A：直接把本镜像当作应用的基础镜像

```dockerfile
FROM yunixintel/node-sharp:24.22.1
# 应用代码
COPY . /app
WORKDIR /app
CMD ["node", "server.js"]
```

`NODE_PATH` 已指向 `/opt/node_modules`，应用里 `require('sharp')` 直接可用。

### 方式 B：复制 `/opt/vips` + `/opt/node_modules/sharp`

适合应用已有自己的 Node 基础镜像。运行阶段必须能解析 libvips 的依赖：

```dockerfile
FROM yunixintel/node:24.22.1

RUN dnf install -y --setopt=install_weak_deps=False \
        glib2 expat libjpeg-turbo libpng libwebp libtiff \
        lcms2 libexif zlib libstdc++ && \
    dnf clean all && rm -rf /var/cache/dnf

COPY --from=yunixintel/node-sharp:24.22.1 /opt/vips /opt/vips
COPY --from=yunixintel/node-sharp:24.22.1 /opt/node_modules/sharp /opt/node_modules/sharp

ENV NODE_PATH=/opt/node_modules \
    LD_LIBRARY_PATH=/opt/vips/lib \
    SHARP_FORCE_GLOBAL_LIBVIPS=1
```

### 方式 C：应用自己 `npm install sharp`，只借用 `.node`

如果应用的 `package-lock.json` 已经固定 sharp 0.35.5，可以让 npm 正常装
JS 部分，只把龙芯原生插件放进 sharp 包：

```dockerfile
COPY --from=yunixintel/node-sharp:24.22.1 \
     /opt/node_modules/sharp/src/build/Release/sharp-linux-loong64-0.35.5.node \
     /app/node_modules/sharp/src/build/Release/sharp-linux-loong64-0.35.5.node

COPY --from=yunixintel/node-sharp:24.22.1 /opt/vips /opt/vips
ENV LD_LIBRARY_PATH=/opt/vips/lib SHARP_FORCE_GLOBAL_LIBVIPS=1
```

sharp 的运行时加载顺序里，`../src/build/Release/sharp-<platform>-<version>.node`
优先于 `@img/sharp-*` 预编译包，所以把 `.node` 放到这个路径即可。此时
`NODE_PATH` 不必设置，Node 会从应用自己的 `node_modules/sharp` 加载。
应用自己的 sharp 包如果没装 `@img/colour`、`detect-libc`、`semver`，
npm 会作为 sharp 的依赖自动装好。

该方式已用全新 `npm install sharp@0.35.5` + 复制单个 `.node` 实跑验证。

注意：`/opt/vips` 的路径不要改。`.node` 的 `DT_NEEDED` 是
`libvips-cpp.so.42`，运行时靠 `LD_LIBRARY_PATH=/opt/vips/lib` 找到；
若改路径，需同步改 `LD_LIBRARY_PATH`。

## 测试证据

测试脚本：`images/node-sharp/test/test-sharp.cjs`。在镜像内执行：

```bash
docker run --rm yunixintel/node-sharp:24.22.1 \
  node -e "console.log(require('sharp').versions)"
```

输出：

```json
{ "vips": "8.18.7", "sharp": "0.35.5" }
```

完整测试（挂载 `test/`）：

```text
sharp.versions = {
  "vips": "8.18.7",
  "sharp": "0.35.5"
}
resize(128,128).webp() bytes = 110
sharp(in.jpg).jpeg() bytes    = 652
sharp(in.jpg).png() bytes     = 782
sharp(in.jpg).webp() bytes    = 198
in.jpg metadata = {"format":"jpeg","width":256,"height":256,"channels":3}
TEST PASS
```

动态链接与架构：

```text
ldd /opt/node_modules/sharp/src/build/Release/sharp-linux-loong64-0.35.5.node
  libvips-cpp.so.42 => /opt/vips/lib/libvips-cpp.so.42
  libvips.so.42     => /opt/vips/lib/libvips.so.42
  libjpeg.so.62 / libpng16.so.16 / libwebp.so.7 / libtiff.so.6
  liblcms2.so.2 / libexif.so.12 / libexpat.so.1 / libz.so.1 ...
not found 计数：0

file .../sharp-linux-loong64-0.35.5.node
  ELF 64-bit LSB shared object, LoongArch, version 1 (GNU/Linux),
  dynamically linked, not stripped
```

## 体积

```text
docker images yunixintel/node-sharp:24.22.1
  446MB

主要层：
  211MB   openEuler 24.03 rootfs
  200MB   /opt/node24（Node 24.22.1）
  13.1MB  运行阶段 dnf 安装的 codec 运行库
  5.8MB   /opt/vips
  1.56MB  /opt/node_modules/sharp（含 .node 与嵌套依赖）
```

Hub 压缩后 157MB（149.5 MiB，manifest 各层 size 之和 156,745,692 字节）。

## 推送结果

```text
yunixintel/node-sharp:24.22.1  sha256:b7dd366c629d363df4d8737317f8425478eb770b52c50fbca4bab332a5c49f49
yunixintel/node-sharp:loong64  sha256:b7dd366c629d363df4d8737317f8425478eb770b52c50fbca4bab332a5c49f49
architecture=loong64  os=linux
```

## 限制

- 外部编解码器只启用 JPEG、PNG、WebP（含 webpmux/webpdemux）、TIFF；
  EXIF 与 LCMS 可用。此外 libvips 内置的 GIF 输入、PPM、VIPS、Radiance、
  RAW 也可用（`sharp.format` 实测 GIF 只读、PPM/VIPS/RAD/RAW 可读写）。
- 未启用 HEIF/AVIF（libheif）、JPEG XL（libjxl）、PDF（poppler/pdfium）、
  SVG（librsvg）、ImageMagick、OpenEXR、cfitsio、FFTW。
  需要这些格式的应用必须另建 libvips，或扩展本镜像的 meson 选项。
- GIF 只能解码、不能编码（`cgif` 未启用）；未启用文字渲染
  （pangocairo/fontconfig）。
- `-Dmodules=disabled`，libvips 为静态编入的单一 `libvips.so`，没有运行时
  可插拔模块。
- 运行库来自 openEuler 24.03；如果应用换成别的发行版基础镜像，需自行保证
  glibc 2.38 及上述 codec 的 SONAME 兼容。
- 镜像包含 libvips 头文件与 `.pc` 文件（约 5.8MB），方便应用在构建期继续
  编译其它原生扩展；如只做运行可自行删减。

## 推送

Docker Hub 推送走 `crane` + 本地代理（与仓库其它镜像一致）：

```bash
docker save -o node-sharp.tar yunixintel/node-sharp:24.22.1
export HTTPS_PROXY=http://127.0.0.1:17890 HTTP_PROXY=http://127.0.0.1:17890
/build/bin/crane push node-sharp.tar yunixintel/node-sharp:24.22.1
/build/bin/crane push node-sharp.tar yunixintel/node-sharp:loong64
/build/bin/crane digest yunixintel/node-sharp:24.22.1
```
