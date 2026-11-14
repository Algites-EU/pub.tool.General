"""Type versions and source documentation must survive every canonical pipeline phase."""
from pathlib import Path
import json
import sys
import pytest
import yaml

TOOL = next(p for p in Path(__file__).resolve().parents if p.name == 'pub.tool.General')
for entry in ('generators/code/common/src/product/python',
              'generators/code/defscodegen/intf/src/product/python',
              'generators/code/defscodegen/impl/src/product/python'):
    sys.path.insert(0, str(TOOL / entry))

from eu.algites.tool.codegen.common.naming_profiles import resolve_codegen_naming_profiles
from eu.algites.tool.codegen.defs.impl.standard.canonical_generated_model import AIngSourceInputKind_1 as Kind
from eu.algites.tool.codegen.defs.impl.standard.canonical_pipeline import (
    AIcDefsCodegenCanonicalPipeline, AIcdDefsCodegenSourceDocument,
)


def pipeline():
    config = TOOL / 'generators/code/profile/algites/src/product/config/eu/algites/lib/naming/convention/sourcecode'
    common = yaml.safe_load((config / 'algites-java-common-codegen-conventions.yml').read_text())
    defs = yaml.safe_load((config / 'algites-java-defs-codegen-conventions.yml').read_text())
    naming = resolve_codegen_naming_profiles(common, 'algites-java-codegen-common_1',
                                              defs, 'algites-java-defscodegen-standard_1')
    schema = json.loads((TOOL / ('generators/code/defscodegen/intf/src/product/jsondefs/'
                                 'eu/algites/tool/codegen/defs/model/canonical-model_1.jsondef.schema.json')).read_text())
    return AIcDefsCodegenCanonicalPipeline(naming, schema)


@pytest.mark.parametrize('kind', [Kind.JSONDEFS, Kind.YAMLDEFS])
def test_root_version_and_field_documentation_survive(kind):
    source = {'$id': 'urn:orders', 'x-algites-schema-version': '2.1',
              'title': 'Orders', 'description': 'Order details.', 'type': 'object',
              'properties': {'code': {'type': 'string', 'description': 'External identifier.'}}}
    value = pipeline().process([AIcdDefsCodegenSourceDocument(kind, 'orders.schema', source)])
    record = value.types[0]
    assert (record.schema_version, record.description) == ('2.1', 'Order details.')
    assert record.structure.children[0].description == 'External identifier.'
    wire = value.payload['types'][0]
    assert (wire['schema_version'], wire['description']) == ('2.1', 'Order details.')
    assert (wire['content']['structure']['ElementList']['children'][0]['Element']['description']
            == 'External identifier.')


def test_definition_version_inherits_source_when_not_explicit():
    source = {'x-algites-schema-version': 3,
              '$defs': {'Item': {'type': 'string', 'description': 'One value.'}}}
    result = pipeline().process([AIcdDefsCodegenSourceDocument(Kind.JSONDEFS, 'lib.json', source)])
    assert [(v.name, v.schema_version, v.description) for v in result.types] == [
        ('Item', '3', 'One value.')]


def test_xml_documentation_is_preserved():
    source = '''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" x-algites-schema-version="1.4">
    <xs:complexType name="Person"><xs:annotation><xs:documentation>Person record.</xs:documentation></xs:annotation>
      <xs:sequence><xs:element name="Name" type="xs:string"><xs:annotation>
        <xs:documentation>Legal name.</xs:documentation></xs:annotation></xs:element></xs:sequence>
    </xs:complexType></xs:schema>'''
    result = pipeline().process([AIcdDefsCodegenSourceDocument(Kind.XMLDEFS, 'person.xsd', source)])
    item = result.types[0]
    assert (item.schema_version, item.description) == ('1.4', 'Person record.')
    assert item.structure.children[0].description == 'Legal name.'


def test_missing_metadata_merges_with_explicit_metadata():
    a = {'$id': 'urn:merged', 'title': 'Entity', 'type': 'object',
         'properties': {'name': {'type': 'string'}}}
    b = {'$id': 'urn:merged', 'title': 'Entity', 'type': 'object', 'x-algites-schema-version': '5',
         'description': 'Shared entity',
         'properties': {'name': {'type': 'string', 'description': 'Value'}}}
    result = pipeline().process([AIcdDefsCodegenSourceDocument(Kind.JSONDEFS, 'a.json', a),
                                 AIcdDefsCodegenSourceDocument(Kind.YAMLDEFS, 'b.yaml', b)])
    assert result.types[0].schema_version == '5'
    assert result.types[0].structure.children[0].description == 'Value'
    assert set(result.types[0].source_bindings) == {Kind.JSONDEFS, Kind.YAMLDEFS}


def test_conflicting_metadata_is_diagnostic():
    a = {'$id': 'urn:merged', 'type': 'string', 'x-algites-schema-version': '1'}
    b = {'$id': 'urn:merged', 'type': 'string', 'x-algites-schema-version': '2'}
    with pytest.raises(ValueError, match='Conflicting canonical definitions'):
        pipeline().process([AIcdDefsCodegenSourceDocument(Kind.JSONDEFS, 'a.json', a),
                            AIcdDefsCodegenSourceDocument(Kind.YAMLDEFS, 'b.yaml', b)])


def test_allof_reference_is_explicit_inheritance_not_lost_properties():
    """Equivalent replacement for the retired flat-property allOf assertion."""
    source = {'$defs': {'content': {'type': 'object', 'required': ['Name'],
                                  'properties': {'Name': {'type': 'string'}}}},
              'allOf': [{'$ref': '#/$defs/content'}]}
    result = pipeline().process([AIcdDefsCodegenSourceDocument(Kind.JSONDEFS, 'composed.json', source)])
    assert len(result.types) == 2
    root, inherited = result.types
    assert root.inherited_from_types == (inherited.identity,)
    assert inherited.structure.children[0].name == 'Name'
    assert inherited.structure.children[0].min_item_count == 1


def test_oneof_enum_list_preserves_all_branch_literals():
    """Equivalent replacement for the retired enum-alternative merger assertion."""
    source = {'title': 'Languages', 'type': 'array', 'items': {'type': 'object', 'x-algites-defscodegen-choice': True,
        'properties': {'java': {'type': 'string', 'enum': ['java']},
                       'python': {'type': 'string', 'enum': ['python']}},
        'minProperties': 1, 'maxProperties': 1, 'additionalProperties': False}}
    result = pipeline().process([AIcdDefsCodegenSourceDocument(Kind.JSONDEFS, 'lang.json', source)])
    list_item = result.types[0].structure.item
    assert list_item.origin.value == 'SYNTHETIC'
    variants = list_item.structure.children
    assert [branch.structure.structure.values[0].wire_value for branch in variants] == [
        'java', 'python']
