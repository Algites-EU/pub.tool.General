"""Bootstrap SDO runs after Defs, for manually declared or generated contracts."""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import shutil
import sys
from types import SimpleNamespace

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
            source = Path(options['sdo-input-paths:python'])
            assert sorted(file.name for file in source.rglob('*.py')) == [
                'aiig_read_contract_1.py', 'read_contract.py']
            assert options['technology-sdoimpl-output-dir:python'] == str(
                selected / 'src/product/python.gen')
            assert any('algites-python-gen-data-yaml-class-versioned_1' in arg
                       for arg in arguments)
            assert any('algites-python-codegen-common_1' in arg for arg in arguments)
            seen.append(arguments)
            return 0
        return run
    monkeypatch.setattr(codegen, '_load_codegen', fake_loader)

    # The real CLI provides this workspace module. Keep the bootstrap test
    # independent of installed generator wheels while enforcing build-local
    # per-artifact staging and cleanup.
    @contextmanager
    def fixture_workspace(repository, artifact, generator):
        workspace = repository / 'build' / artifact.relative_to(repository) / generator / 'fixture'
        workspace.mkdir(parents=True)
        try:
            yield workspace
        finally:
            shutil.rmtree(workspace)

    monkeypatch.setitem(sys.modules, 'eu.algites.tool.codegen.common.workspace',
                        SimpleNamespace(invocation_workspace=fixture_workspace))
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
    assert 'algites-java-codegen-common_1' in build
    assert not (directory.parent / 'codegen/run.sh').exists()


def test_tool_defscodegen_intf_has_interim_sdo_runtime_dependency():
    import yaml
    declaration = BOOTSTRAP.parent.parent / 'generators/code/defscodegen/intf/modustro-artifact.yml'
    data = yaml.safe_load(declaration.read_text())
    items = [item for group in data['Dependencies'] if group['DependencyKind'] == 'modustro'
             for item in group['Items']]
    assert any(item['ArtifactId'] == 'pub.lib.General_data.smartdataobject.impl'
               and 'product_api' in item['Usages'] for item in items)


def test_writable_sdo_contract_is_not_a_new_defs_input(tmp_path):
    """An SDO type carries metadata but must not be fed back into SDO codegen.

    Check an arbitrary class/module name, since name prefixes are configurable.
    The Java bootstrap already enforces the equivalent mutable marker gate.
    """
    source = artifact(tmp_path, 'one', manual=False)
    folder = source / 'src/product/python/example'
    folder.mkdir(parents=True)
    (folder / 'write_contract.py').write_text('''\
class EditablePerson(AIiJsonSmartDataObject):
    __data_object__ = AIcdDataObject(title='Editable person')
''')
    assert codegen._sdo_python_artifacts(tmp_path, tmp_path) == []
    assert not codegen._python_contract_source(folder / 'write_contract.py')


def test_generated_sdo_with_indirect_parent_is_not_a_readonly_input(tmp_path):
    """A prior SDO output must never be fed back into SDO when cleanup is off.

    This also holds if its immediate base is another generated implementation
    and the selected naming convention uses neither AIcgd nor AIigd.
    """
    root = artifact(tmp_path, 'one', manual=False, generated=True)
    generated = root / 'src/product/python.gen/example/impl'
    generated.mkdir(parents=True)
    implementation = generated / 'custom_implementation.py'
    implementation.write_text(
        '"""Generated SmartDataObject implementation for SomeContract."""\n'
        'class CustomImplementation(CustomSharedBase, CustomMutableContract):\n'
        '    __data_object__ = AIcdDataObject(title="SomeContract")\n'
    )
    writable = generated / 'custom_mutable.py'
    writable.write_text(
        '"""Generated mutable contract for SomeContract."""\n'
        'class CustomMutableContract(CustomReadContract, CustomMutableBase):\n'
        '    __data_object__ = AIcdDataObject(title="SomeContract")\n'
    )
    assert not codegen._python_contract_source(implementation)
    assert not codegen._python_contract_source(writable)
    assert codegen._sdo_python_artifacts(tmp_path, tmp_path) == [(root, 'product')]
    manually_written = root / 'src/product/python/example/custom_read.py'
    manually_written.parent.mkdir(parents=True, exist_ok=True)
    manually_written.write_text(
        'class CustomReadContract(AIiDataObject):\n'
        '    __data_object__ = AIcdDataObject(title="Handwritten")\n'
    )
    assert codegen._python_contract_source(manually_written)


def test_sdo_staging_excludes_previous_mutable_outputs(tmp_path, monkeypatch):
    """A second bootstrap must stage only its read-only contracts.

    The generated classes may be indirectly mutable and use arbitrary names;
    a copied SDO module remains SDO-owned regardless of directory naming.
    """
    root = artifact(tmp_path, 'one', manual=True, generated=True)
    generated = root / 'src/product/python.gen/example/impl'
    generated.mkdir(parents=True)
    (generated / 'custom_implementation.py').write_text(
        '"""Generated SmartDataObject implementation for SomeContract."""\n'
        'class CustomImplementation(CustomSharedBase, CustomMutableContract):\n'
        '    __data_object__ = AIcdDataObject(title="SomeContract")\n'
    )
    (generated / 'custom_mutable.py').write_text(
        '"""Generated mutable contract for SomeContract."""\n'
        'class CustomMutableContract(CustomReadContract, CustomMutableBase):\n'
        '    __data_object__ = AIcdDataObject(title="SomeContract")\n'
    )
    seen = []

    def fake_loader(_repository, _output, _module):
        def run(arguments):
            selected = next(item.split('=', 1)[1] for item in arguments
                            if item.startswith('--sdo-input-paths:python='))
            files = sorted(path.name for path in Path(selected).rglob('*.py'))
            seen.append(files)
            assert files == ['aiig_read_contract_1.py', 'read_contract.py']
            assert '--cleanup-output-folder-before-generation=false' in arguments
            return 0
        return run

    @contextmanager
    def fixture_workspace(repository, selected_artifact, generator):
        workspace = repository / 'build' / selected_artifact.relative_to(repository) / generator / 'test'
        workspace.mkdir(parents=True)
        try:
            yield workspace
        finally:
            shutil.rmtree(workspace)

    monkeypatch.setattr(codegen, '_load_codegen', fake_loader)
    monkeypatch.setitem(sys.modules, 'eu.algites.tool.codegen.common.workspace',
                        SimpleNamespace(invocation_workspace=fixture_workspace))
    assert codegen.generate_sdo_python(tmp_path, root, tmp_path / 'build/run/bootstrap') == 0
    assert len(seen) == 1
    # The same staging rule must hold when the generated sources already exist.
    assert codegen.generate_sdo_python(tmp_path, root, tmp_path / 'build/run/bootstrap') == 0
    assert len(seen) == 2
    assert not codegen._python_contract_source(generated / 'custom_mutable.py')
