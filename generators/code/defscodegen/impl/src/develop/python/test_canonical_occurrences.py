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
    AIngSourceInputKind_1 as Kind, AIcgdList_1,
    AIcgdElement_1, AIcgdElementList_1,
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
    assert [(c.name, c.min_item_count, c.max_item_count) for c in children] == [
        ('items', 1, 1), ('nickname', 0, 1)]
    assert children[0].structure.min_item_count == 2
    assert children[0].structure.max_item_count == 5
    data = result.payload['types'][0]['content']['structure']['ElementList']['children']
    assert data[0]['Element']['min_item_count'] == 1
    assert data[0]['Element']['structure']['List']['max_item_count'] == 5


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
    assert isinstance(name, AIcgdElement_1) and (name.min_item_count, name.max_item_count) == (0, 1)
    assert isinstance(tags, AIcgdList_1) and (tags.min_item_count, tags.max_item_count) == (2, -1)
    # XML CHOICE is an explicitly represented embedded TYPE, not a flattened
    # anonymous list. Its occurrence bounds belong to the nested choice.
    assert isinstance(choice, AIcgdElement_1)
    assert (choice.min_item_count, choice.max_item_count) == (0, 1)
    assert isinstance(choice.structure.structure, AIcgdElementList_1)
    assert (choice.structure.structure.min_item_count,
            choice.structure.structure.max_item_count) == (0, 3)
    wire = result.payload['types'][0]['content']['structure']['ElementList']['children'][2]
    assert wire['Element']['structure']['Type']['content']['structure']['ElementList']['max_item_count'] == 3


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
    ({'type': 'object', 'required': ['missing'], 'properties': {}}, ValueError),
    ({'type': 'object', 'required': ['id', 'id'], 'properties': {'id': {'type': 'string'}}}, ValueError),
    # JSON Schema permits this inapplicable facet; the current frontend rejects
    # its nonprojectable conditional meaning rather than calling it malformed.
    ({'type': 'string', 'minItems': 2}, ValueError),
    ({'type': 'array', 'prefixItems': [{'type': 'string'}], 'maxItems': 1}, ValueError),
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
        assert 'min_item_count' in names and 'max_item_count' in names


def test_anyof_is_validation_only_and_does_not_change_structural_contract():
    """Unprojected JSON Schema assertions produce a warning, not CHOICE."""
    source = {'type': 'object', 'properties': {'code': {'type': 'string'}},
              'anyOf': [{'required': ['code']}, {'maxProperties': 2}]}
    with pytest.warns(UserWarning, match='Validation-only JSON Schema anyOf'):
        result = _pipeline().process([
            AIcdDefsCodegenSourceDocument(Kind.JSONDEFS, 'anyof.json', source)])
    assert [child.name for child in result.types[0].structure.children] == ['code']
