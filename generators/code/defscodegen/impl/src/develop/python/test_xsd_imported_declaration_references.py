"""Imported XSD declaration references retain their expanded XML names and types."""

import pytest

from eu.algites.lib.naming.convention.profile.algites.aic_algites_naming_profiles import AIcAlgitesNamingProfiles
from eu.algites.tool.codegen.defs.aicd_definition_load_request import AIcdDefinitionLoadRequest
from eu.algites.tool.codegen.defs.ain_definition_source_kind import AInDefinitionSourceKind
from eu.algites.tool.codegen.defs.impl.standard.aic_xml_defs_frontend import AIcXmlDefsFrontend
from eu.algites.lib.data.dataobject.ain_field_presence_kind import AInFieldPresenceKind
from eu.algites.lib.data.dataobject.xmldefs.ain_xml_value_kind import AInXmlValueKind


def _load(path):
    request = AIcdDefinitionLoadRequest(path, AInDefinitionSourceKind.XMLDEFS,
                                       AIcAlgitesNamingProfiles.python_profile())
    return AIcXmlDefsFrontend().load(request).data_type.properties


def _base(path):
    path.write_text('''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
        xmlns:b="urn:base" targetNamespace="urn:base" version="1" elementFormDefault="qualified">
      <xs:element name="Document" type="xs:int" nillable="true"/>
      <xs:group name="Details"><xs:sequence><xs:element name="Nested" type="xs:string"/></xs:sequence></xs:group>
      <xs:attribute name="Token" type="xs:string"/>
      <xs:attributeGroup name="Keys"><xs:attribute ref="b:Token" use="required"/></xs:attributeGroup>
    </xs:schema>''')


def test_external_elements_groups_and_attributes_preserve_owning_namespace(tmp_path):
    base = tmp_path / 'base_1.xsd'
    _base(base)
    derived = tmp_path / 'derived_1.xsd'
    derived.write_text('''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
        xmlns:b="urn:base" targetNamespace="urn:derived" version="1" elementFormDefault="qualified">
      <xs:import namespace="urn:base" schemaLocation="base_1.xsd"/>
      <xs:complexType name="Derived"><xs:sequence>
        <xs:element ref="b:Document" minOccurs="0" maxOccurs="3"/>
        <xs:group ref="b:Details"/>
      </xs:sequence><xs:attributeGroup ref="b:Keys"/></xs:complexType>
    </xs:schema>''')
    props = {field.source_name: field for field in _load(derived)}
    assert set(props) == {'Document', 'Nested', 'Token'}
    assert [(props[k].xml_field.namespace, props[k].xml_field.value_kind) for k in props] == [
        ('urn:base', AInXmlValueKind.ELEMENT),
        ('urn:base', AInXmlValueKind.ELEMENT),
        ('urn:base', AInXmlValueKind.ATTRIBUTE)]
    assert props['Document'].nullable
    assert props['Document'].data_type.constraints.max_items == 3
    assert props['Document'].presence is AInFieldPresenceKind.ALLOWED
    assert props['Token'].presence is AInFieldPresenceKind.REQUIRED


def test_transitive_includes_resolve_declarations(tmp_path):
    (tmp_path / 'leaf_1.xsd').write_text('''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
        targetNamespace="urn:base" version="1"><xs:element name="Item" type="xs:boolean"/></xs:schema>''')
    (tmp_path / 'middle_1.xsd').write_text('''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
        targetNamespace="urn:base" version="1"><xs:include schemaLocation="leaf_1.xsd"/></xs:schema>''')
    path = tmp_path / 'root_1.xsd'
    path.write_text('''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
        xmlns:b="urn:base" targetNamespace="urn:derived" version="1">
       <xs:import namespace="urn:base" schemaLocation="middle_1.xsd"/>
       <xs:complexType name="Root"><xs:sequence><xs:element ref="b:Item"/></xs:sequence></xs:complexType>
    </xs:schema>''')
    field = _load(path)[0]
    assert field.xml_field.namespace == 'urn:base'
    assert field.source_name == 'Item'


@pytest.mark.parametrize('schema_location,namespace', [('https://example.com/evil.xsd', 'urn:base'),
                                                       ('base_1.xsd', 'urn:wrong')])
def test_remote_or_misdeclared_import_rejected(tmp_path, schema_location, namespace):
    _base(tmp_path / 'base_1.xsd')
    path = tmp_path / 'root_1.xsd'
    path.write_text('''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
      xmlns:b="urn:base" targetNamespace="urn:derived" version="1">
      <xs:import namespace="''' + namespace + '''" schemaLocation="''' + schema_location + '''"/>
      <xs:complexType name="Root"><xs:sequence><xs:element ref="b:Document"/></xs:sequence></xs:complexType>
      </xs:schema>''')
    with pytest.raises(ValueError, match='local files|namespace disagrees'):
        _load(path)


def test_ambiguous_declarations_across_includes_rejected(tmp_path):
    _base(tmp_path / 'base_1.xsd')
    _base(tmp_path / 'other_1.xsd')
    path = tmp_path / 'root_1.xsd'
    path.write_text('''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
       xmlns:b="urn:base" targetNamespace="urn:base" version="1">
       <xs:include schemaLocation="base_1.xsd"/>
       <xs:include schemaLocation="other_1.xsd"/>
       <xs:complexType name="Root"><xs:sequence><xs:element ref="b:Document"/></xs:sequence></xs:complexType>
       </xs:schema>''')
    with pytest.raises(ValueError, match='Ambiguous XSD element'):
        _load(path)
