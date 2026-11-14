"""Regression for a generic list refined into a keyed mapped list.

The Python SDO generator must preserve the parent's mutable generic parameter
when a derived contract narrows a normal list to AIiMultiMappedList. This is the
Python counterpart of AItcSdoMappedCovariantInheritanceTest in Java.
"""
from __future__ import annotations

import importlib
from pathlib import Path

from explicit_sdo_fixture import configured_service


def test_mapped_covariant_getter_keeps_inherited_generic_and_runtime_collection(tmp_path, monkeypatch):
    """Generate, compile, import and exercise both levels of the SDO hierarchy."""
    package = 'sdo_mapped_covariance_' + tmp_path.name.replace('-', '_')
    root = tmp_path / package
    root.mkdir()
    (root / '__init__.py').touch()
    sources = {
        'base_rule': '''from eu.algites.lib.data.dataobject.aii_data_object import AIiDataObject
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
class AIigBaseRule_1(AIiDataObject):
    __data_object__ = AIcdDataObject()
''',
        'json_rule': '''from .aiig_base_rule_1 import AIigBaseRule_1
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
class AIigJsonRule_1(AIigBaseRule_1):
    __data_object__ = AIcdDataObject()
''',
        'parent': '''from __future__ import annotations
from .aiig_base_rule_1 import AIigBaseRule_1
from eu.algites.lib.data.dataobject.aii_data_object import AIiDataObject
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
from eu.algites.lib.data.dataobject.aia_data_object_field import AIaDataObjectField
class AIigParent_1(AIiDataObject):
    __data_object__ = AIcdDataObject()
    @AIaDataObjectField(dataFieldName='RuleList')
    def getRuleList(self) -> list[AIigBaseRule_1]: ...
''',
        'json_child': '''from __future__ import annotations
from .aiig_parent_1 import AIigParent_1
from .aiig_json_rule_1 import AIigJsonRule_1
from eu.algites.lib.common.list.aii_multi_mapped_list import AIiMultiMappedList
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
from eu.algites.lib.data.dataobject.aia_data_object_field import AIaDataObjectField
class AIigJsonChild_1(AIigParent_1):
    __data_object__ = AIcdDataObject()
    @AIaDataObjectField(dataFieldName='RuleList')
    def getRuleList(self) -> AIiMultiMappedList[AIigJsonRule_1]: ...
''',
    }
    for key, source in sources.items():
        (root / f'aiig_{key}_1.py').write_text(source, encoding='utf-8')
    monkeypatch.syspath_prepend(str(tmp_path))
    generator = configured_service()
    generated = {}
    contracts = []
    for key, class_name in (
        ('base_rule', 'AIigBaseRule_1'),
        ('json_rule', 'AIigJsonRule_1'),
        ('parent', 'AIigParent_1'),
        ('json_child', 'AIigJsonChild_1'),
    ):
        read_only = getattr(importlib.import_module(f'{package}.aiig_{key}_1'), class_name)
        contracts.append((key, read_only))
    common = generator._naming(contracts[0][1])
    naming = common  # One naming convention for all read-only SDO contracts.
    for key, read_only in contracts:
        result = generator.service.generate(read_only, naming=naming)
        generated[key] = result
        for item in (result.mutable_interface, result.implementation):
            target = tmp_path / item.relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(item.source, encoding='utf-8')
            compile(item.source, str(target), 'exec')

    parent = generated['parent'].mutable_interface.source
    child = generated['json_child'].mutable_interface.source
    implementation = generated['json_child'].implementation.source
    assert 'TRuleList = TypeVar(' in parent
    assert 'list[TRuleList]' in parent
    assert 'TRuleList = TypeVar(' in child
    assert 'AIigdParent_1[TRuleList]' in child
    assert 'AIiMultiMappedList[TRuleList]' in child
    assert 'AIiMultiMappedList[AIigdJsonRule_1]' in implementation
    assert "get_OrCreateCollectionField('RuleList', True)" in implementation

    mutable_parent = importlib.import_module(f'{package}.aiigd_parent_1').AIigdParent_1
    mutable_child = importlib.import_module(f'{package}.aiigd_json_child_1').AIigdJsonChild_1
    concrete_child = importlib.import_module(f'{package}.aicgd_json_child_1').AIcgdJsonChild_1
    assert issubclass(mutable_child, mutable_parent)
    instance = concrete_child()
    assert isinstance(instance, mutable_child)
    collection = instance.getRuleList()
    from eu.algites.lib.common.list.aii_multi_mapped_list import AIiMultiMappedList
    assert isinstance(collection, AIiMultiMappedList)
    assert instance.getRuleList() is collection
