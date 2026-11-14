"""Complete native Python frontend/merge/link/schema/normalization integration."""
import json
import sys
from pathlib import Path
import pytest
import yaml

TOOL = next(parent for parent in Path(__file__).resolve().parents if parent.name == 'pub.tool.General')
for relative in ('generators/code/common/src/product/python',
                 'generators/code/defscodegen/intf/src/product/python',
                 'generators/code/defscodegen/impl/src/product/python'):
    sys.path.insert(0, str(TOOL / relative))

from eu.algites.tool.codegen.common.naming_profiles import resolve_codegen_naming_profiles
from eu.algites.tool.codegen.defs.impl.standard.canonical_generated_model import AIngSourceInputKind_1 as Kind
from eu.algites.tool.codegen.defs.impl.standard.canonical_pipeline import (
    AIcDefsCodegenCanonicalPipeline, AIcdDefsCodegenSourceDocument,
)


def pipeline():
    path = TOOL / 'generators/code/profile/algites/src/product/config/eu/algites/lib/naming/convention/sourcecode'
    c = yaml.safe_load((path / 'algites-java-common-codegen-conventions.yml').read_text())
    d = yaml.safe_load((path / 'algites-java-defs-codegen-conventions.yml').read_text())
    profile = resolve_codegen_naming_profiles(c, 'algites-java-codegen-common_1',
                                               d, 'algites-java-defscodegen-standard_1')
    schema = json.loads((TOOL / 'generators/code/defscodegen/intf/src/product/jsondefs/eu/algites'
                         '/tool/codegen/defs/model/canonical-model_1.jsondef.schema.json').read_text())
    return AIcDefsCodegenCanonicalPipeline(profile, schema)


def test_cross_technology_recursive_schema_is_merged_and_validated():
    schema = {'x-algites-schema-id': 'urn:my-model', 'title': 'Model', 'type': 'object',
              'properties': {'root': {'$ref': '#/$defs/Node'}},
              '$defs': {'Node': {'type': 'object', 'properties': {
                  'next': {'$ref': '#/$defs/Node'},
                  'value': {'type': 'string'}}}}}
    result = pipeline().process((
        AIcdDefsCodegenSourceDocument(Kind.JSONDEFS, 'tree.json', schema),
        AIcdDefsCodegenSourceDocument(Kind.YAMLDEFS, 'tree.yaml', schema)))
    assert len(result.types) == 2
    assert [t.identity for t in result.types] == ['urn:my-model', 'urn:my-model#/$defs/Node']
    assert result.types[0].structure.children[0].structure.target_identity == 'urn:my-model#/$defs/Node'
    assert result.types[1].structure.children[0].structure.target_identity == 'urn:my-model#/$defs/Node'
    assert set(result.types[1].structure.children[0].structure.source_bindings) == {Kind.JSONDEFS, Kind.YAMLDEFS}
    groups = result.payload['types'][1]['source_bindings']['SourceBindingGroup']
    assert {group['InputKind'] for group in groups} == {'JSONDEFS', 'YAMLDEFS'}
    json_group = next(group for group in groups if group['InputKind'] == 'JSONDEFS')
    assert json_group['Binding'][0]['source_resource'] == 'tree.json'


def test_xsd_named_self_recursive_type_is_linked_and_schema_validated():
    xsd = '''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
    <xs:complexType name="Node"><xs:sequence>
      <xs:element name="child" type="Node"/>
    </xs:sequence></xs:complexType></xs:schema>'''
    result = pipeline().process((AIcdDefsCodegenSourceDocument(Kind.XMLDEFS, 'tree.xsd', xsd),))
    assert result.types[0].structure.children[0].structure.target_identity == 'Node'
    groups = result.payload['types'][0]['source_bindings']['SourceBindingGroup']
    assert any(group['InputKind'] == 'XMLDEFS' for group in groups)


def test_conflict_and_unresolved_reference_prevent_result_publication():
    schema = {'$id': 'urn:a', 'title': 'A', 'type': 'object',
              'properties': {'v': {'type': 'string'}}}
    conflicting = {'$id': 'urn:a', 'title': 'A', 'type': 'object',
                   'properties': {'v': {'type': 'integer'}}}
    with pytest.raises(ValueError, match='Conflicting canonical definitions'):
        pipeline().process((AIcdDefsCodegenSourceDocument(Kind.JSONDEFS, 'a.json', schema),
                            AIcdDefsCodegenSourceDocument(Kind.YAMLDEFS, 'b.yaml', conflicting)))
    with pytest.raises(ValueError, match='unresolved reference'):
        pipeline().process((AIcdDefsCodegenSourceDocument(Kind.JSONDEFS, 'a.json',
            {'type': 'object', 'properties': {'bad': {'$ref': '#/$defs/Missing'}}}),))


def test_source_document_type_validation_and_empty_batch():
    with pytest.raises(TypeError, match='XMLDEFS'):
        AIcdDefsCodegenSourceDocument(Kind.XMLDEFS, 'bad.xsd', {})
    with pytest.raises(TypeError, match='YAMLDEFS'):
        AIcdDefsCodegenSourceDocument(Kind.YAMLDEFS, 'bad.yaml', '<schema/>')
    with pytest.raises(ValueError, match='No canonical TYPE declarations'):
        pipeline().process(())


def test_namespaced_xsd_extension_records_resolved_inheritance():
    xsd = '''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:tns="urn:family"
                     targetNamespace="urn:family">
      <xs:complexType name="Base"><xs:sequence>
        <xs:element name="Id" type="xs:string"/>
      </xs:sequence></xs:complexType>
      <xs:complexType name="Child"><xs:complexContent>
        <xs:extension base="tns:Base"><xs:sequence>
          <xs:element name="Name" type="xs:string"/>
        </xs:sequence></xs:extension>
      </xs:complexContent></xs:complexType>
    </xs:schema>'''
    result = pipeline().process((AIcdDefsCodegenSourceDocument(Kind.XMLDEFS, 'family.xsd', xsd),))
    assert [t.identity for t in result.types] == ['{urn:family}Base', '{urn:family}Child']
    assert result.types[1].inherited_from_types == ('{urn:family}Base',)
    assert result.types[1].structure.children[0].name == 'Name'


def test_json_defs_local_inheritance_resolves_and_retains_named_declaration():
    source = {'x-algites-schema-id': 'urn:models', '$defs': {
        'Base': {'type': 'object', 'properties': {'id': {'type': 'integer'}}},
        'Child': {'type': 'object', 'allOf': [{'$ref': '#/$defs/Base'}],
                  'properties': {'name': {'type': 'string'}}}}}
    result = pipeline().process((AIcdDefsCodegenSourceDocument(Kind.JSONDEFS, 'models.json', source),))
    assert [t.identity for t in result.types] == ['urn:models#/$defs/Base', 'urn:models#/$defs/Child']
    assert result.types[1].inherited_from_types == ('urn:models#/$defs/Base',)


def test_xsd_qnames_distinguish_builtin_and_same_named_declared_type():
    xsd = '''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
                        xmlns:tns="urn:test" targetNamespace="urn:test">
      <xs:complexType name="string"><xs:sequence>
        <xs:element name="marker" type="xs:boolean"/>
      </xs:sequence></xs:complexType>
      <xs:complexType name="Holder"><xs:sequence>
        <xs:element name="builtin" type="xs:string"/>
        <xs:element name="user" type="tns:string"/>
      </xs:sequence></xs:complexType>
    </xs:schema>'''
    result = pipeline().process((AIcdDefsCodegenSourceDocument(Kind.XMLDEFS, 'types.xsd', xsd),))
    holder = next(type_ for type_ in result.types if type_.name == 'Holder')
    builtin, named = holder.structure.children
    assert builtin.structure.scalar_kind.value == 'STRING'
    assert named.structure.target_identity == '{urn:test}string'
    assert named.structure.identity == '{urn:test}string'


def test_xsd_unknown_qname_prefix_is_an_error_not_local_name_alias():
    xsd = '''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
        <xs:complexType name="Node"><xs:sequence>
           <xs:element name="child" type="missing:Node"/>
        </xs:sequence></xs:complexType></xs:schema>'''
    with pytest.raises(ValueError, match='Undeclared XSD QName prefix'):
        pipeline().process((AIcdDefsCodegenSourceDocument(Kind.XMLDEFS, 'broken.xsd', xsd),))
