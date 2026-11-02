"""XMLDEFS xs:unique and xs:key produce different required-key metadata.

Tests both namespaced and namespace-free XSD 1.0 declarations. The generated
files live solely in the test runner's temporary directory.

Author: linhart1.
"""
from __future__ import annotations

import json

import pytest

from explicit_naming_fixture import explicit_legacy_generic_manifest
from eu.algites.tool.codegen.defs.impl.standard.aic_schema_contract_bindings_generator import (
    AIcSchemaContractBindingsGenerator,
)


@pytest.mark.parametrize('namespace', ['', 'urn:test:optional:1'])
def test_unique_optional_key_and_required_key_are_distinct(tmp_path, namespace):
    """Optional missing keys must survive the schema and interface projections."""
    package = 'unique_case'
    source = tmp_path / 'intf' / 'src' / 'product' / 'xmldefs' / package
    source.mkdir(parents=True)
    ns_decl = (f'xmlns:tns="{namespace}" targetNamespace="{namespace}"'
               if namespace else '')
    selector = 'tns:Entry' if namespace else 'Entry'
    document = f'''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
        {ns_decl} elementFormDefault="qualified" version="1">
      <xs:element name="Entries"><xs:complexType><xs:sequence>
        <xs:element name="Entry" minOccurs="0" maxOccurs="unbounded">
          <xs:complexType><xs:attribute name="Code" type="xs:string"/>
            <xs:attribute name="Id" type="xs:string" use="required"/>
          </xs:complexType>
        </xs:element>
      </xs:sequence></xs:complexType>
        <xs:unique name="ByCode"><xs:selector xpath="{selector}"/>
          <xs:field xpath="@Code"/></xs:unique>
        <xs:key name="ById"><xs:selector xpath="{selector}"/>
          <xs:field xpath="@Id"/></xs:key>
      </xs:element>
    </xs:schema>'''
    (source / 'entries_1.xsd').write_text(document)
    manifest = tmp_path / 'bindings.json'
    manifest.write_text(json.dumps(explicit_legacy_generic_manifest({
        'artifact': 'intf', 'languages': ['java', 'python']})))
    AIcSchemaContractBindingsGenerator().generate_repository(tmp_path, manifest)
    java_sources = list((tmp_path / 'intf/src/product/java.gen').rglob('*.java'))
    python_sources = list((tmp_path / 'intf/src/product/python.gen').rglob('*.py'))
    assert java_sources and python_sources
    java = '\n'.join(source.read_text() for source in java_sources)
    python = '\n'.join(source.read_text() for source in python_sources)
    assert 'name = "ByCode", fields = {"Code"}, required = false' in java
    assert 'name = "ById", fields = {"Id"}, required = true' in java
    assert "('ByCode', ('Code',), False)" in python
    assert "('ById', ('Id',), True)" in python


def test_optional_xml_key_runtime_groups_missing_components(tmp_path):
    """Exercise generated SDO XML reader and its live optional-key index."""
    from importlib import import_module
    import sys

    from explicit_sdo_fixture import configured_service

    package = 'unique_sdo_generated'
    source = tmp_path / 'intf/src/product/xmldefs' / package
    source.mkdir(parents=True)
    (source / 'entries_1.xsd').write_text('''<xs:schema
        xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:tns="urn:test:unique:1"
        targetNamespace="urn:test:unique:1" elementFormDefault="qualified" version="1">
      <xs:element name="Entries"><xs:complexType><xs:sequence>
        <xs:element name="Entry" minOccurs="0" maxOccurs="unbounded">
          <xs:complexType><xs:attribute name="Id" type="xs:string" use="required"/>
            <xs:attribute name="Code" type="xs:string"/></xs:complexType>
        </xs:element>
      </xs:sequence></xs:complexType>
        <xs:key name="ById"><xs:selector xpath="tns:Entry"/>
          <xs:field xpath="@Id"/></xs:key>
        <xs:unique name="ByCode"><xs:selector xpath="tns:Entry"/>
          <xs:field xpath="@Code"/></xs:unique>
      </xs:element>
    </xs:schema>''')
    manifest = tmp_path / 'bindings.json'
    manifest.write_text(json.dumps(explicit_legacy_generic_manifest({
        'artifact': 'intf', 'languages': ['java', 'python']})))
    AIcSchemaContractBindingsGenerator().generate_repository(tmp_path, manifest)
    generated = tmp_path / 'intf/src/product/python.gen'
    sys.path.insert(0, str(generated))
    try:
        sdo = configured_service()
        for path in sorted((generated / package).glob('aiig*.py')):
            if '_xn_' in path.stem or '_xe_' in path.stem:
                continue
            module = import_module(f'{package}.{path.stem}')
            contracts = [obj for obj in vars(module).values()
                if isinstance(obj, type) and obj.__module__ == module.__name__
                and obj.__name__.startswith('AIig')]
            for contract in contracts:
                result = sdo.generate(contract)
                for generated_unit in (result.mutable_interface, result.implementation):
                    target = generated / generated_unit.relative_path
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(generated_unit.source)
        owner = import_module(f'{package}.aicgd_entries_1').AIcgdEntries_1
        document = owner.from_xml('''<Entries xmlns="urn:test:unique:1">
          <Entry Id="1"/><Entry Id="2"/><Entry Id="3" Code="A"/>
        </Entries>''')
        collection = document.getEntry()
        by_id = collection.map_by_key_type(collection.key_definition('ById'))
        by_code = collection.map_by_key_type(collection.key_definition('ByCode'))
        assert [item.getId() for item in by_code[None]] == ['1', '2']
        assert by_code['A'][0].getId() == '3'
        assert by_id['3'][0].getCode() == 'A'
        with pytest.raises(ValueError, match='Duplicate unique key'):
            owner.from_xml('''<Entries xmlns="urn:test:unique:1">
              <Entry Id="1" Code="A"/><Entry Id="2" Code="A"/>
            </Entries>''')
        with pytest.raises(ValueError):
            owner.from_xml('''<Entries xmlns="urn:test:unique:1">
              <Entry Code="A"/>
            </Entries>''')
    finally:
        sys.path.remove(str(generated))
        for name in list(sys.modules):
            if name == package or name.startswith(package + '.'):
                del sys.modules[name]
