"""Unsupported XSD content models must not silently generate incomplete interfaces."""
from pathlib import Path

import pytest

from eu.algites.lib.naming.convention.profile.algites.aic_algites_naming_profiles import AIcAlgitesNamingProfiles
from eu.algites.tool.codegen.defs.aicd_definition_load_request import AIcdDefinitionLoadRequest
from eu.algites.tool.codegen.defs.ain_definition_source_kind import AInDefinitionSourceKind
from eu.algites.tool.codegen.defs.impl.standard.aic_xml_defs_frontend import AIcXmlDefsFrontend


@pytest.mark.parametrize('particle', [
    '<xs:assert test="true()"/>',
    '<xs:openContent mode="interleave"><xs:any/></xs:openContent>',
    '<xs:sequence><xs:assert test="true()"/></xs:sequence>',
])
def test_unsupported_schema_children_cannot_be_discarded(tmp_path: Path, particle: str):
    xsd = tmp_path / 'strict_1.xsd'
    xsd.write_text('''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
        targetNamespace="urn:strict" version="1">
        <xs:complexType name="Contract">''' + particle + '''</xs:complexType>
        </xs:schema>''')
    request = AIcdDefinitionLoadRequest(xsd, AInDefinitionSourceKind.XMLDEFS,
                                        AIcAlgitesNamingProfiles.python_profile())
    with pytest.raises(ValueError, match='Unsupported XSD content model child'):
        AIcXmlDefsFrontend().load(request)


def test_unrelated_xml_document_is_not_interpreted_as_xsd(tmp_path: Path):
    document = tmp_path / 'wrong_1.xsd'
    document.write_text('<root><child/></root>')
    request = AIcdDefinitionLoadRequest(document, AInDefinitionSourceKind.XMLDEFS,
                                        AIcAlgitesNamingProfiles.python_profile())
    with pytest.raises(ValueError, match='Expected XML Schema root'):
        AIcXmlDefsFrontend().load(request)


def test_conditional_element_types_must_not_be_flattened(tmp_path: Path):
    schema = tmp_path / 'conditional_1.xsd'
    schema.write_text('''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
        targetNamespace="urn:conditional" version="1">
      <xs:complexType name="Root"><xs:sequence>
        <xs:element name="Mode" type="xs:string">
          <xs:alternative test="true()" type="xs:int"/>
        </xs:element>
      </xs:sequence></xs:complexType>
    </xs:schema>''')
    request = AIcdDefinitionLoadRequest(schema, AInDefinitionSourceKind.XMLDEFS,
                                        AIcAlgitesNamingProfiles.python_profile())
    with pytest.raises(ValueError, match='Unsupported XSD conditional element type'):
        AIcXmlDefsFrontend().load(request)


@pytest.mark.parametrize('directive', ['redefine', 'override', 'defaultOpenContent'])
def test_schema_wide_derivation_override_must_not_be_ignored(tmp_path: Path, directive: str):
    schema = tmp_path / 'override_1.xsd'
    schema.write_text('''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
      targetNamespace="urn:override" version="1">
      <xs:''' + directive + '''/>
      <xs:complexType name="Root"><xs:sequence>
        <xs:element name="A" type="xs:string"/>
      </xs:sequence></xs:complexType></xs:schema>''')
    request = AIcdDefinitionLoadRequest(schema, AInDefinitionSourceKind.XMLDEFS,
                                        AIcAlgitesNamingProfiles.python_profile())
    with pytest.raises(ValueError, match='Unsupported XSD schema directive'):
        AIcXmlDefsFrontend().load(request)
