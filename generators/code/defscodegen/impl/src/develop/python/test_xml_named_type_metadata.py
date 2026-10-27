"""Verify named XSD TYPE identity survives both renderers and second-stage SDO generation."""
from __future__ import annotations
from eu.algites.tool.codegen.defs.aicd_data_type import AIcdDataType

import importlib
from pathlib import Path

import pytest
from eu.algites.lib.naming.convention.profile.algites.aic_algites_naming_profiles import AIcAlgitesNamingProfiles
from eu.algites.lib.data.dataobject.xmldefs.ain_xml_object_definition_kind import AInXmlObjectDefinitionKind
from eu.algites.tool.codegen.defs.aicd_definition_load_request import AIcdDefinitionLoadRequest
from explicit_legacy_naming import configured_generation as AIcdCodeGenerationRequest
from eu.algites.tool.codegen.defs.ain_definition_source_kind import AInDefinitionSourceKind
from eu.algites.tool.codegen.defs.ain_code_generation_target import AInCodeGenerationTarget
from eu.algites.tool.codegen.defs.impl.standard.aic_xml_defs_frontend import AIcXmlDefsFrontend
from eu.algites.tool.codegen.defs.impl.standard.aic_schema_contract_interface_generator import AIcSchemaContractInterfaceGenerator
from explicit_sdo_fixture import configured_service


def test_named_xml_type_qname_and_derived_mutable_contract(tmp_path: Path, monkeypatch):
    """The XSD declared type name is not inferred from the source filename or element QName."""
    source = tmp_path / 'inventory_1.xsd'
    source.write_text('''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
            targetNamespace="urn:stock" version="1">
        <xs:complexType name="WarehouseType"><xs:sequence>
            <xs:element name="count" type="xs:integer"/>
        </xs:sequence></xs:complexType>
        <xs:element name="inventory" type="WarehouseType"/>
    </xs:schema>''')
    profile = AIcAlgitesNamingProfiles.python_profile()
    load = AIcdDefinitionLoadRequest(source, AInDefinitionSourceKind.XMLDEFS, profile)
    frontend = AIcXmlDefsFrontend()
    qname = frontend.root_type_qname(load)
    assert qname == '{urn:stock}WarehouseType'
    request = AIcdCodeGenerationRequest(frontend.load(load), AInCodeGenerationTarget.PYTHON,
        'example.xsd_named_type', profile, qname)
    generator = AIcSchemaContractInterfaceGenerator()
    python = generator.generate(request)
    assert 'AIaXmlDataObject(' in python.source
    assert 'AInXmlObjectDefinitionKind.TYPE' in python.source
    assert "namespace_local_name='WarehouseType'" in python.source
    root = tmp_path / 'generated'
    target = root / python.relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(python.source)
    monkeypatch.syspath_prepend(str(root))
    read_contract = getattr(importlib.import_module('example.xsd_named_type.' + target.stem), python.type_name)
    assert read_contract.__xml_data_object__.definition_kind is AInXmlObjectDefinitionKind.TYPE
    assert read_contract.__xml_data_object__.namespace_local_name == 'WarehouseType'
    generated = configured_service().generate(read_contract, 'd')
    assert "namespace_local_name='WarehouseType'" in generated.mutable_interface.source
    java = generator.generate(AIcdCodeGenerationRequest(frontend.load(load),
        AInCodeGenerationTarget.JAVA, 'example.xsd_named_type', AIcAlgitesNamingProfiles.java_profile(), qname))
    assert 'AInXmlObjectDefinitionKind.TYPE' in java.source
    assert 'namespaceLocalName = "WarehouseType"' in java.source
    assert 'description = ' not in java.source.split('AIaDataObjectField(fieldName = ')[1].split(')',1)[0]


def test_non_xml_definition_cannot_claim_xml_type_qname():
    """Callers must not assign XML QName metadata to an unrelated source technology."""
    from eu.algites.tool.codegen.defs.aicd_canonical_definition import AIcdCanonicalDefinition
    from eu.algites.tool.codegen.defs.ain_data_type_kind import AInDataTypeKind
    definition = AIcdCanonicalDefinition('urn:other', 1, 'Root', AInDefinitionSourceKind.JSONDEFS, 'test.json', 'Test', AIcdDataType(AInDataTypeKind.OBJECT, properties=()), (), None)
    with pytest.raises(ValueError):
        AIcdCodeGenerationRequest(definition, AInCodeGenerationTarget.PYTHON, 'example',
            AIcAlgitesNamingProfiles.python_profile(), '{urn:stock}WarehouseType')
