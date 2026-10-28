"""Common Defs bootstrap discovery and temporary Algites profile regression tests."""
from __future__ import annotations

from pathlib import Path
import subprocess
import sys

import pytest

BOOTSTRAP = Path(__file__).resolve().parents[1] / 'bootstrap'
sys.path.insert(0, str(BOOTSTRAP))
import generate_sources as codegen  # noqa: E402


def _artifact(root: Path, path: str, languages=('java', 'python')) -> Path:
    target = root / path
    target.mkdir(parents=True)
    (target / 'modustro-artifact.yml').write_text('Artifact: {}\n')
    for language in languages:
        (target / 'src/product' / (language + '.gen')).mkdir(parents=True)
    return target


def test_empty_repository_requires_no_generator_or_dependencies(tmp_path, monkeypatch):
    artifact = _artifact(tmp_path, 'nonmatching/one')
    (artifact / 'src/product/jsondefs').mkdir()
    monkeypatch.setattr(codegen, '_load_codegen', lambda *_: pytest.fail('Unexpected import'))
    assert codegen.generate(tmp_path, tmp_path, tmp_path / 'tmp') == 0


def test_noop_even_if_generated_roots_contain_non_schemas(tmp_path, monkeypatch):
    artifact = _artifact(tmp_path, 'one')
    inputs = artifact / 'src/product/yamldefs'
    inputs.mkdir()
    (inputs / 'profile.meta.yml').write_text('metadata-only')
    monkeypatch.setattr(codegen, '_load_codegen', lambda *_: pytest.fail('Unexpected import'))
    assert codegen.generate(tmp_path, tmp_path, tmp_path / 'tmp') == 0


def test_json_encoded_yamldefs_is_discovered_and_scoped(tmp_path):
    a = _artifact(tmp_path, 'a/one')
    b = _artifact(tmp_path, 'b/two')
    for artifact in (a, b):
        source = artifact / 'src/product/yamldefs/example.yamldef.schema.json'
        source.parent.mkdir()
        source.write_text('{}')
    selected = codegen._applicable_artifacts(tmp_path, tmp_path / 'a')
    assert list(selected) == [(a, 'product')]
    assert selected[(a, 'product')] == (['java', 'python'], ['yamldefs'])


def test_algites_profile_is_selected_by_common_bootstrap_not_settings(tmp_path):
    artifact = _artifact(tmp_path, 'project')
    profiles = codegen._manifest(tmp_path, artifact, ['java', 'python'], ['jsondefs', 'xmldefs'])
    assert profiles['schema_input_naming_conventions'] is codegen.ALGITES_INPUT_PROFILES
    assert profiles['technology_outputs']['java'].endswith('/java.gen')
    assert profiles['technology_output_naming_conventions']['java']['common'] == 'algites-java-gen-intf-versioned_1'
    assert profiles['technology_output_naming_conventions']['python']['xmldefs_namespace'] == 'algites-python-gen-xml-namespace-intf_1'
    assert 'resource:algites-java-name-conventions.yml' in profiles['naming_convention_files']


def test_bootstrap_configuration_never_requires_specific_generator_runner():
    script = BOOTSTRAP / 'bootstrap-config.py'
    root = BOOTSTRAP.parent.parent
    result = subprocess.run([sys.executable, str(script), '--repository', str(root), '--nul'],
                            capture_output=True)
    assert result.returncode == 0, result.stderr.decode()
    values = [item for item in result.stdout.decode().split('\x00') if item]
    assert len(values) == 7
    assert 'devops/codegen/run.sh' not in values
    assert not (root / 'devops/codegen/run.sh').exists()
