"""Regression tests for native Defs/SDO CLI invocation from bootstrap."""
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







def test_defs_bootstrap_no_longer_selects_old_cli():
    """The generation driver must load current Defs and SDO public entrypoints."""
    assert 'defs/impl/cli/canonical_defs_codegen_cli.py' in adapter._CODEGEN_MODULE.as_posix()
    assert '/old/' not in adapter._CODEGEN_MODULE.as_posix()
    assert 'sdo/impl/cli/aic_sdo_codegen_cli.py' in adapter._SDO_MODULE.as_posix()
    assert '/old/' not in adapter._SDO_MODULE.as_posix()


def test_defs_bootstrap_uses_public_cli_once_per_artifact(monkeypatch, tmp_path):
    """Bootstrap passes the selected inputs directly, without any --manifest."""
    artifact = tmp_path / 'contracts'
    (artifact / 'src/product/jsondefs').mkdir(parents=True)
    (artifact / 'src/product/java.gen').mkdir(parents=True)
    seen = []

    def fake_cli(arguments):
        seen.append(arguments)
        for i in (1, 2):
            out = artifact / f'src/product/java.gen/example/AIigThing{i}_1.java'
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(f'interface AIigThing{i}_1 {{}}', encoding='utf-8')
        return 0

    monkeypatch.setattr(adapter, '_applicable_artifacts', lambda repo, root: {
        (artifact, 'product'): (['java'], ['jsondefs'])})
    monkeypatch.setattr(adapter, '_native_settings_owner', lambda repo: HERE.parents[1])
    monkeypatch.setattr(adapter, '_source_checkouts', lambda repo: [repo])
    monkeypatch.setattr(adapter, '_load_codegen', lambda repo, output: fake_cli)
    assert adapter.generate(tmp_path, tmp_path, tmp_path / 'output') == 2
    assert len(seen) == 1
    assert not any('--manifest' in token for token in seen[0])
    assert any(item.startswith('--defs-input-paths:java=') for item in seen[0])
    assert any(item.startswith('--defs-dependency-paths:java=') for item in seen[0])
    assert any(item.startswith('--technology-dointf-output-dir:java=') for item in seen[0])


def test_bootstrap_policy_is_strict_and_defaults_false(monkeypatch):
    monkeypatch.delenv('MODUSTRO_CODEGEN_VALIDATE_ONE_INPUT_AT_A_TIME_ONLY', raising=False)
    assert adapter._validation_policy() == 'false'
    monkeypatch.setenv('MODUSTRO_CODEGEN_VALIDATE_ONE_INPUT_AT_A_TIME_ONLY', 'false')
    assert adapter._validation_policy() == 'false'
    monkeypatch.setenv('MODUSTRO_CODEGEN_VALIDATE_ONE_INPUT_AT_A_TIME_ONLY', 'no')
    with pytest.raises(ValueError, match='true or false'):
        adapter._validation_policy()




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






def test_validation_policy_defaults_to_exhaustive_and_first_file_mode_waits_for_all_issues(monkeypatch):
    """An optimized run reports every recorded issue in the first invalid file."""
    from eu.algites.tool.codegen.common.validation_batch import (
        AIcCodegenValidationBatch, AIxCodegenBatchValidationException, selected_policy)
    from eu.algites.tool.codegen.common.aix_codegen_validation_exception import AIxCodegenValidationException

    monkeypatch.delenv('MODUSTRO_CODEGEN_VALIDATE_ONE_INPUT_AT_A_TIME_ONLY', raising=False)
    assert selected_policy([]) is False
    collector = AIcCodegenValidationBatch(True)
    collector.add(AIxCodegenValidationException('invalid attribute A', 'correct A'),
                  source='first.xsd', location='/a')
    collector.add(AIxCodegenValidationException('invalid attribute B', 'correct B'),
                  source='first.xsd', location='/b')
    with pytest.raises(AIxCodegenBatchValidationException) as capture:
        collector.finish_input('first.xsd')
    assert [(item.source, item.location) for item in capture.value.errors] == [
        ('first.xsd', '/a'), ('first.xsd', '/b')]






def test_bootstrap_does_not_select_scalar_xsd_vocabulary(tmp_path):
    """Mirror the library regression: schema metadata are not generated DOs."""
    artifact = tmp_path / 'documentation/intf'
    artifact.mkdir(parents=True)
    (artifact / 'modustro-artifact.yml').write_text('Artifact: {}\n', encoding='utf-8')
    (artifact / 'src/product/java.gen').mkdir(parents=True)
    path = artifact / 'src/product/xmldefs/eu/example/annotation_1.xsd'
    path.parent.mkdir(parents=True)
    path.write_text('''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
<xs:element name="title" type="xs:string"/></xs:schema>''', encoding='utf-8')
    assert adapter._applicable_artifacts(tmp_path, tmp_path) == {}
