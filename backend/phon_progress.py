import json
import os
import re


class Inflecter:
  def __init__(self):
    """初始化变形器，加载形态学规则库"""
    self.base_dir = os.path.dirname(__file__)
    self.morph_path = os.path.join(self.base_dir, 'data', 'morphology.json')
    self.rules = self._load_rules()

  def _load_rules(self):
    """从 JSON 文件加载形态学规则"""
    if not os.path.exists(self.morph_path):
      return {"noun_logic": {}, "verb_logic": {}, "infixes": {}, "tense_mood": {}}
    with open(self.morph_path, 'r', encoding='utf-8') as f:
      return json.load(f)

  def process(self, request):
    """主入口函数"""
    word_type = request.get('word_type', 'verb')
    if word_type == "noun":
      return self._process_noun(request)
    else:
      return self._process_verb(request)

  # --- 名词处理模块 (Noun Module) ---

  def _process_noun(self, request):
    stems_data = request.get('stems', [])
    grammar = request.get('grammar', {})
    target_case = grammar.get('case', 'NOM').upper()
    prep_type = grammar.get('prep_type', 'INF').upper()

    processed_stems = []
    last_stem_info = stems_data[-1]
    overall_ani = last_stem_info.get('animacy', 'inan').lower()
    first_stem_base = stems_data[0]['base']

    for i, stem_info in enumerate(stems_data):
      is_last = (i == len(stems_data) - 1)
      base = stem_info['base']
      ani = stem_info.get('animacy', 'inan').lower()

      decl_class = stem_info.get('inflection_type')
      detected_class, detected_sub = self._identify_noun_class(base)
      if not decl_class: decl_class = detected_class
      sub_type = detected_sub

      node = self.rules.get('noun_logic', {}).get(decl_class, {})

      if decl_class == "D4":
        v_grp = "iu" if re.search(r'[iu]', base) else "eo"
        rules = node.get(sub_type, {}).get(v_grp)
      elif decl_class == "D1":
        rules = node.get(ani)
      else:
        rules = node.get(sub_type, {}).get(ani)

      if not rules:
        processed_stems.append(base)
        continue

      use_abs = (is_last and target_case == "NOM")
      v_mode = "abs" if use_abs else "con"
      ending = rules.get(v_mode, "")

      current_stem = self._combine_noun_stem(base, sub_type, ending, decl_class)

      if is_last and target_case != "NOM":
        if target_case == "GEN":
          current_stem += "s"
        elif target_case == "OBL":
          current_stem += ("h" if overall_ani == "ani" else "x")

      processed_stems.append(current_stem)

    combined = "".join(processed_stems)
    result = self._apply_noun_prefix(combined, prep_type, overall_ani, first_stem_base)

    return {
      "result": self._apply_sandhi(result, "noun"),
      "analysis": processed_stems
    }

  def _apply_noun_prefix(self, word, prep, ani, original_base):
    if prep == "INF": return word
    is_vowel_init = original_base[0].lower() in 'aeiouy'

    if prep == "DEF":
      if ani == "ani":
        return ("ej-" if is_vowel_init else "e-") + word
      else:
        return ("a'-" if is_vowel_init else "a-") + word

    # ... (其他前缀逻辑保持不变)
    return word

  def _identify_noun_class(self, base):
    if base.endswith('nt'): return "D2", "nt"
    last_char = base[-1]
    if last_char in ['p', 't', 'k', 'q']: return "D2", last_char
    if last_char in ['m', 'n', 'l', 'r', 'j', 'i']:
      sub = 'j' if last_char in ['j', 'i'] else last_char
      return "D3", sub
    if last_char in ['w', 'u']: return "D3", "w"
    if last_char in ['s', 'c', 'f']: return "D4", last_char
    return "D1", None

  def _combine_noun_stem(self, base, sub_type, ending, decl_class):
    if base.endswith(('i', 'j', 'u', 'w')) and decl_class in ["D2", "D3", "D4"]:
      return base[:-1] + ending
    if decl_class == "D1":
      if base.endswith(('a', 'e', 'i', 'o', 'u', 'y')): return base[:-1] + ending
      return base + ending
    return base + ending

  # --- 动词处理模块 (Verb Module - 重构版) ---

  def _process_verb(self, request):
    stems_data = request.get('stems', [])
    grammar = request.get('grammar', {})
    processed_stems = []

    for i, stem_info in enumerate(stems_data):
      is_last = (i == len(stems_data) - 1)
      base = stem_info['base']
      inf_type = stem_info.get('inflection_type', '5-step')

      # 1. 确定 Aspect
      aspect = grammar.get('aspect', 'PFV').upper() if is_last else "INF"

      # 2. 应用中缀 (修正位置逻辑：5段支持 CCVC -> CunCVC)
      stem = self._apply_verb_infix(base, stem_info.get('infix'), inf_type)

      # 3. 应用元音交替 (Ablaut)
      stem = self._apply_verb_ablaut(stem, aspect, inf_type)
      processed_stems.append(stem)

    combined = "".join(processed_stems)

    # 4. 附加时态和语气后缀 (根据新 JSON 映射)
    mood = grammar.get('mood', 'R').upper()
    tense = grammar.get('tense', 'NF').upper()
    suffix = self._get_verb_suffix(mood, tense)

    # 5. 音系磨合 (含 V5 喷音化处理)
    return {
      "result": self._apply_sandhi(combined + suffix, "verb"),
      "analysis": {
        "stems": processed_stems,
        "suffix": suffix if suffix else "[NULL]"
      }
    }

  def _apply_verb_infix(self, stem, infix_key, inf_type):
    """
    中缀插入逻辑：
    5-step: CnCVC (复辅音中间插入)
    2-step: CV<v>CV (第一音节后插入)
    """
    if not infix_key or infix_key not in self.rules.get('infixes', {}):
      return stem
    v = self.rules['infixes'][infix_key]

    if inf_type == "5-step":
      # 如果是复辅音开头 CC... -> C<v>C...
      if re.match(r'[^aeiou]{2}', stem):
        return stem[0] + v + stem[1:]
      return stem[0] + v + stem[1:]
    else:
      # 2-step: CV <v> CV
      match = re.match(r'([^aeiou][aeiouy])', stem)
      if match:
        idx = len(match.group(1))
        return stem[:idx] + v + stem[idx:]
      return v + stem

  def _apply_verb_ablaut(self, stem, aspect, inf_type):
    logic = self.rules.get('verb_logic', {}).get(inf_type)
    if not logic: return stem

    cat, trigger = self._get_verb_category(stem, inf_type)
    if not cat: return stem

    rep = logic.get('aspect_ablaut', {}).get(aspect, {}).get(cat)
    if rep is None: return stem

    if inf_type == "5-step":
      # V5 (ʔ) 喷音保护逻辑
      if cat == "ʔ" and rep == "":
        return stem  # 保留 ʔ 供 Sandhi 处理成喷音符
      return stem.replace(trigger, rep, 1)
    else:
      return stem[:-len(trigger)] + rep

  def _get_verb_category(self, stem, inf_type):
    if inf_type == "5-step":
      # 优先级：先识别 ʔ (V5)
      mapping = {"ʔ": "ʔ", "T": "t", "K": "k", "P": "p", "Q": "q"}
      for cat, char in mapping.items():
        if char in stem: return cat, char
    else:
      if re.search(r'(yj|ie|i|j)$', stem):
        return "I", re.search(r'(yj|ie|i|j)$', stem).group()
      if re.search(r'(ow|uo|u|w)$', stem):
        return "U", re.search(r'(ow|uo|u|w)$', stem).group()
    return None, None

  def _get_verb_suffix(self, mood, tense):
    return self.rules.get('tense_mood', {}).get(tense, {}).get(mood, "")

  # --- 音系磨合 (Sandhi - 增强版) ---

  def _apply_sandhi(self, word, mode):
    if mode == "noun":
      word = word.replace("nth", "unc").replace("--", "-")
      word = re.sub(r'fs$', 'ps', word)
      word = re.sub(r'xs$', 'qss', word)
      if word.endswith("ah"): word = word[:-1]
    elif mode == "verb":
      # 1. V5 喷音化 (Ejectives)
      # 防止音段消失：tʔ -> t', jʔ -> j'
      word = word.replace("tʔ", "t'").replace("kʔ", "k'").replace("pʔ", "p'")
      word = word.replace("qʔ", "q'").replace("jʔ", "j").replace("ʔ", "")

      # 2. 条件变体 (i/j, u/w)
      # 元音间的 u/i 自动半元音化
      word = re.sub(r'(?<=[aeiou])u(?=[aeiou])', 'w', word)
      word = re.sub(r'(?<=[aeiou])i(?=[aeiou])', 'j', word)

      # 3. 双元音简化
      word = re.sub(r'([aeiou])\1', r'\1', word)

    return word


# --- 验证 ---
if __name__ == "__main__":
  engine = Inflecter()

  # 验证 1: 5-step CCVC 中缀 + V5 喷音 (IPFV)
  # ktʔap (V5) + n (un) -> kuntʔap -> kunt'ap
  v_test = {
    "word_type": "verb",
    "stems": [{"base": "ktap", "inflection_type": "5-step", "infix": "n"}],
    "grammar": {"aspect": "IPFV", "tense": "NF", "mood": "R"}
  }
  print("Verb Test (ktʔap IPFV):", engine.process(v_test)['result'])

  # 验证 2: 2-step CV 中缀 + F-R 后缀
  # pari + n (un) -> paunri + the -> paunrithe
  v_test2 = {
    "word_type": "verb",
    "stems": [{"base": "pari", "inflection_type": "2-step", "infix": "n"}],
    "grammar": {"aspect": "PFV", "tense": "F", "mood": "R"}
  }
  print("Verb Test (pari PFV Future):", engine.process(v_test2)['result'])