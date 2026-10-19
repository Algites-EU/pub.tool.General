"""Regression coverage for conservative XSD complex-content derivation projections."""
from pathlib import Path
import pytest

from eu.algites.lib.naming.convention.impl.algites.aic_algites_naming_profiles_1 import AIcAlgitesNamingProfiles_1
from eu.algites.lib.data.dataobject.ain_field_presence_kind import AInFieldPresenceKind
from eu.algites.tool.codegen.defs.aicd_definition_load_request import AIcdDefinitionLoadRequest
from eu.algites.tool.codegen.defs.ain_definition_source_kind import AInDefinitionSourceKind
from eu.algites.tool.codegen.defs.impl.standard.aic_xml_defs_frontend import AIcXmlDefsFrontend


_SCHEMA = '''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
  xmlns:tns="urn:derivation" targetNamespace="urn:derivation" version="1">
  <xs:complexType name="Base"><xs:sequence><xs:element name="amount" type="xs:decimal"/>
  </xs:sequence><xs:attribute name="code" type="xs:string" use="optional"/></xs:complexType>
  <xs:complexType name="Derived"><xs:complexContent><xs:extension base="tns:Base">
    <xs:sequence><xs:element name="wallet" type="xs:string" minOccurs="0"/></xs:sequence>
    <xs:attribute name="network" type="xs:string" use="required"/>
  </xs:extension></xs:complexContent></xs:complexType>
  <xs:element name="root" type="tns:Derived"/>
</xs:schema>'''


def _load(tmp_path, xml):
    path = tmp_path / 'derived_1.xsd'
    path.write_text(xml)
    req = AIcdDefinitionLoadRequest(path, AInDefinitionSourceKind.XMLDEFS,
        AIcAlgitesNamingProfiles_1.python_profile())
    return AIcXmlDefsFrontend().load(req)


def test_same_schema_extension_retains_inherited_and_new_fields(tmp_path):
    model = _load(tmp_path, _SCHEMA)
    fields = {p.source_name: p for p in model.data_type.properties}
    assert set(fields) == {'amount', 'code', 'wallet', 'network'}
    assert fields['amount'].presence is AInFieldPresenceKind.REQUIRED
    assert fields['wallet'].presence is AInFieldPresenceKind.ALLOWED
    assert fields['network'].presence is AInFieldPresenceKind.REQUIRED


def test_attribute_restriction_prohibits_inherited_optional_attribute(tmp_path):
    xml = '''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
      xmlns:tns="urn:derivation" targetNamespace="urn:derivation" version="1">
      <xs:complexType name="Base"><xs:attribute name="code" type="xs:string" use="optional"/></xs:complexType>
      <xs:complexType name="Derived"><xs:complexContent><xs:restriction base="tns:Base">
        <xs:attribute name="code" type="xs:string" use="prohibited"/>
      </xs:restriction></xs:complexContent></xs:complexType>
      <xs:element name="root" type="tns:Derived"/>
    </xs:schema>'''
    model = _load(tmp_path, xml)
    assert model.data_type.properties[0].presence is AInFieldPresenceKind.FORBIDDEN


def test_attribute_restriction_missing_optional_becomes_forbidden(tmp_path):
    xml = '''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
      xmlns:tns="urn:derivation" targetNamespace="urn:derivation" version="1">
      <xs:complexType name="Base"><xs:attribute name="code" type="xs:string" use="optional"/></xs:complexType>
      <xs:complexType name="Derived"><xs:complexContent><xs:restriction base="tns:Base"/>
      </xs:complexContent></xs:complexType>
      <xs:element name="root" type="tns:Derived"/>
    </xs:schema>'''
    assert _load(tmp_path, xml).data_type.properties[0].presence is AInFieldPresenceKind.FORBIDDEN


def test_element_particle_restriction_is_rejected_not_silently_flattened(tmp_path):
    xml = _SCHEMA.replace('<xs:extension base="tns:Base">', '<xs:restriction base="tns:Base">').replace(
        '</xs:extension>', '</xs:restriction>')
    with pytest.raises(ValueError, match='particle restriction'):
        _load(tmp_path, xml)


def test_circular_extension_is_rejected(tmp_path):
    xml = '''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
      xmlns:tns="urn:derivation" targetNamespace="urn:derivation" version="1">
      <xs:complexType name="Base"><xs:complexContent><xs:extension base="tns:Derived"/></xs:complexContent></xs:complexType>
      <xs:complexType name="Derived"><xs:complexContent><xs:extension base="tns:Base"/></xs:complexContent></xs:complexType>
      <xs:element name="root" type="tns:Derived"/>
    </xs:schema>'''
    with pytest.raises(ValueError, match='Circular'):
        _load(tmp_path, xml)
