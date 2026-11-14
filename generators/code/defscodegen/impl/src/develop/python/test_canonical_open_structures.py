"""Regressions for typed JSON/YAML keys and lossless wildcard diagnostics.

The public DataObject contract must never silently expose Object/Any values.
"""
from pathlib import Path
import subprocess
import warnings

import pytest

from eu.algites.tool.codegen.defs.impl.standard.canonical_generated_model import (
    AIngSourceInputKind_1 as SourceKind,
    AIngStructureKind_1 as StructureKind,
)
from test_canonical_schema_frontend import frontend
from test_canonical_indexed_json_maps import _emit, LIB


@pytest.mark.parametrize('kind', (SourceKind.JSONDEFS, SourceKind.YAMLDEFS))
def test_real_array_key_is_not_interpreted_as_object_map(kind, tmp_path):
    schema = {'title': 'Registry', 'type': 'object', 'properties': {
        'Entry': {'type': 'array',
                  'x-algites-defscodegen-key': {'id': 'ByName', 'field-name': 'name'},
                  'items': {'type': 'object', 'additionalProperties': False,
                            'properties': {'name': {'type': 'string'},
                                           'code': {'type': 'string'}},
                            'required': ['name']}}}}
    root = frontend().load_json_or_yaml(schema, 'reg.schema.json', kind)
    indexed = root.structure.children[0]
    assert indexed.kind == StructureKind.LIST
    assert indexed.key_definitions[0].identifier == 'ByName'
    assert indexed.key_definitions[0].fields == ('name',)
    assert indexed.key_definitions[0].selector == 'Entry'
    assert indexed.key_definitions[0].source_pointer.endswith('/x-algites-defscodegen-key')
    output = _emit(schema, kind)
    root_java = output['regression/output/AIigT0.java']
    assert 'AIiMultiMappedList<? extends AIigT1> getEntryList()' in root_java
    assert 'KEY_ID__BY_NAME = "ByName"' in root_java
    assert 'fields = {CONSTRegistry.FIELD_NAME__NAME}' in root_java
    assert 'Map<String, Object>' not in '\n'.join(output.values())
    sources = []
    for filename, content in output.items():
        if filename.endswith('.java'):
            dst = tmp_path / filename
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(content)
            sources.append(dst)
    cp = ':'.join(map(str, (LIB/'data/dataobject/intf/src/product/java',
                            LIB/'common/util/src/product/java')))
    result = subprocess.run(['javac', '-sourcepath', cp, '-d', str(tmp_path/'classes'),
                             *map(str, sources)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize('kind', (SourceKind.JSONDEFS, SourceKind.YAMLDEFS))
@pytest.mark.parametrize('additional', (True, {}, {'description': 'anything'}))
def test_untyped_additional_properties_warns_but_has_no_map_getter(kind, additional):
    schema = {'title': 'Known', 'type': 'object', 'properties': {
        'Value': {'type': 'string'}}, 'additionalProperties': additional}
    with pytest.warns(UserWarning, match=r'additionalProperties.*ignored|unconstrained additionalProperties') as found:
        root = frontend().load_json_or_yaml(schema, 'schemas/known.json', kind)
    message = str(found[0].message)
    assert 'schemas/known.json#/additionalProperties' in message
    assert 'Hint:' in message and '$ref' in message and 'roundtrip' in message
    assert [f.name for f in root.structure.children] == ['Value']
    code = '\n'.join(_emit(schema, kind).values())
    assert 'getValue()' in code
    assert 'getAdditionalProperties' not in code
    assert 'Map<String, Object>' not in code


@pytest.mark.parametrize('kind', (SourceKind.JSONDEFS, SourceKind.YAMLDEFS))
def test_missing_additional_properties_is_silent(kind):
    schema = {'title': 'Known', 'type': 'object', 'properties': {'Value': {'type': 'string'}}}
    with warnings.catch_warnings(record=True) as observed:
        warnings.simplefilter('always')
        root = frontend().load_json_or_yaml(schema, 'schemas/known.json', kind)
    assert not [w for w in observed if 'additionalProperties' in str(w.message)]
    assert len(root.structure.children) == 1


@pytest.mark.parametrize('kind', (SourceKind.JSONDEFS, SourceKind.YAMLDEFS))
def test_explicit_typed_additional_properties_still_generates_a_typed_map(kind):
    schema = {'type': 'object', 'properties': {'Value': {'type': 'string'}},
              'additionalProperties': {'type': 'boolean'}}
    root = frontend().load_json_or_yaml(schema, 'schemas/known.json', kind)
    assert len(root.structure.children) == 2
    assert root.structure.children[1].kind == StructureKind.MAP
    assert root.structure.children[1].value_type.kind == StructureKind.SCALAR


@pytest.mark.parametrize('key_field,field_schema,required,why', (
    ('missing', {'type': 'string'}, ['name'], 'missing field'),
    ('name', {'type': 'string'}, [], 'requires field'),
    ('name', {'type': 'object'}, ['name'], 'typed scalar'),
))
def test_invalid_array_key_is_rejected_with_source(key_field, field_schema, required, why):
    source = {'type': 'array', 'items': {'type': 'object',
        'properties': {'name': field_schema}, 'required': required},
        'x-algites-defscodegen-key': {'id': 'ByName', 'field-name': key_field}}
    with pytest.raises(ValueError, match=why) as error:
        frontend().load_json_or_yaml(source, 'schemas/invalid.json', SourceKind.JSONDEFS)
    assert 'schemas/invalid.json#/x-algites-defscodegen-key' in str(error.value)


def test_optional_xsd_wildcards_emit_hints_but_no_fields():
    source = '''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
     <xs:complexType name="Config"><xs:sequence>
       <xs:element name="Known" type="xs:string"/>
       <xs:any minOccurs="0" maxOccurs="unbounded" processContents="lax"/>
     </xs:sequence><xs:anyAttribute namespace="##other"/></xs:complexType>
    </xs:schema>'''
    with pytest.warns(UserWarning) as found:
        roots = frontend().load_xsd(source, 'schemas/optional.xsd')
    diagnostics = '\n'.join(str(w.message) for w in found)
    assert 'schemas/optional.xsd' in diagnostics
    assert 'xs:any at ' in diagnostics and 'xs:anyAttribute at ' in diagnostics
    assert 'Hint:' in diagnostics and '<xs:element' in diagnostics
    assert '<xs:attribute' in diagnostics and 'roundtrip' in diagnostics
    assert len(roots) == 1
    assert 'Ignored optional XML wildcard' in roots[0].description


def test_required_xsd_wildcard_is_an_error_with_hint():
    source = '''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
     <xs:complexType name="Config"><xs:sequence><xs:any minOccurs="1"/>
     </xs:sequence></xs:complexType></xs:schema>'''
    with pytest.raises(NotImplementedError, match='Required XML wildcard.*Hint:') as error:
        frontend().load_xsd(source, 'schemas/required.xsd')
    assert 'schemas/required.xsd' in str(error.value)
