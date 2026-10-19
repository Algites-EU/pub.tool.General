"""Only recursive types are part of the public Java/Python canonical model."""

from dataclasses import fields
import pytest

from eu.algites.lib.data.dataobject.ain_field_presence_kind import AInFieldPresenceKind
from eu.algites.tool.codegen.defs.aicd_canonical_definition import AIcdCanonicalDefinition
from eu.algites.tool.codegen.defs.aicd_data_type import AIcdDataType
from eu.algites.tool.codegen.defs.aicd_definition_reference import AIcdDefinitionReference
from eu.algites.tool.codegen.defs.aicd_property_definition import AIcdPropertyDefinition
from eu.algites.tool.codegen.defs.ain_data_type_kind import AInDataTypeKind
from eu.algites.tool.codegen.defs.ain_definition_source_kind import AInDefinitionSourceKind
from eu.algites.tool.codegen.defs.impl.standard.aic_canonical_definition_merger import AIcCanonicalDefinitionMerger


def test_canonical_records_have_no_flat_projection():
    definition_fields = {field.name for field in fields(AIcdCanonicalDefinition)}
    property_fields = {field.name for field in fields(AIcdPropertyDefinition)}
    assert 'data_type' in definition_fields
    assert 'kind' not in definition_fields
    assert 'properties' not in definition_fields
    assert 'data_type' in property_fields
    assert not ({'value_kind', 'item_value_kind', 'reference', 'constraints', 'required'} & property_fields)
    assert not hasattr(AIcdDataType, 'from_legacy')
    assert not hasattr(AIcdDataType, 'source_type')
    assert not hasattr(AIcdDataType, 'root_type')
    reference_fields = {field.name for field in fields(AIcdDefinitionReference)}
    assert 'target_data_type' in reference_fields
    assert 'target_kind' not in reference_fields


def _definition(source_kind, member_type):
    member = AIcdPropertyDefinition('Items', member_type, AInFieldPresenceKind.REQUIRED)
    return AIcdCanonicalDefinition('urn:recursive', 1, 'recursive', source_kind, 'recursive_1',
                                   None, AIcdDataType(AInDataTypeKind.OBJECT, properties=(member,)))


def test_scalar_canonical_properties_merge_without_array_element_projection():
    string_type = AIcdDataType(AInDataTypeKind.STRING)
    AIcCanonicalDefinitionMerger.merge((
        _definition(AInDefinitionSourceKind.JSONDEFS, string_type),
        _definition(AInDefinitionSourceKind.YAMLDEFS, string_type)))


def test_recursive_array_choice_mismatch_is_reported():
    base = AIcdDataType(AInDataTypeKind.ARRAY, element_type=AIcdDataType(
        AInDataTypeKind.ONE_OF, alternatives=(AIcdDataType(AInDataTypeKind.STRING),
                                              AIcdDataType(AInDataTypeKind.INTEGER))))
    changed = AIcdDataType(AInDataTypeKind.ARRAY, element_type=AIcdDataType(
        AInDataTypeKind.ONE_OF, alternatives=(AIcdDataType(AInDataTypeKind.STRING),
                                              AIcdDataType(AInDataTypeKind.BOOLEAN))))
    with pytest.raises(ValueError, match=r'dataType\.items\.alternatives\[1\]\.kind'):
        AIcCanonicalDefinitionMerger.merge((
            _definition(AInDefinitionSourceKind.JSONDEFS, base),
            _definition(AInDefinitionSourceKind.YAMLDEFS, changed)))
