# domain.py
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict

class EntryType(str, Enum):
    Goal = "Goal"
    Skill = "Skill"
    Session = "Session"
    Notes = "Notes"

@dataclass
class LearnflowState:
    entries: Dict[EntryType, str] = field(
        default_factory=lambda: {e: "" for e in EntryType}
    )
