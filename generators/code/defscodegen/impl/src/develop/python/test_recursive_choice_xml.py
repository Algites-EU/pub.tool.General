"""Recursive canonical types, tagged choices, XML element identities and restrictions."""
from __future__ import annotations

import importlib
import json
import sys

import pytest

from eu.algites.lib.data.dataobject.ain_field_presence_kind import AInFieldPresenceKind
from eu.algites.lib.naming.convention.impl.algites.aic_algites_naming_profiles_1 import AIcAlgitesNamingProfiles_1
from eu.algites.tool.codegen.defs.aicd_definition_load_request import AIcdDefinitionLoadRequest
from eu.algites.tool.codegen.defs.ain_data_type_kind import AInDataTypeKind
from eu.algites.tool.codegen.defs.ain_definition_source_kind import AInDefinitionSourceKind
from eu.algites.tool.codegen.defs.impl.standard.aic_json_defs_frontend import AIcJsonDefsFrontend
from eu.algites.tool.codegen.defs.impl.standard.aic_xml_defs_frontend import AIcXmlDefsFrontend
from eu.algites.tool.codegen.defs.impl.standard.aic_schema_contract_bindings_generator import AIcSchemaContractBindingsGenerator


def _manifest(tmp_path, *languages):
    output = tmp_path / 'bindings.json'
    output.write_text(json.dumps({'artifact': 'intf', 'languages': list(languages)}))
    return output


def test_recursive_types_keep_nested_object_array_and_choice(tmp_path):
    path = tmp_path / 'recursion_1.jsondef.schema.json'
    path.write_text(json.dumps({'type': 'object', 'properties': {
        'items': {'type': 'array', 'items': {'type': 'array', 'items': {'type': 'object',
            'properties': {'code': {'oneOf': [{'type': 'string'}, {'type': 'integer'}]}}}}}}}))
    profile = AIcAlgitesNamingProfiles_1.python_profile()
    model = AIcJsonDefsFrontend().load(AIcdDefinitionLoadRequest(path, AInDefinitionSourceKind.JSONDEFS, profile))
    nodes = model.data_type.properties[0].data_type
    assert nodes.kind is AInDataTypeKind.ARRAY
    assert nodes.element_type.kind is AInDataTypeKind.ARRAY
    assert nodes.element_type.element_type.kind is AInDataTypeKind.OBJECT
    choice = nodes.element_type.element_type.properties[0].data_type
    assert choice.kind is AInDataTypeKind.ONE_OF
    assert tuple(a.kind for a in choice.alternatives) == (AInDataTypeKind.STRING, AInDataTypeKind.INTEGER)


def test_closed_choice_generates_sealed_java_and_importable_python_records(tmp_path, monkeypatch):
    source = tmp_path / 'intf/src/product/jsondefs/example/choice'
    source.mkdir(parents=True)
    (source / 'choice_1.jsondef.schema.json').write_text(json.dumps({
        '$defs': {'crypto': {'type': 'object', 'properties': {'wallet': {'type': 'string'}}}},
        'oneOf': [{'$ref': '#/$defs/crypto'}, {'type': 'integer'}]}))
    generated = AIcSchemaContractBindingsGenerator().generate_repository(tmp_path, _manifest(tmp_path, 'java', 'python'))
    assert len(generated) == 4
    root = tmp_path / 'intf/src/product/java.gen/example/choice'
    assert 'public sealed interface AIigChoice_1 permits' in (root / 'AIigChoice_1.java').read_text()
    assert 'AIigChoiceDefinitionCrypto_1 value' in (root / 'AIcgdChoiceChoiceDefinitionCrypto_1.java').read_text()
    assert 'Long value' in (root / 'AIcgdChoiceAlternative2_1.java').read_text()
    pyroot = tmp_path / 'intf/src/product/python.gen'
    monkeypatch.syspath_prepend(str(pyroot))
    module = importlib.import_module('example.choice.aicgd_choice_alternative2_1')
    assert module.AIcgdChoiceAlternative2_1(42).value == 42
    with pytest.raises(TypeError):
        module.AIcgdChoiceAlternative2_1('not an integer')


def test_global_xml_elements_generate_nominal_substitution_types(tmp_path, monkeypatch):
    root = tmp_path / 'intf/src/product/xmldefs/example/contracts'
    root.mkdir(parents=True)
    (root / 'transaction_1.xsd').write_text('''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
        xmlns:tns="urn:example:transaction" targetNamespace="urn:example:transaction" version="1">
      <xs:complexType name="TransactionType"><xs:sequence>
        <xs:element name="amount" type="xs:decimal"/>
      </xs:sequence></xs:complexType>
      <xs:element name="payment" type="tns:TransactionType" abstract="true"/>
      <xs:element name="cryptoPayment" type="tns:TransactionType" substitutionGroup="tns:payment"/>
      <xs:element name="paymentReference" type="xs:string"/>
    </xs:schema>''')
    output = AIcSchemaContractBindingsGenerator().generate_repository(tmp_path, _manifest(tmp_path, 'java', 'python'))
    assert len(output) == 8
    java = tmp_path / 'intf/src/product/java.gen/example/contracts'
    python = tmp_path / 'intf/src/product/python.gen/example/contracts'
    child = (java / 'AIig_xeCryptoPayment_1.java').read_text()
    assert 'AIig_xePayment_1' in child
    assert 'AIaOpenChoiceTypeOf' not in child
    assert 'AIaXmlDataObject' in child
    assert 'namespaceLocalName = "cryptoPayment"' in child
    assert (python / 'aiig__xe_crypto_payment_1.py').exists()
    scalar = (java / 'AIig_xePaymentReference_1.java').read_text()
    assert 'String getPaymentReference();' in scalar
    assert 'presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED' in scalar
    # Importing the child catches invalid C3-MRO when the substitution head
    # already extends the same content contract.
    monkeypatch.syspath_prepend(str(tmp_path / 'intf/src/product/python.gen'))
    from eu.algites.tool.codegen.sdo.impl.standard.aic_sdo_codegen_service import AIcSdoCodegenService
    from eu.algites.lib.naming.convention.impl.algites.aic_algites_naming_profiles_1 import AIcAlgitesNamingProfiles_1
    catalog = AIcAlgitesNamingProfiles_1.python_profile()
    all_contracts = (
        ('example.contracts.aiig_transaction_1', 'AIigTransaction_1'),
        ('example.contracts.aiig__xe_payment_1', 'AIig_xePayment_1'),
        ('example.contracts.aiig__xe_crypto_payment_1', 'AIig_xeCryptoPayment_1'),
    )
    for module_name, contract_name in all_contracts:
        contract = getattr(importlib.import_module(module_name), contract_name)
        emitted = AIcSdoCodegenService().generate(contract, naming=(catalog, catalog, catalog))
        for part in (emitted.mutable_interface, emitted.implementation):
            target = tmp_path / 'intf/src/product/python.gen' / part.relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(part.source, encoding='utf-8')
    implementation = importlib.import_module('example.contracts.aicgd__xe_crypto_payment_1')
    instance = implementation.AIcgd_xeCryptoPayment_1()
    assert isinstance(instance, importlib.import_module('example.contracts.aiig__xe_payment_1').AIig_xePayment_1)


def test_xsd_explicit_prohibited_attribute_projects_forbidden_presence(tmp_path):
    xsd = tmp_path / 'sample_1.xsd'
    xsd.write_text('''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" version="1">
      <xs:complexType name="Sample"><xs:sequence><xs:element name="value" type="xs:string"/>
      </xs:sequence><xs:attribute name="legacy" type="xs:string" use="prohibited"/>
      </xs:complexType></xs:schema>''')
    model = AIcXmlDefsFrontend().load(AIcdDefinitionLoadRequest(xsd, AInDefinitionSourceKind.XMLDEFS,
        AIcAlgitesNamingProfiles_1.python_profile()))
    assert {field.source_name: field.presence for field in model.data_type.properties} == {
        'value': AInFieldPresenceKind.REQUIRED, 'legacy': AInFieldPresenceKind.FORBIDDEN}


def test_allof_child_can_narrow_inherited_optional_presence(tmp_path):
    schemas = tmp_path / 'intf/src/product/jsondefs/example/restrictions'
    schemas.mkdir(parents=True)
    (schemas / 'parent_1.jsondef.schema.json').write_text(json.dumps({
        'type': 'object', 'properties': {'status': {'type': 'string'}}}))
    (schemas / 'child_1.jsondef.schema.json').write_text(json.dumps({
        'allOf': [{'$ref': 'parent_1.jsondef.schema.json'},
                  {'type': 'object', 'properties': {'status': {'type': 'string'}},
                   'required': ['status']}]}))
    AIcSchemaContractBindingsGenerator().generate_repository(tmp_path, _manifest(tmp_path, 'java', 'python'))
    java = (tmp_path / 'intf/src/product/java.gen/example/restrictions/AIigChild_1.java').read_text()
    python = (tmp_path / 'intf/src/product/python.gen/example/restrictions/aiig_child_1.py').read_text()
    assert 'extends example.restrictions.AIigParent_1' in java
    assert 'presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED' in java
    assert 'AInFieldPresenceKind.REQUIRED' in python


def test_closed_choice_can_wrap_same_simple_name_from_two_other_packages(tmp_path, monkeypatch):
    root = tmp_path / 'intf/src/product/jsondefs/example'
    for package in ('c', 'd'):
        folder = root / package
        folder.mkdir(parents=True)
        (folder / 'value_1.jsondef.schema.json').write_text(json.dumps({
            'type': 'object', 'properties': {'name': {'type': 'string'}}}))
    folder = root / 'payment'
    folder.mkdir(parents=True)
    (folder / 'choice_1.jsondef.schema.json').write_text(json.dumps({
        'oneOf': [{'$ref': '../c/value_1.jsondef.schema.json'},
                  {'$ref': '../d/value_1.jsondef.schema.json'}]}))
    AIcSchemaContractBindingsGenerator().generate_repository(tmp_path, _manifest(tmp_path, 'java', 'python'))
    java = sorted((tmp_path / 'intf/src/product/java.gen/example/payment').glob('AIcgdChoiceValue*.java'))
    assert len(java) == 2
    assert any('example.c.AIigValue_1 value' in path.read_text() for path in java)
    assert any('example.d.AIigValue_1 value' in path.read_text() for path in java)
    python = sorted((tmp_path / 'intf/src/product/python.gen/example/payment').glob('aicgd_choice_value*.py'))
    assert len(python) == 2
    assert any('from example.c.aiig_value_1 import AIigValue_1' in path.read_text() for path in python)
    assert any('from example.d.aiig_value_1 import AIigValue_1' in path.read_text() for path in python)
    monkeypatch.syspath_prepend(str(tmp_path / 'intf/src/product/python.gen'))
    for path in python:
        importlib.import_module('example.payment.' + path.stem)


def test_xsd_disallowed_substitution_is_rejected_instead_of_ignored(tmp_path):
    root = tmp_path / 'intf/src/product/xmldefs/example/restrictions'
    root.mkdir(parents=True)
    (root / 'payment_1.xsd').write_text('''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
        targetNamespace="urn:payment" version="1">
      <xs:complexType name="PaymentType"><xs:sequence>
        <xs:element name="amount" type="xs:decimal"/>
      </xs:sequence></xs:complexType>
      <xs:element name="payment" type="PaymentType" block="substitution"/>
    </xs:schema>''')
    with pytest.raises(ValueError, match='Unsupported XSD substitution/derivation restriction'):
        AIcSchemaContractBindingsGenerator().generate_repository(tmp_path, _manifest(tmp_path, 'java', 'python'))
