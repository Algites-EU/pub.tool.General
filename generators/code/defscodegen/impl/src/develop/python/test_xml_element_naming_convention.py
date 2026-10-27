"""Regression checks for independent XML type and element naming identities."""
from __future__ import annotations

from pathlib import Path

from eu.algites.lib.naming.convention.impl.standard.aic_name_convention_catalog import AIcNameConventionCatalog
from eu.algites.tool.codegen.defs.aicd_code_generation_request import AIcdCodeGenerationRequest
from eu.algites.tool.codegen.defs.aicd_definition_load_request import AIcdDefinitionLoadRequest
from eu.algites.tool.codegen.defs.ain_code_generation_target import AInCodeGenerationTarget
from eu.algites.tool.codegen.defs.ain_definition_source_kind import AInDefinitionSourceKind
from eu.algites.tool.codegen.defs.ain_defs_name_role import AInDefsNameRole
from eu.algites.tool.codegen.defs.impl.standard.aic_selected_naming_catalog import AIcSelectedNamingCatalog
from eu.algites.tool.codegen.defs.impl.standard.aic_xml_defs_frontend import AIcXmlDefsFrontend
from eu.algites.tool.codegen.defs.impl.standard.aic_xml_element_contract_generator import AIcXmlElementContractGenerator


def test_xml_element_records_its_own_naming_convention(tmp_path: Path):
    """An XML element must not inherit the content-type naming ID by accident."""
    source = tmp_path / 'invoice_1.xsd'
    source.write_text('''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
        targetNamespace="urn:invoice" version="1">
        <xs:complexType name="InvoiceType"><xs:sequence>
            <xs:element name="number" type="xs:string"/>
        </xs:sequence></xs:complexType>
        <xs:element name="invoice" type="InvoiceType"/>
    </xs:schema>''', encoding='utf-8')
    for language in ('java', 'python'):
        catalog = AIcNameConventionCatalog.load_resource(f'algites-{language}-name-conventions.yml')
        type_id = f'algites-{language}-gen-xml-type-intf-versioned_1'
        element_id = f'algites-{language}-gen-xml-element-intf-versioned_1'
        profile = AIcSelectedNamingCatalog(catalog, {
            AInDefsNameRole.INTERFACE_TYPE: type_id,
            AInDefsNameRole.INTERFACE_TYPE_FILE_STEM: type_id,
            AInDefsNameRole.XML_ELEMENT_INTERFACE_TYPE: element_id,
            AInDefsNameRole.XML_ELEMENT_INTERFACE_TYPE_FILE_STEM: element_id,
        })
        frontend = AIcXmlDefsFrontend()
        definition = frontend.load(AIcdDefinitionLoadRequest(source, AInDefinitionSourceKind.XMLDEFS, profile))
        declaration = frontend.global_element_declarations(
            AIcdDefinitionLoadRequest(source, AInDefinitionSourceKind.XMLDEFS, profile))[0]
        request = AIcdCodeGenerationRequest(definition,
            AInCodeGenerationTarget.JAVA if language == 'java' else AInCodeGenerationTarget.PYTHON,
            'example.invoice', profile, frontend.root_type_qname(
                AIcdDefinitionLoadRequest(source, AInDefinitionSourceKind.XMLDEFS, profile)),
            type_id, 'xmldefs_type')
        generated = AIcXmlElementContractGenerator().generate(
            request, declaration, {declaration.type_qname: 'example.invoice.AIig_xInvoiceType_1'}, {})
        assert '_xe' in generated.type_name.lower()
        assert element_id in generated.source
        assert type_id not in generated.source
        if language == 'java':
            assert f'namingConvention = "{element_id}"' in generated.source
        else:
            assert f"naming_convention='{element_id}'" in generated.source
