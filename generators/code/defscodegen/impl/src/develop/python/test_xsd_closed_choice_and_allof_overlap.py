"""Cross-language XSD choice contracts and conservative allOf composition guards."""
from __future__ import annotations

import importlib
import json

import pytest

from eu.algites.lib.naming.convention.profile.algites.aic_algites_naming_profiles import AIcAlgitesNamingProfiles
from explicit_legacy_naming import configured_load as AIcdDefinitionLoadRequest
from eu.algites.tool.codegen.defs.ain_data_type_kind import AInDataTypeKind
from eu.algites.tool.codegen.defs.ain_definition_source_kind import AInDefinitionSourceKind
from eu.algites.tool.codegen.defs.impl.standard.aic_json_defs_frontend import AIcJsonDefsFrontend
from eu.algites.tool.codegen.defs.impl.standard.aic_yaml_defs_frontend import AIcYamlDefsFrontend
from eu.algites.tool.codegen.defs.impl.standard.aic_xml_defs_frontend import AIcXmlDefsFrontend
from eu.algites.tool.codegen.defs.impl.standard.aic_schema_contract_bindings_generator import AIcSchemaContractBindingsGenerator
from explicit_naming_fixture import explicit_legacy_generic_manifest


CHOICE = '''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
    targetNamespace="urn:choice:regression" elementFormDefault="qualified" version="1">
  <xs:complexType name="PaymentChoice"><xs:choice>
    <xs:element name="cash" type="xs:integer"/>
    <xs:element name="wire" type="xs:string"/>
  </xs:choice></xs:complexType>
  <xs:element name="payment" type="PaymentChoice"/>
</xs:schema>'''


def test_xml_closed_choice_preserves_qname_in_recursive_alternatives(tmp_path):
    xsd = tmp_path / 'payment_1.xsd'
    xsd.write_text(CHOICE)
    profile = AIcAlgitesNamingProfiles.python_profile()
    definition = AIcXmlDefsFrontend().load(AIcdDefinitionLoadRequest(
        xsd, AInDefinitionSourceKind.XMLDEFS, profile))
    assert definition.data_type.kind is AInDataTypeKind.ONE_OF
    assert [value.properties[0].source_name for value in definition.data_type.alternatives] == ["cash", "wire"]
    assert [value.properties[0].xml_field.namespace for value in definition.data_type.alternatives] == [
        'urn:choice:regression', 'urn:choice:regression']


def test_xml_closed_choice_generates_namespace_contracts_per_language(tmp_path, monkeypatch):
    sources = tmp_path / 'intf/src/product/xmldefs/example/choice'
    sources.mkdir(parents=True)
    (sources / 'payment_1.xsd').write_text(CHOICE)
    manifest = tmp_path / 'generate.json'
    manifest.write_text(json.dumps(explicit_legacy_generic_manifest({'artifact': 'intf', 'languages': ['java', 'python']})))
    generated = AIcSchemaContractBindingsGenerator().generate_repository(tmp_path, manifest)
    assert len(generated) == 6
    java = tmp_path / 'intf/src/product/java.gen/example/choice'
    python = tmp_path / 'intf/src/product/python.gen/example/choice'
    assert len(list(java.glob('*.java'))) == 7
    assert len(list(python.glob('*.py'))) == 7
    main = (java / 'AIigPayment_1.java').read_text()
    assert 'sealed interface AIigPayment_1 extends eu.algites.lib.data.dataobject.xmldefs.AIiXmlDataObject, example.choice.AIig_xnXmlDataObjectUrnChoiceRegression permits' in main
    assert 'namespaceLocalName = "PaymentChoice"' in main
    assert 'AIaXmlDataObjectField' in (java / 'AIigPaymentOneOf0_1.java').read_text()
    element_contract = (java / 'AIig_xePayment_1.java').read_text()
    assert 'AIigPayment_1 getPayment()' in element_contract
    assert 'extends eu.algites.lib.data.dataobject.xmldefs.AIiXmlDataObject' in element_contract
    assert 'localName = ' not in element_contract.split('@eu.algites.lib.data.dataobject.xmldefs.AIaXmlDataObjectField')[0]
    monkeypatch.syspath_prepend(str(tmp_path / 'intf/src/product/python.gen'))
    contract = importlib.import_module('example.choice.aiig_payment_1')
    assert contract.AIigPayment_1.__xml_data_object__.namespace_local_name == 'PaymentChoice'
    branch = importlib.import_module('example.choice.aiig_payment_one_of0_1')
    assert branch.AIigPaymentOneOf0_1.__xml_data_object_fields__['cash'].namespace == 'urn:choice:regression'
    importlib.import_module('example.choice.aiig_payment_alternative1_1')
    element = importlib.import_module('example.choice.aiig__xe_payment_1')
    assert element.AIig_xePayment_1.__xml_data_object__.namespace_local_name == 'payment'


@pytest.mark.parametrize('schema_type', ['jsondefs', 'yamldefs'])
def test_allof_redeclaration_must_not_replace_incompatible_shape(tmp_path, schema_type):
    import yaml
    suffix = 'jsondef.schema.json' if schema_type == 'jsondefs' else 'yamldef.schema.yaml'
    parent = tmp_path / ('parent_1.' + suffix)
    child = tmp_path / ('child_1.' + suffix)
    data_parent = {'type': 'object', 'properties': {'quantity': {'type': 'integer'}}}
    data_child = {'allOf': [
        {'$ref': 'parent_1.' + suffix},
        {'type': 'object', 'properties': {'quantity': {'type': 'string'}}}
    ]}
    render = json.dumps if schema_type == 'jsondefs' else yaml.safe_dump
    parent.write_text(render(data_parent))
    child.write_text(render(data_child))
    frontend = AIcJsonDefsFrontend() if schema_type == 'jsondefs' else AIcYamlDefsFrontend()
    source_kind = AInDefinitionSourceKind.JSONDEFS if schema_type == 'jsondefs' else AInDefinitionSourceKind.YAMLDEFS
    with pytest.raises(ValueError, match='Conflicting allOf property schema'):
        frontend.load(AIcdDefinitionLoadRequest(child, source_kind,
            AIcAlgitesNamingProfiles.python_profile()))


def test_recursive_reference_requires_explicit_identity():
    from eu.algites.tool.codegen.defs.aicd_data_type import AIcdDataType
    with pytest.raises(ValueError, match='REFERENCE requires'):
        AIcdDataType(AInDataTypeKind.REFERENCE)


def test_xml_choice_alternatives_are_compared_recursively(tmp_path):
    from eu.algites.tool.codegen.defs.impl.standard.aic_canonical_definition_merger import AIcCanonicalDefinitionMerger
    left = tmp_path / 'left/payment_1.xsd'
    right = tmp_path / 'right/payment_1.xsd'
    left.parent.mkdir()
    right.parent.mkdir()
    left.write_text(CHOICE)
    right.write_text(CHOICE.replace('name="wire" type="xs:string"',
                                   'name="wire" type="xs:integer"'))
    profile = AIcAlgitesNamingProfiles.python_profile()
    frontend = AIcXmlDefsFrontend()
    first = frontend.load(AIcdDefinitionLoadRequest(left, AInDefinitionSourceKind.XMLDEFS, profile))
    second = frontend.load(AIcdDefinitionLoadRequest(right, AInDefinitionSourceKind.XMLDEFS, profile))
    with pytest.raises(ValueError, match=r'root\.dataType'):
        AIcCanonicalDefinitionMerger.validate([first, second])
