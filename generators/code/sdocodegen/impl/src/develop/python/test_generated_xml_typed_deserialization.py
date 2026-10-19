"""End-to-end XML SDO code generation and QName-based concrete materialization."""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

from eu.algites.tool.codegen.sdo.impl.standard.aic_sdo_codegen_service import AIcSdoCodegenService


def test_xml_generated_nested_repeating_sdo_types(tmp_path, monkeypatch):
    package = 'xmlsdogen_' + tmp_path.name.replace('-', '_')
    folder = tmp_path / package
    folder.mkdir()
    (folder / '__init__.py').write_text('')
    (folder / 'aiig_item_1.py').write_text('''
from eu.algites.lib.data.dataobject.xmldefs.aii_xml_data_object import AIiXmlDataObject
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
from eu.algites.lib.data.dataobject.aicd_data_object_field import AIcdDataObjectField
from eu.algites.lib.data.dataobject.xmldefs.aia_xml_data_object import AIaXmlDataObject
from eu.algites.lib.data.dataobject.xmldefs.aia_xml_data_object_field import AIaXmlDataObjectField
from eu.algites.lib.data.dataobject.xmldefs.ain_xml_object_definition_kind import AInXmlObjectDefinitionKind
class AIigItem_1(AIiXmlDataObject):
    __data_object__ = AIcdDataObject(schema_id='urn:items', schema_version=1)
    __xml_data_object__ = AIaXmlDataObject(definition_kind=AInXmlObjectDefinitionKind.TYPE, namespace='urn:items', namespace_local_name='ItemType')
    __data_object_fields__ = (AIcdDataObjectField('Name', getter_name='getName', expected_type=str),)
    __xml_data_object_fields__ = {'Name': AIaXmlDataObjectField(namespace='urn:items', namespace_local_name='Name')}
    def getName(self) -> str: raise NotImplementedError
''')
    (folder / 'aiig_order_1.py').write_text('''
from __future__ import annotations
from .aiig_item_1 import AIigItem_1
from eu.algites.lib.data.dataobject.xmldefs.aii_xml_data_object import AIiXmlDataObject
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
from eu.algites.lib.data.dataobject.aicd_data_object_field import AIcdDataObjectField
from eu.algites.lib.data.dataobject.xmldefs.aia_xml_data_object import AIaXmlDataObject
from eu.algites.lib.data.dataobject.xmldefs.aia_xml_data_object_field import AIaXmlDataObjectField
from eu.algites.lib.data.dataobject.xmldefs.ain_xml_object_definition_kind import AInXmlObjectDefinitionKind
from eu.algites.lib.data.dataobject.xmldefs.ain_xml_value_kind import AInXmlValueKind
class AIigOrder_1(AIiXmlDataObject):
    __data_object__ = AIcdDataObject(schema_id='urn:orders', schema_version=1)
    __xml_data_object__ = AIaXmlDataObject(definition_kind=AInXmlObjectDefinitionKind.ELEMENT, namespace='urn:orders', namespace_local_name='Order')
    __data_object_fields__ = (AIcdDataObjectField('Item', getter_name='getItem', expected_type=list), AIcdDataObjectField('Flag', getter_name='getFlag', expected_type=bool))
    __xml_data_object_fields__ = {'Item': AIaXmlDataObjectField(namespace='urn:orders', namespace_local_name='Item'), 'Flag': AIaXmlDataObjectField(namespace='', namespace_local_name='flag', value_kind=AInXmlValueKind.ATTRIBUTE)}
    Item: list[AIigItem_1]
    def getItem(self) -> list[AIigItem_1]: raise NotImplementedError
    def getFlag(self) -> bool: raise NotImplementedError
''')
    monkeypatch.syspath_prepend(str(tmp_path))
    child = importlib.import_module(package + '.aiig_item_1').AIigItem_1
    order = importlib.import_module(package + '.aiig_order_1').AIigOrder_1
    generator = AIcSdoCodegenService()
    for contract in (child, order):
        result = generator.generate(contract)
        for source in (result.mutable_interface, result.implementation):
            path = tmp_path / source.relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(source.source, encoding='utf-8')
        if contract is order:
            assert "__xml_repeated_fields__ = ('Item',)" in result.mutable_interface.source
            assert "__xml_field_type_imports__" in result.implementation.source
            assert "def from_xml(cls, aXml" in result.implementation.source
    from eu.algites.lib.data.smartdataobject.impl.xmldefs.aic_xml_smart_data_object import AIcXmlSmartDataObject
    Order = getattr(importlib.import_module(package + '.aicgd_order_1'), 'AIcgdOrder_1')
    Item = getattr(importlib.import_module(package + '.aicgd_item_1'), 'AIcgdItem_1')
    xml = ('<p:Order xmlns:p="urn:orders" xmlns:i="urn:items" flag="true">'
           '<p:Item><i:Name>alpha</i:Name></p:Item>'
           '<p:Item><i:Name>beta</i:Name></p:Item></p:Order>')
    parsed = Order.from_xml(xml)
    assert isinstance(parsed, AIcXmlSmartDataObject)
    assert parsed.getFlag() is True
    assert len(parsed.getItem()) == 2
    assert all(isinstance(item, Item) for item in parsed.getItem())
    assert [item.getName() for item in parsed.getItem()] == ['alpha', 'beta']


def test_xsd_repeating_scalar_flows_through_defs_and_sdo_generators(tmp_path, monkeypatch):
    """The SDO generator must read cardinality from genuine Defs-generated types."""
    import json
    from eu.algites.tool.codegen.defs.impl.standard.aic_schema_contract_bindings_generator import AIcSchemaContractBindingsGenerator
    package = 'xsdsdogen_' + tmp_path.name.replace('-', '_')
    source = tmp_path / 'intf/src/product/xmldefs' / package
    source.mkdir(parents=True)
    (source / 'invoice_1.xsd').write_text('''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
      targetNamespace="urn:invoice" elementFormDefault="qualified" version="1">
      <xs:complexType name="InvoiceType"><xs:sequence>
        <xs:element name="Code" type="xs:string" maxOccurs="5" minOccurs="0"/>
      </xs:sequence></xs:complexType>
    </xs:schema>''')
    manifest = tmp_path / 'bindings.json'
    manifest.write_text(json.dumps({'artifact': 'intf', 'languages': ['python']}))
    AIcSchemaContractBindingsGenerator().generate_repository(tmp_path, manifest)
    pyroot = tmp_path / 'intf/src/product/python.gen'
    monkeypatch.syspath_prepend(str(pyroot))
    module = importlib.import_module(package + '.aiig_invoice_1')
    Contract = module.AIigInvoice_1
    result = AIcSdoCodegenService().generate(Contract)
    assert '__xml_repeated_fields__' in result.mutable_interface.source
    assert "'Code'" in result.mutable_interface.source
    for unit in (result.mutable_interface, result.implementation):
        destination = pyroot / unit.relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(unit.source)
    Instance = importlib.import_module(package + '.aicgd_invoice_1').AIcgdInvoice_1
    obj = Instance.from_xml('<x:InvoiceType xmlns:x="urn:invoice">'
                            '<x:Code>abc</x:Code><x:Code>def</x:Code></x:InvoiceType>')
    assert obj.getCode() == ['abc', 'def']
