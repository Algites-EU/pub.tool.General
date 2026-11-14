"""Structured Codegen diagnostics shared by independent Defs and SDO CLIs."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AInCodegenDiagnosticSeverity(str, Enum):
    """Ordered diagnostic severity; only ERROR makes an input invalid."""

    DEBUG = 'DEBUG'
    INFO = 'INFO'
    WARNING = 'WARNING'
    ERROR = 'ERROR'


@dataclass(frozen=True, slots=True)
class AIcdCodegenDiagnostic:
    """One source-located diagnostic, independent of display formatting.

    Args:
        severity: Ordered severity to use for grouping and presentation.
        message: Nonempty human-readable explanation.
        hint: Optional corrective advice; mandatory for validation errors.
        source: Exact source file/identifier, if known.
        location: Field, JSON Pointer, XPath or CLI option, if known.
    """

    severity: AInCodegenDiagnosticSeverity
    message: str
    hint: str | None = None
    source: str | None = None
    location: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.severity, AInCodegenDiagnosticSeverity):
            raise TypeError('Diagnostic severity must be an AInCodegenDiagnosticSeverity')
        if not self.message or not self.message.strip():
            raise ValueError('Diagnostic message must not be blank')
        if self.severity is AInCodegenDiagnosticSeverity.ERROR and (
                self.hint is None or not self.hint.strip()):
            raise ValueError('Error diagnostics require an actionable hint')
