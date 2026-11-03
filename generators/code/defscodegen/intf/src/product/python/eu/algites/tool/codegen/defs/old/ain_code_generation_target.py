from __future__ import annotations

from enum import Enum

class AInCodeGenerationTarget(str, Enum):
    """Defines the code generation target enumeration."""
    JAVA = "java"
    PYTHON = "python"
