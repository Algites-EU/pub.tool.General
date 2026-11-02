"""Verify the shared two-field validation contract for Defs and SDO Codegen."""
from __future__ import annotations

import io

import pytest

from eu.algites.tool.codegen.common.aix_codegen_validation_exception import AIxCodegenValidationException
from eu.algites.tool.codegen.common.artifact_resolver import parse_artifacts, resolve_artifacts
from eu.algites.tool.codegen.common.diagnostics import format_diagnostic, report_exception


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
