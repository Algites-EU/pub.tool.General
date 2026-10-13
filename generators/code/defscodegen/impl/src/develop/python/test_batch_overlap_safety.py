"""Regression tests for canonical input merging and preflight-safe batch cleanup."""

import json
from importlib import resources
from pathlib import Path

import pytest

from eu.algites.tool.codegen.defs.aic_schema_contract_bindings_generator import AIcSchemaContractBindingsGenerator


def _naming_resource_bytes(name: str) -> bytes:
    """Read published naming resources without depending on another artifact's source layout."""
    providers = (
        ('eu.algites.lib.naming.convention', ()),
        ('algites.pub.lib.general.naming.convention.impl',
         ('eu', 'algites', 'lib', 'naming', 'convention')),
    )
    for package, subpath in providers:
        try:
            candidate = resources.files(package).joinpath(*subpath, name)
        except (ModuleNotFoundError, TypeError):
            continue
        if candidate.is_file():
            return candidate.read_bytes()
    raise FileNotFoundError(f'Missing installed Algites naming resource: {name}')


@pytest.fixture
def prepared(tmp_path):
    config = tmp_path / 'config'
    config.mkdir()
    for name in ('standard-conventions.yml', 'algites-python-name-conventions.yml',
                 'algites-java-name-conventions.yml', 'algites-yamldef-name-conventions.yml',
                 'algites-jsondef-name-conventions.yml'):
        (config / name).write_bytes(_naming_resource_bytes(name))
    return tmp_path


def _schema(root, branch, kind, identity='urn:example:customer:1', *, field_type='string', description='a description'):
    suffix = 'yamldef.schema.json' if kind == 'yamldefs' else 'jsondef.schema.json'
    destination = root / 'schemas' / branch / kind / 'example'
    destination.mkdir(parents=True, exist_ok=True)
    source = destination / ('customer_1.' + suffix)
    content = {'type': 'object', '$id': identity, 'description': description,
               'properties': {'Name': {'type': field_type}}, 'required': ['Name']}
    source.write_text(json.dumps(content), encoding='utf-8')
    return source


def _manifest(root, paths, *, output='python'):
    return {'artifact': '.', 'languages': [output],
            'schema_inputs': [dict(kind=k, directory=str(source.parent.parent)) for k, source in paths],
            'schema_input_naming_profiles': {kind: f'config/algites-{kind[:-1]}-name-conventions.yml'
                                             for kind, _ in paths},
            'technology_outputs': {output: 'src/product/' + output + '.gen'},
            'technology_naming_profiles': {output: f'config/algites-{output}-name-conventions.yml'}}


def _output(root):
    return root / 'src/product/python.gen/example/aiig_customer_1.py'


def test_same_format_duplicate_roots_merge_when_identity_and_contract_match(prepared):
    first = _schema(prepared, 'a', 'yamldefs', description='alpha documentation')
    second = _schema(prepared, 'b', 'yamldefs', description='beta documentation')
    generator = AIcSchemaContractBindingsGenerator()
    result = generator.generate_manifest(prepared, _manifest(prepared, [('yamldefs', first), ('yamldefs', second)]))
    assert len(result) == 2
    text = _output(prepared).read_text(encoding='utf-8')
    assert 'alpha documentation' in text and 'beta documentation' in text
    assert generator.generate_manifest(prepared, _manifest(prepared, [('yamldefs', first), ('yamldefs', second)]), check=True) == result


def test_different_canonical_id_same_output_fails_without_erasing_old_source(prepared):
    first = _schema(prepared, 'a', 'yamldefs')
    generator = AIcSchemaContractBindingsGenerator()
    generator.generate_manifest(prepared, _manifest(prepared, [('yamldefs', first)]))
    before = _output(prepared).read_bytes()
    second = _schema(prepared, 'b', 'yamldefs', identity='urn:different:customer:1')
    with pytest.raises(ValueError, match='Canonical identity collision'):
        generator.generate_manifest(prepared, _manifest(prepared, [('yamldefs', first), ('yamldefs', second)]))
    assert _output(prepared).read_bytes() == before


def test_structurally_incompatible_identical_identity_preserves_old_source(prepared):
    first = _schema(prepared, 'a', 'yamldefs')
    generator = AIcSchemaContractBindingsGenerator()
    generator.generate_manifest(prepared, _manifest(prepared, [('yamldefs', first)]))
    before = _output(prepared).read_bytes()
    second = _schema(prepared, 'b', 'yamldefs', field_type='integer')
    with pytest.raises(ValueError, match='Incompatible canonical representations'):
        generator.generate_manifest(prepared, _manifest(prepared, [('yamldefs', first), ('yamldefs', second)]))
    assert _output(prepared).read_bytes() == before


def test_formatted_publication_ids_normalize_only_for_equivalent_formats(prepared):
    first = _schema(prepared, 'a', 'yamldefs',
                    identity='https://defs.dev.algites.eu/api/yamldefs/eu/example/customer_1.yamldef.schema.json')
    second = _schema(prepared, 'b', 'jsondefs',
                     identity='https://defs.dev.algites.eu/api/jsondefs/eu/example/customer_1.jsondef.schema.json')
    generator = AIcSchemaContractBindingsGenerator()
    result = generator.generate_manifest(prepared, _manifest(prepared, [('yamldefs', first), ('jsondefs', second)]))
    assert len(result) == 2
    assert _output(prepared).is_file()


def test_cleanup_after_valid_preflight_does_not_touch_foreign_files(prepared):
    first = _schema(prepared, 'a', 'yamldefs')
    manifest = _manifest(prepared, [('yamldefs', first)])
    generator = AIcSchemaContractBindingsGenerator()
    generator.generate_manifest(prepared, manifest)
    foreign = _output(prepared).parent / 'not_owned.py'
    foreign.write_text('keep me', encoding='utf-8')
    first.unlink()
    generator.generate_manifest(prepared, manifest)
    assert not _output(prepared).exists()
    assert foreign.read_text(encoding='utf-8') == 'keep me'


def test_missing_ids_use_implicit_package_name_version_and_pointer(prepared):
    first = _schema(prepared, 'a', 'yamldefs')
    second = _schema(prepared, 'b', 'yamldefs')
    for source in (first, second):
        document = json.loads(source.read_text(encoding='utf-8'))
        document.pop('$id')
        source.write_text(json.dumps(document), encoding='utf-8')
    result = AIcSchemaContractBindingsGenerator().generate_manifest(
        prepared, _manifest(prepared, [('yamldefs', first), ('yamldefs', second)]))
    assert len(result) == 2
    assert _output(prepared).exists()


def test_xsd_without_namespace_can_merge_with_implicit_json_identity(prepared):
    json_source = _schema(prepared, 'a', 'jsondefs')
    document = json.loads(json_source.read_text(encoding='utf-8'))
    document.pop('$id')
    json_source.write_text(json.dumps(document), encoding='utf-8')
    xsd = prepared / 'schemas/b/xmldefs/example'
    xsd.mkdir(parents=True)
    xml_source = xsd / 'customer_1.xsd'
    xml_source.write_text('''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" version="1">
      <xs:element name="customer" type="CustomerType"/>
      <xs:complexType name="CustomerType"><xs:sequence>
        <xs:element name="Name" type="xs:string"/>
      </xs:sequence></xs:complexType>
    </xs:schema>''', encoding='utf-8')
    # Reuse the shipped XSD catalog and the same relative example package.
    (prepared / 'config/algites-xmldef-name-conventions.yml').write_bytes(
        _naming_resource_bytes('algites-xmldef-name-conventions.yml'))
    result = AIcSchemaContractBindingsGenerator().generate_manifest(
        prepared, _manifest(prepared, [('jsondefs', json_source), ('xmldefs', xml_source)]))
    assert len(result) == 2
    assert _output(prepared).is_file()
