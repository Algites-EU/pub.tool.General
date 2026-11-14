"""Verify the shared two-field validation contract for Defs and SDO Codegen."""
from __future__ import annotations

import io

import pytest

from eu.algites.tool.codegen.common.aix_codegen_validation_exception import AIxCodegenValidationException
from eu.algites.tool.codegen.common.artifact_resolver import parse_artifacts, resolve_artifacts
from eu.algites.tool.codegen.common.diagnostics import format_diagnostic, report_exception
from eu.algites.tool.codegen.common.validation_batch import AIxCodegenBatchValidationException


def test_unchanged_message_and_separate_hint():
    message = "'credentialProfile' does not match algites-jsondef-schema-versioned_1/type_name"
    hint = 'Rename $defs/credentialProfile to $defs/CredentialProfile and update $ref.'
    err = AIxCodegenValidationException(message, hint,
                                       source='credentials_1.jsondef.schema.json',
                                       location='#/$defs/credentialProfile')
    assert isinstance(err, ValueError)
    assert str(err) == message
    assert err.args == (message,)
    assert err.message == message
    assert err.hint == hint
    report = format_diagnostic(err, generator='Defs Codegen')
    assert f'  Message: {message}' in report
    assert f'  Hint: {hint}' in report
    assert '  Source: credentials_1.jsondef.schema.json' in report
    assert '  Location: #/$defs/credentialProfile' in report


def test_unexpected_error_is_not_mislabeled_as_validation_error():
    target = io.StringIO()
    assert not report_exception(RuntimeError('bug in Codegen'), stream=target)
    assert not report_exception(ValueError('unstructured legacy error'), stream=target)
    assert target.getvalue() == ''


def test_missing_hint_is_rejected():
    with pytest.raises(ValueError, match='Validation hint must not be blank'):
        AIxCodegenValidationException('error', '')


def test_artifact_resolver_propagates_explicit_hint(tmp_path):
    with pytest.raises(AIxCodegenValidationException) as failure:
        resolve_artifacts(parse_artifacts('example@1.1-SNAPSHOT', 'java'), 'java', tmp_path)
    assert 'Expected one local Java artifact' in failure.value.message
    assert 'local artifact repository' in failure.value.hint
    stream = io.StringIO()
    assert report_exception(failure.value, generator='SDO Codegen', stream=stream)
    assert stream.getvalue().count('Hint:') == 1


def test_batch_diagnostics_count_issues_per_source_even_when_interleaved():
    """Keep global order while counting errors within their source file."""
    errors = [
        AIxCodegenValidationException('first-A', 'fix A', source='/schemas/a.xsd', location='/one'),
        AIxCodegenValidationException('only-B', 'fix B', source='/schemas/b.xsd'),
        AIxCodegenValidationException('second-A', 'fix A again', source='/schemas/a.xsd', location='/two'),
        AIxCodegenValidationException('missing provenance', 'inspect input'),
        AIxCodegenValidationException('third-A', 'fix A once more', source='/schemas/a.xsd'),
        AIxCodegenValidationException('another unknown', 'inspect input'),
    ]
    target = io.StringIO()
    assert report_exception(AIxCodegenBatchValidationException(errors),
                            generator='Defs Codegen', stream=target)
    rendered = target.getvalue()
    assert 'VALIDATION ERRORS - Defs Codegen: 6 issue(s)' in rendered
    expected = [
        '[1/6] (1/3) first-A',
        '[2/6] (1/1) only-B',
        '[3/6] (2/3) second-A',
        '[4/6] (1/1) missing provenance',
        '[5/6] (3/3) third-A',
        '[6/6] (1/1) another unknown',
    ]
    assert [line.strip() for line in rendered.splitlines() if line.strip().startswith('[')] == expected
    assert 'Source: /schemas/a.xsd' in rendered
    assert 'Location: /two' in rendered
    assert rendered.count('Hint:') == 6


def test_batch_diagnostics_single_issue_file_in_multi_file_report():
    """A source occurring once in an aggregate report has a (1/1) suffix."""
    errors = [
        AIxCodegenValidationException('A', 'hint', source='a.json'),
        AIxCodegenValidationException('B', 'hint', source='b.json'),
    ]
    target = io.StringIO()
    assert report_exception(AIxCodegenBatchValidationException(errors), stream=target)
    assert '[1/2] (1/1) A' in target.getvalue()
    assert '[2/2] (1/1) B' in target.getvalue()
