# tests/test_service.py
import unittest
from domain import EntryType
from service import LearnflowService

class TestLearnflowService(unittest.TestCase):
    def test_set_and_summary(self):
        s = LearnflowService()
        s.set_entry(EntryType.Goal, "Finish Week 1")
        s.set_entry(EntryType.Notes, "Focus on Tkinter")
        summary = s.summary()
        self.assertEqual(summary["Goal"], "Finish Week 1")
        self.assertEqual(summary["Notes"], "Focus on Tkinter")
        self.assertNotIn("Skill", summary)

    def test_clear(self):
        s = LearnflowService()
        s.set_entry(EntryType.Skill, "Python")
        s.clear()
        self.assertEqual(s.get_entry(EntryType.Skill), "")

if __name__ == "__main__":
    unittest.main()
