"""
tests/test_service.py
Author: Matt Lindborg
Course: MS548 - Advanced Programming Concepts and AI
Assignment: Week 2 (prep for Week 3)
Date: 9/17/2025

Purpose:
This file contains unit tests for the LearnflowService class.
Testing goals:
    - Verify that entries can be added and retrieved correctly.
    - Confirm that multiple entries are stored (append behavior).
    - Ensure the summary method returns only the latest entry.
    - Confirm clear() resets state.
These tests are written with unittest, which is included in Python’s
standard library and commonly used in academic + professional projects.
"""

import unittest
from domain import EntryType, LearningLog   # Domain model
from service import LearnflowService        # Business logic


class TestLearnflowService(unittest.TestCase):
    """
    Unit tests for LearnflowService.
    Each test is independent (fresh instance created).
    """

    def test_set_and_summary(self):
        """
        GIVEN: A new service instance
        WHEN: Adding Goal and Notes entries
        THEN: summary() should return latest entries for each type
              and omit types without entries.
        """
        s = LearnflowService()
        s.set_entry(EntryType.Goal, "Finish Week 1")
        s.set_entry(EntryType.Notes, "Focus on Tkinter")

        summary = s.summary()

        # Check summary contains latest values
        self.assertIn("Goal", summary)
        self.assertTrue(summary["Goal"].startswith("Goal: Finish Week 1"))
        self.assertIn("Notes", summary)
        self.assertTrue(summary["Notes"].startswith("Notes: Focus on Tkinter"))

        # Skill should not appear because nothing was logged
        self.assertNotIn("Skill", summary)

    def test_clear(self):
        """
        GIVEN: A service with at least one entry
        WHEN: clear() is called
        THEN: get_entry() should return empty string for that type.
        """
        s = LearnflowService()
        s.set_entry(EntryType.Skill, "Python")

        # Ensure something is stored before clearing
        self.assertEqual(s.get_entry(EntryType.Skill), "Python")

        # Clear all entries
        s.clear()

        # After clear, no entries should remain
        self.assertEqual(s.get_entry(EntryType.Skill), "")

    def test_multiple_entries_append(self):
        """
        GIVEN: A service
        WHEN: Multiple entries of the same type are added
        THEN: Internal history should contain all of them,
              but get_entry() and summary() should return the latest.
        """
        s = LearnflowService()
        s.set_entry(EntryType.Goal, "First Goal")
        s.set_entry(EntryType.Goal, "Second Goal")

        # Access snapshot (deep copy of state) for inspection
        history = s.snapshot().entries

        # Verify both entries are stored as LearningLog objects
        self.assertEqual(len(history[EntryType.Goal]), 2) # both entries should be stored
        self.assertEqual(history[EntryType.Goal][0].text, "First Goal")
        self.assertEqual(history[EntryType.Goal][1].text, "Second Goal")

        # get_entry should return the latest entry text
        self.assertEqual(s.get_entry(EntryType.Goal), "Second Goal")

        # summary should also show the latest entry only
        summary = s.summary()
        self.assertIn("Goal", summary)
        self.assertTrue(summary["Goal"].startswith("Goal: Second Goal"))


# Python standard entry-point for running tests directly
if __name__ == "__main__":
    unittest.main()
