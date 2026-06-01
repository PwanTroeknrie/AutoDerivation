import json
import os
import random
import re


class LexiconGenerator:
  def __init__(self, data_dir="data"):
    self.data_dir = data_dir
    self.phon_inventory = self._load_json("phon_inventory.json")
    self.syllables = self._load_json("syllables.json")
    self.morphology = self._load_json("morphology.json")

    # 预处理语音库：按特征标签建立加权索引
    self.feature_map = {}
    self._build_feature_map()

  def _load_json(self, filename):
    path = os.path.join(self.data_dir, filename)
    with open(path, 'r', encoding='utf-8') as f:
      return json.load(f)

  def _build_feature_map(self):
    """建立特征映射，例如 'stop': [('p', 5), ('t', 5)...]"""
    for item in self.phon_inventory:
      name = item['name']
      freq = item['frequency']
      for label in item['label']:
        if label not in self.feature_map:
          self.feature_map[label] = []
        self.feature_map[label].append((name, freq))

  def _get_random_by_feature(self, feature):
    """根据特征标签加权随机抽取音素"""
    options = self.feature_map.get(feature, [])
    if not options:
      return ""
    names, weights = zip(*options)
    return random.choices(names, weights=weights)[0]

  def generate_raw_word(self):
    """从 syllables.json 中随机选择一个骨架并填充音素"""
    # 假设 syllables.json 是一个包含骨架对象的列表
    skeleton_node = random.choice(self.syllables)
    skel_str = skeleton_node['skeletal']
    pos_guess = skeleton_node['class']

    word = ""
    # 映射骨架符号到特征标签
    mapping = {
      "C": "consonant",
      "V": "vowel",
      "P": "stop",
      "S": "sonorant",
      "F": "fricative"
    }

    for char in skel_str:
      if char in mapping:
        word += self._get_random_by_feature(mapping[char])
      else:
        # 保留骨架中硬编码的字符 (如 'y', 'i', 'u', 'q', 't')
        word += char

    # 简单的音系清理：防止元音堆积
    word = re.sub(r'([aeiouyɨo])\1+', r'\1', word)
    return word, pos_guess


class MorphologyValidator:
  def __init__(self, morphology_data):
    self.rules = morphology_data

  def validate(self, word, pos_guess):
    """根据 morphology.json 验证词根并赋予完整属性"""
    if pos_guess == "verb":
      return self._verify_verb(word)
    else:
      return self._verify_noun(word)

  def _verify_verb(self, word):
    # 1. 判定 2-step (以 i, u, j, w 结尾)
    if word.endswith(('i', 'j')):
      return {"valid": True, "pos": "verb", "inflection": "2-step", "subtype": "I", "base": word}
    if word.endswith(('u', 'w')):
      return {"valid": True, "pos": "verb", "inflection": "2-step", "subtype": "U", "base": word}

    # 2. 判定 5-step (包含塞音特征)
    mapping = {"t": "T", "k": "K", "p": "P", "q": "Q", "ʔ": "ʔ"}
    # 寻找词根中最后一个塞音作为 Ablaut 的触发器
    for char in reversed(word):
      if char in mapping:
        return {"valid": True, "pos": "verb", "inflection": "5-step", "subtype": mapping[char], "base": word}

    return {"valid": False, "reason": "No verb feature found"}

  def _verify_noun(self, word):
    # D2: 塞音或 nt 结尾
    if word.endswith(('p', 't', 'k', 'q', 'nt')):
      sub = "nt" if word.endswith("nt") else word[-1]
      allowed = self.rules["noun_logic"]["D2"].get(sub)
      if allowed:
        return {
          "valid": True, "pos": "noun", "inflection": "D2", "subtype": sub,
          "animacy": random.choice(list(allowed.keys())), "base": word
        }

    # D3: 共鸣音/流音结尾
    if word.endswith(('m', 'n', 'l', 'r', 'j', 'w')):
      sub = word[-1]
      allowed = self.rules["noun_logic"]["D3"].get(sub)
      if allowed:
        return {
          "valid": True, "pos": "noun", "inflection": "D3", "subtype": sub,
          "animacy": random.choice(list(allowed.keys())), "base": word
        }

    # D4: 擦音结尾 (处理元音和谐)
    if word.endswith(('s', 'c', 'f')):
      sub = word[-1]
      v_grp = "iu" if re.search(r'[iuɨ]', word) else "eo"
      return {
        "valid": True, "pos": "noun", "inflection": "D4", "subtype": sub,
        "v_grp": v_grp, "animacy": random.choice(["ani", "inan"]), "base": word
      }

    # D1: 默认元音结尾
    return {
      "valid": True, "pos": "noun", "inflection": "D1", "subtype": "vowel",
      "animacy": random.choice(["ani", "inan"]), "base": word
    }


def main():
  # 确保脚本在根目录运行或指定 data 路径
  gen = LexiconGenerator(data_dir="data")
  val = MorphologyValidator(gen.morphology)

  valid_lexicon = []
  target_count = 15
  attempts = 0

  print(f"{'Word':<12} | {'POS':<6} | {'Type':<8} | {'Metadata'}")
  print("-" * 60)

  while len(valid_lexicon) < target_count:
    attempts += 1
    raw_word, pos_guess = gen.generate_raw_word()
    result = val.validate(raw_word, pos_guess)

    if result["valid"]:
      valid_lexicon.append(result)
      # 简化显示 metadata
      meta = {k: v for k, v in result.items() if k not in ["valid", "base"]}
      print(f"{result['base']:<12} | {result['pos']:<6} | {result['inflection']:<8} | {meta}")

  print("-" * 60)
  print(f"Success! Generated {target_count} valid roots in {attempts} attempts.")


if __name__ == "__main__":
  main()