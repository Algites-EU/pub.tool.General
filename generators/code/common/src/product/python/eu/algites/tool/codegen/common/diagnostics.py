"""Render explicitly described Defs/SDO validation failures at process boundaries.

No message-based matching is performed: the validator that detects an issue
must supply both the original message and its own actionable hint. Unexpected
exceptions are not classified as user errors and retain their traceback.
"""
from __future__ import annotations

import os
import sys
import traceback
from pathlib import Path
from typing import TextIO

from eu.algites.tool.codegen.common.aix_codegen_validation_exception import AIxCodegenValidationException


def debug_enabled() -> bool:
    """Return whether the operator requested validation tracebacks."""
    return os.environ.get('ALGITES_CODEGEN_DEBUG', '').lower() in ('1', 'true', 'yes', 'on')


def format_diagnostic(error: AIxCodegenValidationException, *, generator: str = 'Codegen') -> str:
    """Format the original message and separate hint for terminal and CI logs.

    Args:
        error: Explicit validation failure with a hint.
        generator: Human-readable generator identity.

    Returns:
        Multiline, plain-text diagnostic with no ANSI escape sequences.
    """
    lines = ['', f'  VALIDATION ERROR - {generator}', '',
             f'  Message: {error.message}']
    if error.source:
        lines.append(f'  Source: {error.source}')
    if error.location:
        lines.append(f'  Location: {error.location}')
    lines.extend(['', f'  Hint: {error.hint}', ''])
    return '\n'.join(lines) + '\n'


def report_exception(exc: BaseException, *, generator: str = 'Codegen',
                     source: str | Path | None = None, location: str | None = None,
                     stream: TextIO | None = None) -> bool:
    """Report a typed validation failure and return True; ignore other failures.

    Args:
        exc: Failure to inspect; no message heuristics are applied.
        generator: Visible tool name.
        source: Optional fallback source if the exception lacks one.
        location: Optional fallback location if the exception lacks one.
        stream: Output stream, defaults to stderr.

    Returns:
        True only when a validation error was rendered.
    """
    if not isinstance(exc, AIxCodegenValidationException):
        return False
    output = stream if stream is not None else sys.stderr
    if source is not None or location is not None:
        exc = AIxCodegenValidationException(exc.message, exc.hint,
                source=exc.source or (str(source) if source is not None else None),
                location=exc.location or location)
    output.write(format_diagnostic(exc, generator=generator))
    if debug_enabled():
        traceback.print_exception(type(exc), exc, exc.__traceback__, file=output)
    return True
