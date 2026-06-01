import json
import os
import re


class Inflecter:
  def __init__(self):
    """初始化变形器，加载形态学规则"""
    self.base_dir = os.path.dirname(__file__)
    self.morph_path = os.path.join(self.base_dir, 'data', 'morphology.json')
    self.rules = self._load_rules()

  def _load_rules(self):
    """从 JSON 加载形态学规则"""
    if not os.path.exists(self.morph_path):
      return {
        "noun_logic": {},
        "verb_logic": {},
        "verbal_agreement": {
          "personal": {},
          "humans": {},
          "animacy": {},
          "infixes": {},
          "tense_mood": {}
        }
      }
    try:
      with open(self.morph_path, 'r', encoding='utf-8') as f:
        return json.load(f)
    except Exception:
      return {"noun_logic": {}, "verb_logic": {}, "verbal_agreement": {}}

  def process(self, request):
    """核心分发函数"""
    word_type = request.get('word_type', 'verb')
    if word_type == "noun":
      return self._process_noun(request)
    else:
      return self._process_verb(request)

  # --- 名词模块 ---

  def _process_noun(self, request):
    stems_data = request.get('stems', [])
    grammar = request.get('grammar', {})
    agreement = request.get('agreement', {})

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

      # 格位标记
      if is_last and target_case != "NOM":
        if target_case == "GEN":
          current_stem += "s"
        elif target_case == "OBL":
          current_stem += ("h" if overall_ani == "ani" else "x")

      processed_stems.append(current_stem)

    combined = "".join(processed_stems)

    # 处理一致性协议 (Agreement)
    agr_suffix = self._compute_agreement_suffix(agreement)
    combined += agr_suffix

    # 应用前缀
    result = self._apply_noun_prefix(combined, prep_type, overall_ani, first_stem_base)

    return {
      "result": self._apply_sandhi(result, "noun"),
      "analysis": {
        "stems": processed_stems,
        "agreement": agr_suffix or "[NONE]"
      }
    }

  # --- 动词模块 ---

  def _process_verb(self, request):
    stems_data = request.get('stems', [])
    grammar = request.get('grammar', {})
    agreement = request.get('agreement', {})

    processed_stems = []

    for i, stem_info in enumerate(stems_data):
      is_last = (i == len(stems_data) - 1)
      base = stem_info['base']
      inf_type = stem_info.get('inflection_type', '5-step')
      aspect = grammar.get('aspect', 'PFV').upper() if is_last else "INF"

      stem = self._apply_verb_infix(base, stem_info.get('infix'), inf_type)
      stem = self._apply_verb_ablaut(stem, aspect, inf_type)
      processed_stems.append(stem)

    combined = "".join(processed_stems)

    # 时态/语气后缀
    tm_suffix = self._get_verb_suffix(grammar.get('mood', 'R'), grammar.get('tense', 'NF'))

    # 动词协议后缀
    agr_suffix = self._compute_agreement_suffix(agreement)

    full_word = combined + tm_suffix + agr_suffix

    return {
      "result": self._apply_sandhi(full_word, "verb"),
      "analysis": {
        "stems": processed_stems,
        "tm_suffix": tm_suffix or "[NULL]",
        "agreement": agr_suffix or "[NULL]"
      }
    }

  # --- 协议计算逻辑 ---

  def _compute_agreement_suffix(self, agreement):
    """解析平行结构中的 agreement 字典并返回后缀"""
    if not agreement: return ""

    ani_class = agreement.get('animacy_class')
    if not ani_class: return ""

    # 极性容错逻辑
    pol_val = agreement.get('polarity')
    if pol_val is None or pol_val == "" or pol_val.upper() == "POS":
      polarity = "POS"
    else:
      polarity = pol_val.upper()

    # 状态缩写支持
    spon_val = agreement.get('spontaneity', 'ACT').upper()
    if spon_val == "A":
      spontaneity = "ACT"
    elif spon_val == "S":
      spontaneity = "STA"
    else:
      spontaneity = spon_val

    agreement_rules = self.rules.get('verbal_agreement', {})

    group = "animacy"
    for g in ["personal", "humans", "animacy"]:
      if ani_class in agreement_rules.get(g, {}):
        group = g
        break

    node = agreement_rules.get(group, {}).get(ani_class, {})
    if not node: return ""

    # 人类特殊逻辑
    if group == "humans":
      if polarity == "NEG":
        base_neg = node.get("NEG", "")
        if not base_neg:
          key = f"{spontaneity}_NEG"
          res = node.get(key, "")
          return "-" + res if res else ""
        suffix = "ha" if base_neg[-1] in "aeiouy" else "a"
        return "-" + base_neg + suffix

      res = node.get(spontaneity, "")
      return "-" + res if res else ""

    key = spontaneity
    if polarity == "NEG":
      key += "_NEG"

    res = node.get(key, "")
    return "-" + res if res else ""

  # --- 辅助方法 ---

  def _apply_noun_prefix(self, word, prep, ani, original_base):
    if prep == "INF": return word
    is_vowel_init = original_base[0].lower() in 'aeiouy'
    if prep == "DEF":
      if ani == "ani":
        return ("ej-" if is_vowel_init else "e-") + word
      else:
        return ("a'-" if is_vowel_init else "a-") + word
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

  def _apply_verb_infix(self, stem, infix_key, inf_type):
    """
    应用动词中缀。
    检测插入点前的字符，如果是元音，则删掉中缀开头的元音（如 'un' -> 'n'）。
    """
    infixes = self.rules.get('verbal_agreement', {}).get('infixes', {})
    if not infix_key or infix_key not in infixes:
      return stem

    v = infixes[infix_key]
    # 5-step 在第1个字母后插入 (C_V...)，2-step 在第2个字母后插入 (CV_C...)
    idx = 1 if inf_type == "5-step" else 2

    if idx >= len(stem):
      return stem

    # 逻辑：如果插入点前是元音且中缀以元音(aeiouy)开头
    # 示例: kapi (2-step idx=2) 前面是 'a'，中缀 'un' -> 'n' -> 'kanpi'
    vowels = "aeiouy"
    if stem[idx - 1].lower() in vowels and v[0].lower() in vowels:
      v = v[1:]

    return stem[:idx] + v + stem[idx:]

  def _apply_verb_ablaut(self, stem, aspect, inf_type):
    logic = self.rules.get('verb_logic', {}).get(inf_type)
    if not logic: return stem
    cat, trigger = self._get_verb_category(stem, inf_type)
    if not cat: return stem
    rep = logic.get('aspect_ablaut', {}).get(aspect, {}).get(cat)
    if rep is None: return stem
    return stem.replace(trigger, rep, 1) if inf_type == "5-step" else (stem[:-len(trigger)] + rep)

  def _get_verb_category(self, stem, inf_type):
    if inf_type == "5-step":
      mapping = {"T": "t", "K": "k", "P": "p", "Q": "q", "ʔ": "ʔ"}
      for cat, char in mapping.items():
        if char in stem[1:3]: return cat, char
    else:
      if re.search(r'(yj|ie|i|j)$', stem): return "I", (re.search(r'(yj|ie|i|j)$', stem).group())
      if re.search(r'(ow|uo|u|w)$', stem): return "U", (re.search(r'(ow|uo|u|w)$', stem).group())
    return None, None

  def _get_verb_suffix(self, mood, tense):
    tm_rules = self.rules.get('verbal_agreement', {}).get('tense_mood', {})
    t_key = "F" if tense == "F" else "NF"
    return tm_rules.get(t_key, {}).get(mood, "")

  def _apply_sandhi(self, word, mode):
    if mode == "noun":
      word = word.replace("nth", "unc").replace("--", "-")
      word = re.sub(r'fs$', 'ps', word)
      if word.endswith("ah"): word = word[:-1]
    word = word.replace("tʔ", "t'").replace("kʔ", "k'").replace("pʔ", "p'").replace("qʔ", "q'").replace("ʔ", "'")
    word = re.sub(r'(?<=[aeiou])u(?=[aeiou])', 'w', word)
    word = re.sub(r'(?<=[aeiou])i(?=[aeiou])', 'j', word)
    word = word.replace("--", "-")
    word = re.sub(r'([aeiouy])\1', r'\1', word)
    return word


# --- 测试 ---
if __name__ == "__main__":
  # 为了演示，手动模拟 rules 加载
  engine = Inflecter()

  # 情况 A: kapi (2-step) -> 前面有 a -> 应为 kanpi
  test_kapi = {
    "word_type": "verb",
    "stems": [{"base": "kapi", "inflection_type": "2-step", "infix": "n"}],
    "grammar": {"aspect": "PFV", "tense": "NF", "mood": "R"},
    "agreement": {"animacy_class": "none"}
  }

  # 情况 B: ktap (5-step) -> 前面是 k -> 应为 kuntap
  test_ktap = {
    "word_type": "verb",
    "stems": [{"base": "ktap", "inflection_type": "5-step", "infix": "n"}],
    "grammar": {"aspect": "PFV", "tense": "F", "mood": "HORT"},
    "agreement": {"animacy_class": "plain","spontaneity":"S","polarity":"NEG" },
  }

  print(f"kapi + 'un' -> {engine.process(test_ktap)['result']}")


  compound_test = {
    "word_type": "noun",
    "stems": [
      {"base": "umi", "inflection_type": "D3", "animacy": "inan"},  # Water
      {"base": "khrwe", "inflection_type": "D3", "animacy": "ani"}  # Flower
    ],
    "grammar": {"case": "NOM", "prep_type": "DEF"},
    "agreement": {"animacy_class": "plain", "spontaneity": "S", "polarity": "NEG"}
  }
  # Expected: e-umjkhrwe (not a-umjkhrwe)
  print("Compound Animacy Test (DEF):", engine.process(compound_test)['result'])