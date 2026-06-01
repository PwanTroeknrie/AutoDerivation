import os

from flask import Flask, jsonify, render_template, request

from generator import LexiconGenerator
from inflecter import Inflecter

_base_dir = os.path.dirname(__file__)
app = Flask(__name__, template_folder=os.path.join(_base_dir, "..", "frontend", "templates"),
                      static_folder=os.path.join(_base_dir, "..", "frontend", "static"))
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
def index():
  return render_template("index.html")


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


if __name__ == "__main__":
  app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)
