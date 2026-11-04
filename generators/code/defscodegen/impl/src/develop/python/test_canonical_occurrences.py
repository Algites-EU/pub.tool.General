"""Cross-source cardinality tests for the schema-generated canonical Defs model."""
from pathlib import Path
import json
import sys
import pytest
import yaml

TOOL = next(p for p in Path(__file__).resolve().parents if p.name == 'pub.tool.General')
for path in ('generators/code/common/src/product/python',
             'generators/code/defscodegen/intf/src/product/python',
             'generators/code/defscodegen/impl/src/product/python'):
    sys.path.insert(0, str(TOOL / path))

from eu.algites.tool.codegen.common.naming_profiles import resolve_codegen_naming_profiles
from eu.algites.tool.codegen.defs.impl.standard.canonical_generated_model import (
    AIigSourceInputKind_1 as Kind, AIcgd_jList_1,
    AIcgd_jElement_1, AIcgd_jElementList_1,
)
from eu.algites.tool.codegen.defs.impl.standard.canonical_pipeline import (
    AIcDefsCodegenCanonicalPipeline, AIcdDefsCodegenSourceDocument,
)


def _pipeline():
    location = TOOL / 'generators/code/profile/algites/src/product/config/eu/algites/lib/naming/convention/sourcecode'
    common = yaml.safe_load((location/'algites-java-common-codegen-conventions.yml').read_text())
    defs = yaml.safe_load((location/'algites-java-defs-codegen-conventions.yml').read_text())
    profile = resolve_codegen_naming_profiles(common, 'algites-java-codegen-common_1',
                                               defs, 'algites-java-defscodegen-standard_1')
    schema_file = TOOL / ('generators/code/defscodegen/intf/src/product/jsondefs/eu/algites'
                          '/tool/codegen/defs/model/canonical-model_1.jsondef.schema.json')
    return AIcDefsCodegenCanonicalPipeline(profile, json.loads(schema_file.read_text()))


@pytest.mark.parametrize('kind', (Kind.JSONDEFS, Kind.YAMLDEFS))
def test_required_and_array_occurrences_survive_link_and_schema_validation(kind):
    schema = {'$id': 'urn:sample', 'type': 'object', 'required': ['items'], 'properties': {
        'items': {'type': 'array', 'minItems': 2, 'maxItems': 5, 'items': {'type': 'string'}},
        'nickname': {'type': 'string'}}}
    result = _pipeline().process([AIcdDefsCodegenSourceDocument(kind, 'sample.schema.json', schema)])
    children = result.types[0].structure.children
    assert [(c.name, c.min_occurs, c.max_occurs) for c in children] == [
        ('items', 1, 1), ('nickname', 0, 1)]
    assert children[0].structure.min_occurs == 2
    assert children[0].structure.max_occurs == 5
    data = result.payload['types'][0]['structure']['ElementList']['children']
    assert data[0]['Element']['min_occurs'] == 1
    assert data[0]['Element']['structure']['List']['max_occurs'] == 5


def test_xsd_optional_repeated_and_optional_choice_occurrences():
    xsd = '''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
      <xs:complexType name="Person"><xs:sequence>
         <xs:element name="Name" type="xs:string" minOccurs="0"/>
         <xs:element name="Tags" type="xs:string" minOccurs="2" maxOccurs="unbounded"/>
         <xs:choice minOccurs="0" maxOccurs="3"><xs:element name="Yes" type="xs:string"/></xs:choice>
      </xs:sequence></xs:complexType>
    </xs:schema>'''
    result = _pipeline().process([AIcdDefsCodegenSourceDocument(Kind.XMLDEFS, 'person.xsd', xsd)])
    name, tags, choice = result.types[0].structure.children
    assert isinstance(name, AIcgd_jElement_1) and (name.min_occurs, name.max_occurs) == (0, 1)
    assert isinstance(tags, AIcgd_jList_1) and (tags.min_occurs, tags.max_occurs) == (2, -1)
    assert isinstance(choice, AIcgd_jElementList_1) and (choice.min_occurs, choice.max_occurs) == (0, 3)
    assert result.payload['types'][0]['structure']['ElementList']['children'][2]['ElementList']['max_occurs'] == 3


def test_cardinality_disagreement_is_not_merged():
    first = {'$id': 'urn:a', 'type': 'object', 'properties': {'id': {'type': 'string'}},
             'required': ['id']}
    second = {'$id': 'urn:a', 'type': 'object', 'properties': {'id': {'type': 'string'}}}
    with pytest.raises(ValueError, match='Conflicting canonical definitions'):
        _pipeline().process((AIcdDefsCodegenSourceDocument(Kind.JSONDEFS, 'a.json', first),
                             AIcdDefsCodegenSourceDocument(Kind.YAMLDEFS, 'a.yaml', second)))


@pytest.mark.parametrize('schema,exception', [
    ({'type': 'array', 'minItems': -1}, ValueError),
    ({'type': 'array', 'minItems': 4, 'maxItems': 3}, ValueError),
    ({'type': 'array', 'minItems': True}, ValueError),
    ({'type': 'object', 'required': ['missing'], 'properties': {}}, NotImplementedError),
    ({'type': 'object', 'required': ['id', 'id'], 'properties': {'id': {'type': 'string'}}}, ValueError),
    ({'type': 'string', 'minItems': 2}, ValueError),
    ({'anyOf': [{'type': 'string'}, {'type': 'integer'}]}, NotImplementedError),
    ({'type': 'array', 'prefixItems': [{'type': 'string'}], 'maxItems': 1}, NotImplementedError),
])
def test_reject_unrepresentable_or_invalid_bounds(schema, exception):
    with pytest.raises(exception):
        _pipeline().process([AIcdDefsCodegenSourceDocument(Kind.JSONDEFS, 'bad.json', schema)])


def test_source_schema_representations_are_in_sync():
    base = TOOL / 'generators/code/defscodegen/intf/src/product'
    first = json.loads((base/'jsondefs/eu/algites/tool/codegen/defs/model/canonical-model_1.jsondef.schema.json').read_text())
    second = json.loads((base/'yamldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.yamldef.schema.json').read_text())
    for kind in ('Element','ElementList','List'):
        assert first['$defs'][kind] == second['$defs'][kind]
    from xml.etree import ElementTree as ET
    xsd = ET.parse(base/'xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd')
    ns = {'xs':'http://www.w3.org/2001/XMLSchema'}
    for kind in ('Element','ElementList','List'):
        declaration = xsd.find(f".//xs:complexType[@name='{kind}']",ns)
        names = [item.get('name') for item in declaration.findall('xs:sequence/xs:element',ns)]
        assert 'min_occurs' in names and 'max_occurs' in names
