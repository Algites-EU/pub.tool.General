"""Regression: format projections must not become independent SDO contracts."""

import pytest

from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
from eu.algites.lib.data.dataobject.aii_data_object import AIiDataObject
from eu.algites.lib.data.dataobject.jsondefs.aia_data_object_json_schema import AIaDataObjectJsonSchema
from eu.algites.tool.codegen.common.aix_codegen_validation_exception import AIxCodegenValidationException
from explicit_sdo_fixture import configured_service


class AIigNeutral_1(AIiDataObject):
    """Canonical read-only DataObject shared by all supported schema formats."""

    __data_object__ = AIcdDataObject()
    __data_object_fields__ = ()


class AIigNeutralDescendant_1(AIigNeutral_1):
    """Legitimate schema-neutral descendant of an annotated DataObject."""


class AIigInheritedProjection_1(AIigNeutral_1):
    """An inherited neutral contract with only a format-local schema annotation."""
    __json_schema__ = AIaDataObjectJsonSchema(schema_id="json")


AIigNeutralDescendant_1.__module__ = 'unit.boundary.neutral_descendant'
AIigNeutral_1.__module__ = 'unit.boundary.neutral'
AIigInheritedProjection_1.__module__ = 'unit.boundary.inherited_projection'


def test_standalone_sdo_rejects_inherited_metadata_from_format_projection():
    """A format projection with no own DataObject declaration cannot be an SDO input."""
    with pytest.raises(AIxCodegenValidationException):
        configured_service().generate(AIigInheritedProjection_1)


def test_standalone_sdo_accepts_unified_annotated_contract():
    """The canonical contract is accepted without a technology role or suffix."""
    result = configured_service().generate(AIigNeutral_1)
    assert result.mutable_interface.type_name == 'AIigdNeutral_1'


def test_standalone_sdo_accepts_neutral_descendant_with_inherited_metadata():
    """Inheritance is established by real DataObject ancestry, never a name."""
    result = configured_service().generate(AIigNeutralDescendant_1)
    assert result.mutable_interface.type_name == 'AIigdNeutralDescendant_1'


def test_standalone_sdo_accepts_explicit_multiformat_common_contract():
    """A common DataObject may itself carry JSON metadata without an extra type."""
    class AIigAnnotatedJson_1(AIigNeutral_1):
        __data_object__ = AIcdDataObject()
        __json_schema__ = AIaDataObjectJsonSchema(schema_id="json", schema_version=1)
    AIigAnnotatedJson_1.__module__ = 'unit.boundary.annotated_json'
    assert configured_service().generate(AIigAnnotatedJson_1).mutable_interface.type_name == 'AIigdAnnotatedJson_1'
