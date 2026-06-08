# AutoDerivation

## 正确启动环境

完整的 Python 虚拟环境位于 `backend/venv/`。系统 Python 可能只有 Flask，缺少 `chromadb`、`sentence-transformers`、`rapidfuzz`、`openai`。

推荐从项目根目录启动：

```powershell
backend\venv\python.exe backend\app.py
```

前端开发服务：

```powershell
cd frontend
npm.cmd run dev
```

生产构建：

```powershell
cd frontend
npm.cmd run build
```

构建结果会输出到 `frontend/static/`，由 Flask 直接托管。

## 环境变量

复制 `.env.example` 中的变量到本机环境。敏感信息不要写入 `backend/config.toml`。

常用变量：

- `DEEPSEEK_API_KEY`: DeepSeek API key
- `AUTODERIVATION_AI_MODE`: `cloud`、`local` 或 `off`
- `AUTODERIVATION_DB_PATH`: ChromaDB 路径
- `AUTODERIVATION_MODEL_PATH`: sentence-transformers 本地模型路径
- `OLLAMA_BASE_URL`: 本地 Ollama chat endpoint
- `OLLAMA_MODEL`: Ollama 模型名

## Etymologist API

健康检查：

```http
GET /api/etymology/status
```

词源分析：

```http
POST /api/etymology
Content-Type: application/json

{
  "concept": "death",
  "limit": 8,
  "use_ai": true,
  "recall_mode": "auto"
}
```

`recall_mode` 可选值：

- `auto`: 优先 Chroma 向量召回，失败后降级到缓存召回
- `vector`: 只使用 Chroma 向量召回
- `cache`: 只使用缓存模糊召回，不加载 embedding 模型
