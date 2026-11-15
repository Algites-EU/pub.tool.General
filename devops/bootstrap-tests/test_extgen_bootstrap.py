"""Persistent generated canonical bootstrap snapshot and naming profile regressions."""
from __future__ import annotations

from pathlib import Path
import importlib.util
import os
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
BOOTSTRAP = ROOT / 'devops/bootstrap'


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_persistent_canonical_sources_match_provenance_manifest():
    script = BOOTSTRAP / 'promote-canonical-extgen.py'
    result = subprocess.run([sys.executable, str(script), '--check'], cwd=ROOT,
                            capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    promote = _load('extgen_snapshot', script)
    files = promote.collect_existing()
    assert files and f'from {len(files)} sources' in result.stdout
    assert not (ROOT / 'generators/code/defscodegen/intf/canonical-bootstrap-extgen.json').exists()


def test_persistent_read_contract_roles_are_checked_not_just_hashes():
    """A rehashed bad snapshot must still fail if common inherits JSON DO."""
    promote = _load('extgen_read_roles', BOOTSTRAP / 'promote-canonical-extgen.py')
    files = promote._existing()
    promote._validate(files)
    import pytest
    for technology, filename in (
            ('java', 'AIigType_1.java'), ('python', 'aiig_type_1.py')):
        matches = [p for p in files if '/'+technology+'.extgen/' in p
                   and p.endswith('/'+filename)]
        assert len(matches) == 1, matches
        name = matches[0]
        actual = files[name]
        assert b'AIiJsonDataObject' not in actual
        tampered = dict(files)
        tampered[name] = actual.replace(b'AIiDataObject', b'AIiJsonDataObject')
        assert tampered[name] != actual
        with pytest.raises(RuntimeError, match='Obsolete DataObject'):
            promote._validate(tampered)


def test_bootstrap_cleanup_never_removes_extgen(tmp_path):
    cleaner = _load('persistent_clean_generated', BOOTSTRAP / 'clean_generated.py')
    src = tmp_path / 'artifact/src/product'
    for suffix in ('python.gen', 'java.gen', 'python.extgen', 'java.extgen'):
        folder = src / suffix
        folder.mkdir(parents=True)
        (folder / 'marker.txt').write_text(suffix)
    cleaner.clean(tmp_path, tmp_path)
    assert not (src / 'python.gen/marker.txt').exists()
    assert not (src / 'java.gen/marker.txt').exists()
    assert (src / 'python.extgen/marker.txt').read_text() == 'python.extgen'
    assert (src / 'java.extgen/marker.txt').read_text() == 'java.extgen'


def test_native_defs_cli_imports_with_only_non_gen_python_roots():
    checkouts = (ROOT, ROOT.parent / 'pub.lib.General')
    directories = [str(d) for repo in checkouts if repo.is_dir()
                   for suffix in ('python', 'python.extgen')
                   for d in repo.rglob('src/product/' + suffix)]
    script = ('import sys; sys.path[:0] = ' + repr(directories) + '\n'
              'from eu.algites.tool.codegen.defs.impl.cli.canonical_defs_codegen_cli import main\n'
              'from eu.algites.tool.codegen.defs.impl.standard.canonical_generated_model import AIcgdType_1\n'
              'assert ".model.impl." in AIcgdType_1.__module__\n')
    result = subprocess.run([sys.executable, '-c', script], cwd=ROOT,
                            env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'},
                            capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr


def test_canonical_first_stage_uses_native_cli_and_both_naming_roles():
    """Canonical first stage must select only this schema via the native CLI."""
    sys.path.insert(0, str(BOOTSTRAP))
    from codegen_settings import defs_settings, setting
    stage = _load('canonical_first_stage_roles', BOOTSTRAP / 'generate-canonical-contracts.py')
    options = stage.canonical_arguments(ROOT, check=True)
    assert '--check' in options
    for language in ('java', 'python'):
        selected = ';'.join(schema.as_posix() for schema in stage.CANONICAL_SCHEMAS.values())
        assert (f'--defs-input-paths:{language}=' + selected) in options
        settings = defs_settings(ROOT, language)
        key = f'dointf-naming-convention:{language}'
        assert f'--{key}=' + setting(settings, key) in options
    assert all('/old/' not in option and 'defs.old' not in option for option in options)


def test_enum_is_selected_by_existing_cli_settings_not_compiler_prefix():
    sys.path.insert(0, str(BOOTSTRAP))
    from codegen_settings import defs_settings, setting, filename_composition
    naming = (ROOT.parent / 'pub.lib.General/naming/convention/profile/algites/'
              'src/product/config/eu/algites/lib/naming/convention/sourcecode')
    for language in ('java', 'python'):
        selected = setting(defs_settings(ROOT, language),
                           f'output-enum-technology-naming-convention:{language}')
        file_id = filename_composition(naming / f'algites-{language}-name-conventions.yml',
                                       selected)
        assert selected and file_id and selected != file_id


def test_filename_composition_rejects_duplicate_names_and_kinds(tmp_path):
    """Bootstrap must reject ambiguous serialized profile identities and roles."""
    import yaml
    import pytest
    sys.path.insert(0, str(BOOTSTRAP))
    from codegen_settings import filename_composition

    def write(entries):
        path = tmp_path / 'catalog.yml'
        path.write_text(yaml.safe_dump({
            'SourceStructureNameConventions': {'NameConventions': {
                'NameConvention': entries}}}), encoding='utf-8')
        return path

    entry = {'name': 'example_1', 'StructureNaming': {'Rule': [
        {'kind': 'file_name_stem', 'Value': 'example-stem'}]}}
    assert filename_composition(write([entry]), 'example_1') == 'example-stem'
    with pytest.raises(ValueError, match='duplicate name'):
        filename_composition(write([entry, entry]), 'example_1')
    duplicate_role = {'name': 'example_1', 'StructureNaming': {'Rule': [
        {'kind': 'file_name_stem', 'Value': 'first'},
        {'kind': 'file_name_stem', 'Value': 'second'}]}}
    with pytest.raises(ValueError, match='duplicate kind'):
        filename_composition(write([duplicate_role]), 'example_1')
    with pytest.raises(ValueError, match='missing convention'):
        filename_composition(write([entry]), 'unknown')


def test_python_artifact_stager_includes_extgen(tmp_path):
    sys.path.insert(0, str(BOOTSTRAP))
    from prepare import stage_one_python
    fake = {'artifactId': 'test-bootstrap-impl',
            'path': 'generators/code/defscodegen/impl',
            'pythonName': 'test-bootstrap-impl', 'description': 'test',
            'pythonRequires': '>=3.12', 'pythonDependencies': []}
    staged = stage_one_python(ROOT, tmp_path, fake, '1.1.dev0')
    assert (staged / 'src/eu/algites/tool/codegen/defs/model/impl'
            '/aicgd_type_1.py').is_file()


def test_canonical_extgen_has_identical_java_python_contract_coverage():
    """Each language owns identical Defs read contracts and SDO source pairs."""
    promote = _load('extgen_coverage', BOOTSTRAP / 'promote-canonical-extgen.py')
    files = set(promote.collect_existing())
    for technology, suffix in (('java', '.java'), ('python', '.py')):
        read_base = ('generators/code/defscodegen/intf/src/product/'
                     + technology + '.extgen/')
        impl_base = ('generators/code/defscodegen/impl/src/product/'
                     + technology + '.extgen/')
        read = [name for name in files if name.startswith(read_base) and name.endswith(suffix)]
        sdo = [name for name in files if name.startswith(impl_base) and name.endswith(suffix)]
        # Bootstrap coverage grows with its schema; the provenance validator
        # enforces the real read/SDO identity pairing, not a historical count.
        assert read and sdo and len(sdo) % 2 == 0
        if technology == 'java':
            assert any(name.rsplit('/', 1)[-1].startswith('AIng') for name in read)
            assert sum('/impl/intf/' in name for name in sdo) == len(sdo) // 2
            assert sum('/impl/AIc' in name for name in sdo) == len(sdo) // 2
        else:
            assert any(name.rsplit('/', 1)[-1].startswith('aing_') for name in read)
            assert sum('/impl/intf/' in name for name in sdo) == len(sdo) // 2
            assert sum('/impl/aic' in name for name in sdo) == len(sdo) // 2


def test_python_read_contract_extgen_belongs_to_intf_artifact(tmp_path):
    """Keep persistent bootstrap read interfaces separate from SDO implementations.

    The native source-generation stage currently writes fresh SDO sources to the
    selected artifact's ``python.gen`` tree.  That does not change ownership of
    the persistent ``defs/model`` snapshot: its read-only interfaces
    belong to ``intf`` and implementations remain in ``impl`` ``*.extgen``.
    """
    sys.path.insert(0, str(BOOTSTRAP))
    from prepare import stage_one_python
    contract = {'artifactId': 'test-bootstrap-intf',
                'path': 'generators/code/defscodegen/intf',
                'pythonName': 'test-bootstrap-intf', 'description': 'test',
                'pythonRequires': '>=3.12', 'pythonDependencies': []}
    staged = stage_one_python(ROOT, tmp_path, contract, '1.1.dev0')
    persistent = staged / 'src/eu/algites/tool/codegen/defs/model'
    assert (persistent / 'aiig_type_1.py').is_file()
    assert not list(persistent.rglob('aicgd*.py'))
    assert not list(persistent.rglob('aiigd*.py'))


def test_promotion_does_not_relocate_or_transform_generated_sources():
    """Bootstrap promotion copies generated bytes without namespace rewriting."""
    promote = _load('symmetrical_promote', BOOTSTRAP / 'promote-canonical-extgen.py')
    assert not hasattr(promote, 'relocate')
    source = (ROOT / 'generators/code/defscodegen/intf/src/product/java.gen/'
              'eu/algites/tool/codegen/defs/model/AIigElement_1.java')
    target = (ROOT / 'generators/code/defscodegen/intf/src/product/java.extgen/'
              'eu/algites/tool/codegen/defs/model/AIigElement_1.java')
    assert source.read_bytes() == target.read_bytes()


def test_canonical_bootstrap_uses_format_local_identity_and_neutral_counts():
    """No legacy schema IDs or occurrence-specific names leak into bootstrap APIs."""
    from importlib.machinery import SourceFileLoader
    normalize = SourceFileLoader('canonical_metadata_adapter', str(
        BOOTSTRAP / 'normalize-canonical-bootstrap.py')).load_module().normalize
    for language, suffix in (('java', '.java'), ('python', '.py')):
        for artifact in ('intf', 'impl'):
            root = (ROOT / 'generators/code/defscodegen' / artifact / 'src/product'
                    / (language + '.extgen'))
            for source in root.rglob('*' + suffix):
                data = source.read_text(encoding='utf-8')
                assert not any(old in data for old in ('min_occurs', 'max_occurs',
                    'MinOccurs', 'MaxOccurs', 'MIN_OCCURS', 'MAX_OCCURS')), source
                if language == 'java':
                    assert not __import__('re').search(
                        r'@eu\.algites\.lib\.data\.dataobject\.AIaDataObject\([^\n]*(schemaId|schemaVersion|schemaUrl|fingerprint|namingConvention)', data), source
                else:
                    assert not __import__('re').search(
                        r'__data_object__\s*=\s*AIcdDataObject\([^\n]*(schema_id|schema_version|schema_url|fingerprint|naming_convention)', data), source
                    assert normalize(data, language) == data, source


def test_canonical_bootstrap_normalizer_is_deterministic():
    """The first-stage adapter preserves schema identity without legacy fields."""
    from importlib.machinery import SourceFileLoader
    normalize = SourceFileLoader('canonical_metadata_adapter_determinism', str(
        BOOTSTRAP / 'normalize-canonical-bootstrap.py')).load_module().normalize
    source = ("from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject\n"
              "class A:\n"
              "    __data_object__ = AIcdDataObject(schema_id='canonical#/$defs/Type', "
              "title='T', naming_convention='algites')\n")
    output = normalize(source, 'python')
    assert "AIcdDataObject(title='T')" in output
    assert "AIaDataObjectJsonSchema(schema_id='canonical#/$defs/Type')" in output
    assert normalize(output, 'python') == output




