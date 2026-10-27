"""Lossless repetition of compositor groups containing one mandatory element."""
from pathlib import Path

import pytest
from eu.algites.lib.data.dataobject.ain_field_presence_kind import AInFieldPresenceKind
from eu.algites.lib.naming.convention.profile.algites.aic_algites_naming_profiles import AIcAlgitesNamingProfiles
from eu.algites.tool.codegen.defs.ain_data_type_kind import AInDataTypeKind
from eu.algites.tool.codegen.defs.ain_definition_source_kind import AInDefinitionSourceKind
from eu.algites.tool.codegen.defs.aicd_definition_load_request import AIcdDefinitionLoadRequest
from eu.algites.tool.codegen.defs.impl.standard.aic_xml_defs_frontend import AIcXmlDefsFrontend


def _load(tmp_path: Path, content: str):
    path = tmp_path / 'composite_1.xsd'
    path.write_text('''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
      xmlns:n="urn:group" targetNamespace="urn:group" elementFormDefault="qualified" version="1">
      ''' + content + '</xs:schema>')
    return AIcXmlDefsFrontend().load(AIcdDefinitionLoadRequest(
        path, AInDefinitionSourceKind.XMLDEFS, AIcAlgitesNamingProfiles.python_profile()))


@pytest.mark.parametrize('compositor', ('sequence', 'all'))
def test_repeated_single_leaf_compositor_is_an_array(tmp_path, compositor):
    result = _load(tmp_path, f'''<xs:complexType name="Composite"><xs:{compositor}
        minOccurs="2" maxOccurs="4"><xs:element name="Code" type="xs:string"/>
        </xs:{compositor}></xs:complexType>''')
    field, = result.data_type.properties
    assert field.source_name == 'Code'
    assert field.presence is AInFieldPresenceKind.REQUIRED
    assert field.data_type.kind is AInDataTypeKind.ARRAY
    assert field.data_type.element_type.kind is AInDataTypeKind.STRING
    assert (field.data_type.constraints.min_items, field.data_type.constraints.max_items) == (2, 4)
    assert (field.xml_field.namespace, field.xml_field.namespace_local_name) == ('urn:group', 'Code')


def test_repeated_reference_to_one_leaf_model_group(tmp_path):
    result = _load(tmp_path, '''
      <xs:group name="CodeGroup"><xs:sequence><xs:element name="Code" type="xs:string"/></xs:sequence></xs:group>
      <xs:complexType name="Composite"><xs:sequence><xs:group ref="n:CodeGroup"
        minOccurs="0" maxOccurs="unbounded"/></xs:sequence></xs:complexType>''')
    field, = result.data_type.properties
    assert field.presence is AInFieldPresenceKind.ALLOWED
    assert field.data_type.kind is AInDataTypeKind.ARRAY
    assert (field.data_type.constraints.min_items, field.data_type.constraints.max_items) == (0, None)


@pytest.mark.parametrize('content', (
    '<xs:sequence maxOccurs="3"><xs:element name="A" type="xs:string"/><xs:element name="B" type="xs:string"/></xs:sequence>',
    '<xs:sequence maxOccurs="3"><xs:element name="A" type="xs:string" maxOccurs="2"/></xs:sequence>',
    '<xs:sequence minOccurs="0"><xs:element name="A" type="xs:string"/><xs:element name="B" type="xs:string"/></xs:sequence>',
))
def test_correlated_group_structure_still_fails_closed(tmp_path, content):
    with pytest.raises(ValueError, match='[Cc]ompositor.*group cardinality'):
        _load(tmp_path, '<xs:complexType name="Composite">' + content + '</xs:complexType>')
