"""Cross-boundary regression: current Defs annotations → current SDO → current runtime.

Unlike historical SDO fixtures, this test uses the new, method-bound
``dataFieldName`` declaration and does not depend on deprecated SDO metadata.
"""
from __future__ import annotations

import importlib
import sys

from eu.algites.lib.data.dataobject.aii_data_object import AIiDataObject
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
from eu.algites.lib.data.dataobject.aia_data_object_field import AIaDataObjectField
from eu.algites.tool.codegen.sdo.impl.standard._read_contract_fields import _data_object_fields
from eu.algites.lib.data.smartdataobject.impl.common.ais_smart_data_object_metadata_registry import (
    AIsSmartDataObjectMetadataRegistry,
)

from explicit_sdo_fixture import configured_service


def test_new_sdo_generator_never_imports_old_runtime_and_keeps_data_names():
    """Emit one contract and check its structural metadata and runtime superclass."""
    class AIigPerson_1(AIiDataObject):
        __data_object__ = AIcdDataObject()

        @AIaDataObjectField(dataFieldName='postal_code')
        def getPostalCode(self) -> str:
            raise NotImplementedError

    AIigPerson_1.__module__ = 'sample_contracts.person'
    fields = _data_object_fields(AIigPerson_1)
    assert list(fields) == ['PostalCode']
    assert fields['PostalCode'].field_name == 'postal_code'
    result = configured_service().generate(AIigPerson_1)
    source = result.implementation.source
    assert 'impl.common.aic_smart_data_object import AIcSmartDataObject' in source
    assert 'AIaSmartDataObjectImplementationBinding(readContracts=' in source
    assert 'impl.standard.aic_smart_data_object' not in source
    assert 'AIcXmlSmartDataObject' not in source
    assert 'xmlNestedTypes' not in source


def test_generated_new_sdo_is_importable_and_resolves_its_metadata(tmp_path, monkeypatch):
    """Actually import generated source; exercise setter/getter and new metadata."""
    package = tmp_path / 'sample_runtime'
    package.mkdir()
    (package / '__init__.py').write_text('', encoding='utf-8')
    (package / 'contracts.py').write_text('''
from eu.algites.lib.data.dataobject.aii_data_object import AIiDataObject
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
from eu.algites.lib.data.dataobject.aia_data_object_field import AIaDataObjectField
class AIigPerson_1(AIiDataObject):
    __data_object__ = AIcdDataObject()
    @AIaDataObjectField(dataFieldName="postal_code")
    def getPostalCode(self) -> str:
        raise NotImplementedError
''', encoding='utf-8')
    monkeypatch.syspath_prepend(str(tmp_path))
    try:
        contract = importlib.import_module('sample_runtime.contracts').AIigPerson_1
        result = configured_service().generate(contract)
        for generated in (result.mutable_interface, result.implementation):
            destination = tmp_path / generated.relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(generated.source, encoding='utf-8')
        importlib.invalidate_caches()
        implementation = getattr(importlib.import_module(result.implementation.module_name),
                                 result.implementation.type_name)
        subject = implementation()
        subject.setPostalCode('12345')
        assert subject.getPostalCode() == '12345'
        assert subject.getRawValues() == {'PostalCode': '12345'}
        field = AIsSmartDataObjectMetadataRegistry.forType(implementation).getField('PostalCode')
        assert field.getSemanticFieldName() == 'PostalCode'
        assert field.getDataFieldName() == 'postal_code'
    finally:
        for name in tuple(sys.modules):
            if name == 'sample_runtime' or name.startswith('sample_runtime.'):
                sys.modules.pop(name, None)


def test_unified_read_contract_inheritance_does_not_require_format_subclasses():
    """One derived getter can narrow presence without a JSON/XML/YAML interface."""
    from eu.algites.lib.data.dataobject.ain_field_presence_kind import AInFieldPresenceKind

    class AIigBaseSettings_1(AIiDataObject):
        __data_object__ = AIcdDataObject()

        @AIaDataObjectField(
            dataFieldName='IdentifierConventions',
            presence=AInFieldPresenceKind.ALLOWED,
        )
        def getIdentifierConventions(self) -> str:
            raise NotImplementedError

    class AIigStandardSettings_1(AIigBaseSettings_1):
        __data_object__ = AIcdDataObject()

        @AIaDataObjectField(
            dataFieldName='IdentifierConventions',
            presence=AInFieldPresenceKind.REQUIRED,
        )
        def getIdentifierConventions(self) -> str:
            raise NotImplementedError

    AIigBaseSettings_1.__module__ = 'sample_unified.settings'
    AIigStandardSettings_1.__module__ = 'sample_unified.settings'
    fields = _data_object_fields(AIigStandardSettings_1)
    assert len(fields) == 1
    assert fields['IdentifierConventions'].presence is AInFieldPresenceKind.REQUIRED
    result = configured_service().generate(AIigStandardSettings_1)
    implementation = result.implementation.source
    assert 'AIaSmartDataObjectImplementationBinding(readContracts=' in implementation
    assert 'impl.common.aic_smart_data_object import AIcSmartDataObject' in implementation
    assert 'AIiXmlSmartDataObject' not in implementation
    assert 'AIiJsonSmartDataObject' not in implementation
    assert 'AIiYamlSmartDataObject' not in implementation
