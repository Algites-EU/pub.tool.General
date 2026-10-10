"""One generated source and its output path."""
from dataclasses import dataclass

@dataclass(frozen=True)
class AIcdGeneratedSdoSource:
    type_name: str
    relative_path: str
    source: str
