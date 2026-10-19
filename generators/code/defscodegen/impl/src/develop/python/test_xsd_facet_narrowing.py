"""Ensure Java/Python XSD projections preserve monotonic scalar restrictions."""
from pathlib import Path

import pytest

from eu.algites.lib.naming.convention.impl.algites.aic_algites_naming_profiles_1 import AIcAlgitesNamingProfiles_1
from eu.algites.tool.codegen.defs.aicd_definition_load_request import AIcdDefinitionLoadRequest
from eu.algites.tool.codegen.defs.ain_definition_source_kind import AInDefinitionSourceKind
from eu.algites.tool.codegen.defs.impl.standard.aic_xml_defs_frontend import AIcXmlDefsFrontend


def _load(tmp_path: Path, base: str, derived: str, *, base_type='xs:decimal', field_type='Derived'):
    path = tmp_path / 'facets_1.xsd'
    path.write_text(f'''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
        xmlns:tns="urn:facets" targetNamespace="urn:facets" version="1">
      <xs:simpleType name="Base"><xs:restriction base="{base_type}">{base}</xs:restriction></xs:simpleType>
      <xs:simpleType name="Derived"><xs:restriction base="tns:Base">{derived}</xs:restriction></xs:simpleType>
      <xs:complexType name="Container"><xs:attribute name="code" type="tns:{field_type}"/></xs:complexType>
      <xs:element name="root" type="tns:Container"/>
    </xs:schema>''')
    request = AIcdDefinitionLoadRequest(path, AInDefinitionSourceKind.XMLDEFS,
        AIcAlgitesNamingProfiles_1.python_profile())
    return AIcXmlDefsFrontend().load(request)


def test_derived_decimal_restriction_preserves_stricter_bounds(tmp_path):
    model = _load(tmp_path, '<xs:minInclusive value="10"/><xs:maxExclusive value="200"/>',
        '<xs:minExclusive value="10"/><xs:maxInclusive value="100"/>')
    constraints = model.data_type.properties[0].data_type.constraints
    assert constraints.minimum == '10' and constraints.exclusive_minimum
    assert constraints.maximum == '100' and not constraints.exclusive_maximum


@pytest.mark.parametrize('base,derived,message', [
    ('<xs:minInclusive value="10"/>', '<xs:minInclusive value="9"/>', 'minimum'),
    ('<xs:minExclusive value="10"/>', '<xs:minInclusive value="10"/>', 'minimum'),
    ('<xs:maxInclusive value="10"/>', '<xs:maxInclusive value="11"/>', 'maximum'),
    ('<xs:maxExclusive value="10"/>', '<xs:maxInclusive value="10"/>', 'maximum'),
    ('<xs:minInclusive value="10"/>', '<xs:maxExclusive value="10"/>', 'numeric restriction'),
    ('<xs:minInclusive value="10"/>', '<xs:totalDigits value="5"/>', 'Unsupported XSD restriction facet'),
])
def test_unsafe_or_unrepresented_numeric_facets_fail_closed(tmp_path, base, derived, message):
    with pytest.raises(ValueError, match=message):
        _load(tmp_path, base, derived)


@pytest.mark.parametrize('base,derived,message', [
    ('<xs:minLength value="3"/>', '<xs:minLength value="2"/>', 'minLength'),
    ('<xs:maxLength value="5"/>', '<xs:maxLength value="6"/>', 'maxLength'),
    ('<xs:minLength value="3"/>', '<xs:maxLength value="2"/>', 'length restriction'),
    ('<xs:pattern value="[A-Z]+"/>', '<xs:pattern value="[A-Z]{3}"/>', 'inherited XSD pattern'),
    ('<xs:enumeration value="A"/><xs:enumeration value="B"/>',
     '<xs:enumeration value="C"/>', 'enumeration'),
])
def test_unsafe_string_restrictions_fail_closed(tmp_path, base, derived, message):
    with pytest.raises(ValueError, match=message):
        _load(tmp_path, base, derived, base_type='xs:string')


def test_derived_enumeration_must_be_subset(tmp_path):
    model = _load(tmp_path, '<xs:enumeration value="A"/><xs:enumeration value="B"/>',
        '<xs:enumeration value="B"/>', base_type='xs:string')
    assert model.data_type.properties[0].data_type.constraints.enum_values == ('B',)


def test_complex_content_attribute_restriction_cannot_discard_base_facets(tmp_path):
    path = tmp_path / 'restriction_1.xsd'
    path.write_text('''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
        xmlns:tns="urn:facets" targetNamespace="urn:facets" version="1">
      <xs:simpleType name="Code"><xs:restriction base="xs:string"><xs:minLength value="3"/></xs:restriction></xs:simpleType>
      <xs:complexType name="Base"><xs:attribute name="code" type="tns:Code"/></xs:complexType>
      <xs:complexType name="Derived"><xs:complexContent><xs:restriction base="tns:Base">
        <xs:attribute name="code" type="xs:string"/>
      </xs:restriction></xs:complexContent></xs:complexType>
      <xs:element name="root" type="tns:Derived"/>
    </xs:schema>''')
    request = AIcdDefinitionLoadRequest(path, AInDefinitionSourceKind.XMLDEFS,
        AIcAlgitesNamingProfiles_1.python_profile())
    with pytest.raises(ValueError, match='minLength'):
        AIcXmlDefsFrontend().load(request)


def test_prohibited_attribute_without_explicit_type_keeps_base_constraints(tmp_path):
    path = tmp_path / 'prohibited_1.xsd'
    path.write_text('''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
        xmlns:tns="urn:facets" targetNamespace="urn:facets" version="1">
      <xs:simpleType name="Code"><xs:restriction base="xs:string"><xs:minLength value="3"/></xs:restriction></xs:simpleType>
      <xs:complexType name="Base"><xs:attribute name="code" type="tns:Code"/></xs:complexType>
      <xs:complexType name="Derived"><xs:complexContent><xs:restriction base="tns:Base">
        <xs:attribute name="code" use="prohibited"/>
      </xs:restriction></xs:complexContent></xs:complexType>
      <xs:element name="root" type="tns:Derived"/>
    </xs:schema>''')
    request = AIcdDefinitionLoadRequest(path, AInDefinitionSourceKind.XMLDEFS,
        AIcAlgitesNamingProfiles_1.python_profile())
    model = AIcXmlDefsFrontend().load(request)
    field = model.data_type.properties[0]
    from eu.algites.lib.data.dataobject.ain_field_presence_kind import AInFieldPresenceKind
    assert field.presence is AInFieldPresenceKind.FORBIDDEN
    assert field.data_type.constraints.min_length == 3
