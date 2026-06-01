import json
import os
import tomllib
import chromadb
import requests
import re
from sentence_transformers import SentenceTransformer, models
from rapidfuzz import fuzz
from openai import OpenAI

# --- 1. 全局配置 (从 config.toml 加载) ---

def _load_config():
  config_path = os.path.join(os.path.dirname(__file__), "config.toml")
  with open(config_path, "rb") as f:
    cfg = tomllib.load(f)
  return {
    "db_path": cfg["paths"]["db_path"],
    "model_path": cfg["paths"]["model_path"],
    "ai_mode": cfg["ai"]["mode"],
    "deepseek": {
      "api_key": cfg["deepseek"]["api_key"],
      "base_url": cfg["deepseek"]["base_url"],
      "model": cfg["deepseek"]["model"],
    },
    "ollama": {
      "base_url": cfg["ollama"]["base_url"],
      "model": cfg["ollama"]["model"],
      "timeout": cfg["ollama"]["timeout"],
    },
    "thresholds": {
      "existed": cfg["thresholds"]["existed"],
      "generate": cfg["thresholds"]["generate"],
    },
  }

CONFIG = _load_config()


class ModelManager:
  _model = None

  @classmethod
  def get_model(cls):
    if cls._model is None:
      try:
        cls._model = SentenceTransformer(CONFIG["model_path"])
      except:
        m = models.Transformer(CONFIG["model_path"])
        p = models.Pooling(m.get_word_embedding_dimension())
        cls._model = SentenceTransformer(modules=[m, p])
    return cls._model


class LocalEmbeddingFunction:
  def __init__(self): self.model = ModelManager.get_model()

  def name(self): return "Local"

  def __call__(self, input):
    return self.model.encode(input if isinstance(input, list) else [input]).tolist()

  def embed_documents(self, input): return self.__call__(input)

  def embed_query(self, input): return self.__call__(input)


# 初始化资源
EMB_FN = LocalEmbeddingFunction()
CHROMA_CLIENT = chromadb.PersistentClient(path=CONFIG["db_path"])
COLLECTION = CHROMA_CLIENT.get_or_create_collection(name="lexicon", embedding_function=EMB_FN)


# --- 2. 核心逻辑 ---

def hybrid_recall(target, n=12):
  v_res = COLLECTION.query(query_texts=[target], n_results=n)
  if not v_res['ids'] or not v_res['ids'][0]: return []
  candidates = []
  for i in range(len(v_res['ids'][0])):
    meta = v_res['metadatas'][0][i]
    dist = v_res['distances'][0][i]
    score = (fuzz.WRatio(target, meta['original_def']) * 0.7) + ((1 - dist) * 30)
    candidates.append({"w": meta['word'], "d": meta['original_def'], "s": round(score, 1)})
  return sorted(candidates, key=lambda x: x['s'], reverse=True)


def call_ai_decision(target, candidates, mode="cloud"):
  """通用 AI 调用接口"""
  cand_str = "; ".join([f"{c['w']}({c['d']})" for c in candidates])

  # 基础 Prompt：增加严格性约束
  prompt_content = (
    f"目标概念: {target}\n"
    f"候选词库: {cand_str}\n"
    f"任务决策要求:\n"
    f"1. [EXISTED]: 词库中已有【完全等同】的词，严禁滥用此项。\n"
    f"2. [DERIVED]: 可由 1 个词派生（如'死亡'派生出'死灵'）。\n"
    f"3. [COMPOUND]: 可由 2 个词合成（如'死' + '期'）。\n"
    f"4. [GENERATE]: 无关或无法直接转换，需新造词。\n"
  )

  if mode == "cloud":
    cfg = CONFIG["deepseek"]
    full_prompt = prompt_content + "\n请以 JSON 格式输出结果，包含字段: choice (枚举值), comp (列表), reason (字符串)。"

    client = OpenAI(api_key=cfg.get("api_key"), base_url=cfg["base_url"])
    response = client.chat.completions.create(
      model=cfg["model"],
      messages=[
        {"role": "system", "content": "你是一个严谨的语言构造助手。你必须严格区分‘语义相关’与‘语义相同’。"},
        {"role": "user", "content": full_prompt}
      ],
      response_format={"type": "json_object"},
      timeout=30
    )
    return json.loads(response.choices[0].message.content)

  else:
    # --- 本地 Ollama 使用 Structured Output ---
    cfg = CONFIG["ollama"]
    json_schema = {
      "type": "object",
      "properties": {
        "choice": {"type": "string", "enum": ["EXISTED", "DERIVED", "COMPOUND", "GENERATE"]},
        "comp": {"type": "array", "items": {"type": "string"}},
        "reason": {"type": "string"}
      },
      "required": ["choice", "comp", "reason"]
    }

    messages = [
      {
        "role": "system",
        "content": "You are a precise linguistic assistant. Output ONLY JSON. \n"
                   "CRITICAL: Do not use 'EXISTED' for related concepts (e.g., 'Necromancer' is NOT 'Death'). \n"
                   "Use 'DERIVED' or 'COMPOUND' for related concepts instead."
      },
      {
        "role": "user",
        "content": prompt_content + "请根据上述严谨性要求做出 JSON 决策。"
      }
    ]

    payload = {
      "model": cfg["model"],
      "messages": messages,
      "format": json_schema,
      "stream": False,
      "think": False,
      "options": {
        "temperature": 0,
        "num_predict": 512,
        "top_k": 1,
        "top_p": 0.1
      }
    }

    try:
      response = requests.post(cfg["base_url"], json=payload, timeout=cfg["timeout"])
      response.raise_for_status()

      result_json = response.json()
      result_text = result_json.get('message', {}).get('content', '')

      clean_content = re.sub(r'<think>.*?</think>', '', result_text, flags=re.DOTALL).strip()

      if clean_content.startswith("```"):
        clean_content = re.sub(r'^```json\s*|\s*```$', '', clean_content, flags=re.MULTILINE)

      return json.loads(clean_content)

    except requests.exceptions.Timeout:
      raise RuntimeError(f"Ollama 响应超时（{cfg['timeout']}s）")
    except json.JSONDecodeError as je:
      raise RuntimeError(f"LLM 输出的 JSON 格式不完整或错误: {je}\n原始输出: {result_text}")
    except Exception as e:
      raise RuntimeError(f"Ollama 调用解析失败: {e}")


def agent_orchestrator(target):
  candidates = hybrid_recall(target)
  if not candidates: return {"choice": "GENERATE", "reason": "词库空"}

  if candidates[0]['s'] >= CONFIG["thresholds"]["existed"]:
    return {"choice": "EXISTED", "word": candidates[0]['w'], "def": candidates[0]['d'], "reason": "初筛精确匹配"}

  if CONFIG["ai_mode"] == "cloud":
    try:
      return call_ai_decision(target, candidates, mode="cloud")
    except Exception as e:
      print(f"⚠️ 云端 AI 失败: {e}")

  try:
    print(f"正在通过本地模型 ({CONFIG['ollama']['model']}) 计算决策...")
    return call_ai_decision(target, candidates, mode="local")
  except Exception as e:
    print(f"⚠️ 本地 LLM 失败: {e}")

  best = candidates[0]
  if best['s'] > 60:
    return {"choice": "DERIVED", "comp": [best['w']], "reason": "保底逻辑：高分关联"}
  return {"choice": "GENERATE", "reason": "保底逻辑：低关联"}


def main_loop():
  print(f"模式: {CONFIG['ai_mode']} | 数据库: {CONFIG['db_path']}")
  while True:
    try:
      q = input("\n> ").strip()
      if not q or q.lower() in ['exit', 'quit']: break

      res = agent_orchestrator(q)
      print(json.dumps(res, indent=2, ensure_ascii=False))

    except KeyboardInterrupt:
      break
    except Exception as e:
      print(json.dumps({"error": str(e)}, ensure_ascii=False))


if __name__ == "__main__":
  main_loop()