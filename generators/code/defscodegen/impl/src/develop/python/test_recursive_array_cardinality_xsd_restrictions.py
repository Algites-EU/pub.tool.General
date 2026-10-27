"""Recursively retained JSON/XSD array intervals and safe XML sequence restrictions."""
import json

import pytest

from eu.algites.lib.naming.convention.profile.algites.aic_algites_naming_profiles import AIcAlgitesNamingProfiles
from explicit_legacy_naming import configured_load as AIcdDefinitionLoadRequest
from eu.algites.tool.codegen.defs.ain_definition_source_kind import AInDefinitionSourceKind
from eu.algites.tool.codegen.defs.ain_data_type_kind import AInDataTypeKind
from eu.algites.tool.codegen.defs.aicd_value_constraints import AIcdValueConstraints
from eu.algites.tool.codegen.defs.impl.standard.aic_json_defs_frontend import AIcJsonDefsFrontend
from eu.algites.tool.codegen.defs.impl.standard.aic_xml_defs_frontend import AIcXmlDefsFrontend
from eu.algites.lib.data.dataobject.ain_field_presence_kind import AInFieldPresenceKind


def _request(path, kind=AInDefinitionSourceKind.XMLDEFS):
    return AIcdDefinitionLoadRequest(path, kind, AIcAlgitesNamingProfiles.python_profile())


def _xml(tmp_path, content):
    path = tmp_path / 'cardinality_1.xsd'
    path.write_text('''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
        xmlns:tns="urn:cards" targetNamespace="urn:cards" version="1" elementFormDefault="qualified">'''
        + content + '</xs:schema>')
    return path


def test_xml_array_occurrence_interval_remains_on_array_node(tmp_path):
    path = _xml(tmp_path, '''<xs:complexType name="Root"><xs:sequence>
      <xs:element name="codes" type="xs:string" minOccurs="2" maxOccurs="5"/>
      <xs:element name="extras" type="xs:int" minOccurs="0" maxOccurs="unbounded"/>
      <xs:element name="absent" type="xs:string" minOccurs="0" maxOccurs="0"/>
    </xs:sequence></xs:complexType>''')
    fields = {field.source_name: field for field in AIcXmlDefsFrontend().load(_request(path)).data_type.properties}
    assert fields['codes'].data_type.kind is AInDataTypeKind.ARRAY
    assert fields['codes'].data_type.constraints.min_items == 2
    assert fields['codes'].data_type.constraints.max_items == 5
    assert fields['codes'].data_type.element_type.constraints.data_type == 'string'
    assert fields['extras'].data_type.constraints.min_items == 0
    assert fields['extras'].data_type.constraints.max_items is None
    assert fields['absent'].presence is AInFieldPresenceKind.FORBIDDEN


def test_json_recursive_arrays_retain_independent_bounds(tmp_path):
    path = tmp_path / 'cardinality_1.jsondef.schema.json'
    path.write_text(json.dumps({'type': 'object', 'properties': {'nested': {'type': 'array',
        'minItems': 1, 'maxItems': 3, 'items': {'type': 'array', 'minItems': 2,
        'maxItems': 4, 'items': {'type': 'integer'}}}}}))
    typ = AIcJsonDefsFrontend().load(_request(path, AInDefinitionSourceKind.JSONDEFS)).data_type
    array = typ.properties[0].data_type
    assert (array.constraints.min_items, array.constraints.max_items) == (1, 3)
    assert (array.element_type.constraints.min_items, array.element_type.constraints.max_items) == (2, 4)
    assert array.element_type.element_type.kind is AInDataTypeKind.INTEGER


def test_flat_sequence_restriction_narrows_array_cardinality(tmp_path):
    path = _xml(tmp_path, '''<xs:complexType name="Base"><xs:sequence>
      <xs:element name="entries" type="xs:string" minOccurs="0" maxOccurs="9"/>
      <xs:element name="optional" type="xs:string" minOccurs="0"/>
    </xs:sequence></xs:complexType>
    <xs:complexType name="Derived"><xs:complexContent>
      <xs:restriction base="tns:Base"><xs:sequence>
        <xs:element name="entries" type="xs:string" minOccurs="2" maxOccurs="4"/>
      </xs:sequence></xs:restriction>
    </xs:complexContent></xs:complexType>''')
    fields = {field.source_name: field for field in AIcXmlDefsFrontend().load_named_type(_request(path), 'Derived').data_type.properties}
    assert (fields['entries'].data_type.constraints.min_items, fields['entries'].data_type.constraints.max_items) == (2, 4)
    assert fields['entries'].presence is AInFieldPresenceKind.REQUIRED
    assert fields['optional'].presence is AInFieldPresenceKind.FORBIDDEN


@pytest.mark.parametrize('minimum,maximum,pattern', [
    (0, 10, 'minOccurs'),
    (2, 12, 'maxOccurs'),
])
def test_sequence_restriction_must_not_widen_array_interval(tmp_path, minimum, maximum, pattern):
    path = _xml(tmp_path, f'''<xs:complexType name="Base"><xs:sequence>
       <xs:element name="entries" type="xs:string" minOccurs="1" maxOccurs="10"/>
       </xs:sequence></xs:complexType>
       <xs:complexType name="Derived"><xs:complexContent><xs:restriction base="tns:Base">
       <xs:sequence><xs:element name="entries" type="xs:string" minOccurs="{minimum}"
          maxOccurs="{maximum}"/></xs:sequence>
       </xs:restriction></xs:complexContent></xs:complexType>''')
    with pytest.raises(ValueError, match=pattern):
        AIcXmlDefsFrontend().load_named_type(_request(path), 'Derived')


def test_sequence_restriction_must_not_change_nested_scalar_type(tmp_path):
    path = _xml(tmp_path, '''<xs:complexType name="Base"><xs:sequence>
      <xs:element name="entries" type="xs:string" minOccurs="1" maxOccurs="10"/>
    </xs:sequence></xs:complexType>
    <xs:complexType name="Derived"><xs:complexContent><xs:restriction base="tns:Base">
      <xs:sequence><xs:element name="entries" type="xs:int" minOccurs="1" maxOccurs="5"/></xs:sequence>
    </xs:restriction></xs:complexContent></xs:complexType>''')
    with pytest.raises(ValueError, match='changes the type'):
        AIcXmlDefsFrontend().load_named_type(_request(path), 'Derived')


def test_optional_compositor_of_several_elements_requires_group_model(tmp_path):
    path = _xml(tmp_path, '''<xs:complexType name="Root"><xs:sequence minOccurs="0">
      <xs:element name="first" type="xs:string"/>
      <xs:element name="second" type="xs:string"/>
    </xs:sequence></xs:complexType>''')
    with pytest.raises(ValueError, match='Optional XSD compositor'):
        AIcXmlDefsFrontend().load(_request(path))


@pytest.mark.parametrize('minimum,maximum', [(-1, 4), (3, 2)])
def test_invalid_canonical_cardinality_rejected(minimum, maximum):
    with pytest.raises(ValueError):
        AIcdValueConstraints(min_items=minimum, max_items=maximum)


def test_local_xsd_group_reference_expands_without_losing_field_qnames(tmp_path):
    path = _xml(tmp_path, '''<xs:group name="Details"><xs:sequence>
      <xs:element name="first" type="xs:string"/>
      <xs:element name="second" type="xs:int" minOccurs="0" maxOccurs="3"/>
    </xs:sequence></xs:group>
    <xs:complexType name="Root"><xs:sequence>
      <xs:group ref="tns:Details"/>
    </xs:sequence></xs:complexType>''')
    fields = AIcXmlDefsFrontend().load(_request(path)).data_type.properties
    assert [p.source_name for p in fields] == ['first', 'second']
    assert all(p.xml_field.namespace == 'urn:cards' for p in fields)
    assert fields[1].data_type.constraints.max_items == 3


def test_optional_multi_element_xsd_group_fails_closed(tmp_path):
    path = _xml(tmp_path, '''<xs:group name="Details"><xs:sequence>
      <xs:element name="first" type="xs:string"/>
      <xs:element name="second" type="xs:string"/>
    </xs:sequence></xs:group>
    <xs:complexType name="Root"><xs:sequence>
      <xs:group ref="tns:Details" minOccurs="0"/>
    </xs:sequence></xs:complexType>''')
    with pytest.raises(ValueError, match='Optional XSD compositor'):
        AIcXmlDefsFrontend().load(_request(path))


def test_recursive_xsd_group_reference_fails_closed(tmp_path):
    path = _xml(tmp_path, '''<xs:group name="Circular"><xs:sequence>
      <xs:group ref="tns:Circular"/>
    </xs:sequence></xs:group>
    <xs:complexType name="Root"><xs:sequence>
      <xs:group ref="tns:Circular"/>
    </xs:sequence></xs:complexType>''')
    with pytest.raises(ValueError, match='Circular XSD group'):
        AIcXmlDefsFrontend().load(_request(path))


def test_local_named_attribute_group_preserves_optional_and_required_attributes(tmp_path):
    path = _xml(tmp_path, '''<xs:attributeGroup name="Meta">
      <xs:attribute name="revision" type="xs:int" use="required"/>
      <xs:attribute name="caption" type="xs:string"/>
    </xs:attributeGroup>
    <xs:complexType name="Root"><xs:sequence>
      <xs:element name="body" type="xs:string"/>
    </xs:sequence><xs:attributeGroup ref="tns:Meta"/></xs:complexType>''')
    fields = {p.source_name: p for p in AIcXmlDefsFrontend().load(_request(path)).data_type.properties}
    assert fields['revision'].presence is AInFieldPresenceKind.REQUIRED
    assert fields['revision'].xml_field.value_kind.name == 'ATTRIBUTE'
    assert fields['caption'].presence is AInFieldPresenceKind.ALLOWED


def test_cyclic_attribute_group_is_rejected(tmp_path):
    path = _xml(tmp_path, '''<xs:attributeGroup name="Loop">
      <xs:attributeGroup ref="tns:Loop"/>
    </xs:attributeGroup>
    <xs:complexType name="Root"><xs:attributeGroup ref="tns:Loop"/></xs:complexType>''')
    with pytest.raises(ValueError, match='Circular XSD attributeGroup'):
        AIcXmlDefsFrontend().load(_request(path))


def test_cross_format_scalar_array_leaf_mismatch_is_not_ignored():
    from eu.algites.tool.codegen.defs.aicd_canonical_definition import AIcdCanonicalDefinition
    from eu.algites.tool.codegen.defs.aicd_property_definition import AIcdPropertyDefinition
    from eu.algites.tool.codegen.defs.aicd_data_type import AIcdDataType
    from eu.algites.tool.codegen.defs.impl.standard.aic_canonical_definition_merger import AIcCanonicalDefinitionMerger

    def model(source_kind, scalar_kind):
        prop = AIcdPropertyDefinition('values', AIcdDataType(AInDataTypeKind.ARRAY,
            element_type=AIcdDataType(AInDataTypeKind.ARRAY,
                element_type=AIcdDataType(scalar_kind))), AInFieldPresenceKind.REQUIRED,
            False, None, None, None)
        return AIcdCanonicalDefinition('urn:example', 1, 'example', source_kind,
            f'example_1.{source_kind.value}', None, AIcdDataType(AInDataTypeKind.OBJECT,
                properties=(prop,)), (), None)

    with pytest.raises(ValueError, match=r'items\.items\.kind'):
        AIcCanonicalDefinitionMerger.validate((model(AInDefinitionSourceKind.XMLDEFS, AInDataTypeKind.STRING),
            model(AInDefinitionSourceKind.JSONDEFS, AInDataTypeKind.INTEGER)))


def test_json_array_bound_conflict_is_reported_by_canonical_merger():
    from eu.algites.tool.codegen.defs.aicd_canonical_definition import AIcdCanonicalDefinition
    from eu.algites.tool.codegen.defs.aicd_data_type import AIcdDataType
    from eu.algites.tool.codegen.defs.impl.standard.aic_canonical_definition_merger import AIcCanonicalDefinitionMerger

    def model(kind, minimum):
        return AIcdCanonicalDefinition('urn:example', 1, 'example', kind, f'{kind.value}_1.json',
            None, AIcdDataType(AInDataTypeKind.ARRAY,
                element_type=AIcdDataType(AInDataTypeKind.STRING),
                constraints=AIcdValueConstraints(min_items=minimum)), (), None)

    with pytest.raises(ValueError, match='min_items'):
        AIcCanonicalDefinitionMerger.validate((model(AInDefinitionSourceKind.JSONDEFS, 1),
            model(AInDefinitionSourceKind.YAMLDEFS, 2)))


@pytest.mark.parametrize('bounds', [
    {'minItems': '2'},
    {'minItems': -1},
    {'minItems': 2.5},
    {'minItems': 5, 'maxItems': 3},
])
def test_invalid_json_array_interval_is_rejected(tmp_path, bounds):
    path = tmp_path / 'invalid_1.jsondef.schema.json'
    path.write_text(json.dumps({'type': 'array', 'items': {'type': 'string'}, **bounds}))
    with pytest.raises(ValueError):
        AIcJsonDefsFrontend().load(_request(path, AInDefinitionSourceKind.JSONDEFS))


def test_global_element_ref_preserves_declared_qname_even_when_local_fields_unqualified(tmp_path):
    path = tmp_path / 'global-ref_1.xsd'
    path.write_text('''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
        xmlns:tns="urn:global" targetNamespace="urn:global" version="1"
        elementFormDefault="unqualified">
      <xs:element name="GlobalCode" type="xs:string" nillable="true"/>
      <xs:complexType name="Root"><xs:sequence>
        <xs:element ref="tns:GlobalCode" minOccurs="0" maxOccurs="4"/>
      </xs:sequence></xs:complexType>
    </xs:schema>''')
    field = AIcXmlDefsFrontend().load(_request(path)).data_type.properties[0]
    assert field.source_name == 'GlobalCode'
    assert field.xml_field.namespace == 'urn:global'
    assert field.xml_field.namespace_local_name == 'GlobalCode'
    assert field.nullable
    assert field.data_type.constraints.max_items == 4


def test_closed_choice_accepts_local_global_element_references(tmp_path):
    path = _xml(tmp_path, '''<xs:element name="Alpha" type="xs:string"/>
      <xs:element name="Beta" type="xs:int"/>
      <xs:complexType name="Root"><xs:choice>
        <xs:element ref="tns:Alpha"/>
        <xs:element ref="tns:Beta"/>
      </xs:choice></xs:complexType>''')
    choice = AIcXmlDefsFrontend().load_named_type(_request(path), 'Root').data_type
    assert choice.kind is AInDataTypeKind.ONE_OF
    assert [alt.properties[0].source_name for alt in choice.alternatives] == ['Alpha', 'Beta']
    assert all(alt.properties[0].xml_field.namespace == 'urn:cards' for alt in choice.alternatives)


def test_imported_global_element_reference_fails_without_cross_schema_binding(tmp_path):
    path = _xml(tmp_path, '''<xs:complexType name="Root"><xs:sequence>
      <xs:element ref="remote:Other"/>
    </xs:sequence></xs:complexType>''')
    text = path.read_text().replace('xmlns:tns="urn:cards"',
        'xmlns:tns="urn:cards" xmlns:remote="urn:other"')
    path.write_text(text)
    with pytest.raises(ValueError, match='Unknown XSD element reference'):
        AIcXmlDefsFrontend().load(_request(path))
