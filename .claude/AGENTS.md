# AutoDerivation — 人造语言自动派生系统

一个计算语言学工具，用于为构造语言 (conlang) 自动生成词根、判断词源关系并执行形态屈折变化。提供 Flask REST API 后端 + Vite/TypeScript 前端 Web 界面。

## 项目架构

```
AutoDerivation/
├── backend/                         # Python Flask 后端
│   ├── app.py                       # Flask API 入口 (端口 5000)
│   ├── config.toml                  # 全局配置 (API key, 模型路径, AI 模式)
│   ├── init.py                      # 向量数据库初始化 & 语义检索 Agent
│   ├── etymologist.py               # AI 词源决策编排器 (云端/本地 LLM)
│   ├── generator.py                 # 词根生成器 + 形态验证器
│   ├── morphologist.py              # 形态引擎 (音系 + 屈折)
│   ├── inflecter.py                 # 屈折引擎 (名词 D1-D4, 动词 2-step/5-step)
│   ├── phon_progress.py             # 音系规则应用引擎
│   ├── tests/
│   │   └── test_generator.py        # 生成器单元测试
│   └── data/                        # 静态语言数据 (JSON)
│       ├── phon_inventory.json      # 音位库 (特征、频率标签)
│       ├── syllables.json           # 音节骨架 (词性分类)
│       ├── morphology.json          # 形态学规则 (名词变格、动词变位、协议)
│       ├── phon_rules.json          # 音系规则
│       └── cache.json               # 翻译对缓存
├── frontend/                        # TypeScript + Vite 前端
│   ├── src/
│   │   ├── app.ts                   # SPA 主逻辑 (生成/验证交互)
│   │   └── styles.css               # 全局样式 (玻璃态面板, 响应式)
│   ├── templates/
│   │   └── index.html               # Jinja2 模板 (Flask 渲染入口)
│   ├── tsconfig.json                # TypeScript 配置 (ES2022, Bundler)
│   └── package.json                 # Vite dev/build 脚本
├── conlang_db/                      # ChromaDB 持久化向量库 (运行时生成)
├── AGENTS.md                        # 本文件 — 项目文档
└── .claude/
    └── CLAUDE.md                    # Claude Code 上下文 (与 AGENTS.md 同步)
```

## 启动方式

### 后端 (Flask API)

```bash
cd backend
python app.py
# 启动于 http://127.0.0.1:5000
```

### 前端开发 (Vite dev server)

```bash
cd frontend
npm run dev
# Vite 启动于 http://localhost:5173，API 请求代理到 Flask
```

### 生产模式

```bash
cd frontend && npm run build    # 输出到 frontend/static/
cd backend && python app.py     # Flask 直接 serve 编译后的静态资源
```

## API 端点

| 方法 | 路径 | 用途 |
|------|------|------|
| GET | `/` | 渲染 frontend/templates/index.html |
| GET | `/api/options` | 返回可选词性和数量列表 |
| POST | `/api/generate` | 批量生成词根 (参数: `pos`, `count`) |
| POST | `/api/validate` | 检测词根合法性 (参数: `word`, `pos`) |

## 核心数据流

```
概念输入 (如 "杀", "死亡")
  │
  ├─→ [etymologist.py] 混合召回 + LLM 决策
  │     ├─ ChromaDB 向量检索 (语义相似度)
  │     ├─ rapidfuzz 字符串模糊匹配
  │     ├─ DeepSeek (cloud) 或 Ollama (local) 结构化输出
  │     └─ 输出: EXISTED | DERIVED | COMPOUND | GENERATE
  │
  ├─→ [generator.py] 新词根生成
  │     ├─ LexiconGenerator: 从 syllables.json 选骨架 → 按特征加权随机填充音素
  │     └─ MorphologyValidator: 验证词根并分配屈折类别
  │
  └─→ [inflecter.py] 形态屈折
        ├─ 名词: D1(元音) / D2(塞音) / D3(共鸣音) / D4(擦音)
        ├─ 动词: 2-step (i/u词尾) / 5-step (塞音 Ablaut)
        ├─ 中缀、时态/语气后缀、协议后缀
        └─ Sandhi 音系磨合
```

## 模块说明

### `backend/app.py` — Flask API 服务器
- 提供 `/api/generate` (词根批量生成) 和 `/api/validate` (词根合法性检测)
- 自动对生成结果调用 inflecter.process 生成屈折样例
- 生产模式下直接 serve frontend/static/ 中的编译产物
- **运行**: `python backend/app.py`

### `backend/init.py` — 向量库初始化
- 加载本地 `paraphrase-multilingual-MiniLM-L12-v2` 模型
- 初始化 ChromaDB PersistentClient，集合名 `lexicon`
- `load_and_index()`: 从 `cache.json` 索引翻译对
- `agent_1_etymologist(concept)`: 根据语义距离阈值 (0.45) 做 DERIVE/GENERATE_ROOT 二元决策

### `backend/etymologist.py` — AI 词源编排器 (核心)
- **配置驱动**: 从 `config.toml` 读取 API key、模型路径、AI 模式
- **混合召回** `hybrid_recall()`: 向量检索 × 0.3 + Fuzzy 匹配 × 0.7 的综合打分
- **AI 决策** `call_ai_decision()`: 区分 EXISTED(等同) / DERIVED(1词派生) / COMPOUND(2词合成) / GENERATE(新造)
- **双模式**: `cloud` (DeepSeek API) / `local` (Ollama)
- **保底逻辑**: 高分关联 → DERIVED, 低分 → GENERATE
- **运行**: `python backend/etymologist.py` (交互式 REPL, 输入概念词)

### `backend/generator.py` — 词根生成与验证
- `LexiconGenerator`: 从 `syllables.json` 随机选骨架, 按特征标签加权抽取音素填充
- `MorphologyValidator`: 判断动词类型 (2-step I/U, 5-step T/K/P/Q/ʔ) 和名词变格类 (D1-D4)
- `generate_batch(count, pos)`: 批量生成 API 入口
- **运行**: `python backend/generator.py` (生成 15 个有效词根并展示)

### `backend/morphologist.py` — 形态引擎
- 封装 `PhonologyEngine` 和形态规则加载
- `generate_root(pos)`: 按词性筛选骨架生成词根
- `inflect(word, pos, feature)`: 按 morphology.json 的 rulesets 链式应用规则

### `backend/inflecter.py` — 屈折引擎 (完整版)
- **名词**: D1-D4 变格, 绝对格/构造格, GEN/OBL 标记, 有定前缀 (e-/a-)
- **动词**: 2-step/5-step 中缀插入, Ablaut 元音交替, 时态语气后缀, 协议后缀
- **Sandhi**: 喷音化 (tʔ→t'), 半元音化, 双元音简化, noun 特殊规则
- 调用方式: `engine.process(dict)` 传入 stems/grammar/agreement

### `backend/phon_progress.py` — 音系规则引擎
- `PhonologyEngine`: 底层音系变换 (与 inflecter.py 略有差异, 为旧版接口)

### `frontend/src/app.ts` — 前端 SPA
- TypeScript 编写的单页应用
- 词根生成表单 (词性 + 数量) → POST `/api/generate`
- 词根检测表单 (词根 + 词性) → POST `/api/validate`
- 结果以卡片网格展示, 点击卡片查看详细分析
- 页面加载时自动生成 12 个混合词根

## 配置文件 (`backend/config.toml`)

```toml
[deepseek]        # DeepSeek API 配置
[ollama]          # Ollama 本地模型配置
[paths]           # 模型路径、缓存路径、向量库路径
[database]        # ChromaDB 集合名
[thresholds]      # 词源决策分数阈值
[ai]              # AI 模式: "cloud" 或 "local"
```

## 依赖

### Python (backend)
```
flask
chromadb
sentence-transformers
rapidfuzz
openai          # DeepSeek API 调用
requests        # Ollama REST 调用
tomllib         # Python 3.11+ 内置
```

### Node.js (frontend)
```
typescript
vite
```

## 运行入口

| 入口 | 命令 | 用途 |
|------|------|------|
| `backend/app.py` | `python backend/app.py` | Flask API 服务器 |
| `backend/etymologist.py` | `python backend/etymologist.py` | 交互式词源决策 REPL |
| `backend/generator.py` | `python backend/generator.py` | 批量词根生成 |
| `backend/init.py` | `python backend/init.py` | 向量库重建 + 单次查询测试 |
| `frontend/` | `npm run dev` | Vite 前端开发服务器 |

## 数据文件格式要点

- **phon_inventory.json**: `[{name, label[], frequency}]` 音位列表
- **syllables.json**: `[{skeletal, class}]` 骨架 (C=辅音, V=元音, P=塞音, S=响音, F=擦音)
- **morphology.json**: 嵌套结构 — `noun_logic`, `verb_logic`, `verbal_agreement` (含 personal/humans/animacy/infixes/tense_mood)
- **cache.json**: `[{id, transliteration/word, senses[{definitions[{text}], tags[]}]}]` 翻译对

## 注意事项

- 敏感信息 (API key) 存储在 `backend/config.toml` 中, **切勿提交到版本控制**
- AI 模式通过 `config.toml` 的 `[ai].mode` 在 `cloud` 和 `local` 之间切换
- 向量模型路径指向本地缓存: `C:\Users\panjo\.cache\chroma\onnx_models\...`
- `inflecter.py` 和 `phon_progress.py` 都定义了 `Inflecter` 类但实现不同, 注意区分
- 前端 `templates/index.html` 为 Jinja2 模板 (Flask 渲染), 其中引用的 `static/app.js` 和 `static/styles.css` 由 Vite 构建生成
- `backend/tests/test_generator.py` 使用 Python unittest 框架
