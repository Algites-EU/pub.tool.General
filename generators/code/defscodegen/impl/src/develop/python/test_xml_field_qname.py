"""XML field QName and ELEMENT/ATTRIBUTE parity across frontends and native generators."""
from __future__ import annotations

import importlib
from pathlib import Path

import pytest

from eu.algites.lib.naming.convention.impl.algites.aic_algites_naming_profiles_1 import AIcAlgitesNamingProfiles_1
from eu.algites.lib.data.dataobject.xmldefs.ain_xml_value_kind import AInXmlValueKind
from eu.algites.tool.codegen.defs.aicd_definition_load_request import AIcdDefinitionLoadRequest
from eu.algites.tool.codegen.defs.aicd_code_generation_request import AIcdCodeGenerationRequest
from eu.algites.tool.codegen.defs.ain_definition_source_kind import AInDefinitionSourceKind
from eu.algites.tool.codegen.defs.ain_code_generation_target import AInCodeGenerationTarget
from eu.algites.tool.codegen.defs.impl.standard.aic_xml_defs_frontend import AIcXmlDefsFrontend
from eu.algites.tool.codegen.defs.impl.standard.aic_schema_contract_interface_generator import AIcSchemaContractInterfaceGenerator
from eu.algites.tool.codegen.sdo.impl.standard.aic_sdo_codegen_service import AIcSdoCodegenService


def _schema(path: Path, attribute_default='unqualified'):
    path.write_text(f'''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
        targetNamespace="urn:ledger" elementFormDefault="qualified"
        attributeFormDefault="{attribute_default}" version="1">
      <xs:complexType name="LedgerType"><xs:sequence>
        <xs:element name="amount" type="xs:decimal"/>
        <xs:element name="note" type="xs:string" form="unqualified"/>
      </xs:sequence>
      <xs:attribute name="currency" type="xs:string" use="required"/>
      <xs:attribute name="ref" type="xs:string" form="qualified"/>
      </xs:complexType>
    </xs:schema>''')


def test_xsd_fields_keep_exact_qname_and_kind(tmp_path):
    schema = tmp_path / 'ledger_1.xsd'
    _schema(schema)
    profile = AIcAlgitesNamingProfiles_1.python_profile()
    request = AIcdDefinitionLoadRequest(schema, AInDefinitionSourceKind.XMLDEFS, profile)
    frontend = AIcXmlDefsFrontend()
    fields = {p.source_name: p.xml_field for p in frontend.load(request).data_type.properties}
    assert {(name, info.namespace, info.namespace_local_name, info.value_kind) for name, info in fields.items()} == {
        ('amount', 'urn:ledger', 'amount', AInXmlValueKind.ELEMENT),
        ('note', '', 'note', AInXmlValueKind.ELEMENT),
        ('currency', '', 'currency', AInXmlValueKind.ATTRIBUTE),
        ('ref', 'urn:ledger', 'ref', AInXmlValueKind.ATTRIBUTE),
    }


def test_xml_metadata_survives_all_contract_renderers_and_sdo(tmp_path, monkeypatch):
    schema = tmp_path / 'ledger_1.xsd'
    _schema(schema)
    profile = AIcAlgitesNamingProfiles_1.python_profile()
    frontend = AIcXmlDefsFrontend()
    req = AIcdDefinitionLoadRequest(schema, AInDefinitionSourceKind.XMLDEFS, profile)
    root = tmp_path / 'out'
    for target in (AInCodeGenerationTarget.PYTHON, AInCodeGenerationTarget.JAVA):
        naming = AIcAlgitesNamingProfiles_1.python_profile() if target == AInCodeGenerationTarget.PYTHON else AIcAlgitesNamingProfiles_1.java_profile()
        generation = AIcdCodeGenerationRequest(frontend.load(AIcdDefinitionLoadRequest(schema, AInDefinitionSourceKind.XMLDEFS, naming)),
            target, 'example.ledger_qname', naming, frontend.root_type_qname(req))
        emitted = AIcSchemaContractInterfaceGenerator().generate(generation)
        if target == AInCodeGenerationTarget.JAVA:
            assert '@eu.algites.lib.data.dataobject.xmldefs.AIaXmlDataObjectField' in emitted.source
            assert 'namespace = "urn:ledger", namespaceLocalName = "amount", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT' in emitted.source
            assert 'namespace = "", namespaceLocalName = "currency", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ATTRIBUTE' in emitted.source
            assert 'order = 0, minOccurs = 1, maxOccurs = 1)' in emitted.source
            assert 'order = 3, minOccurs = 0, maxOccurs = 1)' in emitted.source
            continue
        assert '__xml_data_object_fields__' in emitted.source
        assert 'AInXmlValueKind.ATTRIBUTE' in emitted.source
        destination = root / emitted.relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(emitted.source)
        monkeypatch.syspath_prepend(str(root))
        contract = getattr(importlib.import_module('example.ledger_qname.' + destination.stem), emitted.type_name)
        assert contract.__xml_data_object_fields__['currency'].value_kind is AInXmlValueKind.ATTRIBUTE
        assert [entry.order for entry in contract.__xml_data_object_fields__.values()] == [0, 1, 2, 3]
        result = AIcSdoCodegenService().generate(contract, 'ledger', naming=(naming, naming, naming))
        assert '__xml_data_object_fields__' in result.mutable_interface.source
        assert "namespace='urn:ledger', namespace_local_name='amount'" in result.mutable_interface.source
        assert 'AInXmlValueKind.ATTRIBUTE' in result.mutable_interface.source
        assert 'order=0' in result.mutable_interface.source


def test_xsd_form_default_and_invalid_override(tmp_path):
    schema = tmp_path / 'ledger_1.xsd'
    _schema(schema, attribute_default='qualified')
    profile = AIcAlgitesNamingProfiles_1.python_profile()
    loader = AIcdDefinitionLoadRequest(schema, AInDefinitionSourceKind.XMLDEFS, profile)
    model = AIcXmlDefsFrontend().load(loader)
    assert {p.source_name: p.xml_field.namespace for p in model.data_type.properties}['currency'] == 'urn:ledger'
    schema.write_text(schema.read_text().replace('form="unqualified"', 'form="unknown"'))
    with pytest.raises(ValueError, match='form'):
        AIcXmlDefsFrontend().load(loader)


def test_prohibited_xsd_attribute_cannot_change_expanded_qname(tmp_path):
    """A type-less prohibited declaration must not erase a conflicting attribute namespace."""
    source = tmp_path / 'restricted_1.xsd'
    source.write_text('''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
        xmlns:tns="urn:ledger" targetNamespace="urn:ledger" version="1">
      <xs:complexType name="Base">
        <xs:attribute name="code" type="xs:string" form="qualified"/>
      </xs:complexType>
      <xs:complexType name="Restricted"><xs:complexContent>
        <xs:restriction base="tns:Base"><xs:attribute name="code" use="prohibited"/>
        </xs:restriction>
      </xs:complexContent></xs:complexType>
      <xs:element name="root" type="tns:Restricted"/>
    </xs:schema>''')
    naming = AIcAlgitesNamingProfiles_1.python_profile()
    load = AIcdDefinitionLoadRequest(source, AInDefinitionSourceKind.XMLDEFS, naming)
    with pytest.raises(ValueError, match='QName'):
        AIcXmlDefsFrontend().load(load)
    source.write_text(source.read_text().replace('name="code" use="prohibited"',
        'name="code" use="prohibited" form="qualified"'))
    actual = AIcXmlDefsFrontend().load(load).data_type.properties[0]
    assert actual.xml_field.namespace == 'urn:ledger'
    assert actual.xml_field.value_kind is AInXmlValueKind.ATTRIBUTE


def test_xml_merger_rejects_different_field_qname_for_same_contract(tmp_path):
    """Canonical merges cannot silently erase different XML wire identities."""
    from dataclasses import replace
    from eu.algites.tool.codegen.defs.aicd_xml_field_representation import AIcdXmlFieldRepresentation
    from eu.algites.tool.codegen.defs.impl.standard.aic_canonical_definition_merger import AIcCanonicalDefinitionMerger

    source = tmp_path / 'ledger_1.xsd'
    _schema(source)
    naming = AIcAlgitesNamingProfiles_1.python_profile()
    original = AIcXmlDefsFrontend().load(AIcdDefinitionLoadRequest(
        source, AInDefinitionSourceKind.XMLDEFS, naming))
    altered = replace(original, data_type=original.data_type.with_properties((replace(original.data_type.properties[0],
        xml_field=AIcdXmlFieldRepresentation('urn:changed', 'amount', AInXmlValueKind.ELEMENT)),
        *original.data_type.properties[1:])))
    with pytest.raises(ValueError, match='xmlField'):
        AIcCanonicalDefinitionMerger.validate((original, altered))
