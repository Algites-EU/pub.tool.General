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
from collections import Counter
from typing import TextIO, Iterable
from .diagnostic_model import AIcdCodegenDiagnostic, AInCodegenDiagnosticSeverity

from eu.algites.tool.codegen.common.aix_codegen_validation_exception import AIxCodegenValidationException
from eu.algites.tool.codegen.common.validation_batch import AIxCodegenBatchValidationException


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


def report_diagnostics(diagnostics: Iterable[AIcdCodegenDiagnostic], *,
                       generator: str = 'Codegen', stream: TextIO | None = None) -> bool:
    """Render a single ordered report grouped by increasing severity.

    Every section has independent global and per-file counters, even when the
    underlying diagnostic records from different source files are interleaved.
    DEBUG is suppressed unless ALGITES_CODEGEN_DEBUG is enabled; ERROR is last.

    Args:
        diagnostics: Structured events produced during the current Codegen run.
        generator: Human-readable generator label.
        stream: Optional output stream, defaulting to stderr.

    Returns:
        True when at least one visible diagnostic was emitted.
    """
    output = stream if stream is not None else sys.stderr
    entries = tuple(diagnostics)
    headers = {
        AInCodegenDiagnosticSeverity.DEBUG: 'DEBUG',
        AInCodegenDiagnosticSeverity.INFO: 'INFO',
        AInCodegenDiagnosticSeverity.WARNING: 'VALIDATION WARNINGS',
        AInCodegenDiagnosticSeverity.ERROR: 'VALIDATION ERRORS',
    }
    printed = False
    for level in AInCodegenDiagnosticSeverity:
        if level is AInCodegenDiagnosticSeverity.DEBUG and not debug_enabled():
            continue
        issues = [item for item in entries if item.severity is level]
        if not issues:
            continue
        printed = True
        counts = Counter(item.source for item in issues if item.source and item.source.strip())
        seen: Counter[str] = Counter()
        total = len(issues)
        output.write(f'\n  {headers[level]} - {generator}: {total} message(s)\n'
                     if level in (AInCodegenDiagnosticSeverity.DEBUG, AInCodegenDiagnosticSeverity.INFO)
                     else f'\n  {headers[level]} - {generator}: {total} issue(s)\n')
        for index, item in enumerate(issues, 1):
            if item.source and item.source.strip():
                seen[item.source] += 1
                position, source_total = seen[item.source], counts[item.source]
            else:
                position = source_total = 1
            output.write(f'\n  [{index}/{total}] ({position}/{source_total}) {item.message}\n')
            if item.source:
                output.write(f'  Source: {item.source}\n')
            if item.location:
                output.write(f'  Location: {item.location}\n')
            if item.hint:
                output.write(f'  Hint: {item.hint}\n')
    if printed:
        output.write('\n')
    return printed


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
    if isinstance(exc, AIxCodegenBatchValidationException):
        output = stream if stream is not None else sys.stderr
        report_diagnostics(exc.diagnostics, generator=generator, stream=output)
        if debug_enabled():
            traceback.print_exception(type(exc), exc, exc.__traceback__, file=output)
        return True
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
