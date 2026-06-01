import os
import unittest

from generator import LexiconGenerator, MorphologyValidator


class GeneratorTests(unittest.TestCase):
  @classmethod
  def setUpClass(cls):
    cls.generator = LexiconGenerator(data_dir=os.path.join(os.path.dirname(__file__), "..", "data"), seed=7)
    cls.validator: MorphologyValidator = cls.generator.validator

  def test_generates_requested_count(self):
    roots = self.generator.generate_batch(count=4, pos="verb")
    self.assertEqual(len(roots), 4)
    self.assertTrue(all(root["valid"] for root in roots))
    self.assertTrue(all(root["pos"] == "verb" for root in roots))

  def test_classifies_two_step_verb(self):
    result = self.validator.validate("kapi", "verb")
    self.assertTrue(result["valid"])
    self.assertEqual(result["inflection"], "2-step")
    self.assertEqual(result["subtype"], "I")

  def test_rejects_unknown_symbols(self):
    result = self.validator.validate("ka#", "noun")
    self.assertFalse(result["valid"])
    self.assertTrue(any("Illegal symbol" in item for item in result["diagnostics"]))


if __name__ == "__main__":
  unittest.main()
