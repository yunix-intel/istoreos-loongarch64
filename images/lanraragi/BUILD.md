# LANraragi 0.9.81 (loong64) 构建记录

## 结论

- 镜像：`yunixintel/lanraragi:loong64` / `:24.10-la5`
- Hub 压缩大小：约 273MB（本地镜像 738MB）
- digest：`sha256:374bd7e6c967a5090e277782329be2b5b985c6b33c46b2a1d2da13c1d565efed`
- 版本：LANraragi 0.9.81
- 验证：`/` 200、页面标题 `LANraragi`、Redis 启动、健康检查 healthy

## 构建链路

LANraragi 是 Perl 应用，依赖面很宽：

1. 在龙芯本机用 `install.pl install-back` 通过 `cpanm --local-lib`
   安装约 126 个 CPAN 模块到 `/home/koyomi/perl5`。
2. 用 `install.pl install-front` 安装前端 vendor 依赖。
3. 运行阶段基于 `openeuler/openeuler:24.03`，安装
   `perl perl-local-lib libarchive libffi openssl-libs ImageMagick redis expat zlib`，
   复制 `/home/koyomi/perl5` 与 `/home/koyomi/lanraragi`。
4. entrypoint 先启动 `redis-server`（仅本地缓存，关闭持久化），
   等 `redis-cli ping` 通，再以 UID 9001 的 `koyomi` 用户启动
   `script/launcher.pl -f script/lanraragi`。

## 遇到的问题

- **模块不在 `@INC`**：`cpanm` 装到 `local::lib` 后，启动报
  `Can't locate LANraragi/Utils/Config.pm`。必须显式设置：

  ```
  PERL5LIB=/home/koyomi/perl5/lib/perl5:/home/koyomi/perl5/lib/perl5/loongarch64-linux-thread-multi
  ```

  架构相关目录名是 `loongarch64-linux-thread-multi`，不能只设 `lib/perl5`。

- **`install.pl` 的 libarchive 检查失败**：报
  `Unsupported compile language "C"`。该检查只用于判断 libarchive 版本，
  实际链接正常；在 `install.pl` 第 137–138 行替换为
  `say("libarchive check skipped");` 后继续。

- **运行时缺 `local/lib.pm`**：镜像里补装 `perl-local-lib`。

- **测试残留 720MB `temp/`**：首次启动扫描测试数据后生成，构建镜像前删除，
  否则镜像会无故变大。

- Redis 启动时的 `overcommit_memory` 警告属正常，单机小规模使用可忽略。

## 运行

```bash
docker run -d --name lanraragi -p 3000:3000 \
  -v lanraragi-content:/home/koyomi/lanraragi/content \
  -v lanraragi-thumb:/home/koyomi/lanraragi/thumb \
  -v lanraragi-db:/home/koyomi/lanraragi/database \
  yunixintel/lanraragi:loong64
```

- 默认监听 `3000`，`LRR_NETWORK=http://*:3000`。
- 三个卷建议都持久化；`database` 里是 Redis 数据与索引。
- 默认无密码；对外暴露前在 Web UI 设置密码或置于反向代理认证之后。
- 只支持本地/挂载目录扫描；不要把它直接暴露到公网。
