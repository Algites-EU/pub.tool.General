"""Metadata mapping must follow the schema input profile through generated contracts."""
import json
from pathlib import Path

from eu.algites.tool.codegen.defs.impl.standard.aic_schema_contract_bindings_generator import AIcSchemaContractBindingsGenerator


def test_algites_schema_url_not_confused_with_logical_id(tmp_path: Path):
    source = tmp_path / 'src/product/jsondefs/example/contracts'
    source.mkdir(parents=True)
    url = 'https://example.test/schemas/example_1.json'
    (source / 'example_1.jsondef.schema.json').write_text(json.dumps({
        '$schema': 'https://json-schema.org/draft/2020-12/schema',
        '$id': url,
        '$x-algites-schema-id': 'example.logical',
        '$x-algites-schema-version': 1,
        'type': 'object', 'properties': {'Name': {'type': 'string'}}
    }))
    options = {
        'artifact': '.',
        'schema_inputs': [{'kind': 'jsondefs', 'directory': 'src/product/jsondefs'}],
        'schema_input_naming_conventions': {'jsondefs': 'algites-jsondef-schema-versioned_1'},
        'technology_outputs': {'python': 'src/product/python.gen', 'java': 'src/product/java.gen'},
        'technology_output_naming_conventions': {'python': {'jsondefs': 'algites-python-gen-json-intf-versioned_1'},
                                                  'java': {'jsondefs': 'algites-java-gen-json-intf-versioned_1'}},
        'naming_convention_files': [f'resource:{item}' for item in (
            'standard-conventions.yml', 'algites-python-name-conventions.yml',
            'algites-java-name-conventions.yml',
            'algites-jsondef-name-conventions.yml')],
        'languages': ['python', 'java']
    }
    AIcSchemaContractBindingsGenerator().generate_manifest(tmp_path, options)
    outputs = list((tmp_path / 'src/product/python.gen').rglob('*.py'))
    assert outputs
    generated = '\n'.join(path.read_text() for path in outputs)
    assert "schema_id='example.logical'" in generated
    assert f"schema_url='{url}'" in generated
    assert "data_source_schema_url_field='$schema'" in generated
    assert "data_source_schema_identifier_field=" not in generated
    assert "data_source_schema_version_field=" not in generated
    java_files = list((tmp_path / 'src/product/java.gen').rglob('*.java'))
    assert java_files
    java_generated = '\n'.join(path.read_text() for path in java_files)
    assert 'schemaId = "example.logical"' in java_generated
    assert f'schemaUrl = "{url}"' in java_generated
    assert 'dataSourceSchemaUrlField = "$schema"' in java_generated
    assert 'dataSourceSchemaIdentifierField =' not in java_generated
    assert 'dataSourceSchemaVersionField =' not in java_generated


def test_custom_source_profile_enables_explicit_data_document_id_and_version(tmp_path: Path):
    """Non-default mappings are carried through into annotated Python contracts."""
    import shutil
    import yaml
    from eu.algites.lib.naming.convention.impl.standard.aic_name_convention_catalog import AIcNameConventionCatalog

    schema_root = tmp_path / 'src/product/jsondefs/example/contracts'
    schema_root.mkdir(parents=True)
    (schema_root / 'example_1.jsondef.schema.json').write_text(json.dumps({
        '$schema': 'https://json-schema.org/draft/2020-12/schema',
        '$id': 'https://example.test/schemas/version_1.json',
        '$x-algites-schema-id': 'example.logical',
        '$x-algites-schema-version': 1,
        'type': 'object', 'properties': {'Name': {'type': 'string'}}
    }))
    original = AIcNameConventionCatalog.load_resource('algites-jsondef-name-conventions.yml')
    # The public profile API must reflect the edited catalog, not embedded Algites constants.
    assert original.schema_metadata_fields('algites-jsondef-schema-versioned_1')['data_source_schema_identifier'] == ''
    from eu.algites.tool.codegen.defs.impl.standard._catalog_sources import expand_naming_catalogs
    with expand_naming_catalogs(['resource:algites-jsondef-name-conventions.yml']) as files:
        raw = yaml.safe_load(Path(files[0]).read_text())
    for definition in raw['SourceStructureNameConventions']['NameConventions'].values():
        definition['data_source_schema_identifier'] = '$schemaIdentity'
        definition['data_source_schema_version'] = '$schemaRevision'
    catalog_dir = tmp_path / 'catalogs'
    catalog_dir.mkdir()
    (catalog_dir / 'algites-jsondef-name-conventions.yml').write_text(yaml.safe_dump(raw, sort_keys=False))
    with expand_naming_catalogs(['resource:standard-conventions.yml']) as files:
        shutil.copyfile(files[0], catalog_dir / 'standard-conventions.yml')
    options = {
        'artifact': '.',
        'schema_inputs': [{'kind': 'jsondefs', 'directory': 'src/product/jsondefs'}],
        'schema_input_naming_conventions': {'jsondefs': 'algites-jsondef-schema-versioned_1'},
        'technology_outputs': {'python': 'src/product/python.gen', 'java': 'src/product/java.gen'},
        'technology_output_naming_conventions': {'python': {'jsondefs': 'algites-python-gen-json-intf-versioned_1'},
                                                  'java': {'jsondefs': 'algites-java-gen-json-intf-versioned_1'}},
        'naming_convention_files': ['resource:standard-conventions.yml',
            'resource:algites-python-name-conventions.yml',
            'resource:algites-java-name-conventions.yml',
            'catalogs/algites-jsondef-name-conventions.yml'],
        'languages': ['python', 'java']
    }
    AIcSchemaContractBindingsGenerator().generate_manifest(tmp_path, options)
    generated = '\n'.join(p.read_text() for p in (tmp_path / 'src/product/python.gen').rglob('*.py'))
    assert "data_source_schema_identifier_field='$schemaIdentity'" in generated
    assert "data_source_schema_version_field='$schemaRevision'" in generated


def test_missing_schema_source_metadata_omits_annotation_members(tmp_path: Path):
    """Filename-derived canonical names never masquerade as explicit schema-source metadata."""
    import yaml
    from eu.algites.tool.codegen.defs.impl.standard._catalog_sources import expand_naming_catalogs

    schema = tmp_path / 'src/product/jsondefs/example/contracts/example_1.jsondef.schema.json'
    schema.parent.mkdir(parents=True)
    schema.write_text(json.dumps({'$schema': 'https://json-schema.org/draft/2020-12/schema',
                                  '$id': 'https://example.test/schema_1.json',
                                  'type': 'object', 'properties': {'Name': {'type': 'string'}}}))
    catalog_dir = tmp_path / 'catalogs'
    catalog_dir.mkdir()
    with expand_naming_catalogs(['resource:algites-jsondef-name-conventions.yml']) as files:
        source_catalog = yaml.safe_load(Path(files[0]).read_text())
    for definition in source_catalog['SourceStructureNameConventions']['NameConventions'].values():
        definition['schema_source_schema_identifier'] = ''
        definition['schema_source_schema_version'] = ''
    (catalog_dir / 'source.yml').write_text(yaml.safe_dump(source_catalog))
    with expand_naming_catalogs(['resource:standard-conventions.yml']) as files:
        (catalog_dir / 'standard-conventions.yml').write_text(Path(files[0]).read_text())
    options = {
        'artifact': '.',
        'schema_inputs': [{'kind': 'jsondefs', 'directory': 'src/product/jsondefs'}],
        'schema_input_naming_conventions': {'jsondefs': 'algites-jsondef-schema-versioned_1'},
        'technology_outputs': {'java': 'src/product/java.gen', 'python': 'src/product/python.gen'},
        'technology_output_naming_conventions': {
            'java': {'jsondefs': 'algites-java-gen-json-intf-versioned_1'},
            'python': {'jsondefs': 'algites-python-gen-json-intf-versioned_1'}},
        'naming_convention_files': ['resource:standard-conventions.yml',
            'resource:algites-java-name-conventions.yml',
            'resource:algites-python-name-conventions.yml',
            'catalogs/source.yml'],
        'languages': ['java', 'python']}
    AIcSchemaContractBindingsGenerator().generate_manifest(tmp_path, options)
    java = '\n'.join(f.read_text() for f in (tmp_path / 'src/product/java.gen').rglob('*.java'))
    python = '\n'.join(f.read_text() for f in (tmp_path / 'src/product/python.gen').rglob('*.py'))
    assert 'schemaId = ' not in java and 'schemaVersion = ' not in java
    assert 'schemaUrl = "https://example.test/schema_1.json"' in java
    assert 'schema_id=' not in python and 'schema_version=' not in python
    assert "schema_url='https://example.test/schema_1.json'" in python
    assert 'CANONICAL_SOURCE_ID' in java  # Canonical type identity is retained separately.


def test_selected_method_profile_controls_output_metadata(tmp_path: Path):
    """Output naming profile may disable emission without changing schema identity."""
    import yaml
    schema = tmp_path / 'src/product/jsondefs/example/contracts/example_1.jsondef.schema.json'
    schema.parent.mkdir(parents=True)
    schema.write_text(json.dumps({'$schema': 'https://json-schema.org/draft/2020-12/schema',
                                  '$id': 'https://example.test/schema_1.json',
                                  '$x-algites-schema-id': 'example.logical',
                                  '$x-algites-schema-version': 1,
                                  'type': 'object', 'properties': {'Name': {'type': 'string'}}}))
    from eu.algites.tool.codegen.defs.impl.standard._catalog_sources import expand_naming_catalogs
    catalogs = tmp_path / 'catalogs'
    catalogs.mkdir()
    with expand_naming_catalogs(['resource:algites-python-codegen-method-conventions.yml']) as files:
        method = yaml.safe_load(Path(files[0]).read_text())
    method['GeneratedDataObjectMethodNameConventions']['NameConventions'][
        'algites-python-codegen-standard_1']['data_source_schema_url'] = ''
    (catalogs/'methods.yml').write_text(yaml.safe_dump(method))
    options = {'artifact': '.',
        'schema_inputs': [{'kind':'jsondefs','directory':'src/product/jsondefs'}],
        'schema_input_naming_conventions': {'jsondefs':'algites-jsondef-schema-versioned_1'},
        'technology_outputs': {'python':'src/product/python.gen'},
        'technology_output_naming_conventions': {
            'python':{'jsondefs':'algites-python-gen-json-intf-versioned_1'}},
        'generated_dataobject_method_naming_conventions': {
            'python':'algites-python-codegen-standard_1'},
        'naming_convention_files': ['resource:standard-conventions.yml',
            'resource:algites-python-name-conventions.yml',
            'resource:algites-jsondef-name-conventions.yml', 'catalogs/methods.yml'],
        'languages':['python']}
    AIcSchemaContractBindingsGenerator().generate_manifest(tmp_path, options)
    python = '\n'.join(f.read_text() for f in (tmp_path/'src/product/python.gen').rglob('*.py'))
    assert "schema_id='example.logical'" in python
    assert 'data_source_schema_url_field=' not in python
    assert "schema_url='https://example.test/schema_1.json'" in python


def test_xml_contract_does_not_require_json_schema_metadata_from_method_profile(tmp_path: Path):
    """The JSON/YAML header switches must not disable XMLDEFS contract generation."""
    schema = tmp_path / 'src/product/xmldefs/example/contracts/sample_1.xsd'
    schema.parent.mkdir(parents=True)
    schema.write_text('''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" version="1">
        <xs:complexType name="SampleType"><xs:sequence>
          <xs:element name="Label" type="xs:string"/>
        </xs:sequence></xs:complexType>
        <xs:element name="Sample" type="SampleType"/>
        </xs:schema>''')
    options = {
        'artifact': '.',
        'schema_inputs': [{'kind':'xmldefs', 'directory':'src/product/xmldefs'}],
        'schema_input_naming_conventions': {'xmldefs': 'algites-xmldef-schema-versioned_1'},
        'technology_outputs': {'python': 'src/product/python.gen'},
        'technology_output_naming_conventions': {'python': {
            'xmldefs_type': 'algites-python-gen-xml-type-intf-versioned_1',
            'xmldefs_element': 'algites-python-gen-xml-element-intf-versioned_1',
            'xmldefs_namespace': 'algites-python-gen-xml-namespace-intf_1'}},
        'generated_dataobject_method_naming_conventions': {
            'python': 'algites-python-codegen-standard_1'},
        'naming_convention_files': [f'resource:{name}' for name in (
            'standard-conventions.yml', 'algites-python-name-conventions.yml',
            'algites-xmldef-name-conventions.yml',
            'algites-python-codegen-method-conventions.yml')],
        'languages': ['python'],
    }
    outputs = AIcSchemaContractBindingsGenerator().generate_manifest(tmp_path, options)
    assert outputs
    sources = '\n'.join(p.read_text() for p in (tmp_path / 'src/product/python.gen').rglob('*.py'))
    assert 'AIcdDataObject(' in sources
    assert 'data_source_schema_url_field=' not in sources
