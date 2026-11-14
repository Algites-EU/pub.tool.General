"""Common fail-fast/aggregate validation policy for both independent generators.

False (default) validates the complete selected input scope. True stops after
validating the first failing input, reporting its independently discovered errors.
Neither mode publishes generated output while validation has failed.
"""
from __future__ import annotations

import os
from typing import Iterable

from .aix_codegen_validation_exception import AIxCodegenValidationException
from .diagnostic_model import AIcdCodegenDiagnostic, AInCodegenDiagnosticSeverity

OPTION = '--codegen-validate-one-input-at-a-time-only'
ENVIRONMENT = 'MODUSTRO_CODEGEN_VALIDATE_ONE_INPUT_AT_A_TIME_ONLY'


def parse_boolean(value: str) -> bool:
    """Parse a strict CLI Boolean; reject silent coercion of malformed values."""
    if value == 'true':
        return True
    if value == 'false':
        return False
    raise AIxCodegenValidationException(
        f'{OPTION} expects true or false, received {value!r}',
        'Use --codegen-validate-one-input-at-a-time-only=true or =false.',
        location=OPTION)


def selected_policy(arguments: Iterable[str]) -> bool:
    """Return the explicit last CLI setting, or the bootstrap environment/default."""
    chosen = parse_boolean(os.environ.get(ENVIRONMENT, 'false'))
    for argument in arguments:
        if argument.startswith(OPTION + '='):
            chosen = parse_boolean(argument[len(OPTION) + 1:])
    return chosen


class AIxCodegenBatchValidationException(ValueError):
    """Multiple independently validated source errors, in deterministic order.

    Args:
        errors: Nonempty sequence of input validation errors with provenance.
    """

    def __init__(self, errors: Iterable[AIxCodegenValidationException], *,
                 diagnostics: Iterable[AIcdCodegenDiagnostic] | None = None) -> None:
        self.errors = tuple(errors)
        if not self.errors:
            raise ValueError('Batch error requires at least one issue')
        self.diagnostics = tuple(diagnostics) if diagnostics is not None else tuple(
            AIcdCodegenDiagnostic(AInCodegenDiagnosticSeverity.ERROR, error.message,
                                  error.hint, error.source, error.location)
            for error in self.errors)
        super().__init__(f'{len(self.errors)} input validation error(s)')


class AIcCodegenValidationBatch:
    """Collect source-specific failures, but propagate implementation errors."""

    def __init__(self, fail_fast: bool = False) -> None:
        self.fail_fast = fail_fast
        self.errors: list[AIxCodegenValidationException] = []
        self.diagnostics: list[AIcdCodegenDiagnostic] = []

    def add(self, exc: AIxCodegenValidationException, *, source: str | None = None,
            location: str | None = None) -> None:
        """Record an issue; defer throwing until the input is fully examined."""
        enriched = AIxCodegenValidationException(
            exc.message, exc.hint,
            source=exc.source or source, location=exc.location or location)
        self.errors.append(enriched)
        self.diagnostics.append(AIcdCodegenDiagnostic(
            AInCodegenDiagnosticSeverity.ERROR, enriched.message, enriched.hint,
            enriched.source, enriched.location))

    def add_diagnostic(self, severity: AInCodegenDiagnosticSeverity, message: str,
                       *, hint: str | None = None, source: str | None = None,
                       location: str | None = None) -> None:
        """Collect a structured event; ERROR uses normal typed validation handling."""
        if severity is AInCodegenDiagnosticSeverity.ERROR:
            self.add(AIxCodegenValidationException(message, hint or '',
                     source=source, location=location))
        else:
            self.diagnostics.append(AIcdCodegenDiagnostic(
                severity, message, hint, source, location))

    def debug(self, message: str, *, source: str | None = None,
              location: str | None = None) -> None:
        """Record a developer-level event (rendered only when debug is enabled)."""
        self.add_diagnostic(AInCodegenDiagnosticSeverity.DEBUG, message,
                            source=source, location=location)

    def info(self, message: str, *, source: str | None = None,
             location: str | None = None) -> None:
        """Record an informational event without changing run success."""
        self.add_diagnostic(AInCodegenDiagnosticSeverity.INFO, message,
                            source=source, location=location)

    def warning(self, message: str, *, hint: str | None = None,
                source: str | None = None, location: str | None = None) -> None:
        """Record a recoverable issue that does not cause failure."""
        self.add_diagnostic(AInCodegenDiagnosticSeverity.WARNING, message,
                            hint=hint, source=source, location=location)

    def report_non_errors(self, *, generator: str = 'Codegen', stream=None) -> None:
        """Flush all collected non-error messages after successful validation."""
        from .diagnostics import report_diagnostics
        report_diagnostics((item for item in self.diagnostics
                            if item.severity is not AInCodegenDiagnosticSeverity.ERROR),
                           generator=generator, stream=stream)

    def finish_input(self, source: str) -> None:
        """Stop after collecting all available errors of one input in optimized mode.

        The caller invokes this only at the *end* of the input's validation,
        never after each individual declaration or field.
        """
        if self.fail_fast:
            errors = [error for error in self.errors if error.source == source]
            if errors:
                diagnostics = [item for item in self.diagnostics
                               if item.severity is not AInCodegenDiagnosticSeverity.ERROR
                               or item.source == source]
                if len(errors) == 1 and len(diagnostics) == 1:
                    raise errors[0]
                raise AIxCodegenBatchValidationException(
                    errors, diagnostics=diagnostics)

    def finish(self) -> None:
        """Report all errors, or those from the first invalid input in fast mode."""
        if self.errors:
            if self.fail_fast:
                first = self.errors[0].source
                selected = [error for error in self.errors if error.source == first]
            else:
                selected = self.errors
            diagnostics = ([item for item in self.diagnostics
                            if item.severity is not AInCodegenDiagnosticSeverity.ERROR
                            or item.source == first]
                           if self.fail_fast else self.diagnostics)
            # Preserve the existing single-error API for clients that catch
            # AIxCodegenValidationException and inspect its exact message.
            if len(selected) == 1 and len(diagnostics) == 1:
                raise selected[0]
            raise AIxCodegenBatchValidationException(
                selected, diagnostics=diagnostics)
