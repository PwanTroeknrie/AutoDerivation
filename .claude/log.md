# AutoDerivation 开发日志

## 2026-06-01 — 项目文档初始化

- 创建 `.claude/CLAUDE.md` 记录完整项目架构与数据流
- 创建 `.claude/log.md` 本文件

## 当前状态

### 已完成
- [x] 向量数据库集成 (ChromaDB + MiniLM)
- [x] 语义检索 + 模糊匹配的混合召回
- [x] AI 词源决策 (DeepSeek 云端 / Ollama 本地, 结构化 JSON 输出)
- [x] 词根自动生成 (音节骨架 + 特征加权)
- [x] 名词屈折系统 (D1/D2/D3/D4 + 格/有定性)
- [x] 动词屈折系统 (2-step/5-step + 中缀 + Ablaut + 时态语气)
- [x] 音系磨合 Sandhi 规则

### 待完善
- [ ] 两个 `Inflecter` 类合并 (inflecter.py vs phon_progress.py 重复定义)
- [ ] API key 应从环境变量读取 (当前硬编码在 etymologist.py)
- [ ] 模型路径应可配置化 (当前硬编码 Windows 绝对路径)
- [ ] 缺少 `requirements.txt`
- [ ] 缺少单元测试
- [ ] morphologist.py 的 inflect() 方法仅作为包装, 实际屈折逻辑在 inflecter.py

### 已知问题
- inflecter.py 和 phon_progress.py 各自定义了 Inflecter 类, 接口和实现略有差异
- etymologist.py 的 `ai_mode` 默认为 "local", 如果 Ollama 未运行会 fallback 到保底逻辑
- cache.json 的数据来源不明确 (似乎是外部翻译对导入)
