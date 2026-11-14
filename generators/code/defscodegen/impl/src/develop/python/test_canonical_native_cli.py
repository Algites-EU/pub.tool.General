"""Native opt-in CLI tests with real Algites Java/Python naming catalogs."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

TOOL = next(p for p in Path(__file__).resolve().parents if p.name == 'pub.tool.General')
LIB = TOOL.parent / 'pub.lib.General'
sys.path.insert(0, str(LIB / 'naming/convention/impl/src/product/python'))
sys.path.insert(0, str(LIB / 'naming/convention/intf/src/product/python'))
sys.path.insert(0, str(LIB / 'naming/convention/intf/src/product/config'))
for location in ('generators/code/common/src/product/python',
                 'generators/code/defscodegen/intf/src/product/python',
                 'generators/code/defscodegen/impl/src/product/python',
                 'generators/code/defscodegen/cli/src/product/python'):
    sys.path.insert(0, str(TOOL / location))

from eu.algites.tool.codegen.defs.impl.cli.canonical_defs_codegen_cli import _execute_manifests, prepare, publish, _coalesce_equivalent_enum_sources


def _run_private_batches(arguments: list[str]) -> int:
    """Exercise the compiler-private batches, not the public qualified CLI.

    The production entry point no longer accepts ``--manifest``; these older
    canonical frontend/linker/emitter scenarios still need their exact batch
    fixtures for targeted regression coverage.
    """
    manifests: list[Path] = []
    check = False
    iterator = iter(arguments)
    for argument in iterator:
        if argument == '--manifest':
            manifests.append(Path(next(iterator)))
        elif argument == '--check':
            check = True
        else:
            raise ValueError(f'Unexpected private test batch argument: {argument}')
    return _execute_manifests(manifests, check=check)


def _manifest(tmp_path):
    """Write one independent input and fully specified real naming selection."""
    root = tmp_path / 'repo'
    inputs = root / 'intf/src/product/jsondefs/example/api'
    inputs.mkdir(parents=True)
    (inputs / 'records_1.jsondef.schema.json').write_text(json.dumps({
        '$id': 'urn:records', '$defs': {
            'Node': {'type': 'object', 'properties': {
                'Value': {'type': 'integer'}, 'next': {'$ref': '#/$defs/Node'}}},
            'Status': {'type': 'string', 'enum': ['ready', 'on-hold']}}}))
    common = TOOL / 'generators/code/profile/algites/src/product/config/eu/algites/lib/naming/convention/sourcecode'
    external = LIB / 'naming/convention/profile/algites/src/product/config/eu/algites/lib/naming/convention/sourcecode'
    schema = TOOL / ('generators/code/defscodegen/intf/src/product/jsondefs/eu/algites/'
                     'tool/codegen/defs/model/canonical-model_1.jsondef.schema.json')
    profiles = {}
    compositions = {}
    for target in ('java', 'python'):
        profiles[target] = {
            'common_file': str(common / f'algites-{target}-common-codegen-conventions.yml'),
            'common_id': f'algites-{target}-codegen-common_1',
            'defs_file': str(common / f'algites-{target}-defs-codegen-conventions.yml'),
            'defs_id': f'algites-{target}-defscodegen-standard_1',
            'sourcecode_catalog': str(external / f'algites-{target}-name-conventions.yml')}
        compositions[target] = {
            'interface': f'algites-{target}-gen-intf-versioned_1',
            'interface_file': f'algites-{target}-gen-intf-versioned-file_1',
            'common_interface': f'algites-{target}-gen-intf-versioned_1',
            'common_interface_file': f'algites-{target}-gen-intf-versioned-file_1',
            'enum': f'algites-{target}-gen-enum-versioned_1',
            'enum_file': f'algites-{target}-gen-enum-versioned-file_1'}
    data = {'repository_root': str(root), 'inputs': [{'kind': 'jsondefs',
        'path': 'intf/src/product/jsondefs/example/api/records_1.jsondef.schema.json'}],
        'profiles': profiles, 'canonical_schema': str(schema),
        'output_compositions': compositions,
        'output_dirs': {'java': 'intf/src/product/java.gen',
                        'python': 'intf/src/product/python.gen'},
        'package_name': 'example.api', 'versions': {'*': '1'},
        'input_naming': {kind: {'catalog': str(external / f'algites-{kind.removesuffix("s")}-name-conventions.yml'),
                                'profile': f'algites-{kind.removesuffix("s")}-schema-versioned_1'}
                         for kind in ('jsondefs', 'yamldefs', 'xmldefs')}}
    manifest = tmp_path / 'canonical.json'
    manifest.write_text(json.dumps(data, indent=2))
    return manifest, root


def test_real_naming_catalog_cli_runs_and_checks_all_outputs(tmp_path):
    manifest, root = _manifest(tmp_path)
    assert _run_private_batches(['--manifest', str(manifest)]) == 0
    assert _run_private_batches(['--manifest', str(manifest), '--check']) == 0
    java_dir = root / 'intf/src/product/java.gen/example/api'
    python_dir = root / 'intf/src/product/python.gen/example/api'
    java_files = sorted(java_dir.glob('*.java'))
    py_files = sorted(python_dir.glob('*.py'))
    assert len(java_files) == len(py_files) == 2
    assert (java_dir / 'AIigNode_1.java').is_file()
    assert not (java_dir / 'AIigNode_1.java').exists()
    node = (java_dir / 'AIigNode_1.java').read_text()
    assert '@eu.algites.lib.data.dataobject.jsonschema.AIaDataObjectJsonSchema(' in node
    assert (python_dir / 'aiig_node_1.py').is_file()
    assert 'getValue()' in (java_dir / 'AIigNode_1.java').read_text()
    assert 'def setNext' not in (python_dir / 'aiig_node_1.py').read_text()
    for path in py_files:
        compile(path.read_text(), str(path), 'exec')
    result = subprocess.run(['javac', '-sourcepath', str(LIB / 'data/dataobject/intf/src/product/java'), '-d', str(tmp_path / 'classes'),
                            *map(str, java_files)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    state = root / 'build/defscodegen/generated-files.json'
    assert len(json.loads(state.read_text())) == 4


@pytest.mark.parametrize('kind,extension', [
    ('jsondefs', 'jsondef.schema.json'),
    ('yamldefs', 'yamldef.schema.json'),
])
def test_root_identity_is_composed_from_filename_not_schema_title(tmp_path, kind, extension):
    """Root type and version come from selected input naming catalog, never title."""
    manifest, root = _manifest(tmp_path)
    config = json.loads(manifest.read_text())
    source = root / f'intf/src/product/{kind}/example/api/common-naming-conventions_3.{extension}'
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(json.dumps({
        '$id': f'https://example.org/{kind}/common-naming-conventions_3.{extension}',
        'title': 'Shared naming convention tools',
        'x-algites-schema-version': 3,
        'type': 'object', 'properties': {'Identifier': {'type': 'string'}}
    }))
    config['inputs'] = [{'kind': kind, 'path': source.relative_to(root).as_posix()}]
    config['versions'] = {}
    # Input source naming remains schema-specific; output contracts never do.
    for language in ('java', 'python'):
        assert config['output_compositions'][language]['interface'] == (
            f'algites-{language}-gen-intf-versioned_1')
    manifest.write_text(json.dumps(config))
    assert _run_private_batches(['--manifest', str(manifest)]) == 0
    assert _run_private_batches(['--manifest', str(manifest), '--check']) == 0
    java_path = root / 'intf/src/product/java.gen/example/api/AIigCommonNamingConventions_3.java'
    python_path = root / 'intf/src/product/python.gen/example/api/aiig_common_naming_conventions_3.py'
    assert java_path.is_file() and python_path.is_file()
    assert 'schemaVersion = 3' in java_path.read_text()
    assert 'SharedNamingConventionTools' not in java_path.read_text()
    assert not list(java_path.parent.glob('AIig_[jxy]CommonNamingConventions_3.java'))
    assert not list(python_path.parent.glob('aiig__[jxy]_common_naming_conventions_3.py'))



@pytest.mark.parametrize('kind,extension', [
    ('jsondefs', 'jsondef.schema.json'),
    ('yamldefs', 'yamldef.schema.json'),
])
def test_filename_version_propagates_to_synthetic_types(tmp_path, kind, extension):
    """Embedded canonical declarations must not revert to the manifest wildcard."""
    manifest, root = _manifest(tmp_path)
    config = json.loads(manifest.read_text())
    source = root / f'intf/src/product/{kind}/example/api/nested-example_4.{extension}'
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(json.dumps({'type': 'object', 'title': 'Incorrect title',
        'properties': {'child': {'type': 'object', 'properties': {
            'value': {'type': 'string', 'minLength': 1}}}}}))
    config['inputs'] = [{'kind': kind, 'path': source.relative_to(root).as_posix()}]
    config['versions'] = {}
    manifest.write_text(json.dumps(config))
    assert _run_private_batches(['--manifest', str(manifest)]) == 0
    java_files = list((root / 'intf/src/product/java.gen/example/api').glob('*.java'))
    python_files = list((root / 'intf/src/product/python.gen/example/api').glob('*.py'))
    assert len(java_files) == len(python_files) == 2
    assert all(path.stem.endswith('_4') for path in java_files)
    assert all(path.stem.endswith('_4') for path in python_files)


def test_xsd_declared_type_version_comes_from_input_filename(tmp_path):
    """Named XSD types use the same source filename version as JSON/YAML."""
    manifest, root = _manifest(tmp_path)
    config = json.loads(manifest.read_text())
    path = root / 'intf/src/product/xmldefs/example/api/xml-example_7.xsd'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("""<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
      <xs:complexType name="CommonNamingConventions"><xs:sequence>
        <xs:element name="value" type="xs:string"/>
      </xs:sequence></xs:complexType>
    </xs:schema>""")
    config['inputs'] = [{'kind': 'xmldefs', 'path': path.relative_to(root).as_posix()}]
    config['versions'] = {}
    manifest.write_text(json.dumps(config))
    assert _run_private_batches(['--manifest', str(manifest)]) == 0
    assert _run_private_batches(['--manifest', str(manifest), '--check']) == 0
    java_file = root / 'intf/src/product/java.gen/example/api/AIigCommonNamingConventions_7.java'
    assert java_file.is_file()
    assert 'version: 7.' in java_file.read_text()
    assert (root / 'intf/src/product/python.gen/example/api/aiig_common_naming_conventions_7.py').is_file()


def test_existing_common_naming_schemas_have_one_catalog_derived_root():
    """Real published JSONDEFS/YAMLDEFS roots share the agreed local type name."""
    source = LIB / 'naming/convention/intf/src/product'
    naming = LIB / ('naming/convention/profile/algites/src/product/config/'
                    'eu/algites/lib/naming/convention/sourcecode')
    # The source-document root name is strictly an input-catalog product,
    # independent of a schema title or of any output language prefix.
    from eu.algites.lib.naming.convention.impl.standard.aic_name_convention_catalog import AIcNameConventionCatalog
    for kind in ('jsondefs', 'yamldefs'):
        stem = kind.removesuffix('s')
        extension = 'jsondef.schema.json' if kind == 'jsondefs' else 'yamldef.schema.json'
        filepath = source / kind / 'eu/algites/lib/naming/convention' / f'common-naming-conventions_1.{extension}'
        assert filepath.is_file()
        catalog = AIcNameConventionCatalog.load(naming / f'algites-{stem}-name-conventions.yml')
        chosen = f'algites-{stem}-schema-versioned_1'
        parsed = catalog.recognize_filename(filepath.name, {chosen})
        assert parsed and parsed.variables == {'identifier': 'common-naming-conventions', 'version': '1'}
        derived = catalog.format(chosen, 'type_name', parsed.variables,
                                 catalog.identifier_convention(chosen, 'file_name_stem'))
        assert derived == 'CommonNamingConventions'


def test_input_filename_version_must_match_declared_schema_version(tmp_path):
    manifest, root = _manifest(tmp_path)
    config = json.loads(manifest.read_text())
    file = root / config['inputs'][0]['path']
    file.write_text(json.dumps({'title': 'Wrong name', 'type': 'object',
        'x-algites-schema-version': 2}))
    with pytest.raises(ValueError, match='records_1.*x-algites-schema-version'):
        prepare(manifest)


def test_native_check_is_non_mutating_and_tampering_is_rejected(tmp_path):
    manifest, root = _manifest(tmp_path)
    with pytest.raises(ValueError, match='[Oo]utdated|incomplete'):
        _run_private_batches(['--manifest', str(manifest), '--check'])
    assert not (root / 'build/defscodegen/generated-files.json').exists()
    assert _run_private_batches(['--manifest', str(manifest)]) == 0
    generated = root / 'intf/src/product/java.gen/example/api/AIigNode_1.java'
    generated.write_text('changed outside generator')
    with pytest.raises(ValueError, match='modified outside Codegen|modified independently'):
        _run_private_batches(['--manifest', str(manifest)])
    assert generated.read_text() == 'changed outside generator'


def test_native_cli_rejects_outside_output_and_unknown_schema_semantics(tmp_path):
    manifest, root = _manifest(tmp_path)
    document = json.loads(manifest.read_text())
    document['output_dirs']['java'] = '../elsewhere'
    manifest.write_text(json.dumps(document))
    with pytest.raises(ValueError, match='escapes|generated-source'):
        prepare(manifest)
    document['output_dirs']['java'] = 'intf/src/product/java.gen'
    manifest.write_text(json.dumps(document))
    inputfile = root / 'intf/src/product/jsondefs/example/api/records_1.jsondef.schema.json'
    schema = json.loads(inputfile.read_text())
    schema['$defs']['Node']['properties']['Value']['pattern'] = '^x$'
    inputfile.write_text(json.dumps(schema))
    with pytest.raises(ValueError, match='records_1.jsondef.schema.json.*pattern') as failure:
        prepare(manifest)
    assert isinstance(failure.value.__cause__, NotImplementedError)
    assert not (root / 'intf/src/product/java.gen').exists()


def test_native_cli_compiles_sealed_scalar_choice_with_real_catalogs(tmp_path):
    """Only explicit structural choice emits Java sealed variants."""
    manifest, root = _manifest(tmp_path)
    config = json.loads(manifest.read_text())
    choice = root / 'intf/src/product/jsondefs/example/api/choice_1.jsondef.schema.json'
    choice.write_text(json.dumps({'$id': 'urn:choice', 'title': 'Select',
        'type': 'object', 'x-algites-defscodegen-choice': True,
        'properties': {'text': {'type': 'string'}, 'number': {'type': 'integer'}},
        'minProperties': 1, 'maxProperties': 1, 'additionalProperties': False}))
    config['inputs'].append({'kind': 'jsondefs',
                            'path': choice.relative_to(root).as_posix()})
    manifest.write_text(json.dumps(config))
    assert _run_private_batches(['--manifest', str(manifest)]) == 0
    assert _run_private_batches(['--manifest', str(manifest), '--check']) == 0
    files = list((root / 'intf/src/product/java.gen/example/api').glob('*.java'))
    assert len(files) == 5
    parents = [path for path in files if 'sealed interface' in path.read_text()]
    assert len(parents) == 1
    children = [path for path in files if 'record ' in path.read_text()]
    assert len(children) == 2
    result = subprocess.run(['javac', '-sourcepath', str(LIB / 'data/dataobject/intf/src/product/java'), '-d', str(tmp_path / 'classes'),
                             *map(str, files)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_native_cli_valid_xmldefs_and_yamldefs_round_trip(tmp_path):
    """Use the same canonical emitter for independent XML and YAML declarations."""
    manifest, root = _manifest(tmp_path)
    config = json.loads(manifest.read_text())
    yaml_path = root / 'intf/src/product/yamldefs/example/api/yaml_1.yamldef.schema.json'
    yaml_path.parent.mkdir(parents=True)
    yaml_path.write_text(json.dumps({'$id': 'urn:yaml', 'title': 'YamlThing',
        'type': 'object', 'properties': {'count': {'type': 'integer'}}}))
    xsd_path = root / 'intf/src/product/xmldefs/example/api/xml_1.xsd'
    xsd_path.parent.mkdir(parents=True)
    xsd_path.write_text('''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
       <xs:complexType name="XmlThing"><xs:sequence>
         <xs:element name="Label" type="xs:string"/>
       </xs:sequence></xs:complexType></xs:schema>''')
    config['inputs'].extend([
        {'kind': 'yamldefs', 'path': yaml_path.relative_to(root).as_posix()},
        {'kind': 'xmldefs', 'path': xsd_path.relative_to(root).as_posix()}])
    manifest.write_text(json.dumps(config))
    assert _run_private_batches(['--manifest', str(manifest)]) == 0
    assert _run_private_batches(['--manifest', str(manifest), '--check']) == 0
    java_files = list((root / 'intf/src/product/java.gen/example/api').glob('*.java'))
    assert len(java_files) == 4
    xml_meta = LIB / 'data/dataobject/intf/src/product/java/eu/algites/lib/data/dataobject/xmldefs'
    result = subprocess.run(['javac', '-sourcepath', str(LIB / 'data/dataobject/intf/src/product/java'), '-d', str(tmp_path / 'classes'),
                             *map(str, java_files),
                             str(xml_meta / 'AIaXmlDataObjectField.java'),
                             str(xml_meta / 'AInXmlValueKind.java')], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_native_cli_compiles_structured_choice_and_preserves_ownership(tmp_path):
    """Mixed object/scalar exclusive alternatives survive real naming and --check."""
    manifest, root = _manifest(tmp_path)
    config = json.loads(manifest.read_text())
    choice = root / 'intf/src/product/jsondefs/example/api/choice_1.jsondef.schema.json'
    choice.write_text(json.dumps({'$id': 'urn:choice', 'title': 'Select',
        'type': 'object', 'x-algites-defscodegen-choice': True,
        'properties': {'person': {'type': 'object', 'properties': {
            'name': {'type': 'string'}, 'age': {'type': 'integer'}},
            'required': ['name']}, 'number': {'type': 'integer'}},
        'minProperties': 1, 'maxProperties': 1, 'additionalProperties': False}))
    config['inputs'].append({'kind': 'jsondefs',
                            'path': choice.relative_to(root).as_posix()})
    manifest.write_text(json.dumps(config))
    assert _run_private_batches(['--manifest', str(manifest)]) == 0
    assert _run_private_batches(['--manifest', str(manifest), '--check']) == 0
    java_files = list((root / 'intf/src/product/java.gen/example/api').glob('*.java'))
    py_files = list((root / 'intf/src/product/python.gen/example/api').glob('*.py'))
    assert len(java_files) == len(py_files) == 5
    structured = [path.read_text() for path in java_files if 'record ' in path.read_text()
                  and 'getName()' in path.read_text()]
    assert len(structured) == 1
    assert all('getAge()' in source for source in structured)
    assert all('requireNonNull' in source for source in structured)
    assert any('def getAge(self) -> int | None' in path.read_text() for path in py_files)
    result = subprocess.run(['javac', '-sourcepath', str(LIB / 'data/dataobject/intf/src/product/java'), '-d', str(tmp_path / 'classes'),
                             *map(str, java_files)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_native_cli_preserves_unbounded_integer_and_boolean_enum_codes(tmp_path):
    """End-to-end, exact numeric codes use BigInteger/int and Boolean/bool."""
    manifest, root = _manifest(tmp_path)
    config = json.loads(manifest.read_text())
    numeric = root / 'intf/src/product/jsondefs/example/api/numeric_1.jsondef.schema.json'
    numeric.write_text(json.dumps({'$id': 'urn:enumerations', '$defs': {
        'BigCode': {'type': 'integer', 'enum': [123456789012345678901234567890, -9]},
        'Switch': {'type': 'boolean', 'enum': [True, False]}}}))
    config['inputs'].append({'kind': 'jsondefs',
                            'path': numeric.relative_to(root).as_posix()})
    manifest.write_text(json.dumps(config))
    assert _run_private_batches(['--manifest', str(manifest)]) == 0
    assert _run_private_batches(['--manifest', str(manifest), '--check']) == 0
    java_dir = root / 'intf/src/product/java.gen/example/api'
    py_dir = root / 'intf/src/product/python.gen/example/api'
    assert 'java.math.BigInteger code()' in (java_dir / 'AIngBigCode_1.java').read_text()
    assert 'Boolean code()' in (java_dir / 'AIngSwitch_1.java').read_text()
    assert '= 123456789012345678901234567890' in (py_dir / 'aing_big_code_1.py').read_text()
    assert '= True' in (py_dir / 'aing_switch_1.py').read_text()
    java_files = list(java_dir.glob('*.java'))
    result = subprocess.run(['javac', '-sourcepath', str(LIB / 'data/dataobject/intf/src/product/java'), '-d', str(tmp_path / 'classes'),
                             *map(str, java_files)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_publisher_rolls_back_partial_replace_and_preserves_ownership(tmp_path, monkeypatch):
    """A write failure after one replace must leave all old files byte-identical."""
    from eu.algites.tool.codegen.defs.impl.cli import canonical_defs_codegen_cli as cli
    manifest, root = _manifest(tmp_path)
    repository, old_outputs = prepare(manifest)
    publish(repository, old_outputs)
    files = {rel: (repository / rel).read_bytes() for rel in old_outputs}
    state = repository / 'build/defscodegen/generated-files.json'
    old_state = state.read_bytes()
    modified = {rel: value + '\n/* changed */\n' for rel, value in old_outputs.items()}
    to_fail = sorted(modified)[1]
    original_replace = cli.os.replace
    failed = False

    def fail_second_once(src, dest):
        nonlocal failed
        if not failed and Path(dest) == repository / to_fail:
            failed = True
            raise OSError('simulated replacement failure')
        return original_replace(src, dest)

    monkeypatch.setattr(cli.os, 'replace', fail_second_once)
    with pytest.raises(OSError, match='simulated replacement'):
        publish(repository, modified)
    assert failed
    assert state.read_bytes() == old_state
    assert {rel: (repository / rel).read_bytes() for rel in files} == files
    assert not list(repository.rglob('tmp*'))
    assert publish(repository, old_outputs, check=True) == sorted(old_outputs)


def test_publisher_rolls_back_removed_files_when_manifest_write_fails(tmp_path, monkeypatch):
    """Even obsolete files deleted during commit must be restored on failure."""
    from eu.algites.tool.codegen.defs.impl.cli import canonical_defs_codegen_cli as cli
    manifest, root = _manifest(tmp_path)
    repository, old_outputs = prepare(manifest)
    publish(repository, old_outputs)
    files = {rel: (repository / rel).read_bytes() for rel in old_outputs}
    state = repository / 'build/defscodegen/generated-files.json'
    old_state = state.read_bytes()
    changed = dict(old_outputs)
    changed.pop(sorted(changed)[-1])
    changed[sorted(changed)[0]] += '\n/* changed */\n'
    original_replace = cli.os.replace
    failed = False

    def fail_manifest_once(src, dest):
        nonlocal failed
        if not failed and Path(dest) == state:
            failed = True
            raise OSError('simulated manifest failure')
        return original_replace(src, dest)

    monkeypatch.setattr(cli.os, 'replace', fail_manifest_once)
    with pytest.raises(OSError, match='simulated manifest'):
        publish(repository, changed)
    assert failed
    assert state.read_bytes() == old_state
    assert {rel: (repository / rel).read_bytes() for rel in files} == files
    assert publish(repository, old_outputs, check=True) == sorted(old_outputs)


def test_native_cli_xsd_direct_repeated_particle_compiles_and_checks(tmp_path):
    """An XSD maxOccurs=unbounded element emits an actual typed list contract."""
    manifest, root = _manifest(tmp_path)
    config = json.loads(manifest.read_text())
    file = root / 'intf/src/product/xmldefs/example/api/xml-collection_1.xsd'
    file.parent.mkdir(parents=True)
    file.write_text('''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
      <xs:complexType name="XmlOrder"><xs:sequence>
        <xs:element name="line" type="xs:string" minOccurs="0" maxOccurs="unbounded"/>
      </xs:sequence></xs:complexType>
    </xs:schema>''')
    config['inputs'].append({'kind': 'xmldefs', 'path': file.relative_to(root).as_posix()})
    manifest.write_text(json.dumps(config))
    assert _run_private_batches(['--manifest', str(manifest)]) == 0
    assert _run_private_batches(['--manifest', str(manifest), '--check']) == 0
    java_dir = root / 'intf/src/product/java.gen/example/api'
    python_dir = root / 'intf/src/product/python.gen/example/api'
    java = (java_dir / 'AIigXmlOrder_1.java').read_text()
    python = (python_dir / 'aiig_xml_order_1.py').read_text()
    assert 'java.util.List<? extends String> getLineList()' in java
    assert 'def getLineList(self) -> list[str]' in python
    generated = list(java_dir.glob('*.java'))
    assert len(generated) == 3
    meta = LIB / 'data/dataobject/intf/src/product/java/eu/algites/lib/data/dataobject/xmldefs'
    compiled = subprocess.run(['javac', '-sourcepath', str(LIB / 'data/dataobject/intf/src/product/java'), '-d', str(tmp_path / 'classes'),
                               *map(str, generated),
                               str(meta / 'AIaXmlDataObjectField.java'),
                               str(meta / 'AInXmlValueKind.java')], capture_output=True, text=True)
    assert compiled.returncode == 0, compiled.stderr


def test_native_cli_emits_bounded_xsd_list_with_item_constraints(tmp_path):
    """Native Defs CLI preserves XSD list bounds in the generated field metadata."""
    manifest, root = _manifest(tmp_path)
    config = json.loads(manifest.read_text())
    file = root / 'intf/src/product/xmldefs/example/api/xml-collection_1.xsd'
    file.parent.mkdir(parents=True)
    file.write_text('''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
      <xs:complexType name="XmlOrder"><xs:sequence>
        <xs:element name="line" type="xs:string" minOccurs="2" maxOccurs="5"/>
      </xs:sequence></xs:complexType>
    </xs:schema>''')
    config['inputs'].append({'kind': 'xmldefs', 'path': file.relative_to(root).as_posix()})
    manifest.write_text(json.dumps(config))
    assert _run_private_batches(['--manifest', str(manifest)]) == 0
    assert _run_private_batches(['--manifest', str(manifest), '--check']) == 0
    java_dir = root / 'intf/src/product/java.gen/example/api'
    python_dir = root / 'intf/src/product/python.gen/example/api'
    java = (java_dir / 'AIigXmlOrder_1.java').read_text()
    python = (python_dir / 'aiig_xml_order_1.py').read_text()
    assert 'minItemCount = 2, maxItemCount = 5' in java
    assert 'min_item_count=2, max_item_count=5' in python
    assert 'AIaDataObjectFieldListConstraints(minItems = 2, maxItems = 5)' in java
    assert 'AIaDataObjectFieldListConstraints(min_items=2, max_items=5)' in python


def test_native_cli_emits_and_checks_local_composite_xsd_indexes(tmp_path):
    """Use the real catalogs and production Java runtime interfaces for A/B keys."""
    from test_canonical_indexed_emission import XSD
    manifest, root = _manifest(tmp_path)
    config = json.loads(manifest.read_text())
    xsd_file = root / 'intf/src/product/xmldefs/example/api/staff_1.xsd'
    xsd_file.parent.mkdir(parents=True)
    xsd_file.write_text(XSD)
    config['inputs'].append({'kind': 'xmldefs', 'path': xsd_file.relative_to(root).as_posix()})
    manifest.write_text(json.dumps(config))
    assert _run_private_batches(['--manifest', str(manifest)]) == 0
    assert _run_private_batches(['--manifest', str(manifest), '--check']) == 0
    java_files = sorted((root / 'intf/src/product/java.gen/example/api').glob('*.java'))
    py_files = sorted((root / 'intf/src/product/python.gen/example/api').glob('*.py'))
    assert len(java_files) == len(py_files) == 6
    assert any('AIiMultiMappedList<' in path.read_text() for path in java_files)
    assert any('identity.code' in path.read_text() for path in py_files)
    dependencies = [
        LIB / 'common/util/src/product/java/eu/algites/lib/common/list/AIiMultiMappedList.java',
        LIB / 'common/util/src/product/java/eu/algites/lib/common/list/AIiKeyDefinition.java',
        LIB / 'data/dataobject/intf/src/product/java/eu/algites/lib/data/dataobject/AIaKeyDefinition.java',
        LIB / 'data/dataobject/intf/src/product/java/eu/algites/lib/data/dataobject/AIaKeyDefinitions.java',
        LIB / 'data/dataobject/intf/src/product/java/eu/algites/lib/data/dataobject/xmldefs/AIaXmlDataObjectField.java',
        LIB / 'data/dataobject/intf/src/product/java/eu/algites/lib/data/dataobject/xmldefs/AInXmlValueKind.java',
    ]
    outcome = subprocess.run(['javac', '-sourcepath', str(LIB / 'data/dataobject/intf/src/product/java'), '-d', str(tmp_path / 'classes'),
                              *map(str, java_files + dependencies)], capture_output=True, text=True)
    assert outcome.returncode == 0, outcome.stderr


def test_native_defs_readonly_contract_is_accepted_by_independent_python_sdo(tmp_path, monkeypatch):
    """Exercise Defs -> annotated AIig contract -> independent SDO CLI -> instance."""
    import importlib
    monkeypatch.syspath_prepend(str(TOOL / 'generators/code/sdocodegen/intf/src/product/config'))
    monkeypatch.syspath_prepend(str(TOOL / 'generators/code/profile/algites/src/product/config'))
    monkeypatch.syspath_prepend(str(LIB / 'naming/convention/profile/algites/src/product/config'))
    monkeypatch.syspath_prepend(str(LIB / 'naming/convention/intf/src/product/config'))
    from eu.algites.tool.codegen.sdo.impl.cli.aic_sdo_codegen_cli import main as sdo_main

    manifest, root = _manifest(tmp_path)
    assert _run_private_batches(['--manifest', str(manifest)]) == 0
    read_source = root / 'intf/src/product/python.gen/example/api/aiig_node_1.py'
    assert 'AIaDataObjectField' in read_source.read_text()
    assert 'def setValue' not in read_source.read_text()

    settings = TOOL / ('generators/code/profile/algites/src/product/config/eu/algites/'
                       'tool/codegen/sdo/algites-sdocodegen-python.settings')
    arguments = [f'--repository-root={root}',
                 '--sdo-input-paths:python=intf/src/product/python.gen',
                 '--technology-sdointf-output-dir:python=impl/src/product/python.gen',
                 '--technology-sdoimpl-output-dir:python=impl/src/product/python.gen',
                 '--dointf-input-classes:python=example.api.aiig_node_1:AIigNode_1',
                 '--sdointf-subpackage=impl.intf',
                 '--sdoclass-subpackage=impl']
    arguments.extend(line.strip() for line in settings.read_text().splitlines()
                     if line.startswith('--'))
    # The selected settings already contain the single schema-neutral SDO
    # input convention; technology-specific overrides are now invalid.
    assert sdo_main(arguments) == 0
    assert sdo_main(arguments + ['--check']) == 0

    generated_root = root / 'impl/src/product/python.gen'
    classes = sorted(generated_root.rglob('aic*.py'))
    assert len(classes) == 1
    import ast
    declaration = next(item for item in ast.parse(classes[0].read_text()).body
                       if isinstance(item, ast.ClassDef) and item.name.startswith('AIcgd'))
    sys.path.insert(0, str(generated_root))
    try:
        module_name = '.'.join(classes[0].relative_to(generated_root).with_suffix('').parts)
        implementation = getattr(importlib.import_module(module_name), declaration.name)
        instance = implementation()
        instance.setValue(42)
        assert instance.getValue() == 42
        assert instance.getRawValues()['Value'] == 42
        assert instance._metadata().getField('Value').getDataFieldName() == 'Value'
    finally:
        sys.path.remove(str(generated_root))


def test_native_xml_and_yaml_contracts_drive_independent_sdo(tmp_path, monkeypatch):
    """Both non-JSON frontends create annotated inputs usable by the SDO CLI."""
    import ast
    import importlib
    monkeypatch.syspath_prepend(str(TOOL / 'generators/code/sdocodegen/intf/src/product/config'))
    monkeypatch.syspath_prepend(str(TOOL / 'generators/code/profile/algites/src/product/config'))
    monkeypatch.syspath_prepend(str(LIB / 'naming/convention/profile/algites/src/product/config'))
    monkeypatch.syspath_prepend(str(LIB / 'naming/convention/intf/src/product/config'))
    from eu.algites.tool.codegen.sdo.impl.cli.aic_sdo_codegen_cli import main as sdo_main

    manifest, root = _manifest(tmp_path)
    configuration = json.loads(manifest.read_text())
    yaml_source = root / 'intf/src/product/yamldefs/example/api/settings_1.yamldef.schema.json'
    yaml_source.parent.mkdir(parents=True)
    yaml_source.write_text(json.dumps({'$id': 'urn:settings', 'title': 'YamlSettings',
                                       'type': 'object', 'properties': {'count': {'type': 'integer'}}}))
    xml_source = root / 'intf/src/product/xmldefs/example/api/element_1.xsd'
    xml_source.parent.mkdir(parents=True)
    xml_source.write_text('''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
        <xs:complexType name="XmlPerson"><xs:sequence>
        <xs:element name="Label" type="xs:string"/>
        </xs:sequence></xs:complexType></xs:schema>''')
    # Compile each source format using its actual representation naming role;
    # the compiler combines the three private batches into one common model.
    # A generic (format-neutral) interface must never pretend to provide XML IO.
    source_inputs = list(configuration['inputs'])
    batch_files = [manifest]
    for kind, source, role in (
            ('yamldefs', yaml_source, 'yaml'),
            ('xmldefs', xml_source, 'xml-type')):
        specific = json.loads(json.dumps(configuration))
        specific['inputs'] = [{'kind': kind, 'path': source.relative_to(root).as_posix()}]
        for language in ('java', 'python'):
            assert specific['output_compositions'][language]['interface'] == (
                f'algites-{language}-gen-intf-versioned_1')
        path = tmp_path / f'canonical-{kind}.json'
        path.write_text(json.dumps(specific))
        batch_files.append(path)
    configuration['inputs'] = source_inputs
    manifest.write_text(json.dumps(configuration))
    invocation = [arg for batch in batch_files for arg in ('--manifest', str(batch))]
    assert _run_private_batches(invocation) == 0
    settings = TOOL / ('generators/code/profile/algites/src/product/config/eu/algites/'
                       'tool/codegen/sdo/algites-sdocodegen-python.settings')
    arguments = [f'--repository-root={root}',
                 '--sdo-input-paths:python=intf/src/product/python.gen',
                 '--technology-sdointf-output-dir:python=impl/src/product/python.gen',
                 '--technology-sdoimpl-output-dir:python=impl/src/product/python.gen',
                 ('--dointf-input-classes:python=example.api.aiig_settings_1:AIigSettings_1;'
                  'example.api.aiig_xml_person_1:AIigXmlPerson_1'),
                 '--sdointf-subpackage=impl.intf', '--sdoclass-subpackage=impl']
    arguments.extend(line.strip() for line in settings.read_text().splitlines()
                     if line.startswith('--'))
    # One SDO implementation per read-only contract; formats are metadata
    # providers, not distinct generated SDO class hierarchies.
    assert sdo_main(arguments) == 0
    assert sdo_main(arguments + ['--check']) == 0

    generated_root = root / 'impl/src/product/python.gen'
    sys.path.insert(0, str(generated_root))
    try:
        files = sorted(generated_root.rglob('aic*.py'))
        assert files
        assert not any('__x_' in path.name or '__y_' in path.name
                       for path in files)
        for path in files:
            declaration = next(n for n in ast.parse(path.read_text()).body
                               if isinstance(n, ast.ClassDef) and n.name.startswith('AIcgd'))
            module = '.'.join(path.relative_to(generated_root).with_suffix('').parts)
            implementation = getattr(importlib.import_module(module), declaration.name)
            instance = implementation()
            if 'XmlPerson' in implementation.__name__:
                instance.setLabel('Mia')
                assert instance.getRawValues()['Label'] == 'Mia'
                assert instance._metadata().getField('Label').getDataFieldName() == 'Label'
            elif 'Settings' in implementation.__name__:
                instance.setCount(7)
                assert instance.getRawValues()['Count'] == 7
                assert instance._metadata().getField('Count').getDataFieldName() == 'count'
    finally:
        sys.path.remove(str(generated_root))




def test_multi_source_enum_merges_only_provenance_not_different_api():
    """Three schema technologies can share an enum class without losing origin."""
    def generated(identifier, member='READY'):
        return ('/**\n * Shared enum.\n'
                f' * <p>Generated from canonical definition sample#/{identifier}/1.'
                f' Source: schemas/{identifier}/status_1.schema#{identifier}.'
                ' Do not edit manually.</p>\n'
                ' * @author linhart1\n'
                ' */\npublic enum Shared { ' + member + ' }\n')
    combined = _coalesce_equivalent_enum_sources(generated('json'), generated('xml'),
                                                  'pkg/Shared.java')
    combined = _coalesce_equivalent_enum_sources(combined, generated('yaml'),
                                                  'pkg/Shared.java')
    assert 'sample#/json/1' in combined
    assert 'Equivalent enum schema: sample#/xml/1' in combined
    assert 'Equivalent enum schema: sample#/yaml/1' in combined
    with pytest.raises(ValueError, match='Conflicting Defs enum declarations'):
        _coalesce_equivalent_enum_sources(combined, generated('bad', 'BROKEN'), 'pkg/Shared.java')
    with pytest.raises(ValueError, match='Conflicting Defs outputs'):
        _coalesce_equivalent_enum_sources(combined, generated('same').replace('public enum', 'public class'),
                                          'pkg/Shared.java')


def test_published_json_root_url_is_independent_of_logical_schema_id(tmp_path):
    """External inheritance must locate the published root in both languages.

    A $defs contract belongs to the same *document*, but is not a second root
    eligible for URI-based inheritance. The logical schema ID must remain
    independent of the physical source document URI.
    """
    from eu.algites.tool.codegen.defs.impl.cli.canonical_defs_codegen_cli import (
        _existing_contracts,
    )
    manifest, root = _manifest(tmp_path)
    document = json.loads(manifest.read_text())
    source = root / document['inputs'][0]['path']
    published_url = 'https://example.org/contracts/record_1.jsondef.schema.json'
    source.write_text(json.dumps({
        '$id': published_url,
        'x-algites-schema-id': 'example.records',
        'x-algites-schema-version': 1,
        'title': 'Record',
        'type': 'object',
        'properties': {'Value': {'type': 'string'}},
        '$defs': {'Child': {'type': 'object', 'properties': {'Label': {'type': 'string'}}}},
    }))
    assert _run_private_batches(['--manifest', str(manifest)]) == 0
    java_root = (root / 'intf/src/product/java.gen/example/api/AIigRecords_1.java').read_text()
    python_root = (root / 'intf/src/product/python.gen/example/api/aiig_records_1.py').read_text()
    assert 'schemaId = "example.records"' in java_root
    assert f'schemaUrl = "{published_url}"' in java_root
    assert "schema_id='example.records'" in python_root
    assert f"schema_url='{published_url}'" in python_root
    assert 'schemaUrl = ' not in (root / 'intf/src/product/java.gen/example/api/AIigChild_1.java').read_text()
    assert 'schema_url=' not in (root / 'intf/src/product/python.gen/example/api/aiig_child_1.py').read_text()
    assert _existing_contracts((root,))[published_url] == {
        'java': 'example.api.AIigRecords_1',
        'python_module': 'example.api.aiig_records_1',
        'python_type': 'AIigRecords_1',
    }



def test_published_yaml_root_url_is_separate_from_schema_id(tmp_path):
    """YAMLDEFS has the same format-local identity contract as JSONDEFS."""
    manifest, root = _manifest(tmp_path)
    settings = json.loads(manifest.read_text())
    path = root / 'intf/src/product/yamldefs/example/api/profile_1.yamldef.schema.json'
    path.parent.mkdir(parents=True)
    uri = 'https://example.org/contracts/profile_1.yamldef.schema.json'
    path.write_text(json.dumps({
        '$id': uri, 'x-algites-schema-id': 'example.profile',
        'x-algites-schema-version': 1, 'title': 'Profile',
        'type': 'object', 'properties': {'Label': {'type': 'string'}},
    }))
    settings['inputs'] = [{'kind': 'yamldefs', 'path': path.relative_to(root).as_posix()}]
    # Source dialect changes metadata, never the public output naming role.
    manifest.write_text(json.dumps(settings))
    assert _run_private_batches(['--manifest', str(manifest)]) == 0
    java = (root / 'intf/src/product/java.gen/example/api/AIigProfile_1.java').read_text()
    python = (root / 'intf/src/product/python.gen/example/api/aiig_profile_1.py').read_text()
    assert 'schemaId = "example.profile"' in java
    assert f'schemaUrl = "{uri}"' in java
    assert "schema_id='example.profile'" in python
    assert f"schema_url='{uri}'" in python



def test_equivalent_enums_coalesce_across_xml_json_yaml_provenance():
    """The same public enum keeps distinct canonical XML and JSON identities.

    The canonical emitter documents schema identities, not the physical
    ``/xmldefs/`` and ``/jsondefs/`` source paths of the old backend.
    """
    package = TOOL / 'generators/code/defscodegen/intf/src/product'
    java = (package / 'java.gen/eu/algites/tool/codegen/defs/model/AIngElementKind_1.java').read_text()
    python_source = (package / 'python.gen/eu/algites/tool/codegen/defs/model/aing_element_kind_1.py').read_text()
    json_identity = 'eu.algites.tool.codegen.defs.model.canonical-model#/$defs/ElementKind'
    xml_identity = '{urn:algites:defs}ElementKind'
    for suffix, original in (('.java', java), ('.py', python_source)):
        assert json_identity in original
        source = original.replace(json_identity, xml_identity)
        if suffix == '.java':
            source = source.replace('Serialized field with a wire name (REFERENCED)',
                                    'Named serialized field (REFERENCED)')
            source = source.replace('Canonical enum value REFERENCED.', 'Wire value REFERENCED.')
        else:
            source = source.replace('Serialized field with a wire name (REFERENCED)',
                                    'Named serialized field (REFERENCED)')
        path = f'example/api/AIngElementKind_1{suffix}'
        forward = _coalesce_equivalent_enum_sources(original, source, path)
        reverse = _coalesce_equivalent_enum_sources(source, original, path)
        assert forward == reverse
        assert 'Equivalent schema identity:' in forward
        assert json_identity in forward and xml_identity in forward
        assert _coalesce_equivalent_enum_sources(forward, source, path) == forward
        if suffix == '.py':
            compile(forward, path, 'exec')
        else:
            assert 'public enum AIngElementKind_1' in forward


def test_enum_collision_rejects_different_values_and_versions():
    """Different enum wire codes or schema versions must never be coalesced."""
    source = (TOOL / 'generators/code/defscodegen/intf/src/product/java.gen/'
              'eu/algites/tool/codegen/defs/model/AIngElementKind_1.java').read_text()
    json_identity = 'eu.algites.tool.codegen.defs.model.canonical-model#/$defs/ElementKind'
    other_source = source.replace(json_identity, '{urn:algites:defs}ElementKind')
    assert 'EMBEDDED("EMBEDDED")' in other_source
    assert '; version: 1.' in other_source
    for conflicting in (
            other_source.replace('EMBEDDED("EMBEDDED")', 'EMBEDDED("OTHER")'),
            other_source.replace('; version: 1.', '; version: 2.')):
        with pytest.raises(ValueError, match='Conflicting Defs enum declarations|Conflicting Defs enum schema versions') as error:
            _coalesce_equivalent_enum_sources(source, conflicting, 'example/AIngElementKind_1.java')
        assert json_identity in str(error.value) and 'urn:algites:defs' in str(error.value)


def test_xml_and_json_same_named_enum_emit_single_common_source(tmp_path):
    """Actual XML/JSON emitters share an enum without unrelated object conflicts."""
    manifest, root = _manifest(tmp_path)
    xml = root / 'intf/src/product/xmldefs/example/api/records_1.xsd'
    xml.parent.mkdir(parents=True, exist_ok=True)
    xml.write_text('''<?xml version="1.0" encoding="utf-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
           targetNamespace="urn:records" version="1">
  <xs:simpleType name="Status"><xs:restriction base="xs:string">
    <xs:enumeration value="ready"/><xs:enumeration value="on-hold"/>
  </xs:restriction></xs:simpleType>
</xs:schema>''')
    conf = json.loads(manifest.read_text())
    # Isolate the enum. The full fixture also declares a recursive Node;
    # merging an XML Node with different fields must correctly fail and is
    # not relevant to enum identity/provenance handling.
    json_path = root / conf['inputs'][0]['path']
    json_schema = json.loads(json_path.read_text())
    json_schema['$defs'].pop('Node')
    json_path.write_text(json.dumps(json_schema))
    conf['inputs'] = [{'kind': 'xmldefs', 'path': xml.relative_to(root).as_posix()}]
    # XML emits the same schema-neutral nominal contract naming.
    xml_manifest = tmp_path / 'xml.json'
    xml_manifest.write_text(json.dumps(conf))
    assert _run_private_batches(['--manifest', str(manifest),
                                 '--manifest', str(xml_manifest)]) == 0
    assert _run_private_batches(['--manifest', str(xml_manifest),
                                 '--manifest', str(manifest), '--check']) == 0
    java = root / 'intf/src/product/java.gen/example/api/AIngStatus_1.java'
    python = root / 'intf/src/product/python.gen/example/api/aing_status_1.py'
    assert java.exists() and python.exists()
    assert 'Equivalent schema identity:' in java.read_text()
    assert 'Equivalent schema identity:' in python.read_text()
    assert len(list(java.parent.glob('AIngStatus_1.java'))) == 1
    assert len(list(python.parent.glob('aing_status_1.py'))) == 1
    compile(python.read_text(), str(python), 'exec')


def test_three_distinct_python_canonical_enum_origins_stay_stable():
    """Merged docstrings must remain parseable after each additional source."""
    initial = ('from enum import Enum\nclass Status(str, Enum):\n'
               '    """JSON enum.\n\n'
               '    Canonical identity: example#/$defs/Status; version: 1."""\n'
               '    READY = "ready"\n')
    xml = initial.replace('JSON enum.', 'XML enum.').replace(
        'example#/$defs/Status', '{urn:records}Status')
    yaml = initial.replace('JSON enum.', 'YAML enum.').replace(
        'example#/$defs/Status', 'example#/$defs/YamlStatus')
    path = 'example/status_1.py'
    first = _coalesce_equivalent_enum_sources(initial, xml, path)
    all_three = _coalesce_equivalent_enum_sources(first, yaml, path)
    reversed_order = _coalesce_equivalent_enum_sources(
        _coalesce_equivalent_enum_sources(yaml, xml, path), initial, path)
    assert all_three == reversed_order
    assert all_three.count('Equivalent schema identity:') == 2
    assert _coalesce_equivalent_enum_sources(all_three, yaml, path) == all_three
    compile(all_three, path, 'exec')


def test_real_canonical_elementkind_three_schema_enum_projection(tmp_path):
    """Regression for AIngElementKind_1 from the actual JSON/YAML/XSD schemas.

    The XML sample preserves the exact named XSD simpleType while omitting
    unrelated recursive structures, which are covered by separate tests.
    """
    import re
    import shutil
    manifest, root = _manifest(tmp_path)
    configuration = json.loads(manifest.read_text())
    xsd = (TOOL / 'generators/code/defscodegen/intf/src/product/xmldefs/'
           'eu/algites/tool/codegen/defs/model/canonical-model_1.xsd').read_text()
    elementkind = re.search(r'<xs:simpleType name="ElementKind">.*?</xs:simpleType>',
                            xsd, re.DOTALL).group()
    ns = re.search(r'targetNamespace="([^"]+)"', xsd).group(1)
    candidates = {'.java': [], '.py': []}
    for kind, extension in (('jsondefs', '.jsondef.schema.json'),
                            ('yamldefs', '.yamldef.schema.json'),
                            ('xmldefs', '.xsd')):
        relative = (f'intf/src/product/{kind}/eu/algites/tool/codegen/defs/'
                    f'model/canonical-model_1{extension}')
        source = root / relative
        source.parent.mkdir(parents=True, exist_ok=True)
        if kind == 'xmldefs':
            source.write_text('<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" '
                              f'targetNamespace="{ns}" version="1">\n'
                              + elementkind + '\n</xs:schema>')
        else:
            shutil.copy2(TOOL / ('generators/code/defscodegen/intf/src/product/'
                                 + kind + '/eu/algites/tool/codegen/defs/model/'
                                 + 'canonical-model_1' + extension), source)
        settings = json.loads(manifest.read_text())
        settings['inputs'] = [{'kind': kind, 'path': relative}]
        settings['package_name'] = 'eu.algites.tool.codegen.defs.model'
        # All three dialects share the same read-only output convention.
        batch = tmp_path / (kind + '.json')
        batch.write_text(json.dumps(settings))
        generated = prepare(batch)[1]
        for extension, typename in (('.java', 'AIngElementKind_1.java'),
                                    ('.py', 'aing_element_kind_1.py')):
            output = next(content for path, content in generated.items()
                          if path.endswith('/' + typename))
            candidates[extension].append(output)
    for extension, sources in candidates.items():
        path = 'eu/algites/tool/codegen/defs/model/AIngElementKind_1' + extension
        result = _coalesce_equivalent_enum_sources(
            _coalesce_equivalent_enum_sources(sources[0], sources[1], path),
            sources[2], path)
        reverse = _coalesce_equivalent_enum_sources(
            _coalesce_equivalent_enum_sources(sources[2], sources[1], path),
            sources[0], path)
        assert result == reverse
        assert 'Equivalent schema identity:' in result
        if extension == '.java':
            compiled = tmp_path / 'AIngElementKind_1.java'
            compiled.write_text(result)
            proc = subprocess.run(['javac', '-d', str(tmp_path / 'classes'), str(compiled)],
                                  capture_output=True, text=True)
            assert proc.returncode == 0, proc.stderr
        else:
            compile(result, path, 'exec')


def test_real_name_fragments_enum_merges_across_all_three_source_dialects(tmp_path):
    """All format representations inherit the same version for the shared enum.

    The JSON/YAML inline Kind enum and the named XML enum must not collide
    due to missing canonical provenance or a synthetic schema_version of ''.
    """
    import shutil
    from eu.algites.tool.codegen.defs.impl.cli import canonical_defs_codegen_cli as cli

    manifest, root = _manifest(tmp_path)
    originals = {}
    for kind, ext in (
            ('jsondefs', '.jsondef.schema.json'),
            ('yamldefs', '.yamldef.schema.json'),
            ('xmldefs', '.xsd')):
        relative = (f'naming/convention/intf/src/product/{kind}/'
                    f'eu/algites/lib/naming/convention/common-naming-conventions_1{ext}')
        source = LIB / relative
        if not source.exists():
            pytest.skip('pub.lib.General naming sources unavailable')
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        cfg = json.loads(manifest.read_text())
        cfg['inputs'] = [{'kind': kind, 'path': relative}]
        cfg['package_name'] = 'eu.algites.lib.naming.convention'
        # Every source dialect uses the same schema-neutral DataObject naming.
        # The source provenance of the enum remains distinct and is tested below.
        for language in ('java', 'python'):
            for role in ('interface', 'interface_file'):
                suffix = '-file_1' if role == 'interface_file' else '_1'
                cfg['output_compositions'][language][role] = (
                    f'algites-{language}-gen-intf-versioned{suffix}')
        test_manifest = tmp_path / f'{kind}.json'
        test_manifest.write_text(json.dumps(cfg))
        generated = prepare(test_manifest)[1]
        for name in ('AIngNameFragmentsSegmentValueKind_1.java',
                     'aing_name_fragments_segment_value_kind_1.py'):
            matches = [text for path, text in generated.items() if path.endswith(name)]
            assert len(matches) == 1, (kind, name)
            text = matches[0]
            assert cli._enum_provenance(text, python=name.endswith('.py'))
            originals[(kind, name)] = text

    for name in ('AIngNameFragmentsSegmentValueKind_1.java',
                 'aing_name_fragments_segment_value_kind_1.py'):
        merged = originals[('jsondefs', name)]
        for kind in ('yamldefs', 'xmldefs'):
            merged = _coalesce_equivalent_enum_sources(merged, originals[(kind, name)], name)
        assert 'NameFragmentsSegmentValueKind_1' in merged
        for wire_value in ('constant_string', 'identifier', 'version', 'variable'):
            assert wire_value in merged
