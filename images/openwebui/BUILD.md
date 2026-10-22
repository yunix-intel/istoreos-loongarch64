# openwebui (loong64) 构建记录

## 结论

- 镜像：`yunixintel/openwebui:loong64` / `:24.10-la5`
- 大小：1.8GB，架构 `linux/loong64`
- 验证：200，`/api/config` 200
- 说明：v0.12.3 **轻量模式**：无 torch/onnxruntime/whisper/OCR，聊天对接 Ollama/OpenAI 正常；本地 RAG 需外部 pgvector

## 构建

构建入口：[Dockerfile](Dockerfile)

```bash
docker build -t openwebui:loong64 .
docker tag openwebui:loong64 yunixintel/openwebui:loong64
docker tag openwebui:loong64 yunixintel/openwebui:24.10-la5
docker push yunixintel/openwebui:loong64
docker push yunixintel/openwebui:24.10-la5
```

- 基础镜像：`openeuler/openeuler:24.03`
- 暴露端口：`8080`
- 卷：`["/app/backend/data"]`
- 默认环境：`TZ=UTC \ ; PATH=/opt/venv/bin:$PATH`
- 启动：`["open-webui", "serve", "--host", "0.0.0.0", "--port", "8080"]`

Dockerfile 的上下文依赖：

- `COPY open_webui-0.12.3-py3-none-any.whl /tmp/open_webui.whl`
- `COPY requirements-lite.txt /tmp/requirements-lite.txt`
- `COPY maturin-1.15.0.whl /tmp/maturin.whl`

上游版本、工具链和特殊补丁见 [../IMAGE-BUILD.md](../../docs/IMAGE-BUILD.md) 与 [../BUILDLOG.md](../../docs/BUILDLOG.md)。

## 运行

端口/挂载：`8080`；详细启动参数见 [RUNBOOK.md](../../docs/RUNBOOK.md) 的端口索引。

## 注意

v0.12.3 **轻量模式**：无 torch/onnxruntime/whisper/OCR，聊天对接 Ollama/OpenAI 正常；本地 RAG 需外部 pgvector

## 验证

```bash
docker inspect yunixintel/openwebui:loong64 --format "{{.Architecture}} {{.Os}}"
docker run --rm yunixintel/openwebui:loong64 --help 2>/dev/null || true
```
