"""Generate nominal parent contracts for multiple named types from one XSD file."""
from __future__ import annotations
import importlib
import json
from pathlib import Path

from eu.algites.tool.codegen.defs.impl.standard.aic_schema_contract_bindings_generator import AIcSchemaContractBindingsGenerator
from explicit_naming_fixture import explicit_legacy_generic_manifest


def test_same_file_complex_type_extension_emits_two_types_and_one_element(tmp_path, monkeypatch):
    schema_dir = tmp_path / 'intf/src/product/xmldefs/example/types'
    schema_dir.mkdir(parents=True)
    (schema_dir / 'derived_1.xsd').write_text('''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
        xmlns:tns="urn:multiple-types" targetNamespace="urn:multiple-types"
        elementFormDefault="qualified" version="1">
        <xs:complexType name="BaseType"><xs:sequence>
          <xs:element name="amount" type="xs:integer"/>
        </xs:sequence></xs:complexType>
        <xs:complexType name="DerivedType"><xs:complexContent>
          <xs:extension base="tns:BaseType"><xs:sequence>
            <xs:element name="code" type="xs:string"/>
          </xs:sequence></xs:extension>
        </xs:complexContent></xs:complexType>
        <xs:element name="derivedElement" type="tns:DerivedType"/>
    </xs:schema>''')
    manifest = tmp_path / 'manifest.json'
    manifest.write_text(json.dumps(explicit_legacy_generic_manifest({'artifact': 'intf', 'languages': ['java', 'python']})))
    generated = AIcSchemaContractBindingsGenerator().generate_repository(tmp_path, manifest)
    assert len(generated) == 8  # two types, one global element and one XML namespace per target
    java_dir = tmp_path / 'intf/src/product/java.gen/example/types'
    python_dir = tmp_path / 'intf/src/product/python.gen/example/types'
    root = (java_dir / 'AIigDerived_1.java').read_text()
    base = (java_dir / 'AIigBaseType_1.java').read_text()
    assert 'extends example.types.AIigBaseType_1' in root
    assert 'amount()' not in root
    assert 'namespaceLocalName = "BaseType"' in base
    assert 'AIigDerived_1' in (java_dir / 'AIig_xeDerivedElement_1.java').read_text()
    assert len(list(java_dir.glob('AIig_xe*.java'))) == 1
    monkeypatch.syspath_prepend(str(tmp_path / 'intf/src/product/python.gen'))
    derived = importlib.import_module('example.types.aiig_derived_1').AIigDerived_1
    parent = importlib.import_module('example.types.aiig_base_type_1').AIigBaseType_1
    assert issubclass(derived, parent)
    assert derived.__xml_data_object__.namespace_local_name == 'DerivedType'
    assert parent.__xml_data_object__.namespace_local_name == 'BaseType'
    assert len(list(python_dir.glob('aiig__xe*.py'))) == 1
