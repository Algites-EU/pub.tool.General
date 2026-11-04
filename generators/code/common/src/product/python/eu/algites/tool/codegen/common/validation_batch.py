"""Common fail-fast/aggregate validation policy for both independent generators.

True preserves the legacy fail-fast behavior. False collects errors across all
selected inputs and never publishes partial generated output on validation error.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Iterable

from .aix_codegen_validation_exception import AIxCodegenValidationException

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
    chosen = parse_boolean(os.environ.get(ENVIRONMENT, 'true'))
    for argument in arguments:
        if argument.startswith(OPTION + '='):
            chosen = parse_boolean(argument[len(OPTION) + 1:])
    return chosen


class AIxCodegenBatchValidationException(ValueError):
    """Multiple independently validated source errors, in deterministic order.

    Args:
        errors: Nonempty sequence of input validation errors with provenance.
    """

    def __init__(self, errors: Iterable[AIxCodegenValidationException]) -> None:
        self.errors = tuple(errors)
        if not self.errors:
            raise ValueError('Batch error requires at least one issue')
        super().__init__(f'{len(self.errors)} input validation error(s)')


class AIcCodegenValidationBatch:
    """Collect source-specific failures, but propagate implementation errors."""

    def __init__(self, fail_fast: bool = True) -> None:
        self.fail_fast = fail_fast
        self.errors: list[AIxCodegenValidationException] = []

    def add(self, exc: AIxCodegenValidationException, *, source: str | None = None,
            location: str | None = None) -> None:
        """Record one issue with its source and location, or raise immediately."""
        enriched = AIxCodegenValidationException(
            exc.message, exc.hint,
            source=exc.source or source, location=exc.location or location)
        if self.fail_fast:
            raise enriched from exc
        self.errors.append(enriched)

    def finish(self) -> None:
        """Raise one complete report before any generated file is changed."""
        if self.errors:
            raise AIxCodegenBatchValidationException(self.errors)
