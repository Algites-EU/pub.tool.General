"""Feature tests for stable, severity-grouped diagnostics shared by both Codegens."""
from __future__ import annotations

from contextlib import redirect_stderr
from io import StringIO

import pytest

from eu.algites.tool.codegen.common.aix_codegen_validation_exception import AIxCodegenValidationException
from eu.algites.tool.codegen.common.diagnostic_model import (
    AIcdCodegenDiagnostic, AInCodegenDiagnosticSeverity as Severity,
)
from eu.algites.tool.codegen.common.diagnostics import report_diagnostics, report_exception
from eu.algites.tool.codegen.common.validation_batch import (
    AIcCodegenValidationBatch, AIxCodegenBatchValidationException,
)


def test_each_severity_has_its_own_numbering_and_errors_are_last(monkeypatch):
    monkeypatch.setenv('ALGITES_CODEGEN_DEBUG', 'true')
    batch = AIcCodegenValidationBatch(False)
    batch.add(AIxCodegenValidationException('error A1', 'correct A1', source='a.xsd'))
    batch.info('info A', source='a.xsd')
    batch.warning('warn B', hint='check B', source='b.json', location='/child')
    batch.debug('debug A', source='a.xsd')
    batch.warning('warn A1', source='a.xsd')
    batch.add(AIxCodegenValidationException('error B', 'correct B', source='b.json'))
    batch.warning('warn A2', source='a.xsd')
    batch.add(AIxCodegenValidationException('error A2', 'correct A2', source='a.xsd'))
    batch.info('info C', source='c.xsd')
    with pytest.raises(AIxCodegenBatchValidationException) as failure:
        batch.finish()
    output = StringIO()
    assert report_exception(failure.value, generator='Defs Codegen', stream=output)
    rendered = output.getvalue()
    headers = ['DEBUG - Defs Codegen', 'INFO - Defs Codegen',
               'VALIDATION WARNINGS - Defs Codegen', 'VALIDATION ERRORS - Defs Codegen']
    assert [rendered.index(head) for head in headers] == sorted(rendered.index(head) for head in headers)
    assert '[1/3] (1/2) warn B' not in rendered
    assert '[1/3] (1/1) warn B' in rendered
    assert '[2/3] (1/2) warn A1' in rendered
    assert '[3/3] (2/2) warn A2' in rendered
    assert '[1/3] (1/2) error A1' in rendered
    assert '[2/3] (1/1) error B' in rendered
    assert '[3/3] (2/2) error A2' in rendered
    assert 'Location: /child' in rendered
    assert 'Hint: check B' in rendered


def test_warning_only_does_not_fail_and_debug_is_opt_in(monkeypatch):
    monkeypatch.delenv('ALGITES_CODEGEN_DEBUG', raising=False)
    batch = AIcCodegenValidationBatch(False)
    batch.warning('unsupported index', source='a.xsd')
    batch.info('continued generation', source='a.xsd')
    batch.debug('hidden internals', source='a.xsd')
    batch.finish()  # no error
    out = StringIO()
    batch.report_non_errors(generator='SDO Codegen', stream=out)
    rendered = out.getvalue()
    assert 'VALIDATION WARNINGS - SDO Codegen: 1 issue(s)' in rendered
    assert 'INFO - SDO Codegen: 1 message(s)' in rendered
    assert 'hidden internals' not in rendered
    assert 'VALIDATION ERRORS' not in rendered


def test_one_input_policy_preserves_prior_messages_and_reports_first_invalid_input():
    batch = AIcCodegenValidationBatch(True)
    batch.warning('warning from earlier file', source='a.xsd')
    batch.finish_input('a.xsd')
    batch.add(AIxCodegenValidationException('one', 'fix', source='b.xsd'))
    batch.add(AIxCodegenValidationException('two', 'fix', source='b.xsd'))
    with pytest.raises(AIxCodegenBatchValidationException) as failure:
        batch.finish_input('b.xsd')
    output = StringIO()
    assert report_exception(failure.value, stream=output)
    assert output.getvalue().index('VALIDATION WARNINGS') < output.getvalue().index('VALIDATION ERRORS')
    assert '[1/2] (1/2) one' in output.getvalue()
    assert '[2/2] (2/2) two' in output.getvalue()


def test_invalid_severity_or_error_hint_is_rejected():
    with pytest.raises(TypeError):
        AIcdCodegenDiagnostic('WARN', 'message')
    with pytest.raises(ValueError, match='hint'):
        AIcdCodegenDiagnostic(Severity.ERROR, 'invalid', None)
    with pytest.raises(ValueError, match='hint'):
        AIcCodegenValidationBatch().add_diagnostic(Severity.ERROR, 'invalid')


def test_uncategorized_sources_are_not_mistaken_for_same_file(monkeypatch):
    monkeypatch.delenv('ALGITES_CODEGEN_DEBUG', raising=False)
    output = StringIO()
    messages = [AIcdCodegenDiagnostic(Severity.WARNING, 'unknown1'),
                AIcdCodegenDiagnostic(Severity.WARNING, 'unknown2')]
    assert report_diagnostics(messages, stream=output)
    assert '[1/2] (1/1) unknown1' in output.getvalue()
    assert '[2/2] (1/1) unknown2' in output.getvalue()


def test_one_error_with_warning_still_renders_severity_sections():
    """Nonfatal diagnostics must not disappear into a legacy single-error format."""
    batch = AIcCodegenValidationBatch(False)
    batch.info('read schema', source='first.xsd')
    batch.warning('skipped optional index', source='first.xsd')
    batch.add(AIxCodegenValidationException('bad declaration', 'fix schema',
                                           source='first.xsd'))
    with pytest.raises(AIxCodegenBatchValidationException) as failure:
        batch.finish()
    output = StringIO()
    assert report_exception(failure.value, stream=output)
    rendered = output.getvalue()
    assert rendered.index('INFO - Codegen') < rendered.index('VALIDATION WARNINGS')
    assert rendered.index('VALIDATION WARNINGS') < rendered.index('VALIDATION ERRORS')
    assert '[1/1] (1/1) bad declaration' in rendered


def test_optimized_mode_at_finish_does_not_report_errors_from_other_files():
    """The selected first invalid input must be the only source of ERROR diagnostics."""
    batch = AIcCodegenValidationBatch(True)
    batch.warning('before validation', source='first.xsd')
    batch.add(AIxCodegenValidationException('first error', 'fix first',
                                           source='first.xsd'))
    batch.add(AIxCodegenValidationException('later error', 'fix later',
                                           source='later.xsd'))
    with pytest.raises(AIxCodegenBatchValidationException) as failure:
        batch.finish()
    output = StringIO()
    assert report_exception(failure.value, stream=output)
    rendered = output.getvalue()
    assert 'first error' in rendered
    assert 'later error' not in rendered
    assert '[1/1] (1/1) first error' in rendered
