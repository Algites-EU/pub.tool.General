"""Regression coverage for schema titles and generated localizable field metadata."""
from pathlib import Path
import json

from eu.algites.lib.naming.convention.impl.algites.aic_algites_naming_profiles_1 import AIcAlgitesNamingProfiles_1
from eu.algites.tool.codegen.defs.aicd_definition_load_request import AIcdDefinitionLoadRequest
from eu.algites.tool.codegen.defs.aicd_code_generation_request import AIcdCodeGenerationRequest
from eu.algites.tool.codegen.defs.ain_definition_source_kind import AInDefinitionSourceKind
from eu.algites.tool.codegen.defs.ain_code_generation_target import AInCodeGenerationTarget
from eu.algites.tool.codegen.defs.impl.standard.aic_default_defs_codegen_service import AIcDefaultDefsCodegenService
from eu.algites.tool.codegen.defs.impl.standard.aic_schema_contract_interface_generator import AIcSchemaContractInterfaceGenerator


def test_schema_titles_flow_into_both_language_contracts(tmp_path: Path):
    path = tmp_path / 'credential_1.jsondef.schema.json'
    path.write_text(json.dumps({'type':'object', 'title':'Credential properties',
        'description':'Stored credential metadata.', 'properties': {
        'CertificatePrivateKey': {'type':'string', 'title':'Certificate private key',
            'description':'Private key used by the certificate.'}}}), encoding='utf-8')
    profile = AIcAlgitesNamingProfiles_1.python_profile()
    canonical = AIcDefaultDefsCodegenService().load(AIcdDefinitionLoadRequest(path, AInDefinitionSourceKind.JSONDEFS, profile))
    assert canonical.title == 'Credential properties'
    assert canonical.data_type.properties[0].title == 'Certificate private key'
    for target in (AInCodeGenerationTarget.JAVA, AInCodeGenerationTarget.PYTHON):
        names = AIcAlgitesNamingProfiles_1.java_profile() if target is AInCodeGenerationTarget.JAVA else profile
        source = AIcSchemaContractInterfaceGenerator().generate(
            AIcdCodeGenerationRequest(canonical, target, 'example.test', names)).source
        assert 'Certificate private key' in source
        assert 'Private key used by the certificate.' in source
        assert 'AIaFieldLabel.FIELD_DESCRIPTION' in source
        assert 'AIaFieldLabel' in source
        assert 'Credential properties' in source
        if target is AInCodeGenerationTarget.PYTHON:
            compile(source, '<generated>', 'exec')


def test_xsd_title_and_enum_value_metadata(tmp_path: Path):
    path = tmp_path / 'permissions_1.xsd'
    path.write_text('''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
 xmlns:algdoc="urn:eu:algites:documentation:1" targetNamespace="urn:example:permissions">
  <xs:simpleType name="Permissions">
    <xs:annotation><xs:appinfo><algdoc:title>Access permissions</algdoc:title></xs:appinfo>
      <xs:documentation>Available access rights.</xs:documentation></xs:annotation>
    <xs:restriction base="xs:string">
      <xs:enumeration value="read_only"><xs:annotation>
        <xs:appinfo><algdoc:title>Read only</algdoc:title></xs:appinfo>
        <xs:documentation>Allows access without modifications.</xs:documentation>
      </xs:annotation></xs:enumeration>
    </xs:restriction>
  </xs:simpleType>
</xs:schema>''', encoding='utf-8')
    model = AIcDefaultDefsCodegenService().load(AIcdDefinitionLoadRequest(path,
        AInDefinitionSourceKind.XMLDEFS, AIcAlgitesNamingProfiles_1.python_profile()))
    assert model.title == 'Access permissions'
    assert model.enum_values[0].title == 'Read only'
    assert model.enum_values[0].description == 'Allows access without modifications.'


def test_published_xmldefs_contract_schemas_preserve_titles_and_descriptions():
    """Both interface-artifact XMLDEFS must be parseable into canonical definitions."""
    from eu.algites.tool.codegen.defs.impl.standard.aic_xml_defs_frontend import AIcXmlDefsFrontend
    source = Path(__file__).resolve().parents[4] / 'intf/src/product/xmldefs/eu/algites/tool/codegen/defs'
    for name in ('input-profile', 'schema-field-bindings'):
        path = source / f'{name}_1.xsd'
        assert path.is_file()
        meta = path.with_name(path.name + '.meta.yml').read_text(encoding='utf-8')
        assert f'GlobalPublicationPathId: eu/algites/tool/codegen/defs/{name}_1.xsd' in meta
        obj = AIcXmlDefsFrontend().load(AIcdDefinitionLoadRequest(path, AInDefinitionSourceKind.XMLDEFS,
            AIcAlgitesNamingProfiles_1.python_profile()))
        assert obj.title and obj.description
        assert obj.data_type.properties
        assert all(field.title and field.description for field in obj.data_type.properties)
