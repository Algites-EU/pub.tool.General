"""Regression for a shared XML named keyed container and a required restriction."""

from __future__ import annotations

from pathlib import Path

from eu.algites.lib.data.dataobject.ain_field_presence_kind import AInFieldPresenceKind
from eu.algites.tool.codegen.defs.ain_data_type_kind import AInDataTypeKind
from eu.algites.tool.codegen.defs.ain_definition_source_kind import AInDefinitionSourceKind
from eu.algites.tool.codegen.defs.impl.standard.aic_default_defs_codegen_service import AIcDefaultDefsCodegenService
from eu.algites.tool.codegen.defs.impl.standard.aic_xml_defs_frontend import AIcXmlDefsFrontend
from explicit_legacy_naming import catalog, configured_load


COMMON = '''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:tns="urn:shared-conventions" targetNamespace="urn:shared-conventions" version="1">
    <xs:complexType name="shared">
        <xs:sequence>
            <xs:element name="Entries" type="tns:entries" minOccurs="0">
                <xs:key name="ByName">
                    <xs:selector xpath="Entry"/>
                    <xs:field xpath="@name"/>
                </xs:key>
            </xs:element>
        </xs:sequence>
    </xs:complexType>
    <xs:complexType name="entries">
        <xs:sequence>
            <xs:element name="Entry" minOccurs="0" maxOccurs="unbounded">
                <xs:complexType>
                    <xs:attribute name="name" type="xs:string" use="required"/>
                </xs:complexType>
            </xs:element>
        </xs:sequence>
    </xs:complexType>
</xs:schema>'''

STANDARD = '''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:shared="urn:shared-conventions" targetNamespace="urn:standard-conventions" version="1">
    <xs:import namespace="urn:shared-conventions" schemaLocation="shared_1.xsd"/>
    <xs:complexType name="standard">
        <xs:complexContent>
            <xs:restriction base="shared:shared">
                <xs:sequence>
                    <xs:element name="Entries" type="shared:entries">
                        <xs:key name="ByName">
                            <xs:selector xpath="Entry"/>
                            <xs:field xpath="@name"/>
                        </xs:key>
                    </xs:element>
                </xs:sequence>
            </xs:restriction>
        </xs:complexContent>
    </xs:complexType>
</xs:schema>'''


def test_named_xsd_key_container_survives_required_restriction(tmp_path: Path) -> None:
    """Requiredness tightening must retain the single named multi-mapped list."""
    common = tmp_path / "shared_1.xsd"
    standard = tmp_path / "standard_1.xsd"
    common.write_text(COMMON, encoding="utf-8")
    standard.write_text(STANDARD, encoding="utf-8")

    frontend = AIcXmlDefsFrontend()
    assert "SharedEntriesAdditionalProperties" in frontend.additional_named_type_names(common)
    profile = catalog("java")
    request = configured_load(common, AInDefinitionSourceKind.XMLDEFS, profile)
    entries = frontend.load_named_type(request, "entries")
    assert len(entries.data_type.properties) == 1
    item = entries.data_type.properties[0]
    assert item.source_name == "Entry"
    assert item.data_type.kind is AInDataTypeKind.ARRAY
    assert tuple((key.name, key.fields) for key in item.data_type.key_definitions) == (
        ("ByName", ("name",)),)

    service = AIcDefaultDefsCodegenService()
    derived = service.load(configured_load(standard, AInDefinitionSourceKind.XMLDEFS, profile))
    assert len(derived.data_type.properties) == 1
    assert derived.data_type.properties[0].source_name == "Entries"
    assert derived.data_type.properties[0].presence is AInFieldPresenceKind.REQUIRED
