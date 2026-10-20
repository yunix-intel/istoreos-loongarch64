# 公开前隐私审计清单

仓库当前为 **PRIVATE**。在改回 PUBLIC 之前，必须完成以下检查并留下结论。

## 1. 工作区扫描

```bash
git grep -nIE \
  '(password|passwd|token|secret|api[_-]?key|BEGIN (RSA|OPENSSH|EC) PRIVATE KEY)' \
  -- . ':!docs/PRODUCTION-TEST.md' || true

git grep -nIE \
  '([0-9]{1,3}\.){3}[0-9]{1,3}|[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}' \
  -- . || true

git grep -nIE '(/home/[a-z]+|/root/|/build/|192\.168\.|172\.16\.|10\.[0-9]+\.)' -- . || true
```

逐条判断：文档里的示例占位符可以保留；真实密码、UUID、节点地址、私网 IP、token、SSH 路径必须删除或替换。

## 2. Git 历史扫描

工作区干净不代表历史干净。至少检查：

```bash
git log --all --oneline --decorate
git grep -nIE 'password|token|secret|10\.1\.33\.|<test-password>|Paperclip' $(git rev-list --all) -- . 2>/dev/null | head
git log -p --all -- docs/ | grep -nIE 'password|token|secret' | head
```

如历史中已有敏感值：
- 不要只在新提交里删除；用 `git filter-repo` 重写历史，或
- 删除并重建仓库（私有库可接受），或
- 保持仓库私有，直到历史清理完成。

## 3. 二进制 / 大文件

- `git ls-files | xargs -I{} du -h {} | sort -h | tail`
- 确认没有 Docker Hub token、SSH key、private key、私人固件镜像、真实 mihomo/easytier 配置。
- `release-*/` 中的固件/feed 若含私人预置，公开前必须替换为公版。
- 图片/日志中的二维码、token、IP 也要检查。

## 4. 文档链接与 Hub

- Docker Hub 60 个仓库描述指向 GitHub；仓库私有期间链接不可访问，
  公开后再保留；若长期私有，应把 Hub 描述改为不含链接的版本。
- 确认 README 没有指向私有库的敏感路径（可以指向私有库名称，但不能带 token）。

## 5. 第三方/许可证

- 应用镜像只分发可再分发的上游产物；商业/闭源组件（如 Edge）不打包。
- 保留上游 LICENSE/NOTICE；CasaOS/Pi-hole 等商标使用遵守上游政策。

## 6. 结论模板

```
审计日期：
审计人：
工作区扫描：通过 / 发现 N 项（已处理）
历史扫描：通过 / 发现 N 项（已处理/决定重建）
大文件：通过 / 列表
Hub 链接：可公开 / 暂不公开
结论：可以转 PUBLIC / 继续保持 PRIVATE
备注：
```

未完成本清单前，不要执行 `gh repo edit ... --visibility public`。

## 2026-10-20 审计结果

- 提交数：118。
- 工作区：`10.1.33.*` 0 处；私钥/token/gho_ 0 处；`<test-password>` 仅出现在本文件的扫描示例中。
- **git 历史**：`10.1.33.*` 出现在 59 个提交（`docs/BUILDLOG.md`）；`<test-password>` 出现在 3 个提交。
- 结论：**继续保持 PRIVATE**。直接转公开会把私人网段和测试密码带进历史。
- 可选清理路径：
  1. `git filter-repo --replace-text replacements.txt` 重写全部历史，再 force-push（需明确授权）。
  2. 用当前干净工作区建一个**全新仓库**（保留旧私有库作历史归档）。
  3. 删除并重建仓库。
- Docker Hub 描述目前指向本仓库；私有期间链接不可访问。若长期私有，应改为无链接描述。
