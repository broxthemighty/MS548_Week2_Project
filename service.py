"""
service.py
Author: Matt Lindborg
Course: MS548 - Advanced Programming Concepts and AI
Assignment: Week 2 (prep for Week 3)
Date: 9/17/2025

Purpose:
This file implements the "business logic" for Learnflow Base.
The GUI (ui.py) delegates actions to this service layer.
Key responsibilities:
    - Add new learning entries (Goals, Skills, Sessions, Notes).
    - Store entries as LearningLog objects (defined in domain.py).
    - Provide summaries and history views for the GUI.
    - Clear/reset all entries.
    - Stub in hooks for logfile writing (Week 3 requirement).
This keeps the GUI and data model decoupled, enabling future
expansion (OOP classes, logfile persistence, AI integration).
"""

# --- Imports ---
from typing import Optional, Dict         # Type hinting for clarity
from copy import deepcopy                 # For safe state snapshot
from domain import EntryType, LearnflowState, LearningLog  # Import domain model classes


class LearnflowService:
    """
    The LearnflowService class encapsulates all non-UI functionality.
    It operates on a LearnflowState object, which stores user data.
    """

    def __init__(self, state: Optional[LearnflowState] = None):
        """
        Constructor initializes service with an existing state,
        or creates a new empty LearnflowState if none provided.
        """
        self._state = state or LearnflowState()

    # ------------------- COMMANDS (Mutate State) -------------------

    def set_entry(self, entry_type: EntryType, text: str) -> None:
        """
        Add a new entry to the state.
        Input:
            entry_type - The category of entry (Goal, Skill, Session, Notes).
            text       - The user-provided content string.
        Behavior:
            - Creates a new LearningLog object.
            - Appends it to the list for the given entry_type.
            - Calls write_log() stub for future logfile integration.
        """
        # sanitize text (avoid storing None)
        clean_text = (text or "").strip()

        # create new log record object
        record = LearningLog(entry_type, clean_text) # create a timestamped log entry

        # append to the appropriate list in state
        self._state.entries[entry_type].append(record)

        # placeholder hook for Week 3 logfile writing
        self.write_log(record)

    def clear(self) -> None:
        """
        Reset the entire state back to empty lists.
        Useful for starting over without restarting the program.
        """
        for k in self._state.entries:
            self._state.entries[k] = []

    # ------------------- QUERIES (Read State) -------------------

    def get_entry(self, entry_type: EntryType) -> str:
        """
        Retrieve the most recent entry for a given type.
        Returns:
            - The latest entry text if available.
            - Empty string if no entries exist for this type.
        """
        if self._state.entries[entry_type]:
            return self._state.entries[entry_type][-1].text
        return ""

    def summary(self) -> Dict[str, str]:
        """
        Build a dictionary summary of the most recent entries by type.
        Returns:
            { "Goal": "Finish Week 1", "Notes": "Felt motivated", ... }
        Each value comes from the LearningLog.summary() method.
        """
        result = {}
        for e, records in self._state.entries.items():
            if records:  # only include if there is at least one record
                result[e.value] = records[-1].summary()
        return result

    def snapshot(self) -> LearnflowState:
        """
        Return a deep copy of the current LearnflowState.
        This allows the GUI to display history safely without
        risking accidental modification of the underlying data.
        """
        return deepcopy(self._state)

    # ------------------- PLACEHOLDERS (Future Features) -------------------

    def write_log(self, record: "LearningLog"):
        """
        Append a log entry to a persistent text file (learnflow.log).
        Subclass-aware:
        - GoalLog → includes Status
        - ReflectionLog → includes Mood
        - LearningLog → base summary
        """
        from domain import GoalLog, ReflectionLog

        log_file = "learnflow.log"

        # Base summary always includes entry type and text
        line = f"[{record.timestamp}] {record.entry_type.value}: {record.text}"

        # Add subclass-specific info
        if isinstance(record, GoalLog):
            line += f" (Status: {record.status})"
        elif isinstance(record, ReflectionLog):
            if record.mood:
                line += f" (Mood: {record.mood})"
        elif record.mood:  # Base LearningLog may still carry a mood
            line += f" (Mood: {record.mood})"

        # Write line to logfile
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(line + "\n")

