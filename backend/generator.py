import json
import os
import random
import re
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple


VOWELS = set("aeiouyɨ")
EXTRA_SYMBOL_LABELS = {
  "y": ["vowel", "high", "central"],
  "c": ["consonant", "fricative", "palatal"],
}


@dataclass(frozen=True)
class Phoneme:
  name: str
  labels: Tuple[str, ...]
  frequency: int


class LexiconGenerator:
  """Weighted root generator backed by data/phon_inventory.json and data/syllables.json."""

  skeleton_map = {
    "C": "consonant",
    "V": "vowel",
    "P": "stop",
    "S": "sonorant",
    "F": "fricative",
  }

  def __init__(self, data_dir: str = "data", seed: Optional[int] = None):
    self.data_dir = data_dir
    self.random = random.Random(seed)
    self.phon_inventory = self._load_json("phon_inventory.json")
    self.syllables = self._load_json("syllables.json")
    self.morphology = self._load_json("morphology.json")

    self.phonemes = self._build_phonemes()
    self.feature_map = self._build_feature_map()
    self.validator = MorphologyValidator(self.morphology, self.phonemes)

  def _load_json(self, filename: str) -> Any:
    path = os.path.join(self.data_dir, filename)
    with open(path, "r", encoding="utf-8") as f:
      return json.load(f)

  def _build_phonemes(self) -> Dict[str, Phoneme]:
    phonemes: Dict[str, Phoneme] = {}
    for item in self.phon_inventory:
      phonemes[item["name"]] = Phoneme(
        name=item["name"],
        labels=tuple(item.get("label", [])),
        frequency=int(item.get("frequency", 1)),
      )
    for name, labels in EXTRA_SYMBOL_LABELS.items():
      phonemes.setdefault(name, Phoneme(name=name, labels=tuple(labels), frequency=1))
    return phonemes

  def _build_feature_map(self) -> Dict[str, List[Tuple[str, int]]]:
    feature_map: Dict[str, List[Tuple[str, int]]] = {}
    for phoneme in self.phonemes.values():
      if phoneme.frequency <= 0:
        continue
      for label in phoneme.labels:
        feature_map.setdefault(label, []).append((phoneme.name, phoneme.frequency))
    return feature_map

  def _weighted_choice(self, options: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    weights = [max(int(option.get("frequency", 1)), 1) for option in options]
    return self.random.choices(list(options), weights=weights, k=1)[0]

  def _get_random_by_feature(self, feature: str) -> str:
    options = self.feature_map.get(feature, [])
    if not options:
      raise ValueError(f"No phonemes tagged with feature: {feature}")
    names, weights = zip(*options)
    return self.random.choices(names, weights=weights, k=1)[0]

  def _clean_word(self, word: str) -> str:
    word = re.sub(r"([aeiouyɨ])\1+", r"\1", word)
    word = word.replace("jj", "j").replace("ww", "w")
    return word

  def generate_raw_word(self, pos: Optional[str] = None) -> Tuple[str, str, str]:
    templates = [s for s in self.syllables if not pos or s.get("class") == pos]
    if not templates:
      raise ValueError(f"No syllable templates for pos={pos!r}")

    skeleton_node = self._weighted_choice(templates)
    skeleton = skeleton_node["skeletal"]
    pos_guess = skeleton_node["class"]
    pieces: List[str] = []

    for char in skeleton:
      feature = self.skeleton_map.get(char)
      pieces.append(self._get_random_by_feature(feature) if feature else char)

    return self._clean_word("".join(pieces)), pos_guess, skeleton

  def generate_one(self, pos: Optional[str] = None, max_attempts: int = 250) -> Dict[str, Any]:
    last_result: Optional[Dict[str, Any]] = None
    for attempt in range(1, max_attempts + 1):
      word, pos_guess, skeleton = self.generate_raw_word(pos)
      result = self.validator.validate(word, pos_guess)
      result["skeleton"] = skeleton
      result["attempts"] = attempt
      last_result = result
      if result["valid"]:
        return result
    raise RuntimeError(f"Could not generate a valid root after {max_attempts} attempts: {last_result}")

  def generate_batch(self, count: int = 12, pos: Optional[str] = None) -> List[Dict[str, Any]]:
    return [self.generate_one(pos=pos) for _ in range(max(1, min(count, 64)))]


class MorphologyValidator:
  """Classifies roots and reports phonotactic/morphological legality diagnostics."""

  def __init__(self, morphology_data: Dict[str, Any], phonemes: Optional[Dict[str, Phoneme]] = None):
    self.rules = morphology_data
    self.phonemes = phonemes or {}
    self.token_order = sorted(self.phonemes.keys(), key=len, reverse=True)

  def tokenize(self, word: str) -> Tuple[List[str], List[str]]:
    tokens: List[str] = []
    unknown: List[str] = []
    i = 0
    while i < len(word):
      match = next((p for p in self.token_order if word.startswith(p, i)), None)
      if match:
        tokens.append(match)
        i += len(match)
      else:
        unknown.append(word[i])
        tokens.append(word[i])
        i += 1
    return tokens, unknown

  def labels_for(self, token: str) -> Tuple[str, ...]:
    phoneme = self.phonemes.get(token)
    if phoneme:
      return phoneme.labels
    if token in VOWELS:
      return ("vowel",)
    return ()

  def validate(self, word: str, pos_guess: str = "noun") -> Dict[str, Any]:
    word = (word or "").strip()
    tokens, unknown = self.tokenize(word)
    diagnostics = self._phonotactic_diagnostics(tokens, unknown)

    if not word:
      diagnostics.append("Root is empty.")

    if pos_guess == "verb":
      result = self._verify_verb(word, tokens)
    else:
      result = self._verify_noun(word, tokens)

    result["tokens"] = tokens
    result["diagnostics"] = diagnostics
    result["score"] = self._score(result, diagnostics)
    result["valid"] = result["valid"] and not any(d.startswith("Illegal") for d in diagnostics)
    return result

  def _phonotactic_diagnostics(self, tokens: List[str], unknown: List[str]) -> List[str]:
    diagnostics: List[str] = []
    if unknown:
      diagnostics.append(f"Illegal symbol(s): {', '.join(sorted(set(unknown)))}.")

    vowel_run = 0
    consonant_run = 0
    previous = None
    for token in tokens:
      labels = self.labels_for(token)
      if "vowel" in labels:
        vowel_run += 1
        consonant_run = 0
      else:
        consonant_run += 1
        vowel_run = 0
      if vowel_run >= 3:
        diagnostics.append("Illegal vowel cluster: three adjacent vowels.")
      if consonant_run >= 4:
        diagnostics.append("Illegal consonant cluster: four adjacent consonants.")
      if previous == token:
        diagnostics.append(f"Repeated phoneme: {token}.")
      previous = token

    rare = [t for t in tokens if self.phonemes.get(t) and self.phonemes[t].frequency <= 0]
    if rare:
      diagnostics.append(f"Marked rare/disabled phoneme(s): {', '.join(sorted(set(rare)))}.")
    return diagnostics

  def _verify_verb(self, word: str, tokens: List[str]) -> Dict[str, Any]:
    if not tokens:
      return self._invalid(word, "verb", "No phonemes found.")

    last = tokens[-1]
    if last in ("i", "j"):
      return self._valid(word, "verb", "2-step", "I", "Final high-front segment triggers I ablaut.")
    if last in ("u", "w"):
      return self._valid(word, "verb", "2-step", "U", "Final high-back segment triggers U ablaut.")

    stop_to_class = {"t": "T", "k": "K", "p": "P", "q": "Q", "ʔ": "ʔ"}
    for token in reversed(tokens):
      if token in stop_to_class:
        return self._valid(word, "verb", "5-step", stop_to_class[token], "Last plain stop drives 5-step ablaut.")

    return self._invalid(word, "verb", "Verb must end in i/u/j/w or contain a plain stop p/t/k/q/ʔ.")

  def _verify_noun(self, word: str, tokens: List[str]) -> Dict[str, Any]:
    if not tokens:
      return self._invalid(word, "noun", "No phonemes found.")

    if word.endswith("nt"):
      return self._noun_with_animacy(word, "D2", "nt")

    last = tokens[-1]
    if last in ("p", "t", "k", "q"):
      return self._noun_with_animacy(word, "D2", last)

    if last in ("m", "n", "l", "r", "ɹ", "j", "w", "i", "u"):
      subtype = "r" if last == "ɹ" else "j" if last in ("j", "i") else "w" if last in ("w", "u") else last
      return self._noun_with_animacy(word, "D3", subtype)

    if last in ("s", "c", "f"):
      v_grp = "iu" if re.search(r"[iuɨ]", word) else "eo"
      return self._valid(
        word,
        "noun",
        "D4",
        last,
        f"Fricative-final noun with {v_grp} vowel group.",
        extra={"v_grp": v_grp, "animacy": "inan"},
      )

    if last in VOWELS:
      return self._valid(
        word,
        "noun",
        "D1",
        "vowel",
        "Open vowel-final noun.",
        extra={"animacy": "inan"},
      )

    return self._invalid(word, "noun", f"No noun declension accepts final segment {last!r}.")

  def _noun_with_animacy(self, word: str, declension: str, subtype: str) -> Dict[str, Any]:
    node = self.rules.get("noun_logic", {}).get(declension, {}).get(subtype, {})
    if not node:
      return self._invalid(word, "noun", f"{declension}/{subtype} is not defined in morphology.json.")
    animacy = "ani" if "ani" in node else next(iter(node.keys()))
    return self._valid(
      word,
      "noun",
      declension,
      subtype,
      f"{declension}/{subtype} declension is defined.",
      extra={"animacy": animacy},
    )

  def _valid(
    self,
    word: str,
    pos: str,
    inflection: str,
    subtype: str,
    reason: str,
    extra: Optional[Dict[str, Any]] = None,
  ) -> Dict[str, Any]:
    result = {
      "valid": True,
      "base": word,
      "pos": pos,
      "inflection": inflection,
      "subtype": subtype,
      "reason": reason,
    }
    if extra:
      result.update(extra)
    return result

  def _invalid(self, word: str, pos: str, reason: str) -> Dict[str, Any]:
    return {
      "valid": False,
      "base": word,
      "pos": pos,
      "inflection": None,
      "subtype": None,
      "reason": reason,
    }

  def _score(self, result: Dict[str, Any], diagnostics: List[str]) -> int:
    score = 100 if result.get("valid") else 45
    score -= 18 * len([d for d in diagnostics if d.startswith("Illegal")])
    score -= 7 * len([d for d in diagnostics if d.startswith("Marked") or d.startswith("Repeated")])
    return max(0, min(100, score))

  def build_inflection_request(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
    if analysis.get("pos") == "verb":
      return {
        "word_type": "verb",
        "stems": [{
          "base": analysis["base"],
          "inflection_type": analysis["inflection"],
          "infix": "n",
        }],
        "grammar": {"aspect": "PFV", "tense": "NF", "mood": "R"},
        "agreement": {"animacy_class": "plain", "spontaneity": "ACT", "polarity": "POS"},
      }

    return {
      "word_type": "noun",
      "stems": [{
        "base": analysis["base"],
        "inflection_type": analysis["inflection"],
        "animacy": analysis.get("animacy", "inan"),
      }],
      "grammar": {"case": "NOM", "prep_type": "INF"},
      "agreement": {"animacy_class": "object_inan", "spontaneity": "STA", "polarity": "POS"},
    }


def main() -> None:
  if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

  gen = LexiconGenerator(data_dir=os.path.join(os.path.dirname(__file__), "data"))
  target_count = 15
  roots = gen.generate_batch(target_count)

  print(f"{'Word':<12} | {'POS':<6} | {'Type':<8} | {'Subtype':<8} | {'Score':<5} | Metadata")
  print("-" * 86)
  for result in roots:
    metadata = {
      k: v for k, v in result.items()
      if k not in {"valid", "base", "pos", "inflection", "subtype", "tokens", "diagnostics"}
    }
    print(
      f"{result['base']:<12} | {result['pos']:<6} | {result['inflection']:<8} | "
      f"{result['subtype']:<8} | {result['score']:<5} | {metadata}"
    )
  print("-" * 86)
  print(f"Generated {target_count} valid roots.")


if __name__ == "__main__":
  main()
