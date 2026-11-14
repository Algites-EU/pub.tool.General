"""Reject schema constructs until their meaning is representable without loss."""
import sys
from pathlib import Path
import pytest

TOOL = next(p for p in Path(__file__).resolve().parents if p.name == 'pub.tool.General')
for entry in ('generators/code/common/src/product/python',
              'generators/code/defscodegen/intf/src/product/python',
              'generators/code/defscodegen/impl/src/product/python'):
    sys.path.insert(0, str(TOOL / entry))

from eu.algites.tool.codegen.defs.impl.standard.canonical_generated_model import AIngSourceInputKind_1 as Kind
from eu.algites.tool.codegen.defs.impl.standard.canonical_schema_frontend import (
    AIcDefsCodegenCanonicalSchemaFrontend,
)
from eu.algites.tool.codegen.common.naming_profiles import AIcdCodegenNamingProfile


def frontend():
    return AIcDefsCodegenCanonicalSchemaFrontend(AIcdCodegenNamingProfile(
        'test', {'standard_getter': 'unused', 'standard_setter': 'unused'}, {}, {}, {}, 1, {}))


@pytest.mark.parametrize('kind', [Kind.JSONDEFS, Kind.YAMLDEFS])
@pytest.mark.parametrize('keyword,value,attribute,expected', [
    ('minLength', 3, 'min_length', 3),
    ('maxLength', 12, 'max_length', 12),
    ('pattern', '^[A-Z]$', 'pattern', '^[A-Z]$'),
])
def test_supported_string_facets_survive_in_canonical_model(kind, keyword, value, attribute, expected):
    """Supported lexical constraints must no longer trigger the old fail-closed guard."""
    node = frontend().load_json_or_yaml({'type': 'string', keyword: value}, 'schema.json', kind)
    assert getattr(node.structure, attribute) == expected


@pytest.mark.parametrize('kind', [Kind.JSONDEFS, Kind.YAMLDEFS])
@pytest.mark.parametrize('keyword,value,type_name,attribute,expected', [
    ('minimum', 0, 'integer', 'minimum', '0'),
    ('multipleOf', 2, 'integer', 'multiple_of', '2'),
    ('uniqueItems', True, 'array', 'unique_items', True),
    ('minProperties', 2, 'object', 'min_properties', 2),
])
def test_supported_scalar_collection_and_object_facets_survive(kind, keyword, value, type_name, attribute, expected):
    """Use compatible schema types so native facets retain their correct meaning."""
    schema = {'type': type_name, keyword: value}
    if type_name == 'array':
        schema['items'] = {'type': 'string'}
    if type_name == 'object':
        schema['properties'] = {'name': {'type': 'string'}}
    node = frontend().load_json_or_yaml(schema, 'schema.json', kind)
    assert getattr(node.structure, attribute) == expected


@pytest.mark.parametrize('kind', [Kind.JSONDEFS, Kind.YAMLDEFS])
@pytest.mark.parametrize('keyword,value', [
    ('dependentRequired', {'a': ['b']}),
    ('readOnly', True),
])
def test_validation_only_keywords_warn_without_changing_storage_type(kind, keyword, value):
    with pytest.warns(UserWarning, match=r'Validation-only JSON Schema keyword.*schema.json#'):
        root = frontend().load_json_or_yaml({'type': 'string', keyword: value}, 'schema.json', kind)
    assert root.structure.kind.value == "SCALAR"


@pytest.mark.parametrize('kind', [Kind.JSONDEFS, Kind.YAMLDEFS])
@pytest.mark.parametrize('keyword,value', [
    ('minimum', 0), ('multipleOf', 2), ('uniqueItems', True), ('minProperties', 2),
])
def test_conditional_facets_are_not_mistaken_for_string_constraints(kind, keyword, value):
    """A keyword cannot turn a JSON string into an array, object or number."""
    with pytest.raises(NotImplementedError, match='Conditional'):
        frontend().load_json_or_yaml({'type': 'string', keyword: value}, 'schema.json', kind)


@pytest.mark.parametrize('node,diagnostic', [
    ('<xs:simpleType name="Tokens"><xs:list itemType="xs:string"/></xs:simpleType>', 'simpleType'),
    ('<xs:simpleType name="Union"><xs:union memberTypes="xs:string xs:int"/></xs:simpleType>', 'simpleType'),
    ('<xs:complexType name="Group"><xs:sequence><xs:any/></xs:sequence></xs:complexType>', 'Required XML wildcard'),
    ('<xs:complexType name="Doc"><xs:sequence><xs:element name="Code" type="xs:string" nillable="true"/></xs:sequence></xs:complexType>', 'Nillable XSD'),
    ('''<xs:complexType name="Doc"><xs:sequence><xs:element name="Code" type="xs:string">
        <xs:key name="k"><xs:selector xpath="."/><xs:field xpath="@id"/></xs:key>
       </xs:element></xs:sequence></xs:complexType>''', 'Local XSD keys'),
])
def test_unsupported_xml_contract_is_rejected(node, diagnostic):
    xml = '<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">' + node + '</xs:schema>'
    with pytest.raises(NotImplementedError, match=diagnostic):
        frontend().load_xsd(xml, 'source.xsd')


def test_canonical_type_content_exposes_exactly_one_named_alternative():
    """Both dialects model the Type payload as a named closed structural CHOICE."""
    import json
    from jsonschema import Draft202012Validator
    for dialect, extension in (('jsondefs', 'jsondef'), ('yamldefs', 'yamldef')):
        source = (TOOL / 'generators/code/defscodegen/intf/src/product' / dialect
                  / 'eu/algites/tool/codegen/defs/model'
                  / f'canonical-model_1.{extension}.schema.json')
        schema = json.loads(source.read_text(encoding='utf-8'))
        contract = schema['$defs']['Type']
        assert contract['properties']['content'] == {'$ref': '#/$defs/TypeContent'}
        assert 'content' in contract['required']
        assert 'structure' not in contract['properties']
        assert 'target_identity' not in contract['properties']
        choice = schema['$defs']['TypeContent']
        assert choice['x-algites-defscodegen-choice'] is True
        assert choice['minProperties'] == choice['maxProperties'] == 1
        assert choice['additionalProperties'] is False
        validator = Draft202012Validator({'$defs': schema['$defs'], '$ref': '#/$defs/TypeContent'})
        scalar = {'structure': {'Scalar': {'scalar_kind': 'STRING'}}}
        assert validator.is_valid(scalar)
        assert validator.is_valid({'target_identity': 'urn:defined-type'})
        assert not validator.is_valid({})
        assert not validator.is_valid({**scalar, 'target_identity': 'urn:defined-type'})
        assert not validator.is_valid({'target_identity': ''})


@pytest.mark.parametrize('kind', [Kind.JSONDEFS, Kind.YAMLDEFS])
def test_oneof_on_object_cannot_silently_replace_independent_fields(kind):
    """OneOf is a warning about marshalling-time validation, never a CHOICE."""
    source = {
        'type': 'object',
        'properties': {'common': {'type': 'string'}, 'first': {'type': 'string'},
                       'second': {'type': 'string'}},
        'required': ['common'],
        'oneOf': [{'required': ['first']}, {'required': ['second']}],
    }
    with pytest.warns(UserWarning, match='oneOf'):
        model = frontend().load_json_or_yaml(source, 'object-xor.json', kind)
    assert model.structure.composition.name == 'SEQUENCE'
    assert [field.name for field in model.structure.children] == ['common', 'first', 'second']
    assert model.structure.children[0].min_item_count == 1
