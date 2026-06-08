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

构建结果会输出到 `frontend/dist/`，由 Flask 直接托管。

## 配置

所有配置集中在 `backend/config.toml`（该文件包含 API key，不进版本控制）。结构如下：

```toml
[deepseek]     # DeepSeek API 配置（api_key, base_url, model, timeout）
[ollama]       # Ollama 本地模型配置（base_url, model, timeout）
[paths]        # 模型路径、缓存路径、向量库路径
[database]     # ChromaDB 集合名
[thresholds]   # 词源决策分数阈值
[ai]           # AI 模式: "cloud" 或 "local"
```

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
