import json
import os
import re
import time
import tomllib
from difflib import SequenceMatcher
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple


BASE_DIR = os.path.dirname(__file__)
DECISION_CHOICES = {"EXISTED", "DERIVED", "COMPOUND", "GENERATE"}


class EtymologyError(RuntimeError):
  pass


def _env(name: str, default: Optional[Any] = None) -> Optional[str]:
  value = os.getenv(name)
  return value if value not in (None, "") else default


def _abs_path(path: str) -> str:
  if os.path.isabs(path):
    return path
  return os.path.abspath(os.path.join(BASE_DIR, path))


def _load_config() -> Dict[str, Any]:
  config_path = os.path.join(BASE_DIR, "config.toml")
  with open(config_path, "rb") as f:
    cfg = tomllib.load(f)

  paths = cfg.get("paths", {})
  deepseek = cfg.get("deepseek", {})
  ollama = cfg.get("ollama", {})
  thresholds = cfg.get("thresholds", {})
  ai = cfg.get("ai", {})
  database = cfg.get("database", {})

  return {
    "db_path": _abs_path(_env("AUTODERIVATION_DB_PATH", paths.get("db_path", "conlang_db"))),
    "cache_path": _abs_path(_env("AUTODERIVATION_CACHE_PATH", paths.get("cache_path", "data/cache.json"))),
    "model_path": _env("AUTODERIVATION_MODEL_PATH", paths.get("model_path", "")),
    "collection_name": _env("AUTODERIVATION_COLLECTION", database.get("collection_name", "lexicon")),
    "ai_mode": (_env("AUTODERIVATION_AI_MODE", ai.get("mode", "local")) or "local").lower(),
    "deepseek": {
      "api_key": _env("DEEPSEEK_API_KEY", deepseek.get("api_key", "")),
      "base_url": _env("DEEPSEEK_BASE_URL", deepseek.get("base_url", "https://api.deepseek.com/v1")),
      "model": _env("DEEPSEEK_MODEL", deepseek.get("model", "deepseek-chat")),
      "timeout": int(_env("DEEPSEEK_TIMEOUT", str(deepseek.get("timeout", 30))) or 30),
    },
    "ollama": {
      "base_url": _env("OLLAMA_BASE_URL", ollama.get("base_url", "http://localhost:11434/api/chat")),
      "model": _env("OLLAMA_MODEL", ollama.get("model", "sorc/qwen3.5-instruct-uncensored:2b")),
      "timeout": int(_env("OLLAMA_TIMEOUT", str(ollama.get("timeout", 120))) or 120),
    },
    "thresholds": {
      "existed": float(_env("ETYMOLOGY_EXISTED_THRESHOLD", str(thresholds.get("existed", 90))) or 90),
      "derived": float(_env("ETYMOLOGY_DERIVED_THRESHOLD", str(thresholds.get("derived", 60))) or 60),
      "generate": float(_env("ETYMOLOGY_GENERATE_THRESHOLD", str(thresholds.get("generate", 30))) or 30),
    },
  }


CONFIG = _load_config()
RUNTIME_CONFIG_PATH = os.path.join(BASE_DIR, "runtime_config.json")


def _apply_runtime_config(values: Dict[str, Any]) -> None:
  ai_mode = values.get("ai_mode")
  if ai_mode in {"cloud", "local", "off"}:
    CONFIG["ai_mode"] = ai_mode

  deepseek_key = values.get("deepseek_api_key")
  if deepseek_key is not None:
    CONFIG["deepseek"]["api_key"] = str(deepseek_key)

  for src, target in [
    ("deepseek_base_url", ("deepseek", "base_url")),
    ("deepseek_model", ("deepseek", "model")),
    ("ollama_base_url", ("ollama", "base_url")),
    ("ollama_model", ("ollama", "model")),
    ("db_path", (None, "db_path")),
    ("model_path", (None, "model_path")),
  ]:
    value = values.get(src)
    if value:
      group, key = target
      if group:
        CONFIG[group][key] = str(value)
      else:
        CONFIG[key] = _abs_path(str(value)) if key == "db_path" else str(value)

  if "ollama_timeout" in values:
    CONFIG["ollama"]["timeout"] = int(values["ollama_timeout"])
  if "deepseek_timeout" in values:
    CONFIG["deepseek"]["timeout"] = int(values["deepseek_timeout"])

  _collection.cache_clear()
  _embedding_model.cache_clear()


def _load_runtime_config() -> None:
  if not os.path.exists(RUNTIME_CONFIG_PATH):
    return
  try:
    with open(RUNTIME_CONFIG_PATH, "r", encoding="utf-8") as f:
      values = json.load(f)
    if isinstance(values, dict):
      _apply_runtime_config(values)
  except Exception:
    pass


def _masked(value: Optional[str]) -> str:
  if not value:
    return ""
  if len(value) <= 8:
    return "*" * len(value)
  return f"{value[:4]}...{value[-4:]}"


def public_runtime_config() -> Dict[str, Any]:
  return {
    "ai_mode": CONFIG["ai_mode"],
    "deepseek": {
      "api_key_masked": _masked(CONFIG["deepseek"]["api_key"]),
      "base_url": CONFIG["deepseek"]["base_url"],
      "model": CONFIG["deepseek"]["model"],
      "timeout": CONFIG["deepseek"]["timeout"],
      "configured": bool(CONFIG["deepseek"]["api_key"] and not str(CONFIG["deepseek"]["api_key"]).startswith("sk-REPLACE")),
    },
    "ollama": {
      "base_url": CONFIG["ollama"]["base_url"],
      "model": CONFIG["ollama"]["model"],
      "timeout": CONFIG["ollama"]["timeout"],
    },
    "paths": {
      "db_path": CONFIG["db_path"],
      "model_path": CONFIG["model_path"],
      "cache_path": CONFIG["cache_path"],
    },
  }


def update_runtime_config(values: Dict[str, Any], persist: bool = True) -> Dict[str, Any]:
  allowed = {
    "ai_mode",
    "deepseek_api_key",
    "deepseek_base_url",
    "deepseek_model",
    "deepseek_timeout",
    "ollama_base_url",
    "ollama_model",
    "ollama_timeout",
    "db_path",
    "model_path",
  }
  clean = {key: value for key, value in values.items() if key in allowed and value not in (None, "")}
  _apply_runtime_config(clean)
  if persist:
    existing: Dict[str, Any] = {}
    if os.path.exists(RUNTIME_CONFIG_PATH):
      try:
        with open(RUNTIME_CONFIG_PATH, "r", encoding="utf-8") as f:
          existing = json.load(f)
      except Exception:
        existing = {}
    existing.update(clean)
    with open(RUNTIME_CONFIG_PATH, "w", encoding="utf-8") as f:
      json.dump(existing, f, ensure_ascii=False, indent=2)
  return public_runtime_config()


def _import_optional(module_name: str):
  try:
    return __import__(module_name)
  except Exception as exc:
    raise EtymologyError(f"Missing or unusable dependency {module_name!r}: {exc}") from exc


def _ratio(a: str, b: str) -> float:
  try:
    from rapidfuzz import fuzz
    return float(fuzz.WRatio(a, b))
  except Exception:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio() * 100


def _normalize_candidate(raw: Dict[str, Any], source: str) -> Dict[str, Any]:
  word = str(raw.get("word") or raw.get("w") or raw.get("ipa") or "")
  definition = str(raw.get("definition") or raw.get("d") or raw.get("original_def") or "")
  return {
    "w": word,
    "d": definition,
    "s": round(float(raw.get("score") or raw.get("s") or 0), 1),
    "source": source,
    "tags": raw.get("tags", []),
  }


@lru_cache(maxsize=1)
def _embedding_model():
  if not CONFIG["model_path"]:
    raise EtymologyError("AUTODERIVATION_MODEL_PATH or paths.model_path is not configured.")
  if not os.path.exists(CONFIG["model_path"]):
    raise EtymologyError(f"Embedding model path does not exist: {CONFIG['model_path']}")

  from sentence_transformers import SentenceTransformer, models

  try:
    return SentenceTransformer(CONFIG["model_path"])
  except Exception:
    transformer = models.Transformer(CONFIG["model_path"])
    pooling = models.Pooling(transformer.get_word_embedding_dimension())
    return SentenceTransformer(modules=[transformer, pooling])


class LocalEmbeddingFunction:
  def name(self) -> str:
    return "autoderivation-local"

  def __call__(self, input):
    texts = input if isinstance(input, list) else [input]
    return _embedding_model().encode(texts).tolist()

  def embed_documents(self, input):
    return self.__call__(input)

  def embed_query(self, input):
    return self.__call__(input)


@lru_cache(maxsize=1)
def _collection():
  chromadb = _import_optional("chromadb")
  client = chromadb.PersistentClient(path=CONFIG["db_path"])
  return client.get_or_create_collection(
    name=CONFIG["collection_name"],
    embedding_function=LocalEmbeddingFunction(),
  )


def _definition_text(sense: Dict[str, Any]) -> str:
  definitions = sense.get("definitions") or []
  parts = []
  for item in definitions:
    text = item.get("text") if isinstance(item, dict) else str(item)
    if text:
      parts.append(str(text))
  return " / ".join(parts)


@lru_cache(maxsize=1)
def _cache_entries() -> List[Dict[str, Any]]:
  path = CONFIG["cache_path"]
  if not os.path.exists(path):
    return []

  try:
    with open(path, "r", encoding="utf-8") as f:
      data = json.load(f)
  except Exception:
    return []

  entries: List[Dict[str, Any]] = []
  for item in data if isinstance(data, list) else []:
    word = item.get("transliteration") or item.get("word") or ""
    for sense in item.get("senses", []) or []:
      definition = _definition_text(sense)
      entries.append({
        "word": sense.get("ipa") or word,
        "definition": definition,
        "tags": sense.get("tags", []),
      })
  return entries


def fuzzy_recall(target: str, n: int = 12) -> List[Dict[str, Any]]:
  candidates = []
  for entry in _cache_entries():
    haystack = " ".join([entry.get("word", ""), entry.get("definition", ""), " ".join(entry.get("tags", []))])
    score = _ratio(target, haystack)
    if score > 0:
      candidates.append(_normalize_candidate({**entry, "score": score}, "cache"))
  return sorted(candidates, key=lambda c: c["s"], reverse=True)[:n]


def vector_recall(target: str, n: int = 12) -> List[Dict[str, Any]]:
  collection = _collection()
  result = collection.query(query_texts=[target], n_results=n)
  ids = result.get("ids") or []
  if not ids or not ids[0]:
    return []

  candidates = []
  metadatas = result.get("metadatas") or [[]]
  distances = result.get("distances") or [[]]
  for index, _ in enumerate(ids[0]):
    meta = metadatas[0][index] or {}
    dist = float(distances[0][index] or 1)
    definition = str(meta.get("original_def") or meta.get("definition") or "")
    fuzzy_score = _ratio(target, definition)
    vector_score = max(0.0, (1 - dist) * 30)
    score = (fuzzy_score * 0.7) + vector_score
    candidates.append(_normalize_candidate({
      "word": meta.get("word"),
      "definition": definition,
      "score": score,
      "tags": meta.get("tags", []),
    }, "chroma"))
  return sorted(candidates, key=lambda c: c["s"], reverse=True)


def hybrid_recall(target: str, n: int = 12, recall_mode: str = "auto") -> List[Dict[str, Any]]:
  target = target.strip()
  if not target:
    return []

  recall_mode = recall_mode.lower()
  if recall_mode not in {"auto", "vector", "cache"}:
    raise ValueError("recall_mode must be auto, vector, or cache")

  if recall_mode in {"auto", "vector"}:
    try:
      vector_candidates = vector_recall(target, n=n)
      if vector_candidates:
        return vector_candidates
    except Exception:
      if recall_mode == "vector":
        raise

  return fuzzy_recall(target, n=n)


def _decision_prompt(target: str, candidates: List[Dict[str, Any]]) -> str:
  cand_str = "; ".join([f"{c['w']}({c['d']}) score={c['s']}" for c in candidates[:8]])
  return (
    f"Target concept: {target}\n"
    f"Candidates: {cand_str}\n\n"
    "Choose exactly one decision:\n"
    "- EXISTED: a candidate is an exact semantic equivalent.\n"
    "- DERIVED: one candidate can derive the target concept.\n"
    "- COMPOUND: two candidates can compound into the target concept.\n"
    "- GENERATE: none are sufficiently related, so generate a new root.\n\n"
    "Return JSON only with fields: choice, comp, reason."
  )


def _normalize_decision(data: Dict[str, Any], source: str) -> Dict[str, Any]:
  choice = str(data.get("choice", "GENERATE")).upper()
  if choice not in DECISION_CHOICES:
    choice = "GENERATE"
  comp = data.get("comp", [])
  if isinstance(comp, str):
    comp = [comp]
  if not isinstance(comp, list):
    comp = []
  return {
    "choice": choice,
    "comp": [str(item) for item in comp],
    "reason": str(data.get("reason") or "No reason returned."),
    "source": source,
  }


def call_ai_decision(target: str, candidates: List[Dict[str, Any]], mode: Optional[str] = None) -> Dict[str, Any]:
  mode = (mode or CONFIG["ai_mode"]).lower()
  if mode == "cloud":
    return _call_deepseek(target, candidates)
  if mode == "local":
    return _call_ollama(target, candidates)
  if mode == "off":
    raise EtymologyError("AI mode is off.")
  raise EtymologyError(f"Unknown AI mode: {mode}")


def _call_deepseek(target: str, candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
  cfg = CONFIG["deepseek"]
  if not cfg["api_key"] or str(cfg["api_key"]).startswith("sk-REPLACE"):
    raise EtymologyError("DEEPSEEK_API_KEY is not configured.")

  from openai import OpenAI

  client = OpenAI(api_key=cfg["api_key"], base_url=cfg["base_url"])
  response = client.chat.completions.create(
    model=cfg["model"],
    messages=[
      {"role": "system", "content": "You are a careful conlang etymology assistant. Return JSON only."},
      {"role": "user", "content": _decision_prompt(target, candidates)},
    ],
    response_format={"type": "json_object"},
    timeout=cfg["timeout"],
  )
  content = response.choices[0].message.content or "{}"
  return _normalize_decision(json.loads(content), "deepseek")


def _call_ollama(target: str, candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
  import requests

  cfg = CONFIG["ollama"]
  schema = {
    "type": "object",
    "properties": {
      "choice": {"type": "string", "enum": sorted(DECISION_CHOICES)},
      "comp": {"type": "array", "items": {"type": "string"}},
      "reason": {"type": "string"},
    },
    "required": ["choice", "comp", "reason"],
  }
  response = requests.post(
    cfg["base_url"],
    json={
      "model": cfg["model"],
      "messages": [
        {"role": "system", "content": "Return JSON only. Do not use EXISTED for merely related concepts."},
        {"role": "user", "content": _decision_prompt(target, candidates)},
      ],
      "format": schema,
      "stream": False,
      "think": False,
      "options": {"temperature": 0, "num_predict": 512, "top_k": 1, "top_p": 0.1},
    },
    timeout=cfg["timeout"],
  )
  response.raise_for_status()
  text = response.json().get("message", {}).get("content", "")
  text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
  text = re.sub(r"^```json\s*|\s*```$", "", text, flags=re.MULTILINE).strip()
  return _normalize_decision(json.loads(text), "ollama")


def fallback_decision(candidates: List[Dict[str, Any]], reason: str = "Rule-based fallback.") -> Dict[str, Any]:
  if not candidates:
    return {"choice": "GENERATE", "comp": [], "reason": reason, "source": "fallback"}

  best = candidates[0]
  existed = CONFIG["thresholds"]["existed"]
  derived = CONFIG["thresholds"]["derived"]
  if best["s"] >= existed:
    return {
      "choice": "EXISTED",
      "comp": [best["w"]],
      "word": best["w"],
      "def": best["d"],
      "reason": f"{reason} Best candidate is above existed threshold.",
      "source": "fallback",
    }
  if best["s"] >= derived:
    return {
      "choice": "DERIVED",
      "comp": [best["w"]],
      "reason": f"{reason} Best candidate is related enough for derivation.",
      "source": "fallback",
    }
  return {"choice": "GENERATE", "comp": [], "reason": reason, "source": "fallback"}


_load_runtime_config()


def warmup_chromadb(preload_model: bool = False) -> Dict[str, Any]:
  started = time.perf_counter()
  result: Dict[str, Any] = {
    "ok": False,
    "collection": CONFIG["collection_name"],
    "db_path": CONFIG["db_path"],
    "preload_model": preload_model,
  }
  try:
    collection = _collection()
    result["count"] = collection.count()
    if preload_model:
      _embedding_model()
    result["ok"] = True
  except Exception as exc:
    result["error"] = str(exc)
  result["elapsed_ms"] = round((time.perf_counter() - started) * 1000)
  return result


def analyze_concept(target: str, n: int = 8, use_ai: bool = True, recall_mode: str = "auto") -> Dict[str, Any]:
  started = time.perf_counter()
  target = target.strip()
  if not target:
    raise ValueError("concept is required")

  warnings: List[str] = []
  try:
    candidates = hybrid_recall(target, n=n, recall_mode=recall_mode)
  except Exception as exc:
    candidates = []
    warnings.append(f"Recall failed: {exc}")

  if use_ai and candidates:
    try:
      decision = call_ai_decision(target, candidates)
    except Exception as exc:
      warnings.append(f"AI decision failed: {exc}")
      decision = fallback_decision(candidates, "AI unavailable.")
  else:
    reason = "AI disabled." if candidates else "No recall candidates."
    decision = fallback_decision(candidates, reason)

  return {
    "concept": target,
    "decision": decision,
    "candidates": candidates,
    "warnings": warnings,
    "meta": {
      "ai_mode": CONFIG["ai_mode"],
      "recall_mode": recall_mode,
      "candidate_count": len(candidates),
      "elapsed_ms": round((time.perf_counter() - started) * 1000),
    },
  }


def agent_orchestrator(target: str) -> Dict[str, Any]:
  return analyze_concept(target)["decision"]


def diagnose_environment() -> Dict[str, Any]:
  checks = {
    "python_executable": os.sys.executable,
    "db_path": CONFIG["db_path"],
    "db_exists": os.path.exists(CONFIG["db_path"]),
    "cache_path": CONFIG["cache_path"],
    "cache_exists": os.path.exists(CONFIG["cache_path"]),
    "model_path": CONFIG["model_path"],
    "model_exists": bool(CONFIG["model_path"] and os.path.exists(CONFIG["model_path"])),
    "ai_mode": CONFIG["ai_mode"],
    "deepseek_key_configured": bool(CONFIG["deepseek"]["api_key"] and not str(CONFIG["deepseek"]["api_key"]).startswith("sk-REPLACE")),
    "recommended_command": r"venv\python.exe backend\app.py",
  }
  dependencies = {}
  for name in ["chromadb", "sentence_transformers", "rapidfuzz", "openai", "requests"]:
    try:
      __import__(name)
      dependencies[name] = True
    except Exception:
      dependencies[name] = False
  checks["dependencies"] = dependencies
  checks["runtime_config"] = public_runtime_config()
  return checks


def main_loop() -> None:
  print(json.dumps(diagnose_environment(), indent=2, ensure_ascii=False))
  while True:
    try:
      concept = input("\n> ").strip()
      if not concept or concept.lower() in {"exit", "quit"}:
        break
      print(json.dumps(analyze_concept(concept), indent=2, ensure_ascii=False))
    except KeyboardInterrupt:
      break
    except Exception as exc:
      print(json.dumps({"error": str(exc)}, ensure_ascii=False))


if __name__ == "__main__":
  main_loop()
