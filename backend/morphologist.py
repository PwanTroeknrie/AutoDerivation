import json
import os
from phon_progress import PhonologyEngine


class MorphologyEngine:
  def __init__(self, data_path=None):
    if data_path is None:
      data_path = os.path.join(os.path.dirname(__file__), "data")
    self.data_path = data_path

    # 1. 加载音位与特征 (phon_inventory.json)
    self.inventory = self._load_json("phon_inventory.json")
    # 将音位列表转换为 PhonologyEngine 所需的矩阵格式
    self.feature_matrix = {p['name']: {f: v for f, v in p.items() if f not in ['name', 'label', 'frequency']}
                           for p in self.inventory}

    # 2. 加载音节骨架 (syllables.json)
    self.syllables = self._load_json("syllables.json")

    # 3. 加载变格/变位矩阵 (morphology.json)
    self.morphology = self._load_json("morphology.json")

    # 4. 初始化音系处理器 (复用之前的重构代码)
    self.processor = PhonologyEngine(self.feature_matrix)

  def _load_json(self, filename):
    path = os.path.join(self.data_path, filename)
    with open(path, 'r', encoding='utf-8') as f:
      return json.load(f)

  def generate_root(self, pos="noun"):
    """
    利用 syllables.json 和 phon_inventory.json 生成词根
    """
    import random
    # 筛选对应词性的骨架
    templates = [s for s in self.syllables if s['class'] == pos]
    template = random.choice(templates)['skeletal']

    # 简单的填充逻辑
    root = ""
    for char in template:
      if char == 'C':
        root += random.choice([p['name'] for p in self.inventory if 'consonant' in p['label']])
      elif char == 'V':
        root += random.choice([p['name'] for p in self.inventory if 'vowel' in p['label']])
    return root

  def inflect(self, word, pos, feature):
    """
    根据 morphology.json 执行形态变换
    """
    rulesets = self.morphology.get("rulesets", {}).get(pos, {}).get(feature, [])
    current_form = word
    for group in rulesets:
      for rule in group.get("rules", []):
        current_form = self.processor.apply_rule(current_form, rule)
    return current_form
