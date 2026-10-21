"""Lossless xs:any fragment projection shared by Java and Python contracts."""
from pathlib import Path
import pytest

from eu.algites.tool.codegen.defs.impl.standard.aic_xml_defs_frontend import AIcXmlDefsFrontend
from eu.algites.tool.codegen.defs.aicd_definition_load_request import AIcdDefinitionLoadRequest
from eu.algites.tool.codegen.defs.ain_definition_source_kind import AInDefinitionSourceKind
from eu.algites.tool.codegen.defs.ain_data_type_kind import AInDataTypeKind
from eu.algites.lib.data.dataobject.xmldefs.ain_xml_value_kind import AInXmlValueKind


XSD = '''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
 targetNamespace="urn:builder:technology" xmlns="urn:builder:technology">
 <xs:complexType name="ExtensionsType"><xs:sequence>
   <xs:element name="Key" type="xs:string"/>
   <xs:any namespace="##other" processContents="lax" minOccurs="0" maxOccurs="unbounded"/>
 </xs:sequence></xs:complexType>
 <xs:element name="Extensions" type="ExtensionsType"/>
</xs:schema>'''


def test_xml_value_kind_contains_only_element_and_attribute():
    assert {kind.value for kind in AInXmlValueKind} == {'element', 'attribute'}


def test_xsd_wildcard_preserves_namespace_policy_and_subtree_type(tmp_path):
    path = tmp_path / 'extensions_1.xsd'
    path.write_text(XSD)
    definition = AIcXmlDefsFrontend().load(AIcdDefinitionLoadRequest(
        path, AInDefinitionSourceKind.XMLDEFS, None))
    wildcards = [field for field in definition.data_type.properties
        if field.xml_field is not None and field.xml_field.wildcard_namespace]
    assert len(wildcards) == 1
    wildcard = wildcards[0]
    assert wildcard.data_type.kind is AInDataTypeKind.ARRAY
    assert wildcard.data_type.element_type.kind is AInDataTypeKind.ANY
    assert wildcard.xml_field.namespace == 'urn:builder:technology'
    assert wildcard.xml_field.value_kind is AInXmlValueKind.ELEMENT
    assert wildcard.xml_field.wildcard_namespace == '##other'
    assert wildcard.xml_field.wildcard_process_contents == 'lax'
    assert wildcard.xml_field.min_occurs == 0
    assert wildcard.xml_field.max_occurs == -1


def test_invalid_wildcard_policy_is_rejected(tmp_path):
    path = tmp_path / 'extensions_1.xsd'
    path.write_text(XSD.replace('processContents="lax"', 'processContents="invalid"'))
    with pytest.raises(ValueError, match='processContents'):
        AIcXmlDefsFrontend().load(AIcdDefinitionLoadRequest(
            path, AInDefinitionSourceKind.XMLDEFS, None))
