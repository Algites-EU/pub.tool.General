"""Bootstrap SDO runs after Defs, for manually declared or generated contracts."""
from __future__ import annotations

from pathlib import Path
import sys

import pytest

BOOTSTRAP = Path(__file__).resolve().parents[1] / 'bootstrap'
sys.path.insert(0, str(BOOTSTRAP))
import generate_sources as codegen


def artifact(repository: Path, path: str, *, manual: bool = False,
             generated: bool = False) -> Path:
    root = repository / path
    root.mkdir(parents=True)
    (root / 'modustro-artifact.yml').write_text('Artifact: {TechnologyKinds: [java, python]}\n')
    if manual:
        folder = root / 'src/product/python/example'
        folder.mkdir(parents=True)
        (folder / 'read_contract.py').write_text('''\
class HandwrittenObject(AIiDataObject):
    __data_object__ = AIcdDataObject(schema_id='test', schema_version=1)
''')
    if generated:
        folder = root / 'src/product/python.gen/example'
        folder.mkdir(parents=True)
        (folder / 'aiig_read_contract_1.py').write_text('''\
class AIigReadContract_1(AIiDataObject):
    __data_object__ = AIcdDataObject(schema_id='test', schema_version=1)
''')
    return root


def test_no_dataobjects_never_loads_sdo(tmp_path, monkeypatch):
    artifact(tmp_path, 'one', manual=False)
    monkeypatch.setattr(codegen, '_load_codegen', lambda *_: pytest.fail('Should not load generator'))
    assert codegen.generate_sdo_python(tmp_path, tmp_path, tmp_path / 'work') == 0


def test_one_sdo_run_merges_manual_and_defs_sources(tmp_path, monkeypatch):
    selected = artifact(tmp_path, 'a/one', manual=True, generated=True)
    artifact(tmp_path, 'b/two', manual=True)
    seen = []

    def fake_loader(repository, work, module):
        assert module == codegen._SDO_MODULE
        def run(arguments):
            options = {name: value for name, value in (item[2:].split('=', 1)
                       for item in arguments if item.startswith('--') and '=' in item)}
            source = Path(options['technology-dointf-input-dir'].removeprefix('python:'))
            assert sorted(file.name for file in source.rglob('*.py')) == [
                'aiig_read_contract_1.py', 'read_contract.py']
            assert options['technology-sdoimpl-output-dir'] == 'python:' + str(
                selected / 'src/product/python.gen')
            assert any('algites-python-gen-data-yaml-class-versioned_1' in arg
                       for arg in arguments)
            assert any('algites-python-codegen-standard_1' in arg for arg in arguments)
            seen.append(arguments)
            return 0
        return run
    monkeypatch.setattr(codegen, '_load_codegen', fake_loader)
    assert codegen.generate_sdo_python(tmp_path, tmp_path / 'a', tmp_path / 'work') == 0
    assert len(seen) == 1
    assert (selected / 'src/product/python.gen').is_dir()


def test_manual_source_without_gen_directory_is_discovered(tmp_path):
    a = artifact(tmp_path, 'one', manual=True)
    assert codegen._sdo_python_artifacts(tmp_path, tmp_path) == [(a, 'product')]


def test_java_sdo_staged_before_publication():
    directory = BOOTSTRAP
    shell = (directory / 'build.sh').read_text(encoding='utf-8')
    assert shell.index('bootstrapSdoJava') < shell.index('publishAllPublicationsToBootstrapRepository')
    build = (directory / 'sdo-java.gradle').read_text(encoding='utf-8')
    assert "tasks.register('bootstrapSdoJava')" in build
    assert "dependsOn subprojects.collect { it.tasks.named('jar') }" in build
    assert 'algites-java-gen-data' in build
    assert 'src/product/java.gen' in build
    assert 'new ProcessBuilder(command.toArray(new String[0]))' in build
    assert 'algites-java-codegen-standard_1' in build
    assert not (directory.parent / 'codegen/run.sh').exists()


def test_tool_defscodegen_intf_has_interim_sdo_runtime_dependency():
    import yaml
    declaration = BOOTSTRAP.parent.parent / 'generators/code/defscodegen/intf/modustro-artifact.yml'
    data = yaml.safe_load(declaration.read_text())
    items = [item for group in data['Dependencies'] if group['DependencyKind'] == 'modustro'
             for item in group['Items']]
    assert any(item['ArtifactId'] == 'pub.lib.General_data.smartdataobject.impl'
               and 'product_api' in item['Usages'] for item in items)
