"""Lossless xs:any fragment projection shared by Java and Python contracts."""
from pathlib import Path
import pytest

from eu.algites.tool.codegen.defs.old.impl.standard.aic_xml_defs_frontend import AIcXmlDefsFrontend
from eu.algites.tool.codegen.defs.old.aicd_definition_load_request import AIcdDefinitionLoadRequest
from eu.algites.tool.codegen.defs.old.ain_definition_source_kind import AInDefinitionSourceKind
from eu.algites.lib.naming.convention.impl.standard.aic_name_convention_catalog import AIcNameConventionCatalog


XSD = '''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
 targetNamespace="urn:builder:technology" xmlns="urn:builder:technology">
 <xs:complexType name="ExtensionsType"><xs:sequence>
   <xs:element name="Key" type="xs:string"/>
   <xs:any namespace="##other" processContents="lax" minOccurs="0" maxOccurs="unbounded"/>
 </xs:sequence></xs:complexType>
 <xs:element name="Extensions" type="ExtensionsType"/>
</xs:schema>'''


def test_wildcard_does_not_introduce_additional_dataobject_value_kind():
    from eu.algites.lib.data.dataobject.xmldefs.ain_xml_value_kind import AInXmlValueKind
    assert {kind.value for kind in AInXmlValueKind} == {'element', 'attribute'}


def test_optional_xml_wildcard_is_documented_but_not_generated_as_field(tmp_path):
    path = tmp_path / 'extensions_1.xsd'
    path.write_text(XSD)
    request = AIcdDefinitionLoadRequest(path, AInDefinitionSourceKind.XMLDEFS,
        AIcNameConventionCatalog.load_resource('algites-xmldef-name-conventions.yml'),
            'algites-xmldef-schema-versioned_1')
    with pytest.warns(UserWarning, match='xs:any'):
        definition = AIcXmlDefsFrontend().load(request)
    assert [field.source_name for field in definition.data_type.properties] == ['Key']
    assert 'Ignored optional XML wildcard' in definition.description
    assert '##other' in definition.description
    assert 'processContents="lax"' in definition.description


def test_required_xml_wildcard_is_rejected(tmp_path):
    path = tmp_path / 'extensions_1.xsd'
    path.write_text(XSD.replace('minOccurs="0"', 'minOccurs="1"'))
    with pytest.raises(ValueError, match='Required XML wildcard xs:any'):
        AIcXmlDefsFrontend().load(AIcdDefinitionLoadRequest(path,
            AInDefinitionSourceKind.XMLDEFS,
            AIcNameConventionCatalog.load_resource('algites-xmldef-name-conventions.yml'),
            'algites-xmldef-schema-versioned_1'))


def test_any_attribute_is_optional_without_min_item_count(tmp_path):
    path = tmp_path / 'extensions_1.xsd'
    path.write_text(XSD.replace('</xs:sequence></xs:complexType>',
        '</xs:sequence><xs:anyAttribute namespace="##other" processContents="lax"/></xs:complexType>'))
    request = AIcdDefinitionLoadRequest(path, AInDefinitionSourceKind.XMLDEFS,
        AIcNameConventionCatalog.load_resource('algites-xmldef-name-conventions.yml'),
            'algites-xmldef-schema-versioned_1')
    with pytest.warns(UserWarning):
        definition = AIcXmlDefsFrontend().load(request)
    assert [field.source_name for field in definition.data_type.properties] == ['Key']
    assert 'xs:anyAttribute' in definition.description or 'anyAttribute' in definition.description
    assert 'xs:any' in definition.description or 'ns0:any' in definition.description


def test_invalid_wildcard_policy_is_rejected(tmp_path):
    path = tmp_path / 'extensions_1.xsd'
    path.write_text(XSD.replace('processContents="lax"', 'processContents="invalid"'))
    with pytest.raises(ValueError, match='processContents'):
        AIcXmlDefsFrontend().load(AIcdDefinitionLoadRequest(
            path, AInDefinitionSourceKind.XMLDEFS,
            AIcNameConventionCatalog.load_resource('algites-xmldef-name-conventions.yml'),
            'algites-xmldef-schema-versioned_1'))


def test_wildcard_in_optional_group_is_not_required(tmp_path):
    path = tmp_path / 'extensions_1.xsd'
    path.write_text(XSD.replace(
        '<xs:complexType name="ExtensionsType"><xs:sequence>',
        '<xs:complexType name="ExtensionsType"><xs:sequence minOccurs="0">').replace(
        '<xs:any namespace="##other" processContents="lax" minOccurs="0"',
        '<xs:any namespace="##other" processContents="lax" minOccurs="1"'))
    request = AIcdDefinitionLoadRequest(path, AInDefinitionSourceKind.XMLDEFS,
        AIcNameConventionCatalog.load_resource('algites-xmldef-name-conventions.yml'),
        'algites-xmldef-schema-versioned_1')
    with pytest.warns(UserWarning, match='xs:any'):
        definition = AIcXmlDefsFrontend().load(request)
    assert [field.source_name for field in definition.data_type.properties] == ['Key']
