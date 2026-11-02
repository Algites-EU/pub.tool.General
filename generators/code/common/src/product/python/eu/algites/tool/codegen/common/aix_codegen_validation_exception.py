"""Shared, actionable validation failures for Python Defs and SDO Codegen."""
from __future__ import annotations


class AIxCodegenValidationException(ValueError):
    """Expected invalid configuration or input with a separate corrective hint.

    ``str(exception)`` is exactly the original validation message, so existing
    callers catching ``ValueError`` remain compatible. The hint is explicitly
    supplied by the failing validator, not inferred from the message. A source
    and location may additionally identify the declaration that failed.

    Args:
        message: Original validation message, unaltered.
        hint: Specific action the user can take to correct the issue.
        source: Optional file or artifact identifier.
        location: Optional JSON Pointer, XPath, field, or CLI option.
    """

    def __init__(self, message: str, hint: str, *, source: str | None = None,
                 location: str | None = None) -> None:
        if not hint or not hint.strip():
            raise ValueError('Validation hint must not be blank')
        super().__init__(message)
        self.message = message
        self.hint = hint
        self.source = source
        self.location = location
