"""Regression tests for independent Defs/SDO CLI invocation from bootstrap."""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import sys

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
spec = importlib.util.spec_from_file_location('bootstrap_codegen_source_adapter', HERE / 'generate_sources.py')
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)


def test_defs_bootstrap_passes_all_qualified_parameters(monkeypatch, tmp_path):
    monkeypatch.setenv('MODUSTRO_CODEGEN_VALIDATE_ONE_INPUT_AT_A_TIME_ONLY', 'false')
    artifact = tmp_path / 'contract'
    artifact.mkdir()
    manifest = adapter._manifest(tmp_path, artifact, ['java', 'python'], ['jsondefs', 'xmldefs'])
    arguments = adapter._defs_cli_arguments(tmp_path, manifest)
    assert '--codegen-validate-one-input-at-a-time-only=false' in arguments
    assert '--repository-root=' + str(tmp_path) in arguments
    assert '--schema-input-dir:jsondefs=contract/src/product/jsondefs' in arguments
    assert '--schema-input-dir:xmldefs=contract/src/product/xmldefs' in arguments
    assert '--schema-input-dir:yamldefs=' in arguments
    for lang in ('java', 'python'):
        assert f'--technology-dointf-output-dir:{lang}=contract/src/product/{lang}.gen' in arguments
        assert f'--common-codegen-naming-convention:{lang}=algites-{lang}-codegen-common_1' in arguments
        assert f'--defs-codegen-naming-convention:{lang}=algites-{lang}-defscodegen-standard_1' in arguments
    assert not any('schema-contract-bindings-generator' in item for item in arguments)


def test_defs_bootstrap_uses_cli_and_respects_output_scope(monkeypatch, tmp_path):
    artifact = tmp_path / 'contracts'
    (artifact / 'src/product/jsondefs').mkdir(parents=True)
    (artifact / 'src/product/java.gen').mkdir(parents=True)
    invoked = []

    def fake_cli(arguments):
        invoked.append(arguments)
        out = artifact / 'src/product/java.gen/example/AIigThing_1.java'
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text('interface AIigThing_1 {}', encoding='utf-8')
        return 0

    monkeypatch.setattr(adapter, '_applicable_artifacts', lambda repo, root: {
        (artifact, 'product'): (['java'], ['jsondefs'])})
    monkeypatch.setattr(adapter, '_load_codegen', lambda repo, output: fake_cli)
    assert adapter.generate(tmp_path, tmp_path, tmp_path / 'output') == 1
    assert len(invoked) == 1
    assert '--technology-dointf-output-dir:python=' in invoked[0]
    assert '--technology-dointf-output-dir:java=contracts/src/product/java.gen' in invoked[0]


def test_bootstrap_policy_is_strict_and_defaults_true(monkeypatch):
    monkeypatch.delenv('MODUSTRO_CODEGEN_VALIDATE_ONE_INPUT_AT_A_TIME_ONLY', raising=False)
    assert adapter._validation_policy() == 'true'
    monkeypatch.setenv('MODUSTRO_CODEGEN_VALIDATE_ONE_INPUT_AT_A_TIME_ONLY', 'false')
    assert adapter._validation_policy() == 'false'
    monkeypatch.setenv('MODUSTRO_CODEGEN_VALIDATE_ONE_INPUT_AT_A_TIME_ONLY', 'no')
    with pytest.raises(ValueError, match='true or false'):
        adapter._validation_policy()


def test_defs_cli_accepts_policy_and_forwards_it_to_engine(monkeypatch, tmp_path):
    from eu.algites.tool.codegen.defs.old.impl.cli.aic_defs_codegen_cli import AIcDefsCodegenCli
    from eu.algites.tool.codegen.defs.old.impl.standard.aic_schema_contract_bindings_generator import (
        AIcSchemaContractBindingsGenerator,
    )
    seen = []
    def fake_generate(self, repository, manifest, check=False):
        seen.append(manifest)
        return []
    monkeypatch.setattr(AIcSchemaContractBindingsGenerator, 'generate_manifest', fake_generate)
    args = [
        f'--repository-root={tmp_path}',
        '--schema-input-dir:jsondefs=missing',
        '--input-schema-naming-convention:jsondefs=profile',
        '--technology-dointf-output-dir:python=out',
        '--naming-conventions-file:catalog=resource:standard-conventions.yml',
        '--codegen-validate-one-input-at-a-time-only=false',
    ]
    assert AIcDefsCodegenCli._batch(args) == 0
    assert seen[0]['codegen_validate_one_input_at_a_time_only'] is False


def test_codegen_batch_reports_multiple_sources_without_writing(tmp_path):
    from eu.algites.tool.codegen.common.validation_batch import (
        AIcCodegenValidationBatch, AIxCodegenBatchValidationException,
    )
    from eu.algites.tool.codegen.common.aix_codegen_validation_exception import AIxCodegenValidationException
    from eu.algites.tool.codegen.common.diagnostics import report_exception
    import io
    batch = AIcCodegenValidationBatch(False)
    batch.add(AIxCodegenValidationException('first', 'fix first'), source='one.json')
    batch.add(AIxCodegenValidationException('second', 'fix second'), source='two.xsd')
    with pytest.raises(AIxCodegenBatchValidationException) as capture:
        batch.finish()
    output = io.StringIO()
    assert report_exception(capture.value, generator='Defs Codegen', stream=output)
    assert '2 issue(s)' in output.getvalue()
    assert 'one.json' in output.getvalue()
    assert 'two.xsd' in output.getvalue()


def test_bootstrap_defs_cli_regenerates_real_both_language_contracts(tmp_path):
    """No direct generate_manifest bypass: invoke the real CLI with Algites naming."""
    import json
    from eu.algites.tool.codegen.defs.old.impl.cli.aic_defs_codegen_cli import AIcDefsCodegenCli

    artifact = tmp_path / 'intf'
    schema = artifact / 'src/product/jsondefs/demo/customer_1.jsondef.schema.json'
    schema.parent.mkdir(parents=True)
    schema.write_text(json.dumps({
        '$schema': 'https://json-schema.org/draft/2020-12/schema',
        '$id': 'urn:demo:customer:1', 'x-algites-schema-id': 'demo.customer',
        'x-algites-schema-version': 1, 'type': 'object',
        'properties': {'Name': {'type': 'string'}},
    }), encoding='utf-8')
    for tech in ('java', 'python'):
        (artifact / f'src/product/{tech}.gen').mkdir()
    args = adapter._defs_cli_arguments(tmp_path,
        adapter._manifest(tmp_path, artifact, ['java', 'python'], ['jsondefs']))
    assert AIcDefsCodegenCli.main(args) == 0
    java = list((artifact/'src/product/java.gen').rglob('*.java'))
    python = list((artifact/'src/product/python.gen').rglob('*.py'))
    assert len(java) == len(python) == 2
    assert any('getName' in path.read_text() for path in java)
    assert any('getName' in path.read_text() for path in python)


def test_bootstrap_defs_aggregate_validates_two_schemas_before_generation(tmp_path, monkeypatch):
    """An invalid batch leaves both language output roots unchanged."""
    from eu.algites.tool.codegen.defs.old.impl.cli.aic_defs_codegen_cli import AIcDefsCodegenCli
    from eu.algites.tool.codegen.common.validation_batch import AIxCodegenBatchValidationException
    monkeypatch.setenv('MODUSTRO_CODEGEN_VALIDATE_ONE_INPUT_AT_A_TIME_ONLY', 'false')
    artifact = tmp_path / 'intf'
    root = artifact / 'src/product/jsondefs/demo'
    root.mkdir(parents=True)
    for stem in ('brokenfirst', 'brokensecond'):
        (root / f'{stem}_1.jsondef.schema.json').write_text('{broken JSON', encoding='utf-8')
    for tech in ('java', 'python'):
        (artifact / f'src/product/{tech}.gen').mkdir()
    args = adapter._defs_cli_arguments(tmp_path,
        adapter._manifest(tmp_path, artifact, ['java', 'python'], ['jsondefs']))
    with pytest.raises(AIxCodegenBatchValidationException) as failure:
        AIcDefsCodegenCli.main(args)
    assert len(failure.value.errors) == 2
    assert {Path(e.source).name for e in failure.value.errors} == {
        'brokenfirst_1.jsondef.schema.json', 'brokensecond_1.jsondef.schema.json'}
    assert not any(path.is_file() for tech in ('java', 'python')
                   for path in (artifact / f'src/product/{tech}.gen').rglob('*'))
