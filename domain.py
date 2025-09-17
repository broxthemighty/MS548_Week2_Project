"""
domain.py
Author: Matt Lindborg
Course: MS548 - Advanced Programming Concepts and AI
Assignment: Week 2 (prep for Week 3)
Date: 9/17/2025

Purpose:
This file defines the core domain model for the Learnflow Base application.
It contains the enumerations and data structures used to represent user
learning activity. In Week 2, this is enhanced to prepare for Week 3 by:
    - Introducing a LearningLog class (objects instead of raw strings).
    - Storing multiple entries per type (lists of logs).
    - Adding timestamp + optional mood fields for future analysis.
This separation allows the GUI (ui.py) and business logic (service.py)
to evolve independently while still sharing a consistent data model.
"""

# import dataclass to simplify object creation (auto-generates __init__, __repr__, etc.)
from dataclasses import dataclass, field

# import Enum to define fixed categories of entries
from enum import Enum

# import typing helpers for type annotations
from typing import Dict, List

# import datetime so we can automatically timestamp log entries
from datetime import datetime


class EntryType(str, Enum):
    """
    Enumeration of supported entry types.
    Each entry represents a category of user activity.
    Stored as strings for readability in save/load and GUI.
    """
    Goal = "Goal"       # Represents a learning goal (e.g., "Finish Python project")
    Skill = "Skill"     # Represents a tracked skill or topic (e.g., "Machine Learning")
    Session = "Session" # Represents a daily learning session (e.g., "Studied 2 hours")
    Notes = "Notes"     # Represents reflections or freeform notes (e.g., "Got stuck debugging")


@dataclass
class LearningLog:
    """
    Base log entry class for all types of learning records.
    Each log is timestamped, stores user text, and may include mood.
    This class will later serve as the parent for derived classes
    (Week 3 requirement: GoalLog, ReflectionLog, etc.).
    """
    entry_type: EntryType   # Which type of entry this belongs to
    text: str               # The actual content the user entered
    timestamp: str = field(
        default_factory=lambda: datetime.now().isoformat(timespec="seconds")
    )                       # When the entry was created, default = now
    mood: str = ""          # Optional mood (primarily for Notes entries)

    def summary(self) -> str:
        """
        Return a one-line summary for display in GUI or logs.
        Example: "Notes: Felt stuck [Mood: frustrated]"
        """
        mood_str = f" [Mood: {self.mood}]" if self.mood else ""
        return f"{self.entry_type.value}: {self.text}{mood_str}"


@dataclass
class LearnflowState:
    """
    The overall state of the application.
    Stores lists of LearningLog objects for each EntryType.
    This makes it easy to:
      - Append new logs (instead of overwriting).
      - Retrieve full history later (for CSV export, history viewer).
      - Support OOP enhancements in Week 3 with derived classes.
    """
    entries: Dict[EntryType, List[LearningLog]] = field(
        default_factory=lambda: {e: [] for e in EntryType}
    )
