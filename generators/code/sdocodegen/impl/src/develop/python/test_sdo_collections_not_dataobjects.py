"""Regression: collection contracts are not generated as DataObjects.

The obsolete Java list/DataObject forwarding hybrid is deliberately unsupported.
Do not restore it when extending bounded or multi-mapped list generation.
"""
from pathlib import Path

import pytest

from eu.algites.lib.common.list.aii_bounded_list import AIiBoundedList
from eu.algites.lib.common.list.aii_multi_mapped_list import AIiMultiMappedList
from eu.algites.lib.common.list.aic_multi_mapped_list import AIcMultiMappedList
from eu.algites.tool.codegen.common.aix_codegen_validation_exception import AIxCodegenValidationException
from eu.algites.tool.codegen.sdo.impl.standard.aic_sdo_codegen_service import (
    AIcSdoCodegenService,
)


def test_multi_mapped_is_bounded_list_not_data_object():
    """Keep list inheritance independent of data-object inheritance."""
    from eu.algites.lib.data.dataobject.aii_data_object import AIiDataObject

    assert issubclass(AIiMultiMappedList, AIiBoundedList)
    assert not issubclass(AIiMultiMappedList, AIiDataObject)
    assert isinstance(AIcMultiMappedList(min_size=1), AIiBoundedList)


def test_sdo_codegen_rejects_collection_as_dataobject():
    """The generator may only accept fields containing lists, not list SDOs."""
    service = AIcSdoCodegenService()
    with pytest.raises(AIxCodegenValidationException, match='A collection is not a DataObject'):
        service.generate(AIiMultiMappedList, naming=({}, {}, {}))


def test_no_active_java_forwarding_type_or_generator_reference():
    """Do not reintroduce the obsolete delegated list/DataObject hybrid."""
    repository = Path(__file__).resolve().parents[8]
    library = repository / 'pub.lib.General'
    tool = repository / 'pub.tool.General'
    assert not (library / 'common/util/src/product/java/eu/algites/lib/common/list/'
                'AIiMultiMappedListForwarding.java').exists()
    active = (
        tool / 'generators/code/sdocodegen/impl/src/product/java/eu/algites/tool/'
               'codegen/sdo/impl/standard/AIcSdoCodegenService.java'
    )
    assert 'MultiMappedListForwarding' not in active.read_text(encoding='utf-8')
