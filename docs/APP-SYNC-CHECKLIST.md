# 应用同步清单（强制）

每个新增/更新的应用镜像必须完成以下全部项目。只推镜像不写文档视为未完成。

## A. 构建材料

- [ ] 上游版本/tag 写清楚（源码、release、commit）。
- [ ] Dockerfile 放入 `images/<app>/Dockerfile`；构建上下文依赖写在同一目录的 README 或
      [IMAGE-BUILD.md](IMAGE-BUILD.md)。
- [ ] 若无法保留 Dockerfile，必须给出可复现步骤：基础镜像、工具链、编译命令、补丁、
      前端构建方式、产物复制路径。
- [ ] 特殊补丁独立成文件（`patches/` 或 `images/<app>/patches/`），不要只写在聊天里。
- [ ] 不提交大源码/前端产物；写清从哪个 tag 获取。

## B. 启动手册

- [ ] 在 [RUNBOOK.md](RUNBOOK.md) 增加：镜像名、容器内端口、宿主端口、必需挂载、
      环境变量、健康检查 URL、首次启动注意事项。
- [ ] 明确 `--network=host` vs bridge，是否需要 `--privileged` / docker.sock。
- [ ] 明确持久化目录，禁止把数据只放容器可写层。
- [ ] 给出最小 `docker run` 命令。
- [ ] 写明已知限制（例如无 shell、需要外部 PostgreSQL、浏览器步骤限制）。

## C. 问题记录

- [ ] 新踩的坑写入 [TROUBLESHOOTING.md](TROUBLESHOOTING.md)，格式：
      现象 / 原因 / 修复命令。
- [ ] 同日构建过程写入 [BUILDLOG.md](BUILDLOG.md)，包括失败的尝试和最终方案。
- [ ] 可复用脚本放 `scripts/`（构建、推送、校验），不要只留在构建机。

## D. 清单与索引

- [ ] [IMAGES.md](IMAGES.md) 增加/更新一行：大小、验证结论、端口、限制。
- [ ] `images/catalog.json` 同步（76 只时必须仍是 76 行）。
- [ ] [README.md](../README.md) 的镜像计数更新。
- [ ] 如状态变化，更新 [ROADMAP.md](ROADMAP.md) / [GAPS.md](GAPS.md)。

## E. 发布与校验

```bash
# 双 tag
docker tag <app>:loong64 yunixintel/<app>:loong64
docker tag <app>:loong64 yunixintel/<app>:24.10-la5
docker push yunixintel/<app>:loong64
docker push yunixintel/<app>:24.10-la5

# 架构/标签校验
./scripts/verify-hub-images.sh

# 本地启动校验
docker inspect <app>:loong64 --format '{{.Architecture}} {{.Os}}'
docker logs -f <container>
curl -fsS http://127.0.0.1:<port>/<health>
```

- [ ] Docker Hub 两个 tag 均存在，`architecture=loong64`。
- [ ] Docker Hub 仓库描述指向公开文档（GitHub `docs/IMAGES.md` / `docs/RUNBOOK.md`）。
- [ ] 记录 digest、镜像大小、验证命令和输出摘要。

## F. 文档提交

- [ ] `git status` 确认没有把密钥、真实配置、构建机路径写入公开库。
- [ ] 提交信息写清“新增/修复 + 应用名 + 验证结论”。
- [ ] push 到 `yunix-intel/istoreos-loongarch64`。
- [ ] 私有材料（真实配置/私人包）只推 `yunix-intel/istore-la-private`。

## G. 完成定义

同时满足以下条件才算完成：

1. 镜像已推送且 Hub 校验通过。
2. 别人只读公开仓库，能按文档从上游源码重建出同架构镜像。
3. 启动命令、端口、挂载、健康检查和已知限制都有记录。
4. 新问题在 TROUBLESHOOTING/BUILDLOG 可检索到。
