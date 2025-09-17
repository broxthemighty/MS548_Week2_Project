# service.py
from typing import Optional, Dict
from copy import deepcopy
from domain import EntryType, LearnflowState

class LearnflowService:
    def __init__(self, state: Optional[LearnflowState] = None):
        self._state = state or LearnflowState()

    # Commands (mutate state)
    def set_entry(self, entry_type: EntryType, text: str) -> None:
        self._state.entries[entry_type] = (text or "").strip()

    def clear(self) -> None:
        for k in self._state.entries:
            self._state.entries[k] = ""

    # Queries (read state)
    def get_entry(self, entry_type: EntryType) -> str:
        return self._state.entries[entry_type]

    def summary(self) -> Dict[str, str]:
        # Return only non-empty entries as { "Goal": "...", ... }
        return {e.value: v for e, v in self._state.entries.items() if v}

    def snapshot(self) -> LearnflowState:
        # Safe copy for testing/inspection
        return deepcopy(self._state)