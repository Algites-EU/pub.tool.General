"""End-to-end regression for nested local XSD xs:key indexes.

A generated Company owns two Departments, each with its own independently
indexed Employee collection. This module tests both multiple and composite
keys through Defs Codegen, SDO Codegen, and XML deserialization.

Author: linhart1.
"""

from __future__ import annotations

import importlib
import json
import sys

import pytest

from explicit_naming_fixture import explicit_legacy_generic_manifest
from explicit_sdo_fixture import configured_service
from eu.algites.lib.common.list.aii_multi_mapped_list import AIiMultiMappedList
from eu.algites.tool.codegen.defs.impl.standard.aic_schema_contract_bindings_generator import (
    AIcSchemaContractBindingsGenerator,
)


SCHEMA = '''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:tns="urn:test" targetNamespace="urn:test"
    elementFormDefault="qualified" version="1">
  <xs:element name="Company"><xs:complexType><xs:sequence>
    <xs:element name="Department" maxOccurs="unbounded"><xs:complexType><xs:sequence>
      <xs:element name="Employee" maxOccurs="unbounded"><xs:complexType>
        <xs:sequence><xs:element name="Identity"><xs:complexType><xs:sequence>
          <xs:element name="Code" type="xs:int"/>
        </xs:sequence></xs:complexType></xs:element></xs:sequence>
        <xs:attribute name="id" type="xs:string" use="required"/>
        <xs:attribute name="region" type="xs:string" use="required"/>
      </xs:complexType></xs:element>
    </xs:sequence><xs:attribute name="name" type="xs:string"/></xs:complexType>
      <xs:key name="ById"><xs:selector xpath="tns:Employee"/>
        <xs:field xpath="@id"/></xs:key>
      <xs:key name="ByRegionCode"><xs:selector xpath="tns:Employee"/>
        <xs:field xpath="@region"/>
        <xs:field xpath="tns:Identity/tns:Code"/></xs:key>
    </xs:element>
  </xs:sequence></xs:complexType></xs:element>
</xs:schema>'''

XML = '''<Company xmlns="urn:test">
  <Department name="Development">
    <Employee id="101" region="eu"><Identity><Code>3</Code></Identity></Employee>
    <Employee id="102" region="us"><Identity><Code>003</Code></Identity></Employee>
  </Department>
  <Department name="Sales">
    <Employee id="101" region="eu"><Identity><Code>3</Code></Identity></Employee>
  </Department>
</Company>'''


def test_nested_local_indexes_survive_generation_and_deserialization(tmp_path):
    """Generate both language contracts and Python SDO, then verify live indexes.

    Args:
        tmp_path: Pytest-owned repository root; generated sources stay outside
            checked-in product and generated source trees.
    """
    package = 'case_b_generated'
    source = tmp_path / 'intf' / 'src' / 'product' / 'xmldefs' / package
    source.mkdir(parents=True)
    (source / 'company_1.xsd').write_text(SCHEMA)
    manifest = tmp_path / 'bindings.json'
    manifest.write_text(json.dumps(explicit_legacy_generic_manifest({
        'artifact': 'intf', 'languages': ['java', 'python']})))
    AIcSchemaContractBindingsGenerator().generate_repository(tmp_path, manifest)
    python_root = tmp_path / 'intf' / 'src' / 'product' / 'python.gen'
    java_root = tmp_path / 'intf' / 'src' / 'product' / 'java.gen' / package
    department_source = (java_root / 'AIigCompanyDepartment_1.java').read_text()
    assert '@eu.algites.lib.data.dataobject.xmldefs.AIaXmlKeyDefinition(name = "ById"' in department_source
    assert 'fields = {"region", "Identity.Code"}' in department_source
    assert 'AIiMultiMappedList<AIigCompanyDepartmentEmployee_1>' in department_source
    sys.path.insert(0, str(python_root))
    try:
        sdo = configured_service()
        for path in sorted((python_root / package).glob('aiig*.py')):
            if '_xn_' in path.stem or '_xe_' in path.stem:
                continue
            module = importlib.import_module(f'{package}.{path.stem}')
            contracts = [obj for obj in vars(module).values()
                         if isinstance(obj, type) and obj.__module__ == module.__name__
                         and obj.__name__.startswith('AIig')]
            assert len(contracts) == 1, path
            result = sdo.generate(contracts[0])
            for unit in (result.mutable_interface, result.implementation):
                target = python_root / unit.relative_path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(unit.source)
        company_type = importlib.import_module(f'{package}.aicgd_company_1').AIcgdCompany_1
        company = company_type.from_xml(XML)
        development, sales = company.getDepartment()
        first, second = development.getEmployee(), sales.getEmployee()
        assert isinstance(first, AIiMultiMappedList)
        assert isinstance(second, AIiMultiMappedList)
        assert first is not second
        assert first.key_definition('ById') is not second.key_definition('ById')
        assert [e.getId() for e in first] == ['101', '102']
        assert [e.getId() for e in second] == ['101']
        id_definition = first.key_definition('ById')
        compound_definition = first.key_definition('ByRegionCode')
        assert id_definition is not None and compound_definition is not None
        assert first.map_by_key_type(id_definition)['101'][0].getId() == '101'
        assert first.map_by_key_type(compound_definition)[('us', 3)][0].getId() == '102'
        assert first[1].getIdentity().getCode() == 3
        with pytest.raises(ValueError, match='Duplicate unique key'):
            first.append(first[0])
        assert len(first) == 2
        assert len(first.map_by_key_type(id_definition)) == 2
        bad_composite = XML.replace('id="102" region="us"', 'id="102" region="eu"')
        with pytest.raises(ValueError, match='ByRegionCode'):
            company_type.from_xml(bad_composite)
        bad_id = XML.replace('id="102" region="us"', 'id="101" region="us"')
        with pytest.raises(ValueError, match='ById'):
            company_type.from_xml(bad_id)
        missing = XML.replace('<Identity><Code>3</Code></Identity>', '', 1)
        with pytest.raises(ValueError, match='Identity'):
            company_type.from_xml(missing)
    finally:
        sys.path.remove(str(python_root))
        for name in list(sys.modules):
            if name == package or name.startswith(package + '.'):
                del sys.modules[name]
