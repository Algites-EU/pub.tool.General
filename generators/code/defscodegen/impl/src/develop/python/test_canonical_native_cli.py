"""Native opt-in CLI tests with real Algites Java/Python naming catalogs."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

TOOL = next(p for p in Path(__file__).resolve().parents if p.name == 'pub.tool.General')
LIB = TOOL.parent / 'pub.lib.General'
for location in ('generators/code/common/src/product/python',
                 'generators/code/defscodegen/intf/src/product/python',
                 'generators/code/defscodegen/impl/src/product/python',
                 'generators/code/defscodegen/cli/src/product/python'):
    sys.path.insert(0, str(TOOL / location))

from eu.algites.tool.codegen.defs.impl.cli.canonical_defs_codegen_cli import main, prepare, publish


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
    common = TOOL / 'generators/code/profile/algites/src/product/config/eu/algites/tool/codegen'
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
            'enum': f'algites-{target}-gen-enum-versioned_1',
            'enum_file': f'algites-{target}-gen-enum-versioned-file_1'}
    data = {'repository_root': str(root), 'inputs': [{'kind': 'jsondefs',
        'path': 'intf/src/product/jsondefs/example/api/records_1.jsondef.schema.json'}],
        'profiles': profiles, 'canonical_schema': str(schema),
        'output_compositions': compositions,
        'output_dirs': {'java': 'intf/src/product/java.gen',
                        'python': 'intf/src/product/python.gen'},
        'package_name': 'example.api', 'versions': {'*': '1'}}
    manifest = tmp_path / 'canonical.json'
    manifest.write_text(json.dumps(data, indent=2))
    return manifest, root


def test_real_naming_catalog_cli_runs_and_checks_all_outputs(tmp_path):
    manifest, root = _manifest(tmp_path)
    assert main(['--manifest', str(manifest)]) == 0
    assert main(['--manifest', str(manifest), '--check']) == 0
    java_dir = root / 'intf/src/product/java.gen/example/api'
    python_dir = root / 'intf/src/product/python.gen/example/api'
    java_files = sorted(java_dir.glob('*.java'))
    py_files = sorted(python_dir.glob('*.py'))
    assert len(java_files) == len(py_files) == 2
    assert (java_dir / 'AIigNode_1.java').is_file()
    assert (python_dir / 'aiig_node_1.py').is_file()
    assert 'getValue()' in (java_dir / 'AIigNode_1.java').read_text()
    assert 'def setNext' not in (python_dir / 'aiig_node_1.py').read_text()
    for path in py_files:
        compile(path.read_text(), str(path), 'exec')
    result = subprocess.run(['javac', '-sourcepath', str(LIB / 'data/dataobject/intf/src/product/java'), '-d', str(tmp_path / 'classes'),
                            *map(str, java_files)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    state = root / 'build/run/canonical-defscodegen/generated-files.json'
    assert len(json.loads(state.read_text())) == 4


def test_native_check_is_non_mutating_and_tampering_is_rejected(tmp_path):
    manifest, root = _manifest(tmp_path)
    with pytest.raises(ValueError, match='outdated|incomplete'):
        main(['--manifest', str(manifest), '--check'])
    assert not (root / 'build').exists()
    assert main(['--manifest', str(manifest)]) == 0
    generated = root / 'intf/src/product/java.gen/example/api/AIigNode_1.java'
    generated.write_text('changed outside generator')
    with pytest.raises(ValueError, match='modified independently'):
        main(['--manifest', str(manifest)])
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
    with pytest.raises(NotImplementedError, match='pattern'):
        prepare(manifest)
    assert not (root / 'intf/src/product/java.gen').exists()


def test_native_cli_compiles_sealed_scalar_choice_with_real_catalogs(tmp_path):
    """A real oneOf input must produce Java sealed variants, not an open union."""
    manifest, root = _manifest(tmp_path)
    config = json.loads(manifest.read_text())
    choice = root / 'intf/src/product/jsondefs/example/api/choice_1.jsondef.schema.json'
    choice.write_text(json.dumps({'$id': 'urn:choice', 'title': 'Select',
        'oneOf': [{'type': 'string'}, {'type': 'integer'}]}))
    config['inputs'].append({'kind': 'jsondefs',
                            'path': choice.relative_to(root).as_posix()})
    manifest.write_text(json.dumps(config))
    assert main(['--manifest', str(manifest)]) == 0
    assert main(['--manifest', str(manifest), '--check']) == 0
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
    assert main(['--manifest', str(manifest)]) == 0
    assert main(['--manifest', str(manifest), '--check']) == 0
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
        'oneOf': [{'type': 'object', 'properties': {
            'name': {'type': 'string'}, 'age': {'type': 'integer'}},
            'required': ['name']}, {'type': 'integer'}]}))
    config['inputs'].append({'kind': 'jsondefs',
                            'path': choice.relative_to(root).as_posix()})
    manifest.write_text(json.dumps(config))
    assert main(['--manifest', str(manifest)]) == 0
    assert main(['--manifest', str(manifest), '--check']) == 0
    java_files = list((root / 'intf/src/product/java.gen/example/api').glob('*.java'))
    py_files = list((root / 'intf/src/product/python.gen/example/api').glob('*.py'))
    assert len(java_files) == len(py_files) == 5
    structured = [path.read_text() for path in java_files if 'record ' in path.read_text()
                  and 'getName()' in path.read_text()]
    assert len(structured) == 1
    assert 'getAge()' in structured[0]
    assert 'requireNonNull' in structured[0]
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
    assert main(['--manifest', str(manifest)]) == 0
    assert main(['--manifest', str(manifest), '--check']) == 0
    java_dir = root / 'intf/src/product/java.gen/example/api'
    py_dir = root / 'intf/src/product/python.gen/example/api'
    assert 'java.math.BigInteger code()' in (java_dir / 'AIngBigCode_1.java').read_text()
    assert 'Boolean code()' in (java_dir / 'AIngSwitch_1.java').read_text()
    assert 'VALUE_1 = 123456789012345678901234567890' in (py_dir / 'aing_big_code_1.py').read_text()
    assert 'VALUE_1 = True' in (py_dir / 'aing_switch_1.py').read_text()
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
    state = repository / 'build/run/canonical-defscodegen/generated-files.json'
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
    state = repository / 'build/run/canonical-defscodegen/generated-files.json'
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
    file = root / 'intf/src/product/xmldefs/example/api/xml_collection_1.xsd'
    file.parent.mkdir(parents=True)
    file.write_text('''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
      <xs:complexType name="XmlOrder"><xs:sequence>
        <xs:element name="line" type="xs:string" minOccurs="0" maxOccurs="unbounded"/>
      </xs:sequence></xs:complexType>
    </xs:schema>''')
    config['inputs'].append({'kind': 'xmldefs', 'path': file.relative_to(root).as_posix()})
    manifest.write_text(json.dumps(config))
    assert main(['--manifest', str(manifest)]) == 0
    assert main(['--manifest', str(manifest), '--check']) == 0
    java_dir = root / 'intf/src/product/java.gen/example/api'
    python_dir = root / 'intf/src/product/python.gen/example/api'
    java = next(path.read_text() for path in java_dir.glob('*.java') if 'getLine()' in path.read_text())
    python = next(path.read_text() for path in python_dir.glob('*.py') if 'getLine(self)' in path.read_text())
    assert 'java.util.List<String> getLine()' in java
    assert 'def getLine(self) -> list[str]' in python
    generated = list(java_dir.glob('*.java'))
    assert len(generated) == 3
    meta = LIB / 'data/dataobject/intf/src/product/java/eu/algites/lib/data/dataobject/xmldefs'
    compiled = subprocess.run(['javac', '-sourcepath', str(LIB / 'data/dataobject/intf/src/product/java'), '-d', str(tmp_path / 'classes'),
                               *map(str, generated),
                               str(meta / 'AIaXmlDataObjectField.java'),
                               str(meta / 'AInXmlValueKind.java')], capture_output=True, text=True)
    assert compiled.returncode == 0, compiled.stderr


def test_native_cli_rejects_bounded_xsd_list_without_publishing(tmp_path):
    """The whole batch fails when an XSD bound cannot be enforced in emitted API."""
    manifest, root = _manifest(tmp_path)
    config = json.loads(manifest.read_text())
    file = root / 'intf/src/product/xmldefs/example/api/xml_collection_1.xsd'
    file.parent.mkdir(parents=True)
    file.write_text('''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
      <xs:complexType name="XmlOrder"><xs:sequence>
        <xs:element name="line" type="xs:string" minOccurs="2" maxOccurs="5"/>
      </xs:sequence></xs:complexType>
    </xs:schema>''')
    config['inputs'].append({'kind': 'xmldefs', 'path': file.relative_to(root).as_posix()})
    manifest.write_text(json.dumps(config))
    with pytest.raises(NotImplementedError, match='Bounded LIST'):
        main(['--manifest', str(manifest)])
    assert not (root / 'intf/src/product/java.gen').exists()
    assert not (root / 'intf/src/product/python.gen').exists()


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
    assert main(['--manifest', str(manifest)]) == 0
    assert main(['--manifest', str(manifest), '--check']) == 0
    java_files = sorted((root / 'intf/src/product/java.gen/example/api').glob('*.java'))
    py_files = sorted((root / 'intf/src/product/python.gen/example/api').glob('*.py'))
    assert len(java_files) == len(py_files) == 6
    assert any('AIiMultiMappedList<' in path.read_text() for path in java_files)
    assert any('identity.code' in path.read_text() for path in py_files)
    dependencies = [
        LIB / 'common/util/src/product/java/eu/algites/lib/common/list/AIiMultiMappedList.java',
        LIB / 'common/util/src/product/java/eu/algites/lib/common/list/AIiKeyDefinition.java',
        LIB / 'data/dataobject/intf/src/product/java/eu/algites/lib/data/dataobject/xmldefs/AIaXmlKeyDefinition.java',
        LIB / 'data/dataobject/intf/src/product/java/eu/algites/lib/data/dataobject/xmldefs/AIaXmlKeyDefinitions.java',
        LIB / 'data/dataobject/intf/src/product/java/eu/algites/lib/data/dataobject/xmldefs/AIaXmlDataObjectField.java',
        LIB / 'data/dataobject/intf/src/product/java/eu/algites/lib/data/dataobject/xmldefs/AInXmlValueKind.java',
    ]
    outcome = subprocess.run(['javac', '-sourcepath', str(LIB / 'data/dataobject/intf/src/product/java'), '-d', str(tmp_path / 'classes'),
                              *map(str, java_files + dependencies)], capture_output=True, text=True)
    assert outcome.returncode == 0, outcome.stderr


def test_native_defs_readonly_contract_is_accepted_by_independent_python_sdo(tmp_path):
    """Exercise Defs -> annotated AIig contract -> independent SDO CLI -> instance."""
    import importlib
    from eu.algites.tool.codegen.sdo.impl.cli.aic_sdo_codegen_cli import main as sdo_main

    manifest, root = _manifest(tmp_path)
    assert main(['--manifest', str(manifest)]) == 0
    read_source = root / 'intf/src/product/python.gen/example/api/aiig_node_1.py'
    assert 'AIaDataObjectField' in read_source.read_text()
    assert 'def setValue' not in read_source.read_text()

    settings = TOOL / ('generators/code/profile/algites/src/product/config/eu/algites/'
                       'tool/codegen/sdo/algites-sdocodegen-python.settings')
    arguments = [f'--repository-root={root}',
                 '--technology-dointf-input-dir:python=intf/src/product/python.gen',
                 '--technology-sdointf-output-dir:python=impl/src/product/python.gen',
                 '--technology-sdoimpl-output-dir:python=impl/src/product/python.gen',
                 '--dointf-input-classes:python=example.api.aiig_node_1:AIigNode_1',
                 '--sdointf-subpackage=impl.intf',
                 '--sdoclass-subpackage=impl']
    arguments.extend(line.strip() for line in settings.read_text().splitlines()
                     if line.startswith('--'))
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
        assert instance.to_mapping()['Value'] == 42
    finally:
        sys.path.remove(str(generated_root))


def test_native_xml_and_yaml_contracts_drive_independent_sdo(tmp_path):
    """Both non-JSON frontends create annotated inputs usable by the SDO CLI."""
    import ast
    import importlib
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
    configuration['inputs'].extend([
        {'kind': 'yamldefs', 'path': yaml_source.relative_to(root).as_posix()},
        {'kind': 'xmldefs', 'path': xml_source.relative_to(root).as_posix()}])
    manifest.write_text(json.dumps(configuration))
    assert main(['--manifest', str(manifest)]) == 0
    settings = TOOL / ('generators/code/profile/algites/src/product/config/eu/algites/'
                       'tool/codegen/sdo/algites-sdocodegen-python.settings')
    arguments = [f'--repository-root={root}',
                 '--technology-dointf-input-dir:python=intf/src/product/python.gen',
                 '--technology-sdointf-output-dir:python=impl/src/product/python.gen',
                 '--technology-sdoimpl-output-dir:python=impl/src/product/python.gen',
                 ('--dointf-input-classes:python=example.api.aiig_yaml_settings_1:AIigYamlSettings_1;'
                  'example.api.aiig_xml_person_1:AIigXmlPerson_1'),
                 '--sdointf-subpackage=impl.intf', '--sdoclass-subpackage=impl']
    arguments.extend(line.strip() for line in settings.read_text().splitlines()
                     if line.startswith('--'))
    assert sdo_main(arguments) == 0
    assert sdo_main(arguments + ['--check']) == 0

    generated_root = root / 'impl/src/product/python.gen'
    sys.path.insert(0, str(generated_root))
    try:
        files = sorted(generated_root.rglob('aic*.py'))
        assert len(files) == 2
        for path in files:
            declaration = next(n for n in ast.parse(path.read_text()).body
                               if isinstance(n, ast.ClassDef) and n.name.startswith('AIcgd'))
            module = '.'.join(path.relative_to(generated_root).with_suffix('').parts)
            implementation = getattr(importlib.import_module(module), declaration.name)
            instance = implementation()
            if 'XmlPerson' in implementation.__name__:
                instance.setLabel('Mia')
                assert instance.to_mapping()['Label'] == 'Mia'
                assert implementation.from_xml('<XmlPerson><Label>Mia</Label></XmlPerson>').getLabel() == 'Mia'
            else:
                instance.setCount(7)
                assert instance.to_mapping()['count'] == 7
    finally:
        sys.path.remove(str(generated_root))
