import os
import sys
from functools import lru_cache

# Ensure backend/ is importable regardless of CWD
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, abort, jsonify, request, send_from_directory

from generator import LexiconGenerator
from inflecter import Inflecter

_base_dir = os.path.dirname(__file__)
app = Flask(
  __name__,
  static_folder=os.path.join(_base_dir, "..", "frontend", "dist"),
  static_url_path="/static",
)
generator = LexiconGenerator(data_dir=os.path.join(_base_dir, "data"))
inflecter = Inflecter()


def sample_form(analysis):
  if not analysis.get("valid"):
    return None
  try:
    payload = generator.validator.build_inflection_request(analysis)
    return inflecter.process(payload)
  except Exception as exc:
    return {"result": None, "analysis": {"error": str(exc)}}


@app.get("/")
def serve_spa_root():
    return app.send_static_file("index.html")


@app.get("/<path:path>")
def serve_spa(path):
    # Only handles GET. Guard: 404 for API/static GETs lacking a handler.
    if path.startswith("api/") or path.startswith("static/"):
        abort(404)
    return app.send_static_file("index.html")


@app.get("/favicon.ico")
def favicon_ico():
  return app.send_static_file("favicon.ico")


@app.get("/assets/<path:path>")
def vite_assets(path):
  return send_from_directory(os.path.join(app.static_folder, "assets"), path)


@app.get("/api/options")
def options():
  return jsonify({
    "partsOfSpeech": ["noun", "verb"],
    "counts": [6, 12, 24, 36],
  })


@app.post("/api/generate")
def generate():
  data = request.get_json(silent=True) or {}
  count = int(data.get("count", 12))
  pos = data.get("pos") or None
  if pos not in (None, "noun", "verb"):
    return jsonify({"error": "pos must be noun, verb, or empty"}), 400

  roots = generator.generate_batch(count=count, pos=pos)
  for root in roots:
    root["sample"] = sample_form(root)
  return jsonify({"roots": roots})


@app.post("/api/validate")
def validate():
  data = request.get_json(silent=True) or {}
  word = str(data.get("word", "")).strip()
  pos = data.get("pos") or "noun"
  if pos not in ("noun", "verb"):
    return jsonify({"error": "pos must be noun or verb"}), 400

  analysis = generator.validator.validate(word, pos)
  analysis["sample"] = sample_form(analysis)
  return jsonify(analysis)


@lru_cache(maxsize=1)
def _load_etymology_functions():
  from etymologist import (
    analyze_concept,
    diagnose_environment,
    public_runtime_config,
    update_runtime_config,
    warmup_chromadb,
  )
  return analyze_concept, diagnose_environment, public_runtime_config, update_runtime_config, warmup_chromadb


@app.post("/api/etymology")
def etymology():
  data = request.get_json(silent=True) or {}
  concept = str(data.get("concept", "")).strip()
  if not concept:
    return jsonify({"error": "concept is required"}), 400

  try:
    analyze_concept, _, _, _, _ = _load_etymology_functions()
    limit = int(data.get("limit", 8))
    use_ai = bool(data.get("use_ai", True))
    recall_mode = str(data.get("recall_mode", "auto"))
    return jsonify(analyze_concept(
      concept,
      n=max(1, min(limit, 24)),
      use_ai=use_ai,
      recall_mode=recall_mode,
    ))
  except Exception as exc:
    return jsonify({
      "concept": concept,
      "decision": {"choice": "GENERATE", "reason": "Fallback due to etymology engine error."},
      "candidates": [],
      "warnings": [str(exc)],
      "error": str(exc),
    }), 200


@app.get("/api/etymology/status")
def etymology_status():
  try:
    _, diagnose_environment, _, _, _ = _load_etymology_functions()
    return jsonify(diagnose_environment())
  except Exception as exc:
    return jsonify({"error": str(exc)}), 200


@app.get("/api/config")
def get_config():
  try:
    _, _, public_runtime_config, _, _ = _load_etymology_functions()
    return jsonify(public_runtime_config())
  except Exception as exc:
    return jsonify({"error": str(exc)}), 200


@app.post("/api/config")
def set_config():
  data = request.get_json(silent=True) or {}
  try:
    _, _, _, update_runtime_config, _ = _load_etymology_functions()
    return jsonify(update_runtime_config(data, persist=bool(data.get("persist", True))))
  except Exception as exc:
    return jsonify({"error": str(exc)}), 400


@app.post("/api/etymology/warmup")
def warmup_etymology():
  data = request.get_json(silent=True) or {}
  try:
    _, _, _, _, warmup_chromadb = _load_etymology_functions()
    return jsonify(warmup_chromadb(preload_model=bool(data.get("preload_model", False))))
  except Exception as exc:
    return jsonify({"ok": False, "error": str(exc)}), 200


if __name__ == "__main__":
  app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)
