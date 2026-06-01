import os
import json
import tomllib
import chromadb
from sentence_transformers import SentenceTransformer, models

# --- 配置区 (从 config.toml 加载) ---
def _load_config():
  config_path = os.path.join(os.path.dirname(__file__), "config.toml")
  with open(config_path, "rb") as f:
    cfg = tomllib.load(f)
  return cfg

_cfg = _load_config()
LOCAL_MODEL_PATH = _cfg["paths"]["model_path"]
CACHE_PATH = _cfg["paths"]["cache_path"]
DB_PATH = _cfg["paths"]["db_path"]
COLLECTION_NAME = _cfg["database"]["collection_name"]

# 1. 加载本地模型 (兼容模式)
print("正在加载本地模型...")
try:
  # 尝试直接加载
  static_model = SentenceTransformer(LOCAL_MODEL_PATH)
except Exception:
  # 针对目录结构不完整的手动组装
  word_embedding_model = models.Transformer(LOCAL_MODEL_PATH)
  pooling_model = models.Pooling(word_embedding_model.get_word_embedding_dimension())
  static_model = SentenceTransformer(modules=[word_embedding_model, pooling_model])


# 定义包装类以适配 ChromaDB 接口
class LocalEmbeddingFunction:
  def __init__(self, model):
    self.model = model

  def __call__(self, input):
    # 兼容旧版调用
    return self.embed_documents(input)

  def embed_documents(self, input):
    # 处理多条文本
    if isinstance(input, str):
      input = [input]
    return self.model.encode(input).tolist()

  def embed_query(self, input):
    # 处理查询文本（单条）
    if isinstance(input, str):
      input = [input]
    # 返回列表的第一个元素，因为 encode 返回的是列表的列表
    result = self.model.encode(input).tolist()
    return result


emb_fn = LocalEmbeddingFunction(static_model)

# 2. 初始化 ChromaDB
client = chromadb.PersistentClient(path=DB_PATH)

# --- 核心修复逻辑 ---
# 检查是否已存在同名集合，如果存在则删除（因为旧集合模型不匹配）
try:
  existing_col = client.get_collection(name=COLLECTION_NAME)
  print(f"检测到旧版模型集合 '{COLLECTION_NAME}'，正在清理以更换新模型...")
  client.delete_collection(name=COLLECTION_NAME)
except Exception:
  pass  # 不存在则跳过

# 创建新集合
collection = client.create_collection(
  name=COLLECTION_NAME,
  embedding_function=emb_fn,
  metadata={"hnsw:space": "cosine"}  # 使用余弦相似度
)


# 3. 数据索引函数
def load_and_index():
  if not os.path.exists(CACHE_PATH):
    print(f"错误: 找不到文件 {CACHE_PATH}")
    return

  with open(CACHE_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)

  documents, metadatas, ids = [], [], []

  for entry in data:
    word_val = entry.get("transliteration") or entry.get("word")
    word_id = str(entry.get("id"))

    if "senses" in entry:
      for idx, sense in enumerate(entry["senses"]):
        defs = [d.get("text", "").replace("定义:", "").strip() for d in sense.get("definitions", [])]
        pure_def = " ".join([d for d in defs if d])
        if not pure_def: continue

        # 存入纯粹的语义内容
        doc_content = f"{word_val}: {pure_def}"
        doc_id = f"{word_id}_{idx}"

        documents.append(doc_content)
        metadatas.append({
          "word": str(word_val),
          "tags": ", ".join(sense.get("tags", [])),
          "original_def": pure_def
        })
        ids.append(doc_id)

  if documents:
    # 使用 add 将数据存入集合
    collection.add(documents=documents, metadatas=metadatas, ids=ids)
    print(f"✅ 成功使用新模型索引 {len(documents)} 个语义项。")


# 4. Agent 逻辑
def agent_1_etymologist(target_concept):
  results = collection.query(
    query_texts=[target_concept],
    n_results=3
  )

  if not results['ids'] or not results['ids'][0]:
    return {"decision": "GENERATE_ROOT", "reason": "未找到匹配"}

  best_match = results['metadatas'][0][0]
  distance = results['distances'][0][0]

  # 语义距离阈值判定 (Cosine 距离 0.45 左右通常是派生界限)
  decision = "DERIVE" if distance < 0.45 else "GENERATE_ROOT"

  return {
    "input": target_concept,
    "decision": decision,
    "match": best_match['word'],
    "confidence": round(1 - distance, 4),
    "reason": f"匹配到 '{best_match['word']}' ({best_match['original_def']})"
  }


if __name__ == "__main__":
  load_and_index()
  print("\n--- 测试查询 ---")
  # 测试中文核心概念
  print(json.dumps(agent_1_etymologist("杀"), indent=2, ensure_ascii=False))